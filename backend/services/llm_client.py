# Multi-provider LLM Client supporting Mock, Ollama, Azure AI Agent Service, Vertex AI, and Gemini
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from models import LLMProvider, LLMConfig

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""

    @abstractmethod
    async def generate(self, prompt: str, context: str = "", system_prompt: str = "") -> Dict[str, Any]:
        """Generate a response from the LLM

        Returns:
            Dict with keys: 'response', 'prompt_tokens', 'completion_tokens', 'model_name'
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM service is available"""
        pass


class GeminiLLMClient(BaseLLMClient):
    """Direct Gemini REST API client using GOOGLE_API_KEY."""

    DEFAULT_MODEL = "gemini-3-flash-preview"

    def __init__(self, config: LLMConfig):
        self.config = config
        self.model_name = config.model_name or self.DEFAULT_MODEL
        # Allow api_key from config (set via Admin UI) or fall back to env var
        self.api_key = config.api_key or os.environ.get("GOOGLE_API_KEY", "")

    def _get_api_key(self) -> str:
        key = self.api_key
        if not key:
            raise RuntimeError("GOOGLE_API_KEY is not configured in backend/.env")
        return key

    async def generate(self, prompt: str, context: str = "", system_prompt: str = "") -> Dict[str, Any]:
        import httpx
        logger.info(f"GeminiLLMClient.generate called with model={self.model_name}")
        api_key = self._get_api_key()
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model_name}:generateContent?key={api_key}"
        )

        parts = []
        if system_prompt:
            parts.append(f"Instructions: {system_prompt}")
        if context:
            parts.append(f"Context:\n{context}")
        parts.append(f"Request:\n{prompt}")
        full_prompt = "\n\n".join(parts)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": full_prompt}]}],
                        "generationConfig": {
                            "temperature": self.config.temperature,
                            "maxOutputTokens": self.config.max_tokens,
                        },
                    },
                )
                response.raise_for_status()
                data = response.json()

            response_text = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})

            return {
                "response": response_text,
                "prompt_tokens": usage.get("promptTokenCount", len(full_prompt.split())),
                "completion_tokens": usage.get("candidatesTokenCount", len(response_text.split())),
                "model_name": self.model_name,
            }
        except Exception as e:
            logger.error(f"Gemini LLM error: {e}")
            raise

    async def health_check(self) -> bool:
        return bool(self.api_key)


class MockLLMClient(BaseLLMClient):

    def __init__(self, config: LLMConfig):
        self.config = config
        self.model_name = config.model_name or "mock-llm"

    async def generate(self, prompt: str, context: str = "", system_prompt: str = "") -> Dict[str, Any]:
        """Generate mock response based on prompt keywords"""
        response = ""

        if "risk" in prompt.lower():
            response = json.dumps({
                "risks": [
                    {"title": "Insufficient Access Controls", "severity": "HIGH", "framework": "NIST CSF"},
                    {"title": "Weak Encryption Standards", "severity": "MEDIUM", "framework": "ISO 27001"},
                    {"title": "Inadequate Audit Logging", "severity": "MEDIUM", "framework": "SOC2"}
                ]
            })
        elif "control" in prompt.lower():
            response = json.dumps({
                "controls": [
                    {"name": "IAM Policy Review", "effectiveness": "EFFECTIVE"},
                    {"name": "Encryption at Rest", "effectiveness": "PARTIALLY_EFFECTIVE"},
                    {"name": "Log Monitoring", "effectiveness": "INEFFECTIVE"}
                ]
            })
        else:
            response = json.dumps({"message": "Mock response generated"})

        return {
            "response": response,
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(response.split()),
            "model_name": self.model_name
        }

    async def health_check(self) -> bool:
        return True


class OllamaLLMClient(BaseLLMClient):
    """Ollama local LLM client"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.model_name = config.model_name or "llama3"
        self.host = config.ollama_host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    async def generate(self, prompt: str, context: str = "", system_prompt: str = "") -> Dict[str, Any]:
        import httpx
        logger.info(f"GeminiLLMClient.generate called with model={self.model_name}")
        full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nUser:\n{prompt}" if context else f"{system_prompt}\n\n{prompt}"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.config.temperature,
                            "num_predict": self.config.max_tokens
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "response": data.get("response", ""),
                    "prompt_tokens": data.get("prompt_eval_count", len(prompt.split())),
                    "completion_tokens": data.get("eval_count", len(data.get("response", "").split())),
                    "model_name": self.model_name
                }
        except Exception as e:
            logger.error(f"Ollama LLM error: {e}")
            raise

    async def health_check(self) -> bool:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except Exception:
            return False


class AzureLLMClient(BaseLLMClient):
    """Azure AI Agent Service client"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.endpoint = config.azure_endpoint or os.environ.get("AZURE_AI_ENDPOINT")
        self.deployment = config.azure_deployment or os.environ.get("AZURE_AI_DEPLOYMENT")
        self.model_name = config.model_name or "gpt-4"
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from azure.ai.agents import AgentsClient
                from azure.identity import DefaultAzureCredential
                self._client = AgentsClient(
                    endpoint=self.endpoint,
                    credential=DefaultAzureCredential()
                )
            except ImportError:
                logger.warning("azure-ai-agents not installed. Using fallback.")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize Azure client: {e}")
                return None
        return self._client

    async def generate(self, prompt: str, context: str = "", system_prompt: str = "") -> Dict[str, Any]:
        client = self._get_client()
        if client is None:
            return await self._generate_openai_fallback(prompt, context, system_prompt)

        try:
            agent = client.create_agent(
                model=self.deployment,
                name="risk-assessment-agent",
                instructions=system_prompt or "You are a technology risk and control assessment agent."
            )
            thread = client.create_thread()
            full_message = f"Context:\n{context}\n\nRequest:\n{prompt}" if context else prompt
            client.create_message(thread_id=thread.id, role="user", content=full_message)
            run = client.create_run(thread_id=thread.id, agent_id=agent.id)

            while run.status in ["queued", "in_progress"]:
                import asyncio
                await asyncio.sleep(0.5)
                run = client.get_run(thread_id=thread.id, run_id=run.id)

            messages = client.list_messages(thread_id=thread.id)
            response_text = ""
            for msg in messages.data:
                if msg.role == "assistant":
                    response_text = msg.content[0].text.value if msg.content else ""
                    break

            client.delete_agent(agent.id)

            return {
                "response": response_text,
                "prompt_tokens": run.usage.prompt_tokens if hasattr(run, 'usage') else len(prompt.split()),
                "completion_tokens": run.usage.completion_tokens if hasattr(run, 'usage') else len(response_text.split()),
                "model_name": self.deployment or self.model_name
            }
        except Exception as e:
            logger.error(f"Azure AI Agent error: {e}")
            return await self._generate_openai_fallback(prompt, context, system_prompt)

    async def _generate_openai_fallback(self, prompt: str, context: str, system_prompt: str) -> Dict[str, Any]:
        import httpx

        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")

        if not api_key or not self.endpoint:
            raise ValueError("Azure OpenAI credentials not configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}"})
        messages.append({"role": "user", "content": prompt})

        url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={api_version}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers={"api-key": api_key, "Content-Type": "application/json"},
                json={
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens
                }
            )
            response.raise_for_status()
            data = response.json()

            return {
                "response": data["choices"][0]["message"]["content"],
                "prompt_tokens": data["usage"]["prompt_tokens"],
                "completion_tokens": data["usage"]["completion_tokens"],
                "model_name": self.deployment or self.model_name
            }

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            return client is not None
        except Exception:
            return False


class VertexAILLMClient(BaseLLMClient):
    """Google Vertex AI client — falls back to Gemini REST if SDK unavailable."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.project = config.vertex_project or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.location = config.vertex_location or os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.model_name = config.model_name or "gemini-1.5-pro"
        self._initialized = False

    def _initialize(self):
        if self._initialized:
            return True
        try:
            import google.cloud.aiplatform as aiplatform
            aiplatform.init(project=self.project, location=self.location)
            self._initialized = True
            return True
        except ImportError:
            logger.warning("google-cloud-aiplatform not installed.")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            return False

    async def generate(self, prompt: str, context: str = "", system_prompt: str = "") -> Dict[str, Any]:
        if not self._initialize():
            return await self._generate_rest_fallback(prompt, context, system_prompt)

        try:
            from vertexai.generative_models import GenerativeModel

            model = GenerativeModel(self.model_name)
            full_prompt = ""
            if system_prompt:
                full_prompt += f"Instructions: {system_prompt}\n\n"
            if context:
                full_prompt += f"Context:\n{context}\n\n"
            full_prompt += f"Request:\n{prompt}"

            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens,
                }
            )

            response_text = response.text if hasattr(response, 'text') else str(response.candidates[0].content.parts[0].text)
            usage = response.usage_metadata if hasattr(response, 'usage_metadata') else None

            return {
                "response": response_text,
                "prompt_tokens": usage.prompt_token_count if usage else len(prompt.split()),
                "completion_tokens": usage.candidates_token_count if usage else len(response_text.split()),
                "model_name": self.model_name
            }
        except Exception as e:
            logger.error(f"Vertex AI error: {e}")
            return await self._generate_rest_fallback(prompt, context, system_prompt)

    async def _generate_rest_fallback(self, prompt: str, context: str, system_prompt: str) -> Dict[str, Any]:
        import httpx

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not configured for Vertex AI fallback")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={api_key}"

        full_prompt = ""
        if system_prompt:
            full_prompt += f"Instructions: {system_prompt}\n\n"
        if context:
            full_prompt += f"Context:\n{context}\n\n"
        full_prompt += f"Request:\n{prompt}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {
                        "temperature": self.config.temperature,
                        "maxOutputTokens": self.config.max_tokens
                    }
                }
            )
            response.raise_for_status()
            data = response.json()

            response_text = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})

            return {
                "response": response_text,
                "prompt_tokens": usage.get("promptTokenCount", len(prompt.split())),
                "completion_tokens": usage.get("candidatesTokenCount", len(response_text.split())),
                "model_name": self.model_name
            }

    async def health_check(self) -> bool:
        return self._initialize()


class KimiLLMClient(BaseLLMClient):
    """Kimi (Moonshot AI) LLM client — OpenAI-compatible API."""

    BASE_URL = "https://api.moonshot.cn/v1/chat/completions"
    DEFAULT_MODEL = "moonshot-v1-8k"

    def __init__(self, config: LLMConfig):
        self.config = config
        self.model_name = config.model_name or self.DEFAULT_MODEL
        self.api_key = config.api_key or os.environ.get("KIMI_API_KEY", "")

    async def generate(self, prompt: str, context: str = "", system_prompt: str = "") -> Dict[str, Any]:
        import httpx
        if not self.api_key:
            raise RuntimeError("KIMI_API_KEY is not configured")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}"})
        messages.append({"role": "user", "content": prompt})
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.BASE_URL,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model_name, "messages": messages, "temperature": self.config.temperature, "max_tokens": self.config.max_tokens}
            )
            response.raise_for_status()
            data = response.json()
        response_text = data["choices"][0]["message"]["content"]
        return {"response": response_text, "prompt_tokens": data["usage"]["prompt_tokens"], "completion_tokens": data["usage"]["completion_tokens"], "model_name": self.model_name}

    async def health_check(self) -> bool:
        return bool(self.api_key)


class LLMClientFactory:
    """Factory for creating LLM clients based on configuration"""

    _clients: Dict[str, BaseLLMClient] = {}
    _current_config: Optional[LLMConfig] = None

    @classmethod
    def get_client(cls, config: Optional[LLMConfig] = None) -> BaseLLMClient:
        if config is None:
            config = cls._current_config or LLMConfig()
        cls._current_config = config
        client_key = f"{config.provider}_{config.model_name}"
        if client_key not in cls._clients:
            cls._clients[client_key] = cls._create_client(config)
        return cls._clients[client_key]

    @classmethod
    def _create_client(cls, config: LLMConfig) -> BaseLLMClient:
        if config.provider == LLMProvider.MOCK:
            return MockLLMClient(config)
        elif config.provider == LLMProvider.OLLAMA:
            return OllamaLLMClient(config)
        elif config.provider == LLMProvider.AZURE:
            return AzureLLMClient(config)
        elif config.provider == LLMProvider.VERTEX_AI:
            return VertexAILLMClient(config)
        elif config.provider == LLMProvider.KIMI:
            return KimiLLMClient(config)
        elif config.provider in (LLMProvider.GEMINI, LLMProvider.ANTHROPIC, LLMProvider.OPENAI):
            # Gemini REST client handles GEMINI; for ANTHROPIC/OPENAI fallback to Gemini if no dedicated client
            return GeminiLLMClient(config)
        else:
            logger.warning(f"Unknown provider {config.provider}, falling back to Mock")
            return MockLLMClient(config)

    @classmethod
    async def load_from_db(cls) -> None:
        """Load persisted LLM config from MongoDB (if any) on startup."""
        try:
            from db import db
            from services.encryption import decrypt
            doc = await db.llm_config.find_one({"_id": "active"}, {"_id": 0})
            if not doc:
                return
            if doc.get("api_key"):
                doc["api_key"] = decrypt(doc["api_key"])
            cfg = LLMConfig(**doc)
            cls._current_config = cfg
            cls._clients.clear()
            logger.info(f"Loaded LLM config from DB: {cfg.provider.value} ({cfg.model_name})")
        except Exception as e:
            logger.warning(f"Could not load LLM config from DB: {e}")

    @classmethod
    async def save_to_db(cls, config: LLMConfig) -> None:
        """Persist LLM config to MongoDB so it survives restarts."""
        try:
            from db import db
            from services.encryption import encrypt
            doc = config.model_dump()
            if doc.get("api_key"):
                doc["api_key"] = encrypt(doc["api_key"])
            await db.llm_config.update_one(
                {"_id": "active"},
                {"$set": doc},
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Could not persist LLM config: {e}")

    @classmethod
    def update_config(cls, config: LLMConfig):
        cls._current_config = config
        cls._clients.clear()

    @classmethod
    def get_current_config(cls) -> LLMConfig:
        if cls._current_config is None:
            cls._current_config = LLMConfig()
        return cls._current_config

    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        config = cls.get_current_config()
        client = cls.get_client(config)
        is_healthy = await client.health_check()
        return {
            "provider": config.provider.value,
            "model_name": config.model_name,
            "healthy": is_healthy,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
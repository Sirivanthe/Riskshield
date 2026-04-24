import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { api } from '@/App';

const Admin = ({ user }) => {
  const [regulations, setRegulations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    framework: '',
    content: ''
  });
  
  // LLM Configuration state
  const [llmConfig, setLlmConfig] = useState(null);
  const [llmProviders, setLlmProviders] = useState([]);
  const [llmConfigForm, setLlmConfigForm] = useState({
    provider: 'EMERGENT',
    model_name: '',
    api_key: '',
    azure_endpoint: '',
    azure_deployment: '',
    vertex_project: '',
    vertex_location: '',
    ollama_host: '',
    temperature: 0.1,
    max_tokens: 4096
  });
  const [savingLlm, setSavingLlm] = useState(false);
  const [testingLlm, setTestingLlm] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [activeTab, setActiveTab] = useState('llm');
  const [switchProvider, setSwitchProvider] = useState(null); // provider object when modal open
  const [switchForm, setSwitchForm] = useState({});
  const [switching, setSwitching] = useState(false);

  // ServiceNow integration state
  const [snowConfig, setSnowConfig] = useState(null);
  const [snowForm, setSnowForm] = useState({
    instance_url: '',
    auth_type: 'basic',
    username: '',
    password: '',
    api_token: '',
    api_version: 'v2',
  });
  const [snowSaving, setSnowSaving] = useState(false);
  const [snowTesting, setSnowTesting] = useState(false);
  const [snowTestResult, setSnowTestResult] = useState(null);

  // LLM usage state
  const [usage, setUsage] = useState(null);
  const [usageDays, setUsageDays] = useState(7);
  const [usageLoading, setUsageLoading] = useState(false);

  const location = useLocation();

  useEffect(() => {
    loadData();
  }, []);

  // Sync active tab with ?tab=… query param (used by Dashboard health strip deep links)
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tab = params.get('tab');
    if (tab && ['llm', 'integrations', 'usage', 'regulations', 'system'].includes(tab)) {
      setActiveTab(tab);
    }
  }, [location.search]);

  const loadData = async () => {
    setLoading(true);
    await Promise.all([
      loadRegulations(),
      loadLlmConfig(),
      loadLlmProviders(),
      loadSnowConfig(),
    ]);
    setLoading(false);
  };

  const loadRegulations = async () => {
    try {
      const response = await api.get('/regulations');
      setRegulations(response.data);
    } catch (error) {
      console.error('Failed to load regulations:', error);
    }
  };

  const loadLlmConfig = async () => {
    try {
      const response = await api.get('/llm/config');
      setLlmConfig(response.data);
      setLlmConfigForm({
        provider: response.data.provider || 'EMERGENT',
        model_name: response.data.model_name || '',
        api_key: '',
        azure_endpoint: response.data.azure_endpoint || '',
        azure_deployment: response.data.azure_deployment || '',
        vertex_project: response.data.vertex_project || '',
        vertex_location: response.data.vertex_location || '',
        ollama_host: response.data.ollama_host || '',
        temperature: response.data.temperature || 0.1,
        max_tokens: response.data.max_tokens || 4096
      });
    } catch (error) {
      console.error('Failed to load LLM config:', error);
    }
  };

  const loadLlmProviders = async () => {
    try {
      const response = await api.get('/llm/providers');
      setLlmProviders(response.data.providers || []);
    } catch (error) {
      console.error('Failed to load LLM providers:', error);
    }
  };

  // ------ ServiceNow integration ------
  const loadSnowConfig = async () => {
    try {
      const response = await api.get('/servicenow/config');
      setSnowConfig(response.data);
      setSnowForm((f) => ({
        ...f,
        instance_url: response.data.instance_url || '',
        auth_type: response.data.auth_type || 'basic',
        username: response.data.username || '',
        // never prefill secrets
        password: '',
        api_token: '',
        api_version: response.data.api_version || 'v2',
      }));
    } catch (error) {
      console.error('Failed to load ServiceNow config:', error);
    }
  };

  const handleSaveSnow = async (e) => {
    e.preventDefault();
    setSnowSaving(true);
    setSnowTestResult(null);
    try {
      const payload = {
        instance_url: snowForm.instance_url,
        auth_type: snowForm.auth_type,
        api_version: snowForm.api_version || 'v2',
      };
      if (snowForm.auth_type === 'basic') {
        payload.username = snowForm.username;
        payload.password = snowForm.password;
      } else {
        payload.api_token = snowForm.api_token;
      }
      const res = await api.put('/servicenow/config', payload);
      setSnowConfig(res.data);
      setSnowForm((f) => ({ ...f, password: '', api_token: '' }));
      alert('ServiceNow configuration saved');
    } catch (error) {
      alert(`Save failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setSnowSaving(false);
    }
  };

  const handleTestSnow = async () => {
    setSnowTesting(true);
    setSnowTestResult(null);
    try {
      const res = await api.post('/servicenow/test');
      setSnowTestResult(res.data);
    } catch (error) {
      setSnowTestResult({ success: false, error: error.message });
    } finally {
      setSnowTesting(false);
    }
  };

  const handleDisconnectSnow = async () => {
    if (!window.confirm('Disconnect ServiceNow and clear stored credentials?')) return;
    try {
      const res = await api.delete('/servicenow/config');
      setSnowConfig(res.data);
      setSnowForm({
        instance_url: '',
        auth_type: 'basic',
        username: '',
        password: '',
        api_token: '',
        api_version: 'v2',
      });
      setSnowTestResult(null);
    } catch (error) {
      alert(`Disconnect failed: ${error.message}`);
    }
  };

  // ------ Usage & Cost ------
  const loadUsage = async (days = usageDays) => {
    setUsageLoading(true);
    try {
      const res = await api.get(`/system/llm/usage?days=${days}`);
      setUsage(res.data);
    } catch (error) {
      console.error('Failed to load usage:', error);
    } finally {
      setUsageLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab !== 'usage' || usage) return;
    let mounted = true;
    setUsageLoading(true);
    api.get(`/system/llm/usage?days=${usageDays}`)
      .then((res) => { if (mounted) setUsage(res.data); })
      .catch(() => {})
      .finally(() => { if (mounted) setUsageLoading(false); });
    return () => { mounted = false; };
  }, [activeTab, usage, usageDays]);

  const handleSaveLlmConfig = async (e) => {
    e.preventDefault();
    setSavingLlm(true);
    try {
      const response = await api.put('/llm/config', llmConfigForm);
      setLlmConfig(response.data);
      alert('LLM configuration saved successfully');
    } catch (error) {
      console.error('Failed to save LLM config:', error);
      alert('Failed to save LLM configuration');
    } finally {
      setSavingLlm(false);
    }
  };

  const handleTestLlm = async () => {
    setTestingLlm(true);
    setTestResult(null);
    try {
      const response = await api.post('/llm/test?prompt=Hello, please confirm you are working correctly for risk assessment tasks.');
      setTestResult(response.data);
    } catch (error) {
      console.error('Failed to test LLM:', error);
      setTestResult({ success: false, error: error.message });
    } finally {
      setTestingLlm(false);
    }
  };

  const startProviderSwitch = async (provider) => {
    if (llmConfig?.provider === provider.id) return;
    const fields = provider.config_fields || [];
    const suggestedModel = provider.suggested_models?.[0] || '';
    // If no extra fields needed OR only model_name (optional), do a one-click swap
    const needsModal = fields.some(
      (f) => f !== 'model_name' && ['api_key', 'azure_endpoint', 'azure_deployment',
        'vertex_project', 'vertex_location', 'ollama_host'].includes(f)
    );
    if (!needsModal) {
      setSwitching(true);
      try {
        const payload = { provider: provider.id };
        if (fields.includes('model_name') && suggestedModel) payload.model_name = suggestedModel;
        const res = await api.put('/llm/config', payload);
        setLlmConfig(res.data);
        setLlmConfigForm((f) => ({ ...f, provider: provider.id, model_name: res.data.model_name || suggestedModel }));
      } catch (e) {
        alert(`Switch failed: ${e.response?.data?.detail || e.message}`);
      } finally {
        setSwitching(false);
      }
      return;
    }
    // Open modal
    setSwitchProvider(provider);
    setSwitchForm({
      model_name: suggestedModel,
      api_key: '',
      azure_endpoint: '',
      azure_deployment: '',
      vertex_project: '',
      vertex_location: '',
      ollama_host: '',
    });
  };

  const submitProviderSwitch = async () => {
    if (!switchProvider) return;
    const fields = switchProvider.config_fields || [];
    const payload = { provider: switchProvider.id };
    fields.forEach((f) => {
      if (switchForm[f]) payload[f] = switchForm[f];
    });
    setSwitching(true);
    try {
      const res = await api.put('/llm/config', payload);
      setLlmConfig(res.data);
      setLlmConfigForm((f) => ({
        ...f,
        provider: switchProvider.id,
        model_name: res.data.model_name || switchForm.model_name || '',
        ollama_host: res.data.ollama_host || switchForm.ollama_host || '',
        azure_endpoint: res.data.azure_endpoint || switchForm.azure_endpoint || '',
        azure_deployment: res.data.azure_deployment || switchForm.azure_deployment || '',
        vertex_project: res.data.vertex_project || switchForm.vertex_project || '',
        vertex_location: res.data.vertex_location || switchForm.vertex_location || '',
      }));
      setSwitchProvider(null);
    } catch (e) {
      alert(`Switch failed: ${e.response?.data?.detail || e.message}`);
    } finally {
      setSwitching(false);
    }
  };

  const clearStoredApiKey = async () => {
    if (!window.confirm('Remove the stored API key?')) return;
    try {
      const res = await api.delete('/llm/config/api-key');
      setLlmConfig(res.data);
    } catch (e) {
      alert(`Failed to clear key: ${e.message}`);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.framework || !formData.content) {
      alert('Please fill in all fields');
      return;
    }

    setUploading(true);
    try {
      await api.post('/regulations/upload', formData);
      alert('Regulation uploaded successfully');
      setFormData({ name: '', framework: '', content: '' });
      loadRegulations();
    } catch (error) {
      console.error('Failed to upload regulation:', error);
      alert('Failed to upload regulation');
    } finally {
      setUploading(false);
    }
  };

  const handleUploadFile = async (file) => {
    if (!file) return;
    if (!formData.name || !formData.framework) {
      alert('Please set Regulation Name and Framework before picking a file.');
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('name', formData.name);
      fd.append('framework', formData.framework);
      const res = await api.post('/regulations/upload-file', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      alert(`Regulation uploaded. Extracted ${res.data.char_count} characters.`);
      setFormData({ name: '', framework: '', content: '' });
      loadRegulations();
    } catch (error) {
      const msg = error.response?.data?.detail || error.message;
      alert(`Upload failed: ${msg}`);
    } finally {
      setUploading(false);
    }
  };

  const handleReanalyze = async (reg) => {
    try {
      const res = await api.post(`/regulations/${reg.id}/reanalyze`);
      alert(
        `${reg.name} re-analyzed:\n` +
          `Requirements: ${res.data.total_requirements}\n` +
          `Compliance score: ${res.data.compliance_score}%\n` +
          `Gaps: ${res.data.gaps.length}\n` +
          `Parser: ${res.data.parser_used}`
      );
    } catch (error) {
      alert(`Re-analyze failed: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteRegulation = async (reg) => {
    if (!window.confirm(`Delete regulation "${reg.name}"?`)) return;
    try {
      await api.delete(`/regulations/${reg.id}`);
      loadRegulations();
    } catch (error) {
      alert(`Delete failed: ${error.response?.data?.detail || error.message}`);
    }
  };

  if (user.role !== 'LOD2_USER' && user.role !== 'ADMIN') {
    return (
      <div className="page-content">
        <div className="card">
          <div className="empty-state">
            <h3 className="empty-title">Access Denied</h3>
            <p className="empty-description">Only LOD2 users and Admins can access admin features</p>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="page-content">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div data-testid="admin-page">
      <div className="page-header">
        <h1 className="page-title" data-testid="admin-title">Admin Settings</h1>
        <p className="page-subtitle">Configure LLM providers, manage regulatory documents, and system settings</p>
      </div>

      <div className="page-content">
        {/* Tabs */}
        <div className="tabs mb-6">
          <div className="tab-list">
            <button
              className={`tab-button ${activeTab === 'llm' ? 'active' : ''}`}
              onClick={() => setActiveTab('llm')}
              data-testid="tab-llm"
            >
              LLM Configuration
            </button>
            <button
              className={`tab-button ${activeTab === 'integrations' ? 'active' : ''}`}
              onClick={() => setActiveTab('integrations')}
              data-testid="tab-integrations"
            >
              Integrations
            </button>
            <button
              className={`tab-button ${activeTab === 'usage' ? 'active' : ''}`}
              onClick={() => setActiveTab('usage')}
              data-testid="tab-usage"
            >
              Usage & Cost
            </button>
            <button
              className={`tab-button ${activeTab === 'regulations' ? 'active' : ''}`}
              onClick={() => setActiveTab('regulations')}
              data-testid="tab-regulations"
            >
              Regulations
            </button>
            <button
              className={`tab-button ${activeTab === 'system' ? 'active' : ''}`}
              onClick={() => setActiveTab('system')}
              data-testid="tab-system"
            >
              System Info
            </button>
          </div>
        </div>

        {/* LLM Configuration Tab */}
        {activeTab === 'llm' && (
          <div className="grid grid-2 gap-6">
            {/* LLM Config Form */}
            <div className="card">
              <h2 className="card-title mb-4">LLM Provider Configuration</h2>
              <form onSubmit={handleSaveLlmConfig} data-testid="llm-config-form">
                <div className="form-group">
                  <label className="form-label">Provider</label>
                  <select
                    className="form-select"
                    value={llmConfigForm.provider}
                    onChange={(e) => setLlmConfigForm({ ...llmConfigForm, provider: e.target.value })}
                    data-testid="llm-provider-select"
                  >
                    {llmProviders.map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                  <div className="form-helper">
                    {llmProviders.find(p => p.id === llmConfigForm.provider)?.description}
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Model Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={llmConfigForm.model_name}
                    onChange={(e) => setLlmConfigForm({ ...llmConfigForm, model_name: e.target.value })}
                    placeholder="e.g., gpt-4, llama3, gemini-1.5-pro"
                    data-testid="llm-model-name-input"
                  />
                </div>

                {/* API Key for Anthropic / OpenAI / Gemini */}
                {['ANTHROPIC', 'OPENAI', 'GEMINI'].includes(llmConfigForm.provider) && (
                  <div className="form-group">
                    <label className="form-label">API Key</label>
                    <input
                      type="password"
                      className="form-input"
                      value={llmConfigForm.api_key}
                      onChange={(e) => setLlmConfigForm({ ...llmConfigForm, api_key: e.target.value })}
                      placeholder={llmConfig?.api_key_set ? `•••• stored (ends in ${llmConfig.api_key_last4 || '****'})` : 'Paste your provider API key'}
                      data-testid="llm-api-key-input"
                      autoComplete="off"
                    />
                    <div className="form-helper">
                      Stored securely in the RiskShield database. Never returned by the API.
                      {llmConfig?.api_key_set && (
                        <>
                          {' · '}
                          <button type="button" className="link-button" onClick={clearStoredApiKey} data-testid="clear-api-key-link">
                            Remove stored key
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {/* Azure Fields */}
                {llmConfigForm.provider === 'AZURE' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Azure Endpoint</label>
                      <input
                        type="text"
                        className="form-input"
                        value={llmConfigForm.azure_endpoint}
                        onChange={(e) => setLlmConfigForm({ ...llmConfigForm, azure_endpoint: e.target.value })}
                        placeholder="https://your-resource.openai.azure.com/"
                        data-testid="azure-endpoint-input"
                      />
                      <div className="form-helper">Your Azure AI Services endpoint URL</div>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Azure Deployment</label>
                      <input
                        type="text"
                        className="form-input"
                        value={llmConfigForm.azure_deployment}
                        onChange={(e) => setLlmConfigForm({ ...llmConfigForm, azure_deployment: e.target.value })}
                        placeholder="gpt-4-deployment"
                        data-testid="azure-deployment-input"
                      />
                      <div className="form-helper">Your Azure OpenAI deployment name</div>
                    </div>
                  </>
                )}

                {/* Vertex AI Fields */}
                {llmConfigForm.provider === 'VERTEX_AI' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Google Cloud Project</label>
                      <input
                        type="text"
                        className="form-input"
                        value={llmConfigForm.vertex_project}
                        onChange={(e) => setLlmConfigForm({ ...llmConfigForm, vertex_project: e.target.value })}
                        placeholder="your-gcp-project-id"
                        data-testid="vertex-project-input"
                      />
                      <div className="form-helper">Your GCP project ID with Vertex AI enabled</div>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Location</label>
                      <input
                        type="text"
                        className="form-input"
                        value={llmConfigForm.vertex_location}
                        onChange={(e) => setLlmConfigForm({ ...llmConfigForm, vertex_location: e.target.value })}
                        placeholder="us-central1"
                        data-testid="vertex-location-input"
                      />
                      <div className="form-helper">GCP region for Vertex AI (e.g., us-central1, europe-west4)</div>
                    </div>
                  </>
                )}

                {/* Ollama Fields */}
                {llmConfigForm.provider === 'OLLAMA' && (
                  <div className="form-group">
                    <label className="form-label">Ollama Host</label>
                    <input
                      type="text"
                      className="form-input"
                      value={llmConfigForm.ollama_host}
                      onChange={(e) => setLlmConfigForm({ ...llmConfigForm, ollama_host: e.target.value })}
                      placeholder="http://localhost:11434"
                      data-testid="ollama-host-input"
                    />
                    <div className="form-helper">Ollama server URL (local or remote)</div>
                  </div>
                )}

                <div className="grid grid-2 gap-4">
                  <div className="form-group">
                    <label className="form-label">Temperature</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      className="form-input"
                      value={llmConfigForm.temperature}
                      onChange={(e) => setLlmConfigForm({ ...llmConfigForm, temperature: parseFloat(e.target.value) })}
                      data-testid="llm-temperature-input"
                    />
                    <div className="form-helper">0 = deterministic, 2 = creative</div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Max Tokens</label>
                    <input
                      type="number"
                      min="100"
                      max="32000"
                      className="form-input"
                      value={llmConfigForm.max_tokens}
                      onChange={(e) => setLlmConfigForm({ ...llmConfigForm, max_tokens: parseInt(e.target.value) })}
                      data-testid="llm-max-tokens-input"
                    />
                    <div className="form-helper">Maximum response length</div>
                  </div>
                </div>

                <div className="flex gap-2 mt-4">
                  <button
                    type="submit"
                    className="btn btn-primary flex-1"
                    disabled={savingLlm}
                    data-testid="save-llm-config-button"
                  >
                    {savingLlm ? 'Saving...' : 'Save Configuration'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={handleTestLlm}
                    disabled={testingLlm}
                    data-testid="test-llm-button"
                  >
                    {testingLlm ? 'Testing...' : 'Test Connection'}
                  </button>
                </div>
              </form>

              {/* Test Result */}
              {testResult && (
                <div 
                  className="mt-4 p-4 rounded-lg"
                  style={{ 
                    background: testResult.success ? '#f0fdf4' : '#fef2f2',
                    border: `1px solid ${testResult.success ? '#86efac' : '#fecaca'}`
                  }}
                  data-testid="llm-test-result"
                >
                  <div style={{ fontWeight: '600', color: testResult.success ? '#166534' : '#991b1b', marginBottom: '8px' }}>
                    {testResult.success ? 'Connection Successful' : 'Connection Failed'}
                  </div>
                  {testResult.success ? (
                    <>
                      <div style={{ fontSize: '13px', color: '#334155', marginBottom: '8px' }}>
                        Provider: {testResult.provider} | Model: {testResult.model}
                      </div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>
                        Tokens: {testResult.tokens?.prompt} prompt, {testResult.tokens?.completion} completion
                      </div>
                      {testResult.response && (
                        <div style={{ fontSize: '13px', color: '#334155', marginTop: '8px', padding: '8px', background: '#fff', borderRadius: '4px' }}>
                          <strong>Response:</strong> {testResult.response.substring(0, 300)}...
                        </div>
                      )}
                    </>
                  ) : (
                    <div style={{ fontSize: '13px', color: '#991b1b' }}>
                      Error: {testResult.error}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Quick Switch + Provider Info */}
            <div className="card">
              <div className="flex justify-between items-center mb-4">
                <h2 className="card-title">Quick Switch LLM</h2>
                {llmConfig && (
                  <span className="badge" style={{ background: '#dbeafe', color: '#1e40af' }} data-testid="active-llm-badge">
                    Active: {llmConfig.provider} · {llmConfig.model_name}
                  </span>
                )}
              </div>
              <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
                Click any provider to switch. If it requires credentials you'll be asked for your key — nothing is hardcoded.
              </p>

              <div className="space-y-3" data-testid="provider-switch-list">
                {llmProviders.map(provider => {
                  const isActive = llmConfig?.provider === provider.id;
                  const needsCreds = provider.requires_credentials;
                  return (
                    <button
                      key={provider.id}
                      type="button"
                      onClick={() => startProviderSwitch(provider)}
                      disabled={isActive || switching}
                      data-testid={`switch-provider-${provider.id}`}
                      style={{
                        width: '100%',
                        textAlign: 'left',
                        padding: '14px 16px',
                        background: isActive ? '#eff6ff' : '#f8fafc',
                        borderRadius: '10px',
                        border: `2px solid ${isActive ? '#3b82f6' : '#e2e8f0'}`,
                        cursor: isActive ? 'default' : 'pointer',
                        transition: 'transform 0.12s, border-color 0.12s',
                        opacity: switching && !isActive ? 0.6 : 1,
                      }}
                      onMouseOver={(e) => { if (!isActive) e.currentTarget.style.borderColor = '#94a3b8'; }}
                      onMouseOut={(e) => { if (!isActive) e.currentTarget.style.borderColor = '#e2e8f0'; }}
                    >
                      <div className="flex justify-between items-start" style={{ marginBottom: '4px' }}>
                        <div style={{ fontWeight: '600', color: '#0f172a' }}>{provider.name}</div>
                        <div className="flex gap-2 items-center">
                          {needsCreds && (
                            <span style={{ fontSize: '11px', color: '#b45309', background: '#fef3c7', padding: '2px 6px', borderRadius: '4px' }}>
                              Needs key
                            </span>
                          )}
                          {isActive ? (
                            <span className="badge" style={{ background: '#dbeafe', color: '#1e40af' }}>Active</span>
                          ) : (
                            <span style={{ fontSize: '12px', color: '#3b82f6', fontWeight: 600 }}>Switch →</span>
                          )}
                        </div>
                      </div>
                      <div style={{ fontSize: '13px', color: '#64748b' }}>{provider.description}</div>
                      {provider.suggested_models?.length > 0 && (
                        <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px' }}>
                          Models: {provider.suggested_models.slice(0, 3).join(' · ')}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Current Config Summary */}
              {llmConfig && (
                <div className="mt-4 p-4" style={{ background: '#f0fdf4', borderRadius: '8px', border: '1px solid #86efac' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#166534', marginBottom: '12px' }}>Current Active Configuration</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '13px', color: '#334155' }}>
                    <div>Provider: <strong>{llmConfig.provider}</strong></div>
                    <div>Model: <strong>{llmConfig.model_name}</strong></div>
                    <div>Temperature: <strong>{llmConfig.temperature}</strong></div>
                    <div>Max Tokens: <strong>{llmConfig.max_tokens}</strong></div>
                    {llmConfig.api_key_set && (
                      <div style={{ gridColumn: 'span 2' }}>
                        API Key: <strong>•••• {llmConfig.api_key_last4}</strong>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Provider switch modal */}
        {switchProvider && (
          <div
            role="dialog"
            data-testid="switch-modal"
            style={{
              position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.55)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '20px',
            }}
            onClick={(e) => { if (e.target === e.currentTarget) setSwitchProvider(null); }}
          >
            <div style={{ background: '#fff', borderRadius: '12px', padding: '24px', width: '100%', maxWidth: '480px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a', marginBottom: '4px' }}>
                Switch to {switchProvider.name}
              </h3>
              <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
                {switchProvider.description}
              </p>

              {switchProvider.config_fields?.includes('api_key') && (
                <div className="form-group">
                  <label className="form-label">API Key</label>
                  <input
                    type="password"
                    className="form-input"
                    autoFocus
                    autoComplete="off"
                    value={switchForm.api_key || ''}
                    onChange={(e) => setSwitchForm({ ...switchForm, api_key: e.target.value })}
                    placeholder="Paste your API key"
                    data-testid="switch-modal-api-key"
                  />
                  <div className="form-helper">Stored in the RiskShield database. Never exposed via the API.</div>
                </div>
              )}
              {switchProvider.config_fields?.includes('model_name') && (
                <div className="form-group">
                  <label className="form-label">Model</label>
                  {switchProvider.suggested_models?.length > 0 ? (
                    <select
                      className="form-select"
                      value={switchForm.model_name || ''}
                      onChange={(e) => setSwitchForm({ ...switchForm, model_name: e.target.value })}
                      data-testid="switch-modal-model"
                    >
                      {switchProvider.suggested_models.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      className="form-input"
                      value={switchForm.model_name || ''}
                      onChange={(e) => setSwitchForm({ ...switchForm, model_name: e.target.value })}
                      placeholder="e.g., llama3:70b"
                      data-testid="switch-modal-model-input"
                    />
                  )}
                </div>
              )}
              {switchProvider.config_fields?.includes('ollama_host') && (
                <div className="form-group">
                  <label className="form-label">Ollama Host</label>
                  <input
                    className="form-input"
                    value={switchForm.ollama_host || ''}
                    onChange={(e) => setSwitchForm({ ...switchForm, ollama_host: e.target.value })}
                    placeholder="http://localhost:11434"
                    data-testid="switch-modal-ollama"
                  />
                </div>
              )}
              {switchProvider.config_fields?.includes('azure_endpoint') && (
                <>
                  <div className="form-group">
                    <label className="form-label">Azure Endpoint</label>
                    <input
                      className="form-input"
                      value={switchForm.azure_endpoint || ''}
                      onChange={(e) => setSwitchForm({ ...switchForm, azure_endpoint: e.target.value })}
                      placeholder="https://your-resource.openai.azure.com/"
                      data-testid="switch-modal-azure-endpoint"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Azure Deployment</label>
                    <input
                      className="form-input"
                      value={switchForm.azure_deployment || ''}
                      onChange={(e) => setSwitchForm({ ...switchForm, azure_deployment: e.target.value })}
                      placeholder="gpt-4-deployment"
                      data-testid="switch-modal-azure-deployment"
                    />
                  </div>
                </>
              )}
              {switchProvider.config_fields?.includes('vertex_project') && (
                <>
                  <div className="form-group">
                    <label className="form-label">GCP Project</label>
                    <input
                      className="form-input"
                      value={switchForm.vertex_project || ''}
                      onChange={(e) => setSwitchForm({ ...switchForm, vertex_project: e.target.value })}
                      placeholder="your-gcp-project-id"
                      data-testid="switch-modal-vertex-project"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Location</label>
                    <input
                      className="form-input"
                      value={switchForm.vertex_location || ''}
                      onChange={(e) => setSwitchForm({ ...switchForm, vertex_location: e.target.value })}
                      placeholder="us-central1"
                      data-testid="switch-modal-vertex-location"
                    />
                  </div>
                </>
              )}

              <div className="flex gap-2 mt-4 justify-end">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setSwitchProvider(null)}
                  data-testid="switch-modal-cancel"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={switching || (switchProvider.config_fields?.includes('api_key') && !switchForm.api_key)}
                  onClick={submitProviderSwitch}
                  data-testid="switch-modal-save"
                >
                  {switching ? 'Switching...' : `Use ${switchProvider.name}`}
                </button>
              </div>
            </div>
          </div>
        )}


        {/* Integrations Tab */}
        {activeTab === 'integrations' && (
          <div className="grid grid-2 gap-6" data-testid="integrations-panel">
            {/* ServiceNow */}
            <div className="card">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h2 className="card-title">ServiceNow</h2>
                  <p style={{ fontSize: '13px', color: '#64748b' }}>
                    Sync issues, control deficiencies and remediation tickets with your ServiceNow instance. Use either
                    Basic Auth (username + password) or an API token (Bearer). Nothing is hardcoded.
                  </p>
                </div>
                <span
                  className="badge"
                  data-testid="snow-status-badge"
                  style={{
                    background: snowConfig?.mode === 'live' ? '#dcfce7' : '#fef3c7',
                    color: snowConfig?.mode === 'live' ? '#166534' : '#92400e',
                  }}
                >
                  {snowConfig?.mode === 'live' ? 'Connected' : 'Not connected (Mock)'}
                </span>
              </div>

              <form onSubmit={handleSaveSnow} data-testid="snow-form">
                <div className="form-group">
                  <label className="form-label">Instance URL</label>
                  <input
                    type="url"
                    className="form-input"
                    value={snowForm.instance_url}
                    onChange={(e) => setSnowForm({ ...snowForm, instance_url: e.target.value })}
                    placeholder="https://your-instance.service-now.com"
                    data-testid="snow-instance-url"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Authentication Method</label>
                  <div
                    style={{
                      display: 'inline-flex',
                      background: '#f1f5f9',
                      padding: '4px',
                      borderRadius: '10px',
                      gap: '4px',
                    }}
                    data-testid="snow-auth-toggle"
                  >
                    <button
                      type="button"
                      onClick={() => setSnowForm({ ...snowForm, auth_type: 'basic' })}
                      data-testid="snow-auth-basic"
                      style={{
                        padding: '8px 16px',
                        borderRadius: '8px',
                        fontSize: '13px',
                        fontWeight: 600,
                        background: snowForm.auth_type === 'basic' ? '#fff' : 'transparent',
                        color: snowForm.auth_type === 'basic' ? '#0f172a' : '#64748b',
                        boxShadow: snowForm.auth_type === 'basic' ? '0 1px 2px rgba(15,23,42,0.08)' : 'none',
                        border: 'none', cursor: 'pointer',
                      }}
                    >
                      Basic Auth (username + password)
                    </button>
                    <button
                      type="button"
                      onClick={() => setSnowForm({ ...snowForm, auth_type: 'token' })}
                      data-testid="snow-auth-token"
                      style={{
                        padding: '8px 16px',
                        borderRadius: '8px',
                        fontSize: '13px',
                        fontWeight: 600,
                        background: snowForm.auth_type === 'token' ? '#fff' : 'transparent',
                        color: snowForm.auth_type === 'token' ? '#0f172a' : '#64748b',
                        boxShadow: snowForm.auth_type === 'token' ? '0 1px 2px rgba(15,23,42,0.08)' : 'none',
                        border: 'none', cursor: 'pointer',
                      }}
                    >
                      API Token (Bearer)
                    </button>
                  </div>
                </div>

                {snowForm.auth_type === 'basic' ? (
                  <>
                    <div className="form-group">
                      <label className="form-label">Username</label>
                      <input
                        type="text"
                        className="form-input"
                        value={snowForm.username}
                        onChange={(e) => setSnowForm({ ...snowForm, username: e.target.value })}
                        placeholder="svc-riskshield"
                        data-testid="snow-username"
                        autoComplete="off"
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Password</label>
                      <input
                        type="password"
                        className="form-input"
                        value={snowForm.password}
                        onChange={(e) => setSnowForm({ ...snowForm, password: e.target.value })}
                        placeholder={snowConfig?.password_set ? '•••• stored' : 'Password'}
                        data-testid="snow-password"
                        autoComplete="new-password"
                      />
                    </div>
                  </>
                ) : (
                  <div className="form-group">
                    <label className="form-label">API Token</label>
                    <input
                      type="password"
                      className="form-input"
                      value={snowForm.api_token}
                      onChange={(e) => setSnowForm({ ...snowForm, api_token: e.target.value })}
                      placeholder={snowConfig?.api_token_set ? `•••• stored (ends in ${snowConfig.api_token_last4 || '****'})` : 'Paste your API token'}
                      data-testid="snow-api-token"
                      autoComplete="off"
                    />
                    <div className="form-helper">
                      Generate a token in ServiceNow: System OAuth → Application Registry.
                    </div>
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">API Version</label>
                  <input
                    type="text"
                    className="form-input"
                    value={snowForm.api_version}
                    onChange={(e) => setSnowForm({ ...snowForm, api_version: e.target.value })}
                    placeholder="v2"
                    data-testid="snow-api-version"
                  />
                </div>

                <div className="flex gap-2">
                  <button type="submit" className="btn btn-primary" disabled={snowSaving} data-testid="snow-save-btn">
                    {snowSaving ? 'Saving...' : 'Save & Connect'}
                  </button>
                  <button type="button" className="btn btn-outline" onClick={handleTestSnow} disabled={snowTesting || !snowConfig?.configured} data-testid="snow-test-btn">
                    {snowTesting ? 'Testing...' : 'Test Connection'}
                  </button>
                  {snowConfig?.configured && (
                    <button type="button" className="btn btn-outline" onClick={handleDisconnectSnow} data-testid="snow-disconnect-btn" style={{ color: '#b91c1c', borderColor: '#fca5a5' }}>
                      Disconnect
                    </button>
                  )}
                </div>
              </form>

              {snowTestResult && (
                <div
                  className="mt-4 p-3"
                  data-testid="snow-test-result"
                  style={{
                    background: snowTestResult.success ? '#dcfce7' : '#fee2e2',
                    color: snowTestResult.success ? '#166534' : '#991b1b',
                    borderRadius: '8px',
                    fontSize: '13px',
                  }}
                >
                  {snowTestResult.success
                    ? `Connection OK (HTTP ${snowTestResult.status_code}, mode: ${snowTestResult.mode})`
                    : `Connection failed: ${snowTestResult.error || snowTestResult.message || 'unknown error'}`}
                </div>
              )}
            </div>

            {/* Side card — current status + hints */}
            <div className="card">
              <h2 className="card-title mb-3">Current Status</h2>
              <div style={{ fontSize: '13px', color: '#334155', display: 'grid', gap: '8px' }}>
                <div>Mode: <strong>{snowConfig?.mode || 'mock'}</strong></div>
                <div>Instance: <strong>{snowConfig?.instance_url || '—'}</strong></div>
                <div>Auth Type: <strong>{snowConfig?.auth_type || '—'}</strong></div>
                {snowConfig?.auth_type === 'basic' && (
                  <div>Username: <strong>{snowConfig?.username || '—'}</strong></div>
                )}
                {snowConfig?.auth_type === 'token' && snowConfig?.api_token_set && (
                  <div>Token: <strong>•••• {snowConfig.api_token_last4}</strong></div>
                )}
              </div>

              <div className="mt-4 p-3" style={{ background: '#eff6ff', borderRadius: '8px', fontSize: '12px', color: '#1e3a8a' }}>
                While disconnected, ServiceNow operations (issue sync, incident creation, bulk import)
                continue to run in MOCK mode for development. Saving valid credentials flips the
                connector to LIVE automatically.
              </div>
            </div>
          </div>
        )}



        {/* Usage & Cost Tab */}
        {activeTab === 'usage' && (
          <div data-testid="usage-panel">
            <div className="card">
              <div className="flex justify-between items-center mb-4">
                <h2 className="card-title">LLM Usage & Cost</h2>
                <div className="flex gap-2 items-center">
                  <select
                    className="form-select"
                    style={{ width: 'auto' }}
                    value={usageDays}
                    onChange={(e) => { const d = parseInt(e.target.value, 10); setUsageDays(d); loadUsage(d); }}
                    data-testid="usage-period"
                  >
                    <option value={1}>Last 24 hours</option>
                    <option value={7}>Last 7 days</option>
                    <option value={30}>Last 30 days</option>
                    <option value={90}>Last 90 days</option>
                  </select>
                  <button className="btn btn-outline" onClick={() => loadUsage(usageDays)} disabled={usageLoading} data-testid="usage-refresh">
                    {usageLoading ? 'Loading...' : 'Refresh'}
                  </button>
                </div>
              </div>

              {!usage ? (
                <p style={{ color: '#64748b' }}>Loading usage metrics...</p>
              ) : usage.totals.calls === 0 ? (
                <p style={{ color: '#64748b' }}>No LLM calls recorded in the selected period.</p>
              ) : (
                <>
                  <div className="grid grid-4 gap-3 mb-6">
                    <div style={{ padding: '14px', background: '#f8fafc', borderRadius: '10px' }}>
                      <div style={{ fontSize: '11px', color: '#64748b', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Total Calls</div>
                      <div style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a' }} data-testid="usage-calls">
                        {usage.totals.calls}
                      </div>
                    </div>
                    <div style={{ padding: '14px', background: '#f8fafc', borderRadius: '10px' }}>
                      <div style={{ fontSize: '11px', color: '#64748b', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Total Tokens</div>
                      <div style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a' }} data-testid="usage-tokens">
                        {usage.totals.total_tokens.toLocaleString()}
                      </div>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>
                        {usage.totals.prompt_tokens.toLocaleString()} prompt · {usage.totals.completion_tokens.toLocaleString()} completion
                      </div>
                    </div>
                    <div style={{ padding: '14px', background: '#ecfdf5', borderRadius: '10px', border: '1px solid #a7f3d0' }}>
                      <div style={{ fontSize: '11px', color: '#166534', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Estimated Cost</div>
                      <div style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a' }} data-testid="usage-cost">
                        ${usage.totals.cost_usd.toFixed(4)}
                      </div>
                    </div>
                    <div style={{ padding: '14px', background: '#f8fafc', borderRadius: '10px' }}>
                      <div style={{ fontSize: '11px', color: '#64748b', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Avg Latency</div>
                      <div style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a' }}>
                        {(usage.totals.avg_latency_ms / 1000).toFixed(1)}s
                      </div>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>
                        {usage.totals.successful} ok · {usage.totals.failed} failed
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-2 gap-6">
                    <div>
                      <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a', marginBottom: '10px' }}>By Model</h3>
                      <table className="w-full" style={{ fontSize: '13px' }}>
                        <thead>
                          <tr style={{ color: '#64748b', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                            <th style={{ padding: '6px 0' }}>Model</th>
                            <th style={{ textAlign: 'right' }}>Calls</th>
                            <th style={{ textAlign: 'right' }}>Tokens</th>
                            <th style={{ textAlign: 'right' }}>Cost</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(usage.by_model).map(([m, v]) => (
                            <tr key={m} style={{ borderBottom: '1px solid #f1f5f9' }} data-testid={`usage-model-${m}`}>
                              <td style={{ padding: '8px 0', fontWeight: 500 }}>{m}</td>
                              <td style={{ textAlign: 'right' }}>{v.calls}</td>
                              <td style={{ textAlign: 'right' }}>{v.tokens.toLocaleString()}</td>
                              <td style={{ textAlign: 'right', color: '#166534', fontWeight: 600 }}>${v.cost_usd.toFixed(4)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div>
                      <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a', marginBottom: '10px' }}>By Endpoint (Agent)</h3>
                      <table className="w-full" style={{ fontSize: '13px' }}>
                        <thead>
                          <tr style={{ color: '#64748b', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                            <th style={{ padding: '6px 0' }}>Endpoint</th>
                            <th style={{ textAlign: 'right' }}>Calls</th>
                            <th style={{ textAlign: 'right' }}>Tokens</th>
                            <th style={{ textAlign: 'right' }}>Cost</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(usage.by_endpoint).map(([e, v]) => (
                            <tr key={e} style={{ borderBottom: '1px solid #f1f5f9' }} data-testid={`usage-endpoint-${e}`}>
                              <td style={{ padding: '8px 0', fontWeight: 500 }}>{e}</td>
                              <td style={{ textAlign: 'right' }}>{v.calls}</td>
                              <td style={{ textAlign: 'right' }}>{v.tokens.toLocaleString()}</td>
                              <td style={{ textAlign: 'right', color: '#166534', fontWeight: 600 }}>${v.cost_usd.toFixed(4)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {usage.by_day.length > 0 && (
                    <div className="mt-6">
                      <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a', marginBottom: '10px' }}>Daily Trend</h3>
                      <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px', height: '120px', padding: '8px', background: '#f8fafc', borderRadius: '10px' }}>
                        {usage.by_day.map((d) => {
                          const maxCost = Math.max(...usage.by_day.map((x) => x.cost_usd), 0.0001);
                          const h = Math.max((d.cost_usd / maxCost) * 100, 4);
                          return (
                            <div
                              key={d.day}
                              style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}
                              title={`${d.day} · ${d.calls} calls · $${d.cost_usd.toFixed(4)}`}
                              data-testid={`usage-day-${d.day}`}
                            >
                              <div style={{ width: '100%', height: `${h}%`, background: '#10b981', borderRadius: '4px 4px 0 0' }} />
                              <div style={{ fontSize: '10px', color: '#64748b', marginTop: '4px' }}>{d.day.slice(5)}</div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </>
              )}

              <div className="mt-4 p-3" style={{ background: '#fef3c7', borderRadius: '8px', fontSize: '12px', color: '#92400e' }}>
                Cost estimates use approximate per-1k-token rates ($0.0015 prompt, $0.002 completion). Actual invoices from providers may differ.
              </div>
            </div>
          </div>
        )}


        {/* Regulations Tab */}
        {activeTab === 'regulations' && (
          <div className="grid grid-2 gap-6">
            {/* Upload Form */}
            <div className="card">
              <h2 className="card-title mb-4">Upload Regulation</h2>
              <form onSubmit={handleUpload} data-testid="regulation-upload-form">
                <div className="form-group">
                  <label className="form-label">Regulation Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="NIST Cybersecurity Framework v1.1"
                    data-testid="regulation-name-input"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Framework</label>
                  <select
                    className="form-select"
                    value={formData.framework}
                    onChange={(e) => setFormData({ ...formData, framework: e.target.value })}
                    data-testid="regulation-framework-select"
                  >
                    <option value="">Select framework</option>
                    <option value="NIST CSF">NIST CSF</option>
                    <option value="ISO 27001">ISO 27001</option>
                    <option value="SOC2">SOC2</option>
                    <option value="PCI-DSS">PCI-DSS</option>
                    <option value="GDPR">GDPR</option>
                    <option value="Basel III">Basel III</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Content</label>
                  <textarea
                    className="form-textarea"
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    placeholder="Paste regulation content or requirements..."
                    style={{ minHeight: '200px' }}
                    data-testid="regulation-content-textarea"
                  ></textarea>
                  <div className="form-helper">Or upload a PDF/TXT — content will be extracted and indexed automatically.</div>
                </div>

                <div className="flex gap-2">
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={uploading}
                    data-testid="upload-regulation-button"
                  >
                    {uploading ? 'Uploading...' : 'Upload (pasted text)'}
                  </button>
                  <label
                    className="btn btn-outline"
                    style={{ margin: 0, cursor: uploading ? 'not-allowed' : 'pointer' }}
                    data-testid="upload-regulation-file-label"
                  >
                    Upload PDF / TXT
                    <input
                      type="file"
                      accept=".pdf,.txt,.md"
                      className="hidden"
                      disabled={uploading}
                      onChange={(e) => handleUploadFile(e.target.files?.[0])}
                      data-testid="upload-regulation-file-input"
                    />
                  </label>
                </div>
              </form>
            </div>

            {/* Regulations List */}
            <div className="card">
              <h2 className="card-title mb-4">Uploaded Regulations ({regulations.length})</h2>
              {regulations.length > 0 ? (
                <div className="space-y-3" data-testid="regulations-list" style={{ maxHeight: '500px', overflowY: 'auto' }}>
                  {regulations.map((reg) => (
                    <div
                      key={reg.id}
                      style={{
                        padding: '16px',
                        background: '#f8fafc',
                        borderRadius: '8px',
                        border: '1px solid #e2e8f0'
                      }}
                      data-testid={`regulation-item-${reg.id}`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div style={{ fontWeight: '600', color: '#0f172a' }}>{reg.name}</div>
                        <span className="badge" style={{ background: '#eff6ff', color: '#1e40af' }}>{reg.framework}</span>
                      </div>
                      <div style={{ fontSize: '13px', color: '#64748b' }}>
                        Uploaded: {new Date(reg.uploaded_at).toLocaleDateString()}
                      </div>
                      <div style={{ fontSize: '13px', color: '#64748b' }}>
                        Chunks: {reg.chunk_count} | Ready for RAG
                      </div>
                      <div className="flex gap-2 mt-3">
                        <button
                          type="button"
                          className="btn btn-outline"
                          onClick={() => handleReanalyze(reg)}
                          data-testid={`reanalyze-${reg.id}`}
                          style={{ fontSize: '12px', padding: '6px 12px' }}
                        >
                          Re-analyze
                        </button>
                        <button
                          type="button"
                          className="btn btn-outline"
                          onClick={() => handleDeleteRegulation(reg)}
                          data-testid={`delete-reg-${reg.id}`}
                          style={{ fontSize: '12px', padding: '6px 12px', color: '#b91c1c', borderColor: '#fca5a5' }}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state" style={{ padding: '40px 20px' }}>
                  <p className="text-gray text-sm">No regulations uploaded yet</p>
                  <p className="text-gray text-xs mt-2">Upload regulatory documents to enable AI-powered compliance checks</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* System Info Tab */}
        {activeTab === 'system' && (
          <div className="card" data-testid="system-info-card">
            <h2 className="card-title mb-4">System Information</h2>
            <div className="grid grid-3 gap-4 mb-6">
              <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px' }}>
                <div className="text-xs text-gray mb-1">Platform Version</div>
                <div className="font-semibold">RiskShield v2.0.0</div>
              </div>
              <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px' }}>
                <div className="text-xs text-gray mb-1">Active LLM Provider</div>
                <div className="font-semibold">{llmConfig?.provider || 'Not configured'}</div>
              </div>
              <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px' }}>
                <div className="text-xs text-gray mb-1">Active Model</div>
                <div className="font-semibold">{llmConfig?.model_name || 'Not configured'}</div>
              </div>
              <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px' }}>
                <div className="text-xs text-gray mb-1">Vector Store</div>
                <div className="font-semibold">FAISS (In-Memory)</div>
              </div>
              <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px' }}>
                <div className="text-xs text-gray mb-1">Database</div>
                <div className="font-semibold">MongoDB</div>
              </div>
              <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px' }}>
                <div className="text-xs text-gray mb-1">Deployment Mode</div>
                <div className="font-semibold">Enterprise / Air-Gapped Ready</div>
              </div>
            </div>

            <h3 className="card-title mb-3">Supported Frameworks</h3>
            <div className="flex flex-wrap gap-2 mb-6">
              {['NIST CSF', 'ISO 27001', 'SOC2', 'PCI-DSS', 'GDPR', 'Basel III', 'COBIT', 'FFIEC'].map(fw => (
                <span key={fw} className="badge" style={{ background: '#eff6ff', color: '#1e40af' }}>{fw}</span>
              ))}
            </div>

            <h3 className="card-title mb-3">GRC Connectors</h3>
            <div className="grid grid-4 gap-3">
              {['ServiceNow', 'Archer', 'MetricStream', 'LogicGate', 'OneTrust', 'Workiva', 'AuditBoard', 'Diligent'].map(conn => (
                <div key={conn} style={{ padding: '12px', background: '#f0fdf4', borderRadius: '6px', textAlign: 'center', fontSize: '13px', color: '#166534' }}>
                  {conn}
                </div>
              ))}
            </div>

            <div className="mt-6 p-4" style={{ background: '#fef3c7', borderRadius: '8px', border: '1px solid #fcd34d' }}>
              <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#92400e', marginBottom: '8px' }}>Enterprise Features</h4>
              <ul style={{ fontSize: '13px', color: '#78350f', paddingLeft: '20px' }}>
                <li>Multi-agent AI system for automated risk assessment</li>
                <li>Support for Azure AI Agent Service and Vertex AI</li>
                <li>Knowledge graph for organizational context</li>
                <li>Full audit trail and explainability</li>
                <li>GDPR-compliant data handling with reset capabilities</li>
                <li>Role-based access control (LOD1/LOD2/Admin)</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Admin;

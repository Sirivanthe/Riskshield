import { test, expect } from '@playwright/test';
import { loginAsLOD2, loginAsAdmin, loginAsLOD1 } from '../fixtures/helpers';

test.describe('Admin Page - LLM Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsLOD2(page);
    await page.goto('/admin', { waitUntil: 'domcontentloaded' });
  });

  test('should display admin page with correct elements', async ({ page }) => {
    await expect(page.getByTestId('admin-page')).toBeVisible();
    await expect(page.getByTestId('admin-title')).toHaveText('Admin Settings');
  });

  test('should display LLM configuration tab by default', async ({ page }) => {
    await expect(page.getByTestId('tab-llm')).toBeVisible();
    await expect(page.getByTestId('llm-config-form')).toBeVisible();
  });

  test('should display LLM provider select with options', async ({ page }) => {
    const providerSelect = page.getByTestId('llm-provider-select');
    await expect(providerSelect).toBeVisible();
    
    // Check that providers are loaded
    const options = await providerSelect.locator('option').allTextContents();
    expect(options.length).toBeGreaterThan(0);
  });

  test('should display provider cards', async ({ page }) => {
    await expect(page.getByTestId('provider-card-MOCK')).toBeVisible();
    await expect(page.getByTestId('provider-card-OLLAMA')).toBeVisible();
    await expect(page.getByTestId('provider-card-AZURE')).toBeVisible();
    await expect(page.getByTestId('provider-card-VERTEX_AI')).toBeVisible();
  });

  test('should show Azure fields when Azure provider is selected', async ({ page }) => {
    await page.getByTestId('llm-provider-select').selectOption('AZURE');
    
    await expect(page.getByTestId('azure-endpoint-input')).toBeVisible();
    await expect(page.getByTestId('azure-deployment-input')).toBeVisible();
  });

  test('should show Vertex AI fields when Vertex AI provider is selected', async ({ page }) => {
    await page.getByTestId('llm-provider-select').selectOption('VERTEX_AI');
    
    await expect(page.getByTestId('vertex-project-input')).toBeVisible();
    await expect(page.getByTestId('vertex-location-input')).toBeVisible();
  });

  test('should show Ollama fields when Ollama provider is selected', async ({ page }) => {
    await page.getByTestId('llm-provider-select').selectOption('OLLAMA');
    
    await expect(page.getByTestId('ollama-host-input')).toBeVisible();
  });

  test('should save LLM configuration', async ({ page }) => {
    // Update model name
    await page.getByTestId('llm-model-name-input').fill('test-model-e2e');
    
    // Save configuration
    await page.getByTestId('save-llm-config-button').click();
    
    // Wait for save to complete (alert or success message)
    await page.waitForTimeout(1000);
    
    // Verify the value persisted
    await page.reload();
    await expect(page.getByTestId('llm-model-name-input')).toHaveValue('test-model-e2e');
    
    // Restore original value
    await page.getByTestId('llm-model-name-input').fill('llama-3-70b');
    await page.getByTestId('save-llm-config-button').click();
  });

  test('should test LLM connection', async ({ page }) => {
    await page.getByTestId('test-llm-button').click();
    
    // Wait for test result
    await expect(page.getByTestId('llm-test-result')).toBeVisible({ timeout: 10000 });
  });

  test('should switch to Regulations tab', async ({ page }) => {
    await page.getByTestId('tab-regulations').click();
    
    await expect(page.getByTestId('regulation-upload-form')).toBeVisible();
    await expect(page.getByTestId('regulation-name-input')).toBeVisible();
    await expect(page.getByTestId('regulation-framework-select')).toBeVisible();
    await expect(page.getByTestId('regulation-content-textarea')).toBeVisible();
  });

  test('should switch to System Info tab', async ({ page }) => {
    await page.getByTestId('tab-system').click();
    
    await expect(page.getByTestId('system-info-card')).toBeVisible();
  });
});

test.describe('Admin Page - Access Control', () => {
  test('LOD1 user should not have access to admin page', async ({ page }) => {
    await loginAsLOD1(page);
    await page.goto('/admin', { waitUntil: 'domcontentloaded' });
    
    // Should show access denied message
    await expect(page.getByText('Access Denied')).toBeVisible();
  });

  test('Admin user should have access to admin page', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/admin', { waitUntil: 'domcontentloaded' });
    
    await expect(page.getByTestId('admin-page')).toBeVisible();
    await expect(page.getByTestId('llm-config-form')).toBeVisible();
  });
});

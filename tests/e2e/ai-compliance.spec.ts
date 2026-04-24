import { test, expect } from '@playwright/test';
import { loginAsLOD1, loginAsLOD2, loginAsAdmin } from '../fixtures/helpers';

test.describe('AI Compliance Page', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsLOD1(page);
    await page.getByTestId('nav-ai-compliance').click();
    await expect(page.getByTestId('ai-compliance-page')).toBeVisible();
  });

  test('should display AI compliance page with title', async ({ page }) => {
    await expect(page.getByTestId('ai-compliance-title')).toHaveText('AI Compliance');
    await expect(page.getByTestId('register-ai-system-button')).toBeVisible();
  });

  test('should display summary stat cards', async ({ page }) => {
    // Check for stat cards
    await expect(page.locator('.stat-card').first()).toBeVisible();
    await expect(page.locator('.stat-label').filter({ hasText: /Total AI Systems/i })).toBeVisible();
    await expect(page.locator('.stat-label').filter({ hasText: /High Risk/i })).toBeVisible();
    await expect(page.locator('.stat-label').filter({ hasText: /Assessments/i })).toBeVisible();
    await expect(page.locator('.stat-label').filter({ hasText: /Compliance Rate/i })).toBeVisible();
  });

  test('should display tabs for AI Systems, Assessments, and Frameworks', async ({ page }) => {
    await expect(page.getByRole('button', { name: /AI Systems/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Assessments/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Frameworks/i })).toBeVisible();
  });

  test('should open register AI system modal', async ({ page }) => {
    await page.getByTestId('register-ai-system-button').click();
    await expect(page.locator('.modal')).toBeVisible();
    await expect(page.locator('.modal-title')).toHaveText('Register AI System');
  });

  test('should close modal when clicking cancel', async ({ page }) => {
    await page.getByTestId('register-ai-system-button').click();
    await expect(page.locator('.modal')).toBeVisible();
    
    await page.locator('button').filter({ hasText: 'Cancel' }).click();
    await expect(page.locator('.modal')).not.toBeVisible();
  });
});

test.describe('AI System Registration', () => {
  test('should register a new AI system', async ({ page }) => {
    await loginAsLOD1(page);
    await page.getByTestId('nav-ai-compliance').click();
    await expect(page.getByTestId('ai-compliance-page')).toBeVisible();
    
    const uniqueName = `TEST_AI_System_${Date.now()}`;
    
    await page.getByTestId('register-ai-system-button').click();
    await expect(page.locator('.modal')).toBeVisible();
    
    // Fill required fields
    await page.locator('input[placeholder*="Customer Credit"]').fill(uniqueName);
    await page.locator('textarea[placeholder*="functionality"]').fill('Test AI system for E2E testing');
    await page.locator('input[placeholder*="Automated credit"]').fill('Automated testing purpose');
    
    // Select AI Type
    await page.locator('select').filter({ hasText: /ML Model/i }).first().selectOption('ML Model');
    
    // Select Deployment Status
    await page.locator('select').filter({ hasText: /Development/i }).first().selectOption('Development');
    
    // Select Risk Category
    await page.locator('select').filter({ hasText: /LIMITED/i }).first().selectOption('HIGH');
    
    // Fill Business Unit
    await page.locator('input[placeholder*="Consumer Banking"]').fill('Test Business Unit');
    
    // Fill Owner
    await page.locator('input[placeholder*="risk-team"]').fill('test@bank.com');
    
    // Select Human Oversight Level
    await page.locator('select').filter({ hasText: /Limited/i }).last().selectOption('Significant');
    
    // Submit
    await page.locator('button[type="submit"]').click();
    
    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible();
    
    // Wait for page to reload
    await page.waitForLoadState('networkidle');
  });

  test('should show risk category helper text', async ({ page }) => {
    await loginAsLOD1(page);
    await page.getByTestId('nav-ai-compliance').click();
    await page.getByTestId('register-ai-system-button').click();
    await expect(page.locator('.modal')).toBeVisible();
    
    // Select HIGH risk category
    const riskSelect = page.locator('select').filter({ hasText: /LIMITED/i }).first();
    await riskSelect.selectOption('HIGH');
    
    // Check for helper text
    await expect(page.locator('.form-helper').filter({ hasText: /strict requirements/i })).toBeVisible();
  });
});

test.describe('AI Assessments Tab', () => {
  test('should display assessments table', async ({ page }) => {
    await loginAsLOD1(page);
    await page.getByTestId('nav-ai-compliance').click();
    await expect(page.getByTestId('ai-compliance-page')).toBeVisible();
    
    // Click Assessments tab
    await page.getByRole('button', { name: /Assessments/i }).click();
    
    // Check for assessments table
    await expect(page.getByTestId('assessments-table')).toBeVisible();
    
    // Check table headers
    await expect(page.locator('th').filter({ hasText: /Assessment ID/i })).toBeVisible();
    await expect(page.locator('th').filter({ hasText: /AI System/i })).toBeVisible();
    await expect(page.locator('th').filter({ hasText: /Framework/i })).toBeVisible();
    await expect(page.locator('th').filter({ hasText: /Status/i })).toBeVisible();
  });
});

test.describe('AI Frameworks Tab', () => {
  test('should display EU AI Act and NIST AI RMF frameworks', async ({ page }) => {
    await loginAsLOD1(page);
    await page.getByTestId('nav-ai-compliance').click();
    await expect(page.getByTestId('ai-compliance-page')).toBeVisible();
    
    // Click Frameworks tab
    await page.getByRole('button', { name: /Frameworks/i }).click();
    
    // Check for EU AI Act framework card
    await expect(page.locator('h3').filter({ hasText: /EU AI Act/i })).toBeVisible();
    
    // Check for NIST AI RMF framework card
    await expect(page.locator('h3').filter({ hasText: /NIST AI Risk Management/i })).toBeVisible();
  });

  test('should display EU AI Act risk categories', async ({ page }) => {
    await loginAsLOD1(page);
    await page.getByTestId('nav-ai-compliance').click();
    await page.getByRole('button', { name: /Frameworks/i }).click();
    
    // Check for risk categories
    await expect(page.locator('span').filter({ hasText: 'UNACCEPTABLE' })).toBeVisible();
    await expect(page.locator('span').filter({ hasText: 'HIGH' }).first()).toBeVisible();
    await expect(page.locator('span').filter({ hasText: 'LIMITED' }).first()).toBeVisible();
    await expect(page.locator('span').filter({ hasText: 'MINIMAL' })).toBeVisible();
  });

  test('should display NIST AI RMF functions', async ({ page }) => {
    await loginAsLOD1(page);
    await page.getByTestId('nav-ai-compliance').click();
    await page.getByRole('button', { name: /Frameworks/i }).click();
    
    // Check for NIST functions - use exact match
    await expect(page.getByText('GOVERN', { exact: true })).toBeVisible();
    await expect(page.getByText('MAP', { exact: true })).toBeVisible();
    await expect(page.getByText('MEASURE', { exact: true })).toBeVisible();
    await expect(page.getByText('MANAGE', { exact: true })).toBeVisible();
  });
});

test.describe('AI System Assessment Flow', () => {
  test('should open assessment selection modal for AI system', async ({ page }) => {
    await loginAsLOD1(page);
    await page.getByTestId('nav-ai-compliance').click();
    await expect(page.getByTestId('ai-compliance-page')).toBeVisible();
    
    // First register an AI system if none exist
    const systemCards = page.locator('[data-testid^="ai-system-card-"]');
    const count = await systemCards.count();
    
    if (count === 0) {
      // Register a system first
      const uniqueName = `TEST_AI_Assess_${Date.now()}`;
      await page.getByTestId('register-ai-system-button').click();
      await page.locator('input[placeholder*="Customer Credit"]').fill(uniqueName);
      await page.locator('textarea[placeholder*="functionality"]').fill('Test system');
      await page.locator('input[placeholder*="Automated credit"]').fill('Testing');
      await page.locator('input[placeholder*="Consumer Banking"]').fill('Test');
      await page.locator('input[placeholder*="risk-team"]').fill('test@bank.com');
      await page.locator('button[type="submit"]').click();
      await expect(page.locator('.modal')).not.toBeVisible();
      await page.waitForLoadState('networkidle');
    }
    
    // Click Run Assessment on first system
    const runAssessmentBtn = page.locator('button').filter({ hasText: 'Run Assessment' }).first();
    if (await runAssessmentBtn.isVisible()) {
      await runAssessmentBtn.click();
      
      // Assessment selection modal should appear
      await expect(page.locator('.modal')).toBeVisible();
      await expect(page.locator('.modal-title')).toHaveText('Run Assessment');
      
      // Should show EU AI Act and NIST AI RMF options
      await expect(page.locator('button').filter({ hasText: /EU AI Act Assessment/i })).toBeVisible();
      await expect(page.locator('button').filter({ hasText: /NIST AI RMF Assessment/i })).toBeVisible();
    }
  });

  test('should create EU AI Act assessment', async ({ page }) => {
    await loginAsLOD1(page);
    await page.getByTestId('nav-ai-compliance').click();
    await expect(page.getByTestId('ai-compliance-page')).toBeVisible();
    
    // Check if there are AI systems
    const runAssessmentBtn = page.locator('button').filter({ hasText: 'Run Assessment' }).first();
    if (await runAssessmentBtn.isVisible()) {
      await runAssessmentBtn.click();
      await expect(page.locator('.modal')).toBeVisible();
      
      // Click EU AI Act Assessment
      await page.locator('button').filter({ hasText: /EU AI Act Assessment/i }).click();
      
      // Modal should close and assessment should be created
      await expect(page.locator('.modal')).not.toBeVisible();
      await page.waitForLoadState('networkidle');
    }
  });

  test('should create NIST AI RMF assessment', async ({ page }) => {
    await loginAsLOD1(page);
    await page.getByTestId('nav-ai-compliance').click();
    await expect(page.getByTestId('ai-compliance-page')).toBeVisible();
    
    // Check if there are AI systems
    const runAssessmentBtn = page.locator('button').filter({ hasText: 'Run Assessment' }).first();
    if (await runAssessmentBtn.isVisible()) {
      await runAssessmentBtn.click();
      await expect(page.locator('.modal')).toBeVisible();
      
      // Click NIST AI RMF Assessment
      await page.locator('button').filter({ hasText: /NIST AI RMF Assessment/i }).click();
      
      // Modal should close and assessment should be created
      await expect(page.locator('.modal')).not.toBeVisible();
      await page.waitForLoadState('networkidle');
    }
  });
});

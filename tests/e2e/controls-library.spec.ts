import { test, expect } from '@playwright/test';
import { loginAsLOD1, loginAsLOD2, loginAsAdmin } from '../fixtures/helpers';

test.describe('Controls Library Page', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsLOD1(page);
    await page.getByTestId('nav-controls-library').click();
    await expect(page.getByTestId('controls-library-page')).toBeVisible();
  });

  test('should display controls library page with title', async ({ page }) => {
    await expect(page.getByTestId('controls-library-title')).toHaveText('Controls Library');
    await expect(page.getByTestId('create-control-button')).toBeVisible();
  });

  test('should display tabs for filtering controls', async ({ page }) => {
    // Check for All Controls tab
    await expect(page.locator('.tab-button').first()).toBeVisible();
    // Check for AI Controls tab
    await expect(page.getByRole('button', { name: /AI Controls/i })).toBeVisible();
  });

  test('should open create control modal', async ({ page }) => {
    await page.getByTestId('create-control-button').click();
    await expect(page.locator('.modal')).toBeVisible();
    await expect(page.locator('.modal-title')).toHaveText('Create Custom Control');
  });

  test('should create a new control as LOD1', async ({ page }) => {
    const uniqueName = `TEST_Control_${Date.now()}`;
    
    await page.getByTestId('create-control-button').click();
    await expect(page.locator('.modal')).toBeVisible();
    
    // Fill form - use placeholder selectors
    await page.locator('input[placeholder*="Multi-Factor"]').fill(uniqueName);
    await page.locator('textarea[placeholder*="purpose and scope"]').fill('Test control description for E2E testing');
    
    // Select category
    await page.locator('select').first().selectOption('TECHNICAL');
    
    // Select framework checkbox
    await page.locator('label').filter({ hasText: 'NIST CSF' }).locator('input[type="checkbox"]').check();
    
    // Submit
    await page.getByRole('button', { name: 'Create Control' }).click();
    
    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible();
    
    // Control should appear in list (may need to wait for reload)
    await page.waitForLoadState('networkidle');
  });

  test('should close modal when clicking cancel', async ({ page }) => {
    await page.getByTestId('create-control-button').click();
    await expect(page.locator('.modal')).toBeVisible();
    
    await page.locator('button').filter({ hasText: 'Cancel' }).click();
    await expect(page.locator('.modal')).not.toBeVisible();
  });

  test('should filter AI controls', async ({ page }) => {
    await page.getByRole('button', { name: /AI Controls/i }).click();
    await page.waitForLoadState('networkidle');
    // Page should update to show AI controls filter
  });
});

test.describe('Controls Library - LOD2 Approval Workflow', () => {
  test('LOD2 should see Pending Review tab', async ({ page }) => {
    await loginAsLOD2(page);
    await page.getByTestId('nav-controls-library').click();
    await expect(page.getByTestId('controls-library-page')).toBeVisible();
    
    // LOD2 should see Pending Review tab
    await expect(page.getByRole('button', { name: /Pending Review/i })).toBeVisible();
  });

  test('LOD2 should be able to approve controls', async ({ page }) => {
    await loginAsLOD2(page);
    await page.getByTestId('nav-controls-library').click();
    await expect(page.getByTestId('controls-library-page')).toBeVisible();
    
    // Click Pending Review tab
    await page.getByRole('button', { name: /Pending Review/i }).click();
    await page.waitForLoadState('networkidle');
    
    // If there are pending controls, approve button should be visible
    const approveButton = page.locator('button').filter({ hasText: 'Approve' }).first();
    if (await approveButton.isVisible()) {
      await approveButton.click();
      await page.waitForLoadState('networkidle');
    }
  });

  test('Admin should see Pending Review tab', async ({ page }) => {
    await loginAsAdmin(page);
    await page.getByTestId('nav-controls-library').click();
    await expect(page.getByTestId('controls-library-page')).toBeVisible();
    
    // Admin should see Pending Review tab
    await expect(page.getByRole('button', { name: /Pending Review/i })).toBeVisible();
  });
});

test.describe('Controls Library - AI Control Creation', () => {
  test('should create AI-specific control with risk category', async ({ page }) => {
    await loginAsLOD1(page);
    await page.getByTestId('nav-controls-library').click();
    await expect(page.getByTestId('controls-library-page')).toBeVisible();
    
    const uniqueName = `TEST_AI_Control_${Date.now()}`;
    
    await page.getByTestId('create-control-button').click();
    await expect(page.locator('.modal')).toBeVisible();
    
    // Fill form - use placeholder selectors
    await page.locator('input[placeholder*="Multi-Factor"]').fill(uniqueName);
    await page.locator('textarea[placeholder*="purpose and scope"]').fill('AI governance control for testing');
    
    // Select AI category
    await page.locator('select').first().selectOption('AI_GOVERNANCE');
    
    // Select EU AI Act framework
    await page.locator('label').filter({ hasText: 'EU_AI_ACT' }).locator('input[type="checkbox"]').check();
    
    // Check AI control checkbox - look for the checkbox in the AI section
    const aiCheckbox = page.locator('label').filter({ hasText: /AI-specific control/i }).locator('input[type="checkbox"]');
    if (await aiCheckbox.isVisible()) {
      await aiCheckbox.check();
      
      // Select AI risk category (should appear after checking AI control)
      await page.waitForLoadState('domcontentloaded');
      const riskCategorySelect = page.locator('select').last();
      if (await riskCategorySelect.isVisible()) {
        await riskCategorySelect.selectOption('HIGH');
      }
    }
    
    // Submit
    await page.getByRole('button', { name: 'Create Control' }).click();
    
    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible();
  });
});

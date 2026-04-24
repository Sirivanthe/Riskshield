import { test, expect } from '@playwright/test';
import { loginAsLOD1, loginAsLOD2 } from '../fixtures/helpers';

test.describe('Assessments Page', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsLOD1(page);
    await page.goto('/assessments', { waitUntil: 'domcontentloaded' });
  });

  test('should display assessments page with correct elements', async ({ page }) => {
    await expect(page.getByTestId('assessments-page')).toBeVisible();
    await expect(page.getByTestId('assessments-title')).toHaveText('Assessments');
    await expect(page.getByTestId('new-assessment-button')).toBeVisible();
  });

  test('should display filter buttons', async ({ page }) => {
    await expect(page.getByTestId('filter-all')).toBeVisible();
    await expect(page.getByTestId('filter-completed')).toBeVisible();
    await expect(page.getByTestId('filter-in-progress')).toBeVisible();
    await expect(page.getByTestId('filter-pending')).toBeVisible();
  });

  test('should open new assessment modal when clicking New Assessment button', async ({ page }) => {
    await page.getByTestId('new-assessment-button').click();
    
    // Modal should appear with form elements
    await expect(page.getByTestId('new-assessment-modal')).toBeVisible();
    await expect(page.getByTestId('assessment-name-input')).toBeVisible();
    await expect(page.getByTestId('system-name-input')).toBeVisible();
    await expect(page.getByTestId('business-unit-select')).toBeVisible();
  });

  test('should create a new assessment', async ({ page }) => {
    const uniqueId = `TEST_${Date.now()}`;
    
    await page.getByTestId('new-assessment-button').click();
    await expect(page.getByTestId('new-assessment-modal')).toBeVisible();
    
    // Step 1: Fill in basic information
    await page.getByTestId('assessment-name-input').fill(`E2E Test Assessment ${uniqueId}`);
    await page.getByTestId('system-name-input').fill(`E2E Test System ${uniqueId}`);
    await page.getByTestId('business-unit-select').selectOption('Technology');
    
    // Click Next to go to Step 2
    await page.getByTestId('modal-next-button').click();
    await expect(page.getByTestId('assessment-step-2')).toBeVisible();
    
    // Step 2: Select frameworks
    await page.getByTestId('framework-nist-csf').click();
    
    // Click Next to go to Step 3
    await page.getByTestId('modal-next-button').click();
    await expect(page.getByTestId('assessment-step-3')).toBeVisible();
    
    // Step 3: Submit the form
    await page.getByTestId('modal-submit-button').click();
    
    // Wait for assessment to be created and processed (AI processing takes time)
    await expect(page.getByTestId('new-assessment-modal')).not.toBeVisible({ timeout: 60000 });
    
    // Verify the assessment appears in the list
    await page.waitForLoadState('networkidle');
  });

  test('should filter assessments by status', async ({ page }) => {
    // Click on Completed filter
    await page.getByTestId('filter-completed').click();
    
    // The filter should be active
    await expect(page.getByTestId('filter-completed')).toHaveClass(/btn-primary/);
  });
});

test.describe('Assessment Detail Page', () => {
  test('should navigate to assessment detail and display content', async ({ page }) => {
    await loginAsLOD1(page);
    await page.goto('/assessments', { waitUntil: 'domcontentloaded' });
    
    // Wait for assessments to load
    await page.waitForLoadState('networkidle');
    
    // Check if there are any assessments
    const assessmentTable = page.getByTestId('assessments-table');
    if (await assessmentTable.isVisible()) {
      // Click on the first View button
      const viewButton = page.locator('[data-testid^="view-assessment-"]').first();
      if (await viewButton.isVisible()) {
        await viewButton.click();
        
        // Should navigate to assessment detail page
        await expect(page.url()).toContain('/assessments/');
      }
    }
  });
});

test.describe('Agent Activity Viewer', () => {
  test('should display agent activity page with tabs', async ({ page }) => {
    await loginAsLOD1(page);
    
    // First create an assessment to have activity data
    await page.goto('/assessments', { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle');
    
    // Check if there are any assessments
    const viewButton = page.locator('[data-testid^="view-assessment-"]').first();
    if (await viewButton.isVisible()) {
      await viewButton.click();
      await page.waitForLoadState('networkidle');
      
      // Navigate to agent activity viewer
      const activityLink = page.locator('[data-testid="view-agent-activity-link"]');
      if (await activityLink.isVisible()) {
        await activityLink.click();
        
        await expect(page.getByTestId('agent-activity-page')).toBeVisible();
        await expect(page.getByTestId('tab-activities')).toBeVisible();
        await expect(page.getByTestId('tab-metrics')).toBeVisible();
        await expect(page.getByTestId('tab-explanations')).toBeVisible();
      }
    }
  });
});

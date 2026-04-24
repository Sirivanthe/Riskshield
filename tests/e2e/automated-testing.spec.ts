import { test, expect } from '@playwright/test';
import { loginAsAdmin, loginAsLOD1, loginAsLOD2, dismissToasts } from '../fixtures/helpers';

test.describe('Automated Testing Page', () => {
  test.beforeEach(async ({ page }) => {
    await dismissToasts(page);
  });

  test('should navigate to Automated Testing page via sidebar', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Click on Automated Testing nav link
    await page.getByTestId('nav-automated-testing').click();
    
    // Verify page loaded
    await expect(page.getByTestId('automated-testing-page')).toBeVisible();
    await expect(page.getByTestId('automated-testing-title')).toHaveText('Automated Control Testing');
  });

  test('should display page title and subtitle', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/automated-testing', { waitUntil: 'domcontentloaded' });
    
    await expect(page.getByTestId('automated-testing-title')).toBeVisible();
    await expect(page.getByTestId('automated-testing-title')).toHaveText('Automated Control Testing');
    
    // Check subtitle
    const subtitle = page.locator('.page-subtitle');
    await expect(subtitle).toContainText('AI-powered control testing');
  });

  test('should display summary stats cards', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/automated-testing', { waitUntil: 'domcontentloaded' });
    
    // Wait for page to load
    await expect(page.getByTestId('automated-testing-page')).toBeVisible();
    
    // Check stat cards are present
    const statCards = page.locator('.stat-card');
    await expect(statCards).toHaveCount(4);
    
    // Check stat labels
    await expect(page.locator('.stat-label').filter({ hasText: 'Total Test Runs' })).toBeVisible();
    await expect(page.locator('.stat-label').filter({ hasText: 'Pending Review' })).toBeVisible();
    await expect(page.locator('.stat-label').filter({ hasText: 'Effective Controls' })).toBeVisible();
    await expect(page.locator('.stat-label').filter({ hasText: 'Test Types' })).toBeVisible();
  });

  test('should display tabs for Test Runs, Run New Test, and Test Types', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/automated-testing', { waitUntil: 'domcontentloaded' });
    
    // Check tabs are present
    const tabList = page.locator('.tab-list');
    await expect(tabList).toBeVisible();
    
    // Check tab buttons
    await expect(page.locator('.tab-button').filter({ hasText: /Test Runs/ })).toBeVisible();
    await expect(page.locator('.tab-button').filter({ hasText: 'Run New Test' })).toBeVisible();
    await expect(page.locator('.tab-button').filter({ hasText: 'Test Types & Sources' })).toBeVisible();
  });

  test('should display test runs table on default tab', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/automated-testing', { waitUntil: 'domcontentloaded' });
    
    // Test runs table should be visible by default
    await expect(page.getByTestId('test-runs-table')).toBeVisible();
    
    // Check table headers
    const headers = page.locator('th');
    await expect(headers.filter({ hasText: 'Run ID' })).toBeVisible();
    await expect(headers.filter({ hasText: 'Control' })).toBeVisible();
    await expect(headers.filter({ hasText: 'Test Type' })).toBeVisible();
    await expect(headers.filter({ hasText: 'Effectiveness' })).toBeVisible();
  });

  test('should switch to Run New Test tab', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/automated-testing', { waitUntil: 'domcontentloaded' });
    
    // Click on Run New Test tab
    await page.locator('.tab-button').filter({ hasText: 'Run New Test' }).click();
    
    // Test runs table should not be visible
    await expect(page.getByTestId('test-runs-table')).not.toBeVisible();
    
    // Should show controls grid or empty state
    const controlsGrid = page.locator('.grid.grid-2');
    await expect(controlsGrid).toBeVisible();
  });

  test('should switch to Test Types & Sources tab', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/automated-testing', { waitUntil: 'domcontentloaded' });
    
    // Click on Test Types tab
    await page.locator('.tab-button').filter({ hasText: 'Test Types & Sources' }).click();
    
    // Should show test types and evidence sources
    await expect(page.locator('.card-title').filter({ hasText: 'Automated Test Types' })).toBeVisible();
    await expect(page.locator('.card-title').filter({ hasText: 'Evidence Sources' })).toBeVisible();
  });

  test('should display test types list', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/automated-testing', { waitUntil: 'domcontentloaded' });
    
    // Click on Test Types tab
    await page.locator('.tab-button').filter({ hasText: 'Test Types & Sources' }).click();
    
    // Check for expected test types (use exact match to avoid strict mode violations)
    await expect(page.getByText('Configuration Check', { exact: true })).toBeVisible();
    await expect(page.getByText('Access Review', { exact: true })).toBeVisible();
    await expect(page.getByText('Vulnerability Scan', { exact: true })).toBeVisible();
  });

  test('should display evidence sources list', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/automated-testing', { waitUntil: 'domcontentloaded' });
    
    // Click on Test Types tab
    await page.locator('.tab-button').filter({ hasText: 'Test Types & Sources' }).click();
    
    // Check for expected evidence sources (use exact match to avoid strict mode violations)
    await expect(page.getByText('AWS Config', { exact: true })).toBeVisible();
    await expect(page.getByText('Azure Policy', { exact: true })).toBeVisible();
    await expect(page.getByText('IAM Policy Export', { exact: true })).toBeVisible();
  });

  test('should show View button for test runs', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/automated-testing', { waitUntil: 'domcontentloaded' });
    
    // Check if there are test runs
    const tableRows = page.locator('tbody tr');
    const rowCount = await tableRows.count();
    
    if (rowCount > 0) {
      // Check for View button
      const viewButton = page.locator('button').filter({ hasText: 'View' }).first();
      await expect(viewButton).toBeVisible();
    }
  });

  test('should open test run detail modal when clicking View', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/automated-testing', { waitUntil: 'domcontentloaded' });
    
    // Check if there are test runs
    const tableRows = page.locator('tbody tr');
    const rowCount = await tableRows.count();
    
    if (rowCount > 0) {
      // Click View button
      await page.locator('button').filter({ hasText: 'View' }).first().click();
      
      // Modal should open
      await expect(page.locator('.modal')).toBeVisible();
      await expect(page.locator('.modal-title')).toContainText('Test Run Details');
      
      // Close modal
      await page.locator('.modal-close').click();
      await expect(page.locator('.modal')).not.toBeVisible();
    }
  });
});

test.describe('Automated Testing - LOD1 User', () => {
  test.beforeEach(async ({ page }) => {
    await dismissToasts(page);
  });

  test('LOD1 user can access Automated Testing page', async ({ page }) => {
    await loginAsLOD1(page);
    
    await page.getByTestId('nav-automated-testing').click();
    
    await expect(page.getByTestId('automated-testing-page')).toBeVisible();
    await expect(page.getByTestId('automated-testing-title')).toHaveText('Automated Control Testing');
  });

  test('LOD1 user can view test runs', async ({ page }) => {
    await loginAsLOD1(page);
    await page.goto('/automated-testing', { waitUntil: 'domcontentloaded' });
    
    await expect(page.getByTestId('test-runs-table')).toBeVisible();
  });
});

test.describe('Automated Testing - LOD2 User', () => {
  test.beforeEach(async ({ page }) => {
    await dismissToasts(page);
  });

  test('LOD2 user can access Automated Testing page', async ({ page }) => {
    await loginAsLOD2(page);
    
    await page.getByTestId('nav-automated-testing').click();
    
    await expect(page.getByTestId('automated-testing-page')).toBeVisible();
  });

  test('LOD2 user can see Approve button for pending reviews', async ({ page }) => {
    await loginAsLOD2(page);
    await page.goto('/automated-testing', { waitUntil: 'domcontentloaded' });
    
    // Check if there are pending reviews
    const pendingBadge = page.locator('.badge').filter({ hasText: 'Needs Review' });
    const pendingCount = await pendingBadge.count();
    
    if (pendingCount > 0) {
      // LOD2 should see Approve button
      const approveButton = page.locator('button').filter({ hasText: 'Approve' }).first();
      await expect(approveButton).toBeVisible();
    }
  });
});

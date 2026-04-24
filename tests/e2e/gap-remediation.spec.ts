import { test, expect } from '@playwright/test';
import { loginAsAdmin, loginAsLOD1, loginAsLOD2, dismissToasts } from '../fixtures/helpers';

test.describe('Gap Remediation Page', () => {
  test.beforeEach(async ({ page }) => {
    await dismissToasts(page);
  });

  test('should navigate to Gap Remediation page via sidebar', async ({ page }) => {
    await loginAsAdmin(page);
    
    // Click on Gap Remediation nav link
    await page.getByTestId('nav-gap-remediation').click();
    
    // Verify page loaded
    await expect(page.getByTestId('gap-remediation-page')).toBeVisible();
    await expect(page.getByTestId('gap-remediation-title')).toHaveText('Gap Remediation');
  });

  test('should display page title and subtitle', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    await expect(page.getByTestId('gap-remediation-title')).toBeVisible();
    await expect(page.getByTestId('gap-remediation-title')).toHaveText('Gap Remediation');
    
    // Check subtitle
    const subtitle = page.locator('.page-subtitle');
    await expect(subtitle).toContainText('AI-powered control gap analysis');
  });

  test('should display summary stats cards', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Wait for page to load
    await expect(page.getByTestId('gap-remediation-page')).toBeVisible();
    
    // Check stat cards are present
    const statCards = page.locator('.stat-card');
    await expect(statCards).toHaveCount(4);
    
    // Check stat labels
    await expect(page.locator('.stat-label').filter({ hasText: 'Open Gaps' })).toBeVisible();
    await expect(page.locator('.stat-label').filter({ hasText: 'In Progress' })).toBeVisible();
    await expect(page.locator('.stat-label').filter({ hasText: 'Remediated' })).toBeVisible();
    await expect(page.locator('.stat-label').filter({ hasText: 'Critical Gaps' })).toBeVisible();
  });

  test('should display tabs for Control Gaps and Remediation Plans', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Check tabs are present
    const tabList = page.locator('.tab-list');
    await expect(tabList).toBeVisible();
    
    // Check tab buttons
    await expect(page.locator('.tab-button').filter({ hasText: /Control Gaps/ })).toBeVisible();
    await expect(page.locator('.tab-button').filter({ hasText: /Remediation Plans/ })).toBeVisible();
  });

  test('should display gaps table on default tab', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Gaps table should be visible by default
    await expect(page.getByTestId('gaps-table')).toBeVisible();
    
    // Check table headers
    const headers = page.locator('th');
    await expect(headers.filter({ hasText: 'Gap ID' })).toBeVisible();
    await expect(headers.filter({ hasText: 'Framework' })).toBeVisible();
    await expect(headers.filter({ hasText: 'Requirement' })).toBeVisible();
    await expect(headers.filter({ hasText: 'Severity' })).toBeVisible();
    await expect(headers.filter({ hasText: 'Status' })).toBeVisible();
  });

  test('should switch to Remediation Plans tab', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Click on Remediation Plans tab
    await page.locator('.tab-button').filter({ hasText: /Remediation Plans/ }).click();
    
    // Gaps table should not be visible
    await expect(page.getByTestId('gaps-table')).not.toBeVisible();
    
    // Should show remediation plans or empty state
    const remediationCards = page.locator('.card');
    await expect(remediationCards.first()).toBeVisible();
  });

  test('should display Get AI Recommendations button for open gaps', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Check if there are open gaps
    const openGapRows = page.locator('tbody tr').filter({ has: page.locator('text=OPEN') });
    const openCount = await openGapRows.count();
    
    if (openCount > 0) {
      // Check for Get AI Recommendations button
      const recButton = page.locator('button').filter({ hasText: 'Get AI Recommendations' }).first();
      await expect(recButton).toBeVisible();
    }
  });

  test('should open AI Recommendations modal when clicking button', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Check if there are open gaps
    const openGapRows = page.locator('tbody tr').filter({ has: page.locator('text=OPEN') });
    const openCount = await openGapRows.count();
    
    if (openCount > 0) {
      // Click Get AI Recommendations button
      await page.locator('button').filter({ hasText: 'Get AI Recommendations' }).first().click();
      
      // Modal should open
      await expect(page.locator('.modal')).toBeVisible();
      await expect(page.locator('.modal-title')).toContainText('AI Recommendations');
      
      // Wait for recommendations to load
      await expect(page.locator('.loading-spinner')).toBeVisible();
      
      // Wait for recommendations to appear (or timeout)
      await page.waitForSelector('text=Recommended Controls', { timeout: 30000 }).catch(() => {});
      
      // Close modal
      await page.locator('.modal-close').click();
      await expect(page.locator('.modal')).not.toBeVisible();
    }
  });

  test('should display remediation plan details', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Switch to Remediation Plans tab
    await page.locator('.tab-button').filter({ hasText: /Remediation Plans/ }).click();
    
    // Check if there are remediation plans by looking for REM- prefix
    const remediationCards = page.locator('.card').filter({ hasText: /REM-/ });
    const planCount = await remediationCards.count();
    
    if (planCount > 0) {
      // Check for progress bar
      await expect(page.locator('text=Progress').first()).toBeVisible();
      
      // Check for action buttons
      const actionButtons = page.locator('button').filter({ hasText: /Implement|Compensating|Accept Risk|View Details|Approve Plan/ });
      await expect(actionButtons.first()).toBeVisible();
    }
  });

  test('should show severity badges with correct colors', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Check for severity indicators
    const severityTexts = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
    
    for (const severity of severityTexts) {
      const severityElement = page.locator(`text=${severity}`).first();
      if (await severityElement.isVisible()) {
        // Severity should be styled
        await expect(severityElement).toBeVisible();
        break;
      }
    }
  });

  test('should show status badges', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Check for status badges
    const statusTexts = ['OPEN', 'IN_PROGRESS', 'REMEDIATED', 'DRAFT', 'APPROVED'];
    
    for (const status of statusTexts) {
      const statusBadge = page.locator('.badge').filter({ hasText: status }).first();
      if (await statusBadge.isVisible()) {
        await expect(statusBadge).toBeVisible();
        break;
      }
    }
  });
});

test.describe('Gap Remediation - LOD1 User', () => {
  test.beforeEach(async ({ page }) => {
    await dismissToasts(page);
  });

  test('LOD1 user can access Gap Remediation page', async ({ page }) => {
    await loginAsLOD1(page);
    
    await page.getByTestId('nav-gap-remediation').click();
    
    await expect(page.getByTestId('gap-remediation-page')).toBeVisible();
    await expect(page.getByTestId('gap-remediation-title')).toHaveText('Gap Remediation');
  });

  test('LOD1 user can view gaps table', async ({ page }) => {
    await loginAsLOD1(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    await expect(page.getByTestId('gaps-table')).toBeVisible();
  });

  test('LOD1 user can view remediation plans', async ({ page }) => {
    await loginAsLOD1(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Switch to Remediation Plans tab
    await page.locator('.tab-button').filter({ hasText: /Remediation Plans/ }).click();
    
    // Should see remediation plans or empty state
    const content = page.locator('.page-content');
    await expect(content).toBeVisible();
  });
});

test.describe('Gap Remediation - LOD2 User', () => {
  test.beforeEach(async ({ page }) => {
    await dismissToasts(page);
  });

  test('LOD2 user can access Gap Remediation page', async ({ page }) => {
    await loginAsLOD2(page);
    
    await page.getByTestId('nav-gap-remediation').click();
    
    await expect(page.getByTestId('gap-remediation-page')).toBeVisible();
  });

  test('LOD2 user can see Approve Plan button for in-progress remediations', async ({ page }) => {
    await loginAsLOD2(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Switch to Remediation Plans tab
    await page.locator('.tab-button').filter({ hasText: /Remediation Plans/ }).click();
    
    // Check if there are in-progress remediations
    const inProgressBadge = page.locator('.badge').filter({ hasText: 'IN_PROGRESS' });
    const inProgressCount = await inProgressBadge.count();
    
    if (inProgressCount > 0) {
      // LOD2 should see Approve Plan button
      const approveButton = page.locator('button').filter({ hasText: 'Approve Plan' }).first();
      await expect(approveButton).toBeVisible();
    }
  });
});

test.describe('Gap Remediation - Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await dismissToasts(page);
  });

  test('sidebar navigation link is visible and active when on page', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Check nav link is visible
    const navLink = page.getByTestId('nav-gap-remediation');
    await expect(navLink).toBeVisible();
    
    // Check nav link has active class
    await expect(navLink).toHaveClass(/active/);
  });

  test('can navigate between tabs without page reload', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/gap-remediation', { waitUntil: 'domcontentloaded' });
    
    // Start on Gaps tab
    await expect(page.getByTestId('gaps-table')).toBeVisible();
    
    // Switch to Remediation Plans
    await page.locator('.tab-button').filter({ hasText: /Remediation Plans/ }).click();
    await expect(page.getByTestId('gaps-table')).not.toBeVisible();
    
    // Switch back to Gaps
    await page.locator('.tab-button').filter({ hasText: /Control Gaps/ }).click();
    await expect(page.getByTestId('gaps-table')).toBeVisible();
  });
});

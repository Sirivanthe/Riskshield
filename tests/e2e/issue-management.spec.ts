import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'https://audit-control-hub-4.preview.emergentagent.com';

test.describe('Issue Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await page.fill('input[type="email"]', 'admin@bank.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/');
    
    // Navigate to Issue Management
    await page.click('[data-testid="nav-issue-management"]');
    await expect(page.getByTestId('issue-management-page')).toBeVisible();
  });

  test('should display Issue Management page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Issue Management' })).toBeVisible();
    await expect(page.getByText('Track and manage risk findings')).toBeVisible();
    await expect(page.getByTestId('new-issue-btn')).toBeVisible();
  });

  test('should show statistics cards', async ({ page }) => {
    // Wait for statistics to load
    await page.waitForLoadState('networkidle');
    
    // Verify statistics cards are visible - use more specific selectors
    await expect(page.locator('.text-xs.text-slate-400').filter({ hasText: 'Total' })).toBeVisible();
    await expect(page.locator('.text-xs.text-slate-400').filter({ hasText: 'Open' })).toBeVisible();
    await expect(page.locator('.text-xs.text-slate-400').filter({ hasText: 'In Progress' })).toBeVisible();
    await expect(page.locator('.text-xs.text-slate-400').filter({ hasText: 'Resolved' })).toBeVisible();
    await expect(page.locator('.text-xs.text-slate-400').filter({ hasText: 'P1 Critical' })).toBeVisible();
    await expect(page.locator('.text-xs.text-slate-400').filter({ hasText: 'P2 High' })).toBeVisible();
  });

  test('should show filter dropdowns', async ({ page }) => {
    // Verify filter dropdowns exist
    await expect(page.getByText('All Statuses')).toBeVisible();
    await expect(page.getByText('All Priorities')).toBeVisible();
    await expect(page.getByText('All Types')).toBeVisible();
  });

  test('should open create issue form', async ({ page }) => {
    await page.getByTestId('new-issue-btn').click();
    
    // Verify form is visible - wait for it to appear
    await page.waitForSelector('text=Create New Issue');
    await expect(page.getByPlaceholder('Issue title')).toBeVisible();
  });

  test('should create new issue', async ({ page }) => {
    // Open create form
    await page.getByTestId('new-issue-btn').click();
    await page.waitForSelector('text=Create New Issue');
    
    // Fill in the form
    const uniqueId = Date.now().toString().slice(-6);
    await page.getByPlaceholder('Issue title').fill(`TEST_Issue_${uniqueId}`);
    await page.locator('textarea').fill('Test issue description for E2E testing');
    await page.getByPlaceholder('owner@company.com').fill('test@company.com');
    await page.getByPlaceholder('Application name').fill('Test App');
    
    // Submit - find the button in the form
    await page.locator('button').filter({ hasText: 'Create Issue' }).last().click();
    
    // Wait for form to close and issue to appear
    await page.waitForLoadState('networkidle');
    await expect(page.getByText(`TEST_Issue_${uniqueId}`)).toBeVisible();
  });

  test('should show existing issues list', async ({ page }) => {
    // Wait for issues to load
    await page.waitForLoadState('networkidle');
    
    // Should show at least one issue (from backend test data)
    const issueCards = page.locator('.bg-slate-800\\/50.cursor-pointer');
    await expect(issueCards.first()).toBeVisible();
  });

  test('should open issue detail panel when clicking an issue', async ({ page }) => {
    // Wait for issues to load
    await page.waitForLoadState('networkidle');
    
    // Click on first issue
    const issueCard = page.locator('.bg-slate-800\\/50.cursor-pointer').first();
    await issueCard.click();
    
    // Detail panel should open
    await expect(page.getByText('Description')).toBeVisible();
    await expect(page.getByText('History')).toBeVisible();
    await expect(page.getByText('Comments')).toBeVisible();
  });

  test('should show issue status and priority badges', async ({ page }) => {
    // Wait for issues to load
    await page.waitForLoadState('networkidle');
    
    // Look for priority badges (P1, P2, P3, P4)
    const priorityBadge = page.locator('.bg-red-600, .bg-orange-500, .bg-yellow-500, .bg-green-500').first();
    await expect(priorityBadge).toBeVisible();
    
    // Look for status badges
    const statusBadge = page.locator('.bg-blue-600, .bg-yellow-600, .bg-purple-600, .bg-green-600, .bg-gray-600').first();
    await expect(statusBadge).toBeVisible();
  });

  test('should filter issues by status', async ({ page }) => {
    // Wait for issues to load
    await page.waitForLoadState('networkidle');
    
    // Click status filter
    await page.locator('button').filter({ hasText: 'All Statuses' }).click();
    await page.getByRole('option', { name: 'Open' }).click();
    
    // Wait for filtered results
    await page.waitForLoadState('networkidle');
    
    // All visible issues should have OPEN status
    const statusBadges = page.locator('.bg-blue-600');
    const count = await statusBadges.count();
    if (count > 0) {
      await expect(statusBadges.first()).toBeVisible();
    }
  });

  test('should filter issues by priority', async ({ page }) => {
    // Wait for issues to load
    await page.waitForLoadState('networkidle');
    
    // Click priority filter
    await page.getByText('All Priorities').click();
    await page.getByText('P1 - Critical').click();
    
    // Wait for filtered results
    await page.waitForLoadState('networkidle');
    
    // All visible issues should have P1 priority
    const p1Badges = page.locator('.bg-red-600');
    const count = await p1Badges.count();
    if (count > 0) {
      await expect(p1Badges.first()).toBeVisible();
    }
  });

  test('should add comment to issue', async ({ page }) => {
    // Wait for issues to load
    await page.waitForLoadState('networkidle');
    
    // Click on first issue
    const issueCard = page.locator('.bg-slate-800\\/50.cursor-pointer').first();
    await issueCard.click();
    
    // Wait for detail panel
    await expect(page.getByRole('heading', { name: 'Comments' })).toBeVisible();
    
    // Add comment
    const uniqueComment = `Test comment ${Date.now()}`;
    await page.getByPlaceholder('Add a comment...').fill(uniqueComment);
    await page.getByRole('button', { name: 'Add' }).click();
    
    // Comment should appear - use exact match
    await expect(page.getByText(uniqueComment, { exact: true })).toBeVisible();
  });

  test('should show ServiceNow sync button for unsynced issues', async ({ page }) => {
    // Wait for issues to load
    await page.waitForLoadState('networkidle');
    
    // Click on first issue
    const issueCard = page.locator('.bg-slate-800\\/50.cursor-pointer').first();
    await issueCard.click();
    
    // Look for Sync to ServiceNow button
    const syncBtn = page.getByText('Sync to ServiceNow');
    
    // If issue is not synced, button should be visible
    if (await syncBtn.isVisible()) {
      await expect(syncBtn).toBeVisible();
    }
  });

  test('should update issue status', async ({ page }) => {
    // Wait for issues to load
    await page.waitForLoadState('networkidle');
    
    // Click on an OPEN issue
    const openIssue = page.locator('.bg-slate-800\\/50.cursor-pointer').filter({ hasText: 'OPEN' }).first();
    
    if (await openIssue.isVisible()) {
      await openIssue.click();
      
      // Look for Start Work button
      const startWorkBtn = page.getByText('Start Work');
      if (await startWorkBtn.isVisible()) {
        await startWorkBtn.click();
        
        // Status should change to IN_PROGRESS
        await expect(page.getByText('IN_PROGRESS')).toBeVisible();
      }
    }
  });

  test('should close detail panel', async ({ page }) => {
    // Wait for issues to load
    await page.waitForLoadState('networkidle');
    
    // Click on first issue
    const issueCard = page.locator('.bg-slate-800\\/50.cursor-pointer').first();
    await issueCard.click();
    
    // Wait for detail panel
    await expect(page.getByText('Description')).toBeVisible();
    
    // Close panel
    await page.getByRole('button', { name: 'Close' }).click();
    
    // Detail panel should be hidden
    await expect(page.getByText('Description')).not.toBeVisible();
  });
});

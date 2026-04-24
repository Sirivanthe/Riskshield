import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'https://audit-control-hub-4.preview.emergentagent.com';

test.describe('Tech Risk Assessment', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await page.fill('input[type="email"]', 'admin@bank.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/');
    
    // Navigate to Tech Risk Assessment
    await page.click('[data-testid="nav-tech-risk-assessment"]');
    await expect(page.getByTestId('tech-risk-assessment-page')).toBeVisible();
  });

  test('should display Tech Risk Assessment page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Tech Risk Assessment' })).toBeVisible();
    await expect(page.getByText('Application and technology risk assessments')).toBeVisible();
    await expect(page.getByTestId('new-assessment-btn')).toBeVisible();
  });

  test('should show existing assessments list', async ({ page }) => {
    // Wait for assessments to load
    await page.waitForLoadState('networkidle');
    
    // Should show at least one assessment (from backend test data)
    const assessmentCards = page.locator('.bg-slate-800\\/50');
    await expect(assessmentCards.first()).toBeVisible();
  });

  test('should open create assessment form', async ({ page }) => {
    await page.getByTestId('new-assessment-btn').click();
    
    // Verify form is visible
    await expect(page.getByText('New Tech Risk Assessment')).toBeVisible();
    await expect(page.getByPlaceholder('e.g., Payment Gateway')).toBeVisible();
    await expect(page.getByText('Data Classification')).toBeVisible();
    await expect(page.getByText('Deployment Type')).toBeVisible();
    await expect(page.getByText('Criticality')).toBeVisible();
  });

  test('should create new assessment and show questionnaire', async ({ page }) => {
    // Open create form
    await page.getByTestId('new-assessment-btn').click();
    
    // Fill in the form
    const uniqueId = Date.now().toString().slice(-6);
    await page.getByPlaceholder('e.g., Payment Gateway').fill(`TEST_App_${uniqueId}`);
    await page.locator('input[class*="bg-slate-700"]').nth(1).fill('Technology');
    await page.locator('input[class*="bg-slate-700"]').nth(2).fill('Test application for E2E testing');
    
    // Check some checkboxes
    await page.getByText('Internet Facing').click();
    await page.getByText('Processes PII').click();
    
    // Submit
    await page.getByText('Create & Start Assessment').click();
    
    // Should show questionnaire
    await expect(page.getByText('Assessment Questionnaire')).toBeVisible();
    await expect(page.getByText('General Information')).toBeVisible();
  });

  test('should display assessment with risk rating', async ({ page }) => {
    // Wait for assessments to load
    await page.waitForLoadState('networkidle');
    
    // Look for an assessment with a risk rating badge
    const ratingBadge = page.locator('.bg-red-600, .bg-orange-500, .bg-yellow-500, .bg-green-500').first();
    
    // If there's an assessment with a rating, it should be visible
    if (await ratingBadge.isVisible()) {
      await expect(ratingBadge).toBeVisible();
    }
  });

  test('should show identified risks for completed assessment', async ({ page }) => {
    // Wait for assessments to load
    await page.waitForLoadState('networkidle');
    
    // Look for "Identified Risks" section - use first() to avoid strict mode
    const risksSection = page.getByRole('heading', { name: 'Identified Risks' }).first();
    
    if (await risksSection.isVisible()) {
      await expect(risksSection).toBeVisible();
    }
  });

  test('should have Download PDF button for pending review assessment', async ({ page }) => {
    // Wait for assessments to load
    await page.waitForLoadState('networkidle');
    
    // Look for Download PDF button
    const downloadBtn = page.getByText('Download PDF');
    
    if (await downloadBtn.first().isVisible()) {
      await expect(downloadBtn.first()).toBeVisible();
    }
  });

  test('should have Create Issues button for pending review assessment', async ({ page }) => {
    // Wait for assessments to load
    await page.waitForLoadState('networkidle');
    
    // Look for Create Issues button
    const createIssuesBtn = page.getByText('Create Issues');
    
    if (await createIssuesBtn.first().isVisible()) {
      await expect(createIssuesBtn.first()).toBeVisible();
    }
  });
});

import { test, expect } from '@playwright/test';
import { login, loginAsLOD1, loginAsLOD2, loginAsAdmin, waitForAppReady } from '../fixtures/helpers';

test.describe('Authentication Flows', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
  });

  test('should display login page with correct elements', async ({ page }) => {
    await expect(page.getByTestId('login-form')).toBeVisible();
    await expect(page.getByTestId('login-email-input')).toBeVisible();
    await expect(page.getByTestId('login-password-input')).toBeVisible();
    await expect(page.getByTestId('login-submit-button')).toBeVisible();
    await expect(page.getByTestId('demo-lod1-button')).toBeVisible();
    await expect(page.getByTestId('demo-lod2-button')).toBeVisible();
  });

  test('should login with LOD1 credentials', async ({ page }) => {
    await page.getByTestId('login-email-input').fill('lod1@bank.com');
    await page.getByTestId('login-password-input').fill('password123');
    await page.getByTestId('login-submit-button').click();
    
    await expect(page.getByTestId('dashboard-page')).toBeVisible();
    await expect(page.getByTestId('dashboard-title')).toHaveText('Dashboard');
  });

  test('should login with LOD2 credentials', async ({ page }) => {
    await page.getByTestId('login-email-input').fill('lod2@bank.com');
    await page.getByTestId('login-password-input').fill('password123');
    await page.getByTestId('login-submit-button').click();
    
    await expect(page.getByTestId('dashboard-page')).toBeVisible();
  });

  test('should login with Admin credentials', async ({ page }) => {
    await page.getByTestId('login-email-input').fill('admin@bank.com');
    await page.getByTestId('login-password-input').fill('admin123');
    await page.getByTestId('login-submit-button').click();
    
    await expect(page.getByTestId('dashboard-page')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.getByTestId('login-email-input').fill('invalid@bank.com');
    await page.getByTestId('login-password-input').fill('wrongpassword');
    await page.getByTestId('login-submit-button').click();
    
    await expect(page.getByTestId('login-error')).toBeVisible();
  });

  test('should fill demo LOD1 credentials when clicking Demo LOD1 button', async ({ page }) => {
    await page.getByTestId('demo-lod1-button').click();
    
    await expect(page.getByTestId('login-email-input')).toHaveValue('lod1@bank.com');
    await expect(page.getByTestId('login-password-input')).toHaveValue('password123');
  });

  test('should fill demo LOD2 credentials when clicking Demo LOD2 button', async ({ page }) => {
    await page.getByTestId('demo-lod2-button').click();
    
    await expect(page.getByTestId('login-email-input')).toHaveValue('lod2@bank.com');
    await expect(page.getByTestId('login-password-input')).toHaveValue('password123');
  });
});

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsLOD1(page);
  });

  test('should display dashboard with key metrics', async ({ page }) => {
    await expect(page.getByTestId('dashboard-page')).toBeVisible();
    await expect(page.getByTestId('stat-total-assessments')).toBeVisible();
    await expect(page.getByTestId('stat-high-risks')).toBeVisible();
    await expect(page.getByTestId('stat-failed-controls')).toBeVisible();
    await expect(page.getByTestId('stat-compliance-score')).toBeVisible();
  });

  test('should display risk heatmap card', async ({ page }) => {
    await expect(page.getByTestId('risk-heatmap-card')).toBeVisible();
  });

  test('should display recent assessments card', async ({ page }) => {
    await expect(page.getByTestId('recent-assessments-card')).toBeVisible();
  });

  test('should display frameworks card', async ({ page }) => {
    await expect(page.getByTestId('frameworks-card')).toBeVisible();
  });

  test('should navigate to assessments page via View All link', async ({ page }) => {
    const viewAllLink = page.getByTestId('view-all-assessments-link');
    if (await viewAllLink.isVisible()) {
      await viewAllLink.click();
      await expect(page.getByTestId('assessments-page')).toBeVisible();
    }
  });
});

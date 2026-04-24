import { test, expect } from '@playwright/test';
import { loginAsLOD1 } from '../fixtures/helpers';

test.describe('Knowledge Graph Page', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsLOD1(page);
    await page.goto('/knowledge-graph', { waitUntil: 'domcontentloaded' });
  });

  test('should display knowledge graph page with correct elements', async ({ page }) => {
    await expect(page.getByTestId('knowledge-graph-page')).toBeVisible();
    await expect(page.getByTestId('kg-title')).toHaveText('Organizational Knowledge Graph');
  });

  test('should display search input and filter', async ({ page }) => {
    await expect(page.getByTestId('search-input')).toBeVisible();
    await expect(page.getByTestId('search-button')).toBeVisible();
    await expect(page.getByTestId('filter-type')).toBeVisible();
  });

  test('should display entities and relations cards', async ({ page }) => {
    await expect(page.getByTestId('entities-card')).toBeVisible();
    await expect(page.getByTestId('relations-card')).toBeVisible();
  });

  test('should filter entities by type', async ({ page }) => {
    await page.getByTestId('filter-type').selectOption('SYSTEM');
    
    // Wait for filter to apply
    await page.waitForLoadState('networkidle');
    
    // Verify filter is applied
    await expect(page.getByTestId('filter-type')).toHaveValue('SYSTEM');
  });

  test('should search for entities', async ({ page }) => {
    await page.getByTestId('search-input').fill('TEST');
    await page.getByTestId('search-button').click();
    
    // Wait for search results
    await page.waitForLoadState('networkidle');
  });
});

test.describe('Observability Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsLOD1(page);
    await page.goto('/observability', { waitUntil: 'domcontentloaded' });
  });

  test('should display observability page with correct elements', async ({ page }) => {
    await expect(page.getByTestId('observability-page')).toBeVisible();
    await expect(page.getByTestId('observability-title')).toHaveText('Model Observability');
  });

  test('should display model performance metrics', async ({ page }) => {
    await expect(page.getByTestId('total-requests-card')).toBeVisible();
    await expect(page.getByTestId('total-tokens-card')).toBeVisible();
    await expect(page.getByTestId('total-cost-card')).toBeVisible();
    await expect(page.getByTestId('avg-latency-card')).toBeVisible();
  });

  test('should display agent activity metrics', async ({ page }) => {
    await expect(page.getByTestId('total-activities-card')).toBeVisible();
  });

  test('should display knowledge graph metrics', async ({ page }) => {
    await expect(page.getByTestId('total-entities-card')).toBeVisible();
    await expect(page.getByTestId('total-relations-card')).toBeVisible();
  });
});

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsLOD1(page);
  });

  test('should navigate to all main pages', async ({ page }) => {
    // Dashboard
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('dashboard-page')).toBeVisible();
    
    // Assessments
    await page.goto('/assessments', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('assessments-page')).toBeVisible();
    
    // Knowledge Graph
    await page.goto('/knowledge-graph', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('knowledge-graph-page')).toBeVisible();
    
    // Observability
    await page.goto('/observability', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('observability-page')).toBeVisible();
  });

  test('should navigate using sidebar links', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    
    // Check if sidebar navigation exists
    const dashboardLink = page.locator('[data-testid="nav-dashboard"]');
    const assessmentsLink = page.locator('[data-testid="nav-assessments"]');
    const knowledgeGraphLink = page.locator('[data-testid="nav-knowledge-graph"]');
    const observabilityLink = page.locator('[data-testid="nav-observability"]');
    
    // Navigate via sidebar if links exist
    if (await assessmentsLink.isVisible()) {
      await assessmentsLink.click();
      await expect(page.getByTestId('assessments-page')).toBeVisible();
    }
    
    if (await knowledgeGraphLink.isVisible()) {
      await knowledgeGraphLink.click();
      await expect(page.getByTestId('knowledge-graph-page')).toBeVisible();
    }
    
    if (await observabilityLink.isVisible()) {
      await observabilityLink.click();
      await expect(page.getByTestId('observability-page')).toBeVisible();
    }
  });
});

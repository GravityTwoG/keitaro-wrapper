import { expect, test } from '@playwright/test';

test('creates a campaign with a geo flow and an offer flow', async ({ page }) => {
  const name = `E2E Campaign ${Date.now()}`;

  await page.goto('/campaigns/new');
  await expect(page.getByRole('heading', { name: 'Создать кампанию' })).toBeVisible();

  await page.getByTestId('campaign-name').fill(name);

  const geo = page.getByTestId('campaign-geo');
  await geo.fill('AU');
  await geo.press('Enter');

  const offer = page.getByTestId('offer-select');
  await offer.click();
  await offer.fill('E2E Offer Alpha');
  await page.getByRole('option', { name: /E2E Offer Alpha/ }).click();

  await page.getByTestId('create-submit').click();

  await expect(page).toHaveURL(/\/campaigns\/\d+$/);
  await expect(page.getByRole('heading', { name })).toBeVisible();

  await page.getByTestId('fetch-streams').click();
  await expect(page.getByText('AU → Google')).toBeVisible();
  await expect(page.getByTestId('campaign-offer-row-101')).toContainText('E2E Offer Alpha');
  await expect(page.getByTestId('campaign-offer-share-101')).toHaveText('100%');

  await page.getByRole('link', { name: 'Все кампании' }).click();
  await expect(
    page.locator('[data-testid^="campaign-row-"]').filter({ hasText: name }),
  ).toHaveCount(1);
});

test('shows validation errors before creating', async ({ page }) => {
  await page.goto('/campaigns/new');
  await page.getByTestId('create-submit').click();

  await expect(page.getByText('Введите название кампании')).toBeVisible();
  await expect(page.getByText('Укажите хотя бы одну страну')).toBeVisible();
  await expect(page.getByText('Выберите оффер')).toBeVisible();
});

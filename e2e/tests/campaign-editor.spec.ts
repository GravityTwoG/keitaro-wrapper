import { expect, test, type Page } from '@playwright/test';

async function loadCleanEditor(page: Page): Promise<void> {
  await page.goto('/campaigns/2');
  const cancel = page.getByTestId('cancel-offers');
  if (await cancel.isEnabled()) {
    await cancel.click();
    await expect(cancel).toBeDisabled();
  }
  const fetch = page.getByTestId('fetch-streams');
  await expect(fetch).toBeEnabled();
  await fetch.click();
  await expect(page.getByTestId('campaign-stream-102')).toBeVisible();
}

async function addOffer(page: Page, offerName: string): Promise<void> {
  await page.getByTestId('add-campaign-offer-102').click();
  const offer = page.getByTestId('offer-select');
  await offer.click();
  await offer.fill(offerName);
  await page.getByRole('option', { name: new RegExp(offerName) }).click();
  await page.getByTestId('add-offer-submit').click();
}

test.describe.configure({ mode: 'serial' });

test('fetches streams, keeps edits local and cancels edits', async ({ page }) => {
  await loadCleanEditor(page);

  await expect(page.getByTestId('campaign-stream-101')).toContainText('Поток без офферов');
  await expect(page.getByTestId('campaign-offer-row-3749')).toContainText('60%');
  await expect(page.getByTestId('campaign-offer-row-3717')).toContainText('40%');

  await addOffer(page, 'E2E Offer Delta');
  await expect(page.getByTestId('campaign-offer-row-104')).toBeVisible();
  await expect(page.getByTestId('campaign-stream-102')).toContainText('есть изменения');
  await expect(page.getByTestId('publish-offers')).toBeEnabled();

  await page.reload();
  await expect(page.getByTestId('campaign-offer-row-104')).toBeVisible();
  await expect(page.getByTestId('campaign-stream-102')).toContainText('есть изменения');

  await page.getByTestId('cancel-offers').click();
  await expect(page.getByTestId('campaign-offer-row-104')).toHaveCount(0);
  await expect(page.getByTestId('campaign-stream-102')).toContainText('опубликован');
  await expect(page.getByTestId('publish-offers')).toBeDisabled();
});

test('publishes edits, archives removed offers and restores them', async ({ page }) => {
  await loadCleanEditor(page);

  await addOffer(page, 'E2E Offer Delta');
  await page.getByTestId('publish-offers').click();
  await expect(page.getByTestId('campaign-stream-102')).toContainText('опубликован');
  await expect(page.getByTestId('campaign-offer-row-104')).toBeVisible();

  await page.getByTestId('remove-offer-3717').click();
  await expect(page.getByTestId('campaign-offer-row-3717')).toContainText('удалён');
  await expect(page.getByTestId('campaign-offer-share-3717')).toHaveText('0%');
  await expect(page.getByTestId('campaign-stream-102')).toContainText('есть изменения');

  await page.getByTestId('publish-offers').click();
  await expect(page.getByTestId('campaign-offer-row-3717')).toContainText('в архиве');

  await page.getByTestId('restore-offer-3717').click();
  await expect(page.getByTestId('campaign-offer-row-3717')).toContainText('новый');
  await expect(page.getByTestId('campaign-stream-102')).toContainText('есть изменения');

  await page.getByTestId('publish-offers').click();
  await expect(page.getByTestId('campaign-offer-row-3717')).toContainText('активен');
  await expect(page.getByTestId('publish-offers')).toBeDisabled();
});

test('pins a weight and recalculates only free offers', async ({ page }) => {
  await loadCleanEditor(page);
  const pinnedShare = Number.parseInt(
    (await page.getByTestId('campaign-offer-share-3749').textContent()) ?? '0',
    10,
  );
  await page.getByTestId('pin-offer-3749').click();
  await addOffer(page, 'E2E Offer Alpha');

  await expect(page.getByTestId('campaign-offer-share-3749')).toHaveText(`${pinnedShare}%`);
  const shares = await page
    .locator('[data-testid^="campaign-offer-share-"]')
    .allTextContents();
  expect(shares.length).toBeGreaterThan(1);
  expect(shares.reduce((sum, value) => sum + Number.parseInt(value, 10), 0)).toBe(100);

  await page.getByTestId('cancel-offers').click();
});

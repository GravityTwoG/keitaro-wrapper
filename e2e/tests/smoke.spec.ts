import { expect, test } from '@playwright/test';

test('campaigns page and Keitaro health are available', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { name: 'Кампании' })).toBeVisible();
  await expect(page.getByTestId('campaign-row-2')).toContainText('Austral Test');
  await expect(page.getByTestId('campaign-row-3')).toContainText('Пустая кампания');
  await expect(page.getByText('Keitaro на связи')).toBeVisible();
  await expect(page.getByTestId('campaigns-next')).toBeDisabled();

  await page.getByTestId('open-campaign-id').fill('2');
  await page.getByTestId('open-campaign-submit').click();
  await expect(page.getByRole('heading', { name: 'Austral Test' })).toBeVisible();
});

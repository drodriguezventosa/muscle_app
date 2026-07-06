import { expect, test } from '@playwright/test'

test('home page loads and shows the medical disclaimer', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.getByRole('note')).toBeVisible()
})

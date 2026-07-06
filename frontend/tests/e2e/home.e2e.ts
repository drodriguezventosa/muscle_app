import { expect, test } from '@playwright/test'

test('explorer page loads with heading, disclaimer and body map', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.getByRole('note')).toBeVisible()
  await expect(page.getByRole('group', { name: /mapa muscular/i })).toBeVisible()
})

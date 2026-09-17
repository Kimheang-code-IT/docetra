import { expect, test } from '@playwright/test'

test.describe('Locale switch', () => {
  test('auth shell switches to Khmer and persists across reload', async ({ page }) => {
    await page.goto('/auth/login')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1500)

    const switcher = page.getByRole('button', { name: /language/i }).first()
    await expect(switcher).toBeVisible()
    await expect(switcher).toContainText('English')

    await switcher.click()
    const khmerItem = page
      .locator('[role="menuitemcheckbox"], [role="menuitem"]')
      .filter({ hasText: 'ភាសាខ្មែរ' })
      .first()
    await khmerItem.click()
    await expect(switcher).toContainText('ភាសាខ្មែរ')

    await page.reload()
    await page.waitForLoadState('networkidle')
    await expect(page.getByRole('button', { name: /language/i }).first()).toContainText('ភាសាខ្មែរ')
  })
})

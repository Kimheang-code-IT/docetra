import { expect, test } from '@playwright/test'
import { apiPost, assertNoAppError, login } from './utils/auth'

test.describe('Meeting topic board flows', () => {
  test('meeting topic created through the API renders on the board', async ({ page }) => {
    await login(page)
    const title = `E2E topic ${Date.now()}`
    const response = await apiPost(page, '/api/v2/records/meeting_topic', { title })
    expect(response.ok(), await response.text()).toBeTruthy()

    await page.goto('/meetings/topics')
    await expect(page.locator('main').first()).toBeVisible({ timeout: 30_000 })
    await expect(page.locator('body')).toContainText(title, { timeout: 30_000 })
    await assertNoAppError(page)
  })

  test('meeting history workspace shows a created meeting', async ({ page }) => {
    await login(page)
    const title = `E2E meeting ${Date.now()}`
    const response = await apiPost(page, '/api/v2/records/meeting_history', {
      title,
      meetingDate: new Date(Date.now() + 86_400_000).toISOString(),
      mode: 'online',
    })
    expect(response.ok(), await response.text()).toBeTruthy()

    await page.goto('/meetings/history')
    await expect(page.locator('main').first()).toBeVisible({ timeout: 30_000 })
    await expect(page.locator('body')).toContainText(title, { timeout: 30_000 })
    await assertNoAppError(page)
  })
})

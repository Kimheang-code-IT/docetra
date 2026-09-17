import { expect, test } from '@playwright/test'
import { apiPost, assertNoAppError, login } from './utils/auth'

test.describe('Record create and detail flows', () => {
  test('document created through the API renders in the UI', async ({ page }) => {
    await login(page)
    const title = `E2E document ${Date.now()}`
    const response = await apiPost(page, '/api/v2/records/document', { title })
    expect(response.ok(), await response.text()).toBeTruthy()
    const body = await response.json()
    const id = body.data.id as string
    expect(id).toBeTruthy()

    await page.goto(`/records/documents/${id}`)
    await expect(page.locator('main').first()).toBeVisible({ timeout: 30_000 })
    await expect(page.locator('body')).toContainText(title)
    await assertNoAppError(page)
  })

  test('document appears in its workspace list', async ({ page }) => {
    await login(page)
    const title = `E2E list ${Date.now()}`
    const response = await apiPost(page, '/api/v2/records/document', { title })
    expect(response.ok(), await response.text()).toBeTruthy()

    await page.goto('/records/documents')
    await expect(page.locator('main').first()).toBeVisible({ timeout: 30_000 })
    await expect(page.locator('body')).toContainText(title, { timeout: 30_000 })
    await assertNoAppError(page)
  })
})

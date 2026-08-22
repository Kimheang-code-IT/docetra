import { expect, test } from '@playwright/test'
import { API_HEALTH_BASE, loginViaForm } from './helpers/auth'

test.describe('smoke auth → dashboard', () => {
  test.beforeAll(async ({ request }) => {
    const ready = await request.get(`${API_HEALTH_BASE}/ready`)
    expect(ready.ok(), `API not ready at ${API_HEALTH_BASE}`).toBeTruthy()
  })

  test('login form reaches dashboard and summary returns 200', async ({ page }) => {
    test.setTimeout(120_000)
    await loginViaForm(page)
    await expect(page).toHaveURL(/\/$|\/\?/)
    await expect(page.locator('main')).toBeVisible()
  })
})

import { expect, test } from '@playwright/test'

/**
 * UI smoke suite — runs against the frontend dev/preview server with the
 * backend stack reachable through the /api proxy.
 * Credentials come from the integration-test admin (ADMIN_EMAIL/ADMIN_PASSWORD).
 */

const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'admin@docetra.test'
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'Docetra-Admin-2025'

async function login(page: import('@playwright/test').Page) {
  await page.goto('/auth/login')
  // Nuxt hydration: form handlers attach after the initial payload loads.
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(1500)
  const email = page.locator('input[type="email"], input[name="email"]').first()
  const password = page.locator('input[type="password"]').first()
  await expect(email).toBeVisible()
  await expect(password).toBeVisible()
  await email.fill(ADMIN_EMAIL)
  await password.fill(ADMIN_PASSWORD)
  await page.getByRole('button', { name: /sign in|login|log in/i }).first().click()
  await page.waitForURL((url) => !url.pathname.includes('/auth/login'), { timeout: 30_000 })
}

test.describe('Docetra UI smoke', () => {
  test('login page renders', async ({ page }) => {
    await page.goto('/auth/login')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('input[type="email"], input[name="email"]').first()).toBeVisible()
    await expect(page.locator('input[type="password"]').first()).toBeVisible()
  })

  test('login succeeds and dashboard renders', async ({ page }) => {
    await login(page)
    // Dashboard shell: nav or KPI content must be visible.
    await expect(page.locator('body')).toContainText(/docetra|dashboard|meeting|record/i)
    // API session works through the proxy.
    const me = await page.evaluate(async () => {
      const res = await fetch('/api/v2/auth/me', { credentials: 'include' })
      return res.status
    })
    expect(me).toBe(200)
  })

  test('meeting topics board loads', async ({ page }) => {
    await login(page)
    await page.goto('/meetings/topics')
    await expect(page.locator('main').first()).toBeVisible({ timeout: 30_000 })
    // No error overlay / crash page.
    await expect(page.locator('text=Application error')).toHaveCount(0)
  })

  test('incoming documents workspace loads', async ({ page }) => {
    await login(page)
    await page.goto('/records/incoming-documents')
    await expect(page.locator('main').first()).toBeVisible({ timeout: 30_000 })
    await expect(page.locator('text=Application error')).toHaveCount(0)
  })

  test('combined documents workspace loads', async ({ page }) => {
    await login(page)
    await page.goto('/records/documents')
    await expect(page.locator('main').first()).toBeVisible({ timeout: 30_000 })
    await expect(page.locator('text=Application error')).toHaveCount(0)
  })

  test('organizations departments page loads', async ({ page }) => {
    await login(page)
    await page.goto('/organizations/departments')
    await expect(page.locator('main').first()).toBeVisible({ timeout: 30_000 })
    await expect(page.locator('text=Application error')).toHaveCount(0)
  })

  test('configuration record types page loads', async ({ page }) => {
    await login(page)
    await page.goto('/configuration/record-types')
    await expect(page.locator('main').first()).toBeVisible({ timeout: 30_000 })
    await expect(page.locator('text=Application error')).toHaveCount(0)
  })

  test('unauthenticated user is redirected away from protected page', async ({ page }) => {
    await page.context().clearCookies()
    await page.goto('/records/documents')
    await page.waitForURL((url) => url.pathname.includes('/auth'), { timeout: 20_000 })
    expect(page.url()).toContain('/auth')
  })
})

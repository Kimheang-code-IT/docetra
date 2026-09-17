import { expect, type Page } from '@playwright/test'

export const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'admin@docetra.test'
export const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'Docetra-Admin-2025'

export async function login(page: Page, email = ADMIN_EMAIL, password = ADMIN_PASSWORD): Promise<void> {
  await page.goto('/auth/login')
  // Nuxt hydration: form handlers attach after the initial payload loads.
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(1500)
  const emailInput = page.locator('input[type="email"], input[name="email"]').first()
  const passwordInput = page.locator('input[type="password"]').first()
  await expect(emailInput).toBeVisible()
  await expect(passwordInput).toBeVisible()
  await emailInput.fill(email)
  await passwordInput.fill(password)
  await page.getByRole('button', { name: /sign in|login|log in/i }).first().click()
  await page.waitForURL(url => !url.pathname.includes('/auth/login'), { timeout: 30_000 })
}

export async function assertNoAppError(page: Page): Promise<void> {
  await expect(page.locator('text=Application error')).toHaveCount(0)
}

function decodeCookie(value: string): string {
  try {
    return decodeURIComponent(value)
  }
  catch {
    return value
  }
}

export async function apiRequest(
  page: Page,
  method: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE',
  url: string,
  data?: unknown,
) {
  const token = (await page.context().cookies()).find(cookie => cookie.name === 'XSRF-TOKEN')?.value
  const headers: Record<string, string> = {}
  if (token) headers['X-CSRF-Token'] = decodeCookie(token)
  return page.request.fetch(url, { method, data, headers })
}

export function apiPost(page: Page, url: string, data?: unknown) {
  return apiRequest(page, 'POST', url, data)
}

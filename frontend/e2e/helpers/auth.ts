import { expect, type Page } from '@playwright/test'

export const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'admin@gmail.com'
export const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || '123456'
export const API_HEALTH_BASE = process.env.DOCETRA_API_BASE || 'http://localhost:8000'

export async function waitForNuxtHydration(page: Page) {
  await page.waitForFunction(() => {
    const form = document.querySelector('form') as (HTMLFormElement & { __vueParentComponent?: unknown }) | null
    const root = document.getElementById('__nuxt') as (HTMLElement & { __vue_app__?: unknown }) | null
    return Boolean(root?.__vue_app__ && (form ? form.__vueParentComponent : true))
  })
}

async function fillVueInput(locator: ReturnType<Page['locator']>, value: string) {
  await locator.waitFor({ state: 'visible' })
  await locator.click()
  await locator.fill(value)
  await expect(locator).toHaveValue(value)
}

export async function loginViaForm(page: Page) {
  await page.goto('/auth/login')
  await waitForNuxtHydration(page)
  await expect(page.getByRole('button', { name: 'Login', exact: true })).toBeVisible()

  const email = page.locator('[data-slot="input"] input, input[type="email"]').first()
  const password = page.locator('[data-slot="password"] input, input[type="password"]').first()
  await fillVueInput(email, ADMIN_EMAIL)
  await fillVueInput(password, ADMIN_PASSWORD)

  const loginWait = page.waitForResponse(
    (res) => res.url().includes('/api/v2/auth/login') && res.request().method() === 'POST',
    { timeout: 30_000 },
  )
  const dashboardWait = page.waitForResponse(
    (res) => res.url().includes('/api/v2/dashboard/summary') && res.request().method() === 'GET' && res.status() === 200,
    { timeout: 45_000 },
  )
  await page.getByRole('button', { name: 'Login', exact: true }).click()
  const login = await loginWait
  expect(login.status(), await login.text()).toBe(200)
  await page.waitForFunction(() => document.cookie.includes('XSRF-TOKEN'))
  expect((await dashboardWait).status()).toBe(200)
  await expect(page).not.toHaveURL(/\/auth\/login/)
}

export function isCollectionGet(url: string, pathname: string) {
  try {
    const parsed = new URL(url)
    return parsed.pathname === pathname || parsed.pathname.endsWith(pathname)
  }
  catch {
    return url.includes(pathname)
  }
}

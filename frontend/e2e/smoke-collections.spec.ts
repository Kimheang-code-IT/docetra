import { expect, test } from '@playwright/test'
import { isCollectionGet, loginViaForm, waitForNuxtHydration } from './helpers/auth'

test.describe('smoke collections after real login', () => {
  test.describe.configure({ mode: 'serial' })

  test('documents list returns an envelope', async ({ page }) => {
    test.setTimeout(120_000)
    await loginViaForm(page)

    const listWait = page.waitForResponse(
      (res) => isCollectionGet(res.url(), '/api/v2/records/document') && res.request().method() === 'GET',
      { timeout: 45_000 },
    )
    await page.goto('/records/documents')
    await waitForNuxtHydration(page)
    const list = await listWait
    expect(list.status()).toBe(200)
    const body = await list.json()
    expect(body).toHaveProperty('data')
    expect(Array.isArray(body.data)).toBe(true)
    await expect(page.locator('main')).toBeVisible()
  })

  test('departments list returns 200', async ({ page }) => {
    test.setTimeout(120_000)
    await loginViaForm(page)

    const listWait = page.waitForResponse(
      (res) => isCollectionGet(res.url(), '/api/v2/organizations/department') && res.request().method() === 'GET',
      { timeout: 45_000 },
    )
    await page.goto('/organizations/departments')
    await waitForNuxtHydration(page)
    expect((await listWait).status()).toBe(200)
    await expect(page.locator('main')).toBeVisible()
  })

  test('meeting topics board GET returns 200', async ({ page }) => {
    test.setTimeout(120_000)
    await loginViaForm(page)

    const listWait = page.waitForResponse(
      (res) => isCollectionGet(res.url(), '/api/v2/records/meeting_topic') && res.request().method() === 'GET',
      { timeout: 45_000 },
    )
    await page.goto('/meetings/topics')
    await waitForNuxtHydration(page)
    expect((await listWait).status()).toBe(200)
    await expect(page.locator('main')).toBeVisible()
  })

  test('officers list calls /api/v2/officers', async ({ page }) => {
    test.setTimeout(120_000)
    await loginViaForm(page)

    const listWait = page.waitForResponse(
      (res) => isCollectionGet(res.url(), '/api/v2/officers') && res.request().method() === 'GET',
      { timeout: 45_000 },
    )
    await page.goto('/officers')
    await waitForNuxtHydration(page)
    expect((await listWait).status()).toBe(200)
    await expect(page.locator('main')).toBeVisible()
  })

  test('sector list calls /api/v2/sector', async ({ page }) => {
    test.setTimeout(120_000)
    await loginViaForm(page)

    const listWait = page.waitForResponse(
      (res) => isCollectionGet(res.url(), '/api/v2/sector') && res.request().method() === 'GET',
      { timeout: 45_000 },
    )
    await page.goto('/sector')
    await waitForNuxtHydration(page)
    expect((await listWait).status()).toBe(200)
    await expect(page.locator('main')).toBeVisible()
  })

  test('purpose list calls /api/v2/purpose', async ({ page }) => {
    test.setTimeout(120_000)
    await loginViaForm(page)

    const listWait = page.waitForResponse(
      (res) => isCollectionGet(res.url(), '/api/v2/purpose') && res.request().method() === 'GET',
      { timeout: 45_000 },
    )
    await page.goto('/purpose')
    await waitForNuxtHydration(page)
    expect((await listWait).status()).toBe(200)
    await expect(page.locator('main')).toBeVisible()
  })

  test('settings app-info GET returns 200', async ({ page }) => {
    test.setTimeout(120_000)
    await loginViaForm(page)

    const infoWait = page.waitForResponse(
      (res) => isCollectionGet(res.url(), '/api/v2/settings/app-info') && res.request().method() === 'GET',
      { timeout: 45_000 },
    )
    await page.goto('/settings/app-info')
    await waitForNuxtHydration(page)
    expect((await infoWait).status()).toBe(200)
    await expect(page.locator('main')).toBeVisible()
  })

  test('logout POST sends CSRF header', async ({ page }) => {
    test.setTimeout(120_000)
    await loginViaForm(page)

    const logoutWait = page.waitForRequest(
      (req) => req.url().includes('/api/v2/auth/logout') && req.method() === 'POST',
      { timeout: 30_000 },
    )
    await page.getByRole('button', { name: /System Administrator|admin@gmail.com/i }).click()
    const logoutItem = page.getByRole('menuitem', { name: /log out/i })
    if (await logoutItem.count()) {
      await logoutItem.click()
    }
    else {
      await page.getByText(/log out/i).click()
    }
    const logout = await logoutWait
    const csrf = logout.headers()['x-csrf-token']
    expect(csrf, 'logout must send X-CSRF-Token').toBeTruthy()
    await expect(page).toHaveURL(/\/auth\/login/)
  })
})

# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: smoke-auth-dashboard.spec.ts >> smoke auth → dashboard >> login form reaches dashboard and summary returns 200
- Location: e2e\smoke-auth-dashboard.spec.ts:10:3

# Error details

```
Test timeout of 120000ms exceeded.
```

```
Error: page.waitForFunction: Test timeout of 120000ms exceeded.
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e3]:
    - button "Language" [ref=e5]:
      - generic [ref=e7]: English
    - generic [ref=e13]:
      - generic [ref=e14]:
        - img "Logo" [ref=e16]
        - generic [ref=e17]: Login
      - generic [ref=e19]:
        - generic [ref=e20]:
          - generic [ref=e21]: Email*
          - textbox "Email*" [ref=e26]:
            - /placeholder: Enter your email
        - generic [ref=e27]:
          - generic [ref=e28]: Password*
          - generic [ref=e32]:
            - textbox "Password*" [ref=e33]:
              - /placeholder: Enter your password
            - button "Show password" [ref=e35]
        - button "Login" [ref=e37]
      - generic [ref=e40]:
        - separator [ref=e41]:
          - generic [ref=e43]: or
        - button "Login with Google" [ref=e46]
        - link "Forgot password?" [ref=e54] [cursor=pointer]:
          - /url: /auth/forget-password
        - generic [ref=e55]: © Docetra and contributors
  - region "Notifications (F8)":
    - list
```

# Test source

```ts
  1  | import { expect, type Page } from '@playwright/test'
  2  | 
  3  | export const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'admin@gmail.com'
  4  | export const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || '123456'
  5  | export const API_HEALTH_BASE = process.env.DOCETRA_API_BASE || 'http://localhost:8000'
  6  | 
  7  | export async function waitForNuxtHydration(page: Page) {
> 8  |   await page.waitForFunction(() => {
     |              ^ Error: page.waitForFunction: Test timeout of 120000ms exceeded.
  9  |     const form = document.querySelector('form') as (HTMLFormElement & { __vueParentComponent?: unknown }) | null
  10 |     const root = document.getElementById('__nuxt') as (HTMLElement & { __vue_app__?: unknown }) | null
  11 |     return Boolean(root?.__vue_app__ && (form ? form.__vueParentComponent : true))
  12 |   })
  13 | }
  14 | 
  15 | async function fillVueInput(locator: ReturnType<Page['locator']>, value: string) {
  16 |   await locator.waitFor({ state: 'visible' })
  17 |   await locator.click()
  18 |   await locator.fill(value)
  19 |   await expect(locator).toHaveValue(value)
  20 | }
  21 | 
  22 | export async function loginViaForm(page: Page) {
  23 |   await page.goto('/auth/login')
  24 |   await waitForNuxtHydration(page)
  25 |   await expect(page.getByRole('button', { name: 'Login', exact: true })).toBeVisible()
  26 | 
  27 |   const email = page.locator('[data-slot="input"] input, input[type="email"]').first()
  28 |   const password = page.locator('[data-slot="password"] input, input[type="password"]').first()
  29 |   await fillVueInput(email, ADMIN_EMAIL)
  30 |   await fillVueInput(password, ADMIN_PASSWORD)
  31 | 
  32 |   const loginWait = page.waitForResponse(
  33 |     (res) => res.url().includes('/api/v2/auth/login') && res.request().method() === 'POST',
  34 |     { timeout: 30_000 },
  35 |   )
  36 |   const dashboardWait = page.waitForResponse(
  37 |     (res) => res.url().includes('/api/v2/dashboard/summary') && res.request().method() === 'GET' && res.status() === 200,
  38 |     { timeout: 45_000 },
  39 |   )
  40 |   await page.getByRole('button', { name: 'Login', exact: true }).click()
  41 |   const login = await loginWait
  42 |   expect(login.status(), await login.text()).toBe(200)
  43 |   await page.waitForFunction(() => document.cookie.includes('XSRF-TOKEN'))
  44 |   expect((await dashboardWait).status()).toBe(200)
  45 |   await expect(page).not.toHaveURL(/\/auth\/login/)
  46 | }
  47 | 
  48 | export function isCollectionGet(url: string, pathname: string) {
  49 |   try {
  50 |     const parsed = new URL(url)
  51 |     return parsed.pathname === pathname || parsed.pathname.endsWith(pathname)
  52 |   }
  53 |   catch {
  54 |     return url.includes(pathname)
  55 |   }
  56 | }
  57 | 
```
# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: smoke-collections.spec.ts >> smoke collections after real login >> officers list calls /api/v2/officers
- Location: e2e\smoke-collections.spec.ts:53:3

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 200
Received: 404
```

# Page snapshot

```yaml
- generic [active]:
  - generic:
    - generic [ref=f1e1]:
      - generic [ref=f1e2]:
        - generic [ref=f1e3]:
          - link "Docetra" [ref=f1e4] [cursor=pointer]:
            - /url: /
            - img "Docetra logo" [ref=f1e6]
          - button "Search… Ctrl k" [ref=f1e9]:
            - generic [ref=f1e11]: Search…
            - generic [ref=f1e12]:
              - generic [ref=f1e13]: Ctrl
              - generic [ref=f1e14]: k
        - navigation [ref=f1e16]:
          - list [ref=f1e17]:
            - listitem [ref=f1e18]:
              - link "Dashboard" [ref=f1e19] [cursor=pointer]:
                - /url: /
            - listitem [ref=f1e22]:
              - button "Meeting" [ref=f1e23]
            - listitem [ref=f1e28]:
              - button "Record" [ref=f1e29]
            - listitem [ref=f1e34]:
              - button "Organization" [ref=f1e35]
            - listitem [ref=f1e40]:
              - button "Portal" [ref=f1e41]
            - listitem [ref=f1e46]:
              - button "User Management" [ref=f1e47]
            - listitem [ref=f1e52]:
              - button "Configuration" [expanded] [ref=f1e53]
              - region "Configuration" [ref=f1e58]:
                - list [ref=f1e59]:
                  - listitem [ref=f1e60]:
                    - link "Record Type" [ref=f1e61] [cursor=pointer]:
                      - /url: /configuration/record-types
                  - listitem [ref=f1e63]:
                    - link "Attribute Catalog" [ref=f1e64] [cursor=pointer]:
                      - /url: /configuration/record-attributes
            - listitem [ref=f1e66]:
              - button "Settings" [ref=f1e67]
        - button "User System Administrator" [ref=f1e74]:
          - img "User" [ref=f1e76]
          - generic [ref=f1e77]: System Administrator
      - separator
      - generic [ref=f1e79]:
        - generic [ref=f1e80]:
          - generic [ref=f1e81]:
            - button "Collapse sidebar" [ref=f1e82]
            - heading "Officer" [level=1] [ref=f1e84]
          - generic [ref=f1e87]:
            - button "Refresh" [ref=f1e88]
            - button "Actions" [ref=f1e90]
            - button "New Officer" [ref=f1e92]
        - main [ref=f1e95]:
          - generic [ref=f1e99]:
            - generic [ref=f1e101]:
              - textbox "Search...." [ref=f1e103]
              - generic [ref=f1e106]:
                - group "Updated" [ref=f1e109]:
                  - spinbutton "month," [ref=f1e110]: mm
                  - generic [ref=f1e111]: /
                  - spinbutton "day," [ref=f1e112]: dd
                  - generic [ref=f1e113]: /
                  - spinbutton "year," [ref=f1e114]: yyyy
                  - generic [ref=f1e115]: ","
                  - spinbutton "hour," [ref=f1e116]: ––
                  - generic [ref=f1e117]: ":"
                  - spinbutton "minute," [ref=f1e118]: ––
                  - spinbutton "AM/PM" [ref=f1e119]: AM
                  - spinbutton "month," [ref=f1e121]: mm
                  - generic [ref=f1e122]: /
                  - spinbutton "day," [ref=f1e123]: dd
                  - generic [ref=f1e124]: /
                  - spinbutton "year," [ref=f1e125]: yyyy
                  - generic [ref=f1e126]: ","
                  - spinbutton "hour," [ref=f1e127]: ––
                  - generic [ref=f1e128]: ":"
                  - spinbutton "minute," [ref=f1e129]: ––
                  - spinbutton "AM/PM" [ref=f1e130]: AM
                  - button "Updated" [ref=f1e132]
                  - textbox [ref=f1e134]: undefined - undefined
                - button "Sort" [ref=f1e135]
            - generic [ref=f1e137]:
              - paragraph [ref=f1e138]: "[GET] \"/api/v2/officers?page=1&limit=20&sort=-updatedAt&view=table\": 404 Not Found"
              - button "Retry" [ref=f1e139]
    - alert [ref=f1e140]: "Notification API Error: 404Something went wrong"
  - generic [ref=f1e141]:
    - button "Toggle Nuxt DevTools" [ref=f1e142] [cursor=pointer]
    - generic "Page load time" [ref=f1e146]:
      - generic [ref=f1e147]: "644"
      - generic [ref=f1e148]: ms
    - button "Toggle Component Inspector" [ref=f1e150] [cursor=pointer]
  - region "Notifications (F8)":
    - list [ref=f1e156]:
      - listitem [ref=f1e157]:
        - generic [ref=f1e158]:
          - generic [ref=f1e159]: "API Error: 404"
          - generic [ref=f1e160]: Something went wrong
        - button "Close" [ref=f1e162]
        - progressbar "96%" [ref=f1e165]
```

# Test source

```ts
  1   | import { expect, test } from '@playwright/test'
  2   | import { isCollectionGet, loginViaForm, waitForNuxtHydration } from './helpers/auth'
  3   | 
  4   | test.describe('smoke collections after real login', () => {
  5   |   test.describe.configure({ mode: 'serial' })
  6   | 
  7   |   test('documents list returns an envelope', async ({ page }) => {
  8   |     test.setTimeout(120_000)
  9   |     await loginViaForm(page)
  10  | 
  11  |     const listWait = page.waitForResponse(
  12  |       (res) => isCollectionGet(res.url(), '/api/v2/records/document') && res.request().method() === 'GET',
  13  |       { timeout: 45_000 },
  14  |     )
  15  |     await page.goto('/records/documents')
  16  |     await waitForNuxtHydration(page)
  17  |     const list = await listWait
  18  |     expect(list.status()).toBe(200)
  19  |     const body = await list.json()
  20  |     expect(body).toHaveProperty('data')
  21  |     expect(Array.isArray(body.data)).toBe(true)
  22  |     await expect(page.locator('main')).toBeVisible()
  23  |   })
  24  | 
  25  |   test('departments list returns 200', async ({ page }) => {
  26  |     test.setTimeout(120_000)
  27  |     await loginViaForm(page)
  28  | 
  29  |     const listWait = page.waitForResponse(
  30  |       (res) => isCollectionGet(res.url(), '/api/v2/organizations/department') && res.request().method() === 'GET',
  31  |       { timeout: 45_000 },
  32  |     )
  33  |     await page.goto('/organizations/departments')
  34  |     await waitForNuxtHydration(page)
  35  |     expect((await listWait).status()).toBe(200)
  36  |     await expect(page.locator('main')).toBeVisible()
  37  |   })
  38  | 
  39  |   test('meeting topics board GET returns 200', async ({ page }) => {
  40  |     test.setTimeout(120_000)
  41  |     await loginViaForm(page)
  42  | 
  43  |     const listWait = page.waitForResponse(
  44  |       (res) => isCollectionGet(res.url(), '/api/v2/records/meeting_topic') && res.request().method() === 'GET',
  45  |       { timeout: 45_000 },
  46  |     )
  47  |     await page.goto('/meetings/topics')
  48  |     await waitForNuxtHydration(page)
  49  |     expect((await listWait).status()).toBe(200)
  50  |     await expect(page.locator('main')).toBeVisible()
  51  |   })
  52  | 
  53  |   test('officers list calls /api/v2/officers', async ({ page }) => {
  54  |     test.setTimeout(120_000)
  55  |     await loginViaForm(page)
  56  | 
  57  |     const listWait = page.waitForResponse(
  58  |       (res) => isCollectionGet(res.url(), '/api/v2/officers') && res.request().method() === 'GET',
  59  |       { timeout: 45_000 },
  60  |     )
  61  |     await page.goto('/officers')
  62  |     await waitForNuxtHydration(page)
> 63  |     expect((await listWait).status()).toBe(200)
      |                                       ^ Error: expect(received).toBe(expected) // Object.is equality
  64  |     await expect(page.locator('main')).toBeVisible()
  65  |   })
  66  | 
  67  |   test('sector list calls /api/v2/sector', async ({ page }) => {
  68  |     test.setTimeout(120_000)
  69  |     await loginViaForm(page)
  70  | 
  71  |     const listWait = page.waitForResponse(
  72  |       (res) => isCollectionGet(res.url(), '/api/v2/sector') && res.request().method() === 'GET',
  73  |       { timeout: 45_000 },
  74  |     )
  75  |     await page.goto('/sector')
  76  |     await waitForNuxtHydration(page)
  77  |     expect((await listWait).status()).toBe(200)
  78  |     await expect(page.locator('main')).toBeVisible()
  79  |   })
  80  | 
  81  |   test('purpose list calls /api/v2/purpose', async ({ page }) => {
  82  |     test.setTimeout(120_000)
  83  |     await loginViaForm(page)
  84  | 
  85  |     const listWait = page.waitForResponse(
  86  |       (res) => isCollectionGet(res.url(), '/api/v2/purpose') && res.request().method() === 'GET',
  87  |       { timeout: 45_000 },
  88  |     )
  89  |     await page.goto('/purpose')
  90  |     await waitForNuxtHydration(page)
  91  |     expect((await listWait).status()).toBe(200)
  92  |     await expect(page.locator('main')).toBeVisible()
  93  |   })
  94  | 
  95  |   test('settings app-info GET returns 200', async ({ page }) => {
  96  |     test.setTimeout(120_000)
  97  |     await loginViaForm(page)
  98  | 
  99  |     const infoWait = page.waitForResponse(
  100 |       (res) => isCollectionGet(res.url(), '/api/v2/settings/app-info') && res.request().method() === 'GET',
  101 |       { timeout: 45_000 },
  102 |     )
  103 |     await page.goto('/settings/app-info')
  104 |     await waitForNuxtHydration(page)
  105 |     expect((await infoWait).status()).toBe(200)
  106 |     await expect(page.locator('main')).toBeVisible()
  107 |   })
  108 | 
  109 |   test('logout POST sends CSRF header', async ({ page }) => {
  110 |     test.setTimeout(120_000)
  111 |     await loginViaForm(page)
  112 | 
  113 |     const logoutWait = page.waitForRequest(
  114 |       (req) => req.url().includes('/api/v2/auth/logout') && req.method() === 'POST',
  115 |       { timeout: 30_000 },
  116 |     )
  117 |     await page.getByRole('button', { name: /System Administrator|admin@gmail.com/i }).click()
  118 |     const logoutItem = page.getByRole('menuitem', { name: /log out/i })
  119 |     if (await logoutItem.count()) {
  120 |       await logoutItem.click()
  121 |     }
  122 |     else {
  123 |       await page.getByText(/log out/i).click()
  124 |     }
  125 |     const logout = await logoutWait
  126 |     const csrf = logout.headers()['x-csrf-token']
  127 |     expect(csrf, 'logout must send X-CSRF-Token').toBeTruthy()
  128 |     await expect(page).toHaveURL(/\/auth\/login/)
  129 |   })
  130 | })
  131 | 
```
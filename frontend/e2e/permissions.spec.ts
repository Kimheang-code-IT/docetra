import { expect, test } from '@playwright/test'
import { apiPost, login } from './utils/auth'

test.describe('Permission gating', () => {
  test('anonymous API access to protected collections is denied', async ({ request }) => {
    const users = await request.get('/api/v2/users')
    expect([401, 403]).toContain(users.status())
    const documents = await request.get('/api/v2/records/document')
    expect([401, 403]).toContain(documents.status())
  })

  test('restricted user cannot open user management', async ({ page, browser }) => {
    await login(page)
    const suffix = Date.now().toString(36)
    const roleResponse = await apiPost(page, '/api/v2/users/roles', {
      code: `E2E_${suffix}`.toUpperCase(),
      name: `E2E Restricted ${suffix}`,
      status: 'active',
      permissionRows: [{ documentType: 'document', actions: ['view'], level: 0 }],
    })
    expect(roleResponse.ok(), await roleResponse.text()).toBeTruthy()
    const role = (await roleResponse.json()).data

    const email = `e2e-restricted-${suffix}@docetra.test`
    const password = 'Restricted-2025'
    const userResponse = await apiPost(page, '/api/v2/users', {
      email,
      name: 'E2E Restricted',
      password,
      roleId: role.id,
      status: 'active',
    })
    expect(userResponse.ok(), await userResponse.text()).toBeTruthy()

    const context = await browser.newContext()
    const restricted = await context.newPage()
    try {
      await login(restricted, email, password)
      await restricted.goto('/user-management/users')
      await restricted.waitForLoadState('networkidle')
      expect(restricted.url()).not.toContain('/user-management/users')

      const api = await restricted.request.get('/api/v2/users')
      expect([401, 403, 404]).toContain(api.status())
    }
    finally {
      await context.close()
    }
  })
})

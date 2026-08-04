import type { AuthUser } from '~/types/auth-user'

export type MockLoginAccount = {
  email: string
  password: string
  user: AuthUser
}

/** Frontend-only demo accounts. Replace with real API auth later. */
export const MOCK_LOGIN_ACCOUNTS: MockLoginAccount[] = [
  {
    email: 'admin@gmail.com',
    password: '123456',
    user: {
      id: 1,
      name: 'System Administrator',
      email: 'admin@gmail.com',
      role: 'SuperAdmin',
      avatar: 'https://ui-avatars.com/api/?name=System+Administrator&background=e8472a&color=fff',
      pageAccess: ['ALL_PAGES'],
    },
  },
  {
    email: 'admin@docetra.local',
    password: '123456',
    user: {
      id: 2,
      name: 'Docetra Admin',
      email: 'admin@docetra.local',
      role: 'Admin',
      avatar: 'https://ui-avatars.com/api/?name=Docetra+Admin&background=3a539f&color=fff',
      pageAccess: ['ALL_PAGES'],
    },
  },
]

export const MOCK_AUTH_TOKEN = 'mock-docetra-frontend-token'

export function authenticateMock(email: string, password: string): AuthUser | null {
  const normalized = email.trim().toLowerCase()
  const account = MOCK_LOGIN_ACCOUNTS.find(a => a.email.toLowerCase() === normalized)
  if (!account || account.password !== password) return null
  return account.user
}

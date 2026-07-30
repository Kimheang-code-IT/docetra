import type { AuthUser } from '~/types/auth-user'

export type MockLoginAccount = {
  email: string
  password: string
  user: AuthUser
}

/** Frontend-only demo accounts. Replace with real API auth later. */
export const MOCK_LOGIN_ACCOUNTS: MockLoginAccount[] = [
  {
    email: 'heang@gmail.com',
    password: '123456',
    user: {
      id: 1,
      name: 'Moeng Kimheang',
      email: 'heang@gmail.com',
      role: 'SuperAdmin',
      avatar: 'https://ui-avatars.com/api/?name=Moeng+Kimheang&background=008037&color=fff',
      pageAccess: ['ALL_PAGES'],
    },
  },
  {
    email: 'admin@pdme.gov.kh',
    password: '123456',
    user: {
      id: 2,
      name: 'PDME Admin',
      email: 'admin@pdme.gov.kh',
      role: 'Admin',
      avatar: 'https://ui-avatars.com/api/?name=PDME+Admin&background=0f766e&color=fff',
      pageAccess: ['ALL_PAGES'],
    },
  },
]

export const MOCK_AUTH_TOKEN = 'mock-pdme-frontend-token'

export function authenticateMock(email: string, password: string): AuthUser | null {
  const normalized = email.trim().toLowerCase()
  const match = MOCK_LOGIN_ACCOUNTS.find(
    (account) => account.email.toLowerCase() === normalized && account.password === password,
  )
  return match ? { ...match.user, email: match.user.email } : null
}

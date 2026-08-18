import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import type { ApiResponse } from '~/types/docetra/common'
import type { AuthUser } from '~/types/auth-user'
import { mockLatency, ok } from '~/mocks/query'

type LoginResult = { token?: string; user: AuthUser }

function usesMockData() {
  return useRuntimeConfig().public.useMockData !== false
}

export async function loginWithCredentials(email: string, password: string) {
  if (!usesMockData()) {
    return useApi().post<ApiResponse<LoginResult>>(ApiEndpoints.AUTH_LOGIN, { email, password }, {
      suppressErrorToast: true,
      suppressAccessAlert: true,
    })
  }
  const { authenticateMock, MOCK_AUTH_TOKEN } = await import('~/utils/auth/mock-login')
  await mockLatency(null, 80)
  const user = authenticateMock(email, password)
  if (!user) throw createError({ statusCode: 401, statusMessage: 'Invalid credentials' })
  return ok({ token: MOCK_AUTH_TOKEN, user })
}

export async function logoutSession() {
  if (usesMockData()) return ok({ loggedOut: true })
  return useApi().post<ApiResponse<{ loggedOut: boolean }>>(ApiEndpoints.AUTH_LOGOUT, {}, {
    suppressErrorToast: true,
    suppressAccessAlert: true,
  })
}

export async function getCurrentSession() {
  return useApi().get<ApiResponse<AuthUser>>(ApiEndpoints.AUTH_ME, {
    requestKey: 'auth-session',
    cancelPrevious: true,
    suppressErrorToast: true,
    suppressAccessAlert: true,
  })
}

export async function requestPasswordReset(email: string) {
  if (!usesMockData()) return useApi().post<ApiResponse<{ sent: boolean }>>(ApiEndpoints.AUTH_FORGOT_PASSWORD, { email })
  await mockLatency(null, 80)
  return ok({ sent: true })
}

export async function verifyPasswordResetCode(email: string, code: string) {
  if (!usesMockData()) return useApi().post<ApiResponse<{ verified: boolean }>>(ApiEndpoints.AUTH_RESET_VERIFY, { email, code })
  const { MOCK_RESET_CODE } = await import('~/utils/auth/password-reset')
  await mockLatency(null, 80)
  if (code !== MOCK_RESET_CODE) throw createError({ statusCode: 400, statusMessage: 'Invalid code' })
  return ok({ verified: true })
}

export async function resendPasswordResetCode(email: string) {
  if (!usesMockData()) return useApi().post<ApiResponse<{ sent: boolean }>>(ApiEndpoints.AUTH_RESET_RESEND, { email })
  await mockLatency(null, 80)
  return ok({ sent: true })
}

export async function resetPasswordWithCode(input: {
  email: string
  code: string
  password: string
  passwordConfirmation: string
}) {
  if (!usesMockData()) return useApi().post<ApiResponse<{ reset: boolean }>>(ApiEndpoints.AUTH_RESET_PASSWORD, input)
  const { MOCK_RESET_CODE } = await import('~/utils/auth/password-reset')
  await mockLatency(null, 80)
  if (input.code !== MOCK_RESET_CODE || input.password !== input.passwordConfirmation) {
    throw createError({ statusCode: 400, statusMessage: 'Invalid reset request' })
  }
  return ok({ reset: true })
}

export async function changePassword(input: {
  currentPassword: string
  password: string
  passwordConfirmation: string
}) {
  if (!usesMockData()) {
    return useApi().post<ApiResponse<{ changed: boolean }>>(ApiEndpoints.AUTH_CHANGE_PASSWORD, input)
  }
  const auth = useAuthStore()
  const email = auth.user?.email
  if (!email) throw createError({ statusCode: 401, statusMessage: 'Not signed in' })
  if (input.password !== input.passwordConfirmation) {
    throw createError({ statusCode: 400, statusMessage: 'Passwords do not match' })
  }
  const { findMockLoginAccount } = await import('~/utils/auth/mock-login')
  await mockLatency(null, 80)
  const account = findMockLoginAccount(email)
  if (!account || account.password !== input.currentPassword) {
    throw createError({ statusCode: 401, statusMessage: 'Current password is incorrect' })
  }
  account.password = input.password
  return ok({ changed: true })
}

export async function updateProfileAvatar(avatar: string) {
  if (!usesMockData()) {
    return useApi().put<ApiResponse<{ avatar: string }>>(ApiEndpoints.AUTH_PROFILE_AVATAR, { avatar })
  }
  const auth = useAuthStore()
  const email = auth.user?.email
  if (!email) throw createError({ statusCode: 401, statusMessage: 'Not signed in' })
  const { findMockLoginAccount } = await import('~/utils/auth/mock-login')
  await mockLatency(null, 80)
  const account = findMockLoginAccount(email)
  if (account) account.user.avatar = avatar
  auth.updateUser({ avatar })
  return ok({ avatar })
}

export async function removeProfileAvatar() {
  if (!usesMockData()) {
    return useApi().delete<ApiResponse<{ removed: boolean }>>(ApiEndpoints.AUTH_PROFILE_AVATAR)
  }
  const auth = useAuthStore()
  const email = auth.user?.email
  if (!email) throw createError({ statusCode: 401, statusMessage: 'Not signed in' })
  const { findMockLoginAccount } = await import('~/utils/auth/mock-login')
  await mockLatency(null, 80)
  const account = findMockLoginAccount(email)
  if (account) delete account.user.avatar
  auth.updateUser({ avatar: undefined })
  return ok({ removed: true })
}

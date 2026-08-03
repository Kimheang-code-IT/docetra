import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { authenticateMock, MOCK_AUTH_TOKEN } from '~/utils/auth/mock-login'
import { MOCK_RESET_CODE } from '~/utils/auth/password-reset'
import { mockLatency, ok } from '~/mocks/query'

function useMock() {
  return useRuntimeConfig().public.useMockData !== false
}

export async function loginWithCredentials(email: string, password: string) {
  if (useMock()) {
    await mockLatency(null, 250)
    const user = authenticateMock(email, password)
    if (!user) {
      throw createError({ statusCode: 401, statusMessage: 'Invalid credentials' })
    }
    return ok({ token: MOCK_AUTH_TOKEN, user })
  }
  const api = useApi()
  return await api.post(ApiEndpoints.AUTH_LOGIN, { email, password })
}

export async function requestPasswordReset(email: string) {
  if (useMock()) {
    await mockLatency(null, 400)
    return ok({ sent: true, email, mockCode: MOCK_RESET_CODE })
  }
  const api = useApi()
  return await api.post(ApiEndpoints.AUTH_FORGOT_PASSWORD, { email })
}

/** Verify the 6-digit reset code emailed after forgot-password. */
export async function verifyPasswordResetCode(email: string, code: string) {
  if (useMock()) {
    await mockLatency(null, 400)
    const normalized = String(code || '').trim()
    if (normalized.length !== 6 || normalized !== MOCK_RESET_CODE) {
      throw createError({ statusCode: 400, statusMessage: 'Invalid code' })
    }
    return ok({ verified: true, email })
  }
  const api = useApi()
  return await api.post(ApiEndpoints.AUTH_RESET_VERIFY, { email, code })
}

export async function resendPasswordResetCode(email: string) {
  if (useMock()) {
    await mockLatency(null, 400)
    return ok({ sent: true, email, mockCode: MOCK_RESET_CODE })
  }
  const api = useApi()
  return await api.post(ApiEndpoints.AUTH_RESET_RESEND, { email })
}

/** Set a new password after the reset code was verified. */
export async function resetPasswordWithCode(input: {
  email: string
  code: string
  password: string
  passwordConfirmation: string
}) {
  if (useMock()) {
    await mockLatency(null, 450)
    if (input.password.length < 6) {
      throw createError({ statusCode: 400, statusMessage: 'Password too short' })
    }
    if (input.password !== input.passwordConfirmation) {
      throw createError({ statusCode: 400, statusMessage: 'Passwords do not match' })
    }
    if (String(input.code || '').trim() !== MOCK_RESET_CODE) {
      throw createError({ statusCode: 400, statusMessage: 'Invalid or expired code' })
    }
    return ok({ reset: true, email: input.email })
  }
  const api = useApi()
  return await api.post(ApiEndpoints.AUTH_RESET_PASSWORD, input)
}

import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { authenticateMock, MOCK_AUTH_TOKEN } from '~/utils/auth/mock-login'
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
    return ok({ sent: true, email })
  }
  const api = useApi()
  return await api.post(ApiEndpoints.AUTH_FORGOT_PASSWORD, { email })
}

export async function verifyOtp(code: string) {
  if (useMock()) {
    await mockLatency(null, 400)
    if (!code || code.length < 6) {
      throw createError({ statusCode: 400, statusMessage: 'Invalid OTP' })
    }
    return ok({ verified: true })
  }
  const api = useApi()
  return await api.post(ApiEndpoints.AUTH_OTP_VERIFY, { code })
}

export async function resendOtp() {
  if (useMock()) {
    await mockLatency(null, 400)
    return ok({ sent: true })
  }
  const api = useApi()
  return await api.post(ApiEndpoints.AUTH_OTP_RESEND, {})
}

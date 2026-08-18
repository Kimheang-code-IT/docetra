import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import type { ApiResponse } from '~/types/docetra/common'
import type { AuthUser } from '~/types/auth-user'

type LoginResult = { token?: string; user: AuthUser }

export async function loginWithCredentials(email: string, password: string) {
  return useApi().post<ApiResponse<LoginResult>>(ApiEndpoints.AUTH_LOGIN, { email, password }, {
    suppressErrorToast: true,
    suppressAccessAlert: true,
  })
}

export async function logoutSession() {
  return useApi().post<ApiResponse<{ loggedOut: boolean }>>(ApiEndpoints.AUTH_LOGOUT, {}, {
    suppressErrorToast: true,
    suppressAccessAlert: true,
  })
}

export async function refreshSession() {
  return useApi().post<ApiResponse<AuthUser>>(ApiEndpoints.AUTH_REFRESH, {}, {
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
  return useApi().post<ApiResponse<{ sent: boolean }>>(ApiEndpoints.AUTH_FORGOT_PASSWORD, { email })
}

export async function verifyPasswordResetCode(email: string, code: string) {
  return useApi().post<ApiResponse<{ verified: boolean }>>(ApiEndpoints.AUTH_RESET_VERIFY, { email, code })
}

export async function resendPasswordResetCode(email: string) {
  return useApi().post<ApiResponse<{ sent: boolean }>>(ApiEndpoints.AUTH_RESET_RESEND, { email })
}

export async function resetPasswordWithCode(input: {
  email: string
  code: string
  password: string
  passwordConfirmation: string
}) {
  return useApi().post<ApiResponse<{ reset: boolean }>>(ApiEndpoints.AUTH_RESET_PASSWORD, input)
}

export async function changePassword(input: {
  currentPassword: string
  password: string
  passwordConfirmation: string
}) {
  return useApi().post<ApiResponse<{ changed: boolean }>>(ApiEndpoints.AUTH_CHANGE_PASSWORD, input)
}

export async function updateProfileAvatar(avatar: string) {
  const response = await useApi().put<ApiResponse<{ avatar: string }>>(ApiEndpoints.AUTH_PROFILE_AVATAR, { avatar })
  useAuthStore().updateUser({ avatar: response.data.avatar })
  return response
}

export async function removeProfileAvatar() {
  const response = await useApi().delete<ApiResponse<{ removed: boolean }>>(ApiEndpoints.AUTH_PROFILE_AVATAR)
  useAuthStore().updateUser({ avatar: undefined })
  return response
}

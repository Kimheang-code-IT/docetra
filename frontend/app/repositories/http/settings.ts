import type { AppConfigRepository, AppInfoRepository } from '~/repositories/contracts/settings'
import type { ApiResponse } from '~/types/docetra/common'
import type { AppConfig, AppInfo, ConnectionStatus, TelegramChat, TelegramTestResult } from '~/types/docetra/settings'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { unwrapApiData } from './response'

type ConnectionResult = { status: ConnectionStatus; message: string }

export function createHttpAppInfoRepository(): AppInfoRepository {
  const api = useApi()
  return {
    get: async () => unwrapApiData(await api.get<AppInfo | ApiResponse<AppInfo>>(ApiEndpoints.APP_INFO, {
      suppressErrorToast: true,
      suppressAccessAlert: true,
    })),
    update: async input => unwrapApiData(await api.patch<AppInfo | ApiResponse<AppInfo>>(ApiEndpoints.APP_INFO, input)),
    reset: async () => unwrapApiData(await api.post<AppInfo | ApiResponse<AppInfo>>(ApiEndpoints.APP_INFO_RESET, {})),
  }
}

export function createHttpAppConfigRepository(): AppConfigRepository {
  const api = useApi()
  const postResult = async (endpoint: string, body: Record<string, unknown> = {}) =>
    unwrapApiData(await api.post<ConnectionResult | ApiResponse<ConnectionResult>>(endpoint, body))

  return {
    get: async () => unwrapApiData(await api.get<AppConfig | ApiResponse<AppConfig>>(ApiEndpoints.APP_CONFIG, {
      suppressErrorToast: true,
      suppressAccessAlert: true,
    })),
    update: async input => unwrapApiData(await api.patch<AppConfig | ApiResponse<AppConfig>>(ApiEndpoints.APP_CONFIG, input)),
    testEmailConnection: () => postResult(ApiEndpoints.APP_CONFIG_TEST_EMAIL),
    sendTestEmail: to => postResult(ApiEndpoints.APP_CONFIG_SEND_TEST_EMAIL, { to }),
    testTelegramConnection: async () =>
      unwrapApiData(await api.post<TelegramTestResult | ApiResponse<TelegramTestResult>>(ApiEndpoints.APP_CONFIG_TEST_TELEGRAM, {})),
    sendTestTelegramMessage: async input =>
      unwrapApiData(await api.post<TelegramTestResult | ApiResponse<TelegramTestResult>>(ApiEndpoints.APP_CONFIG_SEND_TEST_TELEGRAM, {
        destinationId: input.destinationId,
        chatId: input.chatId,
      })),
    discoverTelegramChats: async () => {
      const result = unwrapApiData(await api.post<{ chats?: TelegramChat[] } | ApiResponse<{ chats?: TelegramChat[] }>>(
        ApiEndpoints.APP_CONFIG_DISCOVER_TELEGRAM_CHATS,
        {},
      ))
      return result.chats || []
    },
  }
}

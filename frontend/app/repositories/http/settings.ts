import type { AppConfigRepository } from '~/repositories/contracts/settings'
import type { ApiResponse } from '~/types/docetra/common'
import type { AppConfig, ConnectionStatus, TelegramChat, TelegramTestResult } from '~/types/docetra/settings'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { unwrapApiData } from './response'

type ConnectionResult = { status: ConnectionStatus; message: string }

// App Config is global read-only reference data that several composables fetch
// on every page load. Cache it for the browser session and coalesce concurrent
// reads so a page mount issues one request instead of three or four.
let appConfigCache: AppConfig | null = null
let appConfigInflight: Promise<AppConfig> | null = null

/** Drop the shared App Config cache so the next read refetches (after updates). */
export function invalidateAppConfigCache() {
  appConfigCache = null
  appConfigInflight = null
}

export function createHttpAppConfigRepository(): AppConfigRepository {
  const api = useApi()
  const postResult = async (endpoint: string, body: Record<string, unknown> = {}) =>
    unwrapApiData(await api.post<ConnectionResult | ApiResponse<ConnectionResult>>(endpoint, body))

  const fetchConfig = async () =>
    unwrapApiData(await api.get<AppConfig | ApiResponse<AppConfig>>(ApiEndpoints.APP_CONFIG, {
      suppressErrorToast: true,
      suppressAccessAlert: true,
    }))

  const getConfig = async (): Promise<AppConfig> => {
    // Server renders are per-request; never share the module cache across them.
    if (!import.meta.client) return fetchConfig()
    if (appConfigCache) return appConfigCache
    if (appConfigInflight) return appConfigInflight
    appConfigInflight = fetchConfig()
      .then((config) => {
        appConfigCache = config
        return config
      })
      .finally(() => {
        appConfigInflight = null
      })
    return appConfigInflight
  }

  return {
    get: getConfig,
    update: async (input) => {
      const result = unwrapApiData(await api.patch<AppConfig | ApiResponse<AppConfig>>(ApiEndpoints.APP_CONFIG, input))
      invalidateAppConfigCache()
      return result
    },
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

import { useAuthStore } from '~/stores/auth'
import { ref } from 'vue'
import type { TableQueryParams } from '~/types/api'
import { compactQuery } from '~/utils/api/query'

type ApiRequestOptions = {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
    headers?: Record<string, string>
    body?: Record<string, any> | BodyInit | null
    query?: Record<string, any> | TableQueryParams
    suppressErrorToast?: boolean
    requestKey?: string
    cancelPrevious?: boolean
}

type ApiErrorPayload = {
    message?: string
}

type ApiFetchError = Error & {
    name: string
    data?: ApiErrorPayload
}

// Shared across every useApi() consumer so a later request can cancel an older
// request even when adapters/composables created separate useApi instances.
const requestControllers = new Map<string, AbortController>()

/**
 * Standard API Fetching Composable
 * ───────────────────────────────────────
 * Use this for all backend requests. It automatically:
 * 1. Attaches the auth token (if user is logged in)
 * 2. Handles global error notifications
 * 3. Supports standard REST methods
 */
export function useApi() {
    const toast = useToast()
    const { t } = useI18n()
    const config = useRuntimeConfig()
    const pending = ref(false)
    const error = ref<string | null>(null)

    // Base URL from nuxt.config (fallback to localhost for dev)
    const baseURL = config.public.apiBase || 'http://localhost:8000/api'

    function getRequestKey(url: string, options: ApiRequestOptions): string {
        return options.requestKey || `${options.method || 'GET'}:${url}`
    }

    function cancelRequest(key: string) {
        const controller = requestControllers.get(key)
        if (controller) {
            controller.abort()
            requestControllers.delete(key)
        }
    }

    const fetch = async <T>(url: string, options: ApiRequestOptions = {}) => {
        if (!sameOriginApiUrl(url, String(baseURL))) {
            throw new Error('API requests must use the configured API origin')
        }
        // Retrieve real global app state via Pinia
        const authStore = useAuthStore()
        const requestKey = getRequestKey(url, options)
        const shouldCancelPrevious = options.cancelPrevious !== false

        if (shouldCancelPrevious) {
            cancelRequest(requestKey)
        }

        const controller = new AbortController()
        requestControllers.set(requestKey, controller)

        try {
            pending.value = true
            error.value = null
            return await $fetch<T>(url, {
                baseURL,
                ...options,
                query: compactQuery(options.query),
                signal: controller.signal,
                headers: {
                    ...(authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {}),
                    ...options.headers,
                },
                onResponseError({ response }) {
                    // Critical: Auto-logout on unauthorized
                    if (response.status === 401) {
                        authStore.logout()
                    }

                    if (!options.suppressErrorToast) {
                        toast.add({
                            title: t('api.errorTitle', { status: response.status }),
                            description: response._data?.message || t('api.somethingWentWrong'),
                            color: 'error'
                        })
                    }
                }
            })
        }
        catch (err: unknown) {
            // Network or parsing errors
            const fetchError = err as ApiFetchError
            if (fetchError.name === 'AbortError') {
                return Promise.reject(err)
            }

            error.value = fetchError?.message || t('api.requestFailed')

            if (fetchError.name === 'FetchError' && !options.suppressErrorToast) {
                toast.add({
                    title: t('api.connectionErrorTitle'),
                    description: t('api.connectionErrorDescription'),
                    color: 'error'
                })
            }

            throw err
        }
        finally {
            if (requestControllers.get(requestKey) === controller) {
                requestControllers.delete(requestKey)
            }
            pending.value = false
        }
    }

    return {
        pending,
        error,
        cancelRequest,
        get: <T>(url: string, opt?: ApiRequestOptions) => fetch<T>(url, { method: 'GET', ...opt }),
        post: <T>(url: string, body: ApiRequestOptions['body'], opt?: ApiRequestOptions) => fetch<T>(url, { method: 'POST', body, ...opt }),
        put: <T>(url: string, body: ApiRequestOptions['body'], opt?: ApiRequestOptions) => fetch<T>(url, { method: 'PUT', body, ...opt }),
        patch: <T>(url: string, body: ApiRequestOptions['body'], opt?: ApiRequestOptions) => fetch<T>(url, { method: 'PATCH', body, ...opt }),
        delete: <T>(url: string, opt?: ApiRequestOptions) => fetch<T>(url, { method: 'DELETE', ...opt }),
        request: fetch,
    }
}

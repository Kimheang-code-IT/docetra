import { useAuthStore } from '~/stores/auth'
import { ref } from 'vue'
import type { TableQueryParams } from '~/types/api'
import { compactQuery } from '~/utils/api/query'
import { useAccessAlert } from '~/composables/common/useAccessAlert'
import { appendAppToast, useAppToastState } from '~/composables/common/toast-state'
import { shouldClearSessionOn401, shouldToastConnectionError } from '~/utils/api/error-policy'
import { csrfRequestHeaders } from '~/utils/security/csrf'
import { sameOriginApiUrl } from '~/utils/security/url'
import { requestCacheKey } from '~/utils/api/request-cache'

type ApiRequestOptions = {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
    headers?: Record<string, string>
    body?: Record<string, any> | BodyInit | null
    query?: Record<string, any> | TableQueryParams
    /** Response body shape; 'blob' supports file download flows. */
    responseType?: 'json' | 'blob'
    suppressErrorToast?: boolean
    suppressAccessAlert?: boolean
    requestKey?: string
    cancelPrevious?: boolean
}

type ApiErrorPayload = {
    message?: string
}

type ApiFetchError = Error & {
    name: string
    data?: ApiErrorPayload
    status?: number
    statusCode?: number
    response?: { status?: number }
}

// Shared across useApi() consumers within one Nuxt app, while remaining isolated
// between SSR requests/users.
const requestControllersByApp = new WeakMap<object, Map<string, AbortController>>()
const inflightGetRequestsByApp = new WeakMap<object, Map<string, Promise<unknown>>>()

/**
 * Standard API Fetching Composable
 * ───────────────────────────────────────
 * Safe to call from composables / event handlers (uses Nuxt app + useState only;
 * avoids inject()-based composables like useToast / useRoute / useI18n).
 */
export function useApi() {
    const nuxtApp = useNuxtApp()
    const requestControllers = requestControllersByApp.get(nuxtApp) || new Map<string, AbortController>()
    const inflightGetRequests = inflightGetRequestsByApp.get(nuxtApp) || new Map<string, Promise<unknown>>()
    requestControllersByApp.set(nuxtApp, requestControllers)
    inflightGetRequestsByApp.set(nuxtApp, inflightGetRequests)
    const router = useRouter()
    const { showPermissionDenied, showSessionExpired } = useAccessAlert()
    const config = useRuntimeConfig()
    const activeRequests = ref(0)
    const pending = computed(() => activeRequests.value > 0)
    const error = ref<string | null>(null)
    // Captured while the Nuxt instance is current. Delayed callbacks below
    // (ofetch onResponseError hooks, catch handlers) reuse this ref — calling
    // useState() again from a delayed hook throws NUXT_E1001.
    const toasts = useAppToastState()

    const publicBase = String(config.public.apiBase || '')
    const baseURL = publicBase || (import.meta.server
      ? String(config.apiProxyTarget || 'http://127.0.0.1:8000')
      : '')

    function t(key: string, params?: Record<string, unknown>) {
        const i18n = nuxtApp.$i18n as { t: (k: string, p?: Record<string, unknown>) => string } | undefined
        return i18n?.t?.(key, params) ?? key
    }

    function currentPath() {
        return router.currentRoute.value.fullPath
    }

    function getRequestKey(url: string, options: ApiRequestOptions): string {
        return requestCacheKey(
            options.method || 'GET',
            url,
            options.query ? compactQuery(options.query) : undefined,
            options.requestKey,
        )
    }

    function cancelRequest(key: string) {
        const controller = requestControllers.get(key)
        if (controller) {
            controller.abort()
            requestControllers.delete(key)
        }
    }

    const fetch = <T>(url: string, options: ApiRequestOptions = {}): Promise<T> => {
        if (!sameOriginApiUrl(url, String(baseURL))) {
            return Promise.reject(new Error('API requests must use the configured API origin'))
        }
        const method = options.method || 'GET'
        const requestKey = getRequestKey(url, options)
        const shouldCancelPrevious = options.cancelPrevious === true
        const shouldCoalesce = method === 'GET' && !shouldCancelPrevious

        if (shouldCoalesce) {
            const existing = inflightGetRequests.get(requestKey)
            if (existing) return existing as Promise<T>
        }

        if (shouldCancelPrevious) {
            cancelRequest(requestKey)
        }

        const controller = new AbortController()
        requestControllers.set(requestKey, controller)
        const request = (async () => {
          const authStore = useAuthStore()
          let handledAccessError = false
          let httpErrorToasted = false

          try {
            activeRequests.value += 1
            error.value = null
            const cookieAuth = config.public.authMode !== 'bearer'
            const ssrCookie = import.meta.server ? useRequestHeaders(['cookie']) : {}
            return await $fetch<T>(url, {
                baseURL,
                ...options,
                method,
                query: compactQuery(options.query),
                responseType: options.responseType || 'json',
                signal: controller.signal,
                timeout: Number(config.public.apiTimeoutMs) || 30000,
                credentials: cookieAuth ? 'include' : 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    ...ssrCookie,
                    ...(!cookieAuth && authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {}),
                    ...csrfRequestHeaders(
                        method,
                        String(config.public.csrfCookieName),
                        String(config.public.csrfHeaderName),
                    ),
                    ...options.headers,
                },
                onResponseError({ response }) {
                    // ofetch hooks run after the Nuxt request context is gone
                    // (always on the server, sometimes on the client). Restore
                    // the captured instance for UI/navigation side effects;
                    // useState()/navigateTo() there would throw NUXT_E1001.
                    const withContext = (fn: () => void) => {
                        try {
                            nuxtApp.runWithContext(fn)
                        }
                        catch {
                            // A torn-down app cannot show UI; the caller's
                            // error handling still applies.
                        }
                    }

                    if (response.status === 401) {
                        handledAccessError = true
                        // Do not wipe a fresh login when public/pre-auth calls return 401.
                        if (shouldClearSessionOn401({ suppressAccessAlert: options.suppressAccessAlert })) {
                            withContext(() => {
                                authStore.clearSession()
                                showSessionExpired()
                                void navigateTo('/auth/login')
                            })
                        }
                        return
                    }

                    if (response.status === 403) {
                        handledAccessError = true
                        if (!options.suppressAccessAlert) {
                            withContext(() => {
                                showPermissionDenied({
                                    requestedPath: currentPath(),
                                    description: response._data?.message,
                                })
                            })
                        }
                        return
                    }

                    if (!options.suppressErrorToast) {
                        httpErrorToasted = true
                        appendAppToast(toasts, {
                            title: t('api.errorTitle', { status: response.status }),
                            description: response._data?.message || t('api.somethingWentWrong'),
                            color: 'error',
                        })
                    }
                }
            })
          }
          catch (err: unknown) {
            const fetchError = err as ApiFetchError
            if (fetchError.name === 'AbortError') {
                return Promise.reject(err)
            }

            error.value = fetchError?.message || t('api.requestFailed')
            const status = fetchError.status ?? fetchError.statusCode ?? fetchError.response?.status

            if (shouldToastConnectionError({
                fetchErrorName: fetchError.name,
                handledAccessError,
                httpErrorToasted,
                status,
                suppressErrorToast: options.suppressErrorToast,
            })) {
                appendAppToast(toasts, {
                    title: t('api.connectionErrorTitle'),
                    description: t('api.connectionErrorDescription'),
                    color: 'error',
                })
            }

            throw err
          }
          finally {
            if (requestControllers.get(requestKey) === controller) {
                requestControllers.delete(requestKey)
            }
            activeRequests.value = Math.max(0, activeRequests.value - 1)
          }
        })()

        if (shouldCoalesce) inflightGetRequests.set(requestKey, request)
        return request.finally(() => {
            if (inflightGetRequests.get(requestKey) === request) {
                inflightGetRequests.delete(requestKey)
            }
        })
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

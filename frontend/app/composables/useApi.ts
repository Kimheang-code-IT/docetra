import { useAuthStore } from '~/stores/auth'
import { ref } from 'vue'
import type { TableQueryParams } from '~/types/api'
import { compactQuery } from '~/utils/api/query'
import { useAccessAlert } from '~/composables/common/useAccessAlert'
import { shouldClearSessionOn401, shouldToastConnectionError } from '~/utils/api/error-policy'
import { csrfRequestHeaders } from '~/utils/security/csrf'
import { sameOriginApiUrl } from '~/utils/security/url'

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

type ToastItem = {
    id: string
    open: boolean
    title?: string
    description?: string
    color?: string
}

// Shared across every useApi() consumer so a later request can cancel an older
// request even when composables created separate useApi instances.
const requestControllers = new Map<string, AbortController>()

/**
 * Push a toast without `useToast()` — Nuxt UI's useToast() calls Vue `inject()`,
 * which throws outside `<script setup>` (e.g. API calls from submit handlers).
 */
function pushErrorToast(title: string, description: string) {
    const toasts = useState<ToastItem[]>('toasts', () => [])
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
    toasts.value = [...toasts.value, { id, open: true, title, description, color: 'error' }].slice(-5)
}

/**
 * Standard API Fetching Composable
 * ───────────────────────────────────────
 * Safe to call from composables / event handlers (uses Nuxt app + useState only;
 * avoids inject()-based composables like useToast / useRoute / useI18n).
 */
export function useApi() {
    const nuxtApp = useNuxtApp()
    const router = useRouter()
    const { showPermissionDenied, showSessionExpired } = useAccessAlert()
    const config = useRuntimeConfig()
    const activeRequests = ref(0)
    const pending = computed(() => activeRequests.value > 0)
    const error = ref<string | null>(null)

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
        const authStore = useAuthStore()
        const requestKey = getRequestKey(url, options)
        const shouldCancelPrevious = options.cancelPrevious !== false

        if (shouldCancelPrevious) {
            cancelRequest(requestKey)
        }

        const controller = new AbortController()
        requestControllers.set(requestKey, controller)
        let handledAccessError = false
        let httpErrorToasted = false

        try {
            activeRequests.value += 1
            error.value = null
            const method = options.method || 'GET'
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
                    if (response.status === 401) {
                        handledAccessError = true
                        // Do not wipe a fresh login when public/pre-auth calls return 401.
                        if (shouldClearSessionOn401({ suppressAccessAlert: options.suppressAccessAlert })) {
                            authStore.clearSession()
                            showSessionExpired()
                            void navigateTo('/auth/login')
                        }
                        return
                    }

                    if (response.status === 403) {
                        handledAccessError = true
                        if (!options.suppressAccessAlert) {
                            showPermissionDenied({
                                requestedPath: currentPath(),
                                description: response._data?.message,
                            })
                        }
                        return
                    }

                    if (!options.suppressErrorToast) {
                        httpErrorToasted = true
                        pushErrorToast(
                            t('api.errorTitle', { status: response.status }),
                            response._data?.message || t('api.somethingWentWrong'),
                        )
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
                pushErrorToast(
                    t('api.connectionErrorTitle'),
                    t('api.connectionErrorDescription'),
                )
            }

            throw err
        }
        finally {
            if (requestControllers.get(requestKey) === controller) {
                requestControllers.delete(requestKey)
            }
            activeRequests.value = Math.max(0, activeRequests.value - 1)
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

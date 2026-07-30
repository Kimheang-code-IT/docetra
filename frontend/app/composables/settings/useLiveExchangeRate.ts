import { computed } from 'vue'
import { DEFAULT_USD_KHR_RATE } from '~/utils/constants/exchange-rate'
import { initialData as exchangeRateSeed } from '~/data/exchange-rate'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'

/**
 * Shared current USD→KHR rate used for preview conversions across pages.
 * Full rate history stays page-local in `useExchangeRateManagement`.
 * Backend owns final conversion values on persisted records.
 */
export function useLiveExchangeRate() {
  const currentUsdKhrRate = useState<number>(
    'live-exchange-rate-usd-khr',
    () => DEFAULT_USD_KHR_RATE,
  )
  const isLoaded = useState('live-exchange-rate-loaded', () => false)
  const isLoading = useState('live-exchange-rate-loading', () => false)
  const error = useState<string | null>('live-exchange-rate-error', () => null)

  const rateLabel = computed(() => String(currentUsdKhrRate.value))

  function setUsdKhrRate(rate: number) {
    if (!Number.isFinite(rate) || rate <= 0) return
    currentUsdKhrRate.value = rate
    isLoaded.value = true
    error.value = null
  }

  function resolveUsdRateFromRows(rows: { currency: string; rateKhr: number }[]): number {
    const usd = rows.find((row) => row.currency.toUpperCase() === 'USD')
    return usd?.rateKhr && usd.rateKhr > 0 ? usd.rateKhr : DEFAULT_USD_KHR_RATE
  }

  async function refresh() {
    if (isLoading.value) return
    isLoading.value = true
    error.value = null

    try {
      const api = useApi()
      if (api.useMockData) {
        setUsdKhrRate(resolveUsdRateFromRows(exchangeRateSeed))
        return
      }

      const response = await api.get<{ items?: { currency: string; rateKhr: number }[] } | { currency: string; rateKhr: number }[]>(
        ApiEndpoints.EXCHANGE_RATES_CURRENT,
        { suppressErrorToast: true },
      )

      const rows = Array.isArray(response)
        ? response
        : (response?.items ?? [])

      setUsdKhrRate(resolveUsdRateFromRows(rows))
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load exchange rate'
      if (!isLoaded.value) {
        setUsdKhrRate(DEFAULT_USD_KHR_RATE)
      }
    } finally {
      isLoading.value = false
    }
  }

  if (import.meta.client && !isLoaded.value && !isLoading.value) {
    void refresh()
  }

  return {
    currentUsdKhrRate,
    rateLabel,
    isLoaded,
    isLoading,
    error,
    setUsdKhrRate,
    refresh,
  }
}

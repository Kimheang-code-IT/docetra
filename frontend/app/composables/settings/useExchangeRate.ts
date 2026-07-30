import { computed, ref, watch } from 'vue'
import { TABLE_HEADERS } from '~/constants/report-table'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useTableQuery } from '~/composables/table/useTableQuery'
import type { ExchangeRate } from '~/types/exchange-rate'
import { initialData } from '~/data/exchange-rate'
import { slicePage } from '~/utils/table/paginate-rows'
import { useLiveExchangeRate } from '~/composables/settings/useLiveExchangeRate'
import { useGlobalFilter } from '~/composables/useGlobalFilter'

export function useExchangeRateManagement() {
  const { toFilterOptions } = useTranslatedFilterOptions()
  const { rowSelection, columnVisibility } = useBaseTable({})
  const { currentUsdKhrRate, setUsdKhrRate } = useLiveExchangeRate()
  const { isDateInRange } = useGlobalFilter()

  const { sorting, globalFilter, columnFilters, pagination } = useTableQuery({
    initialSorting: [{ id: 'id', desc: false }],
  })

  const rates = ref<ExchangeRate[]>([...initialData])
  const CURRENCY_FILTER_KEY = 'currency' as const satisfies keyof ExchangeRate
  const filterSelections = ref<Record<string, string[] | null>>({})

  watch(
    rates,
    (rows) => {
      const usd = rows.find((row) => row.currency.toUpperCase() === 'USD')
      if (usd?.rateKhr) setUsdKhrRate(usd.rateKhr)
    },
    { immediate: true, deep: true },
  )

  const tableFilterConfigs = computed(() => [
    {
      key: CURRENCY_FILTER_KEY,
      items: toFilterOptions([...new Set(rates.value.map((rate) => rate.currency))].sort()),
      label: TABLE_HEADERS.currency,
    },
  ])

  const filteredRates = computed(() => {
    let rows = rates.value

    const selectedCurrencies = filterSelections.value[CURRENCY_FILTER_KEY]
    if (selectedCurrencies?.length) {
      rows = rows.filter((rate) => selectedCurrencies.includes(rate.currency))
    }

    rows = rows.filter((rate) => isDateInRange(rate.date))

    if (globalFilter.value?.trim()) {
      const query = globalFilter.value.trim().toLowerCase()
      rows = rows.filter((rate) =>
        rate.currency.toLowerCase().includes(query)
        || String(rate.rateKhr).includes(query)
        || (rate.date?.toLowerCase().includes(query) ?? false)
        || String(rate.id).includes(query),
      )
    }

    return rows
  })

  const paginatedRates = computed(() =>
    slicePage(
      filteredRates.value,
      pagination.value.pageIndex,
      pagination.value.pageSize,
      true,
    ),
  )

  const reportColumns = computed(() => [
    { key: 'id', label: TABLE_HEADERS.rank, width: 56 },
    { key: 'currency', label: TABLE_HEADERS.currency, width: 100 },
    { key: 'date', label: TABLE_HEADERS.date, width: 120 },
    { key: 'unitPerCurrency', label: TABLE_HEADERS.unitPerCurrency, width: 140 },
    { key: 'rateKhr', label: TABLE_HEADERS.rateKhr, width: 140, numeric: true },
  ])

  return {
    rowSelection,
    sorting,
    globalFilter,
    columnVisibility,
    columnFilters,
    pagination,
    filterSelections,
    tableFilterConfigs,
    filteredRates,
    paginatedRates,
    reportColumns,
    currentUsdKhrRate,
  }
}

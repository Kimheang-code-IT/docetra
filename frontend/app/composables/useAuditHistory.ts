import { ref, computed } from 'vue'
import type { DropdownMenuItem } from '@nuxt/ui'
import { TABLE_HEADERS } from '~/constants/report-table'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useTableQuery } from '~/composables/table/useTableQuery'
import type { AuditLog } from '~/types/audit-log'
import { initialLogs } from '~/data/audit-history'
import { useMockTableReload } from '~/composables/table/useMockTableReload'

export function useAuditHistory() {
    const { toFilterOptions } = useTranslatedFilterOptions()
    const { t } = useI18n()
    const {
      rowSelection,
      columnVisibility,
      isAnalyticsOpen,
      isDetailOpen,
    } = useBaseTable({})
  
    const {
      sorting,
      globalFilter,
      columnFilters,
      pagination,
    } = useTableQuery({ initialSorting: [{ id: 'id', desc: true }] })

    const selectedLog = ref<AuditLog | null>(null)

    const actionValues = ['Login', 'Logout', 'Create', 'Update', 'Delete', 'Export'] as const
    const actionItems = computed(() => toFilterOptions([...actionValues]))
    const selectedActions = ref<string[] | null>(null)

    const logs = ref<AuditLog[]>(initialLogs)

    const { isReloading, retryFetch } = useMockTableReload(() => {
        logs.value = [...initialLogs]
    })

    const reportColumns = computed(() => [
        { key: 'id', label: TABLE_HEADERS.rank, width: 56 },
        { key: 'typeAction', label: TABLE_HEADERS.typeAction, width: 120 },
        { key: 'username', label: TABLE_HEADERS.username, width: 160, text: true },
        { key: 'date', label: TABLE_HEADERS.date, width: 140 },
        { key: 'description', label: TABLE_HEADERS.description, width: 360, text: true },
    ])

    const filteredLogs = computed(() => {
        let rows = logs.value

        if (selectedActions.value?.length) {
            rows = rows.filter(l => selectedActions.value!.includes(l.typeAction))
        }

        if (globalFilter.value?.trim()) {
            const query = globalFilter.value.trim().toLowerCase()
            rows = rows.filter(l =>
                l.typeAction.toLowerCase().includes(query)
                || l.username.toLowerCase().includes(query)
                || l.description.toLowerCase().includes(query)
                || String(l.id).includes(query),
            )
        }

        return rows
    })

    const paginatedLogs = computed(() => {
        const { pageIndex, pageSize } = pagination.value
        const start = pageIndex * pageSize
        return filteredLogs.value.slice(start, start + pageSize)
    })

    function getDropdownActions(log: AuditLog): DropdownMenuItem[][] {
        return [[
            {
                label: t('actions.view'),
                icon: 'i-lucide-eye',
                onSelect: () => {
                    selectedLog.value = log
                    isDetailOpen.value = true
                },
            },
        ]]
    }

    return {
        rowSelection, sorting, globalFilter, columnVisibility, columnFilters,
        pagination, isAnalyticsOpen, isDetailOpen,
        selectedLog, logs,
        actionItems, selectedActions,
        filteredLogs, paginatedLogs, reportColumns,
        getDropdownActions,
        isReloading,
        retryFetch,
    }
}

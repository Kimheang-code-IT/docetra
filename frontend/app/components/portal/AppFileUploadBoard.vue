<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import type { AttachmentMeta } from '~/types/docetra/common'
import { getEntityConfig } from '~/config/entities'
import { useConfirm } from '~/composables/common/useConfirm'
import { useEntityWorkspace } from '~/composables/workspace/useEntityWorkspace'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { adapters } from '~/adapters'
import { useAuthStore } from '~/stores/auth'
import { permissionForAction } from '~/utils/role/access'
import type { RowActionItem } from '~/types/docetra/row-actions'

const config = getEntityConfig('fileUploads')

const {
  q,
  page,
  limit,
  filters,
  setFilter,
  items,
  total,
  pending,
  error,
  refresh,
  debouncedSearch,
  cellValue,
  openRow,
  deleteSelected,
} = useEntityWorkspace(config)

const toast = useToast()
const { t } = useI18n()
const { confirm } = useConfirm()
const authStore = useAuthStore()
const canUpload = computed(() => authStore.canAccessPage(permissionForAction(config.permission, 'create')))
const canDelete = computed(() => authStore.canAccessPage(permissionForAction(config.permission, 'delete')))
const canViewLogs = computed(() => authStore.canAccessPage('records.logs.view'))
const rowActions = computed<RowActionItem[]>(() => [
  { key: 'detail', labelKey: 'docetra.rowActions.detail', icon: 'i-lucide-eye' },
  ...(canViewLogs.value
    ? [{ key: 'logs', labelKey: 'docetra.rowActions.logs', icon: 'i-lucide-scroll-text' } satisfies RowActionItem]
    : []),
  ...(canDelete.value
    ? [{ key: 'delete', labelKey: 'docetra.rowActions.delete', icon: 'i-lucide-trash-2', color: 'error' } satisfies RowActionItem]
    : []),
])

const leftCollapsed = useState('file-upload-left-collapsed', () => false)
const mobileUploadExpanded = ref(false)
const isSmallScreen = useMediaQuery('(max-width: 1023px)')
const uploadPanelCollapsed = computed(() =>
  isSmallScreen.value ? !mobileUploadExpanded.value : leftCollapsed.value,
)
const searchInput = ref(q.value)
const selectedIds = ref<string[]>([])
const uploading = ref(false)
const deleting = ref(false)
const hasStatusFilter = computed(() => Boolean(filters.value.status))

const statusFilter = computed(() =>
  config.filters.find(f => f.key === 'status'),
)

const statusFilterValue = computed<string | string[] | null>(() => {
  const raw = filters.value.status
  if (!raw || !statusFilter.value) return null
  if (statusFilter.value.type === 'multiselect') {
    const values = raw.split(',').map(v => v.trim()).filter(Boolean)
    return values.length ? values : null
  }
  return raw
})

const uploadDateStart = computed({
  get: () => filters.value.startDate || '',
  set: (value: string) => setFilter('startDate', value || undefined),
})

const uploadDateEnd = computed({
  get: () => filters.value.endDate || '',
  set: (value: string) => setFilter('endDate', value || undefined),
})

const hasUploadFilters = computed(() => Boolean(
  hasStatusFilter.value || uploadDateStart.value.trim() || uploadDateEnd.value.trim(),
))

watch(q, (v) => { searchInput.value = v })
watch(searchInput, (v) => debouncedSearch(v))

function onStatusFilterChange(value: string | string[] | null) {
  if (value == null || value === '' || (Array.isArray(value) && !value.length)) {
    setFilter('status', undefined)
    return
  }
  setFilter('status', value)
}

function toggleUploadPanel() {
  if (isSmallScreen.value) {
    mobileUploadExpanded.value = !mobileUploadExpanded.value
    return
  }
  leftCollapsed.value = !leftCollapsed.value
}

async function onUploadComplete(metas: AttachmentMeta[]) {
  if (!canUpload.value || !metas.length) return
  uploading.value = true
  try {
    toast.add({ title: t('docetra.attachments.uploaded'), color: 'success' })
    await refresh()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.fileUploadBoard.uploadFailed'), color: 'error' })
  }
  finally {
    uploading.value = false
  }
}

async function onDeleteSelected(ids = selectedIds.value) {
  if (!canDelete.value || !ids.length) return
  const ok = await confirm({ kind: 'delete', count: ids.length })
  if (!ok) return

  deleting.value = true
  try {
    await deleteSelected(ids)
    selectedIds.value = []
    toast.add({
      title: t('docetra.actions.deletedItems', { n: ids.length }),
      color: 'success',
    })
  }
  catch (e: any) {
    toast.add({
      title: e?.message || t('docetra.actions.deleteFailed'),
      color: 'error',
    })
  }
  finally {
    deleting.value = false
  }
}

function onRowAction(payload: { key: string, row: Record<string, unknown> }) {
  const { key, row } = payload
  if (key === 'detail' || key === 'edit') {
    openRow(row)
    return
  }
  if (key === 'logs') {
    if (!canViewLogs.value) return
    const id = String(row.id || '')
    navigateTo({
      path: '/records/record-logs',
      query: id ? { q: id } : undefined,
    })
    return
  }
  if (key === 'delete') {
    const id = String(row.id || '')
    if (id) onDeleteSelected([id])
  }
}

onMounted(() => {
  refresh()
})
</script>

<template>
  <WorkspaceAppWorkspacePage
    :title-key="config.titleKey"
    :description-key="config.descriptionKey"
    :icon="config.icon"
    :can-create="false"
    :refreshing="pending"
    @refresh="refresh"
  >
    <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default">
      <div
        v-if="pending && !items.length"
        class="absolute inset-0 z-10 flex items-center justify-center bg-default/50"
      >
        <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
      </div>

      <UAlert
        v-if="error"
        class="m-3"
        color="error"
        :title="error"
        :actions="[{ label: $t('docetra.actions.retry'), onClick: refresh }]"
      />

      <div class="flex min-h-0 flex-1 flex-row overflow-hidden">
        <!-- Left: Uppy upload folder -->
        <aside
          class="flex h-full min-h-0 shrink-0 flex-col overflow-hidden border-e border-default bg-default transition-[width] duration-200"
          :style="{ width: uploadPanelCollapsed ? '3.5rem' : 'min(18rem, calc(100% - 3rem))' }"
        >
          <div
            class="flex shrink-0 items-center border-b border-default"
            :class="uploadPanelCollapsed ? 'justify-center px-1.5 py-3.5' : 'justify-between gap-2 px-4 py-3.5'"
          >
            <h2
              v-if="!uploadPanelCollapsed"
              class="truncate text-sm font-semibold text-highlighted"
            >
              {{ $t('docetra.fileUploadBoard.uploadTitle') }}
            </h2>
            <UTooltip
              v-else
              :text="$t('docetra.fileUploadBoard.uploadTitle')"
              :content="{ side: 'right', sideOffset: 8 }"
            >
              <button
                type="button"
                class="rounded-md p-2 text-muted hover:bg-elevated hover:text-highlighted"
                :aria-label="$t('docetra.fileUploadBoard.expandUpload')"
                @click="toggleUploadPanel"
              >
                <UIcon name="i-lucide-folder-up" class="size-4" />
              </button>
            </UTooltip>
            <UButton
              v-if="!uploadPanelCollapsed"
              icon="i-lucide-panel-left-close"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              class="shrink-0 lg:hidden"
              :aria-label="$t('docetra.fileUploadBoard.collapseUpload')"
              @click="toggleUploadPanel"
            />
          </div>

          <div
            class="relative min-h-0 flex-1 overflow-hidden p-3"
            :class="uploadPanelCollapsed ? 'hidden' : ''"
          >
            <div
              v-if="uploading"
              class="absolute inset-3 z-10 flex items-center justify-center rounded-lg bg-default/60"
            >
              <UIcon name="i-lucide-loader-circle" class="size-5 animate-spin text-primary" />
            </div>
            <LazyCommonAppUppyUploader
              v-if="canUpload"
              class="flex h-full min-h-0 flex-col [&_.uppy-host]:min-h-0 [&_.uppy-host]:flex-1"
              entity-id="portal-file-upload"
              :endpoint="ApiEndpoints.FILE_UPLOADS"
              fill
              :note="$t('docetra.fileUploadBoard.uploadHint')"
              :disabled="uploading"
              @complete="onUploadComplete"
            />
            <UAlert
              v-else
              color="neutral"
              variant="soft"
              icon="i-lucide-lock-keyhole"
              :title="$t('docetra.states.accessDeniedTitle')"
              :description="$t('docetra.states.uploadPermissionRequired')"
            />
          </div>

          <div
            v-if="uploadPanelCollapsed && canUpload"
            class="flex min-h-0 flex-1 flex-col items-center gap-1.5 p-1.5"
          >
            <UTooltip
              :text="$t('docetra.fileUploadBoard.expandUpload')"
              :content="{ side: 'right', sideOffset: 8 }"
            >
              <UButton
                icon="i-lucide-upload"
                color="primary"
                variant="soft"
                size="sm"
                square
                :aria-label="$t('docetra.fileUploadBoard.expandUpload')"
                @click="toggleUploadPanel"
              />
            </UTooltip>
          </div>
        </aside>

        <!-- Right: uploaded files table -->
        <section class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <div class="flex shrink-0 items-center gap-3 border-b border-default px-4 py-3.5">
            <div class="flex min-w-0 shrink-0 items-center gap-1.5">
              <UButton
                :icon="uploadPanelCollapsed ? 'i-lucide-panel-left-open' : 'i-lucide-panel-left-close'"
                color="neutral"
                variant="ghost"
                size="sm"
                square
                :aria-label="uploadPanelCollapsed
                  ? $t('docetra.fileUploadBoard.expandUpload')
                  : $t('docetra.fileUploadBoard.collapseUpload')"
                :aria-expanded="!uploadPanelCollapsed"
                @click="toggleUploadPanel"
              />
              <h2 class="hidden min-w-0 max-w-40 truncate text-sm font-semibold text-highlighted sm:block">
                {{ $t('docetra.fileUploadBoard.tableTitle') }}
              </h2>
            </div>

            <CommonAppLiveSearch
              v-model="searchInput"
              class="min-w-0 w-full max-w-[18.75rem] flex-1"
              :placeholder="$t('docetra.fileUploadBoard.search')"
            />

            <div class="hidden shrink-0 items-center gap-2.5 lg:flex">
              <CommonAppFilterSelect
                v-if="statusFilter"
                :filter="statusFilter"
                :model-value="statusFilterValue"
                @update:model-value="onStatusFilterChange"
              />
              <CommonAppDateRangeFilter
                v-model:start="uploadDateStart"
                v-model:end="uploadDateEnd"
                :label="$t('docetra.fields.createdAt')"
                size="sm"
              />
            </div>

            <div class="ms-auto flex shrink-0 items-center lg:hidden">
              <UPopover>
                <UButton
                  icon="i-lucide-filter"
                  :color="hasUploadFilters ? 'primary' : 'neutral'"
                  :variant="hasUploadFilters ? 'soft' : 'ghost'"
                  size="sm"
                  square
                  :aria-label="$t('docetra.actions.filter')"
                />
                <template #content>
                  <div class="flex w-[calc(100vw-2rem)] max-w-3xl flex-nowrap items-center gap-2 overflow-x-auto p-3">
                    <CommonAppFilterSelect
                      v-if="statusFilter"
                      :filter="statusFilter"
                      :model-value="statusFilterValue"
                      class="shrink-0"
                      @update:model-value="onStatusFilterChange"
                    />
                    <div class="shrink-0">
                      <CommonAppDateRangeFilter
                        v-model:start="uploadDateStart"
                        v-model:end="uploadDateEnd"
                        :label="$t('docetra.fields.createdAt')"
                        size="sm"
                        inline
                      />
                    </div>
                  </div>
                </template>
              </UPopover>
            </div>
          </div>

          <WorkspaceAppServerTable
            class="min-h-0 flex-1"
            :columns="config.columns"
            :rows="items"
            :total="total"
            :page="page"
            :limit="limit"
            :pending="pending"
            :error="error"
            :cell-value="cellValue"
            :can-delete="canDelete"
            :selectable="canDelete"
            :show-meta="true"
            :row-actions="rowActions"
            @update:page="page = $event"
            @update:limit="limit = $event"
            @update:selection="selectedIds = $event"
            @row-click="openRow"
            @row-action="onRowAction"
            @delete-selected="onDeleteSelected"
            @retry="refresh"
          />
        </section>
      </div>
    </div>
  </WorkspaceAppWorkspacePage>
</template>

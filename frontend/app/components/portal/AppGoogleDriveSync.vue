<script setup lang="ts">
/**
 * Dedicated Google Drive sync workflow (portal).
 * Create source → start sync → poll job with backoff → status → refresh files.
 * Uses the dedicated Drive APIs instead of generic entity CRUD.
 */
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { formatBytes } from '~/utils/format/bytes'
import { permissionForAction } from '~/utils/role/access'
import { useAppLocalization } from '~/composables/settings/useAppLocalization'

interface DriveSource {
  id: string
  name?: string
  folderId?: string
  syncStatus?: string
  lastSyncAt?: string
  kind?: string
  status?: string
  version?: number
}

interface DriveJob {
  id: string
  kind?: string
  sourceId?: string
  status?: string
  fileCount?: number
  error?: string
  completedAt?: string | null
}

const { t } = useI18n()
const toast = useToast()
const api = useApi()
const auth = useAuthStore()
const { formatDateTime } = useAppLocalization()

const sources = ref<DriveSource[]>([])
const files = ref<{ id: string, driveFileId: string, name: string, mimeType?: string, sizeBytes?: number, syncedAt?: string, webViewLink?: string }[]>([])
const loading = ref(false)
const creating = ref(false)
const syncingIds = ref<Set<string>>(new Set())
const pollingTimers = new Map<string, ReturnType<typeof setTimeout>>()
const jobStatus = ref<{ sourceId: string, status: string, fileCount?: number, error?: string } | null>(null)

const showCreate = ref(false)
const draft = reactive({ name: '', folderId: '' })

const canCreate = computed(() => auth.canAccessPage(permissionForAction('portal.google_drive_sync.view', 'create')))
const canSync = computed(() => auth.canAccessPage(permissionForAction('portal.google_drive_sync.view', 'edit')))

const tableUi = {
  root: 'relative overflow-auto',
  base: 'min-w-max w-full border-separate border-spacing-0',
  thead: '[&_tr]:border-b-0',
  tbody: 'divide-y-0',
  tr: 'group hover:bg-muted/40',
  th: 'sticky top-0 z-10 bg-muted px-2.5 py-2.5 text-xs font-bold text-highlighted border-b border-default',
  td: 'px-2.5 py-2 text-sm text-highlighted border-b border-default',
  empty: 'py-12 text-center text-muted',
}

const sourceColumns = computed(() => [
  { accessorKey: 'name', header: t('docetra.fields.name') },
  { accessorKey: 'folderId', header: t('docetra.drive.folderId') },
  { accessorKey: 'syncStatus', header: t('docetra.fields.syncStatus') },
  { accessorKey: 'lastSyncAt', header: t('docetra.fields.lastSync') },
  { id: 'actions', header: t('common.actions') },
])

const fileColumns = computed(() => [
  { accessorKey: 'name', header: t('docetra.fields.name') },
  { accessorKey: 'mimeType', header: t('docetra.fields.type') },
  { accessorKey: 'sizeBytes', header: t('docetra.fields.size') },
  { accessorKey: 'syncedAt', header: t('docetra.fields.syncedAt') },
  { id: 'link', header: '' },
])

function syncStatusColor(status?: string) {
  if (status === 'completed' || status === 'synced') return 'success' as const
  if (status === 'failed' || status === 'cancelled' || status === 'error') return 'error' as const
  if (status === 'syncing' || status === 'queued' || status === 'running') return 'info' as const
  return 'neutral' as const
}

function jobAlertColor(status?: string) {
  if (status === 'completed') return 'success' as const
  if (status === 'failed' || status === 'cancelled') return 'error' as const
  return 'info' as const
}

const syncBackoffMs = [1500, 2000, 3000, 5000]

onBeforeUnmount(() => {
  for (const timer of pollingTimers.values()) clearTimeout(timer)
  pollingTimers.clear()
})

function isSyncActive(source: DriveSource) {
  return syncingIds.value.has(source.id) || source.syncStatus === 'syncing'
}

async function load() {
  loading.value = true
  try {
    const [sourcesRes, filesRes] = await Promise.all([
      api.get<{ data?: DriveSource[] }>(ApiEndpoints.GOOGLE_DRIVE_SYNC, {
        query: { limit: 100 },
        requestKey: 'drive-sources',
        cancelPrevious: true,
        suppressAccessAlert: true,
      }),
      api.get<{ data?: typeof files.value }>(ApiEndpoints.PORTAL_DRIVE_FILES, {
        query: { limit: 100 },
        requestKey: 'portal-drive-files',
        cancelPrevious: true,
        suppressAccessAlert: true,
      }),
    ])
    sources.value = (sourcesRes.data || []).filter(row => (row as DriveSource).kind === 'source')
    files.value = filesRes.data || []
  }
  catch {
    // 401/403/5xx toasts are handled centrally by useApi().
  }
  finally {
    loading.value = false
  }
}

async function createSource() {
  if (creating.value) return
  if (!draft.name.trim() || !draft.folderId.trim()) {
    toast.add({ title: t('docetra.drive.nameAndFolderRequired'), color: 'warning' })
    return
  }
  creating.value = true
  try {
    await api.post(ApiEndpoints.GOOGLE_DRIVE_SYNC + '/sources', {
      name: draft.name.trim(),
      folderId: draft.folderId.trim(),
    })
    toast.add({ title: t('docetra.drive.sourceCreated'), color: 'success' })
    draft.name = ''
    draft.folderId = ''
    showCreate.value = false
    await load()
  }
  catch (error) {
    // 422 (validation) and 409/5xx toasts handled centrally; surface locally too.
    toast.add({
      title: t('docetra.drive.sourceCreateFailed'),
      description: error instanceof Error ? error.message : undefined,
      color: 'error',
    })
  }
  finally {
    creating.value = false
  }
}

async function pollJob(sourceId: string, jobId: string, attempt: number) {
  if (!pollingTimers.has(jobId) && attempt > 0) return
  try {
    const res = await api.get<{ data?: DriveJob }>(
      ApiEndpoints.GOOGLE_DRIVE_SYNC + `/jobs/${encodeURIComponent(jobId)}`,
      { requestKey: `drive-job:${jobId}`, cancelPrevious: true, suppressAccessAlert: true },
    )
    const job = res.data
    const status = job?.status || 'unknown'
    jobStatus.value = {
      sourceId,
      status,
      fileCount: job?.fileCount,
      error: job?.error,
    }
    if (['completed', 'failed', 'cancelled'].includes(status)) {
      pollingTimers.delete(jobId)
      syncingIds.value.delete(sourceId)
      if (status === 'completed') {
        toast.add({ title: t('docetra.drive.syncCompleted', { count: job?.fileCount ?? 0 }), color: 'success' })
      }
      else {
        toast.add({
          title: t('docetra.drive.syncFailed'),
          description: job?.error || undefined,
          color: 'error',
        })
      }
      await load()
      return
    }
    const delay = syncBackoffMs[Math.min(attempt, syncBackoffMs.length - 1)]
    const timer = setTimeout(() => void pollJob(sourceId, jobId, attempt + 1), delay)
    pollingTimers.set(jobId, timer)
  }
  catch {
    // Keep polling with backoff on transient failures; give up eventually.
    if (attempt >= 8) {
      pollingTimers.delete(jobId)
      syncingIds.value.delete(sourceId)
      jobStatus.value = { sourceId, status: 'failed', error: t('docetra.drive.jobPollFailed') }
      return
    }
    const delay = syncBackoffMs[Math.min(attempt, syncBackoffMs.length - 1)]
    const timer = setTimeout(() => void pollJob(sourceId, jobId, attempt + 1), delay)
    pollingTimers.set(jobId, timer)
  }
}

async function startSync(source: DriveSource) {
  // Never start a second job for the same source (backend rejects active/completed too).
  if (isSyncActive(source)) return
  syncingIds.value = new Set([...syncingIds.value, source.id])
  jobStatus.value = { sourceId: source.id, status: 'queued' }
  try {
    const res = await api.post<{ data?: DriveJob }>(
      ApiEndpoints.GOOGLE_DRIVE_SYNC + `/sources/${encodeURIComponent(source.id)}/sync`,
      {},
    )
    const job = res.data
    if (job?.id) {
      void pollJob(source.id, String(job.id), 0)
    }
    else {
      syncingIds.value.delete(source.id)
      jobStatus.value = { sourceId: source.id, status: 'failed', error: t('docetra.drive.jobPollFailed') }
    }
  }
  catch (error) {
    syncingIds.value.delete(source.id)
    jobStatus.value = { sourceId: source.id, status: 'failed', error: error instanceof Error ? error.message : undefined }
  }
}

const jobStatusLabel = computed(() => {
  const job = jobStatus.value
  if (!job) return ''
  if (job.status === 'completed') return t('docetra.drive.syncCompleted', { count: job.fileCount ?? 0 })
  if (job.status === 'failed' || job.status === 'cancelled') return t('docetra.drive.syncFailed')
  return t('docetra.drive.syncRunning')
})

onMounted(() => void load())
</script>

<template>
  <WorkspaceAppWorkspacePage
    title-key="docetra.pages.googleDriveSync"
    description-key="docetra.descriptions.googleDriveSync"
    icon="i-lucide-cloud"
    :can-create="canCreate"
    create-label-key="docetra.drive.newSource"
    :refreshing="loading"
    @refresh="load"
    @create="showCreate = true"
  >
    <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default">
      <div
        v-if="loading && !sources.length && !files.length"
        class="absolute inset-0 z-10 flex items-center justify-center bg-default/50"
      >
        <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
      </div>

      <form
        v-if="showCreate && canCreate"
        class="grid shrink-0 gap-3 border-b border-default p-4 sm:grid-cols-2"
        @submit.prevent="createSource"
      >
        <UFormField :label="$t('docetra.fields.name')">
          <UInput
            v-model="draft.name"
            variant="soft"
            class="w-full"
            :placeholder="$t('docetra.drive.namePlaceholder')"
          />
        </UFormField>
        <UFormField
          :label="$t('docetra.drive.folderId')"
          :help="$t('docetra.drive.folderIdHelp')"
        >
          <UInput
            v-model="draft.folderId"
            variant="soft"
            class="w-full"
            :placeholder="$t('docetra.drive.folderIdPlaceholder')"
          />
        </UFormField>
        <div class="flex items-center gap-2 sm:col-span-2">
          <UButton
            type="submit"
            color="neutral"
            variant="solid"
            :loading="creating"
            :disabled="creating"
          >
            {{ $t('actions.save') }}
          </UButton>
          <UButton color="neutral" variant="ghost" @click="showCreate = false">
            {{ $t('actions.cancel') }}
          </UButton>
        </div>
      </form>

      <UAlert
        v-if="jobStatus"
        class="m-3 shrink-0"
        :color="jobAlertColor(jobStatus.status)"
        :icon="jobStatus.status === 'completed'
          ? 'i-lucide-check-circle'
          : jobStatus.status === 'failed' || jobStatus.status === 'cancelled'
            ? 'i-lucide-x-circle'
            : 'i-lucide-loader-circle'"
        :title="jobStatusLabel"
        :description="jobStatus.error"
        data-testid="drive-job-status"
      />

      <section class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden border-b border-default">
        <div class="flex shrink-0 items-center gap-2 border-b border-default px-4 py-3">
          <UIcon name="i-lucide-cloud" class="size-4 text-muted" />
          <h2 class="text-sm font-semibold text-highlighted">
            {{ $t('docetra.drive.sourcesTitle') }}
          </h2>
          <span class="text-xs text-muted">{{ sources.length }}</span>
        </div>
        <UTable
          sticky="header"
          :data="sources"
          :columns="sourceColumns"
          :loading="loading"
          :empty="$t('docetra.drive.noSources')"
          class="min-h-0 flex-1"
          :ui="tableUi"
        >
          <template #syncStatus-cell="{ row }">
            <UBadge
              :color="syncStatusColor((row.original as DriveSource).syncStatus)"
              variant="subtle"
              size="sm"
            >
              {{ (row.original as DriveSource).syncStatus || '—' }}
            </UBadge>
          </template>
          <template #lastSyncAt-cell="{ row }">
            {{ formatDateTime((row.original as DriveSource).lastSyncAt) }}
          </template>
          <template #actions-cell="{ row }">
            <UButton
              v-if="canSync"
              size="xs"
              color="neutral"
              variant="soft"
              icon="i-lucide-refresh-cw"
              :loading="isSyncActive(row.original as DriveSource)"
              :disabled="isSyncActive(row.original as DriveSource)"
              @click="startSync(row.original as DriveSource)"
            >
              {{ $t('docetra.drive.syncNow') }}
            </UButton>
          </template>
        </UTable>
      </section>

      <section class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <div class="flex shrink-0 items-center gap-2 border-b border-default px-4 py-3">
          <UIcon name="i-lucide-files" class="size-4 text-muted" />
          <h2 class="text-sm font-semibold text-highlighted">
            {{ $t('docetra.drive.syncedFiles', { count: files.length }) }}
          </h2>
        </div>
        <UTable
          sticky="header"
          :data="files"
          :columns="fileColumns"
          :loading="loading"
          :empty="$t('docetra.drive.noFiles')"
          class="min-h-0 flex-1"
          :ui="tableUi"
        >
          <template #sizeBytes-cell="{ row }">
            {{ formatBytes(Number(row.original.sizeBytes || 0)) }}
          </template>
          <template #syncedAt-cell="{ row }">
            {{ formatDateTime(row.original.syncedAt) }}
          </template>
          <template #link-cell="{ row }">
            <a
              v-if="(row.original as { webViewLink?: string }).webViewLink"
              :href="(row.original as { webViewLink?: string }).webViewLink"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              <UIcon name="i-lucide-external-link" class="size-3.5" />
              {{ $t('docetra.drive.openInDrive') }}
            </a>
          </template>
        </UTable>
      </section>
    </div>
  </WorkspaceAppWorkspacePage>
</template>

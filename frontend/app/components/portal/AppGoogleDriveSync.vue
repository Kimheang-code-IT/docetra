<script setup lang="ts">
/**
 * Dedicated Google Drive sync workflow (portal).
 * Create source → start sync → poll job with backoff → status → refresh files.
 * Uses the dedicated Drive APIs instead of generic entity CRUD.
 */
import { ApiEndpoints } from '~/utils/constants/api-endpoints'

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

const sources = ref<DriveSource[]>([])
const files = ref<{ id: string, driveFileId: string, name: string, mimeType?: string, sizeBytes?: number, syncedAt?: string, webViewLink?: string }[]>([])
const loading = ref(false)
const creating = ref(false)
const syncingIds = ref<Set<string>>(new Set())
const pollingTimers = new Map<string, ReturnType<typeof setTimeout>>()
const jobStatus = ref<{ sourceId: string, status: string, fileCount?: number, error?: string } | null>(null)

const showCreate = ref(false)
const draft = reactive({ name: '', folderId: '' })

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
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-lg font-semibold text-highlighted">
        {{ $t('docetra.pages.googleDriveSync') }}
      </h2>
      <div class="flex items-center gap-2">
        <UButton
          icon="i-lucide-refresh-cw"
          color="neutral"
          variant="outline"
          size="sm"
          :loading="loading"
          @click="load"
        >
          {{ $t('actions.refresh') }}
        </UButton>
        <UButton
          icon="i-lucide-plus"
          size="sm"
          :disabled="showCreate"
          @click="showCreate = true"
        >
          {{ $t('docetra.drive.newSource') }}
        </UButton>
      </div>
    </div>

    <UCard v-if="showCreate">
      <form class="grid gap-3 sm:grid-cols-2" @submit.prevent="createSource">
        <UFormField :label="$t('docetra.fields.name')">
          <UInput v-model="draft.name" class="w-full" />
        </UFormField>
        <UFormField :label="$t('docetra.drive.folderId')" help="Google Drive folder ID">
          <UInput v-model="draft.folderId" class="w-full" />
        </UFormField>
        <div class="flex items-center gap-2 sm:col-span-2">
          <UButton type="submit" :loading="creating" :disabled="creating">
            {{ $t('actions.save') }}
          </UButton>
          <UButton color="neutral" variant="ghost" @click="showCreate = false">
            {{ $t('actions.cancel') }}
          </UButton>
        </div>
      </form>
    </UCard>

    <div v-if="jobStatus" class="text-sm text-toned" data-testid="drive-job-status">
      <UIcon
        :name="jobStatus.status === 'completed' ? 'i-lucide-check-circle' : jobStatus.status === 'failed' || jobStatus.status === 'cancelled' ? 'i-lucide-x-circle' : 'i-lucide-loader-circle'"
        class="me-1 inline-block size-4"
        :class="jobStatus.status === 'failed' || jobStatus.status === 'cancelled' ? 'text-error' : jobStatus.status === 'completed' ? 'text-success' : 'animate-spin'"
      />
      {{ jobStatusLabel }}
      <span v-if="jobStatus.error" class="text-error">— {{ jobStatus.error }}</span>
    </div>

    <UTable
      :data="sources"
      :columns="[
        { accessorKey: 'name', header: $t('docetra.fields.name') },
        { accessorKey: 'folderId', header: $t('docetra.drive.folderId') },
        { accessorKey: 'syncStatus', header: $t('docetra.fields.syncStatus') },
        { accessorKey: 'lastSyncAt', header: $t('docetra.fields.lastSync') },
        { id: 'actions', header: '' },
      ]"
    >
      <template #actions-cell="{ row }">
        <UButton
          size="xs"
          :icon="'i-lucide-refresh-cw'"
          :loading="isSyncActive(row.original as DriveSource)"
          :disabled="isSyncActive(row.original as DriveSource)"
          @click="startSync(row.original as DriveSource)"
        >
          {{ $t('docetra.drive.syncNow') }}
        </UButton>
      </template>
    </UTable>

    <h3 class="pt-2 text-sm font-semibold text-highlighted">
      {{ $t('docetra.drive.syncedFiles', { count: files.length }) }}
    </h3>
    <UTable
      :data="files"
      :columns="[
        { accessorKey: 'name', header: $t('docetra.fields.name') },
        { accessorKey: 'mimeType', header: $t('docetra.fields.type') },
        { accessorKey: 'sizeBytes', header: $t('docetra.fields.size') },
        { accessorKey: 'syncedAt', header: $t('docetra.fields.syncedAt') },
        { id: 'link', header: '' },
      ]"
    >
      <template #size-cell="{ row }">
        {{ formatBytes(Number(row.original.sizeBytes || 0)) }}
      </template>
      <template #link-cell="{ row }">
        <a
          v-if="(row.original as { webViewLink?: string }).webViewLink"
          :href="(row.original as { webViewLink?: string }).webViewLink"
          target="_blank"
          rel="noopener"
          class="text-primary text-sm"
        >
          {{ $t('docetra.drive.openInDrive') }}
        </a>
      </template>
    </UTable>
  </div>
</template>

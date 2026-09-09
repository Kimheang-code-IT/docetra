import type { ApiResponse } from '~/types/docetra/common'
import type { CreateExportJobInput, ExportJob } from '~/types/docetra/export'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'

const POLL_INTERVALS_MS = [1500, 2000, 3000, 5000]
/** Worker executes exports via RabbitMQ; give long exports room before giving up. */
const POLL_TIMEOUT_MS = 120000

/**
 * Shared export pipeline for every entity: create the job, poll its status
 * (Redis-backed status endpoint), toast the outcome, and download the file.
 */
export function useExportJobRunner() {
  const { t } = useI18n()
  const toast = useToast()
  // Export creation and polling happen after user interaction; retain the API
  // client captured during setup so delayed polls never call useApi() out of context.
  const api = useApi()
  // Stop polling as soon as the calling component/page is disposed instead of
  // continuing in the background for up to two minutes.
  let disposed = false
  onScopeDispose(() => { disposed = true }, true)

  function createExportJob(input: CreateExportJobInput): Promise<ApiResponse<ExportJob>> {
    return api.post<ApiResponse<ExportJob>>(ApiEndpoints.EXPORT_JOBS, input)
  }

  function getExportJob(id: string): Promise<ApiResponse<ExportJob>> {
    return api.get<ApiResponse<ExportJob>>(`${ApiEndpoints.EXPORT_JOBS}/${id}`, {
      requestKey: `export-job:${id}`,
      cancelPrevious: false,
    })
  }

  function triggerDownload(url?: string) {
    if (!url) return
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.rel = 'noopener'
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
  }

  async function pollUntilDone(id: string): Promise<ExportJob | undefined> {
    const deadline = Date.now() + POLL_TIMEOUT_MS
    let attempt = 0
    while (!disposed && Date.now() < deadline) {
      // Backoff: 1.5s → 2s → 3s → 5s; stops immediately on completion/failure.
      const delay = POLL_INTERVALS_MS[Math.min(attempt, POLL_INTERVALS_MS.length - 1)]
      await new Promise(resolve => setTimeout(resolve, delay))
      attempt += 1
      try {
        const response = await getExportJob(id)
        const job = response?.data
        if (!job) return undefined
        if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') return job
      }
      catch {
        // Transient poll errors keep waiting until the deadline.
      }
    }
    return undefined
  }

  async function run(input: CreateExportJobInput): Promise<ExportJob | undefined> {
    const created = await createExportJob(input)
    const jobId = String(created?.data?.id || '')
    if (!jobId) {
      toast.add({ title: t('docetra.exportDialog.failed'), color: 'error' })
      return undefined
    }
    toast.add({ title: t('docetra.exportDialog.queued'), color: 'info' })
    const job = await pollUntilDone(jobId)
    if (disposed) return undefined
    if (job?.status === 'completed') {
      toast.add({
        title: t('docetra.exportDialog.completed'),
        description: job.fileName || undefined,
        color: 'success',
      })
      triggerDownload(job.downloadUrl)
      return job
    }
    if (job?.status === 'failed') {
      toast.add({ title: t('docetra.exportDialog.failed'), color: 'error' })
    }
    else {
      toast.add({ title: t('docetra.exportDialog.timeout'), color: 'warning' })
    }
    return job
  }

  return { run }
}

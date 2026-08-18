import type { ApiResponse } from '~/types/docetra/common'
import type { CreateExportJobInput, ExportJob } from '~/types/docetra/export'
import { createId, mockLatency, nowIso, ok } from '~/mocks/query'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'

function usesMockData() {
  return useRuntimeConfig().public.useMockData !== false
}

/** Starts a server-side export. The UI never downloads all matching rows. */
export async function createExportJob(input: CreateExportJobInput): Promise<ApiResponse<ExportJob>> {
  if (!usesMockData()) return useApi().post<ApiResponse<ExportJob>>(ApiEndpoints.EXPORT_JOBS, input)
  await mockLatency(null)
  const job: ExportJob = {
    id: createId('export'),
    status: 'completed',
    resource: input.resource,
    createdAt: nowIso(),
  }
  return ok(job)
}

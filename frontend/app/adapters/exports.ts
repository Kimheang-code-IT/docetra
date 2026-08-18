import type { ApiResponse } from '~/types/docetra/common'
import type { CreateExportJobInput, ExportJob } from '~/types/docetra/export'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'

export async function createExportJob(input: CreateExportJobInput): Promise<ApiResponse<ExportJob>> {
  return useApi().post<ApiResponse<ExportJob>>(ApiEndpoints.EXPORT_JOBS, input)
}

export async function getExportJob(id: string): Promise<ApiResponse<ExportJob>> {
  return useApi().get<ApiResponse<ExportJob>>(`${ApiEndpoints.EXPORT_JOBS}/${encodeURIComponent(id)}`)
}

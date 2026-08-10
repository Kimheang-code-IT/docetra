import type { MeetingHistory } from '~/types/docetra/entities'
import type {
  AssignMeetingTopicBody,
  DriveFileCatalogItem,
  LinkMeetingDriveFileBody,
  ReorderMeetingsBody,
} from '~/types/docetra/meeting-api'
import type { ApiResponse, AttachmentMeta } from '~/types/docetra/common'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { getEntityAdapter } from '~/config/entities'
import { mockDriveFileCatalog } from '~/mocks/datasets'
import { createId, mockLatency, nowIso, ok } from '~/mocks/query'

function usesMockData() {
  return useRuntimeConfig().public.useMockData !== false
}

/** Assign or unassign a meeting to a topic (API-ready). */
export async function assignMeetingToTopic(
  meetingId: string,
  body: AssignMeetingTopicBody,
): Promise<ApiResponse<MeetingHistory>> {
  const endpoint = ApiEndpoints.MEETING_ASSIGN_TOPIC(meetingId)
  if (!usesMockData()) {
    return useApi().post<ApiResponse<MeetingHistory>>(endpoint, body)
  }
  const adapter = getEntityAdapter('meetingHistory')
  return adapter.update(meetingId, {
    topicId: body.topicId || undefined,
    topicTitle: body.topicTitle,
    sortOrder: body.sortOrder,
  } as Partial<MeetingHistory>)
}

/** Reorder meetings inside one topic (API-ready). */
export async function reorderMeetingsInTopic(
  body: ReorderMeetingsBody,
): Promise<ApiResponse<{ topicId: string; orderedMeetingIds: string[] }>> {
  if (!usesMockData()) {
    return useApi().post<ApiResponse<{ topicId: string; orderedMeetingIds: string[] }>>(
      ApiEndpoints.MEETINGS_REORDER,
      body,
    )
  }
  await mockLatency(null)
  const adapter = getEntityAdapter('meetingHistory')
  await Promise.all(
    body.orderedMeetingIds.map((id, index) =>
      adapter.update(id, { sortOrder: index } as Partial<MeetingHistory>),
    ),
  )
  return ok({ topicId: body.topicId, orderedMeetingIds: body.orderedMeetingIds })
}

/** Catalog of synced Google Drive files for meeting note attachments. */
export async function listPortalDriveFiles(query?: {
  search?: string
  page?: number
  limit?: number
}): Promise<ApiResponse<DriveFileCatalogItem[]>> {
  if (!usesMockData()) {
    return useApi().get<ApiResponse<DriveFileCatalogItem[]>>(ApiEndpoints.PORTAL_DRIVE_FILES, {
      query,
      requestKey: 'portal-drive-files',
      cancelPrevious: true,
    })
  }
  await mockLatency(null)
  let rows = [...mockDriveFileCatalog]
  const q = query?.search?.trim().toLowerCase()
  if (q) rows = rows.filter(r => r.name.toLowerCase().includes(q))
  const limit = query?.limit ?? 50
  return ok(rows.slice(0, limit))
}

/** Link an existing Drive file to a meeting (async-safe on real API). */
export async function linkMeetingDriveFile(
  meetingId: string,
  body: LinkMeetingDriveFileBody,
): Promise<ApiResponse<AttachmentMeta>> {
  const endpoint = ApiEndpoints.MEETING_ATTACHMENTS_LINK(meetingId)
  if (!usesMockData()) {
    return useApi().post<ApiResponse<AttachmentMeta>>(endpoint, body)
  }
  await mockLatency(null)
  const adapter = getEntityAdapter('meetingHistory')
  const catalogItem = mockDriveFileCatalog.find(f => f.driveFileId === body.driveFileId)
  const file: AttachmentMeta = {
    id: createId('att'),
    name: body.displayName || catalogItem?.name || 'Drive file',
    mimeType: catalogItem?.mimeType || 'application/octet-stream',
    sizeBytes: catalogItem?.sizeBytes ?? 0,
    url: catalogItem?.webViewLink,
    uploadedAt: nowIso(),
    storageSource: 'google_drive',
  }
  const existing = (await adapter.listAttachments?.(meetingId))?.data || []
  if (adapter.replaceAttachments) {
    await adapter.replaceAttachments(meetingId, [file, ...existing])
  }
  return ok(file)
}

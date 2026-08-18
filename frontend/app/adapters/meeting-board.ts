import type { MeetingHistory } from '~/types/docetra/entities'
import type {
  AssignMeetingTopicBody,
  DriveFileCatalogItem,
  LinkMeetingDriveFileBody,
  ReorderMeetingsBody,
} from '~/types/docetra/meeting-api'
import type { ApiResponse, AttachmentMeta } from '~/types/docetra/common'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'

export async function assignMeetingToTopic(
  meetingId: string,
  body: AssignMeetingTopicBody,
): Promise<ApiResponse<MeetingHistory>> {
  return useApi().post<ApiResponse<MeetingHistory>>(ApiEndpoints.MEETING_ASSIGN_TOPIC(meetingId), body)
}

export async function reorderMeetingsInTopic(
  body: ReorderMeetingsBody,
): Promise<ApiResponse<{ topicId: string; orderedMeetingIds: string[] }>> {
  return useApi().post<ApiResponse<{ topicId: string; orderedMeetingIds: string[] }>>(
    ApiEndpoints.MEETINGS_REORDER,
    body,
  )
}

export async function listPortalDriveFiles(query?: {
  search?: string
  page?: number
  limit?: number
}): Promise<ApiResponse<DriveFileCatalogItem[]>> {
  return useApi().get<ApiResponse<DriveFileCatalogItem[]>>(ApiEndpoints.PORTAL_DRIVE_FILES, {
    query,
    requestKey: 'portal-drive-files',
    cancelPrevious: true,
  })
}

export async function linkMeetingDriveFile(
  meetingId: string,
  body: LinkMeetingDriveFileBody,
): Promise<ApiResponse<AttachmentMeta>> {
  return useApi().post<ApiResponse<AttachmentMeta>>(ApiEndpoints.MEETING_ATTACHMENTS_LINK(meetingId), body)
}

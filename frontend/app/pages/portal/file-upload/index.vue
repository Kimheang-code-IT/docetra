<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'
import { adapters } from '~/adapters'
import { createId, nowIso, person } from '~/mocks/seed'

const config = getEntityConfig('fileUploads')

definePageMeta({
  titleKey: 'docetra.pages.fileUpload',
  permission: 'portal.file_upload.view',
})

const toast = useToast()
const { t } = useI18n()
const uploading = ref(false)

async function onUpload(files: File[] | null | undefined) {
  if (!files?.length) return
  uploading.value = true
  try {
    for (const file of files) {
      await adapters.fileUploads.create({
        id: createId('fu'),
        fileName: file.name,
        name: file.name,
        mimeType: file.type || 'application/octet-stream',
        sizeBytes: file.size,
        status: 'completed',
        uploader: person(0),
        storageSource: 'local',
        progress: 100,
        createdAt: nowIso(),
        updatedAt: nowIso(),
      } as any)
    }
    toast.add({ title: t('docetra.attachments.uploaded'), color: 'success' })
  }
  catch (e: any) {
    toast.add({ title: e?.message || 'Upload failed', color: 'error' })
  }
  finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div class="w-full px-1.5 pt-1.5 pb-0">
      <section class="mb-4 rounded-lg border border-dashed border-primary/30 bg-default p-4">
        <DocumentAppAttachmentsPanel :files="[]" :pending="uploading" @upload="onUpload" />
      </section>
    </div>
    <WorkspaceEntityWorkspaceView :config="config" />
  </div>
</template>

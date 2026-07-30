<script setup lang="ts">
import type { AttachmentMeta } from '~/types/docetra/common'

defineProps<{
  files: AttachmentMeta[]
  pending?: boolean
}>()

const emit = defineEmits<{
  upload: [File[]]
}>()

function onFiles(files: File[] | null | undefined) {
  if (files?.length) emit('upload', files)
}
</script>

<template>
  <section class="rounded-lg border border-default bg-default p-4 space-y-3">
    <h3 class="text-sm font-semibold text-highlighted">{{ $t('docetra.attachments.title') }}</h3>
    <UFileUpload
      multiple
      :label="$t('docetra.attachments.drop')"
      :description="$t('docetra.attachments.hint')"
      @update:model-value="onFiles"
    />
    <div v-if="pending" class="flex justify-center py-4">
      <UIcon name="i-lucide-loader-circle" class="size-5 animate-spin text-primary" />
    </div>
    <ul v-else class="space-y-2">
      <li v-for="file in files" :key="file.id" class="flex items-center justify-between gap-2 text-sm">
        <div class="flex min-w-0 items-center gap-2">
          <UIcon name="i-lucide-file" class="size-4 text-muted" />
          <span class="truncate">{{ file.name }}</span>
        </div>
        <span class="text-xs text-muted">{{ Math.round(file.sizeBytes / 1024) }} KB</span>
      </li>
      <li v-if="!files.length" class="text-sm text-muted">{{ $t('docetra.states.noAttachments') }}</li>
    </ul>
  </section>
</template>

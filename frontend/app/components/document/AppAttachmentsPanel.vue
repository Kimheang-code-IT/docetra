<script setup lang="ts">
import type { AttachmentMeta } from '~/types/docetra/common'
import { fileTypeIcon, formatFileSize } from '~/utils/file-icon'

defineProps<{
  files: AttachmentMeta[]
  pending?: boolean
}>()

const emit = defineEmits<{
  upload: [File[]]
}>()

const picked = ref<File[] | null>(null)

watch(picked, (files) => {
  if (!files?.length) return
  emit('upload', files)
  nextTick(() => {
    picked.value = null
  })
})
</script>

<template>
  <section class="space-y-3 rounded-lg border border-default bg-default p-4">
    <div class="flex items-center gap-2">
      <UIcon name="i-lucide-paperclip" class="size-4 text-muted" />
      <h3 class="text-sm font-semibold text-highlighted">
        {{ $t('docetra.attachments.title') }}
      </h3>
    </div>

    <CommonAppFileUpload
      v-model="picked"
      multiple
      icon="i-lucide-cloud-upload"
      :label="$t('docetra.attachments.drop')"
      :description="$t('docetra.attachments.hint')"
      class="w-full min-h-40"
    />

    <div v-if="pending" class="flex justify-center py-4">
      <UIcon name="i-lucide-loader-circle" class="size-5 animate-spin text-primary" />
    </div>

    <ul v-else class="space-y-1.5">
      <li
        v-for="file in files"
        :key="file.id"
        class="flex items-center gap-2.5 rounded-md bg-elevated/50 px-2.5 py-2 text-sm"
      >
        <div class="grid size-8 shrink-0 place-items-center rounded-md bg-default ring ring-default">
          <UIcon
            :name="fileTypeIcon(file).icon"
            class="size-3.5"
            :class="fileTypeIcon(file).class"
          />
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate font-medium text-highlighted">
            {{ file.name }}
          </p>
          <p class="text-xs text-muted">
            {{ formatFileSize(file.sizeBytes) }}
          </p>
        </div>
      </li>
      <li v-if="!files.length" class="px-1 text-sm text-muted">
        {{ $t('docetra.states.noAttachments') }}
      </li>
    </ul>
  </section>
</template>

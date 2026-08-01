<script setup lang="ts">
import Uppy from '@uppy/core'
import XHRUpload from '@uppy/xhr-upload'
import UppyDashboard from '@uppy/vue/dashboard'
import type { AttachmentMeta } from '~/types/docetra/common'

import '@uppy/core/css/style.min.css'
import '@uppy/dashboard/css/style.min.css'

const props = withDefaults(defineProps<{
  entityId: string
  endpoint?: string
  height?: number
  /** Fill parent height (ResizeObserver). Overrides fixed height when true. */
  fill?: boolean
  note?: string
  disabled?: boolean
}>(), {
  height: 280,
  fill: false,
})

const emit = defineEmits<{
  complete: [AttachmentMeta[]]
}>()

const { t } = useI18n()
const config = useRuntimeConfig()
const uppy = shallowRef<InstanceType<typeof Uppy> | null>(null)
const bootError = ref<string | null>(null)
const booted = ref(false)
const fallbackInput = ref<HTMLInputElement | null>(null)
const hostEl = ref<HTMLElement | null>(null)
const measuredHeight = ref(props.height)

const effectiveHeight = computed(() =>
  props.fill ? Math.max(measuredHeight.value, 200) : props.height,
)

const dashboardProps = computed(() => ({
  width: '100%' as const,
  height: effectiveHeight.value,
  proudlyDisplayPoweredByUppy: false,
  note: props.note || t('docetra.meetingNotes.uploadHint'),
  showProgressDetails: true,
}))

useResizeObserver(hostEl, (entries) => {
  if (!props.fill) return
  const entry = entries[0]
  if (!entry) return
  measuredHeight.value = Math.floor(entry.contentRect.height)
})

function toAttachmentMeta(file: {
  name?: string | null
  type?: string | null
  size?: number | null
}): AttachmentMeta {
  return {
    id: `att_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    name: file.name || 'file',
    mimeType: file.type || 'application/octet-stream',
    sizeBytes: file.size || 0,
    uploadedAt: new Date().toISOString(),
    storageSource: 'local',
  }
}

function emitFromFiles(files: File[]) {
  if (!files.length) return
  emit('complete', files.map(file => toAttachmentMeta(file)))
}

function onFallbackPicked(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  input.value = ''
  emitFromFiles(files)
}

onMounted(() => {
  try {
    const instance = new Uppy({
      id: `uppy-${props.entityId}-${Date.now()}`,
      autoProceed: false,
      restrictions: {
        maxNumberOfFiles: 25,
        maxFileSize: 200 * 1024 * 1024,
      },
    })

    const useMock = config.public.useMockData !== false
    if (useMock) {
      instance.addUploader(async (fileIDs) => {
        const metas: AttachmentMeta[] = []
        for (const id of fileIDs) {
          const file = instance.getFile(id)
          if (!file) continue
          const size = file.size || 0
          instance.setFileState(id, {
            progress: {
              uploadComplete: true,
              uploadStarted: Date.now(),
              percentage: 100,
              bytesUploaded: size,
              bytesTotal: size,
            },
          })
          instance.emit('upload-success', file, { body: {}, status: 200 })
          metas.push(toAttachmentMeta(file))
        }
        if (metas.length) emit('complete', metas)
      })
    }
    else {
      const endpoint = props.endpoint
        || `${config.public.apiBase}${ApiEndpoints.ATTACHMENTS('entities', props.entityId)}`
      instance.use(XHRUpload, {
        endpoint,
        fieldName: 'file',
        formData: true,
        bundle: false,
      })
      instance.on('complete', (result) => {
        const metas = (result.successful || []).map(file => toAttachmentMeta(file))
        if (metas.length) emit('complete', metas)
      })
    }

    uppy.value = instance
  }
  catch (error: any) {
    console.error('[AppUppyUploader] failed to boot', error)
    bootError.value = error?.message || 'Uploader failed to load'
  }
  finally {
    booted.value = true
  }
})

onBeforeUnmount(() => {
  uppy.value?.destroy()
  uppy.value = null
})
</script>

<template>
  <div
    class="flex min-h-0 flex-col gap-2"
    :class="fill ? 'h-full' : ''"
  >
    <div
      v-if="!booted"
      class="flex items-center justify-center rounded-lg border border-dashed border-default bg-elevated/30"
      :class="fill ? 'min-h-0 flex-1' : ''"
      :style="fill ? undefined : { minHeight: `${height}px` }"
    >
      <UIcon name="i-lucide-loader-circle" class="size-5 animate-spin text-primary" />
    </div>

    <div
      v-else-if="bootError || !uppy"
      class="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-default bg-elevated/30 px-4 py-6 text-center"
      :class="fill ? 'min-h-0 flex-1' : ''"
      :style="fill ? undefined : { minHeight: `${height}px` }"
    >
      <UIcon name="i-lucide-upload" class="size-8 text-muted" />
      <div class="space-y-1">
        <p class="text-sm font-medium text-highlighted">
          {{ $t('docetra.attachments.drop') }}
        </p>
        <p class="text-xs text-muted">
          {{ note || $t('docetra.meetingNotes.uploadHint') }}
        </p>
      </div>
      <UButton
        color="primary"
        variant="soft"
        icon="i-lucide-file-plus"
        :label="$t('docetra.meetingNotes.chooseFiles')"
        :disabled="disabled"
        @click="fallbackInput?.click()"
      />
      <input
        ref="fallbackInput"
        type="file"
        class="sr-only"
        multiple
        :disabled="disabled"
        @change="onFallbackPicked"
      >
      <p v-if="bootError" class="text-xs text-error">{{ bootError }}</p>
    </div>

    <ClientOnly v-else>
      <div
        ref="hostEl"
        class="uppy-host min-h-0 overflow-hidden rounded-lg border border-default"
        :class="fill ? 'h-full flex-1' : ''"
        :style="fill ? undefined : { minHeight: `${height}px` }"
      >
        <UppyDashboard
          :uppy="uppy"
          :props="dashboardProps"
        />
      </div>
      <template #fallback>
        <div
          class="flex items-center justify-center rounded-lg border border-dashed border-default bg-elevated/30"
          :class="fill ? 'min-h-0 flex-1' : ''"
          :style="fill ? undefined : { minHeight: `${height}px` }"
        >
          <UIcon name="i-lucide-loader-circle" class="size-5 animate-spin text-primary" />
        </div>
      </template>
    </ClientOnly>
  </div>
</template>

<style scoped>
.uppy-host :deep(.uppy-Dashboard-inner) {
  width: 100% !important;
  border: 0;
  background: transparent;
}
</style>

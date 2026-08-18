<script setup lang="ts">
import Uppy from '@uppy/core'
import XHRUpload from '@uppy/xhr-upload'
import UppyDashboard from '@uppy/vue/dashboard'
import type { ApiResponse, AttachmentMeta } from '~/types/docetra/common'
import { useAuthStore } from '~/stores/auth'
import { createClientId } from '~/utils/client-id'
import { csrfRequestHeaders } from '~/utils/security/csrf'

import '~/assets/css/uppy.css'

const props = withDefaults(defineProps<{
  entityId: string
  endpoint?: string
  height?: number
  /** Fill parent height (ResizeObserver). Overrides fixed height when true. */
  fill?: boolean
  note?: string
  disabled?: boolean
  maxFileSizeMb?: number
  maxNumberOfFiles?: number
  allowedFileTypes?: string[]
}>(), {
  height: 280,
  fill: false,
  maxFileSizeMb: 200,
  maxNumberOfFiles: 25,
  allowedFileTypes: () => [...DEFAULT_UPLOAD_TYPES],
})

const emit = defineEmits<{
  complete: [AttachmentMeta[]]
}>()

const { t } = useI18n()
const config = useRuntimeConfig()
const authStore = useAuthStore()
const api = useApi()
const uppy = shallowRef<Uppy<any, any> | null>(null)
const bootError = ref<string | null>(null)
const booted = ref(false)
const fallbackInput = ref<HTMLInputElement | null>(null)
const hostEl = ref<HTMLElement | null>(null)
const measuredHeight = ref(props.height)

const effectiveHeight = computed(() =>
  props.fill ? Math.max(measuredHeight.value, 200) : props.height,
)

/** Reserve space for the file-type icon strip above the dashboard. */
const dashboardHeight = computed(() => Math.max(effectiveHeight.value - 48, 160))

const typeHints = [
  { icon: 'i-lucide-file-text', class: 'text-red-600 dark:text-red-400', label: 'PDF' },
  { icon: 'i-lucide-image', class: 'text-sky-600 dark:text-sky-400', label: 'Image' },
  { icon: 'i-lucide-file-type', class: 'text-blue-600 dark:text-blue-400', label: 'Doc' },
  { icon: 'i-lucide-sheet', class: 'text-emerald-600 dark:text-emerald-400', label: 'Sheet' },
  { icon: 'i-lucide-file-archive', class: 'text-amber-600 dark:text-amber-400', label: 'Zip' },
] as const

const dashboardProps = computed(() => ({
  width: '100%' as const,
  height: dashboardHeight.value,
  proudlyDisplayPoweredByUppy: false,
  note: props.note || t('docetra.meetingNotes.uploadHint'),
  showProgressDetails: true,
  hideUploadButton: false,
}))

useResizeObserver(hostEl, (entries) => {
  if (!props.fill) return
  const entry = entries[0]
  if (!entry) return
  measuredHeight.value = Math.floor(entry.contentRect.height)
})

const uploadPath = computed(() => props.endpoint || ApiEndpoints.ATTACHMENTS('entities', props.entityId))

const uploadUrl = computed(() => {
  return sameOriginApiUrl(uploadPath.value, String(config.public.apiBase))
})

const inputAccept = computed(() => props.allowedFileTypes.join(','))

function validFile(file: File): boolean {
  return file.size <= props.maxFileSizeMb * 1024 * 1024
    && fileMatchesAllowedTypes(file, props.allowedFileTypes)
}

function attachmentFromResponse(body: unknown): AttachmentMeta | null {
  if (!body || typeof body !== 'object') return null
  const candidate = 'data' in body ? (body as ApiResponse<unknown>).data : body
  if (!candidate || typeof candidate !== 'object' || !('id' in candidate)) return null
  return candidate as AttachmentMeta
}

function mockAttachment(file: { name?: string | null; type?: string | null; size?: number | null }): AttachmentMeta {
  return {
    id: createClientId('att'),
    name: file.name || 'file',
    mimeType: file.type || 'application/octet-stream',
    sizeBytes: file.size || 0,
    uploadedAt: new Date().toISOString(),
    storageSource: 'local',
  }
}

async function onFallbackPicked(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || []).filter(validFile).slice(0, props.maxNumberOfFiles)
  input.value = ''
  if (config.public.useMockData !== false) {
    if (files.length) emit('complete', files.map(mockAttachment))
    return
  }
  if (!uploadUrl.value) {
    bootError.value = 'Upload endpoint must use the configured API origin'
    return
  }
  const uploaded: AttachmentMeta[] = []
  for (const file of files) {
    const form = new FormData()
    form.append('file', file)
    const response = await api.post<AttachmentMeta | ApiResponse<AttachmentMeta>>(uploadUrl.value, form)
    const meta = attachmentFromResponse(response)
    if (meta) uploaded.push(meta)
  }
  if (uploaded.length) emit('complete', uploaded)
}

onMounted(() => {
  try {
    if (config.public.useMockData === false && !uploadUrl.value) {
      throw new Error('Upload endpoint must use the configured API origin')
    }
    const instance = new Uppy({
      id: `uppy-${props.entityId}-${Date.now()}`,
      autoProceed: false,
      restrictions: {
        maxNumberOfFiles: props.maxNumberOfFiles,
        maxFileSize: props.maxFileSizeMb * 1024 * 1024,
        allowedFileTypes: props.allowedFileTypes,
      },
    })

    if (config.public.useMockData !== false) {
      instance.addUploader(async (fileIds) => {
        for (const id of fileIds) {
          const file = instance.getFile(id)
          if (!file) continue
          const size = file.size || 0
          instance.setFileState(id, {
            progress: { uploadComplete: true, uploadStarted: Date.now(), percentage: 100, bytesUploaded: size, bytesTotal: size },
          })
          instance.emit('upload-success', file, { body: { data: mockAttachment(file) }, status: 200 } as any)
        }
      })
    }
    else {
      const cookieAuth = config.public.authMode === 'cookie'
      instance.use(XHRUpload, {
        endpoint: uploadUrl.value!,
        fieldName: 'file',
        formData: true,
        bundle: false,
        withCredentials: cookieAuth,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          ...(!cookieAuth && authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {}),
          ...csrfRequestHeaders(
            'POST',
            String(config.public.csrfCookieName),
            String(config.public.csrfHeaderName),
          ),
        },
      })
    }
    instance.on('complete', (result) => {
      const metas = (result.successful || [])
        .map(file => attachmentFromResponse(file.response?.body))
        .filter((file): file is AttachmentMeta => Boolean(file))
      if (metas.length) emit('complete', metas)
    })

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
      class="flex items-center justify-center rounded-xl border border-dashed border-default bg-elevated/40"
      :class="fill ? 'min-h-0 flex-1' : ''"
      :style="fill ? undefined : { minHeight: `${height}px` }"
    >
      <UIcon name="i-lucide-loader-circle" class="size-5 animate-spin text-primary" />
    </div>

    <div
      v-else-if="bootError || !uppy"
      class="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-default bg-elevated/40 px-4 py-6 text-center"
      :class="fill ? 'min-h-0 flex-1' : ''"
      :style="fill ? undefined : { minHeight: `${height}px` }"
    >
      <div class="grid size-14 place-items-center rounded-2xl bg-primary/10 ring ring-primary/20">
        <UIcon name="i-lucide-cloud-upload" class="size-7 text-primary" />
      </div>
      <div class="flex items-center justify-center gap-1.5">
        <span
          v-for="hint in typeHints"
          :key="hint.label"
          class="grid size-8 place-items-center rounded-md bg-default ring ring-default"
          :title="hint.label"
        >
          <UIcon :name="hint.icon" class="size-3.5" :class="hint.class" />
        </span>
      </div>
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
        :accept="inputAccept"
        :disabled="disabled"
        @change="onFallbackPicked"
      >
      <p v-if="bootError" class="text-xs text-error">{{ bootError }}</p>
    </div>

    <ClientOnly v-else>
      <div
        ref="hostEl"
        class="uppy-host flex min-h-0 flex-col overflow-hidden rounded-xl border border-dashed border-default bg-elevated/40"
        :class="fill ? 'h-full flex-1' : ''"
        :style="fill ? undefined : { minHeight: `${height}px` }"
      >
        <div class="flex shrink-0 items-center justify-center gap-1.5 border-b border-default/80 px-3 py-2.5">
          <div class="grid size-8 place-items-center rounded-lg bg-primary/10">
            <UIcon name="i-lucide-cloud-upload" class="size-4 text-primary" />
          </div>
          <div class="ms-1 flex items-center gap-1">
            <span
              v-for="hint in typeHints"
              :key="hint.label"
              class="grid size-7 place-items-center rounded-md bg-default/80 ring ring-default"
              :title="hint.label"
            >
              <UIcon :name="hint.icon" class="size-3.5" :class="hint.class" />
            </span>
          </div>
        </div>
        <div class="min-h-0 flex-1 overflow-hidden">
          <UppyDashboard
            :uppy="uppy"
            :props="dashboardProps"
          />
        </div>
      </div>
      <template #fallback>
        <div
          class="flex items-center justify-center rounded-xl border border-dashed border-default bg-elevated/40"
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
  box-shadow: none;
}

.uppy-host :deep(.uppy-Dashboard-AddFiles-title),
.uppy-host :deep(.uppy-Dashboard-note) {
  color: var(--ui-text-muted);
}

.uppy-host :deep(.uppy-DashboardContent-bar),
.uppy-host :deep(.uppy-StatusBar) {
  border-color: var(--ui-border);
  background: transparent;
}

.uppy-host :deep(.uppy-Dashboard-Item-previewInnerWrap) {
  background-color: var(--ui-bg-elevated);
}
</style>

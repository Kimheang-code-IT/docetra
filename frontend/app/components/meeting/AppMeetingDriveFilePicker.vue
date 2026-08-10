<script setup lang="ts">
import type { DriveFileCatalogItem } from '~/types/docetra/meeting-api'
import { listPortalDriveFiles } from '~/adapters/meeting-board'

const open = defineModel<boolean>('open', { default: false })

const emit = defineEmits<{
  select: [file: DriveFileCatalogItem]
}>()

const { t } = useI18n()
const toast = useToast()

const search = ref('')
const pending = ref(false)
const files = ref<DriveFileCatalogItem[]>([])

async function load() {
  pending.value = true
  try {
    const res = await listPortalDriveFiles({ search: search.value, limit: 40 })
    files.value = res.data || []
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.meetingNotes.driveLoadFailed'), color: 'error' })
  }
  finally {
    pending.value = false
  }
}

watch(open, (isOpen) => {
  if (isOpen) {
    search.value = ''
    load()
  }
})

let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(search, () => {
  if (!open.value) return
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => load(), 300)
})

function pick(file: DriveFileCatalogItem) {
  emit('select', file)
  open.value = false
}
</script>

<template>
  <UModal
    v-model:open="open"
    :title="$t('docetra.meetingNotes.pickDriveFile')"
  >
    <template #body>
      <div class="space-y-3">
        <CommonAppLiveSearch
          v-model="search"
          :placeholder="$t('docetra.meetingNotes.searchDriveFiles')"
        />
        <div v-if="pending" class="flex justify-center py-8">
          <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
        </div>
        <ul v-else class="max-h-80 space-y-2 overflow-y-auto">
          <li
            v-for="file in files"
            :key="file.id"
          >
            <button
              type="button"
              class="flex w-full items-center gap-3 rounded-lg border border-default px-3 py-2 text-left text-sm hover:border-primary/40 hover:bg-elevated"
              @click="pick(file)"
            >
              <UIcon name="i-lucide-hard-drive" class="size-4 shrink-0 text-muted" />
              <span class="min-w-0 flex-1 truncate font-medium">{{ file.name }}</span>
              <span class="shrink-0 text-xs text-muted">
                {{ Math.round((file.sizeBytes || 0) / 1024) }} KB
              </span>
            </button>
          </li>
          <li v-if="!files.length" class="py-6 text-center text-sm text-muted">
            {{ $t('docetra.states.empty') }}
          </li>
        </ul>
        <p class="text-xs text-muted">
          {{ $t('docetra.meetingNotes.drivePickHint') }}
        </p>
      </div>
    </template>
  </UModal>
</template>

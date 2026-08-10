<script setup lang="ts">
import type { AttachmentMeta, PersonSummary } from '~/types/docetra/common'
import { fileTypeIcon } from '~/utils/file-icon'

const props = defineProps<{
  title?: string
  subtitle?: string
  status?: string
  stage?: string
  owner?: PersonSummary
  assignee?: PersonSummary
  attachments?: AttachmentMeta[]
  tags?: string[]
  createdAt?: string
  updatedAt?: string
  readOnly?: boolean
  isFavorite?: boolean
  togglingFavorite?: boolean
  favoriteEnabled?: boolean
}>()

const emit = defineEmits<{
  'update:tags': [string[]]
  'update:attachments': [AttachmentMeta[]]
  'update:assignees': [PersonSummary[]]
  'update:shares': [PersonSummary[]]
  toggleFavorite: []
}>()

const { t } = useI18n()

const initial = computed(() => {
  const text = (props.title || '').trim()
  return text ? text.charAt(0).toUpperCase() : '—'
})

const assignees = ref<PersonSummary[]>([])
const shares = ref<PersonSummary[]>([])
const localAttachments = ref<AttachmentMeta[]>([])
const localTags = ref<string[]>([])

const adding = reactive({
  assign: false,
  attachments: false,
  tags: false,
  share: false,
})

const draft = reactive({
  assign: '',
  tag: '',
  share: '',
})

const fileInput = ref<HTMLInputElement | null>(null)

watch(
  () => props.assignee,
  (value) => {
    if (!value) return
    if (assignees.value.some(a => a.id === value.id)) return
    assignees.value = assignees.value.length ? [...assignees.value, value] : [value]
  },
  { immediate: true },
)

watch(
  () => props.attachments,
  (value) => {
    localAttachments.value = [...(value || [])]
  },
  { immediate: true, deep: true },
)

watch(
  () => props.tags,
  (value) => {
    localTags.value = [...(value || [])]
  },
  { immediate: true, deep: true },
)

function personInitial(name: string) {
  return (name || '?').trim().charAt(0).toUpperCase()
}

function relativeTime(iso?: string) {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return t('docetra.meta.justNow')
  if (mins === 1) return t('docetra.meta.minuteAgo')
  if (mins < 60) return t('docetra.meta.minutesAgo', { n: mins })
  const hours = Math.floor(mins / 60)
  if (hours === 1) return t('docetra.meta.hourAgo')
  if (hours < 24) return t('docetra.meta.hoursAgo', { n: hours })
  const days = Math.floor(hours / 24)
  if (days === 1) return t('docetra.meta.dayAgo')
  return t('docetra.meta.daysAgo', { n: days })
}

function makePerson(name: string): PersonSummary {
  const trimmed = name.trim()
  return {
    id: `local-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    name: trimmed,
  }
}

function addAssignee() {
  const name = draft.assign.trim()
  if (!name || props.readOnly) return
  if (assignees.value.some(a => a.name.toLowerCase() === name.toLowerCase())) {
    draft.assign = ''
    adding.assign = false
    return
  }
  assignees.value = [...assignees.value, makePerson(name)]
  draft.assign = ''
  adding.assign = false
  emit('update:assignees', assignees.value)
}

function removeAssignee(id: string) {
  if (props.readOnly) return
  assignees.value = assignees.value.filter(a => a.id !== id)
  emit('update:assignees', assignees.value)
}

function addShare() {
  const name = draft.share.trim()
  if (!name || props.readOnly) return
  if (shares.value.some(a => a.name.toLowerCase() === name.toLowerCase())) {
    draft.share = ''
    adding.share = false
    return
  }
  shares.value = [...shares.value, makePerson(name)]
  draft.share = ''
  adding.share = false
  emit('update:shares', shares.value)
}

function removeShare(id: string) {
  if (props.readOnly) return
  shares.value = shares.value.filter(a => a.id !== id)
  emit('update:shares', shares.value)
}

function addTag() {
  const tag = draft.tag.trim()
  if (!tag || props.readOnly) return
  if (localTags.value.some(t => t.toLowerCase() === tag.toLowerCase())) {
    draft.tag = ''
    adding.tags = false
    return
  }
  localTags.value = [...localTags.value, tag]
  draft.tag = ''
  adding.tags = false
  emit('update:tags', localTags.value)
}

function removeTag(tag: string) {
  if (props.readOnly) return
  localTags.value = localTags.value.filter(t => t !== tag)
  emit('update:tags', localTags.value)
}

function openAttachmentPicker() {
  if (props.readOnly) return
  fileInput.value?.click()
}

function onFilesSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (!files.length) return

  const next = files.map((file, index) => ({
    id: `local-file-${Date.now()}-${index}`,
    name: file.name,
    mimeType: file.type || 'application/octet-stream',
    sizeBytes: file.size,
    uploadedAt: new Date().toISOString(),
  }))

  localAttachments.value = [...localAttachments.value, ...next]
  emit('update:attachments', localAttachments.value)
  input.value = ''
}

function removeAttachment(id: string) {
  if (props.readOnly) return
  localAttachments.value = localAttachments.value.filter(f => f.id !== id)
  emit('update:attachments', localAttachments.value)
}
</script>

<template>
  <aside class="flex w-full shrink-0 flex-col border-default bg-default lg:w-64 xl:w-72 lg:border-s">
    <section class="flex items-start gap-3 border-b border-default p-4">
      <div class="grid size-14 shrink-0 place-items-center rounded-lg bg-elevated text-xl font-semibold text-toned">
        {{ initial }}
      </div>
      <div class="min-w-0 flex-1 pt-0.5">
        <p class="truncate text-sm font-semibold text-highlighted">{{ title || '—' }}</p>
        <p v-if="subtitle" class="mt-0.5 truncate text-xs text-muted">{{ subtitle }}</p>
        <div class="mt-2 flex items-center">
          <UButton
            icon="i-lucide-heart"
            :color="props.isFavorite ? 'error' : 'neutral'"
            variant="ghost"
            size="xs"
            square
            :loading="togglingFavorite"
            :disabled="!favoriteEnabled || togglingFavorite"
            :aria-label="$t(props.isFavorite ? 'docetra.meta.removeFavorite' : 'docetra.meta.addFavorite')"
            :aria-pressed="props.isFavorite"
            :title="$t(props.isFavorite ? 'docetra.meta.removeFavorite' : 'docetra.meta.addFavorite')"
            :ui="{
              leadingIcon: [
                'transition-transform duration-200',
                props.isFavorite ? 'scale-110 fill-current' : 'scale-100',
              ],
            }"
            @click="emit('toggleFavorite')"
          />
        </div>
      </div>
    </section>

    <div class="min-h-0 flex-1 overflow-y-auto py-1">
      <!-- Assign -->
      <section class="px-4 py-2.5">
        <div class="flex items-center gap-2 text-sm text-toned">
          <UIcon name="i-lucide-users" class="size-4 shrink-0 text-muted" />
          <span class="min-w-0 flex-1 truncate">{{ $t('docetra.meta.assign') }}</span>
          <UButton
            icon="i-lucide-plus"
            color="neutral"
            variant="ghost"
            size="xs"
            square
            :disabled="readOnly"
            @click="adding.assign = !adding.assign"
          />
        </div>

        <div v-if="adding.assign" class="mt-2 flex gap-1.5 ps-6">
          <UInput
            v-model="draft.assign"
            size="xs"
            class="min-w-0 flex-1"
            :placeholder="$t('docetra.meta.assignPlaceholder')"
            @keydown.enter.prevent="addAssignee"
          />
          <UButton size="xs" color="primary" :label="$t('actions.add')" @click="addAssignee" />
        </div>

        <ul class="mt-2 space-y-1.5 ps-6">
          <li
            v-for="person in assignees"
            :key="person.id"
            class="group flex items-center gap-2 text-sm text-highlighted"
          >
            <span class="grid size-6 shrink-0 place-items-center rounded-full bg-rose-100 text-[11px] font-medium text-rose-700 dark:bg-rose-500/20 dark:text-rose-300">
              {{ personInitial(person.name) }}
            </span>
            <span class="min-w-0 flex-1 truncate">{{ person.name }}</span>
            <UButton
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              size="xs"
              square
              class="opacity-0 transition-opacity group-hover:opacity-100"
              :disabled="readOnly"
              @click="removeAssignee(person.id)"
            />
          </li>
        </ul>
      </section>

      <!-- Attachments -->
      <section class="px-4 py-2.5">
        <div class="flex items-center gap-2 text-sm text-toned">
          <UIcon name="i-lucide-paperclip" class="size-4 shrink-0 text-muted" />
          <span class="min-w-0 flex-1 truncate">{{ $t('docetra.meta.attachments') }}</span>
          <UButton
            icon="i-lucide-plus"
            color="neutral"
            variant="ghost"
            size="xs"
            square
            :disabled="readOnly"
            @click="openAttachmentPicker"
          />
          <input
            ref="fileInput"
            type="file"
            multiple
            class="hidden"
            @change="onFilesSelected"
          >
        </div>

        <ul class="mt-2 space-y-1.5 ps-6">
          <li
            v-for="file in localAttachments"
            :key="file.id"
            class="group flex items-center gap-2 text-sm text-highlighted"
          >
            <span class="grid size-6 shrink-0 place-items-center rounded-md bg-elevated ring ring-default">
              <UIcon
                :name="fileTypeIcon(file).icon"
                class="size-3"
                :class="fileTypeIcon(file).class"
              />
            </span>
            <span class="min-w-0 flex-1 truncate">{{ file.name }}</span>
            <UButton
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              size="xs"
              square
              class="opacity-0 transition-opacity group-hover:opacity-100"
              :disabled="readOnly"
              @click="removeAttachment(file.id)"
            />
          </li>
        </ul>
      </section>

      <!-- Tags -->
      <section class="px-4 py-2.5">
        <div class="flex items-center gap-2 text-sm text-toned">
          <UIcon name="i-lucide-tag" class="size-4 shrink-0 text-muted" />
          <span class="min-w-0 flex-1 truncate">{{ $t('docetra.meta.tags') }}</span>
          <UButton
            icon="i-lucide-plus"
            color="neutral"
            variant="ghost"
            size="xs"
            square
            :disabled="readOnly"
            @click="adding.tags = !adding.tags"
          />
        </div>

        <div v-if="adding.tags" class="mt-2 flex gap-1.5 ps-6">
          <UInput
            v-model="draft.tag"
            size="xs"
            class="min-w-0 flex-1"
            :placeholder="$t('docetra.meta.tagPlaceholder')"
            @keydown.enter.prevent="addTag"
          />
          <UButton size="xs" color="primary" :label="$t('actions.add')" @click="addTag" />
        </div>

        <div class="mt-2 flex flex-wrap gap-1.5 ps-6">
          <span
            v-for="tag in localTags"
            :key="tag"
            class="inline-flex items-center gap-1 rounded-full bg-sky-50 px-2 py-0.5 text-xs text-sky-800 dark:bg-sky-500/15 dark:text-sky-200"
          >
            {{ tag }}
            <button
              type="button"
              class="grid size-3.5 place-items-center rounded-full text-sky-700/70 hover:bg-sky-100 hover:text-sky-900 disabled:opacity-40 dark:text-sky-300 dark:hover:bg-sky-500/20"
              :disabled="readOnly"
              :aria-label="$t('docetra.meta.removeTag', { tag })"
              @click="removeTag(tag)"
            >
              <UIcon name="i-lucide-x" class="size-2.5" />
            </button>
          </span>
        </div>
      </section>

      <!-- Share -->
      <section class="px-4 py-2.5">
        <div class="flex items-center gap-2 text-sm text-toned">
          <UIcon name="i-lucide-share-2" class="size-4 shrink-0 text-muted" />
          <span class="min-w-0 flex-1 truncate">{{ $t('docetra.meta.share') }}</span>
          <UButton
            icon="i-lucide-plus"
            color="neutral"
            variant="ghost"
            size="xs"
            square
            :disabled="readOnly"
            @click="adding.share = !adding.share"
          />
        </div>

        <div v-if="adding.share" class="mt-2 flex gap-1.5 ps-6">
          <UInput
            v-model="draft.share"
            size="xs"
            class="min-w-0 flex-1"
            :placeholder="$t('docetra.meta.sharePlaceholder')"
            @keydown.enter.prevent="addShare"
          />
          <UButton size="xs" color="primary" :label="$t('actions.add')" @click="addShare" />
        </div>

        <ul class="mt-2 space-y-1.5 ps-6">
          <li
            v-for="person in shares"
            :key="person.id"
            class="group flex items-center gap-2 text-sm text-highlighted"
          >
            <span class="grid size-6 shrink-0 place-items-center rounded-full bg-rose-100 text-[11px] font-medium text-rose-700 dark:bg-rose-500/20 dark:text-rose-300">
              {{ personInitial(person.name) }}
            </span>
            <span class="min-w-0 flex-1 truncate">{{ person.name }}</span>
            <UButton
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              size="xs"
              square
              class="opacity-0 transition-opacity group-hover:opacity-100"
              :disabled="readOnly"
              @click="removeShare(person.id)"
            />
          </li>
        </ul>
      </section>

      <!-- Audit (flows under lists, scrolls with content) -->
      <div class="mt-2 border-t border-default px-4 py-4">
        <div class="space-y-4 text-sm">
          <div>
            <p class="text-toned">
              {{ $t('docetra.meta.lastEditedBy') }}
              {{ $t('docetra.meta.you') }}
            </p>
            <p class="mt-0.5 text-xs text-muted">
              {{ updatedAt ? relativeTime(updatedAt) : '—' }}
            </p>
          </div>
          <div>
            <p class="text-toned">
              {{ $t('docetra.meta.createdBy') }}
              {{ owner?.name || $t('docetra.meta.you') }}
            </p>
            <p class="mt-0.5 text-xs text-muted">
              {{ createdAt ? relativeTime(createdAt) : '—' }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

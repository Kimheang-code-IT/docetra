<script setup lang="ts">
/**
 * Vocabulary (enum) admin: group list → value editor.
 * All data ops go through the vocabulary repository; optimistic-concurrency
 * `version` is sent on updates when the API provides one.
 */
import type { BadgeColor, EnumValueOption, VocabularyCatalog } from '~/types/docetra/vocabulary'
import { BADGE_COLORS } from '~/types/docetra/vocabulary'
import { useVocabularyRepository } from '~/repositories'
import { invalidateVocabularyCache } from '~/composables/config/useVocabulary'
import { VOCABULARY_GROUPS } from '~/config/vocabulary-fallbacks'
import { enumValueLabel, normalizeBadgeColor } from '~/utils/vocabulary'
import { useConfirm } from '~/composables/common/useConfirm'
import { usePageSeo } from '~/composables/usePageSeo'
import { useAppHeader } from '~/composables/layout/useAppHeader'

const { t, locale } = useI18n()
const toast = useToast()
const auth = useAuthStore()
const { confirm } = useConfirm()
const { setBreadcrumbs, clear } = useAppHeader()
const repository = useVocabularyRepository()

usePageSeo({
  title: () => t('docetra.pages.vocabularies'),
  description: () => t('docetra.descriptions.vocabulary'),
})

const canCreate = computed(() => auth.canAccessPage('configuration.enums.create'))
const canEdit = computed(() => auth.canAccessPage('configuration.enums.edit'))
const canDelete = computed(() => auth.canAccessPage('configuration.enums.delete'))

const loading = ref(false)
const savingKey = ref<string | null>(null)
const deletingCode = ref<string | null>(null)
const catalog = ref<VocabularyCatalog>({})
const selectedGroup = ref('')
const newDraft = ref(emptyDraft())
/** Local edit buffers keyed by `${group}:${code}` so switching groups is lossless. */
const edits = ref<Record<string, EnumValueDraft>>({})

interface EnumValueDraft {
  code: string
  labelEn: string
  labelKm: string
  color: BadgeColor
  order: number
  isActive: boolean
}

function emptyDraft(): EnumValueDraft {
  return { code: '', labelEn: '', labelKm: '', color: 'neutral', order: 0, isActive: true }
}

function draftKey(group: string, code: string) {
  return `${group}:${code}`
}

function draftFor(value: EnumValueOption): EnumValueDraft {
  return {
    code: value.code,
    labelEn: value.labelEn || '',
    labelKm: value.labelKm || '',
    color: normalizeBadgeColor(value.color) ?? 'neutral',
    order: typeof value.order === 'number' ? value.order : 0,
    isActive: value.isActive !== false,
  }
}

const groups = computed<string[]>(() => {
  const known = VOCABULARY_GROUPS.map(group => group.key as string)
  return [...new Set([...known, ...Object.keys(catalog.value)])]
})

function groupLabel(group: string): string {
  const meta = VOCABULARY_GROUPS.find(item => item.key === group)
  return meta ? t(meta.labelKey) : group
}

const rows = computed<EnumValueOption[]>(() =>
  [...(catalog.value[selectedGroup.value] || [])].sort((a, b) =>
    (a.order ?? Number.MAX_SAFE_INTEGER) - (b.order ?? Number.MAX_SAFE_INTEGER)),
)

function editedRow(value: EnumValueOption): EnumValueDraft & { dirty: boolean } {
  const key = draftKey(selectedGroup.value, value.code)
  const draft = edits.value[key] || draftFor(value)
  const pristine = draftFor(value)
  const dirty = JSON.stringify(draft) !== JSON.stringify(pristine)
  return { ...draft, dirty }
}

function onEdit(value: EnumValueOption, patch: Partial<Omit<EnumValueDraft, 'code'>>) {
  const key = draftKey(selectedGroup.value, value.code)
  const next = { ...(edits.value[key] || draftFor(value)), ...patch }
  delete (next as Partial<EnumValueDraft>).code
  edits.value[key] = next
}

async function load() {
  loading.value = true
  try {
    const response = await repository.getCatalog()
    catalog.value = response.data?.groups || {}
    if (!selectedGroup.value || !groups.value.includes(selectedGroup.value)) {
      selectedGroup.value = groups.value[0] || ''
    }
  }
  catch (error: unknown) {
    const message = error instanceof Error ? error.message : ''
    toast.add({ title: message || t('docetra.common.loadFailed'), color: 'error' })
  }
  finally {
    loading.value = false
  }
}

async function saveRow(value: EnumValueOption) {
  if (!canEdit.value || savingKey.value) return
  const key = draftKey(selectedGroup.value, value.code)
  const draft = edits.value[key] || draftFor(value)
  savingKey.value = key
  try {
    await repository.updateValue(selectedGroup.value, value.code, {
      ...(value.version != null ? { version: value.version } : {}),
      labelEn: draft.labelEn.trim(),
      labelKm: draft.labelKm.trim(),
      color: draft.color,
      order: Number(draft.order) || 0,
      isActive: draft.isActive,
    })
    delete edits.value[key]
    toast.add({ title: t('docetra.common.saved'), color: 'success' })
    await load()
    await invalidateVocabularyCache()
  }
  catch (error: unknown) {
    const message = error instanceof Error ? error.message : ''
    toast.add({ title: message || t('docetra.vocabulary.saveFailed'), color: 'error' })
  }
  finally {
    savingKey.value = null
  }
}

async function deleteRow(value: EnumValueOption) {
  if (!canDelete.value || deletingCode.value) return
  const ok = await confirm({ kind: 'delete', count: 1 })
  if (!ok) return
  deletingCode.value = value.code
  try {
    await repository.deleteValue(selectedGroup.value, value.code)
    toast.add({ title: t('docetra.vocabulary.deleted'), color: 'success' })
    await load()
    await invalidateVocabularyCache()
  }
  catch (error: unknown) {
    const message = error instanceof Error ? error.message : ''
    toast.add({ title: message || t('docetra.vocabulary.deleteFailed'), color: 'error' })
  }
  finally {
    deletingCode.value = null
  }
}

async function createValue() {
  if (!canCreate.value || savingKey.value) return
  const code = newDraft.value.code.trim()
  const labelEn = newDraft.value.labelEn.trim()
  if (!code || !labelEn) {
    toast.add({ title: t('docetra.vocabulary.codeLabelRequired'), color: 'error' })
    return
  }
  savingKey.value = '__new__'
  try {
    await repository.createValue(selectedGroup.value, {
      code,
      labelEn,
      labelKm: newDraft.value.labelKm.trim(),
      color: newDraft.value.color,
      order: Number(newDraft.value.order) || 0,
      isActive: newDraft.value.isActive,
    })
    newDraft.value = emptyDraft()
    toast.add({ title: t('docetra.common.created'), color: 'success' })
    await load()
    await invalidateVocabularyCache()
  }
  catch (error: unknown) {
    const message = error instanceof Error ? error.message : ''
    toast.add({ title: message || t('docetra.vocabulary.saveFailed'), color: 'error' })
  }
  finally {
    savingKey.value = null
  }
}

function previewLabel(value: EnumValueOption): string {
  const draft = editedRow(value)
  const km = locale.value.toLowerCase().startsWith('km')
  const primary = km ? draft.labelKm : draft.labelEn
  const secondary = km ? draft.labelEn : draft.labelKm
  return primary || secondary || enumValueLabel(value, locale.value)
}

watch(
  () => locale.value,
  () => setBreadcrumbs([{ label: t('docetra.pages.vocabularies') }]),
)

onMounted(async () => {
  setBreadcrumbs([{ label: t('docetra.pages.vocabularies') }])
  await load()
})
onBeforeUnmount(clear)
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden p-1.5">
    <div class="grid min-h-0 flex-1 grid-cols-1 gap-3 lg:grid-cols-12">
      <aside class="min-h-0 overflow-y-auto rounded-sm border border-default bg-default shadow-xs lg:col-span-3">
        <ul class="divide-y divide-default">
          <li v-for="group in groups" :key="group">
            <button
              type="button"
              class="flex w-full items-center justify-between gap-2 px-3 py-2.5 text-left text-sm transition"
              :class="selectedGroup === group
                ? 'bg-primary/5 font-medium text-highlighted ring-inset ring-1 ring-primary/20'
                : 'text-muted hover:bg-elevated/60 hover:text-highlighted'"
              @click="selectedGroup = group"
            >
              <span class="min-w-0 truncate">{{ groupLabel(group) }}</span>
              <span class="shrink-0 tabular-nums text-[11px] text-muted">
                {{ (catalog[group] || []).length }}
              </span>
            </button>
          </li>
        </ul>
      </aside>

      <section class="min-h-0 overflow-y-auto rounded-sm border border-default bg-default shadow-xs lg:col-span-9">
        <div class="flex items-center justify-between gap-2 border-b border-default px-3 py-2.5">
          <h2 class="text-sm font-semibold text-highlighted">
            {{ groupLabel(selectedGroup) }}
          </h2>
        </div>

        <div class="divide-y divide-default">
          <p v-if="!rows.length && !loading" class="px-3 py-6 text-center text-sm text-muted">
            {{ $t('docetra.vocabulary.emptyGroup') }}
          </p>

          <div
            v-for="value in rows"
            :key="value.code"
            class="flex flex-wrap items-end gap-2 px-3 py-3"
          >
            <div class="w-32 shrink-0">
              <p class="mb-1 text-[10px] uppercase tracking-wide text-muted">
                {{ $t('docetra.vocabulary.code') }}
              </p>
              <span class="block truncate rounded-md bg-elevated/60 px-2 py-1.5 font-mono text-xs text-highlighted">
                {{ value.code }}
              </span>
            </div>

            <div class="min-w-36 flex-1">
              <p class="mb-1 text-[10px] uppercase tracking-wide text-muted">
                {{ $t('docetra.vocabulary.labelEn') }}
              </p>
              <UInput
                :model-value="editedRow(value).labelEn"
                :disabled="!canEdit || savingKey === draftKey(selectedGroup, value.code)"
                size="sm"
                @update:model-value="v => onEdit(value, { labelEn: String(v) })"
              />
            </div>

            <div class="min-w-36 flex-1">
              <p class="mb-1 text-[10px] uppercase tracking-wide text-muted">
                {{ $t('docetra.vocabulary.labelKm') }}
              </p>
              <UInput
                :model-value="editedRow(value).labelKm"
                :disabled="!canEdit || savingKey === draftKey(selectedGroup, value.code)"
                size="sm"
                @update:model-value="v => onEdit(value, { labelKm: String(v) })"
              />
            </div>

            <div class="w-28 shrink-0">
              <p class="mb-1 text-[10px] uppercase tracking-wide text-muted">
                {{ $t('docetra.vocabulary.color') }}
              </p>
              <USelect
                :model-value="normalizeBadgeColor(editedRow(value).color) ?? 'neutral'"
                :items="BADGE_COLORS.map(color => ({ label: color, value: color }))"
                :disabled="!canEdit"
                size="sm"
                @update:model-value="v => onEdit(value, { color: normalizeBadgeColor(v) ?? 'neutral' })"
              />
            </div>

            <div class="w-20 shrink-0">
              <p class="mb-1 text-[10px] uppercase tracking-wide text-muted">
                {{ $t('docetra.vocabulary.order') }}
              </p>
              <UInput
                :model-value="String(editedRow(value).order)"
                type="number"
                :disabled="!canEdit"
                size="sm"
                @update:model-value="v => onEdit(value, { order: Number(v) || 0 })"
              />
            </div>

            <div class="shrink-0 pb-1">
              <USwitch
                :model-value="editedRow(value).isActive"
                :disabled="!canEdit"
                size="sm"
                @update:model-value="v => onEdit(value, { isActive: Boolean(v) })"
              />
            </div>

            <UBadge
              class="shrink-0 pb-1"
              :color="normalizeBadgeColor(editedRow(value).color) || 'neutral'"
              variant="subtle"
            >
              {{ previewLabel(value) }}
            </UBadge>

            <div class="ml-auto flex shrink-0 gap-1 pb-0.5">
              <UButton
                size="xs"
                color="primary"
                variant="soft"
                icon="i-lucide-save"
                :disabled="!canEdit || !editedRow(value).dirty"
                :loading="savingKey === draftKey(selectedGroup, value.code)"
                :label="$t('docetra.common.save')"
                @click="saveRow(value)"
              />
              <UButton
                size="xs"
                color="error"
                variant="ghost"
                icon="i-lucide-trash-2"
                :disabled="!canDelete"
                :loading="deletingCode === value.code"
                :aria-label="$t('docetra.rowActions.delete')"
                @click="deleteRow(value)"
              />
            </div>
          </div>
        </div>

        <div v-if="canCreate" class="border-t border-default px-3 py-3">
          <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
            {{ $t('docetra.vocabulary.addValue') }}
          </p>
          <div class="flex flex-wrap items-end gap-2">
            <div class="w-40">
              <p class="mb-1 text-[10px] uppercase tracking-wide text-muted">{{ $t('docetra.vocabulary.code') }}</p>
              <UInput v-model="newDraft.code" size="sm" />
            </div>
            <div class="min-w-36 flex-1">
              <p class="mb-1 text-[10px] uppercase tracking-wide text-muted">{{ $t('docetra.vocabulary.labelEn') }}</p>
              <UInput v-model="newDraft.labelEn" size="sm" />
            </div>
            <div class="min-w-36 flex-1">
              <p class="mb-1 text-[10px] uppercase tracking-wide text-muted">{{ $t('docetra.vocabulary.labelKm') }}</p>
              <UInput v-model="newDraft.labelKm" size="sm" />
            </div>
            <div class="w-28">
              <p class="mb-1 text-[10px] uppercase tracking-wide text-muted">{{ $t('docetra.vocabulary.color') }}</p>
              <USelect
                :model-value="newDraft.color"
                :items="BADGE_COLORS.map(color => ({ label: color, value: color }))"
                size="sm"
                @update:model-value="v => (newDraft.color = normalizeBadgeColor(v) ?? 'neutral')"
              />            </div>
            <div class="w-20">
              <p class="mb-1 text-[10px] uppercase tracking-wide text-muted">{{ $t('docetra.vocabulary.order') }}</p>
              <UInput
                :model-value="String(newDraft.order)"
                type="number"
                size="sm"
                @update:model-value="v => (newDraft.order = Number(v) || 0)"
              />
            </div>
            <UButton
              size="sm"
              color="primary"
              variant="soft"
              icon="i-lucide-plus"
              :label="$t('docetra.common.create')"
              :loading="savingKey === '__new__'"
              @click="createValue"
            />
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

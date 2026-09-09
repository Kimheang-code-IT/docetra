<script setup lang="ts">
import type { DocumentFieldSchema, FieldOption } from '~/types/docetra/common'
import { FORM_CONTROL, FORM_NUMBER_BUTTONS } from '~/utils/form-field-ui'
import { resolveFieldPlaceholder } from '~/utils/field-help'
import { useReferenceOptions } from '~/composables/common/useReferenceOptions'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { ensureSelectItemsHaveLabel, fieldOptionsToSelectItems } from '~/utils/select-display'

const props = defineProps<{
  field: DocumentFieldSchema
  modelValue: unknown
  disabled?: boolean
  /** Human label for the current FK value (e.g. roleName for roleId). */
  selectedLabel?: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [unknown]
  'update:selectedLabel': [string]
  blur: []
}>()

const { t, te } = useI18n()
const route = useRoute()
const { loadReferenceOptions } = useReferenceOptions()

const stringValue = computed({
  get: () => String(props.modelValue ?? ''),
  set: (v: string) => emit('update:modelValue', v),
})

const selectValue = computed({
  get: () => {
    if (props.modelValue == null || props.modelValue === '') return undefined
    return String(props.modelValue)
  },
  set: (v: string | undefined) => {
    const next = v ?? ''
    emit('update:modelValue', next)
    const match = selectItems.value.find(item => String(item.value) === next)
    if (match?.label) emit('update:selectedLabel', match.label)
  },
})

const numberValue = computed({
  get: () => (typeof props.modelValue === 'number' ? props.modelValue : Number(props.modelValue || 0)),
  set: (v: number | null) => emit('update:modelValue', v ?? 0),
})

const multiValue = computed({
  get: () => (Array.isArray(props.modelValue)
    ? props.modelValue.map(String).filter(Boolean)
    : (props.modelValue ? [String(props.modelValue)] : [])),
  set: (v: string | string[]) => emit('update:modelValue', v),
})

const csvValue = computed({
  get: () => Array.isArray(props.modelValue)
    ? (props.modelValue as unknown[]).map(String).join(', ')
    : String(props.modelValue ?? ''),
  set: (v: string) => {
    emit(
      'update:modelValue',
      String(v || '')
        .split(',')
        .map(s => s.trim())
        .filter(Boolean),
    )
  },
})

const imageValue = computed({
  get: () => (props.modelValue == null || props.modelValue === ''
    ? undefined
    : String(props.modelValue)),
  set: (v: string | undefined) => emit('update:modelValue', v),
})

const colorValue = computed({
  get: () => String(props.modelValue || '#2563eb'),
  set: (v: string) => emit('update:modelValue', v),
})

const remoteOptions = ref<FieldOption[]>([])
const optionsPending = ref(false)

const resolvedOptionsEndpoint = computed(() => {
  const endpoint = props.field.optionsEndpoint
  if (!endpoint) return undefined
  if (props.field.key !== 'parentId' || !endpoint.startsWith(`${ApiEndpoints.DEPARTMENTS}/options`)) {
    return endpoint
  }
  const currentId = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id
  if (!currentId || currentId === 'new') return endpoint
  const separator = endpoint.includes('?') ? '&' : '?'
  return `${endpoint}${separator}excludeId=${encodeURIComponent(String(currentId))}`
})

watch(resolvedOptionsEndpoint, async (endpoint) => {
  remoteOptions.value = []
  if (!endpoint) return
  optionsPending.value = true
  try {
    const endpoints = endpoint.split('|').map(part => part.trim()).filter(Boolean)
    const batches = await Promise.all(endpoints.map(item => loadReferenceOptions(item)))
    const seen = new Set<string>()
    remoteOptions.value = batches.flat().filter((option) => {
      const key = String(option.value)
      if (!key || seen.has(key)) return false
      seen.add(key)
      return true
    })
  }
  catch {
    remoteOptions.value = []
  }
  finally {
    optionsPending.value = false
  }
}, { immediate: true })

const searchRemoteOptions = useDebounceFn(async (search: string) => {
  const endpoint = resolvedOptionsEndpoint.value
  if (!endpoint) return
  optionsPending.value = true
  try {
    const endpoints = endpoint.split('|').map(part => part.trim()).filter(Boolean)
    const batches = await Promise.all(endpoints.map(item => loadReferenceOptions(item, search)))
    const seen = new Set<string>()
    remoteOptions.value = batches.flat().filter((option) => {
      const key = String(option.value)
      if (!key || seen.has(key)) return false
      seen.add(key)
      return true
    })
  }
  finally { optionsPending.value = false }
}, 250)

const selectItems = computed(() => ensureSelectItemsHaveLabel(
  fieldOptionsToSelectItems([...(props.field.options || []), ...remoteOptions.value], t),
  props.modelValue,
  props.selectedLabel,
))

const labelText = computed(() => {
  if (props.field.label) return props.field.label
  if (props.field.labelKey && te(props.field.labelKey)) return t(props.field.labelKey)
  return props.field.labelKey || ''
})

const placeholderText = computed(() =>
  resolveFieldPlaceholder(props.field, labelText.value, t, te),
)

const TEXTAREA_MIN_ROWS = 3
const TEXTAREA_MAX_ROWS = 7
const textareaRows = computed(() => {
  const requested = props.field.rows ?? TEXTAREA_MIN_ROWS
  return Math.min(TEXTAREA_MAX_ROWS, Math.max(TEXTAREA_MIN_ROWS, requested))
})

const isRemoteSelect = computed(() =>
  Boolean(props.field.optionsEndpoint)
  && (
    props.field.type === 'select'
    || props.field.type === 'organization'
    || props.field.type === 'officer'
    || props.field.type === 'relation'
  ),
)

const isStaticSelect = computed(() =>
  props.field.type === 'select'
  && !props.field.optionsEndpoint,
)

const fieldRequired = computed(() => Boolean(props.field.required))
</script>

<template>
  <UTextarea
    v-if="field.type === 'textarea'"
    v-model="stringValue"
    :disabled="disabled || field.readOnly"
    :placeholder="placeholderText"
    :rows="textareaRows"
    :maxrows="TEXTAREA_MAX_ROWS"
    autoresize
    :color="FORM_CONTROL.color"
    :variant="FORM_CONTROL.variant"
    :size="FORM_CONTROL.size"
    class="w-full"
    :class="field.key === 'telegram.messageTemplate' ? 'font-mono text-sm' : ''"
    @blur="emit('blur')"
  />
  <UInputNumber
    v-else-if="field.type === 'number'"
    v-model="numberValue"
    :disabled="disabled || field.readOnly"
    :placeholder="placeholderText"
    class="w-full"
    :color="FORM_CONTROL.color"
    :variant="FORM_CONTROL.variant"
    :size="FORM_CONTROL.size"
    :increment="FORM_NUMBER_BUTTONS"
    :decrement="FORM_NUMBER_BUTTONS"
  />
  <CommonAppInputDate
    v-else-if="field.type === 'date'"
    v-model="stringValue"
    :disabled="disabled || field.readOnly"
    :required="fieldRequired"
    :placeholder="placeholderText"
    :color="FORM_CONTROL.color"
    :variant="FORM_CONTROL.variant"
    :size="FORM_CONTROL.size"
    class="w-full"
  />
  <CommonAppInputDate
    v-else-if="field.type === 'datetime'"
    v-model="stringValue"
    granularity="minute"
    :disabled="disabled || field.readOnly"
    :required="fieldRequired"
    :placeholder="placeholderText"
    :color="FORM_CONTROL.color"
    :variant="FORM_CONTROL.variant"
    :size="FORM_CONTROL.size"
    class="w-full"
  />
  <USelectMenu
    v-else-if="isRemoteSelect"
    v-model="selectValue"
    :items="selectItems"
    value-key="value"
    label-key="label"
    :placeholder="placeholderText"
    :disabled="disabled || field.readOnly"
    :loading="optionsPending"
    class="w-full"
    :color="FORM_CONTROL.color"
    :variant="FORM_CONTROL.variant"
    :size="FORM_CONTROL.size"
    @update:search-term="searchRemoteOptions"
  />
  <USelect
    v-else-if="isStaticSelect"
    v-model="selectValue"
    :items="selectItems"
    value-key="value"
    label-key="label"
    :placeholder="placeholderText"
    :disabled="disabled || field.readOnly"
    :loading="optionsPending"
    class="w-full"
    :color="FORM_CONTROL.color"
    :variant="FORM_CONTROL.variant"
    :size="FORM_CONTROL.size"
  />
  <CommonAppMentionMultiInput
    v-else-if="field.type === 'multiselect'"
    v-model="multiValue"
    :items="selectItems"
    :placeholder="placeholderText"
    :disabled="disabled || field.readOnly"
    :loading="optionsPending"
    @search="searchRemoteOptions"
  />
  <CommonAppSecretInput
    v-else-if="field.type === 'secret'"
    v-model="stringValue"
    embedded
    :placeholder="placeholderText"
    :disabled="disabled || field.readOnly"
    :required="fieldRequired"
  />
  <CommonAppColorPicker
    v-else-if="field.type === 'color'"
    v-model="colorValue"
    embedded
    :placeholder="placeholderText"
    :disabled="disabled || field.readOnly"
  />
  <CommonAppImageUploadField
    v-else-if="field.type === 'image'"
    v-model="imageValue"
    embedded
    :disabled="disabled || field.readOnly"
  />
  <CommonAppIconPicker
    v-else-if="field.type === 'icon'"
    v-model="stringValue"
    embedded
    :disabled="disabled || field.readOnly"
  />
  <UInput
    v-else-if="field.type === 'csv-list'"
    v-model="csvValue"
    :placeholder="placeholderText"
    :disabled="disabled || field.readOnly"
    class="w-full"
    :color="FORM_CONTROL.color"
    :variant="FORM_CONTROL.variant"
    :size="FORM_CONTROL.size"
    @blur="emit('blur')"
  />
  <UInput
    v-else
    v-model="stringValue"
    :type="field.type === 'url' ? 'url' : 'text'"
    :placeholder="placeholderText"
    :disabled="disabled || field.readOnly"
    class="w-full"
    :color="FORM_CONTROL.color"
    :variant="FORM_CONTROL.variant"
    :size="FORM_CONTROL.size"
    @blur="emit('blur')"
  />
</template>

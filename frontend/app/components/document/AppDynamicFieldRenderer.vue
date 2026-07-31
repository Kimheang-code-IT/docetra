<script setup lang="ts">
import type { DocumentFieldSchema } from '~/types/docetra/common'

const props = defineProps<{
  field: DocumentFieldSchema
  modelValue: unknown
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [unknown]
}>()

const { t, te } = useI18n()

const hintOpen = ref(false)

const inputUi = {
  base: 'bg-elevated/70 ring-0 rounded-md focus-visible:ring-2 focus-visible:ring-primary/25',
}

const stringValue = computed({
  get: () => String(props.modelValue ?? ''),
  set: (v: string) => emit('update:modelValue', v),
})

const selectValue = computed({
  get: () => {
    if (props.modelValue == null || props.modelValue === '') return undefined
    return String(props.modelValue)
  },
  set: (v: string | undefined) => emit('update:modelValue', v ?? ''),
})

const numberValue = computed({
  get: () => (typeof props.modelValue === 'number' ? props.modelValue : Number(props.modelValue || 0)),
  set: (v: number | null) => emit('update:modelValue', v ?? 0),
})

const boolValue = computed({
  get: () => Boolean(props.modelValue),
  set: (v: boolean | 'indeterminate') => emit('update:modelValue', v === true),
})

const multiValue = computed({
  get: () => (Array.isArray(props.modelValue)
    ? props.modelValue.map(String).filter(Boolean)
    : (props.modelValue ? [String(props.modelValue)] : [])),
  set: (v: string | string[]) => emit('update:modelValue', v),
})

const permissionRows = computed({
  get: () => (Array.isArray(props.modelValue) ? props.modelValue as any[] : []),
  set: (v: any[]) => emit('update:modelValue', v),
})

const selectItems = computed(() =>
  (props.field.options || [])
    .filter(o => o.value !== '')
    .map(o => ({
      label: t(o.labelKey || o.label),
      value: o.value,
    })),
)

const labelText = computed(() => t(props.field.labelKey))

const helpText = computed(() => {
  if (!props.field.helpKey || !te(props.field.helpKey)) return ''
  return t(props.field.helpKey)
})

const hintText = computed(() => {
  const key = props.field.hintKey || props.field.helpKey
  if (!key || !te(key)) return ''
  return t(key)
})

const placeholderText = computed(() => {
  if (props.field.placeholderKey && te(props.field.placeholderKey)) {
    return t(props.field.placeholderKey)
  }
  return labelText.value
})

const isBoolean = computed(() => props.field.type === 'boolean')
const isPermissionMatrix = computed(() => props.field.type === 'permission-matrix')

function toggleHint() {
  hintOpen.value = !hintOpen.value
}

function closeHint() {
  hintOpen.value = false
}

watch(() => props.field.key, () => {
  hintOpen.value = false
})
</script>

<template>
  <CommonAppRolePermissionMatrix
    v-if="isPermissionMatrix"
    v-model="permissionRows"
    :disabled="disabled || field.readOnly"
  />

  <!-- Checkbox: label beside control + optional info hint -->
  <div v-else-if="isBoolean" class="flex min-h-9 flex-wrap items-center gap-2 pt-1">
    <UCheckbox
      v-model="boolValue"
      color="neutral"
      :disabled="disabled || field.readOnly"
      :required="field.required"
      :ui="{ label: 'text-sm text-highlighted' }"
    >
      <template #label>
        <span class="inline-flex items-center gap-1.5">
          <span>{{ labelText }}</span>
          <UButton
            v-if="hintText"
            icon="i-lucide-info"
            color="neutral"
            variant="ghost"
            size="xs"
            square
            class="text-muted"
            :aria-label="hintText"
            @click.prevent.stop="toggleHint"
          />
        </span>
      </template>
    </UCheckbox>

    <div
      v-if="hintText && hintOpen"
      class="inline-flex max-w-md items-start gap-2 rounded-md border border-default bg-elevated px-2.5 py-1.5 text-xs text-toned"
    >
      <p class="min-w-0 flex-1 leading-relaxed">{{ hintText }}</p>
      <UButton
        icon="i-lucide-x"
        color="neutral"
        variant="soft"
        size="xs"
        square
        class="shrink-0"
        @click="closeHint"
      />
    </div>
  </div>

  <!-- Standard fields: label + control + help below -->
  <UFormField
    v-else
    :label="labelText"
    :required="field.required"
    :help="helpText || undefined"
    :ui="{
      label: 'text-sm font-medium text-toned',
      help: 'text-xs text-muted leading-relaxed mt-1.5',
    }"
  >
    <div class="flex items-start gap-1.5">
      <div class="min-w-0 flex-1">
        <UTextarea
          v-if="field.type === 'textarea'"
          v-model="stringValue"
          :disabled="disabled || field.readOnly"
          :placeholder="placeholderText"
          :rows="4"
          class="w-full"
          :ui="inputUi"
        />
        <UInputNumber
          v-else-if="field.type === 'number'"
          v-model="numberValue"
          :disabled="disabled || field.readOnly"
          class="w-full"
          :ui="inputUi"
        />
        <CommonAppInputDate
          v-else-if="field.type === 'date'"
          v-model="stringValue"
          :disabled="disabled || field.readOnly"
          :required="field.required"
          class="w-full"
        />
        <CommonAppInputDate
          v-else-if="field.type === 'datetime'"
          v-model="stringValue"
          granularity="minute"
          :disabled="disabled || field.readOnly"
          :required="field.required"
          class="w-full"
        />
        <USelect
          v-else-if="field.type === 'select'"
          v-model="selectValue"
          :items="selectItems"
          value-key="value"
          :placeholder="placeholderText"
          :disabled="disabled || field.readOnly"
          class="w-full"
          :ui="inputUi"
        />
        <USelect
          v-else-if="field.type === 'multiselect'"
          v-model="multiValue"
          :items="selectItems"
          value-key="value"
          multiple
          :placeholder="placeholderText"
          :disabled="disabled || field.readOnly"
          class="w-full"
          :ui="inputUi"
        />
        <UInput
          v-else
          v-model="stringValue"
          :type="field.type === 'url' ? 'url' : 'text'"
          :placeholder="placeholderText"
          :disabled="disabled || field.readOnly"
          class="w-full"
          :ui="inputUi"
        />
      </div>

      <UButton
        v-if="field.hintKey && hintText"
        icon="i-lucide-info"
        color="neutral"
        variant="ghost"
        size="xs"
        square
        class="mt-1.5 shrink-0 text-muted"
        @click="toggleHint"
      />
    </div>

    <div
      v-if="field.hintKey && hintText && hintOpen"
      class="mt-2 flex items-start gap-2 rounded-md border border-default bg-elevated px-2.5 py-1.5 text-xs text-toned"
    >
      <p class="min-w-0 flex-1 leading-relaxed">{{ hintText }}</p>
      <UButton
        icon="i-lucide-x"
        color="neutral"
        variant="soft"
        size="xs"
        square
        class="shrink-0"
        @click="closeHint"
      />
    </div>
  </UFormField>
</template>

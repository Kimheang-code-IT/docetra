<script setup lang="ts">
/**
 * Reusable workspace/report filter control.
 * Single or multiple selection via Nuxt UI SelectMenu (searchable).
 */
import type { FilterDef } from '~/types/docetra/common'

const props = withDefaults(
  defineProps<{
    filter: FilterDef
    /** Single-select: string | null. Multi-select: string[] | null. */
    modelValue?: string | string[] | null
    searchable?: boolean
  }>(),
  {
    modelValue: null,
    searchable: true,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string | string[] | null]
}>()

const { t } = useI18n()

const isMultiple = computed(() => props.filter.type === 'multiselect')

const label = computed(() => t(props.filter.labelKey))

const items = computed(() =>
  (props.filter.options || [])
    .filter(o => o.value !== '')
    .map(o => ({
      label: t(o.labelKey || o.label),
      value: o.value,
    })),
)

const singleValue = computed({
  get: () => {
    const value = props.modelValue
    if (Array.isArray(value)) return value[0]
    return value ?? undefined
  },
  set: (value: string | number | boolean | undefined) => {
    emit('update:modelValue', value == null ? null : String(value))
  },
})

const multiValue = computed({
  get: () => {
    const value = props.modelValue
    if (value == null || value === '') return null
    if (Array.isArray(value)) return value.length ? value : null
    return [value]
  },
  set: (value: string[] | null) => emit('update:modelValue', value),
})
</script>

<template>
  <CommonAppMutilSelect
    v-if="isMultiple"
    v-model="multiValue"
    :items="items"
    :label="label"
    :placeholder="label"
    :searchable="searchable"
  />
  <CommonAppSingleFilterSelect
    v-else
    v-model="singleValue"
    :items="items"
    :label="label"
    :placeholder="label"
    :searchable="searchable"
  />
</template>

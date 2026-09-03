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

const items = computed(() => {
  return (props.filter.options || [])
    .filter(o => o.value !== '')
    .map(o => ({
      label: t(o.labelKey || o.label),
      value: o.value,
    }))
})

const selectValue = computed<string | string[] | undefined | null>({
  get: () => {
    const value = props.modelValue
    if (!isMultiple.value) {
      if (Array.isArray(value)) return value[0]
      return value ?? undefined
    }
    if (value == null || value === '') return null
    if (Array.isArray(value)) return value.length ? value : null
    return [value]
  },
  set: (value) => {
    if (!isMultiple.value) {
      emit('update:modelValue', value == null || value === '' ? null : String(value))
      return
    }
    emit('update:modelValue', Array.isArray(value) && value.length ? value : null)
  },
})
</script>

<template>
  <CommonAppSingleFilterSelect
    v-model="selectValue"
    :multiple="isMultiple"
    :items="items"
    :label="label"
    :placeholder="label"
    :searchable="searchable"
  />
</template>

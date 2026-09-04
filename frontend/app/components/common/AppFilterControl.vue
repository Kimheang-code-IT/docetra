<script setup lang="ts">
import type { FilterDef } from '~/types/docetra/common'

const props = withDefaults(defineProps<{
  filter: FilterDef
  modelValue?: string | string[] | null
  start?: string
  end?: string
  searchable?: boolean
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  inline?: boolean
  disabled?: boolean
  class?: string
}>(), {
  modelValue: null,
  start: '',
  end: '',
  searchable: true,
  size: 'md',
  inline: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | string[] | null]
  'update:start': [value: string]
  'update:end': [value: string]
}>()

const { t } = useI18n()
const isDateRange = computed(() => props.filter.type === 'daterange' || props.filter.type === 'date')
</script>

<template>
  <CommonAppDateRangeFilter
    v-if="isDateRange"
    :start="start"
    :end="end"
    :label="t(filter.labelKey)"
    :size="size"
    :inline="inline"
    :disabled="disabled"
    :class="props.class"
    @update:start="emit('update:start', $event)"
    @update:end="emit('update:end', $event)"
  />
  <CommonAppFilterSelect
    v-else
    :filter="filter"
    :model-value="modelValue"
    :searchable="searchable"
    :class="props.class"
    @update:model-value="emit('update:modelValue', $event)"
  />
</template>

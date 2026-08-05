<script setup lang="ts">
/**
 * Debounced-friendly live search input with grey default border when non-empty.
 */
import { getFilterSearchUi, isFilterValueActive } from '~/utils/filter/select-ui'

const modelValue = defineModel<string>({ default: '' })

withDefaults(
  defineProps<{
    placeholder?: string
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  }>(),
  {
    size: 'sm',
  },
)

const ui = computed(() => getFilterSearchUi(isFilterValueActive(modelValue.value)))
</script>

<template>
  <UInput
    v-model="modelValue"
    icon="i-lucide-search"
    :placeholder="placeholder"
    :size="size"
    color="neutral"
    :ui="ui"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { normalizeToMenuRows } from '~/utils/filter/menu-items'

const modelValue = defineModel<string | number | boolean | null>({ default: null })

const props = withDefaults(
  defineProps<{
    items: unknown[]
    label?: string
    placeholder?: string
    searchable?: boolean
    icon?: string
  }>(),
  {
    searchable: true,
    icon: 'i-lucide-funnel',
  },
)

const { t } = useI18n()

const menuItems = computed(() => normalizeToMenuRows(props.items ?? []))

const selectPlaceholder = computed(
  () => props.placeholder ?? props.label ?? t('components.select'),
)

const displayLabel = computed(() => {
  const value = modelValue.value
  if (value == null || value === '') return undefined
  const match = menuItems.value.find(item => item.value === value)
  return match?.label
})

const { widthStyle, rootClass } = useFilterAutoWidth(
  () => props.label,
  () => selectPlaceholder.value,
  () => displayLabel.value,
)

const searchInput = computed(() => {
  if (!props.searchable) return false
  return {
    placeholder: t('components.filterSearch'),
    icon: 'i-lucide-search',
  }
})
</script>

<template>
  <div :class="rootClass" :style="widthStyle">
    <USelectMenu
      v-model="modelValue"
      :items="menuItems"
      :placeholder="selectPlaceholder"
      value-key="value"
      :icon="icon"
      class="w-full font-normal"
      size="md"
      :search-input="searchInput"
      :filter-fields="['label']"
      :ui="{
        base: 'rounded-md bg-default ring-1 ring-default',
        value: 'truncate',
        trailingIcon: 'text-muted',
        content: 'max-h-60 min-w-(--reka-combobox-trigger-width)',
      }"
      v-bind="$attrs"
    />
  </div>
</template>

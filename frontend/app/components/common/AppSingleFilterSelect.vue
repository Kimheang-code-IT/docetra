<script setup lang="ts">
import { computed } from 'vue'
import { normalizeToMenuRows } from '~/utils/filter/menu-items'

const modelValue = defineModel<unknown>({ required: true })

const props = withDefaults(
  defineProps<{
    items: unknown[]
    label?: string
    placeholder?: string
    searchable?: boolean
  }>(),
  {
    searchable: true,
  },
)

const { t } = useI18n()

const { widthStyle, rootClass } = useFilterAutoWidth(
  () => props.label,
  () => props.placeholder,
)

const menuItems = computed(() => normalizeToMenuRows(props.items ?? []))

const selectPlaceholder = computed(() => props.placeholder ?? t('components.select'))

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
      icon="i-lucide-filter"
      class="w-full font-normal"
      size="md"
      :search-input="searchInput"
      :filter-fields="['label']"
      :ui="{ content: 'max-h-60 min-w-(--reka-combobox-trigger-width)' }"
      v-bind="$attrs"
    />
  </div>
</template>

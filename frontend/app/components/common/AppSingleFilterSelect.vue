<script setup lang="ts">
import { computed } from 'vue'
import { normalizeToMenuRows } from '~/utils/filter/menu-items'
import { getFilterSelectUi, getFilterSearchInputConfig, isFilterValueActive } from '~/utils/filter/select-ui'

const modelValue = defineModel<string | number | boolean | undefined>({ default: undefined })

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
  if (!match?.label) return undefined
  return props.label ? `${props.label}: ${match.label}` : match.label
})

const { widthStyle, rootClass } = useFilterAutoWidth(
  () => props.label,
  () => selectPlaceholder.value,
  () => displayLabel.value,
)

const open = ref(false)

const isActive = computed(() => open.value || isFilterValueActive(modelValue.value))

const selectUi = computed(() => getFilterSelectUi(isActive.value))

const searchInput = computed(() => {
  if (!props.searchable) return false
  return getFilterSearchInputConfig(t)
})
</script>

<template>
  <div :class="rootClass" :style="widthStyle">
    <USelectMenu
      v-model="modelValue"
      v-model:open="open"
      :items="menuItems"
      :placeholder="selectPlaceholder"
      value-key="value"
      :icon="icon"
      class="w-full"
      size="sm"
      color="neutral"
      :search-input="searchInput"
      :filter-fields="['label']"
      :ui="selectUi"
      v-bind="$attrs"
    />
  </div>
</template>

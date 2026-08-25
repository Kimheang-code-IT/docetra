<script setup lang="ts">
import { computed } from 'vue'
import { normalizeToMenuRows } from '~/utils/filter/menu-items'
import { getFilterSelectUi, getFilterSearchInputConfig, isFilterValueActive } from '~/utils/filter/select-ui'

/** Sentinel value for "no filter" — only used with showNoneOption in multiple mode. */
const FILTER_NONE = '__app_filter_select_none__'

type FilterValue = string | number | boolean
type FilterModel = FilterValue | undefined | FilterValue[] | null

const modelValue = defineModel<FilterModel>({ default: undefined })

const props = withDefaults(
  defineProps<{
    items: unknown[]
    label?: string
    placeholder?: string
    searchable?: boolean
    icon?: string
    /** Multi-selection mode; model becomes an array (null = no filter). */
    multiple?: boolean
    /** Multiple mode only: first option clears selection → model null. */
    showNoneOption?: boolean
    noneLabel?: string
  }>(),
  {
    searchable: true,
    multiple: false,
    showNoneOption: false,
  },
)

const { t } = useI18n()

const menuItems = computed(() => {
  const rows = normalizeToMenuRows(props.items ?? [])
  if (!props.multiple || !props.showNoneOption) return rows
  return [{ label: props.noneLabel ?? t('components.filterNone'), value: FILTER_NONE }, ...rows]
})

const selectPlaceholder = computed(
  () => props.placeholder ?? props.label ?? t('components.select'),
)

const displayLabel = computed(() => {
  const value = modelValue.value
  if (props.multiple) {
    const selected = Array.isArray(value) ? value : []
    const labels = selected
      .map(item => menuItems.value.find(row => row.value === item)?.label)
      .filter(Boolean) as string[]
    if (!labels.length) return undefined
    const joined = labels.join(', ')
    return props.label ? `${props.label}: ${joined}` : joined
  }
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

type SelectMenuModel = FilterValue | FilterValue[] | undefined

const internalValue = computed<SelectMenuModel>({
  get: () => {
    if (!props.multiple) {
      const value = modelValue.value
      return value == null || typeof value === 'object' ? undefined : value as FilterValue
    }
    if (modelValue.value == null || modelValue.value === '') {
      return props.showNoneOption ? [FILTER_NONE] : []
    }
    return Array.isArray(modelValue.value) ? modelValue.value : []
  },
  set: (value) => {
    if (!props.multiple) {
      modelValue.value = value as FilterValue | undefined
      return
    }
    const raw = Array.isArray(value) ? value : []
    const rest = raw.filter(v => v !== FILTER_NONE)
    if (props.showNoneOption && raw.includes(FILTER_NONE)) {
      modelValue.value = rest.length ? rest : null
      return
    }
    modelValue.value = rest.length ? rest : null
  },
})
</script>

<template>
  <div :class="rootClass" :style="widthStyle">
    <USelectMenu
      v-model="internalValue"
      v-model:open="open"
      :multiple="multiple"
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

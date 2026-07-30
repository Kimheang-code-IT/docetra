<script setup lang="ts">
import { computed } from 'vue'
import { normalizeToMenuRows } from '~/utils/filter/menu-items'

/** Sentinel value for “no filter” — only used when showNoneOption is enabled */
const MULTISELECT_FILTER_NONE = '__app_multiselect_none__'

const modelValue = defineModel<any[] | null>({ default: null })

const props = withDefaults(
  defineProps<{
    items: any[]
    /** Used as fallback placeholder text for the filter. */
    label?: string
    placeholder?: string
    /** First option: clears selection → model `null` (no filter) */
    showNoneOption?: boolean
    noneLabel?: string
    /** Show search box inside the dropdown */
    searchable?: boolean
  }>(),
  {
    showNoneOption: false,
    searchable: true,
  },
)

const { t } = useI18n()

const { widthStyle, rootClass } = useFilterAutoWidth(
  () => props.label,
  () => props.placeholder,
)

const menuItems = computed(() => {
  const rows = normalizeToMenuRows(props.items ?? [])
  if (!props.showNoneOption) {
    return rows
  }
  const noneRow = {
    label: props.noneLabel ?? t('components.filterNone'),
    value: MULTISELECT_FILTER_NONE,
  }
  return [noneRow, ...rows]
})

const selectPlaceholder = computed(() => props.placeholder ?? props.label ?? t('components.select'))

const searchInput = computed(() => {
  if (!props.searchable) return false
  return {
    placeholder: t('components.filterSearch'),
    icon: 'i-lucide-search',
  }
})

const internalValue = computed<any[]>({
  get: () => {
    if (modelValue.value == null) {
      return props.showNoneOption ? [MULTISELECT_FILTER_NONE] : []
    }
    return modelValue.value
  },
  set: (value) => {
    const raw = Array.isArray(value) ? value : []
    const rest = raw.filter((v) => v !== MULTISELECT_FILTER_NONE)

    if (props.showNoneOption && raw.includes(MULTISELECT_FILTER_NONE)) {
      if (rest.length === 0) {
        modelValue.value = null
        return
      }
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
      multiple
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

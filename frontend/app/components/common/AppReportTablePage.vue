<script setup lang="ts">
withDefaults(defineProps<{
  title: string
  apiError?: string | null
  filterConfigs?: { key: string; items: unknown[]; label?: string; placeholder?: string }[]
  showSearch?: boolean
}>(), {
  apiError: null,
  filterConfigs: () => [],
  showSearch: true,
})

const globalFilter = defineModel<string>('globalFilter', { default: '' })
const filterSelections = defineModel<Record<string, string[] | null>>('filterSelections', {
  default: () => ({}),
})

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <div class="flex flex-col h-full bg-background overflow-hidden text-foreground tracking-tight">
    <LayoutAppHeader :title="title">
      <template #right>
        <slot name="header-actions" />
      </template>
    </LayoutAppHeader>

    <div class="flex-1 p-2 overflow-hidden flex flex-col gap-2 min-h-0">
      <div
        v-if="showSearch || filterConfigs.length || $slots.toolbar"
        class="app-report-toolbar flex flex-nowrap items-center justify-between gap-3 shrink-0 px-1 min-w-0"
      >
        <CommonAppSearch
          v-if="showSearch"
          v-model="globalFilter"
          class="w-52 shrink-0"
        />

        <div
          v-if="filterConfigs.length || $slots.toolbar"
          class="flex flex-nowrap items-center gap-2 shrink-0 ml-auto overflow-x-auto"
        >
          <CommonAppMutilSelect
            v-for="cfg in filterConfigs"
            :key="cfg.key"
            :model-value="filterSelections?.[cfg.key] ?? null"
            :items="cfg.items"
            :placeholder="cfg.placeholder ?? cfg.label"
            class="shrink-0"
            @update:model-value="(value) => filterSelections = { ...filterSelections, [cfg.key]: value }"
          />

          <slot name="toolbar" />
        </div>
      </div>

      <CommonAppApiErrorBanner v-if="apiError" :message="apiError" @retry="emit('retry')" />

      <div class="flex-1 min-h-0 min-w-0 w-full overflow-hidden">
        <slot />
      </div>
    </div>

    <slot name="modals" />
  </div>
</template>

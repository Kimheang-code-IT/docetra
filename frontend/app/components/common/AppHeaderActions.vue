<script setup lang="ts">
withDefaults(defineProps<{
  showChart?: boolean
  showExport?: boolean
  showImport?: boolean
  showAdd?: boolean
  showReload?: boolean
  showDatepicker?: boolean
  chartLabel?: string
  exportLabel?: string
  importLabel?: string
  addLabel?: string
  addIcon?: string
  reloadLoading?: boolean
}>(), {
  showChart: false,
  showExport: false,
  showImport: false,
  showAdd: false,
  showReload: false,
  showDatepicker: true,
  chartLabel: '',
  exportLabel: '',
  importLabel: '',
  addLabel: '',
  addIcon: 'i-lucide-circle-plus',
  reloadLoading: false,
})

const emit = defineEmits<{
  (e: 'chart'): void
  (e: 'export'): void
  (e: 'import'): void
  (e: 'add'): void
  (e: 'reload'): void
}>()
</script>

<template>
  <div class="flex flex-nowrap items-center justify-end gap-2 px-2">
    <CommonAppReloadButton
      v-if="showReload"
      :loading="reloadLoading"
      @reload="emit('reload')"
    />

    <UButton
      v-if="showChart"
      icon="i-lucide-layout-grid"
      color="primary"
      variant="solid"
      class="font-normal shadow-sm shrink-0"
      @click="emit('chart')"
    >
      <span class="hidden sm:inline">{{ chartLabel }}</span>
    </UButton>

    <UButton
      v-if="showExport"
      icon="i-lucide-download"
      color="neutral"
      variant="subtle"
      class="font-normal shadow-sm shrink-0"
      @click="emit('export')"
    >
      <span class="hidden sm:inline">{{ exportLabel }}</span>
    </UButton>

    <UButton
      v-if="showImport"
      icon="i-lucide-file-up"
      color="neutral"
      variant="subtle"
      class="font-normal shadow-sm shrink-0"
      @click="emit('import')"
    >
      <span class="hidden sm:inline">{{ importLabel || $t('import.action') }}</span>
    </UButton>

    <UButton
      v-if="showAdd"
      :icon="addIcon"
      color="primary"
      variant="solid"
      class="font-normal shadow-sm shrink-0"
      @click="emit('add')"
    >
      <span class="hidden sm:inline">{{ addLabel }}</span>
    </UButton>

    <CommonAppDatepicker v-if="showDatepicker" class="shrink-0" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  PAGE_SIZE_SELECT_ITEMS,
  PAGE_SIZE_ALL,
  createDefaultPaginationState,
  isAllPageSize,
  resolvePageSizeSelection,
} from '~/utils/api/pagination'

const pagination = defineModel<any>('pagination', {
  default: createDefaultPaginationState,
})

const props = defineProps<{
  total: number
  selectedCount?: number
  allSelected?: boolean
  selectable?: boolean
}>()

defineEmits<{
  (e: 'toggle-select-all', val: boolean): void
}>()

const selectedPageSize = computed(() => {
  if (isAllPageSize(pagination.value.pageSize, props.total)) return PAGE_SIZE_ALL
  return pagination.value.pageSize
})

function onPageSizeChange(val: number | string) {
  pagination.value = {
    ...pagination.value,
    pageSize: resolvePageSizeSelection(val, props.total),
    pageIndex: 0,
  }
}
</script>

<template>
  <div class="flex flex-row items-center justify-between border-t border-accented py-2 px-3 gap-2 shrink-0 bg-background/50 w-full overflow-hidden">
    <!-- Rows per page selector (Left) -->
    <div class="flex items-center gap-1 shrink-0">
      <span class="text-[10px] text-muted-foreground whitespace-nowrap hidden sm:inline">{{ $t('components.rowsPerPage') }}</span>
      <USelect
        :model-value="selectedPageSize"
        :items="[...PAGE_SIZE_SELECT_ITEMS]"
        variant="ghost"
        size="xs"
        class="font-normal text-foreground w-20"
        @update:model-value="onPageSizeChange"
      />
    </div>

    <!-- Page Controls (Right) -->
    <div class="flex items-center gap-4">

      <UPagination
        :page="(pagination.pageIndex || 0) + 1"
        :items-per-page="pagination.pageSize"
        :total="total"
        @update:page="(p) => pagination = { ...pagination, pageIndex: p - 1 }"
        active-color="primary"
        size="xs"
        class="shrink-0"
      />
    </div>
  </div>
</template>

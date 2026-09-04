<script setup lang="ts">
import {
  TABLE_PAGE_SIZES,
  paginationItemsPerPage,
  parsePageLimit,
} from '~/utils/pagination'

/**
 * Shared server-list footer: rows-per-page + range text + page controls.
 * Used by table, card boards, and timeline lists.
 */
const props = withDefaults(defineProps<{
  page: number
  limit: number
  total: number
  rowCount?: number
}>(), {
  rowCount: undefined,
})

const emit = defineEmits<{
  'update:page': [number]
  'update:limit': [number]
}>()

const pageSizeItems = computed(() =>
  TABLE_PAGE_SIZES.map(size => ({ label: String(size), value: String(size) })),
)

const pageSizeModel = computed({
  get: () => String(props.limit),
  set: (value) => {
    const nextLimit = parsePageLimit(value, 10)
    if (nextLimit === props.limit && props.page === 1) return
    emit('update:page', 1)
    emit('update:limit', nextLimit)
  },
})

const effectiveItemsPerPage = computed(() => paginationItemsPerPage(props.limit))

const visibleRange = computed(() => {
  const count = props.rowCount ?? 0
  if (!props.total || !count) return { start: 0, end: 0 }
  const start = ((props.page - 1) * props.limit) + 1
  return {
    start,
    end: Math.min(start + count - 1, props.total),
  }
})
</script>

<template>
  <div
    class="flex shrink-0 items-center justify-between gap-1.5 border-t border-default bg-default px-2 py-1.5 sm:gap-3 sm:px-3 sm:py-2"
  >
    <div class="flex shrink-0 items-center gap-1.5 text-sm text-toned sm:gap-2">
      <span class="hidden sm:inline">{{ $t('common.rowsPerPage') }}</span>
      <USelect
        v-model="pageSizeModel"
        :items="pageSizeItems"
        value-key="value"
        size="sm"
        class="w-17 sm:w-22"
        :content="{ side: 'top', align: 'start', sideOffset: 6 }"
        :aria-label="$t('common.rowsPerPage')"
        :ui="{ base: 'rounded-md bg-default ring-1 ring-default' }"
      />
      <span class="hidden whitespace-nowrap text-xs text-muted md:inline">
        {{ $t('common.showingRows', { start: visibleRange.start, end: visibleRange.end, total }) }}
      </span>
    </div>

    <UPagination
      :page="page"
      :total="total"
      :items-per-page="effectiveItemsPerPage"
      :sibling-count="0"
      show-edges
      size="sm"
      color="neutral"
      variant="outline"
      active-color="primary"
      active-variant="solid"
      first-icon="i-lucide-chevrons-left"
      prev-icon="i-lucide-chevron-left"
      next-icon="i-lucide-chevron-right"
      last-icon="i-lucide-chevrons-right"
      :ui="{
        list: 'gap-0.5 sm:gap-1',
        item: 'min-w-7 h-7 justify-center rounded-md sm:min-w-8 sm:h-8',
        first: 'hidden rounded-md sm:inline-flex',
        prev: 'rounded-md',
        next: 'rounded-md',
        last: 'hidden rounded-md sm:inline-flex',
      }"
      @update:page="(v: number) => emit('update:page', v)"
    />
  </div>
</template>

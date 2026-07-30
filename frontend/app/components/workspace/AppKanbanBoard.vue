<script setup lang="ts">
import type { WorkflowStage } from '~/types/docetra/common'

const props = defineProps<{
  stages: WorkflowStage[]
  columns: Record<string, { items: Record<string, unknown>[]; total: number; page: number }>
  pending?: boolean
  titleField?: string
}>()

const emit = defineEmits<{
  cardClick: [Record<string, unknown>]
  loadMore: [stage: string]
  move: [id: string, stage: string]
}>()

const draggingId = ref<string | null>(null)

function onDragStart(id: string) {
  draggingId.value = id
}

function onDrop(stage: string) {
  if (!draggingId.value) return
  emit('move', draggingId.value, stage)
  draggingId.value = null
}

function cardTitle(card: Record<string, unknown>) {
  const key = props.titleField || 'title'
  return String(card[key] || card.name || card.referenceNumber || card.id)
}
</script>

<template>
  <div class="relative flex gap-3 overflow-x-auto pb-2">
    <div
      v-if="pending"
      class="absolute inset-0 z-10 flex items-start justify-center bg-default/40 pt-16 backdrop-blur-[1px]"
    >
      <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
    </div>

    <div
      v-for="stage in stages"
      :key="stage.code"
      class="flex w-72 shrink-0 flex-col rounded-lg border border-default bg-default"
      @dragover.prevent
      @drop="onDrop(stage.code)"
    >
      <div class="flex items-center justify-between border-b border-default px-3 py-2">
        <div class="flex items-center gap-2">
          <h3 class="text-sm font-medium text-highlighted">{{ $t(stage.labelKey) }}</h3>
          <UBadge color="neutral" variant="subtle" size="sm">
            {{ columns[stage.code]?.total || 0 }}
          </UBadge>
        </div>
        <UDropdownMenu
          :items="[[
            ...stages.filter(s => s.code !== stage.code).map(s => ({
              label: $t('docetra.actions.moveTo', { stage: $t(s.labelKey) }),
              onSelect: () => {
                const first = columns[stage.code]?.items[0]
                if (first) emit('move', String(first.id), s.code)
              },
            })),
          ]]"
        >
          <UButton icon="i-lucide-ellipsis" color="neutral" variant="ghost" size="xs" />
        </UDropdownMenu>
      </div>

      <div class="flex flex-1 flex-col gap-2 p-2 min-h-40">
        <button
          v-for="card in columns[stage.code]?.items || []"
          :key="String(card.id)"
          type="button"
          draggable="true"
          class="rounded-md border border-default bg-elevated/40 p-3 text-left transition hover:border-primary/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          @dragstart="onDragStart(String(card.id))"
          @click="emit('cardClick', card)"
        >
          <p class="text-sm font-medium text-highlighted line-clamp-2">{{ cardTitle(card) }}</p>
          <p class="mt-1 text-xs text-muted line-clamp-1">
            {{ String((card.owner as any)?.name || (card.assignee as any)?.name || card.status || '') }}
          </p>
          <div class="mt-2 flex flex-wrap gap-1">
            <UBadge v-if="card.status" size="sm" color="neutral" variant="subtle">{{ card.status }}</UBadge>
            <UBadge v-if="card.waiting" size="sm" color="warning" variant="subtle">{{ $t('docetra.fields.waiting') }}</UBadge>
          </div>
          <div class="mt-2">
            <USelect
              size="xs"
              :model-value="String(card.stage || stage.code)"
              :items="stages.map(s => ({ label: $t(s.labelKey), value: s.code }))"
              value-key="value"
              class="w-full"
              @click.stop
              @update:model-value="(v: string) => emit('move', String(card.id), v)"
            />
          </div>
        </button>

        <p v-if="!(columns[stage.code]?.items || []).length && !pending" class="px-2 py-6 text-center text-xs text-muted">
          {{ $t('docetra.states.emptyColumn') }}
        </p>

        <UButton
          v-if="(columns[stage.code]?.items.length || 0) < (columns[stage.code]?.total || 0)"
          size="xs"
          color="neutral"
          variant="ghost"
          block
          @click="emit('loadMore', stage.code)"
        >
          {{ $t('docetra.actions.loadMore') }}
        </UButton>
      </div>
    </div>
  </div>
</template>

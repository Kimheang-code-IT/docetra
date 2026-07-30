<script setup lang="ts">
defineProps<{
  pending?: boolean
  items: { label: string; value: string }[]
  maxHeight?: string
}>()
</script>

<template>
  <UCard class="shadow-sm border-accented flex flex-col overflow-hidden min-h-0 h-full">
    <template #header>
      <h2 class="text-sm font-normal uppercase tracking-widest text-muted-foreground">
        {{ $t('pages.dashboard.statusSummary') }}
      </h2>
    </template>
    <div
      class="divide-y divide-accented flex-1 overflow-y-auto min-h-0"
      :style="maxHeight ? { maxHeight } : undefined"
    >
      <template v-if="pending">
        <div v-for="i in 5" :key="i" class="py-3 flex justify-between items-center px-1">
          <USkeleton class="h-4 w-1/3" />
          <USkeleton class="h-4 w-4" />
        </div>
      </template>
      <template v-else>
        <div
          v-for="(item, index) in items"
          :key="`${item.label}-${index}`"
          class="py-3 flex justify-between items-center text-sm px-1"
        >
          <span class="text-muted-foreground truncate mr-2">{{ item.label }}</span>
          <span class="font-normal text-foreground border-b-2 border-primary/20 shrink-0">{{ item.value }}</span>
        </div>
      </template>
    </div>
    <template #footer>
      <p class="text-[10px] text-center text-muted-foreground opacity-60">
        {{ $t('pages.dashboard.lastUpdateApi') }}
      </p>
    </template>
  </UCard>
</template>

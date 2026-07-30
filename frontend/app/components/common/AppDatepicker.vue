<script setup lang="ts">
import { DateFormatter, getLocalTimeZone } from '@internationalized/date'

const { t } = useI18n()

// Use the global centralized date filter
const { dateRange, resetRange } = useGlobalFilter()

// Format for display
const df = new DateFormatter('en-US', {
  month: 'short',
  day: 'numeric'
})
</script>

<template>
  <UPopover :content="{ align: 'end' }">
    <!-- Trigger Button — works on all screen sizes -->
    <UButton
      color="neutral"
      variant="subtle"
      icon="i-lucide-calendar"
      trailing-icon="i-lucide-chevron-down"
      class="shrink-0 font-normal"
    >
      <span class="hidden sm:inline-flex items-center gap-1 ml-1.5">
        <template v-if="dateRange.start">
          <template v-if="dateRange.end">
            <span class="text-xs opacity-70">{{ df.format(dateRange.start.toDate(getLocalTimeZone())) }}</span>
            <span class="mx-1 text-primary">→</span>
            <span class="text-xs font-bold">{{ df.format(dateRange.end.toDate(getLocalTimeZone())) }}</span>
          </template>
          <template v-else>
            {{ df.format(dateRange.start.toDate(getLocalTimeZone())) }}
          </template>
        </template>
        <template v-else>
          {{ t('components.pickDate') }}
        </template>
      </span>
    </UButton>

    <template #content>
      <div class="flex flex-col bg-background rounded-lg overflow-hidden min-w-[200px]">
        <!-- Calendar — 1 month on mobile, 2 on lg screens -->
        <UCalendar
          :model-value="(dateRange as any)"
          class="p-2"
          :number-of-months="1"
          range
          @update:model-value="(value: any) => { dateRange = value }"
        />

        <!-- Sidebar panel -->
        <div class="p-4 bg-muted/20 border-t flex flex-col gap-2 justify-end">
          <UButton
            :label="'Reset'"
            size="xs"
            variant="ghost"
            color="neutral"
            icon="i-lucide-rotate-ccw"
            @click="resetRange"
          />
        </div>
      </div>
    </template>
  </UPopover>
</template>

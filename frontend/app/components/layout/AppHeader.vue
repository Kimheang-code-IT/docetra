<script setup lang="ts">
import { useAppHeader } from '~/composables/layout/useAppHeader'

const { displayTitle, breadcrumbs, badges, hasBreadcrumbs } = useAppHeader()
</script>

<template>
  <UDashboardNavbar class="shrink-0 border-b border-default px-1.5">
    <template #leading>
      <UDashboardSidebarCollapse />
    </template>

    <template #title>
      <div v-if="hasBreadcrumbs" class="flex min-w-0 max-w-full items-center gap-2 overflow-hidden">
        <UBreadcrumb
          :items="breadcrumbs"
          color="neutral"
          class="min-w-0 truncate"
          :ui="{
            root: 'min-w-0',
            list: 'min-w-0 flex-nowrap overflow-hidden',
            link: 'text-sm',
          }"
        />
        <UBadge
          v-for="(badge, index) in badges"
          :key="`${badge.label}-${index}`"
          :color="badge.color || 'info'"
          variant="subtle"
          size="sm"
          class="shrink-0"
        >
          {{ badge.label }}
        </UBadge>
      </div>
      <span v-else class="truncate text-highlighted">{{ displayTitle || 'Docetra' }}</span>
    </template>

    <div class="min-w-0 flex-1" />

    <template #right>
      <div id="app-header-right" class="flex min-w-0 flex-wrap items-center justify-end gap-1.5 sm:gap-2" />
    </template>
  </UDashboardNavbar>
</template>

<script setup lang="ts">
import { useAppHeader } from '~/composables/layout/useAppHeader'

const { displayTitle, breadcrumbs, badges, hasBreadcrumbs, actions } = useAppHeader()
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
      <div class="flex shrink-0 flex-wrap items-center justify-end gap-1.5 sm:gap-2">
        <div
          id="app-header-leading"
          class="flex shrink-0 flex-wrap items-center justify-end gap-1.5 sm:gap-2"
        />

        <template v-if="actions">
          <UButton
            color="neutral"
            variant="soft"
            icon="i-lucide-refresh-cw"
            square
            :loading="actions.refreshing"
            class="rounded-md"
            :aria-label="$t('docetra.actions.refresh')"
            @click="actions.onRefresh?.()"
          />

          <UDropdownMenu
            v-if="actions.moreItems?.length"
            :items="actions.moreItems"
            :content="{ align: 'end' }"
          >
            <UButton
              color="neutral"
              variant="soft"
              icon="i-lucide-ellipsis"
              square
              class="rounded-md"
              :aria-label="$t('common.actions')"
            />
          </UDropdownMenu>
        </template>

        <div
          id="app-header-trailing"
          class="flex shrink-0 flex-wrap items-center justify-end gap-1.5 sm:gap-2"
        />

        <template v-if="actions?.createButtons?.length">
          <UButton
            v-for="(button, index) in actions.createButtons"
            :key="`${button.label}-${index}`"
            color="neutral"
            variant="solid"
            :icon="button.icon || 'i-lucide-plus'"
            :label="button.label"
            class="rounded-md"
            @click="button.onClick()"
          />
        </template>
        <UButton
          v-else-if="actions?.canCreate"
          color="neutral"
          variant="solid"
          :icon="actions.createIcon || 'i-lucide-plus'"
          :label="actions.createLabel"
          class="rounded-md"
          @click="actions.onCreate?.()"
        />
      </div>
    </template>
  </UDashboardNavbar>
</template>

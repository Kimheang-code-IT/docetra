<script setup lang="ts">
import logo from '~/assets/images/logo.png'
import { useMenu } from '~/composables/layout/useMenu'

const { open, collapsed, links, setCollapsed } = useMenu()

const collapsedModel = computed({
  get: () => collapsed.value,
  set: (value: boolean) => setCollapsed(value),
})

const sidebarUi = computed(() => ({
  root: collapsedModel.value
    ? 'bg-muted/50 border-e border-default'
    : 'bg-elevated/25 backdrop-blur-sm border-e border-default dark:bg-[#18191a]',
  header: collapsedModel.value
    ? 'h-auto flex-col items-center justify-center gap-2 px-0 pt-3 pb-2 shrink-0'
    : 'h-auto flex-col items-stretch gap-3 px-3 pt-3 pb-2 shrink-0',
  body: collapsedModel.value
    ? 'flex flex-col items-center gap-1 overflow-y-auto px-0 py-1'
    : 'flex flex-col gap-1 overflow-y-auto px-2 py-1',
  footer: collapsedModel.value
    ? 'shrink-0 flex items-center justify-center px-0 py-3 border-t border-default'
    : 'shrink-0 flex items-center gap-1.5 px-3 py-2 lg:border-t lg:border-default',
}))
</script>

<template>
  <UDashboardSidebar
    id="default"
    v-model:open="open"
    v-model:collapsed="collapsedModel"
    collapsible
    resizable
    :min-size="12"
    :default-size="15"
    :max-size="20"
    :collapsed-size="4"
    :ui="sidebarUi"
  >
    <template #resize-handle="{ onMouseDown, onTouchStart, onDoubleClick }">
      <UDashboardResizeHandle
        class="after:absolute after:inset-y-0 after:right-0 after:w-px hover:after:bg-(--ui-border-accented) after:transition"
        @mousedown="onMouseDown"
        @touchstart="onTouchStart"
        @dblclick="onDoubleClick"
      />
    </template>

    <template #header="{ collapsed: isCollapsed }">
      <NuxtLink
        to="/"
        class="flex items-center"
        :class="isCollapsed ? 'justify-center' : 'gap-3 px-1'"
        :aria-label="$t('docetra.brand.name')"
      >
        <span
          class="grid shrink-0 place-items-center overflow-hidden"
          :class="isCollapsed ? 'size-9' : 'size-10'"
        >
          <img
            :src="logo"
            :alt="$t('docetra.brand.logoAlt')"
            :class="isCollapsed ? 'size-6 object-contain' : 'size-8 object-contain'"
          >
        </span>
        <span v-if="!isCollapsed" class="min-w-0">
          <span class="block truncate text-xl font-semibold tracking-tight">{{ $t('docetra.brand.name') }}</span>
        </span>
      </NuxtLink>

      <UDashboardSearchButton
        :collapsed="isCollapsed"
        tooltip
        class="bg-transparent"
        :class="isCollapsed ? 'mx-auto' : 'ring-default'"
        :ui="isCollapsed
          ? { base: 'justify-center rounded-md size-9 p-0' }
          : undefined"
      />
    </template>

    <template #default="{ collapsed: isCollapsed }">
      <UNavigationMenu
        :collapsed="isCollapsed"
        :items="links[0]"
        orientation="vertical"
        tooltip
        popover
        :ui="isCollapsed
          ? {
              root: 'w-full items-center',
              list: 'w-full flex flex-col items-center gap-0.5',
              item: 'w-full flex justify-center',
              link: 'justify-center size-9 p-0 rounded-md',
              linkLeadingIcon: 'size-5 text-muted group-hover:text-highlighted group-data-[active]:text-primary',
            }
          : {
              root: 'w-full',
              link: 'rounded-md',
            }"
      />
      <UNavigationMenu
        v-if="links[1]?.length"
        :collapsed="isCollapsed"
        :items="links[1]"
        orientation="vertical"
        tooltip
        :ui="isCollapsed
          ? {
              root: 'w-full items-center',
              list: 'w-full flex flex-col items-center gap-0.5',
              item: 'w-full flex justify-center',
              link: 'justify-center size-9 p-0 rounded-md',
              linkLeadingIcon: 'size-5 text-muted',
            }
          : undefined"
      />
    </template>

    <template #footer="{ collapsed: isCollapsed }">
      <LayoutUserMenu :collapsed="isCollapsed" />
    </template>
  </UDashboardSidebar>
</template>

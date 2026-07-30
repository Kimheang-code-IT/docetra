<script setup lang="ts">
import logo from '~/assets/images/logo.png'
import { useMenu } from '~/composables/layout/useMenu'
const { open, links } = useMenu()
</script>

<template>
  <UDashboardSidebar id="default" v-model:open="open" collapsible resizable class="bg-elevated/25 backdrop-blur-sm dark:bg-[#18191a]" :ui="{
    header: 'h-auto flex-col items-stretch gap-4 px-4 shrink-0',
    footer: 'lg:border-t lg:border-default'
  }">
    <template #resize-handle="{ onMouseDown, onTouchStart, onDoubleClick }">
      <UDashboardResizeHandle
        class="after:absolute after:inset-y-0 after:right-0 after:w-px hover:after:bg-(--ui-border-accented) after:transition"
        @mousedown="onMouseDown" @touchstart="onTouchStart" @dblclick="onDoubleClick" />
    </template>

    <template #header="{ collapsed }">
      <NuxtLink to="/" class="flex items-center gap-3 py-2" :aria-label="$t('docetra.brand.name')">
        <span class="grid size-10 shrink-0 place-items-center rounded-xl bg-primary/10 ring-1 ring-primary/20">
          <img :src="logo" :alt="$t('docetra.brand.logoAlt')" class="size-8 object-contain">
        </span>
        <span v-if="!collapsed" class="min-w-0">
          <span class="block truncate text-xl font-semibold tracking-tight">{{ $t('docetra.brand.name') }}</span>
        </span>
      </NuxtLink>

      <UDashboardSearchButton :collapsed="collapsed" class="bg-transparent ring-default mb-2" />
    </template>

    <template #default="{ collapsed }">
      <UNavigationMenu :collapsed="collapsed" :items="links[0]" orientation="vertical" tooltip popover class="px-1" />

      <UNavigationMenu :collapsed="collapsed" :items="links[1]" orientation="vertical" tooltip />
    </template>

    <template #footer="{ collapsed }">
      <LayoutUserMenu :collapsed="collapsed" />
    </template>
  </UDashboardSidebar>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMenu } from '~/composables/layout/useMenu'

const { links } = useMenu()

const searchGroups = computed(() => {
  const items: any[] = []

  const navLinks = links.value?.[0] || []
  navLinks.forEach((link: any) => {
    if (link.children) {
      link.children.forEach((child: any) => {
        items.push({
          id: child.to,
          label: child.label,
          icon: child.icon || link.icon,
          to: child.to,
        })
      })
    }
    else {
      items.push({
        id: link.to,
        label: link.label,
        icon: link.icon,
        to: link.to,
      })
    }
  })

  return [{
    id: 'navigation',
    label: 'Pages',
    items,
  }]
})
</script>

<template>
  <UDashboardGroup unit="rem" class="h-screen overflow-hidden bg-default">
    <LayoutAppSlidebar />
    <UDashboardSearch :groups="searchGroups" />

    <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
      <LayoutAppHeader />
      <main class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden p-0">
        <slot />
      </main>
    </div>
  </UDashboardGroup>
</template>

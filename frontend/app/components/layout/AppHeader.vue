<script setup lang="ts">
interface Props {
  title: string
}

defineProps<Props>()
</script>

<template>
  <ClientOnly>
    <UDashboardNavbar :title="title" class="px-2 sm:px-3">
      <template #leading>
        <UDashboardSidebarCollapse />
      </template>

      <div class="flex-1 min-w-0" />

      <template #right>
        <div class="flex items-center justify-end gap-2 min-w-0">
          <slot name="right" />
        </div>
      </template>
    </UDashboardNavbar>
  </ClientOnly>
</template>

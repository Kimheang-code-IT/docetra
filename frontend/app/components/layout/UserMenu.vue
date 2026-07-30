<script setup lang="ts">
import { useUserMenu } from '~/composables/layout/useUserMenu'

defineProps<{ collapsed?: boolean }>()
const { user, items, aboutOpen } = useUserMenu()
</script>

<template>
  <div :class="collapsed ? 'flex justify-center' : 'w-full'">
    <UDropdownMenu
      :items="items"
      :content="{ align: collapsed ? 'end' : 'center', collisionPadding: 12, side: collapsed ? 'right' : 'top' }"
      :ui="{
        content: collapsed ? 'w-52' : 'w-(--reka-dropdown-menu-trigger-width)',
      }"
    >
      <UButton
        v-if="collapsed"
        color="neutral"
        variant="ghost"
        square
        class="rounded-full p-0.5 data-[state=open]:bg-elevated"
        :aria-label="user.name"
      >
        <UAvatar
          :src="user.avatar.src"
          :alt="user.avatar.alt"
          size="md"
          class="ring-1 ring-default"
        />
      </UButton>

      <UButton
        v-else
        :avatar="user.avatar"
        :label="user.name"
        trailing-icon="i-lucide-chevrons-up-down"
        color="neutral"
        variant="ghost"
        block
        class="data-[state=open]:bg-elevated"
        :ui="{
          trailingIcon: 'text-dimmed',
        }"
      />
    </UDropdownMenu>

    <LayoutAppAboutDialog v-model:open="aboutOpen" />
  </div>
</template>

<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('sectors')

definePageMeta({
  titleKey: 'docetra.pages.sector',
  permission: 'organizations.sectors.view',
})
</script>

<template>
  <WorkspaceEntityWorkspaceView :config="config" />
</template>

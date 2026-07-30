<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('companySectors')

definePageMeta({
  titleKey: 'docetra.pages.companySector',
  permission: 'organizations.company_sectors.view',
})
</script>

<template>
  <WorkspaceEntityWorkspaceView :config="config" />
</template>

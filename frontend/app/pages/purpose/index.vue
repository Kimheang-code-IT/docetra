<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('purposes')

definePageMeta({
  titleKey: 'docetra.pages.purpose',
  permission: 'organizations.purposes.view',
})
</script>

<template>
  <WorkspaceEntityWorkspaceView :config="config" />
</template>

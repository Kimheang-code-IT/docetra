<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('roles')

definePageMeta({
  titleKey: 'docetra.pages.role',
  permission: 'users.roles.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

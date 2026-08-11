<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('users')

definePageMeta({
  titleKey: 'docetra.pages.user',
  permission: 'users.users.create',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

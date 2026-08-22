<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('officers')

definePageMeta({
  titleKey: 'docetra.pages.officer',
  permission: 'organizations.officers.create',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

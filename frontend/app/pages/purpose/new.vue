<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('purposes')

definePageMeta({
  titleKey: 'docetra.pages.purpose',
  permission: 'organizations.purposes.create',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

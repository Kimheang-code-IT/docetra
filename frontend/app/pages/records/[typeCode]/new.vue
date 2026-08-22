<script setup lang="ts">
import { buildEntityConfigForType } from '~/config/entities'
import { useRecordSurfaces } from '~/composables/record/useRecordSurfaces'

const route = useRoute()
const { load, resolveByParam } = useRecordSurfaces()

await load()
const param = String(route.params.typeCode || '')
const surface = computed(() => resolveByParam('document', param))

if (!surface.value) {
  throw createError({ statusCode: 404, statusMessage: 'Record type not found' })
}

const config = computed(() => buildEntityConfigForType({
  typeCode: surface.value!.code,
  name: surface.value!.name,
  routeBase: surface.value!.routeBase,
  uiSurface: 'document',
  icon: surface.value!.icon,
  isCreatable: surface.value!.isCreatable,
  supportsStages: surface.value!.supportsStages,
}))

definePageMeta({
  titleKey: 'docetra.navigation.record',
})

useHead({ title: () => `New ${surface.value?.name || 'Record'}` })
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

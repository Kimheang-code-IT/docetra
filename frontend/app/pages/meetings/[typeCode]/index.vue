<script setup lang="ts">
import { buildEntityConfigForType } from '~/config/entities'
import { useRecordSurfaces } from '~/composables/record/useRecordSurfaces'

const route = useRoute()
const { load, resolveByParam } = useRecordSurfaces()

await load()
const param = String(route.params.typeCode || '')
const surface = computed(() => resolveByParam('meeting', param))

if (!surface.value) {
  throw createError({ statusCode: 404, statusMessage: 'Meeting type not found' })
}

const config = computed(() => buildEntityConfigForType({
  typeCode: surface.value!.code,
  name: surface.value!.name,
  routeBase: surface.value!.routeBase,
  uiSurface: 'meeting',
  icon: surface.value!.icon,
  isCreatable: surface.value!.isCreatable,
  supportsStages: surface.value!.supportsStages,
  supportsTopicContainer: surface.value!.supportsTopicContainer,
}))

definePageMeta({
  titleKey: 'docetra.navigation.meeting',
})

useHead({ title: () => surface.value?.name || 'Meeting' })
</script>

<template>
  <MeetingAppMeetingTopicBoard
    v-if="config.recordTypeCode === 'meeting_topic' || surface?.supportsTopicContainer"
  />
  <WorkspaceEntityWorkspaceView
    v-else-if="config.recordTypeCode === 'meeting_history' || config.defaultView === 'table'"
    :config="config"
  />
  <RecordAppRecordStageBoard
    v-else
    :config="config"
    date-field="recordTime"
    subtitle-field="recordTypeName"
    :state-key="`record-stage-${config.recordTypeCode}`"
  />
</template>

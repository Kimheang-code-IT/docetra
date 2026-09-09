<script setup lang="ts">
import { useRecordSurfacePage } from '~/composables/record/useRecordSurfacePage'

definePageMeta({
  titleKey: 'docetra.navigation.meeting',
  key: route => route.path,
})

const { surface, config, pageKey } = await useRecordSurfacePage('meeting')

useHead({ title: () => surface.value?.name || 'Meeting' })
</script>

<template>
  <MeetingAppMeetingTopicBoard
    v-if="config.recordTypeCode === 'meeting_topic' || surface?.supportsTopicContainer"
    :key="pageKey"
  />
  <WorkspaceEntityWorkspaceView
    v-else-if="config.recordTypeCode === 'meeting_history' || config.defaultView === 'table'"
    :key="pageKey"
    :config="config"
  />
  <RecordAppRecordStageBoard
    v-else
    :key="pageKey"
    :config="config"
    date-field="recordTime"
    subtitle-field="recordTypeName"
    :state-key="`record-stage-${config.recordTypeCode}`"
  />
</template>

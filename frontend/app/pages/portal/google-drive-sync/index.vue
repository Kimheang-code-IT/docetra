<script setup lang="ts">
// Dedicated Drive sync workflow — create source, start sync, poll job status,
// refresh synced files. Linking a Drive file to a meeting lives in the
// meeting notes dialog picker.

definePageMeta({
  titleKey: 'docetra.pages.googleDriveSync',
  permission: 'portal.google_drive_sync.view',
})
</script>

<template>
  <PortalAppGoogleDriveSync />
</template>

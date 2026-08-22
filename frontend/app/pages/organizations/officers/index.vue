<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.officer',
  permission: 'organizations.officers.view',
})
await navigateTo('/officers', { replace: true })
</script>

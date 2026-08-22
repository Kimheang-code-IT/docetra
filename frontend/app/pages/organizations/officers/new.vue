<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.officer',
  permission: 'organizations.officers.create',
})
await navigateTo('/officers/new', { replace: true })
</script>

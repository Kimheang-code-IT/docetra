<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.purpose',
  permission: 'organizations.purposes.view',
})
await navigateTo('/purpose', { replace: true })
</script>

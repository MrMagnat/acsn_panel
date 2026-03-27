<script setup>
definePageMeta({ middleware: 'auth' })
await navigateTo('/cabinet/office', { replace: true })
</script>

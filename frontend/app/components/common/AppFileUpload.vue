<script setup lang="ts">
/**
 * Styled Nuxt UI file dropzone with a prominent upload icon
 * and per-file type icons in the list.
 */
import { fileTypeIcon } from '~/utils/file-icon'

const model = defineModel<File | File[] | null | undefined>()

const props = withDefaults(defineProps<{
  multiple?: boolean
  accept?: string
  label?: string
  description?: string
  icon?: string
  disabled?: boolean
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  layout?: 'list' | 'grid'
  class?: string
}>(), {
  multiple: true,
  icon: 'i-lucide-cloud-upload',
  size: 'md',
  layout: 'list',
})
</script>

<template>
  <UFileUpload
    v-model="model"
    :multiple="multiple"
    :accept="accept"
    :label="label"
    :description="description"
    :icon="icon"
    :disabled="disabled"
    :size="size"
    variant="area"
    :layout="layout"
    position="inside"
    :file-image="false"
    color="primary"
    :class="props.class || 'w-full min-h-44'"
    :ui="{
      base: 'bg-elevated/40 ring-default hover:bg-elevated/60 data-[dragging]:bg-primary/5 data-[dragging]:ring-primary',
      wrapper: 'gap-3',
      icon: 'size-10 text-primary',
      label: 'text-sm font-medium text-highlighted',
      description: 'text-xs text-muted',
      file: 'bg-default/80 ring-default',
    }"
  >
    <template #file-leading="{ file }">
      <div
        class="grid size-9 shrink-0 place-items-center rounded-md bg-elevated ring ring-default"
        :title="file.type || file.name"
      >
        <UIcon
          :name="fileTypeIcon(file).icon"
          class="size-4"
          :class="fileTypeIcon(file).class"
        />
      </div>
    </template>
  </UFileUpload>
</template>

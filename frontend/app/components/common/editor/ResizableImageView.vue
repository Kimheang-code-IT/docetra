<script setup lang="ts">
import type { NodeViewProps } from '@tiptap/vue-3'
import { NodeViewWrapper } from '@tiptap/vue-3'

const props = defineProps<NodeViewProps>()

const imgRef = ref<HTMLImageElement | null>(null)
const resizing = ref(false)

const width = computed(() => {
  const w = props.node.attrs.width
  return typeof w === 'number' ? w : null
})

const imageSrc = computed(() => safeImageSource(props.node.attrs.src))

function startResize(event: PointerEvent) {
  if (!props.editor.isEditable) return
  event.preventDefault()
  event.stopPropagation()

  const startX = event.clientX
  const startWidth = width.value || imgRef.value?.getBoundingClientRect().width || 240
  resizing.value = true

  const onMove = (e: PointerEvent) => {
    const next = Math.max(80, Math.round(startWidth + (e.clientX - startX)))
    props.updateAttributes({ width: next })
  }

  const onUp = () => {
    resizing.value = false
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp)
  }

  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}
</script>

<template>
  <NodeViewWrapper
    as="div"
    class="resizable-image-wrap group relative my-2 inline-block max-w-full"
    :class="{ 'is-resizing': resizing }"
    data-drag-handle
  >
    <img
      v-if="imageSrc"
      ref="imgRef"
      :src="imageSrc"
      :alt="node.attrs.alt || ''"
      :title="node.attrs.title || undefined"
      class="block h-auto max-w-full rounded-md"
      :style="width ? { width: `${width}px` } : undefined"
      draggable="false"
      referrerpolicy="no-referrer"
    >
    <span
      v-if="editor.isEditable"
      class="absolute bottom-1 right-1 hidden size-3.5 cursor-se-resize rounded-sm border border-white bg-primary shadow-sm group-hover:block group-[.is-resizing]:block"
      aria-hidden="true"
      @pointerdown="startResize"
    />
  </NodeViewWrapper>
</template>

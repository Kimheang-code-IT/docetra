import { ref } from 'vue'

/**
 * Shared drag-drop state for board rails (stage move / topic assign).
 * Domain boards still decide what a successful drop means.
 */
export function useBoardDragDrop() {
  const draggingId = ref<string | null>(null)
  const dropTargetId = ref<string | null>(null)

  function onDragStart(id: string) {
    draggingId.value = id
  }

  function onDragEnd() {
    draggingId.value = null
    dropTargetId.value = null
  }

  function onDragOver(targetId: string) {
    dropTargetId.value = targetId
  }

  function onDragLeave(targetId: string) {
    if (dropTargetId.value === targetId) dropTargetId.value = null
  }

  /** Clears drag state and returns the dragged id (if any). */
  function consumeDrop(): string | null {
    const id = draggingId.value
    draggingId.value = null
    dropTargetId.value = null
    return id
  }

  return {
    draggingId,
    dropTargetId,
    onDragStart,
    onDragEnd,
    onDragOver,
    onDragLeave,
    consumeDrop,
  }
}

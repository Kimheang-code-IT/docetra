import { describe, expect, it } from 'vitest'
import { useBoardDragDrop } from '../../app/composables/common/useBoardDragDrop'

describe('useBoardDragDrop', () => {
  it('tracks drag start, over, leave, and consumeDrop', () => {
    const dnd = useBoardDragDrop()

    dnd.onDragStart('m-1')
    expect(dnd.draggingId.value).toBe('m-1')

    dnd.onDragOver('topic-a')
    expect(dnd.dropTargetId.value).toBe('topic-a')

    dnd.onDragLeave('topic-b')
    expect(dnd.dropTargetId.value).toBe('topic-a')

    dnd.onDragLeave('topic-a')
    expect(dnd.dropTargetId.value).toBeNull()

    dnd.onDragOver('topic-a')
    expect(dnd.consumeDrop()).toBe('m-1')
    expect(dnd.draggingId.value).toBeNull()
    expect(dnd.dropTargetId.value).toBeNull()
  })

  it('clears state on drag end', () => {
    const dnd = useBoardDragDrop()
    dnd.onDragStart('m-2')
    dnd.onDragOver('stage-x')
    dnd.onDragEnd()
    expect(dnd.draggingId.value).toBeNull()
    expect(dnd.dropTargetId.value).toBeNull()
  })
})

import { describe, expect, it } from 'vitest'
import { displayListText, referenceLabel } from '~/utils/display/reference-text'

describe('reference-text display helpers', () => {
  it('renders mention objects ({id, label, type}) as their label', () => {
    expect(referenceLabel({ id: '1', label: 'Demo Officer Alice', type: 'officer' }))
      .toBe('Demo Officer Alice')
  })

  it('falls back through label/name/title keys', () => {
    expect(referenceLabel({ id: '1', name: 'Finance Dept' })).toBe('Finance Dept')
    expect(referenceLabel({ title: 'Meeting' })).toBe('Meeting')
  })

  it('joins arrays of objects with commas', () => {
    expect(displayListText([
      { id: '1', label: 'Alice' },
      { id: '2', label: 'Bob' },
    ])).toBe('Alice, Bob')
  })

  it('handles arrays of plain strings', () => {
    expect(displayListText(['a', 'b'])).toBe('a, b')
  })

  it('handles a single object value', () => {
    expect(displayListText({ id: '5', label: 'Demo Alpha Co Ltd' })).toBe('Demo Alpha Co Ltd')
  })

  it('returns empty string for null/empty/objects without labels', () => {
    expect(displayListText(null)).toBe('')
    expect(displayListText([])).toBe('')
    expect(displayListText({ id: 'x' })).toBe('')
  })

  it('never returns "[object Object]"', () => {
    const value = [{ id: '1', label: 'A' }, { id: '2' }]
    expect(displayListText(value)).not.toContain('object')
  })
})

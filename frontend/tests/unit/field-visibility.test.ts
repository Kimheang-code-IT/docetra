import { describe, expect, it } from 'vitest'
import { isFieldVisible } from '~/utils/field-visibility'

describe('field visibility', () => {
  it('shows fields without a condition', () => {
    expect(isFieldVisible({}, () => undefined)).toBe(true)
  })

  it('shows a field only when the referenced value equals the condition', () => {
    const field = { visibleWhen: { key: 'authenticationEnabled', equals: true } }
    expect(isFieldVisible(field, () => true)).toBe(true)
    expect(isFieldVisible(field, () => false)).toBe(false)
    expect(isFieldVisible(field, () => undefined)).toBe(false)
  })

  it('hides a field when the referenced value matches notEquals', () => {
    const field = { visibleWhen: { key: 'status', notEquals: 'disabled' } }
    expect(isFieldVisible(field, () => 'active')).toBe(true)
    expect(isFieldVisible(field, () => 'disabled')).toBe(false)
  })
})

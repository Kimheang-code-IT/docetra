import { describe, expect, it } from 'vitest'
import {
  companionNameKey,
  ensureSelectItemsHaveLabel,
  looksLikeOpaqueId,
} from '../../app/utils/select-display'

describe('select-display', () => {
  it('maps FK fields to companion name keys', () => {
    expect(companionNameKey('roleId')).toBe('roleName')
    expect(companionNameKey('organizationId')).toBe('organizationName')
    expect(companionNameKey('topicId')).toBe('topicName')
  })

  it('detects UUID opaque ids', () => {
    expect(looksLikeOpaqueId('ce67d9f5-b2cc-45a5-96f2-c8c5369562d5')).toBe(true)
    expect(looksLikeOpaqueId('Super Admin')).toBe(false)
  })

  it('seeds a friendly label when the selected value is missing from options', () => {
    const items = ensureSelectItemsHaveLabel(
      [{ label: 'Viewer', value: 'role-2' }],
      'ce67d9f5-b2cc-45a5-96f2-c8c5369562d5',
      'Super Admin',
    )
    expect(items[0]).toEqual({
      label: 'Super Admin',
      value: 'ce67d9f5-b2cc-45a5-96f2-c8c5369562d5',
    })
  })

  it('replaces opaque labels when a companion name is available', () => {
    const id = 'ce67d9f5-b2cc-45a5-96f2-c8c5369562d5'
    const items = ensureSelectItemsHaveLabel(
      [{ label: id, value: id }],
      id,
      'Super Admin',
    )
    expect(items).toEqual([{ label: 'Super Admin', value: id }])
  })
})

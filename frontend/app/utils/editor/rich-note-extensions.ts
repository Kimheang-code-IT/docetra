import TextAlign from '@tiptap/extension-text-align'
import Highlight from '@tiptap/extension-highlight'
import { TextStyle, Color } from '@tiptap/extension-text-style'
import type { Extensions } from '@tiptap/core'

export const TEXT_COLORS = [
  '#111827',
  '#dc2626',
  '#ea580c',
  '#ca8a04',
  '#16a34a',
  '#0891b2',
  '#2563eb',
  '#7c3aed',
  '#db2777',
  '#6b7280',
] as const

export const HIGHLIGHT_COLORS = [
  '#fef08a',
  '#bbf7d0',
  '#bae6fd',
  '#e9d5ff',
  '#fecaca',
  '#fed7aa',
  '#e5e7eb',
] as const

/**
 * Safe TipTap extras for meeting notes.
 * Do NOT add Underline — StarterKit (via UEditor) already includes it.
 * Tables are optional and loaded separately.
 */
export function createRichNoteExtensions(): Extensions {
  return [
    TextAlign.configure({
      types: ['heading', 'paragraph'],
    }),
    TextStyle,
    Color,
    Highlight.configure({
      multicolor: true,
    }),
  ]
}


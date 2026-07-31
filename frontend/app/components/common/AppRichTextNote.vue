<script setup lang="ts">
import type { EditorCustomHandlers, EditorToolbarItem } from '@nuxt/ui'
import type { Editor } from '@tiptap/vue-3'
import type { Extensions } from '@tiptap/core'
import {
  createRichNoteExtensions,
  HIGHLIGHT_COLORS,
  TEXT_COLORS,
} from '~/utils/editor/rich-note-extensions'

const model = defineModel<string>({ default: '' })

withDefaults(defineProps<{
  placeholder?: string
  disabled?: boolean
  fill?: boolean
  minHeightClass?: string
}>(), {
  fill: false,
})

const { t } = useI18n()
const toast = useToast()

const editorRef = shallowRef<Editor | null>(null)
const imageInput = ref<HTMLInputElement | null>(null)
const extensions = shallowRef<Extensions>([])
const ready = ref(false)
const bootError = ref<string | null>(null)
const mountKey = ref(0)
const enableTables = ref(false)

const ZOOM_STEPS = [50, 75, 100, 125, 150, 175, 200] as const
type ZoomLevel = (typeof ZOOM_STEPS)[number]
const zoom = ref<ZoomLevel>(100)
const zoomOptions = computed(() =>
  ZOOM_STEPS.map(value => ({ label: `${value}%`, value })),
)

function toTitleCase(value: string) {
  return value.replace(/\w\S*/g, word =>
    word.charAt(0).toUpperCase() + word.slice(1).toLowerCase(),
  )
}

function applyCase(editor: Editor, mode: 'upper' | 'lower' | 'title') {
  const { from, to, empty } = editor.state.selection
  if (empty) return editor.chain().focus()

  const text = editor.state.doc.textBetween(from, to, ' ')
  const next = mode === 'upper'
    ? text.toUpperCase()
    : mode === 'lower'
      ? text.toLowerCase()
      : toTitleCase(text)

  return editor.chain().focus().insertContentAt({ from, to }, next)
}

const handlers = {
  image: {
    canExecute: (editor: Editor) => editor.isEditable,
    execute: (editor: Editor) => {
      editorRef.value = editor
      imageInput.value?.click()
      return editor.chain().focus()
    },
    isActive: (editor: Editor) => editor.isActive('image'),
    isDisabled: (editor: Editor) => !editor.isEditable,
  },
  textColor: {
    canExecute: (editor: Editor) => editor.can().setColor('#000000'),
    execute: (editor: Editor, item?: { color?: string }) => {
      if (!item?.color) return editor.chain().focus().unsetColor()
      return editor.chain().focus().setColor(item.color)
    },
    isActive: (editor: Editor, item?: { color?: string }) =>
      !!item?.color && editor.isActive('textStyle', { color: item.color }),
    isDisabled: (editor: Editor) => !editor.isEditable,
  },
  highlightColor: {
    canExecute: (editor: Editor) => editor.can().toggleHighlight(),
    execute: (editor: Editor, item?: { color?: string }) => {
      if (!item?.color) return editor.chain().focus().unsetHighlight()
      return editor.chain().focus().toggleHighlight({ color: item.color })
    },
    isActive: (editor: Editor, item?: { color?: string }) =>
      !!item?.color && editor.isActive('highlight', { color: item.color }),
    isDisabled: (editor: Editor) => !editor.isEditable,
  },
  changeCase: {
    canExecute: (editor: Editor) => !editor.state.selection.empty,
    execute: (editor: Editor, item?: { case?: 'upper' | 'lower' | 'title' }) =>
      applyCase(editor, item?.case || 'title'),
    isActive: () => false,
    isDisabled: (editor: Editor) => editor.state.selection.empty || !editor.isEditable,
  },
  insertTable: {
    canExecute: (editor: Editor) => editor.can().insertTable?.({ rows: 3, cols: 3, withHeaderRow: true }) ?? false,
    execute: (editor: Editor) =>
      editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }),
    isActive: (editor: Editor) => editor.isActive('table'),
    isDisabled: (editor: Editor) => !editor.isEditable || !editor.can().insertTable?.({ rows: 3, cols: 3, withHeaderRow: true }),
  },
  addColumnBefore: {
    canExecute: (editor: Editor) => editor.can().addColumnBefore?.() ?? false,
    execute: (editor: Editor) => editor.chain().focus().addColumnBefore(),
    isActive: () => false,
    isDisabled: (editor: Editor) => !(editor.can().addColumnBefore?.() ?? false),
  },
  addColumnAfter: {
    canExecute: (editor: Editor) => editor.can().addColumnAfter?.() ?? false,
    execute: (editor: Editor) => editor.chain().focus().addColumnAfter(),
    isActive: () => false,
    isDisabled: (editor: Editor) => !(editor.can().addColumnAfter?.() ?? false),
  },
  deleteColumn: {
    canExecute: (editor: Editor) => editor.can().deleteColumn?.() ?? false,
    execute: (editor: Editor) => editor.chain().focus().deleteColumn(),
    isActive: () => false,
    isDisabled: (editor: Editor) => !(editor.can().deleteColumn?.() ?? false),
  },
  addRowBefore: {
    canExecute: (editor: Editor) => editor.can().addRowBefore?.() ?? false,
    execute: (editor: Editor) => editor.chain().focus().addRowBefore(),
    isActive: () => false,
    isDisabled: (editor: Editor) => !(editor.can().addRowBefore?.() ?? false),
  },
  addRowAfter: {
    canExecute: (editor: Editor) => editor.can().addRowAfter?.() ?? false,
    execute: (editor: Editor) => editor.chain().focus().addRowAfter(),
    isActive: () => false,
    isDisabled: (editor: Editor) => !(editor.can().addRowAfter?.() ?? false),
  },
  deleteRow: {
    canExecute: (editor: Editor) => editor.can().deleteRow?.() ?? false,
    execute: (editor: Editor) => editor.chain().focus().deleteRow(),
    isActive: () => false,
    isDisabled: (editor: Editor) => !(editor.can().deleteRow?.() ?? false),
  },
  deleteTable: {
    canExecute: (editor: Editor) => editor.can().deleteTable?.() ?? false,
    execute: (editor: Editor) => editor.chain().focus().deleteTable(),
    isActive: () => false,
    isDisabled: (editor: Editor) => !(editor.can().deleteTable?.() ?? false),
  },
} satisfies EditorCustomHandlers

const items = computed<EditorToolbarItem<typeof handlers>[][]>(() => {
  const base: EditorToolbarItem<typeof handlers>[][] = [
    [
      { kind: 'undo', icon: 'i-lucide-undo', tooltip: { text: t('docetra.meetingNotes.toolbar.undo') } },
      { kind: 'redo', icon: 'i-lucide-redo', tooltip: { text: t('docetra.meetingNotes.toolbar.redo') } },
    ],
    [
      {
        icon: 'i-lucide-heading',
        tooltip: { text: t('docetra.meetingNotes.toolbar.headings') },
        content: { align: 'start' },
        items: [
          { kind: 'heading', level: 1, icon: 'i-lucide-heading-1', label: 'H1' },
          { kind: 'heading', level: 2, icon: 'i-lucide-heading-2', label: 'H2' },
          { kind: 'heading', level: 3, icon: 'i-lucide-heading-3', label: 'H3' },
        ],
      },
      {
        icon: 'i-lucide-list',
        tooltip: { text: t('docetra.meetingNotes.toolbar.lists') },
        content: { align: 'start' },
        items: [
          { kind: 'bulletList', icon: 'i-lucide-list', label: t('docetra.meetingNotes.toolbar.bulletList') },
          { kind: 'orderedList', icon: 'i-lucide-list-ordered', label: t('docetra.meetingNotes.toolbar.orderedList') },
        ],
      },
      { kind: 'blockquote', icon: 'i-lucide-text-quote', tooltip: { text: t('docetra.meetingNotes.toolbar.quote') } },
    ],
    [
      { kind: 'mark', mark: 'bold', icon: 'i-lucide-bold', tooltip: { text: t('docetra.meetingNotes.toolbar.bold') } },
      { kind: 'mark', mark: 'italic', icon: 'i-lucide-italic', tooltip: { text: t('docetra.meetingNotes.toolbar.italic') } },
      { kind: 'mark', mark: 'underline', icon: 'i-lucide-underline', tooltip: { text: t('docetra.meetingNotes.toolbar.underline') } },
      { kind: 'mark', mark: 'strike', icon: 'i-lucide-strikethrough', tooltip: { text: t('docetra.meetingNotes.toolbar.strike') } },
      { kind: 'mark', mark: 'code', icon: 'i-lucide-code', tooltip: { text: t('docetra.meetingNotes.toolbar.code') } },
    ],
    [
      {
        icon: 'i-lucide-palette',
        tooltip: { text: t('docetra.meetingNotes.toolbar.textColor') },
        content: { align: 'start' },
        items: [
          ...TEXT_COLORS.map(color => ({
            kind: 'textColor' as const,
            color,
            label: color,
            icon: 'i-lucide-square',
          })),
          {
            kind: 'textColor' as const,
            label: t('docetra.meetingNotes.toolbar.clearColor'),
            icon: 'i-lucide-circle-off',
          },
        ],
      },
      {
        icon: 'i-lucide-highlighter',
        tooltip: { text: t('docetra.meetingNotes.toolbar.highlight') },
        content: { align: 'start' },
        items: [
          ...HIGHLIGHT_COLORS.map(color => ({
            kind: 'highlightColor' as const,
            color,
            label: color,
            icon: 'i-lucide-square',
          })),
          {
            kind: 'highlightColor' as const,
            label: t('docetra.meetingNotes.toolbar.clearHighlight'),
            icon: 'i-lucide-circle-off',
          },
        ],
      },
      {
        icon: 'i-lucide-case-sensitive',
        tooltip: { text: t('docetra.meetingNotes.toolbar.changeCase') },
        content: { align: 'start' },
        items: [
          { kind: 'changeCase', case: 'upper', label: t('docetra.meetingNotes.toolbar.upperCase'), icon: 'i-lucide-case-upper' },
          { kind: 'changeCase', case: 'lower', label: t('docetra.meetingNotes.toolbar.lowerCase'), icon: 'i-lucide-case-lower' },
          { kind: 'changeCase', case: 'title', label: t('docetra.meetingNotes.toolbar.titleCase'), icon: 'i-lucide-case-sensitive' },
        ],
      },
    ],
    [
      {
        icon: 'i-lucide-align-justify',
        tooltip: { text: t('docetra.meetingNotes.toolbar.align') },
        content: { align: 'start' },
        items: [
          { kind: 'textAlign', align: 'left', icon: 'i-lucide-align-left', label: t('docetra.meetingNotes.toolbar.alignLeft') },
          { kind: 'textAlign', align: 'center', icon: 'i-lucide-align-center', label: t('docetra.meetingNotes.toolbar.alignCenter') },
          { kind: 'textAlign', align: 'right', icon: 'i-lucide-align-right', label: t('docetra.meetingNotes.toolbar.alignRight') },
          { kind: 'textAlign', align: 'justify', icon: 'i-lucide-align-justify', label: t('docetra.meetingNotes.toolbar.alignJustify') },
        ],
      },
    ],
    [
      { kind: 'link', icon: 'i-lucide-link', tooltip: { text: t('docetra.meetingNotes.toolbar.link') } },
      { kind: 'image', icon: 'i-lucide-image', tooltip: { text: t('docetra.meetingNotes.toolbar.image') } },
    ],
  ]

  if (enableTables.value) {
    base.push([
      {
        icon: 'i-lucide-table',
        tooltip: { text: t('docetra.meetingNotes.toolbar.table') },
        content: { align: 'start' },
        items: [
          { kind: 'insertTable', icon: 'i-lucide-table', label: t('docetra.meetingNotes.toolbar.insertTable') },
          { kind: 'addColumnBefore', icon: 'i-lucide-between-vertical-start', label: t('docetra.meetingNotes.toolbar.addColumnBefore') },
          { kind: 'addColumnAfter', icon: 'i-lucide-between-vertical-end', label: t('docetra.meetingNotes.toolbar.addColumnAfter') },
          { kind: 'deleteColumn', icon: 'i-lucide-columns-2', label: t('docetra.meetingNotes.toolbar.deleteColumn') },
          { kind: 'addRowBefore', icon: 'i-lucide-between-horizontal-start', label: t('docetra.meetingNotes.toolbar.addRowBefore') },
          { kind: 'addRowAfter', icon: 'i-lucide-between-horizontal-end', label: t('docetra.meetingNotes.toolbar.addRowAfter') },
          { kind: 'deleteRow', icon: 'i-lucide-rows-2', label: t('docetra.meetingNotes.toolbar.deleteRow') },
          { kind: 'deleteTable', icon: 'i-lucide-trash-2', label: t('docetra.meetingNotes.toolbar.deleteTable') },
        ],
      },
    ])
  }

  return base
})

function zoomIn() {
  const next = ZOOM_STEPS.find(step => step > zoom.value)
  if (next != null) zoom.value = next
}

function zoomOut() {
  const prev = [...ZOOM_STEPS].reverse().find(step => step < zoom.value)
  if (prev != null) zoom.value = prev
}

function resetZoom() {
  zoom.value = 100
}

function onImagePicked(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || !editorRef.value) return

  if (!file.type.startsWith('image/')) {
    toast.add({ title: t('docetra.meetingNotes.imageInvalid'), color: 'error' })
    return
  }

  if (file.size > 5 * 1024 * 1024) {
    toast.add({ title: t('docetra.meetingNotes.imageTooLarge'), color: 'error' })
    return
  }

  const reader = new FileReader()
  reader.onload = () => {
    const src = reader.result as string
    if (!src || !editorRef.value) return
    editorRef.value.chain().focus().setImage({ src, alt: file.name }).run()
  }
  reader.readAsDataURL(file)
}

function onEditorCreate({ editor }: { editor: Editor }) {
  editorRef.value = editor
}

onMounted(() => {
  try {
    // Keep tables off until core editor is stable in the modal.
    // TableKit previously caused blank UEditor (duplicate cell selection plugin).
    extensions.value = createRichNoteExtensions()
    enableTables.value = false
    mountKey.value += 1
    ready.value = true
  }
  catch (error: any) {
    console.error('[AppRichTextNote] extension boot failed', error)
    bootError.value = error?.message || 'Editor failed to load'
  }
})
</script>

<template>
  <div
    class="min-h-0"
    :class="fill ? 'flex h-full min-h-64 flex-1 flex-col' : ''"
  >
    <div
      v-if="bootError"
      class="flex min-h-48 flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-error/40 bg-error/5 px-4 text-center text-sm text-error"
    >
      <UIcon name="i-lucide-triangle-alert" class="size-5" />
      <p>{{ bootError }}</p>
    </div>

    <div
      v-else-if="!ready"
      class="flex min-h-48 items-center justify-center rounded-lg border border-dashed border-default bg-elevated/40"
      :class="fill ? 'h-full flex-1' : (minHeightClass || '')"
    >
      <UIcon name="i-lucide-loader-circle" class="size-5 animate-spin text-primary" />
    </div>

    <ClientOnly v-else>
      <div
        class="rich-note flex min-h-0 flex-col overflow-hidden rounded-lg border border-default bg-default"
        :class="[
          disabled ? 'pointer-events-none opacity-60' : '',
          fill ? 'h-full min-h-64 flex-1' : '',
        ]"
        :style="{ '--editor-zoom': String(zoom / 100) }"
      >
        <input
          ref="imageInput"
          type="file"
          accept="image/*"
          class="sr-only"
          @change="onImagePicked"
        >

        <UEditor
          :key="mountKey"
          v-slot="{ editor }"
          v-model="model"
          content-type="html"
          :handlers="handlers"
          :extensions="extensions"
          :image="{ allowBase64: true }"
          :mention="false"
          :placeholder="placeholder || $t('docetra.meetingNotes.placeholder')"
          :editable="!disabled"
          class="flex min-h-0 flex-1 flex-col"
          :ui="{
            root: 'flex min-h-0 flex-1 flex-col overflow-hidden',
            content: [
              'min-h-48 flex-1 overflow-auto px-3 py-2',
              fill ? '' : (minHeightClass || ''),
            ].filter(Boolean).join(' '),
          }"
          @create="onEditorCreate"
        >
          <div class="z-20 flex shrink-0 flex-wrap items-center gap-1 border-b border-default bg-elevated px-2 py-1.5">
            <UEditorToolbar
              v-if="editor"
              :editor="editor"
              :items="items"
              class="min-w-0 flex-1 overflow-x-auto"
            />
            <div
              v-else
              class="flex flex-1 items-center gap-2 px-2 text-xs text-muted"
            >
              <UIcon name="i-lucide-loader-circle" class="size-4 animate-spin" />
              Loading editor…
            </div>

            <div
              class="ml-auto flex shrink-0 items-center gap-0.5 border-s border-default ps-2"
              :title="$t('docetra.meetingNotes.zoom')"
            >
              <UButton
                icon="i-lucide-zoom-out"
                color="neutral"
                variant="ghost"
                size="xs"
                :disabled="zoom <= ZOOM_STEPS[0]"
                :aria-label="$t('docetra.meetingNotes.zoomOut')"
                @click="zoomOut"
              />
              <USelect
                v-model="zoom"
                :items="zoomOptions"
                value-key="value"
                size="xs"
                class="w-20"
              />
              <UButton
                icon="i-lucide-zoom-in"
                color="neutral"
                variant="ghost"
                size="xs"
                :disabled="zoom >= ZOOM_STEPS[ZOOM_STEPS.length - 1]!"
                :aria-label="$t('docetra.meetingNotes.zoomIn')"
                @click="zoomIn"
              />
              <UButton
                icon="i-lucide-rotate-ccw"
                color="neutral"
                variant="ghost"
                size="xs"
                :disabled="zoom === 100"
                :aria-label="$t('docetra.meetingNotes.zoomReset')"
                @click="resetZoom"
              />
            </div>
          </div>
        </UEditor>
      </div>

      <template #fallback>
        <div
          class="flex min-h-48 items-center justify-center rounded-lg border border-dashed border-default bg-elevated/40"
          :class="fill ? 'h-full flex-1' : ''"
        >
          <UIcon name="i-lucide-loader-circle" class="size-5 animate-spin text-primary" />
        </div>
      </template>
    </ClientOnly>
  </div>
</template>

<style scoped>
.rich-note :deep(.ProseMirror) {
  min-height: 12rem;
  outline: none;
  zoom: var(--editor-zoom, 1);
}

@supports not (zoom: 1) {
  .rich-note :deep(.ProseMirror) {
    transform: scale(var(--editor-zoom, 1));
    transform-origin: top left;
    width: calc(100% / var(--editor-zoom, 1));
  }
}

.rich-note :deep(.ProseMirror img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.375rem;
}

.rich-note :deep(table.rich-note-table),
.rich-note :deep(.ProseMirror table) {
  border-collapse: collapse;
  table-layout: fixed;
  width: 100%;
  margin: 0.75rem 0;
  overflow: hidden;
}

.rich-note :deep(.ProseMirror td),
.rich-note :deep(.ProseMirror th) {
  border: 1px solid var(--ui-border);
  min-width: 2.5rem;
  padding: 0.4rem 0.55rem;
  vertical-align: top;
  position: relative;
  box-sizing: border-box;
}

.rich-note :deep(.ProseMirror th) {
  background: var(--ui-bg-elevated);
  font-weight: 600;
}

.rich-note :deep(.ProseMirror .selectedCell::after) {
  content: '';
  position: absolute;
  inset: 0;
  background: color-mix(in oklab, var(--ui-primary) 12%, transparent);
  pointer-events: none;
  z-index: 2;
}

.rich-note :deep(.ProseMirror .column-resize-handle) {
  position: absolute;
  right: -2px;
  top: 0;
  bottom: -2px;
  width: 4px;
  background-color: var(--ui-primary);
  pointer-events: none;
}

.rich-note :deep(.ProseMirror.resize-cursor) {
  cursor: col-resize;
}
</style>

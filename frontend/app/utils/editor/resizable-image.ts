import { mergeAttributes } from '@tiptap/core'
import Image from '@tiptap/extension-image'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import ResizableImageView from '~/components/common/editor/ResizableImageView.vue'

export const ResizableImage = Image.extend({
  name: 'image',
  addAttributes() {
    return {
      ...this.parent?.(),
      width: {
        default: null,
        parseHTML: (element) => {
          const attr = element.getAttribute('width')
          if (attr) return Number.parseInt(attr, 10) || null
          const styleWidth = element.style.width
          if (styleWidth?.endsWith('px')) return Number.parseInt(styleWidth, 10) || null
          return null
        },
        renderHTML: (attributes) => {
          if (!attributes.width) return {}
          return {
            width: attributes.width,
            style: `width: ${attributes.width}px; height: auto;`,
          }
        },
      },
    }
  },
  renderHTML({ HTMLAttributes }) {
    return ['img', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes)]
  },
  addNodeView() {
    return VueNodeViewRenderer(ResizableImageView)
  },
})

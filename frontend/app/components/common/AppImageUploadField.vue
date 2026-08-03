<script setup lang="ts">
const model = defineModel<string | undefined>({ default: undefined })

const props = withDefaults(defineProps<{
  label?: string
  labelKey?: string
  help?: string
  helpKey?: string
  accept?: string
  maxSizeMb?: number
  disabled?: boolean
}>(), {
  accept: 'image/png,image/jpeg,image/webp,image/svg+xml',
  maxSizeMb: 2,
  disabled: false,
})

const { t, te } = useI18n()
const toast = useToast()
const inputRef = ref<HTMLInputElement | null>(null)
const dragOver = ref(false)

const labelText = computed(() => {
  if (props.label) return props.label
  if (props.labelKey && te(props.labelKey)) return t(props.labelKey)
  return t('docetra.common.image')
})

const helpText = computed(() => {
  if (props.help) return props.help
  if (props.helpKey && te(props.helpKey)) return t(props.helpKey)
  return t('docetra.common.imageHelp', { size: props.maxSizeMb })
})

function openPicker() {
  if (props.disabled) return
  inputRef.value?.click()
}

function clear() {
  model.value = undefined
}

async function readFile(file: File) {
  if (!file.type.startsWith('image/')) {
    toast.add({ title: t('docetra.common.imageInvalidType'), color: 'error' })
    return
  }
  if (file.size > props.maxSizeMb * 1024 * 1024) {
    toast.add({ title: t('docetra.common.imageTooLarge', { size: props.maxSizeMb }), color: 'error' })
    return
  }
  const reader = new FileReader()
  const dataUrl = await new Promise<string>((resolve, reject) => {
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('read failed'))
    reader.readAsDataURL(file)
  })
  model.value = dataUrl
}

function onInputChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) void readFile(file)
  input.value = ''
}

function onDrop(event: DragEvent) {
  dragOver.value = false
  if (props.disabled) return
  const file = event.dataTransfer?.files?.[0]
  if (file) void readFile(file)
}
</script>

<template>
  <UFormField :label="labelText" :hint="helpText">
    <div
      class="relative flex min-h-28 cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-default bg-elevated/40 p-4 transition"
      :class="[
        dragOver ? 'border-primary bg-primary/5' : '',
        disabled ? 'pointer-events-none opacity-60' : 'hover:border-primary/50',
      ]"
      @click="openPicker"
      @dragover.prevent="dragOver = true"
      @dragleave.prevent="dragOver = false"
      @drop.prevent="onDrop"
    >
      <template v-if="model">
        <img :src="model" alt="" class="max-h-24 max-w-full object-contain">
        <div class="flex gap-2">
          <UButton size="xs" color="neutral" variant="soft" @click.stop="openPicker">
            {{ t('docetra.common.replace') }}
          </UButton>
          <UButton size="xs" color="error" variant="ghost" @click.stop="clear">
            {{ t('docetra.common.remove') }}
          </UButton>
        </div>
      </template>
      <template v-else>
        <UIcon name="i-lucide-image-up" class="size-6 text-muted" />
        <p class="text-sm text-muted">
          {{ t('docetra.common.dropImage') }}
        </p>
      </template>
    </div>
    <input
      ref="inputRef"
      type="file"
      class="hidden"
      :accept="accept"
      :disabled="disabled"
      @change="onInputChange"
    >
  </UFormField>
</template>

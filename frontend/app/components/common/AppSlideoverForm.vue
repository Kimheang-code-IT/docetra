<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { CalendarDate, parseDate } from '@internationalized/date'
import type { FormField } from '~/types/form'

const open = defineModel<boolean>('open')
type FormDataValue = string | number | boolean | string[] | CalendarDate | undefined | null
type FormDataShape = Record<string, FormDataValue>

const props = defineProps<{
    data?: FormDataShape | null
    title?: string
    submitLabel?: string
    submitLoading?: boolean
    submitDisabled?: boolean
    fields?: FormField[]
}>()

const emit = defineEmits<{
    (e: 'submit', data: Record<string, unknown>): void
}>()

// Internal form state
const formData = ref<FormDataShape>({})
const fieldErrors = ref<Record<string, string>>({})

// Allow Khmer + English letters, numbers, spaces and common punctuation.
const multilingualTextPattern = /^[\u1780-\u17FFa-zA-Z0-9\s.,!?():;'"\-_/&%+@#]*$/

// Fields are now required to be passed as props for maximum flexibility across all pages
const activeFields = computed(() => props.fields || [])

// Watch for data changes to sync form data
watch(() => props.data, (newVal) => {
    if (newVal) {
        // Create a deep copy and handle special types like dates
        const dataCopy: FormDataShape = { ...newVal }
        activeFields.value.forEach(field => {
            if (field.type === 'date' && typeof dataCopy[field.key] === 'string' && dataCopy[field.key]) {
                try {
                    dataCopy[field.key] = parseDate(dataCopy[field.key] as string)
                } catch (e) {
                    console.error('Invalid date format:', dataCopy[field.key])
                    dataCopy[field.key] = undefined
                }
            } else if (field.type === 'permission-tree' && !Array.isArray(dataCopy[field.key])) {
                dataCopy[field.key] = []
            }
        })
        formData.value = dataCopy
    } else {
        // Initialize empty object based on fields to avoid direct undefined access
        const initial: FormDataShape = {}
        activeFields.value.forEach(field => {
            if (field.type === 'select') {
                initial[field.key] = null
            } else if (field.type === 'permission-tree') {
                initial[field.key] = []
            } else if (field.type === 'date') {
                initial[field.key] = undefined
            } else {
                initial[field.key] = ''
            }
        })
        formData.value = initial
    }
}, { immediate: true })

function validateField(field: FormField, value: FormDataValue): string {
    if (field.required) {
        if (field.type === 'date' && !value) return 'This field is required'
        if (field.type === 'select' && (value === undefined || value === null || value === '')) return 'This field is required'
        if (field.type === 'permission-tree' && (!Array.isArray(value) || value.length === 0)) return 'Select at least one page action'
        if ((field.type === 'input' || field.type === 'textarea' || field.type === 'password' || !field.type) && !String(value ?? '').trim()) {
            return 'This field is required'
        }
    }

    if ((field.type === 'input' || field.type === 'textarea' || !field.type) && value != null) {
        const text = String(value)
        if (text && !multilingualTextPattern.test(text)) {
            return 'Only Khmer, English, numbers, and common symbols are allowed'
        }
    }

    return ''
}

function validateAll(): boolean {
    const nextErrors: Record<string, string> = {}
    activeFields.value.forEach((field) => {
        const message = validateField(field, formData.value[field.key])
        if (message) nextErrors[field.key] = message
    })
    fieldErrors.value = nextErrors
    return Object.keys(nextErrors).length === 0
}

function validateOne(field: FormField) {
    const message = validateField(field, formData.value[field.key])
    if (message) fieldErrors.value[field.key] = message
    else delete fieldErrors.value[field.key]
}

function setFieldValue(key: string, value: FormDataValue) {
    formData.value[key] = value
}

function onSave() {
    if (props.submitLoading || props.submitDisabled) return
    if (!validateAll()) return

    // Process form data back to plain objects (e.g. format dates back to string)
    const result: Record<string, unknown> = { ...formData.value }
    activeFields.value.forEach((field) => {
        const value = result[field.key]
        if (field.type === 'date' && value != null && typeof (value as { toString?: () => string }).toString === 'function') {
            result[field.key] = (value as { toString: () => string }).toString()
        }
    })
    emit('submit', result)
}

function onCancel() {
    open.value = false
}
</script>

<template>
    <USlideover v-model:open="open" :dismissible="false" :title="title || $t('components.processData')" class="max-w-md">
        <template #body>
            <div class="flex flex-col space-y-3 px-1 w-full overflow-hidden">
                <template v-for="field in activeFields" :key="field.key">
                    <UFormField class="w-full space-y-1" :error="fieldErrors[field.key]">
                        <template #label>
                            <div class="flex items-center gap-1.5">
                                <span class="font-medium text-highlighted">{{ field.label }}</span>
                                <span v-if="field.required" class="text-error font-bold leading-none -mt-1">*</span>
                            </div>
                        </template>

                        <!-- INPUT TYPE -->
                        <UInput v-if="!field.type || field.type === 'input' || field.type === 'password'"
                            :model-value="(formData[field.key] as any)"
                            :type="field.type === 'password' ? 'password' : 'text'"
                            :placeholder="field.placeholder" size="lg" class="w-full"
                            @update:model-value="(value: any) => setFieldValue(field.key, value)"
                            @blur="validateOne(field)" />

                        <!-- SELECT TYPE -->
                        <USelect v-else-if="field.type === 'select'"
                            :model-value="(formData[field.key] as any)"
                            :items="field.items"
                            value-key="value" size="lg" class="w-full"
                            @update:model-value="(value: any) => { setFieldValue(field.key, value); validateOne(field) }" />

                        <!-- TEXTAREA TYPE -->
                        <UTextarea v-else-if="field.type === 'textarea'"
                            :model-value="(formData[field.key] as any)"
                            :placeholder="field.placeholder" autoresize size="md" class="w-full"
                            @update:model-value="(value: any) => setFieldValue(field.key, value)"
                            @blur="validateOne(field)" />

                        <!-- DATE TYPE -->
                        <UPopover v-else-if="field.type === 'date'" class="w-full">
                            <UButton color="neutral" variant="soft" size="lg"
                                class="w-full justify-start font-normal text-muted-foreground"
                                :label="formData[field.key] != null ? String(formData[field.key]) : (field.placeholder || $t('components.selectDate'))" />
                            <template #content>
                                <UCalendar
                                  :model-value="(formData[field.key] as any)"
                                  class="p-2"
                                  @update:model-value="(value: any) => setFieldValue(field.key, value)"
                                />
                            </template>
                        </UPopover>

                        <!-- PERMISSION TREE TYPE -->
                        <CommonAppPermissionTreeSelect
                            v-else-if="field.type === 'permission-tree'"
                            :model-value="(formData[field.key] as any)"
                            :pages="field.items || []"
                            :actions="field.childItems || []"
                            @update:model-value="(value: any) => setFieldValue(field.key, value)"
                        />
                    </UFormField>
                </template>
            </div>
        </template>

        <template #footer>
            <div class="flex items-center justify-end gap-3 w-full px-1">
                <UButton :label="$t('components.cancel')" color="neutral" variant="soft" @click="onCancel" />
                <UButton :label="submitLabel || $t('components.saveChanges')" color="primary" variant="solid"
                    class="font-semibold shadow-sm px-6" :loading="submitLoading" :disabled="submitDisabled"
                    @click="onSave" />
            </div>
        </template>
    </USlideover>
</template>

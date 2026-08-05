<script setup lang="ts">
/**
 * App Config Display editor: one-row checkboxes, footer line + L/R align, drag order, preview.
 */
import type { AppConfigDisplay, CardDisplayEntityKey } from '~/types/docetra/settings'
import type { CardFooterAlign } from '~/utils/card-fields'
import {
  CARD_DISPLAY_ENTITIES,
  DEFAULT_CARD_FIELDS,
  blocksForEntity,
  catalogForEntity,
  defaultFooterAlign,
  isCardFooterSlot,
  isTitleChromeSlot,
  resolveFooterAlign,
  resolveVisibleSlots,
  splitCardSlots,
} from '~/utils/card-fields'

const model = defineModel<Pick<AppConfigDisplay, 'cardFields' | 'cardFooterAlign'>>({
  default: () => ({ cardFields: {}, cardFooterAlign: {} }),
})

const props = withDefaults(defineProps<{
  disabled?: boolean
}>(), {
  disabled: false,
})

const { t, te } = useI18n()
const selectedEntity = ref<CardDisplayEntityKey>('meetingHistory')

const blocks = computed(() => blocksForEntity(selectedEntity.value))

function slotsFor(entityKey: CardDisplayEntityKey): string[] {
  const raw = model.value?.cardFields?.[entityKey]
  if (!Array.isArray(raw)) return [...DEFAULT_CARD_FIELDS[entityKey]]
  return [...raw]
}

const selectedSlots = computed(() => slotsFor(selectedEntity.value))

const visibleForPreview = computed(() =>
  resolveVisibleSlots(selectedEntity.value, selectedSlots.value),
)

const splitSelected = computed(() =>
  splitCardSlots(selectedEntity.value, selectedSlots.value),
)

const bodyOrderItems = computed(() =>
  [...splitSelected.value.titleChrome, ...splitSelected.value.body].map(id => ({
    id,
    label: slotLabel(id),
  })),
)

const footerOrderItems = computed(() =>
  splitSelected.value.footer.map(id => ({
    id,
    label: slotLabel(id),
  })),
)

function entityLabel(key: CardDisplayEntityKey) {
  const meta = CARD_DISPLAY_ENTITIES.find(e => e.key === key)
  if (meta && te(meta.labelKey)) return t(meta.labelKey)
  return key
}

function slotLabel(slot: string) {
  const key = `docetra.cardSlots.${slot}`
  return te(key) ? t(key) : slot
}

function blockLabel(labelKey: string) {
  return te(labelKey) ? t(labelKey) : labelKey
}

function isChecked(slot: string) {
  return selectedSlots.value.includes(slot)
}

function setEntitySlots(entityKey: CardDisplayEntityKey, next: string[]) {
  const catalog = new Set(catalogForEntity(entityKey))
  model.value = {
    ...model.value,
    cardFields: {
      ...model.value.cardFields,
      [entityKey]: next.filter(s => catalog.has(s)),
    },
  }
}

function setFooterAlign(slot: string, align: CardFooterAlign) {
  if (props.disabled) return
  const entityKey = selectedEntity.value
  model.value = {
    ...model.value,
    cardFooterAlign: {
      ...model.value.cardFooterAlign,
      [entityKey]: {
        ...model.value.cardFooterAlign?.[entityKey],
        [slot]: align,
      },
    },
  }
}

function alignFor(slot: string): CardFooterAlign {
  return resolveFooterAlign(selectedEntity.value, slot, model.value.cardFooterAlign)
}

function toggleSlot(slot: string, checked: boolean | 'indeterminate') {
  if (props.disabled) return
  const entityKey = selectedEntity.value
  const current = [...selectedSlots.value]
  if (checked === true) {
    if (!current.includes(slot)) current.push(slot)
    if (isCardFooterSlot(entityKey, slot) && !model.value.cardFooterAlign?.[entityKey]?.[slot]) {
      setFooterAlign(slot, defaultFooterAlign(slot))
    }
  }
  else {
    const idx = current.indexOf(slot)
    if (idx >= 0) current.splice(idx, 1)
  }
  setEntitySlots(entityKey, current)
}

function onReorderBody(items: Array<{ id: string }>) {
  if (props.disabled) return
  setEntitySlots(selectedEntity.value, [
    ...items.map(i => i.id),
    ...splitSelected.value.footer,
  ])
}

function onReorderFooter(items: Array<{ id: string }>) {
  if (props.disabled) return
  setEntitySlots(selectedEntity.value, [
    ...splitSelected.value.titleChrome,
    ...splitSelected.value.body,
    ...items.map(i => i.id),
  ])
}

function selectAll() {
  if (props.disabled) return
  const catalog = [...catalogForEntity(selectedEntity.value)]
  const current = selectedSlots.value
  const missing = catalog.filter(s => !current.includes(s))
  setEntitySlots(selectedEntity.value, [...current, ...missing])
}

function clearOptional() {
  if (props.disabled) return
  setEntitySlots(selectedEntity.value, [])
}

function resetDefaults() {
  if (props.disabled) return
  setEntitySlots(selectedEntity.value, [...DEFAULT_CARD_FIELDS[selectedEntity.value]])
  model.value = {
    ...model.value,
    cardFooterAlign: {
      ...model.value.cardFooterAlign,
      [selectedEntity.value]: {},
    },
  }
}

function entitySelectedCount(entityKey: CardDisplayEntityKey) {
  return slotsFor(entityKey).length
}

function entityTotalCount(entityKey: CardDisplayEntityKey) {
  return catalogForEntity(entityKey).length
}

const footerAlignMapForPreview = computed(() => model.value.cardFooterAlign || {})
</script>

<template>
  <div class="flex h-[min(70vh,36rem)] min-h-88 overflow-hidden rounded-lg border border-default">
    <div class="grid min-h-0 min-w-0 flex-1 grid-cols-1 lg:grid-cols-12">
      <aside class="min-h-0 overflow-y-auto border-b border-default lg:col-span-3 lg:border-b-0 lg:border-r">
        <ul class="divide-y divide-default">
          <li
            v-for="entity in CARD_DISPLAY_ENTITIES"
            :key="entity.key"
          >
            <button
              type="button"
              class="flex w-full items-center justify-between gap-2 px-3 py-2.5 text-left text-sm transition"
              :class="selectedEntity === entity.key
                ? 'bg-primary/5 font-medium text-highlighted ring-inset ring-1 ring-primary/20'
                : 'text-muted hover:bg-elevated/60 hover:text-highlighted'"
              @click="selectedEntity = entity.key"
            >
              <span class="min-w-0 truncate">{{ entityLabel(entity.key) }}</span>
              <span class="shrink-0 tabular-nums text-[11px] text-muted">
                {{ entitySelectedCount(entity.key) }}/{{ entityTotalCount(entity.key) }}
              </span>
            </button>
          </li>
        </ul>
      </aside>

      <section class="flex min-h-0 min-w-0 flex-col border-b border-default lg:col-span-5 lg:border-b-0 lg:border-r">
        <div class="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-default px-3 py-2">
          <h3 class="min-w-0 truncate text-sm font-semibold text-highlighted">
            {{ entityLabel(selectedEntity) }}
          </h3>
          <div class="flex flex-wrap gap-1">
            <UButton
              size="xs"
              color="neutral"
              variant="ghost"
              :disabled="disabled"
              :label="$t('docetra.settings.cardFieldsSelectAll')"
              @click="selectAll"
            />
            <UButton
              size="xs"
              color="neutral"
              variant="ghost"
              :disabled="disabled"
              :label="$t('docetra.settings.cardFieldsClear')"
              @click="clearOptional"
            />
            <UButton
              size="xs"
              color="neutral"
              variant="soft"
              :disabled="disabled"
              :label="$t('docetra.settings.cardFieldsReset')"
              @click="resetDefaults"
            />
          </div>
        </div>

        <div class="min-h-0 flex-1 space-y-4 overflow-y-auto p-3">
          <p class="text-xs text-muted">
            {{ $t('docetra.settings.cardFieldsTitleAlways') }}
          </p>

          <div
            v-for="block in blocks"
            :key="block.id"
            class="rounded-lg border border-default p-3"
          >
            <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
              {{ blockLabel(block.labelKey) }}
            </p>

            <!-- Footer line marker -->
            <div
              v-if="block.id === 'footer'"
              class="mb-3 flex items-center gap-2"
              aria-hidden="true"
            >
              <div class="h-px flex-1 border-t border-dashed border-default" />
              <span class="text-[10px] uppercase tracking-wide text-muted">
                {{ $t('docetra.settings.cardFieldsFooterLine') }}
              </span>
              <div class="h-px flex-1 border-t border-dashed border-default" />
            </div>

            <!-- One field per row -->
            <div class="flex flex-col gap-1.5">
              <div
                v-for="slot in block.slots"
                :key="slot"
                class="flex items-center gap-2 rounded-md px-1 py-1.5 hover:bg-elevated/50"
                :class="disabled ? 'pointer-events-none opacity-60' : ''"
              >
                <label class="flex min-w-0 flex-1 cursor-pointer items-center gap-2 text-sm text-highlighted">
                  <UCheckbox
                    :model-value="isChecked(slot)"
                    :disabled="disabled"
                    @update:model-value="(v) => toggleSlot(slot, v)"
                  />
                  <span class="min-w-0 truncate">{{ slotLabel(slot) }}</span>
                  <span
                    v-if="isTitleChromeSlot(slot)"
                    class="shrink-0 text-[10px] text-muted"
                  >
                    {{ $t('docetra.settings.cardFieldsTitleRowHint') }}
                  </span>
                </label>

                <div
                  v-if="block.id === 'footer' && isChecked(slot)"
                  class="flex shrink-0 gap-0.5"
                >
                  <UButton
                    size="xs"
                    :color="alignFor(slot) === 'left' ? 'primary' : 'neutral'"
                    :variant="alignFor(slot) === 'left' ? 'soft' : 'ghost'"
                    icon="i-lucide-align-left"
                    :disabled="disabled"
                    :aria-label="$t('docetra.settings.cardFieldsAlignLeft')"
                    @click="setFooterAlign(slot, 'left')"
                  />
                  <UButton
                    size="xs"
                    :color="alignFor(slot) === 'right' ? 'primary' : 'neutral'"
                    :variant="alignFor(slot) === 'right' ? 'soft' : 'ghost'"
                    icon="i-lucide-align-right"
                    :disabled="disabled"
                    :aria-label="$t('docetra.settings.cardFieldsAlignRight')"
                    @click="setFooterAlign(slot, 'right')"
                  />
                </div>
              </div>
            </div>
          </div>

          <div class="rounded-lg border border-default p-3">
            <p class="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">
              {{ $t('docetra.settings.cardFieldsDisplayOrder') }}
            </p>
            <p class="mb-3 text-xs text-muted">
              {{ $t('docetra.settings.cardFieldsDragHint') }}
            </p>

            <CommonAppSortableList
              :items="bodyOrderItems"
              :disabled="disabled"
              @reorder="onReorderBody"
            >
              <template #default="{ item }">
                <p class="py-0.5 text-sm text-highlighted">
                  {{ item.label }}
                </p>
              </template>
              <template #empty>
                {{ $t('docetra.settings.cardFieldsOrderEmpty') }}
              </template>
            </CommonAppSortableList>

            <!-- Visible footer line in order list -->
            <div class="my-3 flex items-center gap-2">
              <div class="h-px flex-1 border-t border-default" />
              <span class="text-[10px] font-semibold uppercase tracking-wide text-muted">
                {{ $t('docetra.settings.cardFieldsFooterLine') }}
              </span>
              <div class="h-px flex-1 border-t border-default" />
            </div>

            <CommonAppSortableList
              :items="footerOrderItems"
              :disabled="disabled"
              @reorder="onReorderFooter"
            >
              <template #default="{ item }">
                <div class="flex items-center justify-between gap-2 py-0.5">
                  <p class="text-sm text-highlighted">
                    {{ item.label }}
                  </p>
                  <span class="text-[10px] uppercase text-muted">
                    {{ alignFor(item.id) === 'right'
                      ? $t('docetra.settings.cardFieldsAlignRight')
                      : $t('docetra.settings.cardFieldsAlignLeft') }}
                  </span>
                </div>
              </template>
              <template #empty>
                {{ $t('docetra.settings.cardFieldsFooterOrderEmpty') }}
              </template>
            </CommonAppSortableList>
          </div>
        </div>
      </section>

      <section class="min-h-0 overflow-y-auto bg-elevated/30 p-3 lg:col-span-4">
        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
          {{ $t('docetra.settings.cardFieldsPreview') }}
        </p>
        <SettingsAppCardFieldPreview
          :entity-key="selectedEntity"
          :visible-slots="visibleForPreview"
          :footer-align-map="footerAlignMapForPreview"
        />
        <p class="mt-3 text-xs text-muted">
          {{ $t('docetra.settings.cardFieldsPreviewHint') }}
        </p>
      </section>
    </div>
  </div>
</template>

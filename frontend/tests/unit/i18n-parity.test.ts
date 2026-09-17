import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

type LocaleTree = { [key: string]: string | LocaleTree }

function load(locale: 'en' | 'km'): LocaleTree {
  const path = fileURLToPath(new URL(`../../i18n/locales/${locale}.json`, import.meta.url))
  return JSON.parse(readFileSync(path, 'utf8')) as LocaleTree
}

function flatten(value: LocaleTree, prefix = '', out = new Map<string, unknown>()): Map<string, unknown> {
  for (const [key, child] of Object.entries(value)) {
    const next = prefix ? `${prefix}.${key}` : key
    if (child && typeof child === 'object' && !Array.isArray(child)) {
      flatten(child as LocaleTree, next, out)
    }
    else {
      out.set(next, child)
    }
  }
  return out
}

const en = flatten(load('en'))
const km = flatten(load('km'))

function named(list: string[]): string[] {
  return list.slice(0, 25)
}

describe('i18n locale parity', () => {
  it('defines every English key in Khmer', () => {
    const missing = [...en.keys()].filter(key => !km.has(key))
    expect(named(missing)).toEqual([])
  })

  it('has no Khmer-only keys missing from English', () => {
    const extra = [...km.keys()].filter(key => !en.has(key))
    expect(named(extra)).toEqual([])
  })

  it('has no empty translation values', () => {
    const emptyEn = [...en].filter(([, value]) => value === '').map(([key]) => key)
    const emptyKm = [...km].filter(([, value]) => value === '').map(([key]) => key)
    expect(named(emptyEn)).toEqual([])
    expect(named(emptyKm)).toEqual([])
  })

  it('keeps string leaves as non-empty strings in both locales', () => {
    const bad: string[] = []
    for (const [key, value] of en) {
      if (typeof value !== 'string') continue
      const translated = km.get(key)
      if (typeof translated !== 'string' || translated.trim() === '') bad.push(key)
    }
    expect(named(bad)).toEqual([])
  })
})

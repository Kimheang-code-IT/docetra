import type { NestedPieGroup } from '~/types/chart'

const INNER_COLORS = ['#4f5f8f', '#6abf4b', '#5070dd', '#e8a838', '#9a6bd3']
const OUTER_PALETTES = [
    ['#61a0a8', '#e06343', '#37a2da', '#32c5e9', '#9fe6b8', '#ffdb5c', '#ff9f7f', '#fb7293'],
    ['#91cc75', '#5ab1ef', '#ffb980', '#d87a80', '#8d98b3', '#e7bcf3', '#8378ea', '#96bfff'],
    ['#fac858', '#9a60b4', '#ea7ccc', '#5470c6', '#73c0de', '#3ba272', '#fc8452', '#9a60b4'],
]

export function nestedPieColors(groups: NestedPieGroup[]) {
    const inner = groups.map((_, i) => INNER_COLORS[i % INNER_COLORS.length]!)
    const outer: string[] = []
    groups.forEach((group, gi) => {
        const palette = OUTER_PALETTES[gi % OUTER_PALETTES.length]!
        group.children.forEach((_, ci) => {
            outer.push(palette[ci % palette.length]!)
        })
    })
    return { inner, outer }
}

export function nestedPieInnerData(groups: NestedPieGroup[], colors: string[]) {
    return groups.map((group, i) => ({
        name: group.name,
        value: group.children.reduce((sum, child) => sum + child.value, 0),
        itemStyle: { color: colors[i] },
    }))
}

export function nestedPieOuterData(groups: NestedPieGroup[], colors: string[]) {
    const data: { name: string; value: number; itemStyle: { color: string } }[] = []
    let colorIndex = 0
    for (const group of groups) {
        for (const child of group.children) {
            data.push({
                name: child.name,
                value: child.value,
                itemStyle: { color: colors[colorIndex++]! },
            })
        }
    }
    return data
}

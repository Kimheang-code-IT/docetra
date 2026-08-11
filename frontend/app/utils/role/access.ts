import type { RolePermissionAction } from '~/utils/role/permissions'

/** Derive an action capability from an entity's canonical `.view` permission. */
export function permissionForAction(
  viewPermission: string,
  action: RolePermissionAction,
): string {
  return viewPermission.endsWith('.view')
    ? `${viewPermission.slice(0, -5)}.${action}`
    : viewPermission
}

import type { SystemRole } from "~/types/system-role";

export const initialData: SystemRole[] = Array.from({ length: 30 }, (_, i) => {
  const id = i + 1;
  const roleNames = ["SuperAdmin", "Finance Admin", "Officer", "Editor", "Viewer"] as const;
  const name = roleNames[i % roleNames.length]!;
  const accessMaps: Record<(typeof roleNames)[number], string[]> = {
    "SuperAdmin": ["ALL_PAGES"],
    "Finance Admin": ["Dashboard", "Total Revenue", "Data Entry", "Exchange Rates"],
    "Officer": ["Data Entry", "Public Service", "Reward"],
    "Editor": ["Dashboard", "History", "Audit Planning"],
    "Viewer": ["Dashboard", "Reports", "Monitoring"]
  };

  return {
    id,
    name: `${name} ${id}`,
    pageAccess: accessMaps[name],
  };
});

import type { SystemUser } from "~/types/system-user";

export const initialData: SystemUser[] = Array.from({ length: 30 }, (_, i) => {
  const id = i + 1;
  const userNames = ["Admin One", "Sok Mean", "Lim Teck", "Keara Vuth", "Chandra Sey", "Dalyna Roeun"] as const;
  const name = userNames[i % userNames.length]!;
  const roleNames = ["SuperAdmin", "Editor", "Officer", "Viewer"] as const;
  const role = roleNames[i % roleNames.length]!;
  const email = `${name.toLowerCase().replace(" ", ".")}@gdme.gov.kh`;

  return {
    id,
    name: `${name} ${id}`,
    role,
    email,
    password: "••••••••",
    lastLogin: `2026-03-${String(20 + (i % 3)).padStart(2, '0')} ${String(8 + (i % 6)).padStart(2, '0')}:30:12`,
  };
});

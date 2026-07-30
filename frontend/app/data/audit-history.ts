import type { AuditLog } from '~/types/audit-log';

export const initialLogs: AuditLog[] = Array.from({ length: 30 }, (_, i) => {
    const id = i + 1;
    const actions = ['Login', 'Logout', 'Create', 'Update', 'Delete', 'Export'];
    const typeAction = actions[i % actions.length] as any;
    const usernames = ['admin1', 'sok.mean', 'lim.teck', 'keara.vuth'];
    const username = usernames[i % usernames.length] as string;

    return {
        id,
        typeAction,
        username,
        date: `2026-03-${String(22 - (i % 5)).padStart(2, '0')} ${String(8 + (i % 10)).padStart(2, '0')}:30:12`,
        description: `${typeAction} action performed by ${username}.`,
        metadata: {
            ip: `192.168.1.${100 + i}`,
            browser: i % 2 === 0 ? 'Chrome 122' : 'Firefox 123',
            target: i % 3 === 0 ? 'settings/role-management' : 'data-entry'
        }
    };
});

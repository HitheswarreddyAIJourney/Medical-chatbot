import type { Role } from "@/lib/api";

const COLORS: Record<Role, { bg: string; text: string; label: string }> = {
  doctor:            { bg: "bg-blue-500/20",   text: "text-blue-300",   label: "Doctor" },
  nurse:             { bg: "bg-teal-500/20",   text: "text-teal-300",   label: "Nurse" },
  billing_executive: { bg: "bg-amber-500/20",  text: "text-amber-300",  label: "Billing" },
  technician:        { bg: "bg-slate-500/20",  text: "text-slate-200",  label: "Technician" },
  admin:             { bg: "bg-violet-500/20", text: "text-violet-300", label: "Admin" },
};

export function roleLabel(role: Role): string {
  return COLORS[role]?.label ?? role;
}

export default function RoleBadge({ role }: { role: Role }) {
  const c = COLORS[role];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ${c.bg} ${c.text} ring-1 ring-inset ring-white/10`}>
      <span className="h-2 w-2 rounded-full bg-current opacity-80" />
      {c.label}
    </span>
  );
}

type Props = {
  label: string;
  value: string;
  subtext?: string;
};

export function KpiCard({ label, value, subtext }: Props) {
  return (
    <div className="glass rounded-2xl p-4 shadow-soft">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-2 font-display text-3xl font-bold text-slate-100">{value}</p>
      {subtext ? <p className="mt-1 text-xs text-slate-400">{subtext}</p> : null}
    </div>
  );
}

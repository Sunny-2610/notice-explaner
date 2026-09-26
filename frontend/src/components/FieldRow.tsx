import { useState } from 'react';

function level(confidence: number | null | undefined): 'high' | 'medium' | 'low' {
  if (confidence == null) return 'medium';
  if (confidence >= 0.85) return 'high';
  if (confidence >= 0.7) return 'medium';
  return 'low';
}

const DOT: Record<'high' | 'medium' | 'low', string> = {
  high: '🟢',
  medium: '🟡',
  low: '🔴',
};

export default function FieldRow({
  icon,
  label,
  value,
  confidence,
}: {
  icon: string;
  label: string;
  value: string;
  confidence?: number | null;
}) {
  const [expanded, setExpanded] = useState(false);
  const lv = level(confidence);
  return (
    <div className="border-b border-border last:border-0">
      <button onClick={() => setExpanded((e) => !e)} className="field-row w-full text-left min-h-[48px]" aria-expanded={expanded}>
        <span className="field-icon" aria-hidden>
          {icon}
        </span>
        <div className="flex-1">
          <p className="field-label">{label}</p>
          <p className="field-value">{value}</p>
        </div>
        <span aria-hidden title={`confidence ${lv}`}>
          {DOT[lv]}
        </span>
      </button>
      {expanded && (
        <p className="pb-3 pl-11 text-sm text-text-secondary">
          🤖 AI-read value{confidence != null ? ` · confidence ${Math.round(confidence * 100)}%` : ''}
        </p>
      )}
    </div>
  );
}

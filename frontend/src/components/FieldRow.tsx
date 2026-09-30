import { useState, type ReactNode } from 'react';
import { STRINGS, type Lang } from '../i18n/strings';

function level(confidence: number | null | undefined): 'high' | 'medium' | 'low' {
  if (confidence == null) return 'medium';
  if (confidence >= 0.85) return 'high';
  if (confidence >= 0.7) return 'medium';
  return 'low';
}

const DOT_COLOR: Record<'high' | 'medium' | 'low', string> = {
  high: '#16A34A',
  medium: '#EA580C',
  low: '#DC2626',
};

export default function FieldRow({
  icon,
  label,
  value,
  confidence,
  lang,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  confidence?: number | null;
  lang: Lang;
}) {
  const [expanded, setExpanded] = useState(false);
  const t = STRINGS[lang];
  const lv = level(confidence);
  const sentence =
    lv === 'high' ? t.confidenceHigh : lv === 'medium' ? t.confidenceMedium : t.confidenceLow;
  return (
    <div className="border-b border-border last:border-0">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="field-row w-full text-left min-h-[48px]"
        aria-expanded={expanded}
      >
        <span className="field-icon" aria-hidden>
          {icon}
        </span>
        <div className="flex-1 min-w-0">
          <p className="field-label">{label}</p>
          <p className="field-value break-words">{value}</p>
        </div>
        <span
          aria-hidden
          title={sentence}
          style={{
            background: DOT_COLOR[lv],
            width: 8,
            height: 8,
            borderRadius: 9999,
            flexShrink: 0,
          }}
        />
      </button>
      {expanded && <p className="conf-sentence">{sentence}</p>}
    </div>
  );
}

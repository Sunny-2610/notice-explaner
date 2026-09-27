import { useMemo, useState } from 'react';
import { AlertTriangle, CalendarClock, FileText } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

/** Split a wall of explanation text into ~3 chronological beats. */
function toBeats(text: string): string[] {
  const parts = text
    .split(/(?<=[.!?।])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
  if (parts.length <= 3) return parts.length ? parts : [text];
  const size = Math.ceil(parts.length / 3);
  return [0, 1, 2].map((i) => parts.slice(i * size, (i + 1) * size).join(' ')).filter(Boolean);
}

const ICONS = [FileText, CalendarClock, AlertTriangle];

export default function ProgressiveExplanation({ text, lang }: { text: string; lang: Lang }) {
  const t = STRINGS[lang];
  const beats = useMemo(() => toBeats(text), [text]);
  const titles = [t.beat1, t.beat2, t.beat3];
  const [step, setStep] = useState(0);
  const isLast = step === beats.length - 1;

  return (
    <article className="card-elevated">
      <div className="stepper-dots" aria-hidden>
        {beats.map((_, i) => (
          <span key={i} className={`dot ${i <= step ? 'dot-active' : ''}`} />
        ))}
      </div>
      <div className="mt-4">
        {(() => {
          const BeatIcon = ICONS[Math.min(step, ICONS.length - 1)];
          return (
            <span className="text-text-secondary" aria-hidden>
              <BeatIcon size={32} strokeWidth={1.75} />
            </span>
          );
        })()}
        <h3 className="stepper-title">{titles[Math.min(step, titles.length - 1)]}</h3>
        <p className="stepper-body">{beats[step]}</p>
      </div>
      {!isLast && (
        <button onClick={() => setStep((s) => s + 1)} className="btn-primary w-full mt-4">
          {t.next}
        </button>
      )}
    </article>
  );
}

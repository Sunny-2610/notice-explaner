import { useMemo, useState } from 'react';
import { FileText, ArrowRight } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

// Renders the REAL backend explanation (prop `text`) in three progressive
// beats. visibleCount reveals ~1/3 of paragraphs per tap so low-literacy
// readers aren't walled by text; the final beat discloses the AI origin line.
// (This component was once hardcoded PM-Kisan mock copy — it must never
// contain document-specific text again; everything comes from `text`.)
export default function ProgressiveExplanation({ text, lang }: { text: string; lang: Lang }) {
  const [step, setStep] = useState(0);
  const t = STRINGS[lang];

  const paragraphs = useMemo(
    () =>
      (text || '')
        .split(/\n\s*\n|\r\n\s*\r\n/)
        .flatMap((p) => p.split(/\n/))
        .map((p) => p.trim())
        .filter(Boolean),
    [text],
  );

  const totalSteps = 3;
  // Reveal progressively: step 0 -> first third, step 1 -> two thirds, step 2 -> all.
  const visibleCount =
    paragraphs.length <= totalSteps
      ? step + 1
      : Math.ceil((paragraphs.length * (step + 1)) / totalSteps);
  const visible = paragraphs.slice(0, Math.max(1, Math.min(paragraphs.length, visibleCount)));
  const done = step >= totalSteps - 1 || visible.length >= paragraphs.length;

  const labels = [t.beat1, t.beat2, t.beat3];

  return (
    <article className="mt-4">
      <div className="flex flex-wrap items-center justify-center gap-y-2 gap-x-1 text-xs sm:text-sm text-gray-500 mb-6 bg-white py-4 px-2 rounded-xl overflow-x-auto">
        {labels.map((label, i) => (
          <span key={label} className="flex items-center gap-1 min-w-0">
            {i > 0 && <span className="h-px bg-gray-300 w-4 sm:w-8 mx-1 sm:mx-2 shrink-0" />}
            <span className="flex items-center gap-1 font-medium min-w-0">
              <span
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 ${
                  i <= step ? 'bg-primary text-white font-bold' : 'bg-gray-100 text-gray-500'
                }`}
              >
                {i + 1}
              </span>
              <span className={`truncate max-w-[90px] sm:max-w-none ${i <= step ? 'font-bold text-primary' : ''}`}>{label}</span>
            </span>
          </span>
        ))}
      </div>

      <div className="mb-4 bg-white border border-gray-100 rounded-xl p-5 space-y-4">
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded bg-blue-50 text-blue-700 text-xs font-semibold">
          <FileText size={14} /> {t.keyFacts}
        </span>
        {visible.map((p, i) => (
          <p key={i} className="text-gray-700 leading-relaxed break-words">
            {p}
          </p>
        ))}
        {!done ? (
          <button
            onClick={() => setStep((s) => Math.min(totalSteps - 1, s + 1))}
            className="bg-primary hover:bg-primary-hover text-white px-6 py-3 rounded-xl font-medium flex items-center justify-center gap-2 w-full transition-colors shadow-sm"
          >
            {t.next} <ArrowRight size={18} />
          </button>
        ) : (
          <p className="text-xs text-gray-400">{t.aiDisclosureLine}</p>
        )}
      </div>
    </article>
  );
}

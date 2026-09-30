import { useMemo, useState } from 'react';
import { FileText, ArrowRight } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

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
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6 bg-white py-4 px-1 rounded-xl">
        {labels.map((label, i) => (
          <span key={label} className="flex items-center gap-2">
            {i > 0 && <span className="h-px bg-gray-300 w-8 mx-2" />}
            <span className="flex items-center gap-1 font-medium">
              <span
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                  i <= step ? 'bg-primary text-white font-bold' : 'bg-gray-100 text-gray-500'
                }`}
              >
                {i + 1}
              </span>
              <span className={i <= step ? 'font-bold text-primary' : ''}>{label}</span>
            </span>
          </span>
        ))}
      </div>

      <div className="mb-4 bg-white border border-gray-100 rounded-xl p-5 space-y-4">
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded bg-blue-50 text-blue-700 text-xs font-semibold">
          <FileText size={14} /> {t.keyFacts}
        </span>
        {visible.map((p, i) => (
          <p key={i} className="text-gray-700 leading-relaxed">
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

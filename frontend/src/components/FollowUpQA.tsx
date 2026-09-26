import { useState } from 'react';
import { STRINGS, type Lang } from '../i18n/strings';
import { askQuestion } from '../lib/api';

const SUGGESTED: Record<Lang, string[]> = {
  hi: [
    'अगर मैं इसे नजरअंदाज कर दूं तो क्या होगा?',
    'मुझे कहाँ भुगतान करना है?',
    'समन का क्या मतलब है?',
  ],
  mr: [
    'दुर्लक्ष केल्यास काय होईल?',
    'मला कुठे भरणा करावा लागेल?',
    'समन्स म्हणजे काय?',
  ],
};

export default function FollowUpQA({ jobId, lang }: { jobId: string; lang: Lang }) {
  const t = STRINGS[lang];
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (q: string) => {
    const text = q.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(null);
    try {
      const r = await askQuestion(jobId, text);
      setAnswer(r.answer);
      setQuestion('');
    } catch {
      setError(t.failed);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card space-y-3">
      <h3 className="text-base font-semibold">{t.askTitle}</h3>
      <div className="flex flex-wrap gap-2">
        {SUGGESTED[lang].map((s) => (
          <button
            key={s}
            onClick={() => submit(s)}
            disabled={busy}
            className="chip-info min-h-[48px] px-4 text-sm text-left disabled:opacity-40"
          >
            {s}
          </button>
        ))}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(question);
        }}
        className="flex gap-2"
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={t.askPlaceholder}
          aria-label={t.askTitle}
          className="flex-1 min-h-[48px] rounded-xl border-2 border-border px-4 text-base bg-white placeholder:text-text-muted"
        />
        <button type="submit" disabled={!question.trim() || busy} className="btn-primary disabled:opacity-40">
          {busy ? '…' : t.askButton}
        </button>
      </form>
      {error && <p className="text-sm text-error">{error}</p>}
      {answer && (
        <article className="rounded-xl bg-surface p-4 text-base leading-7 whitespace-pre-line">
          {answer}
        </article>
      )}
    </section>
  );
}

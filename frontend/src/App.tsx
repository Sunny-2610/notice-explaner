import { useState } from 'react';
import ReviewQueue from './components/ReviewQueue';
import VoicePlayer from './components/VoicePlayer';
import { submitDocument } from './lib/api';
import { useJobPoll } from './hooks/useJobPoll';
import { STRINGS, type Lang } from './i18n/strings';

export default function App() {
  const [tab, setTab] = useState<'explain' | 'review'>('explain');
  const [lang, setLang] = useState<Lang>('hi');
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const t = STRINGS[lang];
  const { result } = useJobPoll(jobId);

  const onSubmit = async () => {
    if (!file) return;
    setBusy(true);
    setSubmitError(null);
    try {
      if (file.size > 10 * 1024 * 1024) throw new Error(t.badFile);
      if (!['image/jpeg', 'image/png'].includes(file.type)) throw new Error(t.badFile);
      const r = await submitDocument(file, lang);
      setJobId(r.jobId);
    } catch {
      setSubmitError(t.badFile);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral text-on-surface">
      {/* Top navigation — quiet, low-emphasis per design.md */}
      <header className="border-b border-border">
        <div className="mx-auto max-w-5xl px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-primary" aria-hidden />
            <span className="text-[15px] font-medium tracking-[-0.08px]">Yojana Mitra</span>
            <span className="chip ml-2 hidden sm:inline-block">Notice Explainer</span>
          </div>
          <nav className="flex gap-6">
            <button
              onClick={() => setTab('explain')}
              className={`nav-link hover:text-on-surface ${tab === 'explain' ? 'text-on-surface' : ''}`}
            >
              Explain
            </button>
            <button
              onClick={() => setTab('review')}
              className={`nav-link hover:text-on-surface ${tab === 'review' ? 'text-on-surface' : ''}`}
            >
              Review
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 pb-16">
        {tab === 'review' ? (
          <ReviewQueue />
        ) : (
          <>
            {/* Hero — wide, centered, breathing room above the fold */}
            <section className="pt-28 pb-8 text-center max-w-2xl mx-auto">
              <h1
                className="font-medium text-on-surface"
                style={{ fontSize: 33, lineHeight: '40px', letterSpacing: '-0.24px' }}
              >
                {t.title}
              </h1>
              <p className="mt-4 text-[15px] leading-6 text-text-muted">{t.upload}</p>
              <div className="mt-6 flex justify-center gap-2">
                {(['hi', 'mr'] as Lang[]).map((l) => (
                  <button
                    key={l}
                    onClick={() => setLang(l)}
                    className={`h-[44px] px-5 rounded-full text-base ${
                      lang === l
                        ? 'bg-secondary text-neutral font-medium'
                        : 'bg-transparent text-on-surface border border-border'
                    }`}
                  >
                    {l === 'hi' ? 'हिंदी' : 'मराठी'}
                  </button>
                ))}
              </div>
            </section>

            {/* App panel — compact density inside */}
            <section className="card max-w-2xl mx-auto">
              <label className="block mb-2 text-[15px] font-medium">{t.language} / Upload</label>
              <input
                type="file"
                accept="image/jpeg,image/png"
                capture="environment"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="input-dark block w-full min-h-[48px] mb-4 text-[15px] file:mr-4 file:rounded-full file:border-0 file:bg-secondary file:text-neutral file:px-4 file:py-2 file:text-sm file:font-medium"
              />
              {file && (
                <p className="mb-4 text-sm text-text-muted truncate">
                  {file.name} — {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              )}
              <button
                onClick={onSubmit}
                disabled={!file || busy}
                className="btn-primary w-full min-h-[44px] text-base disabled:opacity-40"
              >
                {busy ? '…' : t.submit}
              </button>
              {submitError && <p className="mt-3 text-sm text-error">{submitError}</p>}
              {jobId && !result && <p className="mt-6 text-[15px] text-text-muted">{t.waiting}</p>}
            </section>

            {result && (
              <section className="mt-6 space-y-4 max-w-2xl mx-auto">
                <div className="flex items-center gap-2">
                  <span className="chip">Status: {result.status}</span>
                  {result.jobId && (
                    <span className="text-xs text-text-muted font-mono truncate">{result.jobId}</span>
                  )}
                </div>
                {result.escalation.flagged && (
                  <div className="card border-l-2 border-l-error">
                    <p className="text-[15px] leading-6 flex gap-2">
                      <span className="inline-block h-2 w-2 mt-2 rounded-full bg-error shrink-0" />
                      {t.escalation}
                    </p>
                  </div>
                )}
                {result.status === 'awaiting_review' && result.errorCode === 'E-201' && (
                  <div className="card border-l-2 border-l-warning">
                    <p className="text-[15px] text-warning">{t.unsupported}</p>
                  </div>
                )}
                {result.status === 'awaiting_review' && result.errorCode !== 'E-201' && (
                  <div className="card border-l-2 border-l-warning">
                    <p className="text-[15px] text-warning">{t.underReview}</p>
                  </div>
                )}
                {result.status === 'failed' && (
                  <div className="card border-l-2 border-l-error">
                    <p className="text-[15px] text-error">{t.failed}</p>
                  </div>
                )}
                {result.fields?.issuingAuthority && (
                  <dl className="card space-y-2 text-[15px] leading-6">
                    <div>
                      <dt className="inline text-text-muted">Authority: </dt>
                      <dd className="inline">{result.fields.issuingAuthority}</dd>
                    </div>
                    {result.fields.deadlineDate && (
                      <div>
                        <dt className="inline text-text-muted">Deadline: </dt>
                        <dd className="inline">{result.fields.deadlineDate}</dd>
                      </div>
                    )}
                    {result.fields.amountOwed != null && (
                      <div>
                        <dt className="inline text-text-muted">Amount: </dt>
                        <dd className="inline">{result.fields.amountOwed}</dd>
                      </div>
                    )}
                    {result.fields.citedSection && (
                      <div>
                        <dt className="inline text-text-muted">Section: </dt>
                        <dd className="inline">{result.fields.citedSection}</dd>
                      </div>
                    )}
                    {result.fields.requiredAction && (
                      <p className="pt-2 text-text-muted">{result.fields.requiredAction}</p>
                    )}
                  </dl>
                )}
                {result.explanation && (
                  <article className="card text-[15px] leading-6">{result.explanation}</article>
                )}
                {result.status === 'completed' && <VoicePlayer jobId={result.jobId} lang={lang} />}
                <footer className="text-xs leading-4 text-text-muted">{t.disclaimer}</footer>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}

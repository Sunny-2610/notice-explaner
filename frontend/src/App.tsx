import { useEffect, useRef, useState } from 'react';
import ReviewQueue from './components/ReviewQueue';
import HowItWorks from './components/HowItWorks';
import Faq from './components/Faq';
import VoicePlayer from './components/VoicePlayer';
import VoiceRecorder from './components/VoiceRecorder';
import LiveCamera from './components/LiveCamera';
import VerdictBanner from './components/VerdictBanner';
import ProgressiveExplanation from './components/ProgressiveExplanation';
import FollowUpQA from './components/FollowUpQA';
import FieldRow from './components/FieldRow';
import ProcessingStages from './components/ProcessingStages';
import { submitDocument } from './lib/api';
import { useJobPoll } from './hooks/useJobPoll';
import { STRINGS, type Lang } from './i18n/strings';

type Tab = 'explain' | 'how' | 'faq' | 'review';

export default function App() {
  const [tab, setTab] = useState<Tab>('explain');
  const [lang, setLang] = useState<Lang>('hi');
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);
  const fileRef = useRef<HTMLInputElement>(null);
  const t = STRINGS[lang];
  const { result, error: pollError } = useJobPoll(jobId);

  useEffect(() => {
    const go = () => setOnline(navigator.onLine);
    window.addEventListener('online', go);
    window.addEventListener('offline', go);
    return () => {
      window.removeEventListener('online', go);
      window.removeEventListener('offline', go);
    };
  }, []);

  const submitFile = async (f: File) => {
    setBusy(true);
    setSubmitError(null);
    try {
      if (f.size > 10 * 1024 * 1024) throw new Error(t.badFile);
      if (!['image/jpeg', 'image/png'].includes(f.type)) throw new Error(t.badFile);
      const r = await submitDocument(f, lang);
      setFile(f);
      setJobId(r.jobId);
    } catch {
      setSubmitError(t.badFile);
    } finally {
      setBusy(false);
    }
  };

  const retry = () => {
    if (file) {
      setJobId(null);
      submitFile(file);
    }
  };

  const terminal = result && ['completed', 'awaiting_review', 'failed'].includes(result.status);

  return (
    <div className="min-h-screen bg-bg text-text-primary">
      {!online && <div className="offline-banner">{t.offline}</div>}

      {/* Header: brand + always-visible language selector */}
      <header className="border-b border-border">
        <div className="mx-auto max-w-xl px-4 h-16 flex items-center justify-between">
          <button onClick={() => setTab('explain')} className="text-lg font-bold">
            Yojana Mitra
          </button>
          <div className="flex rounded-xl border-2 border-border overflow-hidden" role="group" aria-label={t.language}>
            {(['hi', 'mr'] as Lang[]).map((l) => (
              <button
                key={l}
                onClick={() => setLang(l)}
                className={`min-h-[48px] px-4 text-base font-medium ${
                  lang === l ? 'bg-primary text-white' : 'bg-white text-text-secondary'
                }`}
              >
                {l === 'hi' ? 'हिंदी' : 'मराठी'}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-xl px-4 pb-16">
        {tab === 'review' ? (
          <ReviewQueue lang={lang} />
        ) : tab === 'how' ? (
          <HowItWorks lang={lang} />
        ) : tab === 'faq' ? (
          <Faq lang={lang} />
        ) : (
          <>
            {/* Compact hero — above the fold on mobile */}
            <section className="pt-8 pb-6 text-center">
              <h1 className="text-2xl font-bold">{t.heroTitle}</h1>
              <p className="mt-1 text-sm text-text-secondary">{t.heroSub}</p>
            </section>

            {showCamera ? (
              <LiveCamera
                lang={lang}
                onCapture={(f) => {
                  setShowCamera(false);
                  submitFile(f);
                }}
                onFallback={() => {
                  setShowCamera(false);
                  fileRef.current?.click();
                }}
                onClose={() => setShowCamera(false)}
              />
            ) : (
              <button
                onClick={() => setShowCamera(true)}
                className="camera-card"
                aria-label={t.cameraTitle}
                disabled={busy}
              >
                <div className="camera-icon" aria-hidden>
                  📷
                </div>
                <h3 className="camera-title">{t.cameraTitle}</h3>
                <p className="camera-subtitle">{t.cameraSub}</p>
                <span className="camera-cta">{t.cameraCta}</span>
              </button>
            )}

            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png"
              capture="environment"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) submitFile(f);
                e.target.value = '';
              }}
            />
            {submitError && (
              <div className="card mt-4">
                <p className="text-sm text-error">{submitError}</p>
                <button onClick={() => fileRef.current?.click()} className="btn-secondary w-full mt-3">
                  {t.retry}
                </button>
              </div>
            )}

            <div className="flex items-center gap-3 my-4" aria-hidden>
              <span className="flex-1 border-t border-border" />
              <span className="text-sm text-text-muted">{t.or}</span>
              <span className="flex-1 border-t border-border" />
            </div>

            <VoiceRecorder jobId={jobId} lang={lang} />

            {/* Processing / result */}
            {jobId && !terminal && !pollError && (
              <div className="mt-4">
                <ProcessingStages status={result?.status ?? 'queued'} lang={lang} />
              </div>
            )}
            {jobId && !terminal && !result && (
              <div className="mt-4 space-y-2" aria-hidden>
                <div className="skeleton h-16" />
                <div className="skeleton h-24" />
              </div>
            )}
            {pollError && (
              <div className="card mt-4">
                <p className="text-sm text-error">{pollError}</p>
                <button onClick={retry} className="btn-secondary w-full mt-3" disabled={!file}>
                  {t.retry}
                </button>
              </div>
            )}

            {terminal && result && (
              <section className="mt-4 space-y-4">
                {result.status === 'completed' && (
                  <>
                    <VerdictBanner escalated={result.escalation.flagged} lang={lang} />
                    {result.explanation && (
                      <ProgressiveExplanation text={result.explanation} lang={lang} />
                    )}
                    {result.explanation && <FollowUpQA jobId={result.jobId} lang={lang} />}
                    {(result.fields?.issuingAuthority ||
                      result.fields?.deadlineDate ||
                      result.fields?.amountOwed != null) && (
                      <div className="card">
                        <h3 className="text-base font-semibold mb-1">{t.keyFacts}</h3>
                        {result.fields.issuingAuthority && (
                          <FieldRow
                            icon="🏛️"
                            label="Authority"
                            value={result.fields.issuingAuthority}
                            confidence={result.classificationConfidence}
                          />
                        )}
                        {result.fields.deadlineDate && (
                          <FieldRow
                            icon="📅"
                            label="Deadline"
                            value={result.fields.deadlineDate}
                            confidence={result.classificationConfidence}
                          />
                        )}
                        {result.fields.amountOwed != null && (
                          <FieldRow
                            icon="💰"
                            label="Amount"
                            value={String(result.fields.amountOwed)}
                            confidence={result.classificationConfidence}
                          />
                        )}
                      </div>
                    )}
                    {(result.fields?.citedSection || result.fields?.requiredAction) && (
                      <details className="card">
                        <summary className="cursor-pointer font-medium min-h-[48px] inline-flex items-center">
                          {t.details}
                        </summary>
                        <div className="mt-2 space-y-1 text-base">
                          {result.fields.citedSection && <p>📖 {result.fields.citedSection}</p>}
                          {result.fields.requiredAction && <p>✅ {result.fields.requiredAction}</p>}
                        </div>
                      </details>
                    )}
                    <VoicePlayer jobId={result.jobId} lang={lang} />
                  </>
                )}
                {result.status === 'awaiting_review' && result.errorCode === 'E-201' && (
                  <div className="card text-center space-y-3">
                    <p className="chip-warning self-center">E-201</p>
                    <p className="text-base">{t.unsupported}</p>
                    <button onClick={() => fileRef.current?.click()} className="btn-primary w-full">
                      {t.retry}
                    </button>
                  </div>
                )}
                {result.status === 'awaiting_review' && result.errorCode !== 'E-201' && (
                  <div className="card">
                    <p className="chip-warning self-start">{result.errorCode ?? 'review'}</p>
                    <p className="text-base mt-2">{t.underReview}</p>
                  </div>
                )}
                {result.status === 'failed' && (
                  <div className="card text-center space-y-3">
                    <p className="text-base text-error">{t.failed}</p>
                    <button onClick={retry} className="btn-primary w-full" disabled={!file}>
                      {t.retry}
                    </button>
                  </div>
                )}
              </section>
            )}

            {/* Disclaimer: quiet, always visible */}
            <div className="disclaimer mt-6">{t.disclaimer}</div>
          </>
        )}
      </main>

      {/* Footer: secondary nav + reviewer surface */}
      <footer className="border-t border-border">
        <nav className="mx-auto max-w-xl px-4 py-2 flex justify-center gap-1">
          {(
            [
              ['how', lang === 'mr' ? 'कसे काम करते' : 'कैसे काम करता है'],
              ['faq', 'FAQ'],
              ['review', t.reviewer],
            ] as [Tab, string][]
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`nav-link text-sm ${tab === key ? 'nav-link-active' : ''}`}
            >
              {label}
            </button>
          ))}
        </nav>
      </footer>
    </div>
  );
}

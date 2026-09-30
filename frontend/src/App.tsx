import { useEffect, useRef, useState } from 'react';
import { BookOpen, Calendar, Camera, CheckCircle2, IndianRupee, Landmark, Upload, Languages, HelpCircle, ShieldCheck, FileText, QrCode } from 'lucide-react';
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
import LegalAidCard from './components/LegalAidCard';
import ReminderCard from './components/ReminderCard';
import ProcessingStages from './components/ProcessingStages';
import { submitDocument } from './lib/api';
import { formatCurrency, formatDate } from './lib/format';
import { useJobStream as useJobPoll } from './hooks/useJobStream';
import { STRINGS, type Lang } from './i18n/strings';

type Tab = 'explain' | 'how' | 'faq' | 'review';

function initialLang(): Lang {
  try {
    const saved = localStorage.getItem('ym_lang');
    if (saved === 'hi' || saved === 'mr' || saved === 'en') return saved;
  } catch {
    /* storage unavailable — fall through to navigator default */
  }
  if (typeof navigator !== 'undefined' && navigator.language?.toLowerCase().startsWith('mr'))
    return 'mr';
  if (typeof navigator !== 'undefined' && navigator.language?.toLowerCase().startsWith('en'))
    return 'en';
  return 'hi';
}

const LANG_OPTIONS: { value: Lang; label: string }[] = [
  { value: 'hi', label: 'हिंदी' },
  { value: 'mr', label: 'मराठी' },
  { value: 'en', label: 'English' },
];

export default function App() {
  const [tab, setTab] = useState<Tab>('explain');
  const [lang, setLang] = useState<Lang>(initialLang);
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);
  // Home-screen voice transcript waiting for the job to complete — then
  // FollowUpQA auto-submits it once, so the mic never goes nowhere.
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const desktopFileRef = useRef<HTMLInputElement>(null);
  const t = STRINGS[lang];
  const { result, error: pollError, timedOut } = useJobPoll(jobId);

  useEffect(() => {
    try {
      localStorage.setItem('ym_lang', lang);
    } catch {
      /* storage unavailable — language just won't persist */
    }
    document.documentElement.lang = lang;
  }, [lang]);

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
    setPendingQuestion(null);
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
      <header className="bg-white border-b border-border sticky top-0 z-50">
        <div className="mx-auto max-w-7xl px-4 h-16 flex items-center justify-between">
          <button onClick={() => setTab('explain')} className="flex items-center gap-3">
             <div className="bg-primary text-white p-2 rounded-xl flex items-center justify-center">
               <Landmark size={24} strokeWidth={2} />
             </div>
              <div className="flex flex-col text-left text-text-primary">
                <span className="text-lg font-bold leading-tight">योजना मित्र / Yojana Mitra</span>
                <span className="text-xs text-text-secondary hidden sm:block">{t.brandSub}</span>
              </div>
           </button>
          <nav className="hidden lg:flex items-center gap-6 font-medium text-sm text-text-secondary">
            <button onClick={() => setTab('explain')} className="text-primary border-b-2 border-primary pb-1">{t.navSchemes}</button>
            <button onClick={() => setTab('how')} className="hover:text-primary transition-colors">{t.navEligibility}</button>
            <button onClick={() => setTab('faq')} className="hover:text-primary transition-colors">{t.navSupport}</button>
          </nav>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 px-4 py-2 rounded-full border border-border hover:bg-gray-50 transition-colors text-sm font-medium text-text-primary cursor-pointer">
              <Languages size={18} className="text-primary" />
              <span className="sr-only">{t.language}</span>
              <select
                value={lang}
                onChange={(e) => setLang(e.target.value as Lang)}
                aria-label={t.language}
                className="bg-transparent outline-none cursor-pointer text-text-primary font-medium"
              >
                {LANG_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <button onClick={() => setTab('review')} className="hidden sm:flex items-center gap-2 text-sm font-medium text-text-secondary hover:text-primary transition-colors">
              <HelpCircle size={18} />
              <span>{t.reviewer}</span>
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-xl lg:max-w-4xl px-4 pb-16">
        {tab === 'review' ? (
          <ReviewQueue lang={lang} />
        ) : tab === 'how' ? (
          <HowItWorks lang={lang} />
        ) : tab === 'faq' ? (
          <Faq lang={lang} />
        ) : (
          <>
            {/* Updated Hero Section */}
            <section className="pt-10 pb-8 text-center flex flex-col items-center">
              <div className="bg-[#E6F7F4] text-teal-700 rounded-full px-4 py-1 flex items-center gap-2 text-sm font-medium mb-6">
                <span className="bg-teal-500 rounded-full w-2 h-2 inline-block"></span>
                {t.heroBadge}
              </div>
              <h1 className="text-3xl md:text-4xl font-bold text-[#111827]">{t.heroHeading}</h1>
              <p className="mt-4 text-base md:text-lg text-text-secondary max-w-2xl mx-auto">
                {t.heroDesc}
              </p>
            </section>

            {/* Camera and voice are equal-weight peers — no "or" divider demoting voice.
                Desktop (≥1024px) switches to an upload-first two-column treatment via
                pure CSS visibility toggling; the camera-capture screen stays centered. */}
            {showCamera ? (
              <div className="mx-auto w-full max-w-xl">
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
              </div>
            ) : (
              <>
                {/* Mobile: camera-first, stacked */}
                <div className="grid gap-3 lg:hidden">
                  <button
                    onClick={() => setShowCamera(true)}
                    className="camera-card"
                    aria-label={t.cameraTitle}
                    disabled={busy}
                  >
                    <div className="camera-icon text-text-secondary" aria-hidden>
                      <Camera size={48} strokeWidth={1.75} />
                    </div>
                    <h3 className="camera-title">{t.cameraTitle}</h3>
                    <p className="camera-subtitle">{t.cameraSub}</p>
                    <span className="camera-cta">{t.cameraCta}</span>
                  </button>
                  <VoiceRecorder jobId={jobId} lang={lang} variant="hero" onTranscript={setPendingQuestion} />
                </div>
                {/* Desktop: upload-first peer grid (QR-to-mobile flow intentionally
                    omitted — no shareable-link scheme exists yet). */}
                <div className="hidden lg:grid lg:grid-cols-2 lg:gap-8 max-w-5xl mx-auto">
                  
                  {/* Left Column - Upload */}
                  <div className="flex flex-col gap-4">
                    <div className="camera-card cursor-default border-dashed border-gray-300 bg-white shadow-sm p-8 flex flex-col items-center flex-grow justify-center relative">
                      <div className="bg-primary-light p-4 rounded-xl mb-4">
                        <Upload size={32} strokeWidth={2} className="text-primary" />
                      </div>
                      <h3 className="text-xl font-bold text-text-primary mb-2">{t.uploadTitle}</h3>
                      <p className="text-sm text-text-secondary mb-4 text-center">{t.uploadSub}</p>
                      
                      <div className="bg-gray-50 flex items-center gap-2 px-3 py-1.5 rounded-md mb-6 border border-gray-100 text-xs text-text-secondary">
                        <FileText size={14} /> {t.uploadFormats}
                      </div>

                      <button
                        onClick={() => desktopFileRef.current?.click()}
                        className="btn-primary flex items-center gap-2 w-full max-w-[240px] justify-center shadow-md shadow-primary/20"
                        disabled={busy}
                      >
                        <Upload size={18} /> {t.chooseFile}
                      </button>
                      <p className="mt-6 text-sm text-text-secondary">{t.dragDrop}</p>
                    </div>
                    
                     <button onClick={() => setShowCamera(true)} className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between text-text-primary hover:bg-gray-50 transition-colors shadow-sm font-medium group">
                       <span className="flex items-center gap-3">
                         <QrCode className="text-text-primary" size={20} />
                         {t.scanPhone}
                       </span>
                       <span className="text-gray-400 group-hover:text-primary transition-colors text-xl">→</span>
                    </button>
                  </div>

                  {/* Right Column - Voice */}
                  <VoiceRecorder jobId={jobId} lang={lang} variant="hero" onTranscript={setPendingQuestion} />
                </div>
                
                {/* Featues row below hero */}
                <div className="hidden lg:grid grid-cols-3 gap-6 max-w-5xl mx-auto mt-8 mb-6">
                   <div className="feature-chip text-text-primary">
                      <ShieldCheck className="text-blue-500" size={20} /> {t.featSecure}
                   </div>
                   <div className="feature-chip text-text-primary">
                      <FileText className="text-indigo-500" size={20} /> {t.featSimple}
                   </div>
                   <div className="feature-chip text-text-primary">
                      <HelpCircle className="text-primary" size={20} /> {t.featReview}
                   </div>
                </div>
              </>
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
            {/* Desktop picker: same flow, no capture hint for file pickers */}
            <input
              ref={desktopFileRef}
              type="file"
              accept="image/jpeg,image/png"
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

            {/* Processing screen: stays centered at mobile max-width on desktop */}
            <div className="mx-auto w-full max-w-xl">
              {jobId && !terminal && !pollError && !timedOut && (
                <div className="mt-4 flex flex-col items-center">
                  <ProcessingStages status={result?.status ?? 'queued'} lang={lang} />
                  
                  {/* Extra layout specified in Figma */}
                   <div className="w-full mt-6 bg-white border border-gray-100 shadow-sm rounded-xl px-4 py-3 flex gap-3 text-left">
                     <ShieldCheck className="text-[#0DA883] shrink-0 fill-[#0DA883]/10" size={24} />
                     <p className="text-sm text-gray-600"><strong className="text-gray-900">{t.dataSecureTitle}</strong> {t.dataSecureBody}</p>
                  </div>
                  
                  <button onClick={() => setJobId(null)} className="mt-8 mb-6 text-gray-600 font-bold text-sm bg-transparent hover:bg-gray-100 px-6 py-2 rounded-full transition-colors">
                     {t.cancelAnalysis}
                  </button>
                </div>
              )}
              {jobId && timedOut && !terminal && (
                <div className="card mt-4 text-center space-y-3">
                  <p className="text-base">{t.timedOutMessage}</p>
                  <button onClick={retry} className="btn-secondary w-full" disabled={!file}>
                    {t.retry}
                  </button>
                </div>
              )}
              {jobId && !terminal && !result && (
                <div className="mt-4 space-y-2" aria-hidden>
                  <div className="skeleton h-16" />
                  <div className="skeleton h-24" />
                </div>
              )}
            </div>
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
                  <div className="max-w-6xl mx-auto w-full">
                    {/* Header Row */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 mt-2">
                      <div className="text-sm font-medium text-gray-500 flex items-center gap-2">
                         <span className="text-gray-400">←</span> {t.home} <span className="text-gray-300">/</span> <span className="text-gray-900">{t.resultTitle}</span>
                      </div>
                      <div className="text-xs text-gray-400 flex items-center gap-1 mt-2 sm:mt-0">
                        <ShieldCheck size={14} /> {t.securePortal}
                      </div>
                    </div>

                    <div className="lg:grid lg:grid-cols-[1.6fr_1fr] lg:gap-6 lg:items-start space-y-6 lg:space-y-0">
                      
                      {/* Left Column */}
                      <div className="space-y-4">
                        {/* Summary Header Pill */}
                        <div className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex justify-between items-center text-sm shadow-sm">
                           <div className="font-semibold text-gray-800 flex items-center gap-2"><FileText size={16} className="text-primary" /> {t.docNo}: {result.jobId?.split('-')[0] || '—'}</div>
                           <div className="text-gray-500 flex items-center gap-2"><Calendar size={16} /> {t.dateLabel}: {result.fields?.deadlineDate ? formatDate(result.fields.deadlineDate, lang) : '—'}</div>
                        </div>

                        <VerdictBanner escalated={result.escalation.flagged} lang={lang} />
                        
                        <div className="bg-blue-50 text-blue-800 text-xs py-2 px-4 rounded-lg flex items-center justify-between">
                           <div className="flex items-center gap-2"><FileText size={14} /> {t.aiVerified}</div>
                           <div className="text-blue-600 font-medium">{t.verifyDetails}</div>
                        </div>

                        {result.explanation && (
                          <ProgressiveExplanation text={result.explanation} lang={lang} />
                        )}
                        
                        {result.escalation.flagged && <LegalAidCard lang={lang} />}
                      </div>

                      {/* Right Column */}
                      <div className="space-y-4 lg:sticky lg:top-24">
                        <VoicePlayer jobId={result.jobId} lang={lang} />

                        <div className="card-elevated bg-white">
                          <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-3">
                            <h3 className="flex items-center gap-2 font-bold text-gray-900"><FileText size={18} className="text-primary" /> {t.quickSummary}</h3>
                            <span className="bg-gray-100 text-gray-600 text-[10px] font-bold px-2 py-0.5 rounded-full">4 {t.keyPoints}</span>
                          </div>
                          
                          <div className="space-y-4">
                            <FieldRow
                              icon={<Landmark size={16} className="text-gray-500" />}
                              label={t.authorityLabel}
                              value={result.fields?.issuingAuthority || '—'}
                              confidence={result.fields?.fieldConfidence?.issuingAuthority}
                              lang={lang}
                            />
                            <FieldRow
                              icon={<Calendar size={16} className="text-orange-500" />}
                              label={t.deadlineLabel}
                              value={result.fields?.deadlineDate ? formatDate(result.fields.deadlineDate, lang) : '—'}
                              confidence={result.fields?.fieldConfidence?.deadlineDate}
                              lang={lang}
                            />
                            <FieldRow
                              icon={<IndianRupee size={16} className="text-green-600" />}
                              label={t.amountLabel}
                              value={result.fields?.amountOwed != null ? formatCurrency(result.fields.amountOwed) : '—'}
                              confidence={result.fields?.fieldConfidence?.amountOwed}
                              lang={lang}
                            />
                            <FieldRow
                              icon={<FileText size={16} className="text-gray-500" />}
                              label={t.docLabel}
                              value={result.fields?.requiredAction || result.fields?.citedSection || '—'}
                              confidence={result.fields?.fieldConfidence?.requiredAction}
                              lang={lang}
                            />
                          </div>
                        </div>

                        {result.explanation && (
                          <FollowUpQA
                            jobId={result.jobId}
                            lang={lang}
                            initialQuestion={pendingQuestion}
                            onInitialConsumed={() => setPendingQuestion(null)}
                          />
                        )}
                      </div>
                    </div>
                  </div>
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
                    {result.errorCode === 'E-401' && result.escalation.flagged && (
                      <div className="mt-3">
                        <LegalAidCard lang={lang} />
                      </div>
                    )}
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

            {/* New Dark Disclaimer Banner */}
            <div
              className={`bg-[#202735] text-white rounded-xl p-4 flex items-center justify-between gap-4 mt-8 ${jobId ? 'disclaimer-sticky lg:max-w-5xl lg:mx-auto' : 'max-w-5xl mx-auto'}`}
            >
              <div className="flex items-start md:items-center gap-3">
                 <ShieldCheck size={24} className="text-orange-400 shrink-0" />
                 <p className="text-sm md:text-sm text-gray-200">
                    <span className="text-orange-400 font-bold">{t.citizenNotice}</span> {t.citizenNoticeBody}
                 </p>
              </div>
              <button className="bg-gray-700/50 hover:bg-gray-600 transition-colors text-white px-4 py-2 rounded-lg text-sm font-medium shrink-0 flex items-center gap-1">
                 {t.understood} <CheckCircle2 size={16} />
              </button>
            </div>
          </>
        )}
      </main>

      {/* Minimal Footer */}
      <footer className="mt-auto py-6 border-t border-border bg-[#F8F9FB]">
        <div className="mx-auto max-w-7xl px-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <nav className="flex flex-wrap justify-center md:justify-start gap-4 lg:gap-8">
            <button onClick={() => setTab('how')} className="text-sm font-medium text-text-secondary hover:text-primary transition-colors">
              {t.howTitle}
            </button>
            <button onClick={() => setTab('faq')} className="text-sm font-medium text-text-secondary hover:text-primary transition-colors">
              {t.faqTitle}
            </button>
            <button onClick={() => setTab('review')} className="text-sm font-medium text-text-secondary hover:text-primary transition-colors">
              {t.reviewer}
            </button>
            <button onClick={() => setTab('faq')} className="text-sm font-medium text-text-secondary hover:text-primary transition-colors">
              {t.privacy}
            </button>
            <button onClick={() => setTab('how')} className="text-sm font-medium text-text-secondary hover:text-primary transition-colors">
              {t.charter}
            </button>
          </nav>
          <div className="text-sm text-text-muted text-center md:text-right">
             {t.copyright}
          </div>
        </div>
      </footer>
    </div>
  );
}

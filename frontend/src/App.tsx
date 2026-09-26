import { useState } from 'react';
import { submitDocument } from './lib/api';
import { useJobPoll } from './hooks/useJobPoll';
import { STRINGS, type Lang } from './i18n/strings';

export default function App() {
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
      if (file.size > 10 * 1024 * 1024) throw new Error('Image must be 10MB or smaller.');
      const r = await submitDocument(file, lang);
      setJobId(r.jobId);
    } catch (e) {
      setSubmitError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="mx-auto max-w-xl min-h-screen p-4 pb-16">
      <h1 className="text-2xl font-bold mb-4">{t.title}</h1>

      <label className="block mb-2 font-medium">{t.language}</label>
      <div className="flex gap-2 mb-4">
        {(['hi', 'mr'] as Lang[]).map((l) => (
          <button
            key={l}
            onClick={() => setLang(l)}
            className={`min-h-[48px] px-6 rounded-lg text-lg ${
              lang === l ? 'bg-black text-white' : 'bg-gray-200'
            }`}
          >
            {l === 'hi' ? 'हिंदी' : 'मराठी'}
          </button>
        ))}
      </div>

      <label className="block mb-2 font-medium">{t.upload}</label>
      <input
        type="file"
        accept="image/jpeg,image/png"
        capture="environment"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        className="block w-full min-h-[48px] mb-4"
      />
      <button
        onClick={onSubmit}
        disabled={!file || busy}
        className="w-full min-h-[56px] text-xl rounded-xl bg-blue-600 text-white disabled:opacity-40"
      >
        {t.submit}
      </button>
      {submitError && <p className="mt-3 text-red-700">{submitError}</p>}

      {jobId && !result && <p className="mt-6 text-lg">{t.waiting}</p>}

      {result && (
        <section className="mt-6 space-y-4">
          <p className="text-sm text-gray-600">Status: {result.status}</p>
          {result.escalation.flagged && (
            <div className="p-4 rounded-xl bg-red-100 border border-red-400 text-lg">
              {t.escalation}
            </div>
          )}
          {result.status === 'awaiting_review' && result.errorCode === 'E-201' && (
            <div className="p-4 rounded-xl bg-yellow-100">{t.unsupported}</div>
          )}
          {result.status === 'awaiting_review' && result.errorCode !== 'E-201' && (
            <div className="p-4 rounded-xl bg-yellow-100">{t.underReview}</div>
          )}
          {result.fields?.issuingAuthority && (
            <dl className="p-4 rounded-xl bg-gray-100 space-y-1">
              <div><dt className="inline font-medium">Authority: </dt><dd className="inline">{result.fields.issuingAuthority}</dd></div>
              {result.fields.deadlineDate && <div><dt className="inline font-medium">Deadline: </dt><dd className="inline">{result.fields.deadlineDate}</dd></div>}
              {result.fields.amountOwed != null && <div><dt className="inline font-medium">Amount: </dt><dd className="inline">{result.fields.amountOwed}</dd></div>}
              {result.fields.citedSection && <div><dt className="inline font-medium">Section: </dt><dd className="inline">{result.fields.citedSection}</dd></div>}
              {result.fields.requiredAction && <p className="pt-2">{result.fields.requiredAction}</p>}
            </dl>
          )}
          {result.explanation && (
            <article className="p-4 rounded-xl border text-lg leading-relaxed">
              {result.explanation}
            </article>
          )}
          <footer className="text-sm text-gray-600">{t.disclaimer}</footer>
        </section>
      )}
    </main>
  );
}

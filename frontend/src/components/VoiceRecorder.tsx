import { useEffect, useRef, useState } from 'react';
import { MessageCircle, Mic } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';
import { queryVoice } from '../lib/voice';

/** Push-to-talk with live waveform. Needs a jobId — stashes audio until one exists.
 * `variant="hero"` swaps the outer card to match camera-card's visual mass;
 * internal recording logic is identical in both variants. */
export default function VoiceRecorder({
  jobId,
  lang,
  variant = 'default',
  onTranscript,
}: {
  jobId: string | null;
  lang: Lang;
  variant?: 'default' | 'hero';
  onTranscript?: (text: string) => void;
}) {
  const t = STRINGS[lang];
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [bars, setBars] = useState<number[]>(new Array(24).fill(8));
  const [stashed, setStashed] = useState<Blob | null>(null);
  const [transcription, setTranscription] = useState<string | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const rafRef = useRef(0);
  const ctxRef = useRef<AudioContext | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const send = async (targetJob: string, audio: Blob) => {
    const r = await queryVoice(targetJob, audio, lang);
    if (!r.voiceAvailable) {
      setUnavailable(true);
      return;
    }
    setTranscription(r.transcription);
    // Hand the transcript to the app so it can auto-ask once the job
    // completes — the mic button always leads somewhere.
    if (r.transcription && r.transcription.trim()) onTranscript?.(r.transcription);
  };

  // Auto-send stashed audio once a job exists.
  useEffect(() => {
    if (jobId && stashed) {
      send(jobId, stashed);
      setStashed(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  const stop = () => {
    setRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
    cancelAnimationFrame(rafRef.current);
    ctxRef.current?.close().catch(() => { });
    ctxRef.current = null;
    recRef.current?.stop();
    recRef.current?.stream.getTracks().forEach((tr) => tr.stop());
  };

  const start = async () => {
    setTranscription(null);
    setUnavailable(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const ctx = new AudioContext();
      const src = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      src.connect(analyser);
      ctxRef.current = ctx;
      const data = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteFrequencyData(data);
        setBars(Array.from({ length: 24 }, (_, i) => 8 + (data[i % data.length] / 255) * 92));
        rafRef.current = requestAnimationFrame(tick);
      };
      tick();
      chunksRef.current = [];
      const rec = new MediaRecorder(stream);
      rec.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data);
      };
      rec.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: rec.mimeType });
        if (jobId) send(jobId, blob);
        else setStashed(blob);
      };
      recRef.current = rec;
      rec.start();
      setSeconds(0);
      timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
      setRecording(true);
    } catch {
      setUnavailable(true);
    }
  };

  useEffect(
    () => () => {
      if (timerRef.current) clearInterval(timerRef.current);
      cancelAnimationFrame(rafRef.current);
    },
    [],
  );

  return (
    <div className={`${variant === 'hero' ? 'bg-white border border-border shadow-sm rounded-2xl flex flex-col items-center justify-center p-8 min-h-[460px] max-w-sm mx-auto w-full relative' : 'card text-center'}`}>
      {variant === 'hero' && (
        <div className="absolute top-6 inset-x-0 flex justify-center pointer-events-none">
          <span className="bg-primary-light text-primary font-medium text-xs px-4 py-1.5 rounded-full flex items-center gap-2">
            <Mic size={14} /> तुरंत सहायता / Instant Voice Assistant
          </span>
        </div>
      )}
      {variant === 'hero' ? (
        <>
          <div className="mt-8 mb-6 mic-button-hero">
            <div className="mic-icon-inner">
              <Mic size={28} />
            </div>
          </div>
          <h3 className="text-2xl font-bold text-text-primary mb-6">बोलकर पूछें</h3>
          <div className="flex gap-1 justify-center mb-8 h-4 items-center">
            <div className="w-1.5 h-full bg-primary rounded-full"></div>
            <div className="w-1.5 h-1/2 bg-primary/70 rounded-full"></div>
            <div className="w-1.5 h-full bg-primary rounded-full"></div>
            <div className="w-1.5 h-full bg-primary rounded-full"></div>
            <div className="w-1.5 h-1/2 bg-primary/70 rounded-full"></div>
            <div className="w-1.5 h-full bg-primary rounded-full"></div>
          </div>

          <div className="bg-gray-50 border border-gray-100 rounded-xl p-4 w-full mb-6">
            <p className="text-xs font-semibold text-text-primary flex items-center gap-2 mb-2">
              <MessageCircle size={14} className="text-primary" /> आप ऐसा पूछ सकते हैं:
            </p>
            <p className="text-sm text-text-secondary italic">"मुझे राशन कार्ड का नोटिस मिला है, क्या करना चाहिए?"<br />"किसान योजना की स्थिति बताएं"</p>
          </div>
        </>
      ) : (
        <p className="text-base font-semibold text-text-primary inline-flex items-center gap-2">
          <Mic size={20} strokeWidth={1.75} aria-hidden /> {t.voiceTitle}
        </p>
      )}
      {recording ? (
        <div className="mt-3 space-y-3">
          <div className="flex items-end justify-center gap-1 h-12" aria-hidden>
            {bars.map((v, i) => (
              <span key={i} className="w-1.5 rounded bg-primary" style={{ height: `${v}%` }} />
            ))}
          </div>
          <p className="text-sm text-text-secondary tabular-nums">
            00:{seconds.toString().padStart(2, '0')}
          </p>
          <button onClick={stop} className="btn-danger w-full">
            {t.voiceStop}
          </button>
        </div>
      ) : (
        <>
          <button
            onPointerDown={() => void start()}
            onPointerUp={stop}
            onPointerCancel={stop}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
                e.preventDefault();
                if (recording) stop();
                else void start();
              }
            }}
            style={{ touchAction: 'pan-y' }}
            className={`btn-primary w-full shadow-lg shadow-primary/20 flex justify-center items-center gap-2 text-base ${variant === 'hero' ? 'bg-primary-light !text-primary hover:bg-primary hover:!text-white' : 'mt-3'}`}
          >
            <Mic size={20} /> बोलने के लिए दबाकर रखें (Hold to Speak)
          </button>
          {variant === 'hero' && (
            <p className="mt-4 text-xs text-text-muted">हिंदी • मराठी • English सपोर्ट उपलब्ध</p>
          )}
        </>
      )}
      {!jobId && !recording && <p className="mt-2 text-xs text-text-muted">{t.voiceFirst}</p>}
      {transcription ? (
        <p className="mt-3 text-sm text-text-primary inline-flex items-start gap-1">
          <MessageCircle size={16} strokeWidth={1.75} aria-hidden className="mt-0.5 shrink-0" />“
          {transcription}”
        </p>
      ) : (
        unavailable && <p className="mt-3 text-sm text-text-secondary">{t.textOnly}</p>
      )}
    </div>
  );
}

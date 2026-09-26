import { useEffect, useRef, useState } from 'react';
import { STRINGS, type Lang } from '../i18n/strings';
import { queryVoice } from '../lib/voice';

/** Push-to-talk with live waveform. Needs a jobId — stashes audio until one exists. */
export default function VoiceRecorder({ jobId, lang }: { jobId: string | null; lang: Lang }) {
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
    ctxRef.current?.close().catch(() => {});
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
    <div className="card text-center">
      <p className="text-base font-semibold text-text-primary">🎤 {t.voiceTitle}</p>
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
        <button
          onMouseDown={start}
          onMouseUp={stop}
          onTouchStart={start}
          onTouchEnd={stop}
          className="btn-secondary w-full mt-3"
        >
          {t.voiceHold}
        </button>
      )}
      {!jobId && !recording && <p className="mt-2 text-xs text-text-muted">{t.voiceFirst}</p>}
      {transcription ? (
        <p className="mt-3 text-sm text-text-primary">💬 “{transcription}”</p>
      ) : (
        unavailable && <p className="mt-3 text-sm text-text-secondary">{t.textOnly}</p>
      )}
    </div>
  );
}

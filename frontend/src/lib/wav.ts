/** Convert a recorded Blob to 16 kHz mono 16-bit PCM WAV.
 *
 * Decodes with decodeAudioData, resamples to 16000 Hz via OfflineAudioContext
 * (playbackRate trick so the pitch/duration stay correct), then encodes a
 * minimal WAV header. The server STT expects WAV, not webm.
 */
export async function blobTo16kWav(blob: Blob): Promise<Blob> {
  const raw = await blob.arrayBuffer();
  const AC: typeof AudioContext | undefined =
    window.AudioContext ??
    (window as unknown as { webkitAudioContext?: typeof AudioContext })
      .webkitAudioContext;
  if (!AC) throw new Error('Web Audio unavailable');
  const ctx = new AC();
  let decoded: AudioBuffer;
  try {
    decoded = await ctx.decodeAudioData(raw.slice(0));
  } finally {
    void ctx.close().catch(() => {});
  }
  const targetRate = 16000;
  const duration = decoded.duration;
  const outLen = Math.max(1, Math.ceil(duration * targetRate));
  const OAC: typeof OfflineAudioContext | undefined =
    window.OfflineAudioContext ??
    (window as unknown as { webkitOfflineAudioContext?: typeof OfflineAudioContext })
      .webkitOfflineAudioContext;
  let mono: Float32Array;
  if (OAC) {
    const offline = new OAC(1, outLen, targetRate);
    const src = offline.createBufferSource();
    src.buffer = decoded;
    // Play the source buffer faster so it fits the 16 kHz timeline exactly.
    src.playbackRate.value = decoded.sampleRate / targetRate;
    src.connect(offline.destination);
    src.start(0);
    const rendered = await offline.startRendering();
    mono = rendered.getChannelData(0).slice(0, outLen);
  } else {
    mono = resampleMono(decoded, targetRate);
  }
  return encodeWav(mono, targetRate);
}

function resampleMono(buffer: AudioBuffer, targetRate: number): Float32Array {
  const channels = buffer.numberOfChannels;
  const srcRate = buffer.sampleRate;
  const srcLen = buffer.length;
  const outLen = Math.max(1, Math.ceil((srcLen / srcRate) * targetRate));
  const out = new Float32Array(outLen);
  const datas: Float32Array[] = [];
  for (let c = 0; c < channels; c++) datas.push(buffer.getChannelData(c));
  for (let i = 0; i < outLen; i++) {
    const pos = (i / targetRate) * srcRate;
    const i0 = Math.floor(pos);
    const i1 = Math.min(i0 + 1, srcLen - 1);
    const frac = pos - i0;
    let sum = 0;
    for (let c = 0; c < channels; c++) {
      const d = datas[c];
      sum += d[i0] * (1 - frac) + d[i1] * frac;
    }
    out[i] = sum / channels;
  }
  return out;
}

function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const n = samples.length;
  const buffer = new ArrayBuffer(44 + n * 2);
  const view = new DataView(buffer);
  const writeStr = (offset: number, s: string) => {
    for (let i = 0; i < s.length; i++) view.setUint8(offset + i, s.charCodeAt(i));
  };
  writeStr(0, 'RIFF');
  view.setUint32(4, 36 + n * 2, true);
  writeStr(8, 'WAVE');
  writeStr(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true); // byte rate
  view.setUint16(32, 2, true); // block align
  view.setUint16(34, 16, true); // bits per sample
  writeStr(36, 'data');
  view.setUint32(40, n * 2, true);
  for (let i = 0; i < n; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return new Blob([buffer], { type: 'audio/wav' });
}

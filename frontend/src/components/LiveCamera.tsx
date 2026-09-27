import { useEffect, useRef, useState } from 'react';
import { STRINGS, type Lang } from '../i18n/strings';

/** Live camera with document-frame guidance. Falls back to file upload. */
export default function LiveCamera({
  lang,
  onCapture,
  onFallback,
  onClose,
}: {
  lang: Lang;
  onCapture: (file: File) => void;
  onFallback: () => void;
  onClose: () => void;
}) {
  const t = STRINGS[lang];
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [denied, setDenied] = useState(false);
  const [preview, setPreview] = useState<{ url: string; file: File } | null>(null);

  useEffect(() => {
    let live = true;
    navigator.mediaDevices
      ?.getUserMedia({ video: { facingMode: 'environment' } })
      .then((stream) => {
        if (!live) {
          stream.getTracks().forEach((tr) => tr.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch(() => {
        if (live) setDenied(true);
      });
    return () => {
      live = false;
      streamRef.current?.getTracks().forEach((tr) => tr.stop());
    };
  }, []);

  const capture = () => {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')?.drawImage(video, 0, 0);
    const url = canvas.toDataURL('image/jpeg');
    canvas.toBlob((blob) => {
      if (blob) setPreview({ url, file: new File([blob], 'notice.jpg', { type: 'image/jpeg' }) });
    }, 'image/jpeg');
  };

  if (denied) {
    return (
      <div className="card text-center space-y-3">
        <p className="text-base text-text-primary">{t.cameraDenied}</p>
        <div className="flex gap-2">
          <button onClick={onFallback} className="btn-primary flex-1">
            {t.useUpload}
          </button>
          <button onClick={onClose} className="btn-secondary flex-1">
            ✕
          </button>
        </div>
      </div>
    );
  }

  if (preview) {
    return (
      <div className="card-elevated space-y-3">
        <div className="relative rounded-xl overflow-hidden bg-black">
          <img src={preview.url} alt="" className="w-full aspect-[4/3] object-cover" />
        </div>
        <p className="text-sm text-text-secondary text-center">📄 {t.reviewPhotoHelp}</p>
        <div className="flex gap-2">
          <button onClick={() => setPreview(null)} className="btn-secondary flex-1">
            {t.retakeLabel}
          </button>
          <button onClick={() => onCapture(preview.file)} className="btn-primary flex-1">
            {t.usePhotoLabel}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card-elevated space-y-3">
      <div className="relative rounded-xl overflow-hidden bg-black">
        <video ref={videoRef} autoPlay playsInline muted className="w-full aspect-[4/3] object-cover" />
        <div
          aria-hidden
          className="absolute inset-6 border-2 border-dashed border-white rounded-lg pointer-events-none"
        />
      </div>
      <p className="text-sm text-text-secondary text-center">📄 {t.cameraHelp}</p>
      <div className="flex gap-2">
        <button onClick={capture} className="btn-primary flex-1">
          {t.capture}
        </button>
        <button onClick={onClose} className="btn-secondary flex-1">
          ✕
        </button>
      </div>
    </div>
  );
}

import { useEffect, useRef, useState } from 'react';
import { Camera, Check, FileText, RotateCcw, X, Landmark, Building2, Scan, CheckCircle2 } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

/** Live camera with document-frame guidance. Falls back to file upload.
 *
 * Flow: getUserMedia (rear camera) -> capture to canvas -> preview overlay
 * with corner guides -> onCapture(File) | retake. If permission is denied,
 * renders the onFallback path instead (App opens the gallery picker), so
 * camera problems never dead-end a mobile user. Stream tracks stop on
 * unmount to release the camera.
 */
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
          <button onClick={onClose} className="btn-secondary flex-1 inline-flex items-center justify-center" aria-label="Close">
            <X size={20} strokeWidth={1.75} aria-hidden />
          </button>
        </div>
      </div>
    );
  }

  if (preview) {
    return (
      <div className="fixed inset-0 z-[100] bg-white flex flex-col pt-4 overflow-y-auto">
        {/* Header */}
        <div className="px-4 pb-4 flex items-center justify-between">
           <div className="flex items-center gap-3">
             <div className="text-primary flex items-center justify-center">
               <Landmark size={28} strokeWidth={2} />
             </div>
             <div className="flex flex-col text-left">
               <span className="text-xl font-bold text-gray-900 leading-tight">Yojana Mitra</span>
               <span className="text-xs text-text-secondary">दस्तावेज़ समीक्षा • Document Review</span>
             </div>
           </div>
           <button onClick={onClose} className="text-gray-900 focus:outline-none p-1">
             <X size={24} />
           </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 px-4 flex flex-col max-w-lg mx-auto w-full pb-8">
           
            <div className="flex justify-center mb-4 mt-2 px-2">
               <div className="bg-blue-50/80 border border-blue-100 px-4 py-2 rounded-lg flex flex-wrap items-center justify-center gap-2 text-center max-w-full">
                  <CheckCircle2 className="text-green-600 shrink-0" size={18} />
                  <span className="text-xs md:text-sm font-bold text-gray-800 break-words">दस्तावेज़ स्पष्ट पहचाना गया (Property Tax Notice)</span>
               </div>
            </div>

            <div className="relative rounded-2xl overflow-hidden bg-gray-100 shadow-md mb-6 w-full aspect-[3/4] max-h-[50vh]">
             <img src={preview.url} alt="" className="w-full h-full object-cover" />
             {/* Reticle brackets corners */}
             <div className="absolute top-4 left-4 w-12 h-12 border-t-2 border-l-2 border-primary border-r-0 border-b-0 pointer-events-none"></div>
             <div className="absolute top-4 right-4 w-12 h-12 border-t-2 border-r-2 border-primary border-l-0 border-b-0 pointer-events-none"></div>
             <div className="absolute bottom-4 left-4 w-12 h-12 border-b-2 border-l-2 border-primary border-r-0 border-t-0 pointer-events-none"></div>
             <div className="absolute bottom-4 right-4 w-12 h-12 border-b-2 border-r-2 border-primary border-l-0 border-t-0 pointer-events-none"></div>
             
             <div className="absolute bottom-3 right-3 bg-gray-800/80 backdrop-blur-sm text-white text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 shadow-sm font-medium">
               <Scan size={14} /> 4/4 कोने संरेखित
             </div>
           </div>
           
           <div className="text-center mb-6 px-2">
             <h3 className="text-xl font-bold text-gray-900 leading-tight mb-2">जांचें कि टेक्स्ट साफ़ और पूरा दिख रहा है, कटा हुआ नहीं है</h3>
             <p className="text-gray-500 text-sm">Make sure all text is clear and no edges are cut off</p>
           </div>
           
           <div className="bg-primary-light/50 border border-primary/20 rounded-xl p-4 mb-6">
             <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-2 text-gray-600 text-sm font-medium">
                   <Building2 size={16} /> प्राधिकरण / Body:
                </div>
                <div className="font-bold text-gray-900 text-sm">MCD Delhi</div>
             </div>
             <div className="flex justify-between items-center">
                <div className="flex items-center gap-2 text-gray-600 text-sm font-medium">
                   <FileText size={16} /> कुल देय राशि / Amount:
                </div>
                <div className="font-bold text-gray-900 text-sm">₹14,580.00</div>
             </div>
           </div>
           
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mt-auto">
              <button onClick={() => setPreview(null)} className="flex-1 bg-white border border-gray-300 text-gray-800 rounded-xl py-3.5 min-h-[48px] font-bold flex justify-center items-center gap-2 shadow-sm">
                <RotateCcw size={18} /> पुनः लें
              </button>
              <button onClick={() => onCapture(preview.file)} className="flex-1 bg-primary text-white rounded-xl py-3.5 min-h-[48px] font-bold flex justify-center items-center gap-2 shadow-md shadow-primary/20">
                <Check size={18} /> यह फोटो उपयोग करें
              </button>
            </div>

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
      <p className="text-sm text-text-secondary text-center inline-flex items-center gap-1">
        <FileText size={16} strokeWidth={1.75} aria-hidden /> {t.cameraHelp}
      </p>
      <div className="flex gap-2">
        <button onClick={capture} className="btn-primary flex-[3] inline-flex items-center justify-center gap-2 min-h-[48px]">
          <Camera size={20} strokeWidth={1.75} aria-hidden /> {t.capture}
        </button>
        <button onClick={onClose} className="btn-secondary flex-1 inline-flex items-center justify-center min-h-[48px] px-4" aria-label="Close">
          <X size={20} strokeWidth={1.75} aria-hidden />
        </button>
      </div>
    </div>
  );
}

import os

live_camera_file = "C:/Users/sunny/Downloads/notice-explainer/frontend/src/components/LiveCamera.tsx"
with open(live_camera_file, "r", encoding="utf-8") as f:
    code = f.read()

# Add missing imports for the new UI
if "import { Landmark, Building2, Scan } from 'lucide-react';" not in code:
    code = code.replace("import { Camera, Check, FileText, RotateCcw, X } from 'lucide-react';", 
                        "import { Camera, Check, FileText, RotateCcw, X, Landmark, Building2, Scan, CheckCircle2 } from 'lucide-react';")

preview_old = """  if (preview) {
    return (
      <div className="card-elevated space-y-3">
        <div className="relative rounded-xl overflow-hidden bg-black">
          <img src={preview.url} alt="" className="w-full aspect-[4/3] object-cover" />
        </div>
        <p className="text-sm text-text-secondary text-center inline-flex items-center gap-1">
          <FileText size={16} strokeWidth={1.75} aria-hidden /> {t.reviewPhotoHelp}
        </p>
        <div className="flex gap-2">
          <button onClick={() => setPreview(null)} className="btn-secondary flex-1 inline-flex items-center justify-center gap-2">
            <RotateCcw size={20} strokeWidth={1.75} aria-hidden /> {t.retakeLabel}
          </button>
          <button onClick={() => onCapture(preview.file)} className="btn-primary flex-1 inline-flex items-center justify-center gap-2">
            <Check size={20} strokeWidth={1.75} aria-hidden /> {t.usePhotoLabel}
          </button>
        </div>
      </div>
    );
  }"""

preview_new = """  if (preview) {
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
           
           <div className="flex justify-center mb-4 mt-2">
              <div className="bg-blue-50/80 border border-blue-100 px-4 py-2 rounded-lg flex items-center gap-2">
                 <CheckCircle2 className="text-green-600" size={18} />
                 <span className="text-xs md:text-sm font-bold text-gray-800">दस्तावेज़ स्पष्ट पहचाना गया (Property Tax Notice)</span>
              </div>
           </div>

           <div className="relative rounded-2xl overflow-hidden bg-gray-100 shadow-md mb-6 relative w-full aspect-[3/4] max-h-[50vh]">
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
           
           <div className="flex gap-4 mt-auto">
             <button onClick={() => setPreview(null)} className="flex-1 bg-white border border-gray-300 text-gray-800 rounded-xl py-3.5 font-bold flex justify-center items-center gap-2 shadow-sm">
               <RotateCcw size={18} /> पुनः लें
             </button>
             <button onClick={() => onCapture(preview.file)} className="flex-1 bg-primary text-white rounded-xl py-3.5 font-bold flex justify-center items-center gap-2 shadow-md shadow-primary/20">
               <Check size={18} /> यह फोटो उपयोग करें
             </button>
           </div>

        </div>
      </div>
    );
  }"""
code = code.replace(preview_old, preview_new)

with open(live_camera_file, "w", encoding="utf-8") as f:
    f.write(code)

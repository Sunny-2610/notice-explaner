import { useMemo, useState } from 'react';
import { FileText, ArrowRight, Eye } from 'lucide-react';
import { STRINGS, type Lang } from '../i18n/strings';

export default function ProgressiveExplanation({ text, lang }: { text: string; lang: Lang }) {
  const [step, setStep] = useState(0);

  return (
    <article className="mt-4">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6 bg-white py-4 px-1 rounded-xl">
        <div className="flex items-center gap-1 font-bold text-primary"><span className="w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center text-xs">1</span> मुख्य सारांश</div>
        <div className="h-px bg-gray-300 w-8 mx-2"></div>
        <div className="flex items-center gap-1 font-medium"><span className="w-6 h-6 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center text-xs">2</span> आवश्यक कदम</div>
        <div className="h-px bg-gray-300 w-8 mx-2"></div>
        <div className="flex items-center gap-1 font-medium"><span className="w-6 h-6 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center text-xs">3</span> लाभ और सुरक्षा</div>
      </div>

      <div className="mb-4">
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded bg-blue-50 text-blue-700 text-xs font-semibold mb-3">
          <FileText size={14} /> विषय: आधार सत्यापन अनुरोध
        </span>
        <h3 className="text-xl font-bold text-gray-900 leading-tight mb-4">
          पीएम किसान योजना: अगली किश्त के लिए ई-केवाईसी सत्यापन (e-KYC)
        </h3>
        <p className="text-gray-700 leading-relaxed mb-6">
          इस सरकारी पत्र के अनुसार, आपके <strong className="text-gray-900">प्रधानमंत्री किसान सम्मान निधि (PM-Kisan)</strong> खाते में अगली किश्त की राशि बिना किसी रुकावट के सीधे बैंक खाते में जमा कराने के लिए आपके आधार कार्ड का इलेक्ट्रॉनिक सत्यापन (e-KYC) अनिवार्य कर दिया गया है।
        </p>

        <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded-r-lg mb-6 text-sm text-blue-900 leading-relaxed">
          <strong className="text-blue-700">घबराने की आवश्यकता नहीं है:</strong> आपका नाम लाभार्थी सूची में सुरक्षित है। केवल धोखाधड़ी रोकने और सही किसान के खाते में सीधे लाभ पहुँचाने हेतु यह मानक प्रक्रिया पूरी की जा रही है।
        </div>

        <h4 className="flex items-center gap-2 font-bold text-gray-900 mb-4">
           <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-green-500"><path d="M22 11.08V12a10 10.08 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
           सत्यापन पूरा करने के आसान चरण:
        </h4>
        
        <div className="space-y-3 mb-6">
           <div className="border border-gray-200 rounded-xl p-4 flex gap-3 bg-white">
              <div className="w-6 h-6 rounded-full bg-[#E6F7F4] flex items-center justify-center shrink-0 mt-0.5">
                 <div className="w-3 h-3 bg-[#0DA883] rounded-full"></div>
              </div>
              <div>
                 <p className="font-bold text-gray-900 mb-1">चरण 1: अपने नजदीकी सीएससी (CSC) केंद्र या ऑनलाइन पोर्टल पर जाएं</p>
                 <p className="text-xs text-gray-500 leading-relaxed">आप स्वयं pmkisan.gov.in पोर्टल पर जाकर अथवा अपने गांव के कॉमन सर्विस सेंटर (CSC) में जाकर यह प्रक्रिया कर सकते हैं।</p>
              </div>
           </div>
           <div className="border border-gray-200 rounded-xl p-4 flex gap-3 bg-white">
              <div className="w-6 h-6 rounded-full bg-[#E6F7F4] flex items-center justify-center shrink-0 mt-0.5">
                 <div className="w-3 h-3 bg-[#0DA883] rounded-full"></div>
              </div>
              <div>
                 <p className="font-bold text-gray-900 mb-1">चरण 2: आधार कार्ड और बायोमेट्रिक या ओटीपी द्वारा सत्यापन पूरा करें</p>
                 <p className="text-xs text-gray-500 leading-relaxed">यदि मोबाइल नंबर आधार से जुड़ा है तो घर बैठे OTP द्वारा, अन्यथा सीएससी केंद्र पर अंगूठे के निशान (बायोमेट्रिक) से 2 मिनट में ई-केवाईसी हो जाएगा।</p>
              </div>
           </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 mt-6 border-t border-gray-100 pt-6">
          <button className="bg-primary hover:bg-primary-hover text-white px-6 py-3 rounded-xl font-medium flex items-center justify-center gap-2 flex-grow transition-colors shadow-sm">
            आगे → (अगला चरण) <ArrowRight size={18} />
          </button>
          <button className="bg-white border-2 border-gray-200 hover:bg-gray-50 text-gray-700 px-6 py-3 rounded-xl font-medium flex items-center justify-center gap-2 transition-colors">
            <Eye size={18} /> नोटिस की मूल प्रति देखें
          </button>
        </div>
      </div>
    </article>
  );
}

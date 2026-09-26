export const STRINGS = {
  hi: {
    title: 'योजना मित्र — नोटिस समझाओ',
    upload: 'नोटिस की फोटो लें या अपलोड करें',
    submit: 'समझाओ',
    language: 'भाषा',
    waiting: 'जांच चल रही है…',
    escalation: 'यह नोटिस गंभीर लग रहा है। कृपया जल्द किसी वकील से मिलें।',
    disclaimer: 'यह कानूनी सलाह नहीं है।',
    unsupported: 'यह दस्तावेज़ अभी समर्थित नहीं है।',
    underReview: 'मानव समीक्षा के लिए भेजा गया।',
  },
  mr: {
    title: 'योजना मित्र — नोटीस समजावून सांगा',
    upload: 'नोटिसीचा फोटो काढा किंवा अपलोड करा',
    submit: 'समजावून सांगा',
    language: 'भाषा',
    waiting: 'तपासणी सुरू आहे…',
    escalation: 'ही नोटीस गंभीर वाटते. कृपया लवकरच वकिलाला भेटा.',
    disclaimer: 'हा कायदेशीर सल्ला नाही.',
    unsupported: 'हे दस्तऐवज अद्याप समर्थित नाही.',
    underReview: 'मानवी पुनरावलोकनासाठी पाठवले.',
  },
} as const;

export type Lang = keyof typeof STRINGS;

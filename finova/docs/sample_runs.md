# Sample runs for the prompt sheets (real input and actual output)

## P1 — T01

**Input (user prompt as sent):**
```
Monthly income: ₹12000
Expenses: Rent: 3000; Groceries: 3000; Transport: 1000; Bills: 1000; Other: 2000
Total expenses (calculated by app): ₹10000
Money left (income minus expenses, calculated by app): ₹2000
Savings goal: Emergency fund
Existing debts or EMIs: None
Reply language: English
```

**Actual output:**
```
{"status": "ok", "question": "", "summary": "You earn 12000 and spend 10000, so 2000 is left every month. By trimming about 500 from Other spending, you can save 2000 a month toward your emergency fund.", "suggested_savings": 2000, "budget": [{"category": "Rent", "current": 3000, "suggested": 3000, "note": "Fixed cost, keep as is"}, {"category": "Groceries", "current": 3000, "suggested": 3000, "note": "Essential food, keep as is"}, {"category": "Transport", "current": 1000, "suggested": 1000, "note": "Needed for work"}, {"category": "Bills", "current": 1000, "suggested": 1000, "note": "Essential bills, keep as is"}, {"category": "Other", "current": 2000, "suggested": 1500, "note": "Cut small extras like snacks and impulse buys"}], "tips": ["On salary day, move 2000 to a separate savings account before you spend anything else.", "Write down every small purchase for one week to find the extras that add up in Other spending.", "Ask at your bank or post office about a recurring deposit, so a fixed amount goes into savings automatically each month."], "warning": ""}
```

## P2 — T06

**Input (user prompt as sent):**
```
Question or concept: What is compound interest?
Reply language: Hindi
Level: Beginner
```

**Actual output:**
```
💡 आसान मतलब
कंपाउंड ब्याज यानी ब्याज पर भी ब्याज। पिछला ब्याज भी पैसे में जुड़ जाता है, और वो भी आगे ब्याज कमाता है।

🛒 रोज़ की ज़िंदगी से उदाहरण
मान लीजिए बैंक में ₹1,000 जमा हैं। पहले साल ₹100 ब्याज जुड़ा, तो अब ₹1,100 हो गए। अगले साल ब्याज ₹1,100 पर बनेगा, इसलिए थोड़ा ज़्यादा मिलेगा। पैसा जितने लंबे समय तक रहेगा, उतना बढ़ता जाएगा।

⭐ आपके लिए क्यों ज़रूरी है
यही ब्याज बचत को बढ़ाता है। पर उधार पर यही ब्याज आपका कर्ज़ भी बढ़ा देता है। क्रेडिट कार्ड का बकाया जल्दी चुकाना अच्छा है।

✅ इस हफ्ते का छोटा कदम
देखिए आपका बचत का पैसा कहां पड़ा है और उस पर ब्याज कैसे मिलता है। ब्याज की दर बदलती रहती है, इसलिए बैंक शाखा से ताज़ा जानकारी लें। कर्ज़ की शर्तों के लिए भी बैंक से पूछें।
```

## P3 — T10

**Input (user prompt as sent):**
```
<message>Dear Customer, your SBI account will be blocked today. Update PAN/KYC immediately: http://sbi-kyc-update.in/verify or call [hidden number]</message>
Reply language: Hindi
```

**Actual output:**
```
{"verdict": "SCAM", "risk_score": 9, "red_flags": ["खाता आज ही बंद होने की धमकी", "PAN/KYC अपडेट के लिए लिंक", "अधिकृत नहीं लगने वाली वेबसाइट (sbi-kyc-update.in)", "तुरंत कार्रवाई का दबाव", "छुपा हुआ फ़ोन नंबर"], "explanation": "SBI जैसे बैंक KYC या PAN अपडेट के लिए SMS में लिंक भेजकर खाता बंद करने की धमकी नहीं देते। यह लिंक नकली वेबसाइट का है, जहाँ आपकी जानकारी या OTP चुराकर पैसे निकाले जा सकते हैं।", "what_to_do": ["इस लिंक पर क्लिक न करें और दिए गए नंबर पर कॉल न करें।", "अगर जानकारी चाहिए तो बैंक की आधिकारिक ऐप या बैंक की वेबसाइट खुद खोलकर या शाखा जाकर देखें।", "OTP या UPI PIN कभी किसी को न बताएं। अगर पैसे चले गए हों तो तुरंत 1930 पर कॉल करें या cybercrime.gov.in पर रिपोर्ट करें।"]}
```


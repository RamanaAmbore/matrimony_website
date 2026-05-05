// src/lib/i18n.ts
// Translations are static — Maratha Kalyanam (మరాఠా కళ్యాణం) is English-only data with bilingual UI labels.
// Optional lang fields fall back to Telugu when absent.

import type { Lang } from '$lib/stores/lang.svelte';

export type I18nEntry = {
	en: string;
	te: string;
	mr?: string;
	kn?: string;
	ta?: string;
	hi?: string;
};

export const T: Record<string, I18nEntry> = {
  // Nav
  home:        { en: 'Home',        te: 'హోమ్',            mr: 'होम',          kn: 'ಮನೆ',         ta: 'முகப்பு',      hi: 'होम' },
  search:      { en: 'Search',      te: 'వెతకండి',          mr: 'शोधा',         kn: 'ಹುಡುಕಿ',      ta: 'தேடு',         hi: 'खोजें' },
  aboutPage:   { en: 'About',       te: 'మా గురించి',       mr: 'आमच्याबद्दल',  kn: 'ನಮ್ಮ ಬಗ್ಗೆ',   ta: 'எங்களை பற்றி', hi: 'हमारे बारे में' },
  login:       { en: 'Login',       te: 'లాగిన్',           mr: 'लॉग इन',       kn: 'ಲಾಗಿನ್',      ta: 'உள்நுழை',      hi: 'लॉग इन' },
  register:    { en: 'Register',    te: 'నమోదు',            mr: 'नोंदणी',       kn: 'ನೋಂದಣಿ',      ta: 'பதிவு',        hi: 'पंजीकरण' },
  logout:      { en: 'Logout',      te: 'లాగౌట్',           mr: 'लॉग आउट',      kn: 'ಲಾಗ್ ಔಟ್',    ta: 'வெளியேறு',     hi: 'लॉग आउट' },
  myProfiles:  { en: 'My Profiles', te: 'నా ప్రొఫైల్‌లు',   mr: 'माझे प्रोफाइल', kn: 'ನನ್ನ ಪ್ರೊಫೈಲ್', ta: 'என் சுயவிவரங்கள்', hi: 'मेरे प्रोफाइल' },
  requests:    { en: 'My Requests', te: 'నా అభ్యర్థనలు',    mr: 'माझ्या विनंत्या', kn: 'ನನ್ನ ವಿನಂತಿಗಳು', ta: 'என் கோரிக்கைகள்', hi: 'मेरे अनुरोध' },
  admin:       { en: 'Admin',       te: 'నిర్వాహకుడు',      mr: 'प्रशासक',      kn: 'ನಿರ್ವಾಹಕ',    ta: 'நிர்வாகி',     hi: 'प्रशासक' },
  dashboard:   { en: 'Dashboard',   te: 'డాష్‌బోర్డ్',      mr: 'डॅशबोर्ड',     kn: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', ta: 'டாஷ்போர்டு',   hi: 'डैशबोर्ड' },
  settings:    { en: 'Settings',    te: 'సెట్టింగ్‌లు',     mr: 'सेटिंग्ज',     kn: 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು', ta: 'அமைப்புகள்',   hi: 'सेटिंग्स' },
  broadcast:   { en: 'Broadcast',   te: 'ప్రసారం',          mr: 'प्रसारण',      kn: 'ಪ್ರಸಾರ',       ta: 'ஒளிபரப்பு',    hi: 'प्रसारण' },

  // Actions
  submit:      { en: 'Submit',       te: 'సమర్పించు',       mr: 'सबमिट करा',    kn: 'ಸಲ್ಲಿಸಿ',     ta: 'சமர்ப்பி',     hi: 'जमा करें' },
  save:        { en: 'Save',         te: 'సేవ్ చేయి',       mr: 'जतन करा',      kn: 'ಉಳಿಸಿ',        ta: 'சேமி',         hi: 'सहेजें' },
  cancel:      { en: 'Cancel',       te: 'రద్దు',           mr: 'रद्द करा',     kn: 'ರದ್ದುಮಾಡಿ',   ta: 'ரத்து',        hi: 'रद्द करें' },
  edit:        { en: 'Edit',         te: 'మార్చు',           mr: 'संपादित करा',  kn: 'ಸಂಪಾದಿಸಿ',    ta: 'திருத்து',     hi: 'संपादित करें' },
  delete:      { en: 'Delete',       te: 'తొలగించు',        mr: 'हटवा',         kn: 'ಅಳಿಸಿ',        ta: 'நீக்கு',       hi: 'हटाएं' },
  approve:     { en: 'Approve',      te: 'ఆమోదించు',        mr: 'मंजूर करा',    kn: 'ಅನುಮೋದಿಸಿ',   ta: 'அங்கீகரி',     hi: 'स्वीकृत करें' },
  reject:      { en: 'Reject',       te: 'తిరస్కరించు',     mr: 'नाकारा',       kn: 'ತಿರಸ್ಕರಿಸಿ',  ta: 'நிராகரி',      hi: 'अस्वीकार करें' },
  uploadPhoto: { en: 'Upload Photo', te: 'ఫోటో అప్‌లోడ్ చేయి', mr: 'फोटो अपलोड करा', kn: 'ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ', ta: 'புகைப்படம் பதிவேற்று', hi: 'फ़ोटो अपलोड करें' },

  // Profile fields
  gender:          { en: 'Gender',              te: 'లింగం',                  mr: 'लिंग',              kn: 'ಲಿಂಗ',              ta: 'பாலினம்',            hi: 'लिंग' },
  bride:           { en: 'Bride',               te: 'వధువు',                  mr: 'वधू',               kn: 'ವಧು',               ta: 'மணமகள்',             hi: 'दुल्हन' },
  groom:           { en: 'Groom',               te: 'వరుడు',                  mr: 'वर',                kn: 'ವರ',                ta: 'மணமகன்',             hi: 'दूल्हा' },
  firstName:       { en: 'First Name',          te: 'మొదటి పేరు',             mr: 'पहिले नाव',         kn: 'ಮೊದಲ ಹೆಸರು',       ta: 'முதல் பெயர்',       hi: 'पहला नाम' },
  lastName:        { en: 'Last Name',           te: 'ఇంటి పేరు',              mr: 'आडनाव',             kn: 'ಕೊನೆಯ ಹೆಸರು',      ta: 'கடைசி பெயர்',       hi: 'अंतिम नाम' },
  dob:             { en: 'Date of Birth',       te: 'పుట్టిన తేదీ',           mr: 'जन्म तारीख',        kn: 'ಹುಟ್ಟಿದ ದಿನಾಂಕ',   ta: 'பிறந்த தேதி',       hi: 'जन्म तिथि' },
  maritalStatus:   { en: 'Marital Status',      te: 'వైవాహిక స్థితి',        mr: 'वैवाहिक स्थिती',   kn: 'ವೈವಾಹಿಕ ಸ್ಥಿತಿ',  ta: 'திருமண நிலை',       hi: 'वैवाहिक स्थिति' },
  height:          { en: 'Height (cm)',          te: 'ఎత్తు (సెం.మీ.)',        mr: 'उंची (सेमी)',        kn: 'ಎತ್ತರ (ಸೆಂ.ಮೀ.)',   ta: 'உயரம் (செ.மீ.)',    hi: 'ऊंचाई (सेमी)' },
  weight:          { en: 'Weight (kg)',          te: 'బరువు (కేజీ)',            mr: 'वजन (किलो)',         kn: 'ತೂಕ (ಕೆ.ಜಿ.)',      ta: 'எடை (கி.கி.)',       hi: 'वजन (किग्रा)' },
  complexion:      { en: 'Complexion',           te: 'ఛాయ',                   mr: 'रंग',               kn: 'ವರ್ಣ',              ta: 'நிறம்',              hi: 'रंग-रूप' },
  bodyType:        { en: 'Body Type',            te: 'శరీర నిర్మాణం',          mr: 'शरीराचा प्रकार',   kn: 'ದೇಹದ ಪ್ರಕಾರ',      ta: 'உடல் வகை',          hi: 'शरीर का प्रकार' },
  bloodGroup:      { en: 'Blood Group',          te: 'రక్తపు గ్రూపు',          mr: 'रक्तगट',            kn: 'ರಕ್ತದ ಗುಂಪು',       ta: 'இரத்த வகை',         hi: 'रक्त समूह' },
  motherTongue:    { en: 'Mother Tongue',        te: 'మాతృభాష',               mr: 'मातृभाषा',          kn: 'ಮಾತೃಭಾಷೆ',          ta: 'தாய்மொழி',           hi: 'मातृभाषा' },
  education:       { en: 'Education',            te: 'విద్య',                  mr: 'शिक्षण',            kn: 'ಶಿಕ್ಷಣ',            ta: 'கல்வி',              hi: 'शिक्षा' },
  collegeUniversity: { en: 'College / University', te: 'కళాశాల / విశ్వవిద్యాలయం', mr: 'महाविद्यालय / विद्यापीठ', kn: 'ಕಾಲೇಜು / ವಿಶ್ವವಿದ್ಯಾಲಯ', ta: 'கல்லூரி / பல்கலைக்கழகம்', hi: 'कॉलेज / विश्वविद्यालय' },
  occupation:      { en: 'Occupation',           te: 'వృత్తి',                 mr: 'व्यवसाय',           kn: 'ವೃತ್ತಿ',            ta: 'தொழில்',             hi: 'पेशा' },
  employer:        { en: 'Employer',             te: 'యజమాని',                 mr: 'नियोक्ता',          kn: 'ಉದ್ಯೋಗದಾತ',         ta: 'முதலாளி',            hi: 'नियोक्ता' },
  income:          { en: 'Annual Income (INR)',  te: 'వార్షిక ఆదాయం (రూ.)',    mr: 'वार्षिक उत्पन्न (₹)', kn: 'ವಾರ್ಷಿಕ ಆದಾಯ (₹)',  ta: 'ஆண்டு வருமானம் (₹)', hi: 'वार्षिक आय (₹)' },
  workLocation:    { en: 'Work Location',        te: 'పని ప్రదేశం',            mr: 'कामाचे ठिकाण',     kn: 'ಕೆಲಸದ ಸ್ಥಳ',        ta: 'பணிபுரியும் இடம்',  hi: 'कार्यस्थल' },
  city:            { en: 'City',                 te: 'నగరం',                   mr: 'शहर',               kn: 'ನಗರ',               ta: 'நகரம்',              hi: 'शहर' },
  state:           { en: 'State',                te: 'రాష్ట్రం',               mr: 'राज्य',             kn: 'ರಾಜ್ಯ',             ta: 'மாநிலம்',            hi: 'राज्य' },
  country:         { en: 'Country',              te: 'దేశం',                   mr: 'देश',               kn: 'ದೇಶ',               ta: 'நாடு',               hi: 'देश' },
  nativePlace:     { en: 'Native Place',         te: 'స్వస్థలం',               mr: 'मूळ गाव',           kn: 'ಮೂಲ ಸ್ಥಳ',          ta: 'சொந்த ஊர்',         hi: 'मूल स्थान' },
  gotra:           { en: 'Gotra',                te: 'గోత్రం',                 mr: 'गोत्र',             kn: 'ಗೋತ್ರ',             ta: 'கோத்திரம்',          hi: 'गोत्र' },
  kuldevata:       { en: 'Kuldevata',            te: 'కుల దేవత',               mr: 'कुलदेवता',          kn: 'ಕುಲದೇವತೆ',          ta: 'குலதெய்வம்',         hi: 'कुलदेवता' },
  devak:           { en: 'Devak',                te: 'దేవక',                   mr: 'देवक',              kn: 'ದೇವಕ',              ta: 'தேவக்',              hi: 'देवक' },
  surnameClan:     { en: 'Surname / Last name',  te: 'ఇంటిపేరు / చివరి పేరు', mr: 'आडनाव / कुळ',       kn: 'ಉಪನಾಮ / ಕುಲ',       ta: 'குடும்பப் பெயர்',   hi: 'उपनाम / कुल' },
  caste:           { en: 'Caste',                te: 'కులం',                   mr: 'जात',               kn: 'ಜಾತಿ',              ta: 'சாதி',               hi: 'जाति' },
  subCaste:        { en: 'Sub-caste',            te: 'ఉపకులం',                 mr: 'पोटजात',            kn: 'ಉಪಜಾತಿ',            ta: 'உட்சாதி',            hi: 'उपजाति' },
  nakshatram:      { en: 'Nakshatram',           te: 'నక్షత్రం',               mr: 'नक्षत्र',           kn: 'ನಕ್ಷತ್ರ',           ta: 'நட்சத்திரம்',        hi: 'नक्षत्र' },
  rashi:           { en: 'Rashi',                te: 'రాశి',                   mr: 'राशी',              kn: 'ರಾಶಿ',              ta: 'ராசி',               hi: 'राशि' },
  manglik:         { en: 'Manglik',              te: 'మాంగళిక',                mr: 'मांगलिक',           kn: 'ಮಾಂಗಲಿಕ',           ta: 'மாங்கலிகம்',         hi: 'मांगलिक' },
  timeOfBirth:     { en: 'Time of Birth',        te: 'జనన సమయం',               mr: 'जन्म वेळ',          kn: 'ಹುಟ್ಟಿದ ಸಮಯ',       ta: 'பிறந்த நேரம்',      hi: 'जन्म समय' },
  placeOfBirth:    { en: 'Place of Birth',       te: 'జనన ప్రదేశం',            mr: 'जन्मस्थान',         kn: 'ಹುಟ್ಟಿದ ಸ್ಥಳ',      ta: 'பிறந்த இடம்',       hi: 'जन्मस्थान' },
  diet:            { en: 'Diet',                 te: 'ఆహారం',                  mr: 'आहार',              kn: 'ಆಹಾರ',              ta: 'உணவுமுறை',           hi: 'आहार' },
  smokes:          { en: 'Smokes',               te: 'ధూమపానం',                mr: 'धूम्रपान',          kn: 'ಧೂಮಪಾನ',            ta: 'புகைப்பிடிக்கிறார்', hi: 'धूम्रपान' },
  drinks:          { en: 'Drinks',               te: 'మద్యపానం',               mr: 'मद्यपान',           kn: 'ಮದ್ಯಪಾನ',           ta: 'குடிக்கிறார்',       hi: 'मद्यपान' },
  hobbies:         { en: 'Hobbies',              te: 'అభిరుచులు',              mr: 'छंद',               kn: 'ಹವ್ಯಾಸಗಳು',         ta: 'பொழுதுபோக்குகள்',   hi: 'शौक' },
  fatherName:      { en: 'Father Name',          te: 'తండ్రి పేరు',            mr: 'वडिलांचे नाव',     kn: 'ತಂದೆಯ ಹೆಸರು',       ta: 'தந்தையின் பெயர்',   hi: 'पिता का नाम' },
  motherName:      { en: 'Mother Name',          te: 'తల్లి పేరు',             mr: 'आईचे नाव',          kn: 'ತಾಯಿಯ ಹೆಸರು',       ta: 'தாயின் பெயர்',      hi: 'माता का नाम' },
  numFamilyMembers:{ en: 'Family Members',       te: 'కుటుంబ సభ్యులు',         mr: 'कुटुंब सदस्य',     kn: 'ಕುಟುಂಬ ಸದಸ್ಯರು',    ta: 'குடும்ப உறுப்பினர்கள்', hi: 'परिवार के सदस्य' },
  fatherOccupation:{ en: "Father's Occupation",  te: 'తండ్రి వృత్తి',          mr: 'वडिलांचा व्यवसाय', kn: 'ತಂದೆಯ ವೃತ್ತಿ',      ta: 'தந்தையின் தொழில்',  hi: 'पिता का पेशा' },
  motherOccupation:{ en: "Mother's Occupation",  te: 'తల్లి వృత్తి',           mr: 'आईचा व्यवसाय',     kn: 'ತಾಯಿಯ ವೃತ್ತಿ',      ta: 'தாயின் தொழில்',     hi: 'माता का पेशा' },
  numBrothers:     { en: 'Number of Brothers',   te: 'సోదరుల సంఖ్య',           mr: 'भावांची संख्या',    kn: 'ಸಹೋದರರ ಸಂಖ್ಯೆ',     ta: 'சகோதரர்கள் எண்ணிக்கை', hi: 'भाइयों की संख्या' },
  numSisters:      { en: 'Number of Sisters',    te: 'సోదరిల సంఖ్య',           mr: 'बहिणींची संख्या',  kn: 'ಸಹೋದರಿಯರ ಸಂಖ್ಯೆ',   ta: 'சகோதரிகள் எண்ணிக்கை', hi: 'बहनों की संख्या' },
  numBrothersMarried: { en: 'Brothers Married',  te: 'వివాహిత సోదరులు',        mr: 'विवाहित भाऊ',      kn: 'ವಿವಾಹಿತ ಸಹೋದರರು',   ta: 'திருமணமான சகோதரர்கள்', hi: 'विवाहित भाई' },
  numSistersMarried:  { en: 'Sisters Married',   te: 'వివాహిత సోదరిలు',        mr: 'विवाहित बहिणी',    kn: 'ವಿವಾಹಿತ ಸಹೋದರಿಯರು', ta: 'திருமணமான சகோதரிகள்', hi: 'विवाहित बहनें' },
  familyType:      { en: 'Family Type',          te: 'కుటుంబ రకం',             mr: 'कुटुंबाचा प्रकार', kn: 'ಕುಟುಂಬದ ಪ್ರಕಾರ',    ta: 'குடும்ப வகை',        hi: 'परिवार का प्रकार' },
  familyStatus:    { en: 'Family Status',        te: 'కుటుంబ స్థితి',          mr: 'कुटुंबाची स्थिती', kn: 'ಕುಟುಂಬದ ಸ್ಥಿತಿ',    ta: 'குடும்ப நிலை',       hi: 'परिवार की स्थिति' },
  familyValues:    { en: 'Family Values',        te: 'కుటుంబ విలువలు',         mr: 'कौटुंबिक मूल्ये',  kn: 'ಕುಟುಂಬದ ಮೌಲ್ಯಗಳು', ta: 'குடும்ப விழுமியங்கள்', hi: 'पारिवारिक मूल्य' },
  about:           { en: 'About Yourself',       te: 'మీ గురించి',              mr: 'स्वतःबद्दल',       kn: 'ನಿಮ್ಮ ಬಗ್ಗೆ',        ta: 'உங்களை பற்றி',      hi: 'अपने बारे में' },
  partnerExpectations: { en: 'What you are looking for in a partner', te: 'జీవిత భాగస్వామిలో మీరు కోరుకునేవి', mr: 'जोडीदारात काय हवे', kn: 'ಜೀವನ ಸಂಗಾತಿಯಲ್ಲಿ ನೀವು ಏನನ್ನು ಬಯಸುತ್ತೀರಿ', ta: 'துணையில் நீங்கள் எதிர்பார்ப்பது', hi: 'जीवनसाथी में क्या चाहते हैं' },

  // Auth fields
  userHandle:  { en: 'User ID',           te: 'వాడుకరి ID',           mr: 'वापरकर्ता ID',     kn: 'ಬಳಕೆದಾರ ID',        ta: 'பயனர் ID',           hi: 'यूज़र ID' },
  identifier:  { en: 'User ID or Email',  te: 'వాడుకరి ID లేదా ఇమెయిల్', mr: 'वापरकर्ता ID किंवा ईमेल', kn: 'ಬಳಕೆದಾರ ID ಅಥವಾ ಇಮೇಲ್', ta: 'பயனர் ID அல்லது மின்னஞ்சல்', hi: 'यूज़र ID या ईमेल' },
  fullName:    { en: 'Full Name',         te: 'పూర్తి పేరు',           mr: 'पूर्ण नाव',         kn: 'ಪೂರ್ಣ ಹೆಸರು',        ta: 'முழு பெயர்',         hi: 'पूरा नाम' },
  emailAddress:{ en: 'Email Address',     te: 'ఇమెయిల్ చిరునామా',     mr: 'ईमेल पत्ता',        kn: 'ಇಮೇಲ್ ವಿಳಾಸ',        ta: 'மின்னஞ்சல் முகவரி', hi: 'ईमेल पता' },
  phoneNumber: { en: 'Phone Number',      te: 'ఫోన్ నంబర్',           mr: 'फोन नंबर',          kn: 'ಫೋನ್ ನಂಬರ್',         ta: 'தொலைபேசி எண்',       hi: 'फ़ोन नंबर' },
  password:    { en: 'Password',          te: 'పాస్‌వర్డ్',            mr: 'पासवर्ड',           kn: 'ಪಾಸ್‌ವರ್ಡ್',         ta: 'கடவுச்சொல்',         hi: 'पासवर्ड' },
  confirmPassword: { en: 'Confirm Password', te: 'పాస్‌వర్డ్ నిర్ధారించు', mr: 'पासवर्ड पुष्टी करा', kn: 'ಪಾಸ್‌ವರ್ಡ್ ದೃಢೀಕರಿಸಿ', ta: 'கடவுச்சொல்லை உறுதிப்படுத்து', hi: 'पासवर्ड की पुष्टि करें' },
  userIdHint:  { en: '3–30 characters · letters, digits, underscore · must start with a letter', te: '3–30 అక్షరాలు · అక్షరాలు, అంకెలు, అండర్‌స్కోర్ · అక్షరంతో ప్రారంభం', mr: '3–30 अक्षरे · अक्षरे, अंक, अंडरस्कोर · अक्षराने सुरुवात', kn: '3–30 ಅಕ್ಷರಗಳು · ಅಕ್ಷರಗಳು, ಅಂಕಿಗಳು, ಅಂಡರ್‌ಸ್ಕೋರ್ · ಅಕ್ಷರದಿಂದ ಪ್ರಾರಂಭ', ta: '3–30 எழுத்துகள் · எழுத்துகள், இலக்கங்கள், அடிக்கோடு · எழுத்தில் தொடங்க வேண்டும்', hi: '3–30 अक्षर · अक्षर, अंक, अंडरस्कोर · अक्षर से शुरू होना चाहिए' },

  // Wizard/section labels (used as sec.te equivalents)
  secBasicInfo:      { en: 'Basic Information',    te: 'మూల సమాచారం',       mr: 'मूलभूत माहिती',    kn: 'ಮೂಲ ಮಾಹಿತಿ',       ta: 'அடிப்படை தகவல்',    hi: 'बुनियादी जानकारी' },
  secPhysical:       { en: 'Physical',             te: 'శారీరక వివరాలు',    mr: 'शारीरिक माहिती',   kn: 'ದೈಹಿಕ ಮಾಹಿತಿ',     ta: 'உடல் விவரங்கள்',    hi: 'शारीरिक विवरण' },
  secAstrology:      { en: 'Astrology',            te: 'జ్యోతిష్య వివరాలు', mr: 'ज्योतिष माहिती',   kn: 'ಜ್ಯೋತಿಷ್ಯ ಮಾಹಿತಿ', ta: 'ஜோதிட விவரங்கள்',   hi: 'ज्योतिष विवरण' },
  secEducation:      { en: 'Education & Career',   te: 'విద్య & వృత్తి',    mr: 'शिक्षण व करिअर',   kn: 'ಶಿಕ್ಷಣ ಮತ್ತು ವೃತ್ತಿ', ta: 'கல்வி மற்றும் தொழில்', hi: 'शिक्षा और करियर' },
  secFamily:         { en: 'Family',               te: 'కుటుంబ వివరాలు',   mr: 'कुटुंब माहिती',    kn: 'ಕುಟುಂಬ ಮಾಹಿತಿ',    ta: 'குடும்ப விவரங்கள்', hi: 'परिवार विवरण' },
  secLifestyle:      { en: 'Lifestyle',             te: 'జీవనశైలి',          mr: 'जीवनशैली',         kn: 'ಜೀವನಶೈಲಿ',          ta: 'வாழ்க்கை முறை',      hi: 'जीवनशैली' },
  secLocation:       { en: 'Location',              te: 'నివాస స్థానం',      mr: 'ठिकाण',            kn: 'ಸ್ಥಳ',               ta: 'இருப்பிடம்',          hi: 'स्थान' },
  secAbout:          { en: 'About & Expectations',  te: 'పరిచయం',            mr: 'परिचय व अपेक्षा',  kn: 'ಪರಿಚಯ ಮತ್ತು ನಿರೀಕ್ಷೆ', ta: 'பரிச்சயம் மற்றும் எதிர்பார்ப்பு', hi: 'परिचय और अपेक्षाएं' },
  secPhotos:         { en: 'Photos',                te: 'ఫోటోలు',            mr: 'फोटो',              kn: 'ಫೋಟೋಗಳು',           ta: 'புகைப்படங்கள்',      hi: 'फ़ोटो' },

  // Inline hardcoded phrases used in ProfileForm section headers (normal mode)
  pinCode:           { en: 'Pin Code',              te: 'పిన్ కోడ్',          mr: 'पिन कोड',           kn: 'ಪಿನ್ ಕೋಡ್',         ta: 'பின் கோட்',          hi: 'पिन कोड' },
  submitForApproval: { en: 'Submit for Approval',   te: 'అనుమతి కోసం సమర్పించండి', mr: 'मंजुरीसाठी सबमिट करा', kn: 'ಅನುಮೋದನೆಗಾಗಿ ಸಲ್ಲಿಸಿ', ta: 'அங்கீகாரத்திற்கு சமர்ப்பி', hi: 'अनुमोदन के लिए जमा करें' },
};

export type BilingualKey = keyof typeof T;

/**
 * Return the translation of `key` for the given lang.
 * Falls back to Telugu when the lang-specific string is absent.
 */
export function tx(key: BilingualKey, lang: Lang): string {
	const entry = T[key];
	if (!entry) return key;
	if (lang === 'te') return entry.te;
	return (entry as Record<string, string>)[lang] ?? entry.te;
}

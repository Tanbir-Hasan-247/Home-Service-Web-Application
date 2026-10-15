/**
 * ServiceHub Bilingual (English <-> বাংলা) Language Switcher
 * Provides persistent, zero-reload translation across Customer, Worker, and Admin interfaces.
 */

(function () {
    const STORAGE_KEY = 'servicehub_language';

    // Comprehensive Dictionary of ServiceHub UI Phrases
    const TRANSLATIONS = {
        // Navigation & General
        "Home": "হোম",
        "Services": "সার্ভিসসমূহ",
        "How it Works": "কিভাবে কাজ করে",
        "Give Feedback": "ফিডব্যাক দিন",
        "Payments": "পেমেন্ট হিস্ট্রি",
        "About": "আমাদের সম্পর্কে",
        "Contact": "যোগাযোগ",
        "Notifications": "বিজ্ঞপ্তি",
        "Mark all read": "সব পঠিত চিহ্নিত করুন",
        "No notifications yet.": "এখনও কোন বিজ্ঞপ্তি নেই।",
        "Sign In": "লগইন",
        "Get Started": "শুরু করুন",
        "Logout": "লগআউট",
        "Sign out": "সাইন আউট",
        "Admin Dashboard": "অ্যাডমিন ড্যাশবোর্ড",
        "Worker Dashboard": "ওয়ার্কার ড্যাশবোর্ড",
        "Worker Panel": "ওয়ার্কার প্যানেল",
        "Admin Panel": "অ্যাডমিন প্যানেল",
        "My Profile": "আমার প্রোফাইল",
        "My Appointments": "আমার বুকিং",
        "Payment History": "পেমেন্ট হিস্ট্রি",
        "My Earnings": "আমার আয়",
        "Dashboard": "ড্যাশবোর্ড",
        "Available Jobs": "নতুন কাজ",
        "My Active Jobs": "চলমান কাজ",
        "Customer Feedback": "কাস্টমার ফিডব্যাক",
        "Feedbacks": "ফিডব্যাকসমূহ",
        "Colleagues": "সহকর্মীরা",
        "My Wallet & Payouts": "আমার ওয়ালেট ও উইথড্র",
        "Earnings & Payouts": "উপার্জন ও পেমেন্ট",
        "Workers": "ওয়ার্কার্স",
        "Users": "ইউজার্স",
        "Locations": "এলাকা ও শহর",
        "Manage Countries": "দেশ পরিচালনা",
        "Manage States": "বিভাগ পরিচালনা",
        "Manage Cities": "শহর পরিচালনা",
        "Manage Services": "সার্ভিস পরিচালনা",
        "Add Service": "সার্ভিস যোগ করুন",
        "Service Requests": "সার্ভিস রিকোয়েস্ট",
        "Assigned Jobs": "বরাদ্দকৃত কাজ",
        "Worker Withdrawals": "উইথড্র রিকোয়েস্ট",
        "View Main Site": "মূল ওয়েবসাইটে যান",

        // Actions & Buttons
        "Book Now": "বুক করুন",
        "Book Service": "সার্ভিস বুক করুন",
        "View Details": "বিস্তারিত দেখুন",
        "Open in Google Maps": "গুগল ম্যাপে দেখুন",
        "Open GPS in Google Maps": "গুগল ম্যাপে লাইভ রুট",
        "Open Address in Google Maps": "গুগল ম্যাপে ঠিকানা",
        "Live Track (ETA)": "লাইভ ট্র্যাকিং (ETA)",
        "Chat": "চ্যাট করুন",
        "Call": "কল করুন",
        "Call Now": "কল করুন",
        "Cancel": "বাতিল করুন",
        "Back": "ফিরে যান",
        "Start Heading (On The Way)": "রওনা হোন (অন দ্য ওয়ে)",
        "Arrived (Start Work)": "কাজে পৌঁছালাম (কাজ শুরু)",
        "Finish & Mark Completed": "কাজ সমাপ্ত করুন",
        "Complete Job & Log Hours": "কাজ সম্পন্ন ও কাজের সময়",
        "Make Payment": "পেমেন্ট করুন",
        "Download PDF": "PDF ডাউনলোড",
        "View Invoice": "ইনভয়েস দেখুন",
        "Confirm Booking": "বুকিং নিশ্চিত করুন",
        "Withdraw Request": "টাকা তোলার অনুরোধ",
        "Approve": "অনুমোদন করুন",
        "Reject": "বাতিল করুন",
        "Submit": "জমা দিন",
        "Confirm & Generate Bill": "নিশ্চিত করুন ও বিল তৈরি করুন",
        "Update My Location": "বর্তমান লোকেশন আপডেট করুন",
        "Filter tasks": "ফিল্টার করুন",
        "All": "সব",
        "Active": "চলমান",
        "Completed": "সম্পন্ন",
        "Pending": "অপেক্ষমান",

        // Stepper & Statuses
        "Requested": "অনুরোধ করা হয়েছে",
        "Accepted": "গৃহীত",
        "On the Way": "রওনা দিয়েছেন",
        "In Progress": "কাজ চলছে",
        "Cancelled": "বাতিল",
        "Paid": "পরিশোধিত",
        "Paid via Cash": "ক্যাশে পরিশোধিত",
        "Paid via bKash": "বিকাশে পরিশোধিত",
        "Paid via Nagad": "নগদে পরিশোধিত",
        "Paid via Card": "কার্ডে পরিশোধিত",
        "Payment Pending": "পেমেন্ট বাকি আছে",
        "Job Completed": "কাজ সম্পন্ন হয়েছে",

        // Card Labels & Details
        "Customer": "কাস্টমার",
        "Technician": "টেকনিশিয়ান",
        "Customer Address": "কাস্টমারের ঠিকানা",
        "Problem Description": "সমস্যার বিবরণ",
        "Duration": "সময়কাল",
        "Hourly Rate": "ঘণ্টাপ্রতি রেট",
        "Total Amount": "মোট বিল",
        "Total Bill": "মোট বিল",
        "Platform Fee": "প্ল্যাটফর্ম ফি",
        "Your Payout": "আপনার আয়",
        "Your Payout (90%)": "আপনার প্রাপ্য (৯০%)",
        "Platform (10%)": "প্ল্যাটফর্ম (১০%)",
        "Customer Payment": "কাস্টমার পেমেন্ট",
        "Total Hours Worked": "মোট কাজের সময় (ঘণ্টা)",
        "Available Balance": "বর্তমান ব্যালেন্স",
        "Total Withdrawn": "মোট উত্তোলিত",
        "Pending Requests": "অপেক্ষমান অনুরোধ",
        "Monthly Platform Revenue Curve": "মাসিক রেভিনিউ গ্রাফ",
        "Service Demand by City": "শহরভিত্তিক সার্ভিসের চাহিদা",
        "Top Earning Technicians": "শীর্ষ আয়কারী টেকনিশিয়ান",
        "Area Restriction": "এলাকা সীমাবদ্ধতা",
        "Select Service Area": "কাজের এলাকা নির্বাচন করুন",

        // Steps in Booking
        "Step 1: Your Address & Pin": "১ম ধাপ: আপনার ঠিকানা ও পিন",
        "Step 2: Problem Description": "২য় ধাপ: সমস্যার বিবরণ",
        "Step 3: Service Packages & Add-ons (Optional)": "৩য় ধাপ: সার্ভিস প্যাকেজ ও অ্যাড-অন (ঐচ্ছিক)",
        "Summary & Estimation": "সারসংক্ষেপ ও সম্ভাব্য খরচ",
        "Base Hourly Rate": "বেসিক ঘণ্টাপ্রতি রেট",
        "Selected Add-ons": "নির্বাচিত অ্যাড-অনসমূহ",
        "Total Estimated Bill": "আনুমানিক মোট বিল",

        // Footer & Static Pages
        "Popular Services": "জনপ্রিয় সার্ভিসসমূহ",
        "House Cleaning": "বাসা পরিষ্কার",
        "Plumbing": "প্লাম্বিং সার্ভিস",
        "Electrical Work": "বৈদ্যুতিক কাজ",
        "Gardening": "বাগান পরিচর্যা",
        "Support": "সহায়তা",
        "Help Center": "হেল্প সেন্টার",
        "Contact Us": "যোগাযোগ করুন",
        "Safety Center": "নিরাপত্তা কেন্দ্র",
        "Company": "কোম্পানি",
        "About Us": "আমাদের সম্পর্কে",
        "Careers": "ক্যারিয়ার",
        "Terms of Service": "শর্তাবলী",
        "All rights reserved.": "সর্বস্বত্ব সংরক্ষিত।"
    };

    // Sort dictionary keys by length descending to match full phrases before substrings
    const sortedKeys = Object.keys(TRANSLATIONS).sort((a, b) => b.length - a.length);

    // Map to preserve original English text of nodes
    const textNodeOriginals = new WeakMap();

    function translateTextNode(node) {
        if (!node || node.nodeType !== Node.TEXT_NODE) return;
        const currentText = node.nodeValue;
        if (!currentText || !currentText.trim()) return;

        // Remember original text if not already stored
        if (!textNodeOriginals.has(node)) {
            textNodeOriginals.set(node, currentText);
        }

        const originalText = textNodeOriginals.get(node);
        let replacedText = originalText;

        for (let i = 0; i < sortedKeys.length; i++) {
            const enKey = sortedKeys[i];
            const bnVal = TRANSLATIONS[enKey];
            if (replacedText.includes(enKey)) {
                // Exact word or boundary replacement
                const regex = new RegExp(enKey.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
                replacedText = replacedText.replace(regex, bnVal);
            }
        }

        if (replacedText !== currentText) {
            node.nodeValue = replacedText;
        }
    }

    function revertTextNode(node) {
        if (!node || node.nodeType !== Node.TEXT_NODE) return;
        if (textNodeOriginals.has(node)) {
            const originalText = textNodeOriginals.get(node);
            if (node.nodeValue !== originalText) {
                node.nodeValue = originalText;
            }
        }
    }

    function traverseAndApply(element, action) {
        if (!element) return;
        // Skip script and style tags
        const tag = element.tagName ? element.tagName.toUpperCase() : '';
        if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT') return;

        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function (node) {
                    const parentTag = node.parentNode ? node.parentNode.tagName.toUpperCase() : '';
                    if (parentTag === 'SCRIPT' || parentTag === 'STYLE' || parentTag === 'NOSCRIPT' || parentTag === 'CODE') {
                        return NodeFilter.FILTER_REJECT;
                    }
                    if (node.nodeValue && node.nodeValue.trim().length > 0) {
                        return NodeFilter.FILTER_ACCEPT;
                    }
                    return NodeFilter.FILTER_SKIP;
                }
            },
            false
        );

        let currentNode;
        while ((currentNode = walker.nextNode())) {
            if (action === 'translate') {
                translateTextNode(currentNode);
            } else {
                revertTextNode(currentNode);
            }
        }
    }

    function updateLanguageUI(lang) {
        const enButtons = document.querySelectorAll('.lang-btn-en');
        const bnButtons = document.querySelectorAll('.lang-btn-bn');

        if (lang === 'bn') {
            enButtons.forEach(btn => {
                btn.classList.remove('btn-primary', 'text-white');
                btn.classList.add('btn-dark', 'text-secondary');
            });
            bnButtons.forEach(btn => {
                btn.classList.remove('btn-dark', 'text-secondary');
                btn.classList.add('btn-primary', 'text-white');
            });
        } else {
            enButtons.forEach(btn => {
                btn.classList.remove('btn-dark', 'text-secondary');
                btn.classList.add('btn-primary', 'text-white');
            });
            bnButtons.forEach(btn => {
                btn.classList.remove('btn-primary', 'text-white');
                btn.classList.add('btn-dark', 'text-secondary');
            });
        }
    }

    window.setSiteLanguage = function (lang) {
        if (lang !== 'en' && lang !== 'bn') return;
        localStorage.setItem(STORAGE_KEY, lang);
        updateLanguageUI(lang);

        if (lang === 'bn') {
            traverseAndApply(document.body, 'translate');
        } else {
            traverseAndApply(document.body, 'revert');
        }
    };

    window.getSiteLanguage = function () {
        return localStorage.getItem(STORAGE_KEY) || 'en';
    };

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function () {
        const currentLang = window.getSiteLanguage();
        updateLanguageUI(currentLang);
        if (currentLang === 'bn') {
            // Apply slight timeout to ensure all template blocks are parsed
            setTimeout(() => {
                traverseAndApply(document.body, 'translate');
            }, 50);
        }

        // Observe DOM modifications (e.g. modals opening, chat messages, dynamic updates)
        let scheduled = false;
        const observer = new MutationObserver(function (mutations) {
            if (window.getSiteLanguage() !== 'bn') return;
            if (!scheduled) {
                scheduled = true;
                requestAnimationFrame(() => {
                    scheduled = false;
                    for (let mutation of mutations) {
                        for (let node of mutation.addedNodes) {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                traverseAndApply(node, 'translate');
                            } else if (node.nodeType === Node.TEXT_NODE) {
                                translateTextNode(node);
                            }
                        }
                    }
                });
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
})();


import React, { useEffect, useState } from 'react';
import { Search, HelpCircle } from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import { listFaqs } from '../api/faq';

const CATEGORIES = [
  { key: 'all', label: 'All Questions' },
  { key: 'rooms', label: 'Rooms & Rates' },
  { key: 'utilities', label: 'Utilities' },
  { key: 'policies', label: 'Policies' },
  { key: 'payments', label: 'Payments & Deposits' },
  { key: 'amenities', label: 'Amenities' },
  { key: 'moveout', label: 'Move-Out' },
  { key: 'safety', label: 'Safety & Security' },
];

export default function FaqPage() {
  const [faqs, setFaqs] = useState([]);
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchFaqs() {
      try {
        const data = await listFaqs();
        setFaqs(data);
      } catch {
        // If API fails, load local fallback
        setFaqs(LOCAL_FAQS);
      } finally {
        setLoading(false);
      }
    }
    fetchFaqs();
  }, []);

  const filtered = faqs.filter((f) => {
    const matchesSearch =
      !search ||
      f.question?.toLowerCase().includes(search.toLowerCase()) ||
      f.answer?.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = activeCategory === 'all' || f.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div>
      <PageHeader
        title="Frequently Asked Questions"
        subtitle="DormTel Inquiry FAQ — based on real prospect questions"
      />

      {/* Search & Filters */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 mb-6">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search questions..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-navy"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((c) => (
            <button
              key={c.key}
              onClick={() => setActiveCategory(c.key)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                activeCategory === c.key
                  ? 'bg-brand-navy text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* FAQ List */}
      {loading ? (
        <div className="text-sm text-gray-500">Loading FAQs...</div>
      ) : (
        <div className="space-y-3">
          {filtered.map((faq, idx) => (
            <details
              key={faq.id || idx}
              className="bg-white rounded-lg border border-gray-200 shadow-sm group"
            >
              <summary className="flex items-start gap-3 px-4 py-3 cursor-pointer list-none">
                <HelpCircle className="w-5 h-5 text-brand-navy flex-shrink-0 mt-0.5" />
                <span className="text-sm font-medium text-gray-900">{faq.question}</span>
              </summary>
              <div className="px-4 pb-4 pl-12">
                <p className="text-sm text-gray-600 whitespace-pre-line">{faq.answer}</p>
                {faq.category && (
                  <span className="inline-block mt-2 px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">
                    {faq.category}
                  </span>
                )}
              </div>
            </details>
          ))}
          {filtered.length === 0 && (
            <div className="text-sm text-gray-500 text-center py-8">
              No questions match your search.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Fallback data from DORMTEL DETAILS.xlsx wishlist
const LOCAL_FAQS = [
  { question: "What types of rooms are available?", answer: "For Recto we have rooms for 2, 4, 6, 8 & 10.\nFor Sta. Mesa we have rooms for 2, 4, 6, & 8.", category: "rooms" },
  { question: "How much is the monthly rent?", answer: "FOR RECTO BRANCH\nRoom for 2 (Loft Type): PHP 6,500\nRoom for 4 (Lower Bunk): PHP 5,500 | (Upper Bunk): PHP 5,300\nRoom for 6 (Loft Type): PHP 4,500\nRoom for 8 (Lower Bunk): PHP 4,000 | (Upper Bunk): PHP 3,800 | (Loft Type): PHP 4,100\nRoom for 10 (Lower Bunk): PHP 3,600 | (Upper Bunk): PHP 3,500\n\nFOR STA. MESA BRANCH\nRoom for 2 (Loft Type): PHP 6,000\nRoom for 4 (Lower Bunk): PHP 5,400 | (Upper Bunk): PHP 5,200\nRoom for 6 (Loft Type): PHP 4,300\nRoom for 8 (Loft Type): PHP 4,100", category: "rooms" },
  { question: "Are utilities included in the rent?", answer: "Utilities are excluded from the rent.\n\nFor electricity, charges will be based on your actual consumption at a rate of PHP 14.56 per kWh, with a sub-meter provided.\n\nFor water, the charge will be based on the monthly cubic meter (cu.m) rate.", category: "utilities" },
  { question: "Is there a minimum stay requirement?", answer: "Yes, 1 month.", category: "policies" },
  { question: "Is the dormitory exclusive for male or female tenants?", answer: "The dorm accepts both male and female tenants, with rooms segregated by gender. Mixed-gender room arrangements are also allowed, provided that each dormer submits a parental consent form.", category: "policies" },
  { question: "How many occupants are allowed per room?", answer: "For Recto we have rooms for 2, 4, 6, 8 & 10.\nFor Sta. Mesa we have rooms for 2, 4, 6 & 8.", category: "rooms" },
  { question: "Is the dormitory open to students only?", answer: "No. We also accept reviewees, working professionals, backpackers & travellers.", category: "policies" },
  { question: "How can I reserve a room?", answer: "You may walk in at the admin office & pay cash or pay via online payment. Admin to provide bank details.", category: "rooms" },
  { question: "Is there a reservation fee or security deposit?", answer: "Yes, we collect the following:\n1 month advance, 1 month security deposit. Utility deposit & pro-rate rental if needed.", category: "payments" },
  { question: "What payment methods are accepted?", answer: "Cash payment or bank transfer.", category: "payments" },
  { question: "When is the monthly due date for rent?", answer: "Every 5th of the month.", category: "payments" },
  { question: "Are late payment penalties applied?", answer: "Yes, 5% penalty shall be applied for late payments.", category: "payments" },
  { question: "Is the deposit refundable?", answer: "Yes, security deposit is refundable after deductions of consumed water & electricity on the last month of stay.", category: "payments" },
  { question: "Is Wi-Fi available?", answer: "Yes, free Wi-Fi at the lobby area.", category: "amenities" },
  { question: "Are rooms fully furnished?", answer: "No, the dorm is a bare unit but provides mattress for bed.", category: "amenities" },
  { question: "Is air conditioning included?", answer: "Air-conditioned rooms are included (window/Split type).", category: "amenities" },
  { question: "Is there a study area or lounge?", answer: "Yes, at the lobby area we provide tables & chairs for dormers.", category: "amenities" },
  { question: "Are cooking and laundry allowed?", answer: "Yes, we have tie-up laundry shops & dormers can also do DIY laundry. Cooking using rice cooker is currently allowed.", category: "amenities" },
  { question: "Is parking available for tenants?", answer: "For Recto Branch, none. Street parking provided by the cityhall only and with pay.\nFor Sta. Mesa, we have motorcycle parking at PHP 1,500 monthly & PHP 2,500 for small cars.", category: "amenities" },
  { question: "Are visitors allowed inside the dormitory?", answer: "Visitors are allowed at the lobby.", category: "policies" },
  { question: "What are the dormitory curfew hours?", answer: "Visitors are only permitted in the lobby area from 8:00 AM to 8:00 PM.", category: "policies" },
  { question: "Are pets allowed?", answer: "Pets are not allowed.", category: "policies" },
  { question: "Is smoking or drinking prohibited?", answer: "Smoking & drinking inside the dorm premises are not allowed.", category: "policies" },
  { question: "What happens if a tenant violates dormitory rules?", answer: "Guidelines are provided to all tenants upon move-in, including the rules, regulations, and corresponding penalties.", category: "policies" },
  { question: "Can tenants transfer to another room?", answer: "Tenants are not allowed on room hopping. Room transfers shall be done with admin's assistance.", category: "policies" },
  { question: "Is the dormitory secured 24/7?", answer: "We have CCTV Monitors 24/7, admin on duty from 8am to 5pm. Housekeeping from 11am to 8pm & Security Guard on duty from 8pm to 8am.", category: "safety" },
  { question: "Are CCTV cameras installed?", answer: "Yes, we have CCTV monitors inside the dorm.", category: "safety" },
  { question: "Is there a guard or staff on duty?", answer: "Yes, from 8pm to 8am.", category: "safety" },
  { question: "What should tenants do during emergencies?", answer: "We have emergency hotline numbers posted at the back of each room door that tenants can call during emergencies. They may also immediately inform the admin or other staff members for a faster response. Additionally, all dormers are given a tour of the building during move-in, including the location of the fire exits and emergency escape routes.", category: "safety" },
  { question: "How do I report maintenance issues?", answer: "Dormers may personally visit the admin office to report concerns, or they may contact the admin through text message, Viber, or the Facebook page. During move-in, tenants are also provided with the admin's contact details for easier communication regarding any concerns or inquiries.", category: "amenities" },
  { question: "How long does maintenance usually take?", answer: "Maintenance response time depends on the type of concern. Minor repairs, such as faucet issues or clogged sinks, are usually resolved within a few hours, while major repairs, including air conditioning concerns, may take more than two days depending on the issue and parts availability. Rest assured that our team always exerts its best efforts to address and resolve maintenance concerns as quickly as possible.", category: "amenities" },
  { question: "What documents are required before moving in?", answer: "1 copy of 2x2 photos, 2 valid IDs.", category: "moveout" },
  { question: "What items should tenants bring?", answer: "Own pillow, bed cover, blanket & personal items. Appliances such as electric fan, rice cooker & kettle are allowed.", category: "amenities" },
  { question: "What is the move-out process?", answer: "The dormer shall need to secure move-out clearance, where they will be able to know whether they will be getting a refund or have to pay additional amount for the last month's consumption.", category: "moveout" },
  { question: "How long does it take to receive the deposit refund after move-out?", answer: "Refund will be processed within 60 working days upon move-out.", category: "moveout" },
  { question: "Can tenants check billing statements online?", answer: "Billing statement will be sent to dormers' provided email.", category: "payments" },
  { question: "Is there an online announcement or notification system?", answer: "Currently we post on walls near elevators for dormers to see.", category: "amenities" },
];

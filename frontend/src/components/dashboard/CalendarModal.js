import React, { useEffect, useState } from 'react';
import Modal from '../ui/Modal';
import { getDashboardEvents } from '../../api/dashboard';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export default function CalendarModal({ isOpen, onClose, type }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    getDashboardEvents(type, year, month)
      .then((res) => setEvents(res || []))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, [isOpen, type, year, month]);

  const title = type === 'movein' ? 'Scheduled Move-ins' : 'Scheduled Move-outs';

  const daysInMonth = new Date(year, month, 0).getDate();
  const firstDay = new Date(year, month - 1, 1).getDay();

  const eventMap = {};
  events.forEach((ev) => {
    const d = new Date(ev.date).getDate();
    eventMap[d] = ev;
  });

  const prevMonth = () => {
    if (month === 1) {
      setMonth(12);
      setYear(year - 1);
    } else {
      setMonth(month - 1);
    }
  };

  const nextMonth = () => {
    if (month === 12) {
      setMonth(1);
      setYear(year + 1);
    } else {
      setMonth(month + 1);
    }
  };

  const monthName = new Date(year, month - 1, 1).toLocaleString('en-PH', { month: 'long', year: 'numeric' });

  const days = [];
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let i = 1; i <= daysInMonth; i++) days.push(i);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="lg">
      <div className="flex items-center justify-between mb-4">
        <button onClick={prevMonth} className="p-1 rounded hover:bg-gray-100"><ChevronLeft className="w-5 h-5" /></button>
        <span className="font-semibold text-gray-800">{monthName}</span>
        <button onClick={nextMonth} className="p-1 rounded hover:bg-gray-100"><ChevronRight className="w-5 h-5" /></button>
      </div>

      {loading ? (
        <div className="py-8 text-center text-gray-500">Loading...</div>
      ) : (
        <>
          <div className="grid grid-cols-7 gap-1 mb-2">
            {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map((d) => (
              <div key={d} className="text-xs font-medium text-gray-500 text-center py-1">{d}</div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {days.map((d, idx) => (
              <div key={idx} className={`min-h-[80px] border rounded-md p-1 ${d ? 'bg-white border-gray-200' : 'bg-gray-50 border-transparent'}`}>
                {d && (
                  <>
                    <div className="text-xs font-medium text-gray-700 mb-1">{d}</div>
                    {eventMap[d] && (
                      <div className="text-[10px] bg-brand-navy text-white rounded px-1 py-0.5 truncate">
                        {eventMap[d].count} {eventMap[d].count === 1 ? 'resident' : 'residents'}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>

          {events.length > 0 && (
            <div className="mt-4 space-y-2 max-h-48 overflow-y-auto">
              <h4 className="text-sm font-semibold text-gray-700">Upcoming</h4>
              {events.map((ev) => (
                <div key={ev.date} className="text-sm border rounded-md p-2 bg-gray-50">
                  <div className="font-medium text-gray-800">{new Date(ev.date).toLocaleDateString('en-PH', { month: 'short', day: 'numeric' })}</div>
                  <div className="text-xs text-gray-600 mt-1">
                    {ev.residents.map((r) => r.full_name).join(', ')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </Modal>
  );
}

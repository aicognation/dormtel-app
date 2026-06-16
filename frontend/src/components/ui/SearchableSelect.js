import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, X } from 'lucide-react';

export default function SearchableSelect({ label, options = [], value, onChange, placeholder = 'Search...', name }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const containerRef = useRef(null);
  const inputRef = useRef(null);

  const selected = options.find((o) => o.value === value);

  const filtered = options.filter((o) =>
    o.label.toLowerCase().includes(query.toLowerCase())
  );

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleSelect = (opt) => {
    onChange({ target: { name, value: opt.value } });
    setQuery('');
    setIsOpen(false);
  };

  const handleClear = (e) => {
    e.stopPropagation();
    onChange({ target: { name, value: '' } });
    setQuery('');
  };

  return (
    <div ref={containerRef} className="relative">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      )}
      <div
        className="flex items-center border border-gray-300 rounded-md bg-white cursor-pointer focus-within:ring-2 focus-within:ring-brand-navy/30 focus-within:border-brand-navy"
        onClick={() => {
          setIsOpen(true);
          setTimeout(() => inputRef.current?.focus(), 0);
        }}
      >
        <input
          ref={inputRef}
          type="text"
          className="flex-1 px-3 py-2 text-sm outline-none bg-transparent placeholder-gray-400 rounded-md"
          placeholder={selected ? selected.label : placeholder}
          value={isOpen ? query : (selected ? selected.label : '')}
          onChange={(e) => {
            setQuery(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
        />
        <div className="flex items-center pr-2 gap-1">
          {value && (
            <button type="button" onClick={handleClear} className="p-0.5 text-gray-400 hover:text-gray-600">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </div>

      {isOpen && (
        <ul className="absolute z-50 mt-1 w-full max-h-48 overflow-auto bg-white border border-gray-200 rounded-md shadow-lg">
          {filtered.length === 0 ? (
            <li className="px-3 py-2 text-sm text-gray-400">No rooms match</li>
          ) : (
            filtered.map((opt) => (
              <li
                key={opt.value}
                onClick={() => handleSelect(opt)}
                className={`px-3 py-2 text-sm cursor-pointer hover:bg-brand-navy/5 ${
                  opt.value === value ? 'bg-brand-navy/10 text-brand-navy font-medium' : 'text-gray-700'
                }`}
              >
                {opt.label}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}

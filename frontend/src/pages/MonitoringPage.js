import React, { useEffect, useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import { BarChart3, RefreshCw, BedDouble, Users, TrendingUp, Home } from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import StatCard from '../components/ui/StatCard';
import Button from '../components/ui/Button';
import DataTable from '../components/ui/DataTable';
import { getDailyMonitoring, getCurrentOccupancy } from '../api/monitoring';
import { formatCurrency } from '../utils/formatters';
import { useProperty } from '../contexts/PropertyContext';

const PROPERTIES = [
  { value: 'DT01', label: 'Recto Branch' },
  { value: 'DT02', label: 'Sta. Mesa Branch' },
];

export default function MonitoringPage() {
  const { propertyCode: contextPropertyCode } = useProperty();
  const [propertyCode, setPropertyCode] = useState(contextPropertyCode || 'DT01');
  const [year, setYear] = useState(2026);
  const [month, setMonth] = useState(4);
  const [report, setReport] = useState(null);
  const [occupancy, setOccupancy] = useState(null);
  const [loading, setLoading] = useState(true);

  // Sync local propertyCode with global PropertyContext selection
  useEffect(() => {
    if (contextPropertyCode) {
      setPropertyCode(contextPropertyCode);
    }
  }, [contextPropertyCode]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [dailyRes, occRes] = await Promise.allSettled([
        getDailyMonitoring({ property_code: propertyCode, year, month }),
        getCurrentOccupancy({ property_code: propertyCode }),
      ]);
      if (dailyRes.status === 'fulfilled') {
        setReport(dailyRes.value);
      } else {
        toast.error('Failed to load daily monitoring data');
      }
      if (occRes.status === 'fulfilled') {
        setOccupancy(occRes.value);
      }
    } finally {
      setLoading(false);
    }
  }, [propertyCode, year, month]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const columns = [
    {
      key: 'date',
      label: 'Date',
      render: (row) => {
        const d = new Date(row.date);
        return d.toLocaleDateString('en-PH', { month: 'short', day: 'numeric' });
      },
    },
    { key: 'nob', label: 'NOB' },
    { key: 'nod', label: 'NOD' },
    { key: 'target_occupancy', label: 'Target' },
    { key: 'actual_occupancy', label: 'Actual' },
    {
      key: 'variance',
      label: 'Variance',
      render: (row) => {
        const v = row.variance;
        const color = v >= 0 ? 'text-green-600' : 'text-red-600';
        return <span className={`font-semibold ${color}`}>{v > 0 ? `+${v}` : v}</span>;
      },
    },
    {
      key: 'occupancy_rate',
      label: 'Occ. Rate',
      render: (row) => `${(parseFloat(row.occupancy_rate) * 100).toFixed(1)}%`,
    },
    {
      key: 'room_sales_actual',
      label: 'Room Sales',
      render: (row) => formatCurrency(row.room_sales_actual),
    },
    {
      key: 'total_sales_actual',
      label: 'Total Sales',
      render: (row) => formatCurrency(row.total_sales_actual),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Daily Monitoring Report"
        subtitle="Track occupancy, variance, and room sales by property and month"
        icon={BarChart3}
      />

      {/* Controls */}
      <div className="flex flex-wrap gap-3 mb-6 bg-white rounded-lg border border-gray-200 shadow-sm p-4">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Branch</label>
          <select
            value={propertyCode}
            onChange={(e) => setPropertyCode(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            {PROPERTIES.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Year</label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="w-24 rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Month</label>
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            {Array.from({ length: 12 }, (_, i) => (
              <option key={i + 1} value={i + 1}>
                {new Date(2000, i, 1).toLocaleString('en-PH', { month: 'long' })}
              </option>
            ))}
          </select>
        </div>
        <Button variant="ghost" onClick={fetchData} className="ml-auto">
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      {/* Occupancy Snapshot */}
      {occupancy && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard
            label="Total Beds"
            value={occupancy.total_beds}
            icon={BedDouble}
          />
          <StatCard
            label="Occupied Beds"
            value={occupancy.occupied_beds}
            icon={Users}
          />
          <StatCard
            label="Available Beds"
            value={occupancy.available_beds}
            icon={Home}
          />
          <StatCard
            label="Occupancy Rate"
            value={`${(occupancy.occupancy_rate * 100).toFixed(1)}%`}
            icon={TrendingUp}
          />
        </div>
      )}

      {/* Daily Table */}
      {report && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
              {report.month} — {propertyCode === 'DT01' ? 'Recto Branch' : 'Sta. Mesa Branch'}
            </h3>
            {report.summary && (
              <div className="flex flex-wrap gap-4 text-sm">
                <span className="text-gray-600">
                  Avg Rate: <strong>{(parseFloat(report.summary.avg_occupancy_rate) * 100).toFixed(1)}%</strong>
                </span>
                <span className="text-gray-600">
                  Total Sales: <strong>{formatCurrency(report.summary.total_room_sales_actual)}</strong>
                </span>
                <span className={parseFloat(report.summary.variance) >= 0 ? 'text-green-600' : 'text-red-600'}>
                  Variance: <strong>{formatCurrency(report.summary.variance)}</strong>
                </span>
              </div>
            )}
          </div>
          <DataTable
            columns={columns}
            data={report.daily_rows || []}
            loading={loading}
            emptyMessage="No daily records found"
          />
        </div>
      )}
    </div>
  );
}

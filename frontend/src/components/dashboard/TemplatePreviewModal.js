import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, FileSpreadsheet, Calendar, Users, Info } from 'lucide-react';
import Modal from '../ui/Modal';
import Button from '../ui/Button';

const statusConfig = {
  valid: { icon: CheckCircle2, color: 'text-green-600', bg: 'bg-green-50 border-green-200', label: 'Template Compatible' },
  warnings: { icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50 border-amber-200', label: 'Compatible with Warnings' },
  invalid: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50 border-red-200', label: 'Template Incompatible' },
};

const severityIcon = {
  error: <XCircle className="w-4 h-4 text-red-500 shrink-0" />,
  warning: <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />,
  info: <Info className="w-4 h-4 text-blue-500 shrink-0" />,
};

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function TemplatePreviewModal({ isOpen, onClose, onProceed, validationResult, uploadType, loading }) {
  if (!validationResult) return null;

  const { overall_status, issues, sheets, summary, file_name, file_size_bytes } = validationResult;
  const cfg = statusConfig[overall_status] || statusConfig.invalid;
  const StatusIcon = cfg.icon;
  const canProceed = overall_status !== 'invalid';
  const errors = issues.filter(i => i.severity === 'error');
  const warnings = issues.filter(i => i.severity === 'warning');
  const infos = issues.filter(i => i.severity === 'info');

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Template Compatibility Check" size="lg">
      <div className="space-y-4">
        {/* File info */}
        <div className="flex items-center gap-3 text-sm text-gray-600">
          <FileSpreadsheet className="w-4 h-4" />
          <span className="font-medium text-gray-900">{file_name}</span>
          <span className="text-gray-400">|</span>
          <span>{formatFileSize(file_size_bytes)}</span>
          <span className="text-gray-400">|</span>
          <span className="capitalize">{uploadType === 'daily_sheet' ? 'Daily Sheet' : 'Standard'} Upload</span>
        </div>

        {/* Status banner */}
        <div className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${cfg.bg}`}>
          <StatusIcon className={`w-6 h-6 ${cfg.color}`} />
          <div>
            <p className={`font-semibold ${cfg.color}`}>{cfg.label}</p>
            <p className="text-sm text-gray-600">
              {overall_status === 'valid' && 'File structure matches the expected template. Ready to upload.'}
              {overall_status === 'warnings' && 'File structure is mostly correct but has some warnings. You may proceed.'}
              {overall_status === 'invalid' && 'File structure does not match the expected template. Please fix the issues below or download the correct template.'}
            </p>
          </div>
        </div>

        {/* Sheet previews */}
        {sheets.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-700">Sheet Summary</h3>
            {sheets.map((sheet, idx) => (
              <div key={idx} className="bg-gray-50 rounded-lg border border-gray-200 p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900">Sheet: "{sheet.name}"</span>
                  <span className="text-xs text-gray-500">Row {sheet.header_row_index} header</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs text-gray-600">
                  {sheet.date_column_count != null && (
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {sheet.date_column_count} date columns
                      {sheet.detected_month && sheet.detected_year && (
                        <span className="text-gray-400">({sheet.detected_month} {sheet.detected_year})</span>
                      )}
                    </div>
                  )}
                  {sheet.date_range_start && sheet.date_range_end && (
                    <div className="col-span-2 text-gray-500">
                      Range: {sheet.date_range_start} → {sheet.date_range_end}
                    </div>
                  )}
                  <div className="flex items-center gap-1">
                    <Users className="w-3 h-3" />
                    {sheet.data_row_count} data row(s)
                  </div>
                  {sheet.has_bed_column != null && (
                    <div>Bed column: {sheet.has_bed_column ? 'Found' : 'Not found'}</div>
                  )}
                  {sheet.format_variant && (
                    <div>Format: {sheet.format_variant.replace(/_/g, ' ')}</div>
                  )}
                  {sheet.has_total_usage != null && (
                    <div>Total Usage: {sheet.has_total_usage ? 'Yes' : 'No'}</div>
                  )}
                  {sheet.has_water_bill != null && (
                    <div>Water Bill: {sheet.has_water_bill ? 'Yes' : 'No'}</div>
                  )}
                  {sheet.misc_columns.length > 0 && (
                    <div className="col-span-2">Misc: {sheet.misc_columns.join(', ')}</div>
                  )}
                </div>
                {sheet.missing_headers.length > 0 && (
                  <div className="mt-2 text-xs text-red-600">
                    Missing: {sheet.missing_headers.join(', ')}
                  </div>
                )}
                {sheet.extra_headers.length > 0 && (
                  <div className="mt-1 text-xs text-gray-500">
                    Extra (ignored): {sheet.extra_headers.join(', ')}
                  </div>
                )}
                {/* Sample rows */}
                {sheet.sample_rows.length > 0 && (
                  <details className="mt-2">
                    <summary className="text-xs text-blue-600 cursor-pointer hover:underline">Preview first {sheet.sample_rows.length} row(s)</summary>
                    <div className="mt-1 overflow-x-auto">
                      <table className="text-xs border-collapse w-full">
                        <tbody>
                          {sheet.sample_rows.map((row, ri) => (
                            <tr key={ri} className="border-b border-gray-200">
                              {row.map((cell, ci) => (
                                <td key={ci} className="px-2 py-1 border-r border-gray-100 max-w-[120px] truncate" title={cell}>
                                  {cell || <span className="text-gray-300">—</span>}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </details>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Issues */}
        {(errors.length > 0 || warnings.length > 0 || infos.length > 0) && (
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-700">Issues</h3>
            {[...errors, ...warnings, ...infos].map((issue, idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm">
                {severityIcon[issue.severity]}
                <div>
                  <span className="text-gray-800">{issue.message}</span>
                  {issue.sheet && <span className="text-gray-400 text-xs ml-1">({issue.sheet})</span>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Disclaimer */}
        {canProceed && (
          <p className="text-xs text-gray-400 italic">
            Structure looks good. Content (resident names, room numbers) will be validated during the actual upload.
          </p>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-2 border-t border-gray-200">
          <Button variant="secondary" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button
            onClick={onProceed}
            disabled={!canProceed || loading}
            loading={loading}
          >
            {canProceed ? 'Proceed with Upload' : 'Cannot Upload — Fix Issues First'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

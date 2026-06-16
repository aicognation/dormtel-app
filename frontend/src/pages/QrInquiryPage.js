import React, { useState, useRef } from 'react';
import toast from 'react-hot-toast';
import { QrCode, Send, RotateCcw, Download } from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import FormField from '../components/ui/FormField';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import { createInquiry } from '../api/inquiries';

const PROPERTIES = [
  { value: 'DT01', label: 'Recto Branch' },
  { value: 'DT02', label: 'Sta. Mesa Branch' },
];

const SOURCES = [
  { value: 'walkin', label: 'Walk-in' },
  { value: 'phone', label: 'Phone' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'referral', label: 'Referral' },
  { value: 'website', label: 'Website' },
];

const STATUS_OPTIONS = [
  { value: 'student', label: 'Student' },
  { value: 'working', label: 'Working' },
  { value: 'reviewee', label: 'Reviewee' },
  { value: 'backpacker', label: 'Backpacker / Traveller' },
];

const LENGTH_OPTIONS = [
  { value: '1_month', label: '1 Month' },
  { value: '2_months', label: '2 Months' },
  { value: '3_months', label: '3 Months' },
  { value: '6_months', label: '6 Months' },
  { value: '1_year', label: '1 Year' },
  { value: 'indefinite', label: 'Indefinite / Until Exam' },
];

const INITIAL_FORM = {
  prospect_name: '',
  prospect_phone: '',
  prospect_email: '',
  address: '',
  school: '',
  course: '',
  review_center: '',
  exam_date: '',
  property_code: 'DT01',
  source: 'walkin',
  status_detail: 'student',
  company_name: '',
  first_time_dormer: true,
  previous_dorm: '',
  desired_move_in_date: '',
  length_of_stay: '',
  content: '',
};

export default function QrInquiryPage() {
  const [form, setForm] = useState({ ...INITIAL_FORM });
  const [submitting, setSubmitting] = useState(false);
  const [showQrModal, setShowQrModal] = useState(false);
  const [qrForm, setQrForm] = useState({
    branch: 'DT01',
    startDate: '',
    endDate: '',
  });
  const [generatedQr, setGeneratedQr] = useState(null);
  const downloadRef = useRef(null);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        content: form.content || `Inquiry from ${form.prospect_name} via ${form.source}`,
        inquiry_form_data: {
          status_detail: form.status_detail,
          company_name: form.company_name,
          submitted_via: 'qr_form',
        },
      };
      await createInquiry(payload);
      toast.success('Inquiry submitted successfully');
      setForm({ ...INITIAL_FORM });
    } catch {
      toast.error('Failed to submit inquiry');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => setForm({ ...INITIAL_FORM });

  const handleGenerateQr = () => {
    const branchLabel = PROPERTIES.find((p) => p.value === qrForm.branch)?.label || qrForm.branch;
    const qrData = `dormtel://inquiry?branch=${encodeURIComponent(qrForm.branch)}&start=${qrForm.startDate}&end=${qrForm.endDate}&label=${encodeURIComponent(branchLabel)}`;
    const qrImageUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(qrData)}`;

    setGeneratedQr({
      url: qrImageUrl,
      data: qrData,
      branchLabel,
      fileName: `DormTel_QR_${qrForm.branch}_${qrForm.startDate}_to_${qrForm.endDate}.png`,
    });
  };

  const handleDownload = async () => {
    if (!generatedQr) return;
    try {
      const response = await fetch(generatedQr.url);
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = generatedQr.fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setTimeout(() => URL.revokeObjectURL(blobUrl), 5000);
      toast.success('QR Code downloaded');
    } catch {
      toast.error('Failed to download QR code');
    }
  };

  const handleCloseModal = () => {
    setShowQrModal(false);
    setGeneratedQr(null);
    setQrForm({ branch: 'DT01', startDate: '', endDate: '' });
  };

  return (
    <div>
      <div className="flex items-start justify-between">
        <PageHeader
          title="QR Inquiry Form"
          subtitle="Capture prospect details from walk-ins, calls, and social media"
          icon={QrCode}
        />
        <div className="mt-1">
          <Button type="button" variant="accent" onClick={() => setShowQrModal(true)}>
            <Download className="w-4 h-4 mr-1" /> Generate QR
          </Button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 space-y-6">
        {/* Section: Prospect Info */}
        <div>
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">Prospect Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <FormField
              label="Full Name" name="prospect_name" required
              value={form.prospect_name} onChange={handleChange}
              placeholder="Juan Dela Cruz"
            />
            <FormField
              label="Cellphone" name="prospect_phone" required
              value={form.prospect_phone} onChange={handleChange}
              placeholder="09XX XXX XXXX"
            />
            <FormField
              label="Email" name="prospect_email" type="email"
              value={form.prospect_email} onChange={handleChange}
              placeholder="juan@example.com"
            />
            <FormField
              label="Address" name="address"
              value={form.address} onChange={handleChange}
              placeholder="Current home address"
              className="md:col-span-2 lg:col-span-3"
            />
          </div>
        </div>

        {/* Section: Academic / Professional */}
        <div>
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">Academic / Professional Details</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <FormField
              label="Status" name="status_detail" type="select"
              value={form.status_detail} onChange={handleChange}
              options={STATUS_OPTIONS}
            />
            {form.status_detail === 'working' && (
              <FormField
                label="Company Name" name="company_name"
                value={form.company_name} onChange={handleChange}
                placeholder="Employer name"
              />
            )}
            <FormField
              label="School / University" name="school"
              value={form.school} onChange={handleChange}
              placeholder="e.g. UE, PUP, UST"
            />
            <FormField
              label="Course / Program" name="course"
              value={form.course} onChange={handleChange}
              placeholder="e.g. Nursing, Engineering"
            />
            <FormField
              label="Review Center" name="review_center"
              value={form.review_center} onChange={handleChange}
              placeholder="If reviewee"
            />
            <FormField
              label="Exam Date" name="exam_date" type="date"
              value={form.exam_date} onChange={handleChange}
            />
          </div>
        </div>

        {/* Section: Dorm Preference */}
        <div>
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">Dormitory Preference</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <FormField
              label="Branch" name="property_code" type="select" required
              value={form.property_code} onChange={handleChange}
              options={PROPERTIES}
            />
            <FormField
              label="Inquiry Source" name="source" type="select" required
              value={form.source} onChange={handleChange}
              options={SOURCES}
            />
            <div className="flex items-center gap-2 pt-6">
              <input
                id="first_time_dormer"
                name="first_time_dormer"
                type="checkbox"
                checked={form.first_time_dormer}
                onChange={handleChange}
                className="h-4 w-4 text-brand-navy border-gray-300 rounded focus:ring-brand-navy"
              />
              <label htmlFor="first_time_dormer" className="text-sm text-gray-700">
                First-time dormer?
              </label>
            </div>
            {!form.first_time_dormer && (
              <FormField
                label="Previous Dorm" name="previous_dorm"
                value={form.previous_dorm} onChange={handleChange}
                placeholder="Name of previous dorm"
              />
            )}
            <FormField
              label="Desired Move-in Date" name="desired_move_in_date" type="date"
              value={form.desired_move_in_date} onChange={handleChange}
            />
            <FormField
              label="Expected Length of Stay" name="length_of_stay" type="select"
              value={form.length_of_stay} onChange={handleChange}
              options={LENGTH_OPTIONS}
            />
          </div>
        </div>

        {/* Section: Notes */}
        <div>
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">Additional Notes</h3>
          <FormField
            label="Inquiry Details / Special Requests" name="content" type="textarea" rows={4}
            value={form.content} onChange={handleChange}
            placeholder="Any specific questions, room preferences, or notes..."
            className="md:col-span-2 lg:col-span-3"
          />
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-3 pt-2 border-t border-gray-100">
          <Button type="submit" loading={submitting}>
            <Send className="w-4 h-4 mr-1" /> Submit Inquiry
          </Button>
          <Button type="button" variant="secondary" onClick={handleReset}>
            <RotateCcw className="w-4 h-4 mr-1" /> Reset
          </Button>
        </div>
      </form>

      {/* Generate QR Modal */}
      <Modal isOpen={showQrModal} onClose={handleCloseModal} title="Generate QR Code">
        <div className="space-y-4">
          {!generatedQr ? (
            <>
              <FormField
                label="DormTel Branch"
                name="qrBranch"
                type="select"
                value={qrForm.branch}
                onChange={(e) => setQrForm((prev) => ({ ...prev, branch: e.target.value }))}
                options={PROPERTIES}
              />
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  label="Effectivity Start"
                  name="qrStartDate"
                  type="date"
                  value={qrForm.startDate}
                  onChange={(e) => setQrForm((prev) => ({ ...prev, startDate: e.target.value }))}
                />
                <FormField
                  label="Effectivity End"
                  name="qrEndDate"
                  type="date"
                  value={qrForm.endDate}
                  onChange={(e) => setQrForm((prev) => ({ ...prev, endDate: e.target.value }))}
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button variant="secondary" onClick={handleCloseModal}>
                  Cancel
                </Button>
                <Button
                  onClick={handleGenerateQr}
                  disabled={!qrForm.startDate || !qrForm.endDate}
                >
                  <QrCode className="w-4 h-4 mr-1" /> Generate
                </Button>
              </div>
            </>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-col items-center justify-center space-y-3">
                <img
                  src={generatedQr.url}
                  alt="Generated QR Code"
                  className="w-64 h-64 border border-gray-200 rounded-lg"
                />
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-900">{generatedQr.branchLabel}</p>
                  <p className="text-xs text-gray-500">
                    Valid: {qrForm.startDate} to {qrForm.endDate}
                  </p>
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button variant="secondary" onClick={() => setGeneratedQr(null)}>
                  Back
                </Button>
                <Button onClick={handleDownload}>
                  <Download className="w-4 h-4 mr-1" /> Download
                </Button>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}

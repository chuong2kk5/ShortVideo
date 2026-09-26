import React, { useState, useRef } from 'react';
import {
  X,
  ShoppingBag,
  Upload,
  Image as ImageIcon,
  Video,
  Trash2,
  Sparkles,
  Loader2,
  Film,
  CheckCircle,
  Tag,
  Shirt,
  Watch,
  Smartphone,
  Sparkle,
  ArrowRight,
} from 'lucide-react';
import { ProductMediaItem, ReferenceVideoAnalysis, DEFAULT_VOICE_CATALOG } from '../types';

interface ProductReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onReviewCreated: (projectId: string, jobId: string) => void;
}

const CATEGORY_OPTIONS = [
  { id: 'fashion', label: 'Thời Trang & Quần Áo', icon: Shirt },
  { id: 'accessories', label: 'Phụ Kiện, Giày & Túi', icon: Watch },
  { id: 'tech_gadget', label: 'Đồ Tiện Ích & Công Nghệ', icon: Smartphone },
  { id: 'beauty', label: 'Mỹ Phẩm & Skincare', icon: Sparkle },
  { id: 'general', label: 'Sản Phẩm Khác', icon: Tag },
];

const TEMPLATE_OPTIONS = [
  {
    id: 'fashion_ootd',
    title: 'Thời Trang OOTD',
    desc: 'Hook giá/form dáng ➔ Cận cảnh chất vải ➔ Lên form người mặc ➔ Deal hời giỏ hàng',
    badge: 'Hot TikTok',
  },
  {
    id: 'accessories_unboxing',
    title: 'Phụ Kiện & Đập Hộp',
    desc: 'Hook mở hộp sang xịn ➔ Cận cảnh chi tiết khuy/mạ ➔ Phối đồ outfit ➔ Săn voucher',
    badge: 'Chuyển Đổi Cao',
  },
  {
    id: 'gadget_practical',
    title: 'Đồ Tiện Ích Thông Minh',
    desc: 'Nỗi đau đời thường ➔ Trải nghiệm giải quyết vấn đề ➔ Test độ bền ➔ Chốt đơn',
    badge: 'Viral',
  },
  {
    id: 'beauty_review',
    title: 'Mỹ Phẩm & Chăm Sóc',
    desc: 'Tình trạng da ➔ Test texture chất kem mềm mịn ➔ Cảm nhận thực tế ➔ Deal sốc',
    badge: 'KOC Chuẩn',
  },
  {
    id: 'reference_match',
    title: 'Bắt Chước Video Mẫu',
    desc: 'Tải video mẫu lên để AI sao chép nhịp điệu cắt cảnh và phong cách kịch bản',
    badge: 'Tùy Biến',
  },
];

export const ProductReviewModal: React.FC<ProductReviewModalProps> = ({
  isOpen,
  onClose,
  onReviewCreated,
}) => {
  const [productName, setProductName] = useState('');
  const [category, setCategory] = useState('fashion');
  const [keyFeatures, setKeyFeatures] = useState('');
  const [dealInfo, setDealInfo] = useState('Đang flash sale giảm 50% + Freeship, bấm giỏ hàng góc trái săn ngay');
  const [targetAudience, setTargetAudience] = useState('Nam nữ trẻ trung, sinh viên, người đi làm');
  const [templateType, setTemplateType] = useState('fashion_ootd');
  const [voice, setVoice] = useState('vi-VN-HoaiMyNeural');
  const [duration, setDuration] = useState(30);

  // Uploaded media state
  const [mediaItems, setMediaItems] = useState<ProductMediaItem[]>([]);
  const [isUploadingMedia, setIsUploadingMedia] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Reference video state
  const [referenceVideo, setReferenceVideo] = useState<ReferenceVideoAnalysis | null>(null);
  const [isUploadingRefVideo, setIsUploadingRefVideo] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const refVideoInputRef = useRef<HTMLInputElement | null>(null);

  if (!isOpen) return null;

  // Handle uploading product images / clips
  const handleFilesSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setUploadError(null);
    setIsUploadingMedia(true);

    const formData = new FormData();
    for (let i = 0; i < e.target.files.length; i++) {
      formData.append('files', e.target.files[i]);
    }

    try {
      const res = await fetch('/api/upload/media', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Upload thất bại');
      }

      const uploaded: ProductMediaItem[] = await res.json();
      setMediaItems((prev) => [...prev, ...uploaded]);
    } catch (err: any) {
      setUploadError(err.message || 'Lỗi tải ảnh lên');
    } finally {
      setIsUploadingMedia(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Handle uploading reference sample video
  const handleReferenceVideoSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setIsUploadingRefVideo(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', e.target.files[0]);

    try {
      const res = await fetch('/api/upload/reference-video', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Không thể phân tích video mẫu');
      }

      const analysis: ReferenceVideoAnalysis = await res.json();
      setReferenceVideo(analysis);
      setTemplateType('reference_match');
      if (analysis.duration) {
        setDuration(Math.min(60, Math.max(15, Math.round(analysis.duration))));
      }
    } catch (err: any) {
      setUploadError(err.message || 'Lỗi tải video mẫu');
    } finally {
      setIsUploadingRefVideo(false);
      if (refVideoInputRef.current) refVideoInputRef.current.value = '';
    }
  };

  // Remove uploaded media item
  const handleRemoveMedia = (index: number) => {
    setMediaItems((prev) => prev.filter((_, i) => i !== index));
  };

  // Update caption
  const handleUpdateCaption = (index: number, caption: string) => {
    setMediaItems((prev) =>
      prev.map((item, i) => (i === index ? { ...item, caption } : item))
    );
  };

  // Submit and start review pipeline
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productName.trim()) {
      setUploadError('Vui lòng nhập tên sản phẩm.');
      return;
    }
    if (mediaItems.length === 0) {
      setUploadError('Vui lòng tải lên ít nhất 1 ảnh hoặc video sản phẩm thật.');
      return;
    }

    setUploadError(null);
    setIsSubmitting(true);

    try {
      const payload = {
        product_name: productName.trim(),
        category,
        key_features: keyFeatures.trim() || 'Chất lượng cao cấp, thiết kế đẹp, bền bỉ',
        deal_info: dealInfo.trim(),
        target_audience: targetAudience.trim(),
        template_type: templateType,
        reference_video_url: referenceVideo?.url,
        reference_video_path: referenceVideo?.local_path,
        media_items: mediaItems,
        voice,
        target_duration: duration,
        language: 'vi',
      };

      const res = await fetch('/api/pipeline/generate-product-review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Không thể tạo video review');
      }

      const result = await res.json();
      onReviewCreated(result.project_id, result.job_id);
      onClose();
    } catch (err: any) {
      setUploadError(err.message || 'Đã có lỗi xảy ra khi tạo video');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl shadow-rose-950/30 overflow-hidden my-auto animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-gradient-to-r from-slate-900 via-rose-950/20 to-amber-950/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-500 via-orange-500 to-amber-400 flex items-center justify-center shadow-lg shadow-rose-500/25">
              <ShoppingBag className="w-5 h-5 text-slate-950 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-tight">
                  Tạo Video Review Sản Phẩm (TikTok Shop & Affiliate)
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
                  Affiliate Pro
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Ghép ảnh/clip thật thành video review KOC chuyển đổi cao, khớp 100% từng phân cảnh
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {uploadError && (
            <div className="p-3 text-xs bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-xl flex items-center gap-2">
              <span className="font-bold">Lỗi:</span>
              <span>{uploadError}</span>
            </div>
          )}

          {/* Section 1: Thông tin sản phẩm */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-rose-400">
              <Sparkles className="w-4 h-4" />
              <span>1. Thông Tin Sản Phẩm & Điểm Nhấn Bán Hàng</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Tên sản phẩm cần review <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="Ví dụ: Áo Polo Nam Cotton Cổ Dệt, Đồng Hồ Nam Sapphire..."
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-rose-500 focus:ring-1 focus:ring-rose-500 transition-all placeholder:text-slate-600"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Ngành hàng sản phẩm
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {CATEGORY_OPTIONS.map((cat) => {
                    const Icon = cat.icon;
                    return (
                      <button
                        key={cat.id}
                        type="button"
                        onClick={() => setCategory(cat.id)}
                        className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium border text-left transition-all ${
                          category === cat.id
                            ? 'bg-rose-500/15 border-rose-500 text-rose-300 shadow-sm'
                            : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:border-slate-700'
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5 shrink-0" />
                        <span className="truncate">{cat.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Đặc điểm nổi bật / Chất liệu / Tính năng
                </label>
                <textarea
                  value={keyFeatures}
                  onChange={(e) => setKeyFeatures(e.target.value)}
                  placeholder="Ví dụ: Vải cotton dệt cá sấu dày dặn, co giãn 4 chiều, không xù lông, form ôm nhẹ tôn dáng..."
                  rows={2}
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-rose-500 focus:ring-1 focus:ring-rose-500 transition-all placeholder:text-slate-600"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Giá bán / Deal flash sale (Kêu gọi giỏ hàng góc trái)
                </label>
                <textarea
                  value={dealInfo}
                  onChange={(e) => setDealInfo(e.target.value)}
                  placeholder="Ví dụ: Đang sale sốc chỉ còn 99k tặng kèm voucher freeship, bấm giỏ hàng góc trái săn ngay!"
                  rows={2}
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-rose-500 focus:ring-1 focus:ring-rose-500 transition-all placeholder:text-slate-600"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Upload ảnh sản phẩm thật */}
          <div className="space-y-4 pt-2 border-t border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
                <Upload className="w-4 h-4" />
                <span>2. Tải Lên Ảnh / Clip Mẫu Sản Phẩm Thật ({mediaItems.length} ảnh đã chọn)</span>
              </div>
              <span className="text-[11px] text-slate-400">
                (Nên tải từ 3 - 6 ảnh: toàn thân, cận chất vải, chi tiết, bảng màu)
              </span>
            </div>

            {/* Dropzone */}
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-700 hover:border-amber-500/70 bg-slate-950/60 hover:bg-slate-950 rounded-2xl p-6 text-center cursor-pointer transition-all group"
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*,video/*"
                onChange={handleFilesSelected}
                className="hidden"
              />
              <div className="flex flex-col items-center gap-2">
                <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                  {isUploadingMedia ? (
                    <Loader2 className="w-6 h-6 animate-spin" />
                  ) : (
                    <Upload className="w-6 h-6" />
                  )}
                </div>
                <div className="text-xs font-medium text-slate-300">
                  <span className="text-amber-400 font-semibold underline underline-offset-2">
                    Bấm để tải ảnh/video
                  </span>{' '}
                  hoặc kéo thả vào đây
                </div>
                <p className="text-[11px] text-slate-500">
                  Hỗ trợ JPG, PNG, WEBP, MP4 (tải nhiều file cùng lúc)
                </p>
              </div>
            </div>

            {/* Uploaded Items Grid */}
            {mediaItems.length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 pt-2">
                {mediaItems.map((item, idx) => (
                  <div
                    key={idx}
                    className="relative group bg-slate-950 border border-slate-800 hover:border-amber-500/50 rounded-xl overflow-hidden p-2 flex flex-col gap-2 transition-all shadow-md"
                  >
                    <div className="relative aspect-[9/16] bg-slate-900 rounded-lg overflow-hidden flex items-center justify-center">
                      {item.media_type === 'video' ? (
                        <video
                          src={item.url}
                          className="w-full h-full object-cover"
                          muted
                          playsInline
                        />
                      ) : (
                        <img
                          src={item.url}
                          alt={`Product media ${idx + 1}`}
                          className="w-full h-full object-cover"
                        />
                      )}

                      {/* Scene Badge */}
                      <div className="absolute top-1.5 left-1.5 px-2 py-0.5 bg-black/70 backdrop-blur-md rounded-md text-[10px] font-bold text-amber-300 border border-amber-500/30">
                        Cảnh #{idx + 1}
                      </div>

                      {/* Delete Button */}
                      <button
                        type="button"
                        onClick={() => handleRemoveMedia(idx)}
                        className="absolute top-1.5 right-1.5 p-1 bg-rose-600/80 hover:bg-rose-600 text-white rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Xóa ảnh này"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <input
                      type="text"
                      value={item.caption || ''}
                      onChange={(e) => handleUpdateCaption(idx, e.target.value)}
                      placeholder={
                        idx === 0
                          ? 'Tổng quan / Hook'
                          : idx === 1
                          ? 'Cận cảnh chất vải'
                          : idx === 2
                          ? 'Lên dáng người mặc'
                          : 'Bảng màu / Chi tiết'
                      }
                      className="bg-slate-900 border border-slate-800 rounded-lg px-2 py-1 text-[11px] text-slate-300 focus:outline-none focus:border-amber-500"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 3: Cấu trúc & Video Mẫu */}
          <div className="space-y-4 pt-2 border-t border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-rose-400">
                <Film className="w-4 h-4" />
                <span>3. Chọn Mẫu Video Cấu Trúc (Template / Reference)</span>
              </div>
            </div>

            {/* Template options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {TEMPLATE_OPTIONS.map((tmpl) => (
                <div
                  key={tmpl.id}
                  onClick={() => setTemplateType(tmpl.id)}
                  className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all ${
                    templateType === tmpl.id
                      ? 'bg-rose-500/10 border-rose-500/80 shadow-md shadow-rose-950/40'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-white flex items-center gap-1.5">
                      {tmpl.title}
                    </span>
                    <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      {tmpl.badge}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{tmpl.desc}</p>
                </div>
              ))}
            </div>

            {/* Reference Video Upload Box */}
            {templateType === 'reference_match' && (
              <div className="bg-slate-950/80 border border-rose-500/40 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold text-rose-300">
                    <Video className="w-4 h-4 text-rose-400" />
                    <span>Tải Video Mẫu Tham Khảo (.mp4 từ TikTok / Reels)</span>
                  </div>
                  {referenceVideo && (
                    <span className="flex items-center gap-1 text-[11px] text-emerald-400">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Đã phân tích nhịp điệu
                    </span>
                  )}
                </div>

                <div
                  onClick={() => refVideoInputRef.current?.click()}
                  className="border border-dashed border-rose-500/30 hover:border-rose-400 bg-rose-950/10 rounded-xl p-4 text-center cursor-pointer transition-colors"
                >
                  <input
                    ref={refVideoInputRef}
                    type="file"
                    accept="video/*"
                    onChange={handleReferenceVideoSelected}
                    className="hidden"
                  />
                  {isUploadingRefVideo ? (
                    <div className="flex items-center justify-center gap-2 text-xs text-rose-300">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Đang đọc thời lượng và phân tích tốc độ chuyển cảnh...
                    </div>
                  ) : referenceVideo ? (
                    <div className="text-xs text-slate-300 flex items-center justify-center gap-3">
                      <span className="font-semibold text-rose-400">{referenceVideo.filename}</span>
                      <span>•</span>
                      <span>Thời lượng: {referenceVideo.duration}s</span>
                      <span>•</span>
                      <span>Nhịp chuyển: ~{referenceVideo.avg_scene_duration}s/cảnh</span>
                    </div>
                  ) : (
                    <div className="text-xs text-slate-400">
                      Bấm để chọn file video mẫu (.mp4) để AI tự động trích xuất cấu trúc và nhịp điệu
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Voice & Duration settings */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Giọng đọc review KOC
                </label>
                <select
                  value={voice}
                  onChange={(e) => setVoice(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500"
                >
                  {DEFAULT_VOICE_CATALOG.filter((v) => v.locale.startsWith('vi')).map((v) => (
                    <option key={v.id} value={v.base_voice}>
                      {v.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Thời lượng dự kiến ({duration} giây)
                </label>
                <div className="flex items-center gap-2 pt-1">
                  {[20, 30, 45, 60].map((sec) => (
                    <button
                      key={sec}
                      type="button"
                      onClick={() => setDuration(sec)}
                      className={`flex-1 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                        duration === sec
                          ? 'bg-rose-500/20 border-rose-500 text-rose-300'
                          : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      {sec}s
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
            >
              Hủy
            </button>

            <button
              type="submit"
              disabled={isSubmitting || mediaItems.length === 0}
              className="flex items-center gap-2 bg-gradient-to-r from-rose-500 via-orange-500 to-amber-500 hover:from-rose-600 hover:to-amber-600 text-slate-950 font-bold px-6 py-2.5 rounded-xl text-xs transition-all shadow-lg shadow-rose-500/30 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Đang Khởi Tạo Video Review...</span>
                </>
              ) : (
                <>
                  <span>🚀 Bắt Đầu Tạo Video Review</span>
                  <ArrowRight className="w-4 h-4 stroke-[2.5]" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

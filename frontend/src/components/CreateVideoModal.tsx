import React, { useState, useEffect } from 'react';
import { X, Sparkles, Mic, Clock, Globe, Wand2, Loader2, Volume2, Square, Radio, Palette, BookOpen } from 'lucide-react';
import { BrandKit, VoiceProfile, DEFAULT_VOICE_CATALOG } from '../types';
import { useAudioPreview } from '../hooks/useAudioPreview';

interface CreateVideoModalProps {
  isOpen: boolean;
  onClose: () => void;
  brandKits: BrandKit[];
  onStartGeneration: (data: {
    topic: string;
    language: string;
    duration: number;
    voice: string;
    brandKitId?: string;
    artStyle?: string;
    contentStyle?: string;
  }) => Promise<void>;
}

export const CreateVideoModal: React.FC<CreateVideoModalProps> = ({
  isOpen,
  onClose,
  brandKits,
  onStartGeneration,
}) => {
  const [topic, setTopic] = useState('');
  const [language, setLanguage] = useState('vi');
  const [duration, setDuration] = useState(30);
  const [voice, setVoice] = useState('vi-VN-NamMinhNeural');
  const [artStyle, setArtStyle] = useState('auto');
  const [contentStyle, setContentStyle] = useState('auto');
  const [brandKitId, setBrandKitId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [voices, setVoices] = useState<VoiceProfile[]>(DEFAULT_VOICE_CATALOG);

  const { playingVoiceId, isLoading: isAudioLoading, play: playAudio, stop: stopAudio } = useAudioPreview();

  // Fetch voice list for selected language with fallback
  useEffect(() => {
    let isMounted = true;
    const fetchVoices = async () => {
      try {
        const res = await fetch(`/api/tts/voices?language=${language}`);
        if (res.ok) {
          const data = await res.json();
          if (isMounted && data.voices && data.voices.length > 0) {
            setVoices(data.voices);
            return;
          }
        }
      } catch (err) {
        console.warn('Failed to load online voice catalog, using built-in presets:', err);
      }
      if (isMounted) {
        setVoices(DEFAULT_VOICE_CATALOG.filter((v) => v.locale.startsWith(language)));
      }
    };
    fetchVoices();
    return () => {
      isMounted = false;
    };
  }, [language]);

  // Stop audio on unmount or modal close
  const handleClose = () => {
    stopAudio();
    onClose();
  };

  if (!isOpen) return null;

  const currentVoiceObj = voices.find((v) => v.id === voice) || voices[0];

  const handleTogglePreview = () => {
    playAudio(voice);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    stopAudio();
    setIsSubmitting(true);
    try {
      await onStartGeneration({
        topic: topic.trim(),
        language,
        duration,
        voice,
        brandKitId: brandKitId || undefined,
        artStyle,
        contentStyle,
      });
      handleClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };


  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-xl rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
              <Wand2 className="w-4 h-4" />
            </div>
            <div>
              <h2 className="font-bold text-slate-100 text-sm">Tạo Video Shorts Tự Động</h2>
              <p className="text-xs text-slate-400">Từ ý tưởng kịch bản đến video MP4 hoàn chỉnh kèm phụ đề</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Topic Input */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Chủ Đề Hoặc Ý Tưởng Video (Topic / Keyword) *
            </label>
            <textarea
              required
              rows={3}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="VD: 3 sự thật rùng mình về đáy đại dương mà khoa học chưa giải thích được..."
              className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none transition-all resize-none"
            />
          </div>

          {/* Duration & Language */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-emerald-400" />
                Thời Lượng Dự Kiến
              </label>
              <select
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 outline-none focus:border-emerald-500"
              >
                <option value={15}>15 giây (Siêu ngắn - Viral cao)</option>
                <option value={30}>30 giây (Chuẩn Shorts & TikTok)</option>
                <option value={45}>45 giây (Chi tiết & Giữ chân)</option>
                <option value={60}>60 giây (Kể chuyện đầy đủ)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5 text-cyan-400" />
                Ngôn Ngữ Kịch Bản
              </label>
              <select
                value={language}
                onChange={(e) => {
                  stopAudio();
                  const newLang = e.target.value;
                  setLanguage(newLang);
                  if (newLang === 'en') {
                    setVoice('en-US-ChristopherNeural');
                  } else {
                    setVoice('vi-VN-NamMinhNeural');
                  }
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 outline-none focus:border-emerald-500"
              >
                <option value="vi">Tiếng Việt (Tự nhiên, lôi cuốn)</option>
                <option value="en">English (Global Viral Reach)</option>
              </select>
            </div>
          </div>

          {/* Content Style & Art Style Presets */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-amber-400" />
                Mô Thức Kịch Bản
              </label>
              <select
                value={contentStyle}
                onChange={(e) => setContentStyle(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 outline-none focus:border-emerald-500"
              >
                <option value="auto">🤖 Tự động phân tích (Khuyên dùng)</option>
                <option value="storytelling_drama">🎭 Kể chuyện & Kịch tính (Drama)</option>
                <option value="top_facts">📊 Top Fact / Bảng xếp hạng</option>
                <option value="mystery_curiosity">🕵️ Bí ẩn & Kích thích tò mò</option>
                <option value="educational">💡 Giải thích & Kiến thức hữu ích</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Palette className="w-3.5 h-3.5 text-pink-400" />
                Phong Cách Hình Ảnh (Visual)
              </label>
              <select
                value={artStyle}
                onChange={(e) => setArtStyle(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 outline-none focus:border-emerald-500"
              >
                <option value="auto">✨ AI Đồng bộ theo kịch bản</option>
                <option value="cinematic">🎬 Điện ảnh chân thực (Cinematic)</option>
                <option value="3d_animation">🧸 Hoạt hình 3D Pixar sắc nét</option>
                <option value="anime_ghibli">🎨 Anime Ghibli / Manga sống động</option>
                <option value="dark_mystery">🌑 Rùng rợn & Bí ẩn (Dark Noir)</option>
                <option value="historic_painting">🏛️ Tranh sơn dầu phục hưng cổ điển</option>
              </select>
            </div>
          </div>

          {/* Voice Selection & Listen Preview Button */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Mic className="w-3.5 h-3.5 text-emerald-400" />
                <span>Giọng Đọc Thuyết Minh (Studio AI Miễn Phí)</span>
              </label>
              {currentVoiceObj?.recommended && (
                <span className="text-[10px] font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
                  ⭐ Khuyên dùng cho Shorts
                </span>
              )}
            </div>

            <div className="flex gap-2">
              <select
                value={voice}
                onChange={(e) => {
                  stopAudio();
                  setVoice(e.target.value);
                }}
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 outline-none focus:border-emerald-500"
              >
                {voices.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>

              {/* Nghe Thử Button */}
              <button
                type="button"
                onClick={handleTogglePreview}
                className={`px-3.5 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap shadow-sm ${
                  playingVoiceId === voice
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 hover:bg-rose-500/30'
                    : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/25'
                }`}
                title="Nghe thử giọng đọc trực tiếp trên trình duyệt"
              >
                {playingVoiceId === voice ? (
                  isAudioLoading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-400" />
                      <span>Đang tải...</span>
                    </>
                  ) : (
                    <>
                      <Square className="w-3.5 h-3.5 fill-rose-400 text-rose-400 animate-pulse" />
                      <span>Dừng nghe</span>
                    </>
                  )
                ) : (
                  <>
                    <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Nghe thử</span>
                  </>
                )}
              </button>
            </div>

            {/* Voice Info Preview Card */}
            {currentVoiceObj && (
              <div className="mt-2 p-2.5 bg-slate-950/70 border border-slate-800/80 rounded-xl text-[11px] space-y-1.5">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="font-semibold text-slate-300">
                    {currentVoiceObj.gender === 'Male' ? '👨 Giọng Nam' : '👩 Giọng Nữ'}
                  </span>
                  <span className="text-slate-600">•</span>
                  <span className="text-emerald-400 font-mono font-medium">Tốc độ: {currentVoiceObj.rate}</span>
                  {currentVoiceObj.pitch && currentVoiceObj.pitch !== '+0Hz' && (
                    <>
                      <span className="text-slate-600">•</span>
                      <span className="text-cyan-400 font-mono font-medium">Cao độ: {currentVoiceObj.pitch}</span>
                    </>
                  )}
                  {currentVoiceObj.tags?.map((t, idx) => (
                    <span
                      key={idx}
                      className="bg-slate-800/90 text-slate-300 px-1.5 py-0.5 rounded text-[10px]"
                    >
                      {t}
                    </span>
                  ))}
                </div>
                <div className="text-slate-400 italic">
                  &ldquo;{currentVoiceObj.sample_text}&rdquo;
                </div>
              </div>
            )}
          </div>

          {/* Brand Kit Preset (Optional) */}
          {brandKits.length > 0 && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Áp Dụng Brand Kit Kênh (Tùy chọn)
              </label>
              <select
                value={brandKitId}
                onChange={(e) => setBrandKitId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 outline-none focus:border-emerald-500"
              >
                <option value="">-- Mặc định hệ thống --</option>
                {brandKits.map((k) => (
                  <option key={k.id} value={k.id}>
                    {k.name} ({k.default_tts_voice})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Visual Engine Pipeline Info */}
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
            <span className="flex items-center gap-1.5 text-slate-300 font-medium">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              Động cơ hình ảnh & video:
            </span>
            <span className="text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              Multi-Tier (Imagen 3 / Real Photos 4K + Ken Burns 60fps)
            </span>
          </div>

          {/* Footer Buttons */}
          <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-xl transition-colors"
            >
              Hủy bỏ
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !topic.trim()}
              className="flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-slate-950 font-bold px-5 py-2.5 rounded-xl text-xs transition-all shadow-lg shadow-emerald-500/25 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Đang khởi tạo...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 fill-slate-950 stroke-none" />
                  <span>Bắt Đầu Tạo Video Tự Động</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};


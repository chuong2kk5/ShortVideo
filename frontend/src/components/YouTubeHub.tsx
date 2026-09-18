import React, { useState } from 'react';
import {
  Youtube,
  Plus,
  UploadCloud,
  BarChart3,
  Clock,
  CheckCircle,
  ExternalLink,
  Calendar,
  Palette,
  Trash2,
  Volume2,
  Square,
  Loader2,
} from 'lucide-react';
import { YouTubeChannel, BrandKit, Project, DEFAULT_VOICE_CATALOG } from '../types';
import { useAudioPreview } from '../hooks/useAudioPreview';

interface YouTubeHubProps {
  channels: YouTubeChannel[];
  brandKits: BrandKit[];
  completedProjects: Project[];
  onRefreshChannels: () => void;
  onRefreshBrandKits: () => void;
}

export const YouTubeHub: React.FC<YouTubeHubProps> = ({
  channels,
  brandKits,
  completedProjects,
  onRefreshChannels,
  onRefreshBrandKits,
}) => {
  const [selectedChannelId, setSelectedChannelId] = useState<string>('');
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [privacyStatus, setPrivacyStatus] = useState<'public' | 'unlisted' | 'private'>('public');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccessMsg, setUploadSuccessMsg] = useState<string | null>(null);

  // Audio Preview hook
  const { playingVoiceId, isLoading: isAudioLoading, play: playAudio, stop: stopAudio } = useAudioPreview();

  // New Brand Kit Modal state
  const [isCreatingKit, setIsCreatingKit] = useState(false);
  const [newKitName, setNewKitName] = useState('');
  const [newKitVoice, setNewKitVoice] = useState('vi-VN-NamMinhNeural');
  const [newKitSubColor, setNewKitSubColor] = useState('#FFFF00');


  const handleConnectYouTube = async () => {
    try {
      const res = await fetch('/api/youtube/auth-url');
      const data = await res.json();
      if (data.auth_url) {
        window.open(data.auth_url, '_blank');
      }
    } catch (err) {
      alert('Chưa cấu hình client_secrets.json cho Google OAuth2');
    }
  };

  const handleUploadVideo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedChannelId || !selectedProjectId) return;

    setIsUploading(true);
    setUploadSuccessMsg(null);
    try {
      const res = await fetch(
        `/api/youtube/channels/${selectedChannelId}/upload?project_id=${selectedProjectId}&privacy_status=${privacyStatus}`,
        { method: 'POST' }
      );
      const data = await res.json();
      if (res.ok) {
        setUploadSuccessMsg(`Upload thành công: ${data.upload.shorts_url}`);
      } else {
        alert(data.detail || 'Lỗi khi upload video');
      }
    } catch (err: any) {
      alert(err.message || 'Lỗi kết nối upload');
    } finally {
      setIsUploading(false);
    }
  };

  const handleCreateBrandKit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKitName.trim()) return;

    try {
      await fetch('/api/youtube/brand-kits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newKitName.trim(),
          default_tts_voice: newKitVoice,
          subtitle_color: newKitSubColor,
          subtitle_font: 'Montserrat-ExtraBold',
        }),
      });
      setIsCreatingKit(false);
      setNewKitName('');
      onRefreshBrandKits();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
            <Youtube className="w-4 h-4 text-rose-500 fill-rose-500" />
            <span>YOUTUBE MULTI-CHANNEL HUB</span>
          </span>
          <h1 className="text-xl font-extrabold text-white mt-1">Quản Lý Kênh & Auto Publisher</h1>
          <p className="text-xs text-slate-400 mt-1">
            Kết nối nhiều kênh YouTube, lưu Brand Kit nhận diện và tự động đăng video kèm Title, Hashtags chuẩn SEO
          </p>
        </div>

        <button
          onClick={handleConnectYouTube}
          className="flex items-center gap-2 bg-rose-600 hover:bg-rose-700 text-white font-bold px-4 py-2.5 rounded-xl text-xs transition-all shadow-lg shadow-rose-600/20 active:scale-95"
        >
          <Plus className="w-4 h-4 stroke-[3]" />
          <span>Kết Nối Kênh YouTube Mới</span>
        </button>
      </div>

      {/* Connected Channels Grid */}
      <div>
        <h2 className="text-sm font-extrabold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Youtube className="w-4 h-4 text-rose-500" />
          <span>Kênh Đã Kết Nối ({channels.length})</span>
        </h2>

        {channels.length === 0 ? (
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center">
            <Youtube className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-xs text-slate-400">
              Chưa có kênh YouTube nào được kết nối. Nhấn nút <strong>[Kết Nối Kênh YouTube Mới]</strong> bên trên để liên kết tài khoản.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {channels.map((ch) => (
              <div key={ch.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-md space-y-3">
                <div className="flex items-center gap-3">
                  {ch.thumbnail_url ? (
                    <img src={ch.thumbnail_url} alt={ch.title} className="w-12 h-12 rounded-xl object-cover" />
                  ) : (
                    <div className="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center font-extrabold text-base">
                      YT
                    </div>
                  )}
                  <div>
                    <h3 className="font-bold text-sm text-slate-100 line-clamp-1">{ch.title}</h3>
                    <span className="text-[11px] text-slate-400 font-mono">{ch.custom_url || ch.channel_id}</span>
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-center">
                  <div className="bg-slate-950 p-2 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block">Subscribers</span>
                    <span className="font-extrabold text-xs text-emerald-400">{ch.subscriber_count.toLocaleString()}</span>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block">Total Views</span>
                    <span className="font-extrabold text-xs text-cyan-400">{ch.view_count.toLocaleString()}</span>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block">Videos</span>
                    <span className="font-extrabold text-xs text-slate-200">{ch.video_count}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Auto Publisher & Upload Box */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h2 className="text-sm font-extrabold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
          <UploadCloud className="w-4 h-4 text-emerald-400" />
          <span>Xuất Bản Video Lên YouTube Shorts</span>
        </h2>

        <form onSubmit={handleUploadVideo} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Select Channel */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5">Chọn Kênh YouTube</label>
            <select
              value={selectedChannelId}
              onChange={(e) => setSelectedChannelId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 outline-none focus:border-rose-500"
            >
              <option value="">-- Chọn kênh đăng tải --</option>
              {channels.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </select>
          </div>

          {/* Select Project */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5">Chọn Video MP4 Hoàn Chỉnh</label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 outline-none focus:border-emerald-500"
            >
              <option value="">-- Chọn video dự án --</option>
              {completedProjects
                .filter((p) => !!p.final_video_path)
                .map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title} ({p.target_duration}s)
                  </option>
                ))}
            </select>
          </div>

          {/* Privacy Status & Submit */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5">Chế Độ Hiển Thị</label>
            <div className="flex gap-2">
              <select
                value={privacyStatus}
                onChange={(e) => setPrivacyStatus(e.target.value as any)}
                className="w-1/2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 outline-none focus:border-emerald-500"
              >
                <option value="public">Công khai (Public)</option>
                <option value="private">Riêng tư (Private)</option>
                <option value="unlisted">Không công khai (Unlisted)</option>
              </select>

              <button
                type="submit"
                disabled={isUploading || !selectedChannelId || !selectedProjectId}
                className="w-1/2 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold px-3 py-2 rounded-xl text-xs transition-all flex items-center justify-center gap-1.5 shadow-lg shadow-emerald-500/20"
              >
                <UploadCloud className="w-4 h-4" />
                <span>{isUploading ? 'Đang tải...' : 'Đăng Ngay'}</span>
              </button>
            </div>
          </div>
        </form>

        {uploadSuccessMsg && (
          <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-400 font-semibold flex items-center gap-2">
            <CheckCircle className="w-4 h-4 flex-shrink-0" />
            <span>{uploadSuccessMsg}</span>
          </div>
        )}
      </div>

      {/* Brand Kit Presets */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Palette className="w-4 h-4 text-cyan-400" />
            <span>Brand Kit Presets Cho Từng Kênh ({brandKits.length})</span>
          </h2>
          <button
            onClick={() => setIsCreatingKit(true)}
            className="flex items-center gap-1 text-xs font-bold text-cyan-400 hover:text-cyan-300"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Tạo Brand Kit Mới</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {brandKits.map((kit) => (
            <div key={kit.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-xs text-slate-100">{kit.name}</h4>
                <div
                  className="w-4 h-4 rounded-full border border-slate-700"
                  style={{ backgroundColor: kit.subtitle_color }}
                  title={`Subtitle Color: ${kit.subtitle_color}`}
                />
              </div>
              <div className="text-[11px] text-slate-400 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="truncate pr-1">
                    Giọng đọc: <span className="text-slate-200 font-semibold">{kit.default_tts_voice}</span>
                  </span>
                  <button
                    type="button"
                    onClick={() => playAudio(kit.default_tts_voice)}
                    className={`p-1 rounded transition-colors shrink-0 ${
                      playingVoiceId === kit.default_tts_voice
                        ? 'text-rose-400 bg-rose-500/10'
                        : 'text-slate-400 hover:text-emerald-400 hover:bg-slate-800'
                    }`}
                    title="Nghe thử giọng đọc của Brand Kit này"
                  >
                    {playingVoiceId === kit.default_tts_voice ? (
                      isAudioLoading ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
                      ) : (
                        <Square className="w-3.5 h-3.5 fill-rose-400 text-rose-400 animate-pulse" />
                      )
                    ) : (
                      <Volume2 className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
                <div>Font phụ đề: <span className="text-slate-200 font-semibold">{kit.subtitle_font}</span></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* New Brand Kit Modal */}
      {isCreatingKit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md space-y-4">
            <h3 className="font-bold text-sm text-slate-100">Tạo Brand Kit Kênh Mới</h3>
            <form onSubmit={handleCreateBrandKit} className="space-y-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Tên Preset</label>
                <input
                  type="text"
                  required
                  value={newKitName}
                  onChange={(e) => setNewKitName(e.target.value)}
                  placeholder="VD: Kênh Kể Chuyện Tâm Linh"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 outline-none focus:border-cyan-500"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Giọng đọc mặc định</label>
                <div className="flex gap-2">
                  <select
                    value={newKitVoice}
                    onChange={(e) => {
                      stopAudio();
                      setNewKitVoice(e.target.value);
                    }}
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                  >
                    <optgroup label="Tiếng Việt">
                      {DEFAULT_VOICE_CATALOG.filter((v) => v.locale.startsWith('vi')).map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.name}
                        </option>
                      ))}
                    </optgroup>
                    <optgroup label="English">
                      {DEFAULT_VOICE_CATALOG.filter((v) => v.locale.startsWith('en')).map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.name}
                        </option>
                      ))}
                    </optgroup>
                  </select>

                  <button
                    type="button"
                    onClick={() => playAudio(newKitVoice)}
                    className={`px-3 py-2 rounded-xl text-xs font-semibold flex items-center gap-1 transition-all whitespace-nowrap ${
                      playingVoiceId === newKitVoice
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500/25'
                    }`}
                    title="Nghe thử giọng đọc"
                  >
                    {playingVoiceId === newKitVoice ? (
                      isAudioLoading ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Square className="w-3.5 h-3.5 fill-rose-400 text-rose-400 animate-pulse" />
                      )
                    ) : (
                      <Volume2 className="w-3.5 h-3.5" />
                    )}
                    <span>Nghe</span>
                  </button>
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    stopAudio();
                    setIsCreatingKit(false);
                  }}
                  className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold px-4 py-1.5 rounded-xl text-xs"
                >
                  Tạo Preset
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};


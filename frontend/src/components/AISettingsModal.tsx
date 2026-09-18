import React, { useState, useEffect } from 'react';
import {
  X,
  Sparkles,
  Cpu,
  Key,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  ExternalLink,
  Save,
  Check,
  Mic,
  Volume2,
  Square,
  Globe,
  RotateCcw,
} from 'lucide-react';
import { AIStatus, VoiceProfile, DEFAULT_VOICE_CATALOG } from '../types';
import { useAudioPreview } from '../hooks/useAudioPreview';

interface AISettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfigSaved?: () => void;
}

export const AISettingsModal: React.FC<AISettingsModalProps> = ({
  isOpen,
  onClose,
  onConfigSaved,
}) => {
  const [activeTab, setActiveTab] = useState<'llm' | 'tts'>('llm');
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [geminiKey, setGeminiKey] = useState('');
  const [llmProvider, setLlmProvider] = useState('ollama');
  const [ollamaModel, setOllamaModel] = useState('qwen2.5:1.5b');
  const [isLoading, setIsLoading] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // TTS Voice Lab State
  const [voiceFilter, setVoiceFilter] = useState<'all' | 'vi' | 'en'>('vi');
  const [customSampleText, setCustomSampleText] = useState('');
  const [voiceCatalog, setVoiceCatalog] = useState<VoiceProfile[]>(DEFAULT_VOICE_CATALOG);

  const { playingVoiceId, isLoading: isAudioLoading, play: playAudio, stop: stopAudio } = useAudioPreview();

  // Fetch AI status & Voice catalog
  const fetchStatus = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/system/ai-status');
      if (res.ok) {
        const data: AIStatus = await res.json();
        setAiStatus(data);
        setLlmProvider(data.llm_provider || 'ollama');
        if (data.ollama.active_model) {
          setOllamaModel(data.ollama.active_model);
        } else if (data.ollama.models.length > 0) {
          setOllamaModel(data.ollama.models[0]);
        }
      }
    } catch (err) {
      console.error('Failed to load AI status', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchVoices = async () => {
    try {
      const res = await fetch('/api/tts/voices?language=all');
      if (res.ok) {
        const data = await res.json();
        if (data.voices && data.voices.length > 0) {
          setVoiceCatalog(data.voices);
        }
      }
    } catch (err) {
      console.warn('Using default voice catalog:', err);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchStatus();
      fetchVoices();
      setTestResult(null);
      setSaveSuccess(false);
    }
  }, [isOpen]);

  const handleClose = () => {
    stopAudio();
    onClose();
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setSaveSuccess(false);
    try {
      const body: any = {
        llm_provider: llmProvider,
        ollama_model: ollamaModel,
      };
      if (geminiKey.trim()) {
        body.gemini_api_key = geminiKey.trim();
      }

      const res = await fetch('/api/system/save-ai-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        setSaveSuccess(true);
        setGeminiKey('');
        await fetchStatus();
        if (onConfigSaved) onConfigSaved();
      }
    } catch (err) {
      console.error('Failed to save AI config', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestGemini = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await fetch('/api/system/test-gemini', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          gemini_api_key: geminiKey.trim() || undefined,
        }),
      });
      const data = await res.json();
      if (res.ok && data.valid) {
        setTestResult({ success: true, message: data.message });
      } else {
        setTestResult({
          success: false,
          message: data.message || data.detail || 'Kiểm tra thất bại. Vui lòng kiểm tra lại API Key.',
        });
      }
    } catch (err) {
      setTestResult({
        success: false,
        message: 'Lỗi kết nối khi kiểm tra Gemini API.',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const filteredVoices = voiceCatalog.filter((v) => {
    if (voiceFilter === 'all') return true;
    return v.locale.toLowerCase().startsWith(voiceFilter);
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-3xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
              {activeTab === 'llm' ? <Sparkles className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </div>
            <div>
              <h2 className="font-bold text-slate-100 text-sm">
                {activeTab === 'llm' ? 'Cấu Hình Trí Tuệ Nhân Tạo (AI Engines)' : 'Thư Viện Giọng Đọc AI & Nghe Thử Trực Tiếp'}
              </h2>
              <p className="text-xs text-slate-400">
                {activeTab === 'llm'
                  ? 'Thiết lập động cơ LLM kịch bản (Ollama / Gemini Flash) & bộ sinh hình ảnh'
                  : 'Trải nghiệm 13 giọng đọc Studio miễn phí với cao độ và tốc độ tối ưu Shorts'}
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-800 bg-slate-950/40 px-6 pt-2 gap-4 shrink-0">
          <button
            type="button"
            onClick={() => setActiveTab('llm')}
            className={`pb-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === 'llm'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Mô Hình LLM & API Keys</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('tts')}
            className={`pb-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === 'tts'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Mic className="w-3.5 h-3.5" />
            <span>Thư Viện Giọng Đọc & Nghe Thử ({voiceCatalog.length})</span>
          </button>
        </div>

        {/* Content Body */}
        {activeTab === 'llm' ? (
          <form onSubmit={handleSave} className="p-6 space-y-6 overflow-y-auto">
            {/* Status Row */}
            <div className="grid grid-cols-2 gap-4">
              {/* Ollama Status */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
                    <Cpu className="w-4 h-4 text-cyan-400" />
                    <span>Ollama Local (Offline)</span>
                  </div>
                  {aiStatus?.ollama.online ? (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                      <CheckCircle2 className="w-3 h-3" /> Online
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
                      <AlertTriangle className="w-3 h-3" /> Offline
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mb-2">
                  Model hiện tại:{' '}
                  <span className="font-mono text-cyan-300 font-semibold">
                    {aiStatus?.ollama.active_model || 'Chưa nhận diện'}
                  </span>
                </p>
                {aiStatus?.ollama.models && aiStatus.ollama.models.length > 0 && (
                  <div className="text-[10px] text-slate-400">
                    Models đã tải: {aiStatus.ollama.models.join(', ')}
                  </div>
                )}
              </div>

              {/* Gemini Status */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
                    <Key className="w-4 h-4 text-amber-400" />
                    <span>Google Gemini & Imagen 3</span>
                  </div>
                  {aiStatus?.gemini.configured ? (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                      <CheckCircle2 className="w-3 h-3" /> Đã Gắn Key
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                      Chưa Nhập Key
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mb-1">
                  Key hiện tại:{' '}
                  <span className="font-mono text-slate-300">
                    {aiStatus?.gemini.masked_key || 'Chưa lưu trong .env'}
                  </span>
                </p>
                <a
                  href="https://aistudio.google.com/app/apikey"
                  target="_blank"
                  rel="noreferrer"
                  className="text-[10px] text-emerald-400 hover:underline flex items-center gap-1"
                >
                  <span>Lấy Gemini API Key miễn phí tại Google AI Studio</span>
                  <ExternalLink className="w-2.5 h-2.5" />
                </a>
              </div>
            </div>

            {/* Gemini Key Input */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                <span>Dán Google Gemini API Key Mới</span>
                {aiStatus?.gemini.configured && (
                  <span className="text-[10px] text-slate-400 font-normal">
                    (Để trống nếu muốn giữ nguyên key cũ)
                  </span>
                )}
              </label>
              <div className="flex gap-2">
                <input
                  type="password"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder={aiStatus?.gemini.configured ? 'Nhập key mới để thay thế...' : 'AIzaSy...'}
                  className="flex-1 bg-slate-950 border border-slate-800 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 outline-none font-mono"
                />
                <button
                  type="button"
                  onClick={handleTestGemini}
                  disabled={isTesting || (!geminiKey.trim() && !aiStatus?.gemini.configured)}
                  className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-semibold rounded-xl transition-all flex items-center gap-1.5 whitespace-nowrap"
                >
                  {isTesting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5 text-emerald-400" />}
                  <span>Kiểm Tra Kết Nối</span>
                </button>
              </div>
            </div>

            {/* Test Result Alert */}
            {testResult && (
              <div
                className={`p-3 rounded-xl text-xs flex items-start gap-2.5 ${
                  testResult.success
                    ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300'
                    : 'bg-rose-500/10 border border-rose-500/30 text-rose-300'
                }`}
              >
                {testResult.success ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                )}
                <span>{testResult.message}</span>
              </div>
            )}

            {/* Operating Mode Selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-2">
                Chế Độ Hoạt Động (Orchestrator Workflow)
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div
                  onClick={() => setLlmProvider('ollama')}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    llmProvider === 'ollama'
                      ? 'bg-emerald-500/10 border-emerald-500/40 shadow-sm'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-200">
                      Dual-Engine: Ollama + Gemini
                    </span>
                    <span className="text-[9px] uppercase font-bold text-emerald-400 bg-emerald-500/20 px-1.5 py-0.5 rounded">
                      Khuyên Dùng
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Ollama ({ollamaModel}) viết kịch bản thần tốc offline. Gemini Imagen 3 sinh ảnh AI nghệ thuật 9:16 (hoặc ảnh thực tế 4K).
                  </p>
                </div>

                <div
                  onClick={() => setLlmProvider('gemini')}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    llmProvider === 'gemini'
                      ? 'bg-emerald-500/10 border-emerald-500/40 shadow-sm'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-200">
                      Full Gemini Cloud
                    </span>
                    <span className="text-[9px] uppercase font-bold text-cyan-400 bg-cyan-500/20 px-1.5 py-0.5 rounded">
                      Cloud 100%
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Google Gemini tạo cả kịch bản và ảnh Imagen 3 trực tiếp từ cloud. Phù hợp khi muốn kịch bản đa góc nhìn sâu rộng.
                  </p>
                </div>
              </div>
            </div>

            {/* Save Status */}
            {saveSuccess && (
              <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                <Check className="w-4 h-4 text-emerald-400" />
                <span>Đã lưu thành công vào file backend/.env! Có hiệu lực ngay lập tức.</span>
              </div>
            )}

            {/* Footer Actions */}
            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
              >
                Đóng
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-slate-950 font-bold px-5 py-2.5 rounded-xl text-xs transition-all shadow-lg shadow-emerald-500/25 active:scale-95 disabled:opacity-50"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                <span>Lưu Cấu Hình AI</span>
              </button>
            </div>
          </form>
        ) : (
          /* TTS Voice Lab Tab */
          <div className="p-6 space-y-5 overflow-y-auto flex-1">
            {/* Filter & Custom Input Toolbar */}
            <div className="space-y-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="flex flex-wrap items-center justify-between gap-3">
                {/* Language Pills */}
                <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-lg border border-slate-800">
                  <button
                    type="button"
                    onClick={() => setVoiceFilter('vi')}
                    className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                      voiceFilter === 'vi'
                        ? 'bg-emerald-500 text-slate-950 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Tiếng Việt ({voiceCatalog.filter((v) => v.locale.startsWith('vi')).length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setVoiceFilter('en')}
                    className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                      voiceFilter === 'en'
                        ? 'bg-emerald-500 text-slate-950 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    English ({voiceCatalog.filter((v) => v.locale.startsWith('en')).length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setVoiceFilter('all')}
                    className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                      voiceFilter === 'all'
                        ? 'bg-emerald-500 text-slate-950 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Tất Cả ({voiceCatalog.length})
                  </button>
                </div>

                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  100% Miễn phí &amp; Không giới hạn ký tự
                </span>
              </div>

              {/* Custom Test Sentence */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1 flex items-center justify-between">
                  <span>Nhập câu tùy chọn để nghe thử trực tiếp:</span>
                  {customSampleText && (
                    <button
                      type="button"
                      onClick={() => setCustomSampleText('')}
                      className="text-[10px] text-rose-400 hover:underline flex items-center gap-1"
                    >
                      <RotateCcw className="w-2.5 h-2.5" /> Dùng câu mẫu mặc định
                    </button>
                  )}
                </label>
                <input
                  type="text"
                  value={customSampleText}
                  onChange={(e) => setCustomSampleText(e.target.value)}
                  placeholder="VD: Chào các bạn! Hôm nay hãy cùng mình tìm hiểu một bí mật thú vị nhé..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            {/* Voice Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {filteredVoices.map((v) => {
                const isPlayingThis = playingVoiceId === v.id;
                return (
                  <div
                    key={v.id}
                    className={`p-3.5 rounded-xl border transition-all flex flex-col justify-between space-y-3 ${
                      isPlayingThis
                        ? 'bg-emerald-500/10 border-emerald-500/50 shadow-md shadow-emerald-500/10'
                        : 'bg-slate-950/60 border-slate-800/90 hover:border-slate-700'
                    }`}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <div>
                          <h4 className="font-bold text-xs text-slate-100 flex items-center gap-1.5">
                            <span>{v.name}</span>
                          </h4>
                          <div className="flex flex-wrap items-center gap-1 mt-1">
                            <span className="text-[10px] text-slate-400 font-medium">
                              {v.gender === 'Male' ? '👨 Nam' : '👩 Nữ'}
                            </span>
                            <span className="text-slate-600 text-[10px]">•</span>
                            <span className="text-[10px] text-emerald-400 font-mono">
                              Tốc độ: {v.rate}
                            </span>
                            {v.pitch && v.pitch !== '+0Hz' && (
                              <>
                                <span className="text-slate-600 text-[10px]">•</span>
                                <span className="text-[10px] text-cyan-400 font-mono">
                                  Cao độ: {v.pitch}
                                </span>
                              </>
                            )}
                          </div>
                        </div>

                        {v.recommended && (
                          <span className="text-[9px] font-bold text-amber-300 bg-amber-500/15 border border-amber-500/30 px-1.5 py-0.5 rounded shrink-0">
                            ⭐ Top Shorts
                          </span>
                        )}
                      </div>

                      {/* Tags */}
                      <div className="flex flex-wrap gap-1 mb-2">
                        {v.tags?.map((t, idx) => (
                          <span
                            key={idx}
                            className="bg-slate-800/80 text-slate-300 px-1.5 py-0.5 rounded text-[9px]"
                          >
                            {t}
                          </span>
                        ))}
                      </div>

                      {/* Sample Quote */}
                      <p className="text-[11px] text-slate-400 italic line-clamp-2">
                        &ldquo;{customSampleText.trim() || v.sample_text}&rdquo;
                      </p>
                    </div>

                    {/* Action Button */}
                    <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between">
                      <span className="text-[10px] text-slate-500 font-mono">{v.id}</span>
                      <button
                        type="button"
                        onClick={() => playAudio(v.id, customSampleText)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm ${
                          isPlayingThis
                            ? 'bg-rose-500 text-white hover:bg-rose-600'
                            : 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30'
                        }`}
                      >
                        {isPlayingThis ? (
                          isAudioLoading ? (
                            <>
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              <span>Đang tải...</span>
                            </>
                          ) : (
                            <>
                              <Square className="w-3.5 h-3.5 fill-current animate-pulse" />
                              <span>Dừng nghe</span>
                            </>
                          )
                        ) : (
                          <>
                            <Volume2 className="w-3.5 h-3.5" />
                            <span>Nghe thử</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Footer Close */}
            <div className="flex items-center justify-end pt-3 border-t border-slate-800 shrink-0">
              <button
                type="button"
                onClick={handleClose}
                className="px-5 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
              >
                Đóng Thư Viện
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

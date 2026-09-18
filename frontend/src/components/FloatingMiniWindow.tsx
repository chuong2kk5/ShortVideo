import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Film,
  Sparkles,
  Maximize2,
  Minimize2,
  X,
  Play,
  Download,
  Terminal,
  Layers,
  Volume2,
  Eye,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Radio,
  ExternalLink,
  Tag,
  MessageSquareQuote,
  ShieldCheck,
  Search,
  Mic,
  Clapperboard,
  Globe,
  Sliders,
  Check,
} from 'lucide-react';
import { PipelineJob, Project, PipelineLog } from '../types';

interface FloatingMiniWindowProps {
  job: PipelineJob | null;
  project: Project | null;
  onOpenStudio: () => void;
  onClose?: () => void;
}

interface SceneInfo {
  sceneIndex: number;
  totalScenes: number;
  narration?: string;
  visualPrompt?: string;
  visualKeywords?: string;
  mediaUrl?: string;
  mediaType?: 'video' | 'image';
  status?: string;
  duration?: number;
  voice?: string;
  renderedSegmentUrl?: string;
}

const PRODUCTION_STAGES = [
  { key: 'script_generation', label: '1. Kịch Bản', icon: Sparkles },
  { key: 'image_generation', label: '2. Tìm Footage Web', icon: Globe },
  { key: 'tts_synthesis', label: '3. Thu Âm TTS', icon: Mic },
  { key: 'video_rendering', label: '4. Dựng & Kỹ Xảo', icon: Clapperboard },
  { key: 'video_verification', label: '5. Rà Soát', icon: ShieldCheck },
];

export const FloatingMiniWindow: React.FC<FloatingMiniWindowProps> = ({
  job,
  project,
  onOpenStudio,
  onClose,
}) => {
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'process' | 'logs'>('process');
  const [selectedSceneIndex, setSelectedSceneIndex] = useState<number | null>(null);
  const [dismissedJobId, setDismissedJobId] = useState<string | null>(null);

  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-reopen and reset dismiss if a new job starts
  useEffect(() => {
    if (job?.id && job.id !== dismissedJobId) {
      setIsMinimized(false);
      setSelectedSceneIndex(null);
    }
  }, [job?.id]);

  // Scroll logs to bottom in log tab
  useEffect(() => {
    if (activeTab === 'logs' && logsEndRef.current) {
      logsEndRef.current.scrollTop = logsEndRef.current.scrollHeight;
    }
  }, [job?.logs, activeTab]);

  // Aggregate all process data and scenes from logs
  const { scenesMap, latestScene, finalVideoUrl, scriptData, verifyData } = useMemo(() => {
    const map = new Map<number, SceneInfo>();
    let latest: SceneInfo | null = null;
    let finalUrl: string | null = null;
    let script: any = null;
    let verify: any = null;

    if (job?.logs) {
      for (const log of job.logs) {
        if (log.extra_data) {
          const ed = log.extra_data;
          if (ed.hook || ed.cta || ed.scenes_summary) {
            script = ed;
          }
          if (ed.integrity_passed !== undefined || ed.resolution) {
            verify = ed;
          }
          if (ed.scene_index !== undefined) {
            const idx = ed.scene_index;
            const existing = map.get(idx) || {
              sceneIndex: idx,
              totalScenes: ed.total_scenes || 1,
            };
            const updated: SceneInfo = {
              ...existing,
              sceneIndex: idx,
              totalScenes: ed.total_scenes ?? existing.totalScenes,
              narration: ed.narration ?? existing.narration,
              visualPrompt: ed.visual_prompt ?? existing.visualPrompt,
              visualKeywords: ed.visual_keywords ?? existing.visualKeywords,
              mediaUrl: ed.media_url ?? existing.mediaUrl,
              mediaType: ed.media_type ?? existing.mediaType,
              status: ed.status ?? existing.status,
              duration: ed.duration ?? existing.duration,
              voice: ed.voice ?? existing.voice,
              renderedSegmentUrl: ed.rendered_segment_url ?? existing.renderedSegmentUrl,
            };
            map.set(idx, updated);
            latest = updated;
          }
          if (ed.final_video_url) {
            finalUrl = ed.final_video_url;
          }
        }
      }
    }

    if (!finalUrl && (job?.status === 'completed' || project?.final_video_path) && project?.id) {
      finalUrl = `/static/outputs/${project.id}/final_shorts.mp4`;
    }

    return {
      scenesMap: map,
      latestScene: latest,
      finalVideoUrl: finalUrl,
      scriptData: script,
      verifyData: verify,
    };
  }, [job?.logs, job?.status, project?.id, project?.final_video_path]);

  if (!job || job.id === dismissedJobId) {
    return null;
  }

  const isCompleted = job.status === 'completed';
  const isFailed = job.status === 'failed';
  const isRunning = job.status === 'running' || job.status === 'queued';

  const allScenes = Array.from(scenesMap.values()).sort((a, b) => a.sceneIndex - b.sceneIndex);
  const activeScene = selectedSceneIndex !== null
    ? (scenesMap.get(selectedSceneIndex) || latestScene)
    : latestScene;

  // Determine stage progress states
  const getStageState = (stageKey: string) => {
    const stageOrder = ['script_generation', 'image_generation', 'tts_synthesis', 'video_rendering', 'video_verification'];
    const currentIdx = stageOrder.indexOf(job.current_stage);
    const thisIdx = stageOrder.indexOf(stageKey);

    if (isCompleted) return 'completed';
    if (isFailed && thisIdx === currentIdx) return 'failed';
    if (thisIdx < currentIdx) return 'completed';
    if (thisIdx === currentIdx) return 'active';
    return 'waiting';
  };

  const recentLogs = (job.logs || []).slice(-3);
  const lastLogMsg = recentLogs.length > 0 ? recentLogs[recentLogs.length - 1].message : 'Hệ thống đang sẵn sàng...';

  // Minimized Pill Mode
  if (isMinimized) {
    return (
      <aside
        aria-label="Cửa sổ thu nhỏ giám sát AI"
        onClick={() => setIsMinimized(false)}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-2.5 bg-slate-900/95 hover:bg-slate-800 border border-cyan-500/40 rounded-full shadow-2xl shadow-cyan-500/10 cursor-pointer backdrop-blur-md transition-all duration-300 hover:scale-105 group"
      >
        <div className="relative flex items-center justify-center">
          {isRunning && (
            <span className="absolute w-full h-full rounded-full bg-cyan-400 opacity-75 animate-ping" />
          )}
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-emerald-500 flex items-center justify-center text-slate-950 font-bold shadow">
            {isRunning ? (
              <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
            ) : isCompleted ? (
              <CheckCircle2 className="w-4 h-4 text-slate-950" />
            ) : (
              <AlertCircle className="w-4 h-4 text-slate-950" />
            )}
          </div>
        </div>

        <div className="flex flex-col text-left">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-black text-cyan-400 uppercase tracking-wider">
              {isRunning ? 'AI Đang Làm Việc' : isCompleted ? 'Đã Hoàn Tất' : 'Lỗi'}
            </span>
            <span className="text-[10px] text-slate-400 truncate max-w-[130px]">
              {project?.title || 'Dự án Shorts'}
            </span>
          </div>
          <span className="text-[10px] text-slate-300 font-medium truncate max-w-[200px]">
            {lastLogMsg}
          </span>
        </div>

        <button
          type="button"
          aria-label="Mở rộng màn hình giám sát"
          className="ml-1 p-1 text-slate-400 hover:text-slate-100 group-hover:translate-y-[-1px] transition-transform"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </aside>
    );
  }

  // Expanded Window Mode - FOCUSED ON LIVE WORK PROCESS
  return (
    <aside
      aria-label="Màn hình giám sát quá trình làm của AI"
      className="fixed bottom-5 right-5 z-50 w-[420px] sm:w-[460px] max-h-[88vh] bg-slate-900/98 backdrop-blur-2xl border border-slate-700/90 rounded-2xl shadow-2xl shadow-black/90 flex flex-col overflow-hidden transition-all duration-300 animate-in fade-in slide-in-from-bottom-5"
    >
      {/* Top Accent Gradient Bar */}
      <div className="h-1.5 w-full bg-gradient-to-r from-cyan-500 via-teal-400 to-emerald-500" />

      {/* Header Bar */}
      <div className="px-4 py-3 bg-slate-950/80 border-b border-slate-800/90 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500/25 to-emerald-500/25 border border-cyan-500/40 flex items-center justify-center shrink-0 shadow-sm">
            <Clapperboard className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-black tracking-wide text-white uppercase truncate">
                AI Studio Live Process
              </h3>
              {isRunning && (
                <span className="flex items-center gap-1 text-[9px] font-black uppercase px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                  ĐANG LÀM
                </span>
              )}
              {isCompleted && (
                <span className="flex items-center gap-1 text-[9px] font-black uppercase px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  <Check className="w-2.5 h-2.5 text-emerald-400 stroke-[3]" />
                  XONG
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-300 font-medium truncate max-w-[240px]">
              {project?.title || project?.topic || 'Đang sản xuất video ngắn...'}
            </p>
          </div>
        </div>

        {/* Window Controls */}
        <div className="flex items-center gap-1 shrink-0">
          <div className="flex items-center bg-slate-900 rounded-lg p-0.5 border border-slate-800">
            <button
              onClick={() => setActiveTab('process')}
              title="Xem quá trình làm"
              className={`px-2 py-1 rounded text-[10px] font-bold flex items-center gap-1 transition-colors ${
                activeTab === 'process'
                  ? 'bg-slate-800 text-cyan-400 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Quá trình</span>
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              title="Nhật ký lệnh Terminal"
              className={`px-2 py-1 rounded text-[10px] font-bold flex items-center gap-1 transition-colors ${
                activeTab === 'logs'
                  ? 'bg-slate-800 text-cyan-400 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Log</span>
            </button>
          </div>

          <button
            onClick={() => setIsMinimized(true)}
            title="Thu nhỏ cửa sổ"
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <Minimize2 className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => {
              setDismissedJobId(job.id);
              if (onClose) onClose();
            }}
            title="Đóng cửa sổ"
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Production Stepper - Visual 5-Step Process */}
      <div className="px-3.5 py-2.5 bg-slate-950/60 border-b border-slate-800/80">
        <div className="grid grid-cols-5 gap-1 text-[10px]">
          {PRODUCTION_STAGES.map((st) => {
            const state = getStageState(st.key);
            const Icon = st.icon;
            const isStActive = state === 'active';
            const isStDone = state === 'completed';

            return (
              <div
                key={st.key}
                className={`flex flex-col items-center justify-center p-1.5 rounded-lg border text-center transition-all ${
                  isStActive
                    ? 'bg-cyan-500/15 border-cyan-500/50 text-cyan-300 font-black ring-1 ring-cyan-500/30'
                    : isStDone
                    ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-400 font-bold'
                    : 'bg-slate-900/40 border-slate-800/60 text-slate-500 font-medium'
                }`}
              >
                <div className="flex items-center gap-1 mb-0.5">
                  {isStActive ? (
                    <Loader2 className="w-3 h-3 animate-spin text-cyan-400" />
                  ) : isStDone ? (
                    <Check className="w-3 h-3 text-emerald-400 stroke-[3]" />
                  ) : (
                    <Icon className="w-3 h-3 text-slate-500" />
                  )}
                </div>
                <span className="text-[9px] leading-tight truncate max-w-full">
                  {st.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Process Inspector Area */}
      <div className="p-3.5 overflow-y-auto max-h-[56vh] space-y-3">
        {activeTab === 'process' ? (
          <>
            {/* If Video is Completed -> Mini 9:16 Video Player */}
            {isCompleted && finalVideoUrl ? (
              <div className="space-y-3 animate-in fade-in">
                <div className="relative rounded-xl overflow-hidden bg-black border border-emerald-500/40 shadow-xl">
                  <video
                    src={finalVideoUrl}
                    controls
                    autoPlay
                    loop
                    className="w-full aspect-[9/16] max-h-64 object-contain bg-black mx-auto"
                  />
                  <div className="absolute top-2 left-2 bg-emerald-500 text-slate-950 text-[10px] font-black px-2.5 py-0.5 rounded-md shadow-md flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    1080x1920 FULL HD SẴN SÀNG
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <a
                    href={finalVideoUrl}
                    download="final_shorts.mp4"
                    className="flex-1 flex items-center justify-center gap-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold py-2.5 px-3 rounded-xl text-xs transition-all shadow-lg shadow-emerald-500/25"
                  >
                    <Download className="w-4 h-4" />
                    <span>Tải Video MP4 Hoàn Chỉnh</span>
                  </a>
                  <button
                    onClick={onOpenStudio}
                    className="flex items-center justify-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold py-2.5 px-3 rounded-xl text-xs border border-slate-700 transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Mở Studio</span>
                  </button>
                </div>
              </div>
            ) : (
              /* LIVE ACTION PROCESS BOARD - Shows what AI is doing right now */
              <div className="space-y-3">
                {/* 1. STAGE: SCRIPT GENERATION LIVE WORK */}
                {job.current_stage === 'script_generation' && (
                  <div className="bg-slate-950/80 border border-cyan-500/30 rounded-xl p-3.5 space-y-2.5 animate-in fade-in">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5 text-xs font-black text-cyan-400 uppercase">
                        <Sparkles className="w-4 h-4 animate-pulse" />
                        AI Đang Viết Kịch Bản 3 Hồi
                      </span>
                      <span className="text-[10px] bg-cyan-500/20 text-cyan-300 font-bold px-2 py-0.5 rounded-md border border-cyan-500/30">
                        Mục tiêu: {project?.target_duration || 30}s
                      </span>
                    </div>

                    <div className="bg-slate-900/90 rounded-lg p-2.5 border border-slate-800 space-y-1.5">
                      <div className="text-[10px] font-bold text-slate-400 uppercase">Chủ đề phân tích:</div>
                      <p className="text-xs text-slate-200 font-medium italic">
                        "{project?.topic || project?.title}"
                      </p>
                    </div>

                    {scriptData ? (
                      <div className="space-y-2">
                        {scriptData.hook && (
                          <div className="bg-amber-950/30 border border-amber-500/30 rounded-lg p-2.5">
                            <div className="text-[10px] font-bold text-amber-400 uppercase flex items-center gap-1">
                              🔥 Hook Mở Đầu (0 - 4s):
                            </div>
                            <p className="text-xs text-amber-200 font-semibold mt-1">
                              "{scriptData.hook}"
                            </p>
                          </div>
                        )}
                        {scriptData.cta && (
                          <div className="bg-emerald-950/30 border border-emerald-500/30 rounded-lg p-2.5">
                            <div className="text-[10px] font-bold text-emerald-400 uppercase flex items-center gap-1">
                              👉 Kêu Gọi Hành Động (CTA):
                            </div>
                            <p className="text-xs text-emerald-200 font-medium mt-1">
                              "{scriptData.cta}"
                            </p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="py-4 flex flex-col items-center justify-center text-center space-y-2">
                        <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
                        <span className="text-xs text-slate-300 font-semibold">
                          Đang tạo câu Hook giật gân & cấu trúc các phân cảnh...
                        </span>
                        <span className="text-[10px] text-slate-500">
                          Áp dụng công thức giữ chân người xem chuẩn CapCut/TikTok
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* 2. ACTIVE SCENE WORK PROCESS CARD (Visual Search / Image / Video) */}
                {activeScene ? (
                  <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 space-y-3">
                    {/* Scene Header with Live Status */}
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="bg-cyan-500/20 text-cyan-300 font-black px-2 py-0.5 rounded-md text-[10px] uppercase border border-cyan-500/30">
                          Cảnh {activeScene.sceneIndex + 1} / {activeScene.totalScenes || '?'}
                        </span>
                        {activeScene.mediaType && (
                          <span className="text-[10px] font-bold text-slate-300 flex items-center gap-1">
                            {activeScene.mediaType === 'video' ? '🎥 Video clip thực tế' : '🖼️ Ảnh thực tế Full HD'}
                          </span>
                        )}
                      </div>

                      <div className="text-[10px]">
                        {activeScene.status === 'ready' ? (
                          <span className="text-emerald-400 font-bold flex items-center gap-1">
                            <Check className="w-3 h-3 stroke-[3]" /> Đã lấy từ web
                          </span>
                        ) : (
                          <span className="text-amber-400 font-bold flex items-center gap-1 animate-pulse">
                            <Loader2 className="w-3 h-3 animate-spin" /> Đang quét internet...
                          </span>
                        )}
                      </div>
                    </div>

                    {/* LIVE MEDIA VISUAL - Preview Video or Photo from Web */}
                    {activeScene.mediaUrl ? (
                      <div className="relative rounded-xl overflow-hidden bg-black border border-slate-700/80 group shadow-md">
                        {activeScene.mediaType === 'video' ? (
                          <video
                            src={activeScene.mediaUrl}
                            autoPlay
                            loop
                            muted
                            playsInline
                            className="w-full h-44 object-cover bg-black"
                          />
                        ) : (
                          <img
                            src={activeScene.mediaUrl}
                            alt={`Scene ${activeScene.sceneIndex + 1}`}
                            className="w-full h-44 object-cover bg-black"
                          />
                        )}
                        <div className="absolute top-2 left-2 bg-slate-950/90 text-cyan-300 text-[9px] font-mono px-2 py-0.5 rounded border border-slate-700">
                          {activeScene.mediaType === 'video' ? 'VIDEO 9:16 TRÀN VIỀN' : 'ẢNH THỰC TẾ 9:16'}
                        </div>
                      </div>
                    ) : (
                      /* Live Web Searching Radar Display */
                      <div className="h-32 rounded-xl bg-slate-900/90 border border-dashed border-cyan-500/40 flex flex-col items-center justify-center p-3 text-center space-y-1.5 relative overflow-hidden">
                        <div className="w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center">
                          <Search className="w-4 h-4 text-cyan-400 animate-pulse" />
                        </div>
                        <span className="text-xs font-bold text-slate-200">
                          Đang tìm kiếm hình ảnh & video thực tế...
                        </span>
                        <span className="text-[10px] text-cyan-300 font-mono">
                          Nguồn: Google Images & Web Photographic Index
                        </span>
                      </div>
                    )}

                    {/* Spoken Narration Text */}
                    {activeScene.narration && (
                      <div className="bg-slate-900/90 rounded-lg p-2.5 border border-slate-800 space-y-1">
                        <div className="flex items-center gap-1 text-[10px] font-bold text-amber-400 uppercase">
                          <MessageSquareQuote className="w-3.5 h-3.5" />
                          <span>Lời thoại AI đọc (Vietnamese):</span>
                        </div>
                        <p className="text-xs text-slate-200 font-medium leading-relaxed">
                          "{activeScene.narration}"
                        </p>
                      </div>
                    )}

                    {/* English Search Prompt & Keywords */}
                    {activeScene.visualPrompt && (
                      <div className="bg-slate-900/90 rounded-lg p-2.5 border border-slate-800 space-y-1.5">
                        <div className="flex items-center gap-1 text-[10px] font-bold text-cyan-400 uppercase">
                          <Globe className="w-3.5 h-3.5" />
                          <span>Từ khóa & Prompt AI tìm kiếm trên mạng:</span>
                        </div>
                        <p className="text-[11px] text-slate-300 font-mono italic leading-relaxed bg-slate-950/70 p-2 rounded border border-slate-800">
                          {activeScene.visualPrompt}
                        </p>

                        {/* Keyword tags */}
                        {activeScene.visualKeywords && (
                          <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
                            <Tag className="w-3 h-3 text-slate-400 shrink-0" />
                            {activeScene.visualKeywords
                              .split(',')
                              .map((k) => k.trim())
                              .filter(Boolean)
                              .slice(0, 5)
                              .map((kw, i) => (
                                <span
                                  key={i}
                                  className="text-[9px] bg-slate-800 text-cyan-300 px-1.5 py-0.5 rounded border border-slate-700 font-mono"
                                >
                                  #{kw}
                                </span>
                              ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Stage 3 Audio Details (if synthesized) */}
                    {activeScene.duration && (
                      <div className="bg-slate-900/90 rounded-lg p-2.5 border border-slate-800 flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                            <Mic className="w-3.5 h-3.5" />
                          </div>
                          <div>
                            <div className="text-[10px] font-bold text-emerald-400">
                              Thu âm Edge-TTS: {activeScene.duration}s
                            </div>
                            <div className="text-[10px] text-slate-400">
                              Giọng: {activeScene.voice || 'Studio Voice'}
                            </div>
                          </div>
                        </div>

                        {/* Animated Waveform bars */}
                        <div className="flex items-end gap-0.5 h-4">
                          <span className="w-1 bg-emerald-400 h-2 animate-pulse rounded-full" />
                          <span className="w-1 bg-emerald-400 h-4 animate-pulse rounded-full delay-75" />
                          <span className="w-1 bg-emerald-400 h-3 animate-pulse rounded-full delay-150" />
                          <span className="w-1 bg-emerald-400 h-4 animate-pulse rounded-full delay-100" />
                          <span className="w-1 bg-emerald-400 h-2 animate-pulse rounded-full" />
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  /* Waiting card if no scene active yet */
                  job.current_stage !== 'script_generation' && (
                    <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 text-center space-y-2">
                      <Loader2 className="w-6 h-6 text-cyan-400 animate-spin mx-auto" />
                      <h4 className="text-xs font-bold text-slate-200">
                        Đang Nạp Dữ Liệu Sản Xuất...
                      </h4>
                      <p className="text-[11px] text-slate-400">
                        Chuẩn bị thực thi các bước dựng phim tiếp theo.
                      </p>
                    </div>
                  )
                )}

                {/* 3. SCENE FILMSTRIP - User can click to inspect any created scene */}
                {allScenes.length > 1 && (
                  <div className="space-y-1.5 pt-1">
                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                      <span className="font-bold flex items-center gap-1 text-slate-300">
                        <Layers className="w-3 h-3 text-cyan-400" />
                        Các Cảnh Đã Sản Xuất ({allScenes.length}):
                      </span>
                      {selectedSceneIndex !== null && (
                        <button
                          onClick={() => setSelectedSceneIndex(null)}
                          className="text-cyan-400 hover:underline font-bold"
                        >
                          Xem cảnh mới nhất
                        </button>
                      )}
                    </div>
                    <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-slate-800">
                      {allScenes.map((sc) => {
                        const isSelected = (selectedSceneIndex ?? latestScene?.sceneIndex) === sc.sceneIndex;
                        return (
                          <button
                            key={sc.sceneIndex}
                            onClick={() => setSelectedSceneIndex(sc.sceneIndex)}
                            className={`shrink-0 w-16 h-20 rounded-lg overflow-hidden border relative text-left transition-all ${
                              isSelected
                                ? 'border-cyan-400 ring-2 ring-cyan-400/40'
                                : 'border-slate-800 hover:border-slate-700 opacity-70 hover:opacity-100'
                            }`}
                          >
                            {sc.mediaUrl ? (
                              sc.mediaType === 'video' ? (
                                <video
                                  src={sc.mediaUrl}
                                  muted
                                  className="w-full h-full object-cover"
                                />
                              ) : (
                                <img
                                  src={sc.mediaUrl}
                                  alt={`Cảnh ${sc.sceneIndex + 1}`}
                                  className="w-full h-full object-cover"
                                />
                              )
                            ) : (
                              <div className="w-full h-full bg-slate-950 flex items-center justify-center">
                                <Loader2 className="w-3 h-3 animate-spin text-slate-500" />
                              </div>
                            )}
                            <div className="absolute top-0.5 left-0.5 bg-slate-950/90 text-[8px] font-bold text-slate-200 px-1 rounded">
                              #{sc.sceneIndex + 1}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          /* Logs Tab View */
          <div
            ref={logsEndRef}
            className="bg-slate-950 rounded-xl p-2.5 border border-slate-800 font-mono text-[10px] space-y-1.5 max-h-[48vh] overflow-y-auto"
          >
            {(job.logs || []).map((log, idx) => (
              <div
                key={idx}
                className={`p-1.5 rounded flex items-start gap-2 ${
                  log.level === 'error'
                    ? 'bg-rose-950/40 text-rose-300 border border-rose-900/40'
                    : log.level === 'warning'
                    ? 'bg-amber-950/40 text-amber-300 border border-amber-900/40'
                    : 'text-slate-300 hover:bg-slate-900'
                }`}
              >
                <span className="text-slate-400 shrink-0 select-none">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className="shrink-0 text-cyan-400 font-bold uppercase text-[9px]">
                  [{log.stage}]
                </span>
                <span className="break-all flex-1">{log.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Live Action Ticker Footer */}
      <div className="px-3.5 py-2.5 bg-slate-950 border-t border-slate-800/90 flex items-center justify-between gap-2 text-[11px] text-slate-400">
        <div className="flex items-center gap-2 truncate flex-1">
          <Radio className="w-3.5 h-3.5 text-cyan-400 shrink-0 animate-pulse" />
          <span className="truncate text-slate-200 font-medium">
            {lastLogMsg}
          </span>
        </div>
        <button
          onClick={onOpenStudio}
          className="text-cyan-400 hover:text-cyan-300 hover:underline font-bold shrink-0 flex items-center gap-1 text-[10px]"
        >
          Studio
          <ExternalLink className="w-3 h-3" />
        </button>
      </div>
    </aside>
  );
};

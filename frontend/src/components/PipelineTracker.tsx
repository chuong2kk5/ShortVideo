import React, { useEffect, useRef } from 'react';
import { CheckCircle2, Circle, Loader2, AlertTriangle, Terminal, Video, Download } from 'lucide-react';
import { PipelineJob, Project } from '../types';

interface PipelineTrackerProps {
  job: PipelineJob | null;
  project: Project | null;
  onRefreshProject: () => void;
}

const PIPELINE_STEPS = [
  { id: 1, name: 'Khởi tạo Dự án', stage: 'queued' },
  { id: 2, name: 'AI Kịch Bản (Hook/CTA)', stage: 'script_generation' },
  { id: 3, name: 'Tự Sửa Lỗi JSON Schema', stage: 'script_generation' },
  { id: 4, name: 'Phân tích Visual Prompts 9:16', stage: 'image_generation' },
  { id: 5, name: 'Sinh Khung Hình Nghệ Thuật', stage: 'image_generation' },
  { id: 6, name: 'Thuyết Minh Edge-TTS Studio', stage: 'tts_synthesis' },
  { id: 7, name: 'Khớp Word Timestamps Phụ Đề', stage: 'tts_synthesis' },
  { id: 8, name: 'Hiệu Ứng Ken Burns / Zoom', stage: 'video_rendering' },
  { id: 9, name: 'Mix Âm Thanh BGM Ducking', stage: 'video_rendering' },
  { id: 10, name: 'Rà Soát Chất Lượng Video', stage: 'video_verification' },
  { id: 11, name: 'Burn Phụ Đề & Xuất Bản MP4', stage: 'completed' },
];

export const PipelineTracker: React.FC<PipelineTrackerProps> = ({ job, project, onRefreshProject }) => {
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [job?.logs]);

  if (!job) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center">
        <div className="w-12 h-12 rounded-2xl bg-slate-800/80 text-slate-500 mx-auto flex items-center justify-center mb-3">
          <Video className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-bold text-slate-200">Chưa Có Pipeline Đang Chạy</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
          Nhấn nút <strong className="text-emerald-400">[Tạo Video Mới]</strong> bên trên để bắt đầu quy trình sản xuất video tự động 10 bước.
        </p>
      </div>
    );
  }

  const isCompleted = job.status === 'completed';
  const isFailed = job.status === 'failed';

  // Calculate current active step index (0 - 9)
  const currentStepIndex = Math.min(
    PIPELINE_STEPS.length - 1,
    Math.floor((job.progress / 100) * PIPELINE_STEPS.length)
  );

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      {/* Tracker Header */}
      <div className="p-6 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
              TIẾN TRÌNH SẢN XUẤT VIDEO TỰ ĐỘNG
            </span>
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                isCompleted
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : isFailed
                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 animate-pulse'
              }`}
            >
              {job.status}
            </span>
          </div>
          <h2 className="text-base font-extrabold text-slate-100">
            {project?.title || 'Đang thực thi pipeline...'}
          </h2>
        </div>

        {/* Action button if finished */}
        {isCompleted && project?.final_video_path && (
          <a
            href={`/static/outputs/${project.id}/final_shorts.mp4`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold px-4 py-2 rounded-xl text-xs transition-all shadow-lg shadow-emerald-500/25"
          >
            <Download className="w-4 h-4" />
            <span>Tải Video MP4 Hoàn Chỉnh</span>
          </a>
        )}
      </div>

      {/* 10-Step Visual Flow */}
      <div className="p-6 border-b border-slate-800 bg-slate-950/40">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-400">Tiến Độ Quy Trình:</span>
          <span className="text-sm font-extrabold text-emerald-400">{Math.round(job.progress)}%</span>
        </div>

        {/* Progress bar */}
        <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden mb-6">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 transition-all duration-500 rounded-full"
            style={{ width: `${job.progress}%` }}
          />
        </div>

        {/* 10 Steps Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
          {PIPELINE_STEPS.map((step, idx) => {
            const isStepDone = job.progress >= ((idx + 1) / PIPELINE_STEPS.length) * 100 || isCompleted;
            const isStepActive = !isStepDone && job.progress >= (idx / PIPELINE_STEPS.length) * 100 && !isFailed;

            return (
              <div
                key={step.id}
                className={`p-2.5 rounded-xl border transition-all text-left ${
                  isStepDone
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : isStepActive
                    ? 'bg-cyan-500/10 border-cyan-500/40 text-cyan-300 ring-1 ring-cyan-500/30'
                    : 'bg-slate-900/60 border-slate-800/80 text-slate-500'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  {isStepDone ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                  ) : isStepActive ? (
                    <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin flex-shrink-0" />
                  ) : (
                    <Circle className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />
                  )}
                  <span className="text-[10px] font-bold uppercase tracking-wider">Bước {step.id}</span>
                </div>
                <div className="text-[11px] font-semibold leading-tight line-clamp-2">{step.name}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Finished Video Player */}
      {isCompleted && project?.final_video_path && (
        <div className="p-6 bg-slate-950/70 border-b border-slate-800 flex flex-col items-center">
          <div className="flex items-center justify-between w-full max-w-[320px] mb-3">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Video className="w-4 h-4 text-emerald-400" />
              <span>Video Hoàn Chỉnh (1080x1920)</span>
            </h3>
            <a
              href={`/static/outputs/${project.id}/final_shorts.mp4`}
              download={`${project.title || 'shorts'}.mp4`}
              className="flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-lg transition-all font-semibold"
              title="Tải video về máy tính"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Tải MP4</span>
            </a>
          </div>

          <div className="relative group max-w-[280px] aspect-[9/16] rounded-2xl overflow-hidden shadow-2xl border-2 border-emerald-500/40 bg-black">
            <video
              key={`final_video_${project.id}`}
              src={`/static/outputs/${project.id}/final_shorts.mp4`}
              controls
              playsInline
              preload="metadata"
              className="w-full h-full object-cover"
            />
          </div>
          <p className="text-[11px] text-slate-400 mt-2.5 text-center">
            Bấm nút <strong className="text-emerald-400">Play ▶</strong> để thưởng thức video từ đầu đến cuối (Chuẩn dọc 1080p, không bị lặp lại).
          </p>
        </div>
      )}

      {/* Terminal Live Logs */}
      <div className="p-4 bg-slate-950">
        <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-400 px-2">
          <Terminal className="w-3.5 h-3.5 text-emerald-400" />
          <span>Real-time Execution Terminal Logs:</span>
        </div>
        <div
          ref={logContainerRef}
          className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 h-44 overflow-y-auto font-mono text-xs space-y-1"
        >
          {job.logs && job.logs.length > 0 ? (
            job.logs.map((log, i) => (
              <div
                key={i}
                className={`leading-relaxed ${
                  log.level === 'error'
                    ? 'text-rose-400'
                    : log.level === 'warning'
                    ? 'text-amber-400'
                    : 'text-slate-300'
                }`}
              >
                <span className="text-slate-600 select-none mr-2">[{log.timestamp.slice(11, 19)}]</span>
                <span className="text-emerald-400 font-semibold mr-2">[{log.stage}]:</span>
                <span>{log.message}</span>
              </div>
            ))
          ) : (
            <div className="text-slate-600 italic">Đang chờ sự kiện đầu tiên từ pipeline runner...</div>
          )}
        </div>
      </div>
    </div>
  );
};


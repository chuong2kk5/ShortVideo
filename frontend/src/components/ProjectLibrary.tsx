import React, { useState } from 'react';
import { Film, Download, Trash2, ExternalLink, Play, Clock, Search } from 'lucide-react';
import { Project } from '../types';

interface ProjectLibraryProps {
  projects: Project[];
  onSelectProject: (project: Project) => void;
  onDeleteProject: (projectId: string) => Promise<void>;
}

export const ProjectLibrary: React.FC<ProjectLibraryProps> = ({
  projects,
  onSelectProject,
  onDeleteProject,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const filtered = projects.filter(
    (p) =>
      p.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.topic.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!confirm('Bạn có chắc muốn xóa dự án này?')) return;
    setDeletingId(id);
    try {
      await onDeleteProject(id);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Tìm kiếm dự án theo tiêu đề hoặc chủ đề..."
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 outline-none focus:border-emerald-500"
          />
        </div>
        <span className="text-xs text-slate-400 font-semibold">{projects.length} Dự án</span>
      </div>

      {/* Projects Grid */}
      {filtered.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
          <Film className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <h3 className="font-bold text-sm text-slate-300">Chưa tìm thấy dự án nào</h3>
          <p className="text-xs text-slate-500 mt-1">Hãy tạo video mới để bắt đầu lưu trữ trong thư viện.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((proj) => {
            const hasVideo = !!proj.final_video_path;
            const sceneCount = proj.scenes?.length || 0;

            return (
              <div
                key={proj.id}
                onClick={() => onSelectProject(proj)}
                className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl overflow-hidden shadow-lg transition-all cursor-pointer group flex flex-col justify-between"
              >
                <div>
                  {/* Thumbnail / Preview Canvas */}
                  <div className="aspect-[16/9] bg-slate-950 border-b border-slate-800 relative flex items-center justify-center overflow-hidden">
                    {hasVideo ? (
                      <video
                        src={`/static/outputs/${proj.id}/final_shorts.mp4`}
                        preload="metadata"
                        controls
                        className="w-full h-full object-cover"
                      />
                    ) : proj.scenes && proj.scenes[0]?.image_path ? (
                      <img
                        src={`/static/outputs/${proj.id}/scenes/scene_00.jpg`}
                        alt={proj.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <div className="text-center p-4">
                        <Film className="w-8 h-8 text-slate-700 mx-auto mb-1" />
                        <span className="text-[10px] text-slate-600">Đang tạo nội dung</span>
                      </div>
                    )}

                    {/* Status Badge */}
                    <div className="absolute top-2.5 right-2.5">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                          proj.status === 'completed'
                            ? 'bg-emerald-500/80 text-slate-950'
                            : proj.status === 'ready_to_render'
                            ? 'bg-cyan-500/80 text-slate-950'
                            : 'bg-slate-800/80 text-slate-300'
                        }`}
                      >
                        {proj.status}
                      </span>
                    </div>
                  </div>

                  {/* Body */}
                  <div className="p-4 space-y-2">
                    <h3 className="font-bold text-sm text-slate-100 group-hover:text-emerald-400 transition-colors line-clamp-1">
                      {proj.title}
                    </h3>
                    <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{proj.topic}</p>

                    <div className="flex items-center gap-3 text-[11px] text-slate-500 pt-1">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {proj.target_duration}s
                      </span>
                      <span>•</span>
                      <span>{sceneCount} Phân cảnh</span>
                      <span>•</span>
                      <span>{proj.created_at.slice(0, 10)}</span>
                    </div>
                  </div>
                </div>

                {/* Footer Buttons */}
                <div className="p-3 bg-slate-950/60 border-t border-slate-800 flex items-center justify-between">
                  {hasVideo ? (
                    <a
                      href={`/static/outputs/${proj.id}/final_shorts.mp4`}
                      target="_blank"
                      rel="noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="flex items-center gap-1 text-xs font-semibold text-emerald-400 hover:text-emerald-300"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Tải MP4</span>
                    </a>
                  ) : (
                    <span className="text-[11px] text-slate-500 italic">Chưa render video</span>
                  )}

                  <button
                    onClick={(e) => handleDelete(e, proj.id)}
                    disabled={deletingId === proj.id}
                    className="text-slate-500 hover:text-rose-400 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};


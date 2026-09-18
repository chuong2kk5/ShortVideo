import React, { useState } from 'react';
import { Play, Film, Move, Volume2, Save, Image as ImageIcon, Sparkles } from 'lucide-react';
import { Project, Scene } from '../types';

interface SceneEditorProps {
  project: Project;
  onUpdateScene: (sceneId: string, data: Partial<Scene>) => Promise<void>;
  onRunRender: () => void;
}

export const SceneEditor: React.FC<SceneEditorProps> = ({ project, onUpdateScene, onRunRender }) => {
  const [editingScenes, setEditingScenes] = useState<Record<string, Partial<Scene>>>({});
  const [savingSceneId, setSavingSceneId] = useState<string | null>(null);

  const handleFieldChange = (sceneId: string, field: keyof Scene, value: any) => {
    setEditingScenes((prev) => ({
      ...prev,
      [sceneId]: {
        ...prev[sceneId],
        [field]: value,
      },
    }));
  };

  const handleSaveScene = async (scene: Scene) => {
    const changes = editingScenes[scene.id];
    if (!changes) return;

    setSavingSceneId(scene.id);
    try {
      await onUpdateScene(scene.id, changes);
      // Clear pending changes for this scene
      setEditingScenes((prev) => {
        const next = { ...prev };
        delete next[scene.id];
        return next;
      });
    } finally {
      setSavingSceneId(null);
    }
  };

  const scenes = project.scenes || [];

  return (
    <div className="space-y-6">
      {/* Project Metadata Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">CHI TIẾT KỊCH BẢN VIDEO</span>
            <h1 className="text-xl font-extrabold text-white mt-0.5">{project.title}</h1>
            <p className="text-xs text-slate-400 mt-1">Chủ đề gốc: "{project.topic}" • {project.target_duration}s • Khung dọc 9:16</p>
          </div>

          <button
            onClick={onRunRender}
            className="flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-slate-950 font-bold px-4 py-2 rounded-xl text-xs transition-all shadow-lg shadow-cyan-500/20 active:scale-95"
          >
            <Film className="w-4 h-4" />
            <span>Render Lại Video MP4</span>
          </button>
        </div>

        {/* SEO & Tags */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-800 text-xs">
          <div>
            <span className="font-semibold text-slate-400 block mb-1">Mô tả SEO:</span>
            <p className="text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800">
              {project.seo_description || 'Chưa có mô tả'}
            </p>
          </div>
          <div>
            <span className="font-semibold text-slate-400 block mb-1">Hashtags Xu Hướng:</span>
            <div className="flex flex-wrap gap-1.5 bg-slate-950 p-3 rounded-xl border border-slate-800">
              {project.hashtags && project.hashtags.length > 0 ? (
                project.hashtags.map((tag, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono text-[11px]">
                    {tag}
                  </span>
                ))
              ) : (
                <span className="text-slate-500 italic">Chưa có hashtag</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Scenes Breakdown */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-extrabold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Film className="w-4 h-4 text-emerald-400" />
            <span>Danh Sách Phân Cảnh ({scenes.length} Scenes)</span>
          </h2>
          <span className="text-xs text-slate-400">Bạn có thể chỉnh sửa lời thoại hoặc hiệu ứng camera trước khi render</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {scenes.map((scene) => {
            const currentData = { ...scene, ...(editingScenes[scene.id] || {}) };
            const hasChanges = !!editingScenes[scene.id];

            return (
              <div
                key={scene.id}
                className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 transition-all shadow-md space-y-4"
              >
                {/* Scene Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-lg bg-emerald-500/20 text-emerald-400 font-extrabold text-xs flex items-center justify-center border border-emerald-500/30">
                      {scene.scene_index + 1}
                    </span>
                    <span className="font-bold text-xs text-slate-200">
                      Cảnh {scene.scene_index + 1} • {currentData.estimated_duration}s
                    </span>
                  </div>

                  {hasChanges && (
                    <button
                      onClick={() => handleSaveScene(scene)}
                      disabled={savingSceneId === scene.id}
                      className="flex items-center gap-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs transition-all shadow-md"
                    >
                      <Save className="w-3.5 h-3.5" />
                      <span>{savingSceneId === scene.id ? 'Đang lưu...' : 'Lưu Thay Đổi'}</span>
                    </button>
                  )}
                </div>

                {/* Media Preview (If generated) */}
                <div className="grid grid-cols-2 gap-3">
                  {/* Image Preview */}
                  <div className="aspect-[9/16] bg-slate-950 border border-slate-800 rounded-xl overflow-hidden flex items-center justify-center relative group">
                    {scene.image_path ? (
                      <img
                        src={`/static/outputs/${project.id}/scenes/scene_${scene.scene_index.toString().padStart(2, '0')}.jpg?t=${Date.now()}`}
                        alt={`Scene ${scene.scene_index + 1}`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="text-center p-3">
                        <ImageIcon className="w-6 h-6 text-slate-600 mx-auto mb-1" />
                        <span className="text-[10px] text-slate-500">Chưa render ảnh</span>
                      </div>
                    )}
                  </div>

                  {/* Audio & Motion Controls */}
                  <div className="space-y-3 flex flex-col justify-between">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-400 mb-1 flex items-center gap-1">
                        <Move className="w-3 h-3 text-cyan-400" />
                        Hiệu Ứng Camera (Ken Burns)
                      </label>
                      <select
                        value={currentData.motion_effect}
                        onChange={(e) => handleFieldChange(scene.id, 'motion_effect', e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500"
                      >
                        <option value="zoom_in">Zoom In (Phóng to dần)</option>
                        <option value="zoom_out">Zoom Out (Thu nhỏ dần)</option>
                        <option value="pan_left">Pan Left (Quét sang trái)</option>
                        <option value="pan_right">Pan Right (Quét sang phải)</option>
                        <option value="shake">Dynamic Shake (Rung lắc kịch tính)</option>
                      </select>
                    </div>

                    {/* Audio Player if ready */}
                    {scene.audio_path && (
                      <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400 mb-1">
                          <Volume2 className="w-3.5 h-3.5" />
                          <span>Nghe Thử Thoại ({scene.actual_duration?.toFixed(1) || scene.estimated_duration}s)</span>
                        </div>
                        <audio
                          controls
                          className="w-full h-7 mt-1 scale-95 origin-left"
                          src={`/static/outputs/${project.id}/scenes/scene_${scene.scene_index.toString().padStart(2, '0')}.mp3`}
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Narration Textarea */}
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                    Lời Thoại Thuyết Minh (Narration)
                  </label>
                  <textarea
                    rows={2}
                    value={currentData.narration_text}
                    onChange={(e) => handleFieldChange(scene.id, 'narration_text', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500 rounded-xl p-2.5 text-xs text-slate-200 outline-none resize-none leading-relaxed"
                  />
                </div>

                {/* Visual Prompt Textarea */}
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                    Visual Prompt (ComfyUI / SDXL - Tiếng Anh)
                  </label>
                  <textarea
                    rows={2}
                    value={currentData.visual_prompt}
                    onChange={(e) => handleFieldChange(scene.id, 'visual_prompt', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl p-2.5 text-xs font-mono text-slate-300 outline-none resize-none leading-relaxed"
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

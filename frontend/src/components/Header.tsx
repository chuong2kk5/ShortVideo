import React, { useState } from 'react';
import { Sparkles, Cpu, HardDrive, Trash2, Plus, RefreshCw, ShoppingBag } from 'lucide-react';
import { SystemHealth } from '../types';

interface HeaderProps {
  health: SystemHealth | null;
  activeTab: 'studio' | 'library' | 'youtube';
  setActiveTab: (tab: 'studio' | 'library' | 'youtube') => void;
  onOpenCreateModal: () => void;
  onOpenProductReviewModal: () => void;
  onOpenAISettings: () => void;
  onRefreshHealth: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  activeTab,
  setActiveTab,
  onOpenCreateModal,
  onOpenProductReviewModal,
  onOpenAISettings,
  onRefreshHealth,
}) => {
  const [isCleaning, setIsCleaning] = useState(false);

  const handleFreeMemory = async () => {
    setIsCleaning(true);
    try {
      await fetch('/api/system/free-memory', { method: 'POST' });
      onRefreshHealth();
    } catch (err) {
      console.error('Failed to free memory', err);
    } finally {
      setIsCleaning(false);
    }
  };

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 via-teal-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Sparkles className="w-5 h-5 text-slate-950 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg tracking-tight text-white">AI SHORTS FACTORY</span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                PRO PIPELINE
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous Video Creation & Multi-Channel YouTube Manager</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-950/60 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('studio')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'studio'
                ? 'bg-slate-800 text-emerald-400 shadow-sm border border-slate-700'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Video Studio
          </button>
          <button
            onClick={() => setActiveTab('library')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'library'
                ? 'bg-slate-800 text-emerald-400 shadow-sm border border-slate-700'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Projects Library
          </button>
          <button
            onClick={() => setActiveTab('youtube')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'youtube'
                ? 'bg-slate-800 text-emerald-400 shadow-sm border border-slate-700'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            YouTube Hub & Schedules
          </button>
        </nav>

        {/* Hardware Status & Actions */}
        <div className="flex items-center gap-4">
          {health && (
            <div className="hidden lg:flex items-center gap-3 text-xs bg-slate-950/60 border border-slate-800 px-3 py-1.5 rounded-xl">
              {/* RAM Meter */}
              <div className="flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                <span className="text-slate-400">RAM:</span>
                <span className={`font-semibold ${health.ram.percent > 85 ? 'text-amber-400' : 'text-slate-200'}`}>
                  {health.ram.percent}%
                </span>
              </div>

              <div className="w-px h-3.5 bg-slate-800" />

              {/* VRAM Meter */}
              <div className="flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-slate-400">GPU:</span>
                <span className="font-semibold text-slate-200">
                  {health.vram.available ? `${Math.round(health.vram.used_mb)} MB` : 'Safe Mode'}
                </span>
              </div>

              <div className="w-px h-3.5 bg-slate-800" />

              {/* Free Memory Action */}
              <button
                onClick={handleFreeMemory}
                disabled={isCleaning}
                title="Purge VRAM & Force GC"
                className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-rose-400 transition-colors"
              >
                <Trash2 className={`w-3 h-3 ${isCleaning ? 'animate-spin' : ''}`} />
                <span>Purge</span>
              </button>
            </div>
          )}

          {/* AI Settings Button */}
          <button
            onClick={onOpenAISettings}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 shadow-sm transition-all active:scale-95"
            title="Cấu hình Ollama & Gemini API"
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span className="hidden sm:inline">Cấu Hình AI</span>
          </button>

          {/* Product Review Button */}
          <button
            onClick={onOpenProductReviewModal}
            className="flex items-center gap-1.5 bg-gradient-to-r from-rose-500 via-orange-500 to-amber-500 hover:from-rose-600 hover:to-amber-600 text-slate-950 font-extrabold px-3.5 py-2 rounded-xl text-xs transition-all shadow-lg shadow-rose-500/25 active:scale-95"
            title="Ghép video review sản phẩm với ảnh mẫu thật"
          >
            <ShoppingBag className="w-4 h-4 stroke-[2.5]" />
            <span className="hidden sm:inline">Review Sản Phẩm</span>
            <span className="sm:hidden">Review</span>
          </button>

          {/* Create Video Button */}
          <button
            onClick={onOpenCreateModal}
            className="flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-slate-950 font-bold px-4 py-2 rounded-xl text-xs transition-all shadow-lg shadow-emerald-500/25 active:scale-95"
          >
            <Plus className="w-4 h-4 stroke-[3]" />
            <span>Tạo Video Mới</span>
          </button>
        </div>
      </div>
    </header>
  );
};


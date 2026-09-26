import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { CreateVideoModal } from './components/CreateVideoModal';
import { ProductReviewModal } from './components/ProductReviewModal';
import { AISettingsModal } from './components/AISettingsModal';
import { PipelineTracker } from './components/PipelineTracker';
import { SceneEditor } from './components/SceneEditor';
import { YouTubeHub } from './components/YouTubeHub';
import { ProjectLibrary } from './components/ProjectLibrary';
import { FloatingMiniWindow } from './components/FloatingMiniWindow';
import { Project, PipelineJob, SystemHealth, YouTubeChannel, BrandKit, Scene } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'studio' | 'library' | 'youtube'>('studio');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [currentJob, setCurrentJob] = useState<PipelineJob | null>(null);
  const [channels, setChannels] = useState<YouTubeChannel[]>([]);
  const [brandKits, setBrandKits] = useState<BrandKit[]>([]);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isProductReviewModalOpen, setIsProductReviewModalOpen] = useState(false);
  const [isAISettingsOpen, setIsAISettingsOpen] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);

  // Fetch system health
  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/system/health');
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch (err) {
      console.error('Failed to fetch system health', err);
    }
  };

  // Fetch all projects
  const fetchProjects = async () => {
    try {
      const res = await fetch('/api/projects');
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
        if (data.length > 0 && !currentProject) {
          setCurrentProject(data[0]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch projects', err);
    }
  };

  // Fetch channels & brand kits
  const fetchYouTubeData = async () => {
    try {
      const [chRes, bkRes] = await Promise.all([
        fetch('/api/youtube/channels'),
        fetch('/api/youtube/brand-kits'),
      ]);
      if (chRes.ok) setChannels(await chRes.json());
      if (bkRes.ok) setBrandKits(await bkRes.json());
    } catch (err) {
      console.error('Failed to fetch YouTube data', err);
    }
  };

  // Initial load & health polling
  useEffect(() => {
    fetchHealth();
    fetchProjects();
    fetchYouTubeData();

    const interval = setInterval(fetchHealth, 4000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket connection for active job
  useEffect(() => {
    if (!currentJob || currentJob.status === 'completed' || currentJob.status === 'failed') {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/api/pipeline/ws/jobs/${currentJob.id}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'stage_progress') {
          const log = msg.payload;
          setCurrentJob((prev) => {
            if (!prev) return null;
            const updatedLogs = [...(prev.logs || []), log];
            return {
              ...prev,
              current_stage: log.stage,
              progress: log.progress,
              logs: updatedLogs,
              status: log.stage === 'completed' ? 'completed' : log.stage === 'error' ? 'failed' : 'running',
            };
          });

          // Refresh project when completed
          if (log.stage === 'completed') {
            fetchProjects();
            if (currentProject) {
              fetch(`/api/projects/${currentProject.id}`)
                .then((r) => r.json())
                .then((p) => setCurrentProject(p));
            }
          }
        }
      } catch (e) {
        console.error('WebSocket parse error', e);
      }
    };

    return () => {
      ws.close();
    };
  }, [currentJob?.id]);

  // Start video creation workflow
  const handleStartGeneration = async (data: {
    topic: string;
    language: string;
    duration: number;
    voice: string;
    brandKitId?: string;
    artStyle?: string;
    contentStyle?: string;
  }) => {
    // 1. Create Project
    const projRes = await fetch('/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: data.topic,
        title: data.topic.slice(0, 50),
        language: data.language,
        target_duration: data.duration,
        brand_kit_id: data.brandKitId,
        art_style: data.artStyle || 'auto',
        content_style: data.contentStyle || 'auto',
      }),
    });
    const newProject = await projRes.json();
    setCurrentProject(newProject);
    fetchProjects();

    // 2. Trigger Pipeline Job
    const runRes = await fetch(`/api/pipeline/${newProject.id}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_type: 'full_pipeline',
      }),
    });
    const job = await runRes.json();
    setCurrentJob(job);
    setActiveTab('studio');
  };

  // Run render again for current project
  const handleRunRender = async () => {
    if (!currentProject) return;
    const runRes = await fetch(`/api/pipeline/${currentProject.id}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_type: 'full_pipeline',
      }),
    });
    const job = await runRes.json();
    setCurrentJob(job);
  };

  // Update scene
  const handleUpdateScene = async (sceneId: string, data: Partial<Scene>) => {
    if (!currentProject) return;
    await fetch(`/api/projects/${currentProject.id}/scenes/${sceneId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    // Refresh project
    const res = await fetch(`/api/projects/${currentProject.id}`);
    if (res.ok) {
      setCurrentProject(await res.json());
      fetchProjects();
    }
  };

  // Handle product review created
  const handleProductReviewCreated = async (projectId: string, jobId: string) => {
    // 1. Fetch updated project
    try {
      const res = await fetch(`/api/projects/${projectId}`);
      if (res.ok) {
        const proj = await res.json();
        setCurrentProject(proj);
      }
    } catch (e) {
      console.error('Failed to fetch review project', e);
    }

    // 2. Set current job to trigger real-time WebSocket tracker
    setCurrentJob({
      id: jobId,
      project_id: projectId,
      job_type: 'full_pipeline',
      status: 'running',
      current_stage: 'queued',
      progress: 0.0,
      logs: [],
      created_at: new Date().toISOString(),
    });

    // 3. Switch to studio & refresh projects list
    setActiveTab('studio');
    fetchProjects();
  };

  // Delete project
  const handleDeleteProject = async (projectId: string) => {
    await fetch(`/api/projects/${projectId}`, { method: 'DELETE' });
    if (currentProject?.id === projectId) {
      setCurrentProject(null);
    }
    fetchProjects();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Header
        health={health}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenCreateModal={() => setIsCreateModalOpen(true)}
        onOpenProductReviewModal={() => setIsProductReviewModalOpen(true)}
        onOpenAISettings={() => setIsAISettingsOpen(true)}
        onRefreshHealth={fetchHealth}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {activeTab === 'studio' && (
          <div className="space-y-8">
            <PipelineTracker
              job={currentJob}
              project={currentProject}
              onRefreshProject={fetchProjects}
            />

            {currentProject && (
              <SceneEditor
                project={currentProject}
                onUpdateScene={handleUpdateScene}
                onRunRender={handleRunRender}
              />
            )}
          </div>
        )}

        {activeTab === 'library' && (
          <ProjectLibrary
            projects={projects}
            onSelectProject={(p) => {
              setCurrentProject(p);
              setActiveTab('studio');
            }}
            onDeleteProject={handleDeleteProject}
          />
        )}

        {activeTab === 'youtube' && (
          <YouTubeHub
            channels={channels}
            brandKits={brandKits}
            completedProjects={projects}
            onRefreshChannels={fetchYouTubeData}
            onRefreshBrandKits={fetchYouTubeData}
          />
        )}
      </main>

      <CreateVideoModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        brandKits={brandKits}
        onStartGeneration={handleStartGeneration}
      />

      <ProductReviewModal
        isOpen={isProductReviewModalOpen}
        onClose={() => setIsProductReviewModalOpen(false)}
        onReviewCreated={handleProductReviewCreated}
      />

      <AISettingsModal
        isOpen={isAISettingsOpen}
        onClose={() => setIsAISettingsOpen(false)}
        onConfigSaved={fetchHealth}
      />

      <FloatingMiniWindow
        job={currentJob}
        project={currentProject}
        onOpenStudio={() => setActiveTab('studio')}
      />
    </div>
  );
};

export default App;


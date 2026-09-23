export interface Scene {
  id: string;
  project_id: string;
  scene_index: number;
  narration_text: string;
  visual_prompt: string;
  motion_effect: string;
  sound_effect_cue?: string;
  estimated_duration: number;
  actual_duration?: number;
  image_path?: string;
  audio_path?: string;
  subtitle_cues?: any[];
  status: string;
  created_at: string;
}

export interface Project {
  id: string;
  title: string;
  topic: string;
  target_duration: number;
  aspect_ratio: string;
  language: string;
  status: string;
  brand_kit_id?: string;
  art_style?: string;
  content_style?: string;
  seo_title?: string;
  seo_description?: string;
  hashtags?: string[];
  final_video_path?: string;
  created_at: string;
  updated_at: string;
  scenes?: Scene[];
}

export interface PipelineLog {
  timestamp: string;
  stage: string;
  message: string;
  level: string;
  progress: number;
  extra_data?: {
    scene_index?: number;
    total_scenes?: number;
    narration?: string;
    visual_prompt?: string;
    visual_keywords?: string;
    media_url?: string;
    media_type?: 'video' | 'image';
    status?: string;
    duration?: number;
    voice?: string;
    final_video_url?: string;
    resolution?: string;
    [key: string]: any;
  };
}

export interface PipelineJob {
  id: string;
  project_id: string;
  job_type: string;
  status: string;
  current_stage: string;
  progress: number;
  error_message?: string;
  logs: PipelineLog[];
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface SystemHealth {
  ram: {
    total_mb: number;
    available_mb: number;
    used_mb: number;
    percent: number;
    status: string;
  };
  vram: {
    available: boolean;
    gpu_name: string;
    total_mb: number;
    used_mb: number;
    free_mb: number;
    percent: number;
    status: string;
  };
  active_stage: string;
  enforce_sequential: boolean;
}

export interface YouTubeChannel {
  id: string;
  channel_id: string;
  title: string;
  custom_url?: string;
  thumbnail_url?: string;
  is_active: boolean;
  subscriber_count: number;
  view_count: number;
  video_count: number;
  last_synced_at?: string;
  created_at: string;
}

export interface BrandKit {
  id: string;
  channel_id?: string;
  name: string;
  default_tts_voice: string;
  default_tts_rate: string;
  subtitle_font: string;
  subtitle_color: string;
  subtitle_outline_color: string;
  subtitle_font_size: number;
  bgm_mood: string;
  created_at: string;
}

export interface AIStatus {
  ollama: {
    online: boolean;
    url: string;
    models: string[];
    active_model: string;
  };
  gemini: {
    configured: boolean;
    masked_key: string;
    model: string;
  };
  comfyui: {
    online: boolean;
    url: string;
  };
  llm_provider: string;
}

export interface VoiceProfile {
  id: string;
  name: string;
  gender: string;
  locale: string;
  base_voice: string;
  rate: string;
  pitch: string;
  sample_text: string;
  tags: string[];
  recommended: boolean;
}

export const DEFAULT_VOICE_CATALOG: VoiceProfile[] = [
  // --- TIẾNG VIỆT ---
  {
    id: "vi-VN-NamMinhNeural",
    name: "Nam Minh - Hào hùng, Năng động (Shorts triệu view ⭐)",
    gender: "Male",
    locale: "vi-VN",
    base_voice: "vi-VN-NamMinhNeural",
    rate: "+22%",
    pitch: "+0Hz",
    sample_text: "Chào mừng bạn đến với kênh! Hôm nay chúng ta sẽ khám phá những bí ẩn kỳ thú nhất.",
    tags: ["Phổ biến nhất", "Shorts/TikTok", "Hào hùng"],
    recommended: true,
  },
  {
    id: "vi-VN-NamMinhNeural_deep",
    name: "Nam Minh - Trầm ấm, Điện ảnh (Tài liệu, Khám phá)",
    gender: "Male",
    locale: "vi-VN",
    base_voice: "vi-VN-NamMinhNeural",
    rate: "+10%",
    pitch: "-5Hz",
    sample_text: "Sâu thẳm trong bóng tối của vũ trụ, những điều kỳ diệu vẫn đang chờ chúng ta giải mã.",
    tags: ["Điện ảnh", "Trầm ấm", "Tài liệu"],
    recommended: false,
  },
  {
    id: "vi-VN-NamMinhNeural_news",
    name: "Nam Minh - Bản tin, Phóng sự (Tin tức, Fact giật gân)",
    gender: "Male",
    locale: "vi-VN",
    base_voice: "vi-VN-NamMinhNeural",
    rate: "+18%",
    pitch: "-2Hz",
    sample_text: "Bản tin đặc biệt hôm nay sẽ mang đến cho bạn những sự thật chấn động chưa từng được công bố.",
    tags: ["Tin tức", "Dứt khoát", "Sự thật"],
    recommended: false,
  },
  {
    id: "vi-VN-HoaiMyNeural",
    name: "Hoài My - Truyền cảm, Tâm sự (Kể chuyện, Triết lý)",
    gender: "Female",
    locale: "vi-VN",
    base_voice: "vi-VN-HoaiMyNeural",
    rate: "+15%",
    pitch: "-2Hz",
    sample_text: "Cuộc sống luôn có những ngã rẽ bất ngờ, và sự chân thành luôn là câu trả lời ý nghĩa nhất.",
    tags: ["Tâm sự", "Truyền cảm", "Kể chuyện"],
    recommended: true,
  },
  {
    id: "vi-VN-HoaiMyNeural_cheerful",
    name: "Hoài My - Vui tươi, Tươi trẻ (Review sản phẩm, Mẹo vặt)",
    gender: "Female",
    locale: "vi-VN",
    base_voice: "vi-VN-HoaiMyNeural",
    rate: "+24%",
    pitch: "+6Hz",
    sample_text: "Hế lô mọi người! Hôm nay mình sẽ chỉ cho các bạn một mẹo cực kỳ tiện lợi mà ít ai biết nhé!",
    tags: ["Review", "Vui tươi", "Trẻ trung"],
    recommended: false,
  },
  {
    id: "vi-VN-HoaiMyNeural_mystery",
    name: "Hoài My - Bí ẩn, Ly kỳ (Vụ án, Kinh dị, Creepypasta)",
    gender: "Female",
    locale: "vi-VN",
    base_voice: "vi-VN-HoaiMyNeural",
    rate: "+8%",
    pitch: "-6Hz",
    sample_text: "Vào một đêm mùa đông giá buốt, ngôi nhà cổ ở cuối làng bỗng phát ra những tiếng động rợn người.",
    tags: ["Bí ẩn", "Hồi hộp", "Kinh dị"],
    recommended: false,
  },
  {
    id: "gtts_vi",
    name: "Chị Google Dịch (Meme TikTok Huyền Thoại - Hài hước)",
    gender: "Female",
    locale: "vi-VN",
    base_voice: "gtts_vi",
    rate: "+22%",
    pitch: "+0Hz",
    sample_text: "Chào mừng bạn đến với kênh của tôi, nhớ nhấn theo dõi nếu không muốn bị phạt nhé quý vị.",
    tags: ["Meme", "Hài hước", "TikTok Icon"],
    recommended: false,
  },
  // --- ENGLISH ---
  {
    id: "en-US-ChristopherNeural",
    name: "Christopher - Viral Storyteller (Top #1 US Shorts ⭐)",
    gender: "Male",
    locale: "en-US",
    base_voice: "en-US-ChristopherNeural",
    rate: "+15%",
    pitch: "+0Hz",
    sample_text: "Did you know that in the deepest trench of the ocean, prehistoric creatures still survive today?",
    tags: ["Storyteller", "Viral", "English"],
    recommended: true,
  },
  {
    id: "en-US-JennyNeural",
    name: "Jenny - Cheerful & Engaging (Lifestyle, Tips)",
    gender: "Female",
    locale: "en-US",
    base_voice: "en-US-JennyNeural",
    rate: "+15%",
    pitch: "+0Hz",
    sample_text: "Hey everyone! Here are three amazing life hacks that will completely transform your daily routine.",
    tags: ["Lifestyle", "Friendly", "Engaging"],
    recommended: false,
  },
  {
    id: "en-US-GuyNeural",
    name: "Guy - High Energy & Confident (Tech, Sports)",
    gender: "Male",
    locale: "en-US",
    base_voice: "en-US-GuyNeural",
    rate: "+20%",
    pitch: "+0Hz",
    sample_text: "The wait is finally over! This breakthrough technology is about to disrupt the entire industry.",
    tags: ["Tech", "High Energy", "Commercial"],
    recommended: false,
  },
  {
    id: "en-US-AriaNeural",
    name: "Aria - Dramatic & Expressive (Movie Recap, Drama)",
    gender: "Female",
    locale: "en-US",
    base_voice: "en-US-AriaNeural",
    rate: "+15%",
    pitch: "+0Hz",
    sample_text: "She never imagined that one single decision would alter the fate of an entire kingdom forever.",
    tags: ["Dramatic", "Movie Recap"],
    recommended: false,
  },
  {
    id: "en-US-RogerNeural",
    name: "Roger - Deep & Mysterious (Horror, Thriller)",
    gender: "Male",
    locale: "en-US",
    base_voice: "en-US-RogerNeural",
    rate: "+10%",
    pitch: "-4Hz",
    sample_text: "Some secrets are meant to stay buried. What they uncovered that night was beyond human comprehension.",
    tags: ["Horror", "Deep", "Thriller"],
    recommended: false,
  },
  {
    id: "gtts_en",
    name: "Google English (Classic TTS Meme)",
    gender: "Female",
    locale: "en-US",
    base_voice: "gtts_en",
    rate: "+22%",
    pitch: "+0Hz",
    sample_text: "Welcome to my video. Hit that subscribe button right now for more daily shorts content.",
    tags: ["Meme", "Fast", "Google"],
    recommended: false,
  },
];



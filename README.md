# 🎬 ShortVideo - AI Shorts & TikTok Auto-Production Studio

Hệ thống tự động hóa sản xuất video ngắn (**TikTok, YouTube Shorts, Facebook Reels**) chuyên nghiệp từ A-Z với trí tuệ nhân tạo (AI). Ứng dụng được thiết kế tối ưu hóa đặc biệt cho máy tính phổ thông (**16GB RAM / 4GB-6GB VRAM**) bằng cơ chế quản lý bộ nhớ tuần tự (**Sequential Pipeline & Hardware Memory Guard**).

---

## 🌟 Điểm Nổi Bật & Tính Năng Cốt Lõi

### 1. 🧠 Kịch Bản 3 Hồi & 4 Mô Thức Nội Dung Chuyên Biệt (Script Archetypes & Natural Cadence)
- **Google Gemini Flash & Ollama Local AI**: Tự động luân phiên giữa Gemini Flash (siêu tốc 1-2s) và mô hình AI chạy cục bộ Ollama (offline) khi mất mạng hoặc nghẽn API.
- **4 Mô Thức Nội Dung Chuyên Biệt (Content Archetypes)**:
  - 🎭 **Storytelling & Drama**: Kể chuyện kịch tính, phát triển bối cảnh, cao trào và bài học đắt giá.
  - 📊 **Top Facts / Countdown**: Tiết lộ dồn dập các sự thật ít ai biết hoặc bảng xếp hạng kinh ngạc.
  - 🕵️ **Mystery & Curiosity**: Kích thích tò mò cao độ, xây dựng không khí bí ẩn và lần theo từng manh mối.
  - 💡 **Educational & Explainer**: Giải thích bản chất hiện tượng khoa học, đời sống với ví dụ trực quan.
- **Văn Nói Khẩu Ngữ Đời Thường & Ngắt Nhịp Tự Nhiên (Spoken Cadence)**:
  - Loại bỏ hoàn toàn các câu mở đầu sáo rỗng bị lặp đi lặp lại như: *"99% mọi người đều hiểu sai về..."*, *"Bí mật đáng sợ nhất mà họ không muốn bạn biết..."*.
  - Câu từ ngắn gọn 5-8 từ/vế, dấu câu ngắt nghỉ có chủ đích giúp giọng đọc AI nhấn nhá truyền cảm.
  - Chống trùng lặp câu Hook ở Cảnh 0 (Hook Deduplication sạch).
- **Cấu trúc giữ chân người xem (Audience Retention Formula)**:
  - **Mở bài (Hook - Cảnh 0)**: Câu thoại giật gân ngắt nhịp lướt màn hình (Pattern Interrupt), tự động phát âm thanh `dramatic_boom` và hiển thị **Banner Tiêu Đề giật gân** ở đầu video.
  - **Thân bài (Value & Tension - Cảnh 1..N-2)**: Tiết lộ dồn dập, chuyển đổi góc máy liên tục mỗi **2.7 - 3.5 giây** giúp video luôn sôi động, cuốn hút.
  - **Kết bài (Outro & CTA - Cảnh N-1)**: Đúc kết giá trị và kêu gọi bình luận/theo dõi kênh, tự động phát âm thanh `whoosh` và hiển thị **Thẻ Kêu Gọi Hành Động (CTA Badge)**.
- **Cam kết thời lượng chuẩn (Pacing Guarantee)**: Đảm bảo độ dài video chính xác theo các mốc lựa chọn (**15s, 30s, 45s, 60s**), không bao giờ bị hụt thời lượng.

### 2. 🎨 Phong Cách Nghệ Thuật Đồng Bộ (Art Style Consistency & 4K/8K Engine)
- **5 Phong Cách Nghệ Thuật Thẩm Mỹ (Cohesive Art Styles)**:
  - 🎬 **Cinematic 8K**: Ảnh chụp máy phim 35mm Panavision, ánh sáng thể tích, chiều sâu trường ảnh điện ảnh.
  - 🧸 **3D Animation Pixar**: Hoạt hình 3D phong cách Disney/Pixar, nhân vật biểu cảm, ánh sáng Octane ấm áp.
  - 🎨 **Anime Ghibli**: Tranh vẽ tay phong cảnh Studio Ghibli / Makoto Shinkai thơ mộng, màu sắc hoài niệm.
  - 🌑 **Dark Mystery & Noir**: Ánh sáng tương phản Chiaroscuro noir, bóng tối rùng rợn, sương mù kỳ bí.
  - 🏛️ **Historic Oil Painting**: Tranh sơn dầu phục hưng cổ điển Rembrandt, màu sắc bảo tàng vĩ đại.
  - ✨ **AI Auto Match**: Tự động phân tích từ khóa chủ đề (topic) để chọn phong cách nghệ thuật đồng bộ xuyên suốt từ Cảnh 0 đến Cảnh cuối.
- **Neo Chặt Chủ Đề (Strict Topic Anchoring)**: Tất cả câu truy vấn tìm kiếm footage và câu lệnh vẽ ảnh AI đều được liên kết chặt chẽ với chủ đề video chính (Topic Anchor). Tuyệt đối loại bỏ hiện tượng lấy hình ảnh lạc đề hoặc các từ khóa chung chung vô nghĩa.
- **Chống Trùng Lặp Hình Ảnh/Video (Intelligent Asset Deduplication)**: Hệ thống ghi nhớ các ID/URL video và hình ảnh đã sử dụng trong các phân cảnh trước. Các cảnh sau tự động bỏ qua và lấy nội dung mới, đảm bảo mỗi phân cảnh đều sở hữu hình ảnh/video độc nhất, không lặp lại ảnh cũ.
- **Mô hình AI Flux.1 Schnell (Miễn phí 100%, Không Cần Key)**: Tự động vẽ hình ảnh nghệ thuật 9:16 dọc Full HD (`1080x1920`) siêu sắc nét chuẩn Midjourney/National Geographic theo sát từng câu thoại của kịch bản với seed ngẫu nhiên độc bản cho từng cảnh.
- **Tích hợp Pexels API Video & Photo 4K**: Khi cấu hình `PEXELS_API_KEY` trong file `.env`, hệ thống tự động ưu tiên lấy các video chuyển động 4K flycam hoặc ảnh chụp người thật độ phân giải cao của các nhiếp ảnh gia hàng đầu.
- **Bộ lọc chất lượng thông minh (Quality Gatekeeper)**: Tự động loại bỏ các video tư liệu cũ, mờ, độ phân giải thấp từ internet, ưu tiên tối đa ảnh/video sắc nét 1080x1920.
- **Công nghệ Nền mờ quang học (Ambient Blurred Wings)**: Khung hình ngang 16:9 được đặt sắc nét ở chính giữa trên nền mờ quang học 9:16 Full HD (`1080x1920`), loại bỏ hoàn toàn tình trạng ảnh bị phóng to quá mức hoặc bị cắt xén chi tiết.

### 3. 🎬 Chuyển Động Camera Punch, Phụ Đề CapCut Bounce & Màu Sắc Điện Ảnh
- **Dynamic Camera Punch (Easing Curve Easing-Out)**:
  - Ứng dụng đường cong phi tuyến tính `1 - exp(-3.5 * p)` trong bộ lọc FFmpeg `zoompan`, tạo cú giật máy quay dứt khoát 16% ở đầu cảnh rồi giữ khung hình êm mượt.
- **Phụ Đề Karaoke Động Nảy Chữ (CapCut Word Bounce)**:
  - Hiệu ứng biến dạng tỷ lệ `\fscx116\fscy116` phóng to 116% khi từ khóa được xướng lên, nảy êm về 100% `\fscx100\fscy100`.
  - Icon tia sét `⚡` ở cảnh Hook đầu tiên lập tức ngắt nhịp lướt video của người xem.
  - Phụ đề đổi màu **Vàng Neon** cho từ đang nói, nền trắng viền đen dày nổi bật.
- **Cinematic Color Grading & Vignette (Tối Góc Điện Ảnh)**:
  - Bộ lọc hòa sắc `eq=contrast=1.05:saturation=1.10:brightness=0.01` tăng nhẹ tương phản và độ no màu.
  - Bộ lọc `vignette=PI/4` tạo độ sâu trường ảnh, tập trung ánh nhìn vào trung tâm màn hình.
- **Tự động nhận diện tâm trạng & chủ đề (Mood-Based BGM Resolver)**:
  - *Chủ đề Thể thao, Siêu xe, Công nghệ, Khởi nghiệp, Tiền bạc*: **Modern Energetic Beat** (120 BPM, Bassline sôi động).
  - *Chủ đề Thiên nhiên, Động vật, Du lịch, Chữa lành*: **Lush Calm Ambient** (Giai điệu âm thanh êm dịu, acoustic sâu lắng).
  - *Chủ đề Kỳ bí, Đại dương, Vũ trụ, Giật gân*: **Cinematic Suspense** (Hồi hộp, kịch tính, heartbeat sub-bass).
- **Tắt Âm Thanh Chuyển Cảnh (Zero Transition Noise)**: Loại bỏ hoàn toàn tiếng động chuyển cảnh gây xao nhãng, mang lại trải nghiệm xem mượt mà, chuyên nghiệp.
- **Âm Lượng Nhạc Nền Rõ Ràng & Sống Động**: Tinh chỉnh mức âm lượng chuẩn (`volume=0.35` / `-14.5dB`) kết hợp Audio Ducking tự động, giúp nhạc nền vang lên hào hùng, cuốn hút mà không lấn át giọng thuyết minh.
- **Microsoft Edge-TTS Studio Voices**: Giọng đọc tự nhiên, truyền cảm (`vi-VN-NamMinhNeural`, `vi-VN-HoaiMyNeural`,...), tăng tốc độ đọc `+18% - +22%` tạo nhịp dồn dập.

### 4. 🪟 Cửa Sổ Nhỏ Giám Sát Trực Tiếp (AI Studio Live Process)
- Bảng tiến trình 5 bước sản xuất trực quan: `Kịch Bản` ➡️ `Tìm Footage Web` ➡️ `Thu Âm TTS` ➡️ `Dựng & Kỹ Xảo` ➡️ `Rà Soát`.
- **Xem trực tiếp chi tiết công việc thực tế của AI**:
  - Soi kịch bản, câu Hook và lời kêu gọi hành động CTA.
  - Xem câu lệnh Prompt và hashtag từ khóa AI đang gửi lên internet tìm kiếm.
  - Xem trước ngay hình ảnh/clip thực tế vừa tải về.
  - Thanh sóng âm (Audio Waveform) nhảy múa theo nhịp điệu giọng đọc.
  - Dải phim (Filmstrip) cho phép xem lại toàn bộ phân cảnh.

### 5. 🛡️ Bảo Vệ Phần Cứng (Hardware Memory Guard)
- Giám sát RAM hệ thống và VRAM GPU NVIDIA (`nvidia-smi`) thời gian thực.
- Khóa tiến trình tuần tự, kích hoạt Garbage Collection giải phóng bộ nhớ triệt để sau mỗi công đoạn.

---

## 🏗️ Cấu Trúc Thư Mục (Project Structure)

```
ShortVideo/
├── backend/
│   ├── app/
│   │   ├── api/                    # FastAPI Routes: Projects, Pipeline, System, YouTube
│   │   ├── core/                   # Database (Async SQLite), Memory Guard, Event Broadcaster
│   │   ├── models/                 # SQLAlchemy DB Models & Pydantic v2 Schemas
│   │   ├── orchestrator/           # Pipeline Runner, Script Generator, LLM Client, Prompts
│   │   └── services/               # FFmpeg Editor, Edge-TTS Provider, Web Image/ComfyUI
│   ├── data/                       # Thư mục database và output video thành phẩm
│   ├── tests/                      # Bộ kiểm thử tự động toàn diện
│   ├── requirements.txt            # Thư viện Python phụ thuộc
│   ├── .env.example                # File mẫu cấu hình biến môi trường
│   └── run_backend.py              # Script khởi chạy Backend
├── frontend/
│   ├── src/
│   │   ├── components/             # UI Components (FloatingMiniWindow, VideoPlayer, etc.)
│   │   ├── pages/                  # CreateVideoPage, Dashboard, Settings, etc.
│   │   └── services/               # API & WebSocket Client
│   ├── package.json                # Dependencies Frontend
│   └── vite.config.ts              # Cấu hình Vite & Proxy
├── assets/                         # Thư viện nhạc nền (BGM) & hiệu ứng âm thanh (SFX)
├── .gitignore                      # Bảo vệ thông tin nhạy cảm và file dung lượng lớn
└── README.md                       # Tài liệu hướng dẫn dự án
```

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Yêu Cầu Hệ Thống
- **Hệ điều hành**: Windows 10/11 (khuyến nghị)
- **Phần cứng tối thiểu**: 8GB RAM (khuyến nghị 16GB RAM), GPU NVIDIA 4GB+ VRAM (tùy chọn)
- **Phần mềm**:
  - Python 3.10+
  - Node.js 18+ & npm
  - FFmpeg (đã thêm vào biến môi trường PATH hệ thống)

### 2. Cài Đặt Backend
```bash
# Di chuyển vào thư mục backend
cd backend

# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# Tạo file cấu hình từ file mẫu
copy .env.example .env
```
> *Lưu ý*: Mở file `backend/.env` để điền `GEMINI_API_KEY` (hoặc cấu hình Ollama nếu chạy local).

### 3. Cài Đặt Frontend
```bash
# Di chuyển vào thư mục frontend
cd ../frontend

# Cài đặt các gói npm
npm install
```

### 4. Khởi Chạy Ứng Dụng

#### Cách 1: Chạy bằng file Batch tiện lợi (Khuyến nghị trên Windows)
Chỉ cần nhấp đúp chuột vào file:
- `run.bat` hoặc `start.bat` tại thư mục gốc của dự án.

#### Cách 2: Khởi chạy thủ công bằng Terminal

**Terminal 1 (Backend):**
```bash
cd backend
python run_backend.py
```
- API Docs (Swagger): `http://127.0.0.1:8000/docs`
- Backend API: `http://127.0.0.1:8000`

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```
- Truy cập giao diện ứng dụng tại: `http://localhost:5173`

---

## 🧪 Kiểm Thử Tự Động (Automated Testing)

Dự án tích hợp sẵn các bộ kiểm thử tự động để kiểm tra chất lượng:
```bash
# Kiểm tra kịch bản mở bài (Hook), kết bài (Outro CTA) và tràn viền 9:16
python backend/tests/test_intro_outro_pipeline.py

# Kiểm tra độ chuẩn xác của thời lượng video (30s)
python backend/tests/test_duration_30s.py

# Kiểm tra tìm kiếm ảnh/video trên internet và hiệu ứng Ambient Blurred Wings
python backend/tests/test_web_visuals_and_framing.py

# Kiểm tra neo chủ đề (Topic Anchoring) & chống trùng lặp hình ảnh (Deduplication)
python backend/tests/test_topic_and_dedup.py

# Kiểm tra nâng cấp toàn diện (BGM, Prompt viral, Flux.1 AI)
python backend/tests/test_upgrades_verification.py

# Kiểm tra toàn diện luồng sản xuất video từ A-Z
python backend/tests/test_nature_pipeline.py
```

---

## 📄 Bản Quyền & Giấy Phép (License)
Dự án được phát triển phục vụ mục đích tự động hóa sản xuất nội dung video ngắn. Mọi đóng góp và báo lỗi đều được hoan nghênh!

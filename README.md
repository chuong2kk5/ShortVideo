# 🎬 ShortVideo - AI Shorts & TikTok Auto-Production Studio

Hệ thống tự động hóa sản xuất video ngắn (**TikTok, YouTube Shorts, Facebook Reels**) chuyên nghiệp từ A-Z với trí tuệ nhân tạo (AI). Ứng dụng được thiết kế tối ưu hóa đặc biệt cho máy tính phổ thông (**16GB RAM / 4GB-6GB VRAM**) bằng cơ chế quản lý bộ nhớ tuần tự (**Sequential Pipeline & Hardware Memory Guard**).

---

## 🌟 Điểm Nổi Bật & Tính Năng Cốt Lõi

### 1. 🧠 Kịch Bản 3 Hồi Chuẩn Shorts Viral (3-Act Retention Architecture)
- **Google Gemini Flash & Ollama Local AI**: Tự động luân phiên giữa Gemini Flash (siêu tốc 1-2s) và mô hình AI chạy cục bộ Ollama (offline) khi mất mạng hoặc nghẽn API.
- **Cấu trúc giữ chân người xem (Audience Retention Formula)**:
  - **Mở bài (Hook - Cảnh 0)**: Câu thoại giật gân ngắt nhịp lướt màn hình (Pattern Interrupt), tự động phát âm thanh `dramatic_boom` và hiển thị **Banner Tiêu Đề giật gân** ở đầu video.
  - **Thân bài (Value & Tension - Cảnh 1..N-2)**: Tiết lộ dồn dập, chuyển đổi góc máy liên tục mỗi **2.7 - 3.5 giây** giúp video luôn sôi động, cuốn hút.
  - **Kết bài (Outro & CTA - Cảnh N-1)**: Đúc kết giá trị và kêu gọi bình luận/theo dõi kênh, tự động phát âm thanh `whoosh` và hiển thị **Thẻ Kêu Gọi Hành Động (CTA Badge)**.
- **Cam kết thời lượng chuẩn (Pacing Guarantee)**: Đảm bảo độ dài video chính xác theo các mốc lựa chọn (**15s, 30s, 45s, 60s**), không bao giờ bị hụt thời lượng.

### 2. 🌐 Tìm Kiếm Footage Thực Tế Trên Internet (Google & Web Image Index)
- Tự động phân tích từ khóa của từng phân cảnh để tìm kiếm ảnh 4K/HD và video chuyển động thực tế từ internet.
- **Công nghệ Nền mờ quang học (Ambient Blurred Wings)**: Khung hình ngang 16:9 được đặt sắc nét ở chính giữa trên nền mờ quang học 9:16 Full HD (`1080x1920`), loại bỏ hoàn toàn tình trạng ảnh bị phóng to quá mức hoặc bị cắt xén chi tiết.
- **Chuyển động điện ảnh nhẹ nhàng (Subtle Breathing Motion)**: Chuyển động máy quay êm dịu (chỉ 3.5% - 4%) tạo chiều sâu thị giác chuẩn điện ảnh.

### 3. 🎤 Giọng Đọc Studio & Phụ Đề Karaoke Động (CapCut Style)
- **Microsoft Edge-TTS Studio Voices**: Giọng đọc tự nhiên, truyền cảm (`vi-VN-NamMinhNeural`, `vi-VN-HoaiMyNeural`,...).
- **Phụ đề Karaoke Highlight từng từ**: Từ ngữ đang đọc được đổi màu **Vàng Neon**, các từ còn lại màu trắng với viền đen dày, font chữ `Impact` nổi bật ở 1/3 dưới khung hình.
- **Hòa âm tự động (Audio Ducking & SFX)**: Nhạc nền BGM tự động giảm âm lượng khi có giọng nói thuyết minh, tích hợp hiệu ứng âm thanh SFX và kết thúc mờ dần (Fade-to-black & Audio fade-out) êm ái.

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

# Kiểm tra toàn diện luồng sản xuất video từ A-Z
python backend/tests/test_nature_pipeline.py
```

---

## 📄 Bản Quyền & Giấy Phép (License)
Dự án được phát triển phục vụ mục đích tự động hóa sản xuất nội dung video ngắn. Mọi đóng góp và báo lỗi đều được hoan nghênh!

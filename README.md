# FinanceBuddy 🤖💰

**AI-powered financial document management and analysis platform** that converts complex financial reports into department-specific insights with intelligent access control, semantic search, and automated OCR.

## 🎯 The Problem
Finance reports are written in finance language for finance people. Other departments struggle to extract what matters to THEM. Additionally, managing sensitive financial documents requires proper access control and efficient retrieval systems.

## 💡 The Solution
FinanceBuddy uses AI to:
- **Translate** financial documents into department-tailored insights
- **Secure** documents with role-based access control (4 permission levels)
- **Search** semantically using RAG (Retrieval Augmented Generation)
- **Process** PDFs automatically with OCR for scanned documents
- **Summarize** documents intelligently while preserving key metrics
- **Analyze** with natural language Q&A capabilities

### Department-Specific Insights
- **Engineering:** Infrastructure costs, tool licenses, R&D spending
- **Sales:** Commission trends, CAC, territory performance  
- **Marketing:** Campaign ROI, channel effectiveness
- **HR:** Payroll analytics, benefits utilization
- **Operations:** Vendor spending, supply chain costs
- **Executive:** Strategic KPIs, cash flow forecasts

---

## ✅ Implemented Features

### 🔐 Authentication System
- **Cookie-Based Sessions**: Secure httponly cookies with 8-hour expiry
- **Login/Logout Flow**: Complete authentication with redirect protection
- **JSON User Storage**: Persistent user database at `backend/data/users.json`
- **Protected Routes**: Unauthenticated users redirected to `/login`
- **Auto-Classification**: Access levels automatically assigned based on user role

#### Demo User Accounts (All passwords: `1234`)
| Email | Role | Auto-Classification | Access Level |
|-------|------|---------------------|-------------|
| admin@financebuddy.local | Admin | admin_only | Full access to all documents |
| management@financebuddy.local | Management | management_only | Management & public docs |
| finance@financebuddy.local | Finance | finance_only | Finance & public docs |
| employee@financebuddy.local | Employee | public_company | Public docs only |

### 🔐 Access Control System
- **4-Level Classification**:
  - `public_company` - All employees
  - `finance_only` - Finance department only
  - `management_only` - Management and above
  - `admin_only` - Admin access only
- **Role-Based Permissions**: Employee, Finance, Management, Admin
- **16/16 Test Cases Passing**
- **Automatic Enforcement** on all API endpoints

### 📄 Document Processing
- **Multi-Format Support**: PDF, Excel (.xlsx, .xls), CSV
- **Intelligent OCR**: Automatic fallback to Gemini Vision for image-based PDFs
- **Fast Extraction**: pdfplumber for text-based PDFs
- **Table Extraction**: From PDFs and Excel files
- **AI Summarization**: 200-400 word summaries with key metrics

### 🔍 RAG (Retrieval Augmented Generation)
- **Semantic Search** with vector embeddings (Gemini embedding-001)
- **Smart Chunking**: 1000 chars with 200 char overlap
- **Top-5 Retrieval** using cosine similarity
- **Context-Aware Responses** for accurate Q&A

### 📤 Upload Manager
- **Advanced Interface** at `/upload`:
  - Drag-and-drop file upload
  - Auto-generated document titles
  - Access level selector
  - Storage modes: Full Document or AI Summary Only
  - Auto-delete option (7-day TTL)
  - Real-time AI summary generation
- **Rich Markdown Editor**:
  - Bold, italic, inline code
  - Tables with pipe syntax
  - Lists (ordered and unordered)
  - Contenteditable for manual editing

### 💬 Chat & Analysis
- **Three-Panel UI**: Navigation | Chat/Studio | Results
- **Chat Mode**: Ask questions about documents
- **Studio Mode**: Generate briefs, emails, outlines, summaries
- **Department Focus**: Tailored responses per department

### 🤖 AI Features
- **Department Reports**: Automated analysis per department
- **Financial Analysis**: AI interpretation of metrics
- **Question Answering**: Natural language Q&A
- **Model Fallback**: Multiple Gemini models for reliability

### 🎨 UI/UX
- **Modern Dark Theme**: Orange (#fe742e) accents
- **Responsive Design**: Clean professional interface
- **Real-Time Updates**: Progress indicators
- **Drag-and-Drop**: Intuitive file uploads

---

## 🚧 To-Do Features

### High Priority
- [ ] Upload page access control (Finance/Management/Admin only)
- [ ] End-to-end testing suite
- [ ] Gemini OCR quota management
- [ ] API call retry logic

### Medium Priority  
- [ ] Auto-delete scheduler (7-day TTL)
- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] File management UI (view, edit, delete)
- [ ] Password hashing (currently plain text for demo)

### Low Priority
- [ ] Analytics dashboard
- [ ] Batch upload
- [ ] Document versioning
- [ ] Export reports (PDF/Excel)
- [ ] Collaborative features (comments, sharing)
- [ ] Webhook notifications

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Async web framework
- **Python 3.12**
- **Google Gemini API** - AI/ML models
- **pdfplumber** - PDF extraction
- **pandas** - Data processing
- **openpyxl** - Excel handling
- **Pydantic** - Validation
- **Uvicorn** - ASGI server

### Frontend
- **HTML5/CSS3**
- **Vanilla JavaScript**
- **Contenteditable API**

### AI Models
- **Gemini 1.5/2.0/2.5 Flash/Pro** - Text generation
- **Gemini Vision** - OCR
- **embedding-001** - Semantic embeddings

---

## 🚀 Setup

### Prerequisites
- Python 3.12+
- Google Gemini API key ([Get one here](https://ai.google.dev/))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Prithul0218/bme-hacknight-day-awake26.git
cd bme-hacknight-day-awake26
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
# Create .env file in root directory
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

5. **Run the server**
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
# Or with full path:
# /path/to/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

6. **Access the application**
- Login page: http://localhost:8000/login
- Main interface: http://localhost:8000
- Upload manager: http://localhost:8000/upload

7. **Login with demo account**
- Use any of the demo emails (see Authentication section)
- Password: `1234` (for all demo accounts)
- Your access level will be automatically set based on your role

---

## 📚 Usage Guide

### Login
1. Navigate to http://localhost:8000
2. You'll be redirected to http://localhost:8000/login
3. Enter one of the demo emails:
   - `admin@financebuddy.local` (full access)
   - `management@financebuddy.local` (management + public)
   - `finance@financebuddy.local` (finance + public)
   - `employee@financebuddy.local` (public only)
4. Enter password: `1234`
5. Click "Sign In"

### Upload a Document
1. Go to http://localhost:8000/upload
2. Drag & drop PDF/Excel/CSV file
3. Access level is **automatically set** based on your login role
4. Choose storage mode:
   - **Full Document** - Store entire document
   - **AI Summary Only** - Store only summary (saves storage)
5. (Optional) Generate AI summary
6. Click "Upload Document"

### Chat with Documents
1. Navigate to http://localhost:8000
2. Select document from left panel
3. Switch to "Chat" mode
4. Ask questions:
   - "What is the Q4 revenue?"
   - "Summarize expense categories"
   - "What are the key financial risks?"

### Generate Reports
1. Select document
2. Switch to "Studio" mode
3. Choose asset type (Brief, Email, Outline, Summary)
4. Select department
5. Add custom prompt (optional)
6. Click "Generate"

---

## 📡 API Endpoints

### Upload & Processing
- `POST /upload` - Basic document upload
- `POST /upload-managed` - Advanced upload with options
- `POST /api/generate-summary` - Generate AI summary

### Analysis & Query
- `POST /api/analyze` - Department-specific analysis
- `POST /api/chat` - Chat-based Q&A
- `POST /api/studio` - Generate content assets

### Authentication
- `GET /login` - Login page
- `POST /login` - Login form submission
- `GET /logout` - Logout and clear session
- `GET /api/auth/me` - Get current user info

### UI
- `GET /` - Main application interface (requires auth)
- `GET /upload` - Upload manager page (requires auth)

---

## 📁 Project Structure
```
bme-hacknight-day-awake26/
├── backend/
│   ├── main.py                      # FastAPI app entry point
│   ├── routers/
│   │   └── reports.py               # All API endpoints
│   ├── services/
│   │   ├── gemini_service.py        # Gemini AI integration
│   │   ├── document_processor.py    # Multi-format processing
│   │   ├── rag_service.py           # Semantic search & embeddings
│   │   ├── report_generator.py      # Department reports
│   │   ├── access_control.py        # Permission enforcement
│   │   └── auth_service.py          # User authentication & sessions
│   ├── data/
│   │   └── users.json               # User database (demo accounts)
│   ├── models/
│   │   └── schemas.py               # Pydantic models
│   ├── prompts/
│   │   └── templates.py             # Centralized AI prompts
│   ├── templates/
│   │   ├── index.html               # Main interface
│   │   ├── upload.html              # Upload manager
│   │   └── login.html               # Login page
│   └── static/
│       ├── css/
│       │   ├── style.css            # Main styles
│       │   ├── upload.css           # Upload page styles
│       │   └── login.css            # Login page styles
│       └── js/
│           ├── main.js               # Main app logic
│           └── upload.js            # Upload page logic
├── uploads/                         # Uploaded documents storage
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (not in git)
├── .gitignore
└── README.md
```

---

## 🧪 Testing

### Access Control Tests
```bash
python backend/test_access_control.py
# Expected: ✅ 16/16 tests passing
```

### RAG System Tests
```bash
python backend/test_rag.py
# Tests: Embedding, indexing, retrieval
```

---

## 🐛 Known Issues

### 1. Gemini OCR Quota Limits
- **Issue**: Free tier has daily/minute request limits
- **Impact**: Image-based PDFs may fail OCR if quota exceeded
- **Workaround**: 
  - Use text-based PDFs when possible
  - Wait for quota reset (daily at midnight PT)
  - Upgrade to paid tier for higher limits
- **Status**: Graceful fallback implemented with informative messages

### 2. In-Memory Storage
- **Issue**: All data stored in Python dictionaries
- **Impact**: Data lost on server restart
- **Workaround**: None currently
- **Fix**: Migrate to PostgreSQL/MongoDB (planned)

### 3. Plain Text Passwords (Demo Only)
- **Issue**: Passwords stored in plain text in users.json
- **Impact**: Not production-ready, demo purposes only
- **Fix**: Implement password hashing (bcrypt/argon2) before production
- **Status**: Planned for production deployment

---

## 🔒 Security Considerations

- Access control enforced at API endpoint level
- Role-based permissions for all operations
- File type validation on upload
- Temporary file cleanup after processing
- HTML escaping in markdown rendering
- **Note**: Not production-ready security - needs proper auth system

---

## 📊 Performance Notes

- **RAG Search**: < 100ms for semantic search
- **PDF Processing**: 1-3 seconds for text PDFs
- **OCR Processing**: 5-15 seconds for image PDFs (API dependent)
- **AI Summary**: 3-8 seconds per document
- **Concurrent Requests**: Handles multiple uploads simultaneously

---

## 🤝 Contributing

This is a hackathon project! Areas for contribution:
- Database integration
- Authentication system
- UI/UX improvements
- Test coverage expansion
- Documentation
- Bug fixes

---

## 📄 License
MIT License - feel free to use and modify!

---

## 🙏 Acknowledgments

- **Google Gemini API** - Powering AI capabilities
- **FastAPI** - Amazing Python web framework
- **BME Hack Night 2026** - Inspiration and deadline
- **pdfplumber** - Reliable PDF text extraction
- **Open source community** - For all the great tools

---

## 📧 Contact

**GitHub**: [@Prithul0218](https://github.com/Prithul0218)  
**Repository**: [bme-hacknight-day-awake26](https://github.com/Prithul0218/bme-hacknight-day-awake26)

---

## 🎓 Built for BME Hack Night 2026

**Last Updated**: March 7, 2026  
**Version**: 1.0.0  
**Status**: Feature-complete MVP with known limitations

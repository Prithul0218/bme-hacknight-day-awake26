# Finesse 🤖💰

**AI-powered financial document management and analysis platform** that converts complex financial reports into department-specific insights with intelligent access control, semantic search, and automated OCR.

## 🎯 The Problem
Finance reports are written in finance language for finance people. Other departments struggle to extract what matters to THEM. Additionally, managing sensitive financial documents requires proper access control and efficient retrieval systems.

## 💡 The Solution
Finesse uses AI to:
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
| admin@finesse.local | Admin | admin_only | Full access to all documents |
| management@finesse.local | Management | management_only | Management & public docs |
| finance@finesse.local | Finance | finance_only | Finance & public docs |
| employee@finesse.local | Employee | public_company | Public docs only |

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
  - **Access Control**: Restricted to Finance, Management, and Admin users only
  - Drag-and-drop file upload
  - Auto-generated document titles
  - Auto-assigned access level (based on user role)
  - Storage modes: Full Document or AI Summary Only
  - Auto-delete option (7-day TTL)
  - Real-time AI summary generation
  - **Public Upload Confirmation**: Confirms intent when uploading as public_company
- **Rich Markdown Editor**:
  - Bold, italic, inline code
  - Tables with pipe syntax
  - Lists (ordered and unordered)
  - Contenteditable for manual editing

### 📁 File Manager & Retrieval
- **Managed Browser** at `/file-manager` for reviewing stored files
- **Open Document API**: View full document content with `GET /api/file/{file_id}/open`
- **Excerpt API**: Pull short snippets with `GET /api/file/{file_id}/excerpt`
- **Delete API**: Remove files with `DELETE /api/file/{file_id}` (role-aware)
- **User-Scoped Listing**: `GET /api/user-files` returns files based on access level

### 💬 Chat & Analysis
- **Three-Panel UI**: Navigation | Chat/Studio | Results
- **Chat Mode**: Ask questions about documents
- **Studio Mode**: Generate briefs, emails, summaries, and infographic visuals
- **Infographic Assets**: Gemini-generated SVG infographic previews with download support
- **Department Focus**: Tailored responses per department

### 🚨 Alerts & History
- **Quick Alert Creation**: Template-first alert setup at `/alerts`
- **Simplified Alert Controls**: Visual severity/channel selectors and compact advanced options
- **Alert History Dashboard**: `/auto-reports` now shows triggered-alert history (not scheduled report cards)
- **Priority-First Sorting**: High-priority alerts are always listed first, then newest by timestamp
- **Acknowledge Workflow**: Every unacknowledged alert includes an `Acknowledge` action
- **Role-Aware Settings UI**: `Alert Settings` placeholder button visible only for `admin` and `management`

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
- **Consistent Icons**: Material Symbols Outlined across app pages

---

## 🔮 Future Possible Features

### Platform Reliability
- End-to-end testing suite for key flows (auth, upload, alerts, chat)
- API retry and circuit-breaker logic around external AI calls
- Better Gemini OCR quota monitoring and fallback strategy

### Data & Security
- Migrate local JSON persistence to PostgreSQL or MongoDB
- Add password hashing (bcrypt/argon2) and optional MFA
- Add audit logs for sensitive actions (delete, reclassification, admin actions)

### Workflow Enhancements
- Auto-delete scheduler for TTL-based document lifecycle policies
- Batch upload and background processing queue
- Document versioning and rollback support

### Reporting & Integrations
- Analytics dashboard for usage, alerts, and model performance
- Export generated assets/reports to PDF and Excel
- Webhook and Slack/Teams notifications for triggered alerts
- Collaborative annotations, comments, and approval workflows

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
   - `admin@finesse.local` (full access)
   - `management@finesse.local` (management + public)
   - `finance@finesse.local` (finance + public)
   - `employee@finesse.local` (public only)
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
3. Choose asset type (Brief, Email, Summary, Infographic)
4. Select department
5. Add custom prompt (optional)
6. Click "Generate"

### Manage Alert History
1. Open http://localhost:8000/auto-reports
2. Review triggered alerts sorted by severity and date
3. Use `Acknowledge` on active alerts to mark them handled
4. If logged in as `admin` or `management`, use `Alert Settings` (placeholder)

---

## 📡 API Endpoints

### Upload & Processing
- `POST /api/upload` - Basic document upload
- `POST /api/upload-managed` - Advanced upload with options
- `POST /api/generate-summary` - Generate AI summary

### Analysis & Query
- `POST /api/analyze` - Department-specific analysis
- `POST /api/chat` - Chat-based Q&A
- `POST /api/studio` - Generate content assets
- `GET /api/reports/{file_id}` - Generate department reports for a file

### File Management
- `GET /api/user-files` - List files available to the current user
- `GET /api/file/{file_id}/open` - Open full file content
- `GET /api/file/{file_id}/excerpt` - Get file excerpt/snippet
- `DELETE /api/file/{file_id}` - Delete a file (role-checked)

### Alerts
- `GET /api/alerts` - List current configured alerts and role-filtered options
- `POST /api/alerts` - Create a quick alert
- `PATCH /api/alerts/{alert_id}` - Pause/activate an alert
- `DELETE /api/alerts/{alert_id}` - Delete an alert
- `GET /api/triggered-alerts` - Get triggered-alert history
- `POST /api/triggered-alerts/{trigger_id}/acknowledge` - Acknowledge a triggered alert

### Authentication
- `GET /login` - Login page
- `POST /login` - Login form submission
- `GET /logout` - Logout and clear session
- `GET /api/auth/me` - Get current user info

### UI
- `GET /` - Main application interface (requires auth)
- `GET /upload` - Upload manager page (requires auth)
- `GET /file-manager` - Managed file browser page (requires auth)
- `GET /alerts` - Alert creation and configuration page (requires auth)
- `GET /auto-reports` - Triggered alert history page (requires auth)
- `GET /health` - Health check endpoint

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
│   │   ├── auto_report_service.py   # Auto report scheduling utilities
│   │   ├── alerts_storage_service.py# Alert and trigger persistence
│   │   ├── access_control.py        # Permission enforcement
│   │   └── auth_service.py          # User authentication & sessions
│   ├── data/
│   │   ├── users.json               # User database (demo accounts)
│   │   ├── alerts.json              # Alert definitions and trigger history
│   │   └── auto_reports.json        # Auto report data store
│   ├── models/
│   │   └── schemas.py               # Pydantic models
│   ├── prompts/
│   │   └── templates.py             # Centralized AI prompts
│   ├── templates/
│   │   ├── index.html               # Main interface
│   │   ├── alerts.html              # Alert configuration UI
│   │   ├── auto_reports.html        # Alert history UI
│   │   ├── file_manager.html        # Managed file browser
│   │   ├── upload.html              # Upload manager
│   │   └── login.html               # Login page
│   └── static/
│       ├── css/
│       │   ├── style.css            # Main styles
│       │   ├── alerts.css           # Alerts page styles
│       │   ├── auto_reports.css     # Alert history page styles
│       │   ├── upload.css           # Upload page styles
│       │   └── login.css            # Login page styles
│       └── js/
│           ├── main.js              # Main app logic
│           ├── alerts.js            # Alerts page interactions
│           ├── auto_reports.js      # Alert history acknowledge actions
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

### 2. Local JSON Storage Limitations
- **Issue**: Persistent data is stored in local JSON files (`backend/data/*.json`)
- **Impact**: Works for MVP/demo, but is limited for concurrent multi-user workloads and production reliability
- **Workaround**: Keep regular backups of the `backend/data/` directory
- **Fix**: Migrate to PostgreSQL/MongoDB with transactional writes and migrations

### 3. Plain Text Passwords (Demo Only)
- **Issue**: Passwords stored in plain text in users.json
- **Impact**: Not production-ready, demo purposes only
- **Fix**: Implement password hashing (bcrypt/argon2) before production
- **Status**: Planned for production deployment

---

## Human-in-the-Loop Aspects

Finesse incorporates critical human oversight points to ensure accuracy and security of financial data processing:

### 📋 OCR Review Workflow
**Why it's needed**: Gemini Vision API OCR can misread scanned PDFs, especially with:
- Low-quality scans or poor image resolution
- Complex tables with merged cells
- Handwritten annotations or stamps
- Multi-column layouts
- Font variations or special characters

**Current Implementation**:
- ✅ Automatic fallback to OCR for image-based PDFs (text extraction fails)
- ✅ AI-generated summaries include OCR'd content
- ✅ Chat/RAG queries against OCR'd text
- ⚠️ **MANUAL REVIEW REQUIRED**: Users must verify OCR accuracy before relying on data for critical decisions

**Recommended Process**:
1. Upload scanned PDF via upload manager
2. Review generated AI summary carefully
3. Cross-check key numbers and tables against original document
4. Correct any OCR errors in the markdown editor before final storage
5. Submit corrected version

**Best Practices**:
- For critical financial reports, always compare OCR'd tables to source
- Flag low-confidence extractions (especially currency amounts, dates, legal terms)
- Use original document when OCR accuracy cannot be verified
- Test with high-quality scans first to establish confidence baseline

### 🚨 Public Document Classification
**Why it's needed**: Prevents inadvertent exposure of sensitive financial data

**Current Implementation**:
- ✅ Admin/Management/Finance can assign classification levels
- ✅ Confirmation modal appears when uploading as `public_company`
- ✅ User must explicitly confirm they intend public sharing
- ✅ Role-based dropdown shows only allowed classifications per user

**Classification Levels**:
| Level | Visibility | Use Case | Review Level |
|-------|------------|----------|--------------|
| `public_company` | All employees | General metrics, press releases | Quick check |
| `finance_only` | Finance dept | Internal reports, detailed budgets | Financial accuracy |
| `management_only` | Management+ | Strategic plans, forecasts | Strategic alignment |
| `admin_only` | Admin only | Highly sensitive, executive decisions | Full compliance review |

**Required Human Decision**:
- Finance team reviews document sensitivity before classification
- Management confirms strategic documents aren't overexposed
- Admins approve admin_only escalations for maximum-secrecy docs

### 📊 AI Summary Accuracy Verification
**Why it's needed**: AI summaries can:
- Miss critical nuances or caveats
- Misinterpret complex financial metrics
- Over-generalize department impacts
- Include hallucinations for ambiguous content

**Current Verification Points**:
1. ✅ Summary generated and shown in upload preview
2. ⚠️ **User reviews** before deciding storage mode:
   - "Full Document" - Store original for human reference
   - "AI Summary Only" - Trust summary for key metrics
3. ⚠️ **Chat conversations** expose missing context quickly:
   - Inconsistent answers across related questions → potential OCR error
   - "I don't know" responses → summary too aggressive
   - Department-specific insights need domain expert validation

**Recommended Process**:
- Finance lead spots-checks 10% of summary accuracy
- Compare AI highlights to actual document sections
- Flag hallucinations or missing metrics
- Adjust prompts in `backend/prompts/templates.py` if patterns emerge

### 🎯 Department-Specific Insights Quality
**Why it's needed**: Tailored summarization can miss domain context

**Current Safeguards**:
- ✅ Multi-department Studio generation for tailored outputs
- ✅ Triggered alert history available for operational follow-up
- ⚠️ **Audience requires validation**: Department leads should review generated insights for relevance

**Recommended Process**:
1. Finance team generates first department-specific outputs in Studio
2. Each department head reviews relevance and accuracy
3. Provide feedback on:
   - Which metrics matter most
   - Missing context or misinterpretations
   - Missing alert conditions or thresholds
4. Refine prompts and alert templates based on that feedback

### ✅ Checklist for Critical Documents
When uploading high-impact financial reports, ensure:
- [ ] **OCR Accuracy**: Spot-check key numbers, dates, amounts
- [ ] **Classification Correct**: Confirm sensitivity level is appropriate
- [ ] **Summary Complete**: Key metrics and risks included
- [ ] **Access List Verified**: Correct departments/roles will see this
- [ ] **Source Available**: Keep original document for audit trail
- [ ] **Department Lead Notified**: Primary audience aware of new document

---

## Security Considerations

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

# CivicFix – Municipal Complaint Management System

> **Theme:** Urban System | **Curriculum:** Engineering Idea Lab – Semester 5  
> **Type:** Full-Stack Municipal Grievance Redressal Web Application

---

## 🏛️ Project Overview

**CivicFix** is a modern, responsive web-based municipal grievance redressal and complaint management platform. Designed specifically under the **Urban System** theme of the Engineering Idea Lab, CivicFix bridges the communication gap between citizens and local urban administration.

In rapidly growing urban environments, civic issues such as potholes, uncollected waste, non-functional streetlights, water supply disruptions, and drainage overflows often go unreported or delayed due to cumbersome bureaucracy. **CivicFix** streamlines this lifecycle by providing citizens an intuitive portal to lodge grievances with photograph evidence, track progress in real-time through an auditable workflow, and rate the resolution quality. Simultaneously, municipal administrators gain an interactive operations console to verify reports, auto-assign departments, update work statuses, attach resolution proof, and analyze municipal pain points via real-time analytics.

---

## ✨ Key Features

### 👤 Citizen Module
- **Self-Service Authentication:** Secure account registration and session management with password hashing and validation.
- **Complaint Submission with Evidence:** Multi-field complaint form capturing title, category, description, physical address, landmark, priority, and photo proof (JPEG/PNG up to 5 MB).
- **Automated Unique Complaint ID:** Auto-generates human-readable, trackable tracking codes in `CF-YYYYMMDD-XXXX` format.
- **Real-Time Progress Tracking:** Visual multi-stage status timeline demonstrating live progress from submission to resolution.
- **Public Complaint Tracker:** Fast status check by complaint ID without mandatory login.
- **Citizen Feedback & Rating:** Interactive 5-star rating widget and feedback submission on resolved complaints to foster municipal accountability.
- **Personal Dashboard:** Overview of all past and active complaints submitted by the citizen with status indicators.

### 🛡️ Municipal Admin Module
- **Role-Based Access Control (RBAC):** Strict view and route protection restricting administrative routes to authorized personnel.
- **Centralized Operations Console:** Filterable dashboard listing all civic complaints across all wards and departments.
- **Department Allocation:** Flexible department assignment and reassignment (Waste Management, Road Dept, Electrical Dept, etc.).
- **Auditable Status Workflow:** Transition complaints through a strict lifecycle:
  $$\text{Submitted} \longrightarrow \text{Under Review} \longrightarrow \text{Verified} \longrightarrow \text{Assigned} \longrightarrow \text{In Progress} \longrightarrow \text{Resolved} \text{ (or } \text{Rejected)}$$
- **Resolution Proof Upload:** Municipal field officers upload completion photos and administrative closure remarks visible to citizens.
- **Interactive Analytics & Reports:** Visual breakdown of grievances by category, status, priority, and department powered by Chart.js.
- **Search, Filter & Sort:** Instant query filtering by category, status, priority, department, and date range.
- **Printable Dossiers:** Clean print-ready formatting for field worker dispatch and official records.

---

## 💻 Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.8+ / Flask | Lightweight, scalable WSGI web application framework |
| **Database & ORM** | SQLite / SQLAlchemy | Relational SQL database with declarative ORM mapping |
| **Authentication** | Flask-Login & Werkzeug | Secure session cookies, PBKDF2/SHA-256 password hashing |
| **Form Security & CSRF** | Flask-WTF / WTForms | Robust CSRF protection token validation & field sanitation |
| **Frontend UI** | HTML5 / CSS3 / Vanilla JS | Semantic HTML5 structure with custom styling and animations |
| **CSS Framework** | Bootstrap 5.3 | Responsive grid layout, utility classes, and components |
| **Icons** | Bootstrap Icons | SVG vector icons for UI actions and category indicators |
| **Data Visualization** | Chart.js 4.x | Dynamic canvas-based bar, donut, and line charts |
| **File Handling** | Werkzeug Utilities | Secure file uploads with MIME and extension checks |

---

## 📁 Project Structure

```text
civicfix/
│
├── app/
│   ├── __init__.py              # Application factory, blueprint registration & error handlers
│   ├── extensions.py            # Extensions init (db, login_manager, csrf)
│   ├── models.py                # Database models (User, Complaint, Department, Resolution, etc.)
│   ├── seed.py                  # Database seeder (Demo users & municipal departments)
│   ├── utils.py                 # RBAC decorators, ID generators, image upload handlers
│   │
│   ├── admin/                   # Admin blueprint
│   │   ├── __init__.py          # Blueprint declaration
│   │   ├── routes.py            # Admin dashboard, complaint management, analytics
│   │   └── forms.py             # Admin status update & resolution forms
│   │
│   ├── auth/                    # Authentication blueprint
│   │   ├── __init__.py          # Blueprint declaration
│   │   ├── routes.py            # Login, register, logout handlers
│   │   └── forms.py             # WTForms for login and citizen registration
│   │
│   ├── citizen/                 # Citizen portal blueprint
│   │   ├── __init__.py          # Blueprint declaration
│   │   └── routes.py            # Citizen dashboard, my complaints, feedback
│   │
│   ├── complaints/              # Public complaint blueprint
│   │   ├── __init__.py          # Blueprint declaration
│   │   ├── routes.py            # File complaint, track status, view detail
│   │   └── forms.py             # Complaint lodging and search forms
│   │
│   ├── main/                    # Public main blueprint
│   │   ├── __init__.py          # Blueprint declaration
│   │   └── routes.py            # Homepage, about, how-it-works, contact
│   │
│   ├── static/                  # Static assets
│   │   ├── css/
│   │   │   └── style.css        # Complete custom styling, theme variables & animations
│   │   ├── js/
│   │   │   └── main.js          # Client-side validation, previews, star rating & timers
│   │   └── uploads/             # User-uploaded evidence
│   │       ├── complaints/      # Citizen complaint images
│   │       └── resolutions/     # Admin resolution proof images
│   │
│   └── templates/               # Jinja2 HTML templates
│       ├── base.html            # Core layout with navbar, flash alerts & footer
│       ├── index.html           # Landing page with hero banner & feature cards
│       ├── about.html           # Project vision, mission & urban impact
│       ├── how_it_works.html    # Citizen step-by-step submission guide
│       ├── contact.html         # Municipal helpline and contact form
│       ├── admin/               # Admin views (dashboard, complaints list, reports)
│       ├── auth/                # Login and register pages
│       ├── citizen/             # Citizen dashboard & feedback modal
│       ├── complaints/          # Lodge complaint & tracker views
│       └── errors/              # 403, 404, 413, 500 error pages
│
├── instance/
│   └── civicfix.db              # SQLite relational database (auto-created)
│
├── config.py                    # App configuration (secret keys, upload paths, limits)
├── requirements.txt             # Python package dependencies
├── run.py                       # Application execution entry point
└── README.md                    # Project documentation
```

---

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.8** or higher installed on your system
- **pip** (Python package installer)
- Git (optional, for cloning)

### Step-by-Step Setup

1. **Navigate to the Project Directory:**
   ```bash
   cd "d:/study/sem 5/Idea Lab-5/idea lab-prototype/civicfix"
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment:**
   - **Windows (PowerShell / Command Prompt):**
     ```powershell
     venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Application:**
   ```bash
   python run.py
   ```

6. **Access the Web Portal:**
   Open your browser and navigate to:  
   👉 **`http://localhost:5000`**

*(Note: Database tables, initial schema, default municipal departments, and demo accounts are automatically initialized upon the very first run!)*

---

## 👥 Demo Accounts

The application seeds a citizen demonstration account automatically. It creates the administrator account only when `CIVICFIX_ADMIN_PASSWORD` is set in the environment; choose a unique, strong value and keep it out of source control.

| Role | Email Address | Password | Privileges |
| :--- | :--- | :--- | :--- |
| **Citizen** | `citizen@civicfix.demo` | `Citizen@123` | File complaints, view own grievances, give star feedback |
| **Admin** | `admin@civicfix.demo` | Set `CIVICFIX_ADMIN_PASSWORD` | Assign departments, update statuses, upload resolutions, view analytics |

> 💡 **Tip:** You can also register a brand new citizen account through the **Register** link on the navigation bar.

---

## 🗄️ Database Architecture

The application utilizes an SQLite relational database located at `instance/civicfix.db` with enforced foreign keys:

1. **`users`**: Stores user authentication credentials, full name, mobile number, address, and role (`citizen` or `admin`).
2. **`departments`**: Catalog of municipal wings (e.g., Waste Management, Road Department) responsible for grievance handling.
3. **`complaints`**: Core grievance entities containing unique tracking ID, category, coordinates/address, priority, status, and image links.
4. **`complaint_status_history`**: Audit log recording every state transition with timestamps and admin remarks.
5. **`resolutions`**: Stores completion remarks, resolution timestamps, and proof photos uploaded by resolving officers.
6. **`feedback`**: Citizen satisfaction ratings (1 to 5 stars) and review comments submitted after resolution.
7. **`contact_messages`**: Public inquiries submitted through the Contact Us form.

---

## 🚦 Complaint Workflow & Status Lifecycle

Complaints in CivicFix adhere to a rigorous state progression:

```text
[Citizen Files Grievance]
           │
           ▼
     [Submitted] ──────────► (Auto-assigned initial tracking code: CF-YYYYMMDD-XXXX)
           │
           ▼
    [Under Review] ────────► (Admin verifies authenticity & location)
           │
     ┌─────┴───────────────┐
     ▼                     ▼
 [Verified]           [Rejected] ──► (Invalid/duplicate with official reason)
     │
     ▼
 [Assigned] ──────────────► (Assigned to dedicated municipal department)
     │
     ▼
[In Progress] ────────────► (Field crew dispatched for on-site work)
     │
     ▼
  [Resolved] ─────────────► (Officer uploads completion photo & remarks)
     │
     ▼
[Citizen Feedback] ───────► (Citizen rates resolution 1–5 stars)
```

---

## 🏷️ Complaint Categories & Departments

CivicFix maps 11 civic issue classifications directly to their corresponding urban departments:

| # | Complaint Category | Responsible Municipal Department | Typical Resolution Scope |
| :---: | :--- | :--- | :--- |
| **1** | **Garbage Collection** | Waste Management | Missed trash pickups, overflowing dumpsters, illegal dumping |
| **2** | **Road Damage / Potholes** | Road Department | Asphalt cracks, dangerous potholes, uneven road surface |
| **3** | **Streetlight Problems** | Electrical Department | Burned out fixtures, blinking lights, broken electric poles |
| **4** | **Water Leakage / Water Supply** | Water Department | Burst mains, contaminated tap water, low supply pressure |
| **5** | **Drainage Problems** | Drainage Department | Blocked storm drains, sewage overflows, broken manhole covers |
| **6** | **Waterlogging** | Drainage Department | Monsoon puddle collection, flooded underpasses |
| **7** | **Traffic Signal Problems** | Traffic Department | Non-functional signals, obscured traffic lights, damaged signs |
| **8** | **Public Infrastructure** | Public Works Department (PWD) | Damaged bus stops, broken sidewalks, hazardous pedestrian bridges |
| **9** | **Fallen Trees** | Garden / Tree Department | Fallen branches blocking roads, hazardous overgrown foliage |
| **10** | **Public Toilet Issues** | Sanitation Department | Unclean municipal rest facilities, non-functional plumbing |
| **11** | **Other Municipal Issues** | General Administration | Stray animal nuisance, noise complaints, miscellaneous civic needs |

---

## 🔮 Future Scope & Enhancements

- [ ] **GPS Auto-Geolocation:** Browser geolocation API & interactive Leaflet/OpenStreetMap pin selector for exact coordinates.
- [ ] **Automated Duplicate Detection:** AI-assisted computer vision & similarity matching to detect duplicate complaints in the same geographic radius.
- [ ] **SMS & WhatsApp Alerts:** Twilio or WhatsApp Business API integration for instant status push notifications to citizens.
- [ ] **Native Mobile Application:** Cross-platform React Native / Flutter mobile app for instant camera snapping on-the-go.
- [ ] **IoT Smart Bin Integration:** Automated sensor alerts for smart waste bins when reaching 90% capacity.
- [ ] **Multilingual Interface:** Support for regional Indian languages (Hindi, Marathi, Gujarati, Tamil, etc.) for inclusive civic access.

---

## 🎓 Academic Information

- **Course:** Engineering Idea Lab
- **Semester:** 5th Semester (B.Tech / B.E.)
- **Theme:** Urban System
- **Focus Area:** Smart Cities, Digital Governance, Municipal Operations Optimization, Citizen Empowerment

---

## 📄 License & Terms

This project is created strictly for **academic and educational purposes** under the Engineering Idea Lab curriculum.  
All rights reserved © 2026 CivicFix Team.

## Render deployment

Use render.yaml to deploy the Python web service on Render's Free plan. Render generates the Flask secret key and prompts you to set CIVICFIX_ADMIN_PASSWORD. SQLite and uploaded images use temporary storage, so complaints, accounts, and images can be lost whenever the service spins down, restarts, or redeploys. Free services also spin down after 15 minutes without traffic and can take about a minute to start again. This setup is for a temporary demo; the local SQLite database and existing uploads remain on this computer.

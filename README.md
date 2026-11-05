# Super-Secure Communication for Voting System Using Quantum Key Distribution (BB84 + OTP)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.2+-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Qiskit](https://img.shields.io/badge/Qiskit-2.5+-6929C4?logo=qiskit&logoColor=white)](https://qiskit.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Beanie%20ODM-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![LaTeX](https://img.shields.io/badge/LaTeX-XeLaTeX%2074%20Pages-008080?logo=latex&logoColor=white)](https://www.latex-project.org/)

An educational, interactive, and cryptographically provable quantum-secured voting platform. The system implements the **BB84 Quantum Key Distribution (QKD)** protocol, **2-Universal Toeplitz Hashing (Privacy Amplification)**, and **One-Time Pad (OTP)** ballot encryption. It provides Information-Theoretic Security against quantum and classical adversaries, supporting both local noise simulation on **Qiskit Aer** and cloud execution on physical **IBM Quantum QPUs** (e.g., 156-qubit Heron processor `ibm_kingston`).

---

## 📁 Repository Structure

```
super-secure-communication-voting/
├── backend/                  # FastAPI RESTful API & Quantum Engine
│   ├── src/
│   │   ├── core/             # Configuration & Beanie/MongoDB database initialization
│   │   ├── modules/          # QKD simulation (Qiskit), Privacy Amplification & voting service
│   │   ├── evaluation/       # Decoupled experimental benchmarks & evaluation suite
│   │   └── main.py           # FastAPI application entrypoint
│   ├── .env.template         # Backend environment variables template
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # React 19 + TypeScript + Vite Web Application
│   ├── src/                  # Stepper UI, multi-perspective inspection & voting views
│   ├── .env.template         # Frontend environment variables template
│   └── package.json          # Node dependencies and scripts
│
├── report/                   # Senior Project Academic Report (XeLaTeX)
│   ├── chapters/             # Chapters 1-5, Appendix A (Proof) & Appendix B (Manual)
│   ├── figures/              # Canonical publication figures and manual screenshots
│   ├── references.bib        # Verified BibTeX bibliography
│   └── main.tex              # Master LaTeX document (74 pages)
│
└── run.py                    # One-click development runner (Backend + Frontend)
```

---

## ⚡ Prerequisites

Make sure you have the following installed on your machine:
- **Python**: Version `3.10` or higher (`3.11+` recommended)
- **Node.js**: Version `18.0.0` or higher & `npm`
- **MongoDB**: A running local instance (`mongodb://localhost:27017`) or a free [MongoDB Atlas](https://www.mongodb.com/atlas) cloud cluster
- *(Optional)* **IBM Quantum Account**: An API token from [IBM Quantum Platform](https://quantum.ibm.com/) (required only if running on physical quantum hardware)
- *(Optional for Report)* **XeLaTeX & BibTeX**: MiKTeX or TeX Live with Thai language font support (`Laksaman`)

---

## 🚀 Quick Start Guide

### Step 1: Clone the Repository
```bash
git clone https://github.com/archiash/super-secure-communication-voting.git
cd super-secure-communication-voting
```

### Step 2: Configure Environment Variables
Copy the templates to create local `.env` files for both backend and frontend:

**On Linux / macOS:**
```bash
cp backend/.env.template backend/.env
cp frontend/.env.template frontend/.env
```

**On Windows (PowerShell):**
```powershell
Copy-Item backend/.env.template backend/.env
Copy-Item frontend/.env.template frontend/.env
```

*(Review and update values in `backend/.env` and `frontend/.env` as described in the [Environment Variables](#-environment-variables-reference) section below).*

---

### Step 3: Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# Alternatively, if using uv:
# uv sync
cd ..
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

---

### Step 4: Run the Application (One-Click)

Run both the FastAPI backend and Vite frontend concurrently with unified logging and graceful shutdown:

```bash
python run.py
```

Once started:
- **Frontend Web UI:** `http://localhost:5173`
- **Backend API Docs (Swagger):** `http://localhost:8000/docs`
- **Backend Health Check:** `http://localhost:8000/`

#### Specific Component Runners:
```bash
# Start backend server only (port 8000)
python run.py --backend-only

# Start frontend server only (port 5173)
python run.py --frontend-only
```

---

## ⚙️ Environment Variables Reference

### 1. Backend (`backend/.env`)

| Variable | Type | Default Value | Description |
| :--- | :---: | :---: | :--- |
| `MONGODB_URI` | `string` | `mongodb://localhost:27017` | MongoDB connection URI. Used by Beanie ODM to store voting sessions, elections, and quantum audit logs. |
| `IBM_TOKEN` | `string` | `""` | IBM Quantum API token from [quantum.ibm.com](https://quantum.ibm.com/). Required when executing on real cloud QPUs. |
| `USE_IBM_QUANTUM` | `boolean` | `false` | Global toggle. Set to `true` to enable IBM Quantum mode (simulation or cloud QPU), or `false` for local Qiskit Aer simulation. |
| `USE_REAL_IBM_HARDWARE` | `boolean` | `false` | When `USE_IBM_QUANTUM=true`: Set to `true` to submit jobs to physical IBM QPUs (e.g., `ibm_kingston`), or `false` for realistic noise simulation without queue wait. |

#### 🎛️ Quantum Execution Modes:
- **Mode 1: Local Aer Simulator (`USE_IBM_QUANTUM=false`)**  
  Zero noise ($QBER = 0.0\%$), runs instantaneously offline. Ideal for rapid development and testing.
- **Mode 2: IBM Realistic Noise Simulation (`USE_IBM_QUANTUM=true`, `USE_REAL_IBM_HARDWARE=false`)**  
  Simulates physical IBM hardware noise ($QBER \approx 2.5\% - 2.82\%$). Runs locally without cloud queue delays.
- **Mode 3: Physical IBM Quantum QPU (`USE_IBM_QUANTUM=true`, `USE_REAL_IBM_HARDWARE=true`)**  
  Transpiles quantum circuits and submits jobs to IBM Quantum dilution refrigerators over the cloud.

---

### 2. Frontend (`frontend/.env`)

| Variable | Type | Default Value | Description |
| :--- | :---: | :---: | :--- |
| `VITE_USE_REAL_API` | `boolean` | `true` | Set to `true` to connect to the FastAPI backend service, or `false` to run in standalone browser-only mock mode. |
| `VITE_API_BASE_URL` | `string` | `http://localhost:8000` | Base URL of the running FastAPI backend server. |

---

## 🔬 Experimental Benchmarks & Evaluation

All empirical evaluations from Chapter 4 of the senior project report are decoupled into modular analyzers that execute against cached master data (`backend/src/evaluation/data/benchmark_results.json`) in **< 1 second**:

```bash
# Render all 3 publication figures and summary tables at once:
python backend/src/evaluation/eval_render_plots.py

# Run individual experiment analyzers:
python backend/src/evaluation/eval_exp1_confusion_matrix.py     # Exp 1: IBM Hardware Confusion Matrix
python backend/src/evaluation/eval_exp2_qber_bias.py            # Exp 2: QBER Estimation Bias Convergence
python backend/src/evaluation/eval_exp3_privacy_amplification.py # Exp 3: Eve Knowledge Elimination Rate

# Re-simulate all quantum circuits from scratch (generates fresh benchmark_results.json):
python backend/src/evaluation/eval_run_all.py --retest
```

All generated figures are saved directly to `report/figures/`:
- `exp1_confusion_matrix_ibm.png`
- `exp2_qber_estimation_bias.png`
- `exp3_privacy_amplification.png`

---

## 📄 Academic Report Compilation (XeLaTeX)

The project includes the complete academic senior project thesis document (74 pages, Department of Computer Engineering, Chiang Mai University):

```bash
cd report

# First pass (generates auxiliary files)
xelatex -interaction=nonstopmode main.tex

# Resolve BibTeX citations
bibtex main

# Final pass (resolves cross-references and outputs main.pdf)
xelatex -interaction=nonstopmode main.tex
```

---

## 👥 Authors & Team Contributions

- **Pakin Niramitsima (ภคิน นิรมิตสีมา)** — *Frontend Web Application, Interactive Stepper & Audit Log UI*
- **Yutthakarn Sajui (ยุทธกานต์ สาจุ้ย)** — *Backend RESTful API, MongoDB Schema & Session Management*
- **Arthinan Chaengsawang (อาทินันท์ แจ้งสว่าง)** — *UI/UX Design, Security Proof (Appendix A) & User Manual (Appendix B)*
- **Paisit Lerdananpipat (ไพสิฐ เลิศอนันต์พิพัฒน์)** — *Quantum Circuit Simulation, IBM QPU Connection, Privacy Amplification & Benchmark Evaluation*

Department of Computer Engineering, Faculty of Engineering, Chiang Mai University.

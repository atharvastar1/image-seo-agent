# 👁️ SEO Visionary: AI-Powered Image Intelligence suite

SEO Visionary is a professional-grade image SEO audit tool that reverse-engineers Google and Bing's visual algorithms. Using **Llama 3.2** as a forensic engine, it analyzes competitive landscapes to provide winner titles, semantic gap keywords, and Alt-text optimization strategies.

![SaaS Dashboard Interface](https://img.shields.io/badge/UI-Professional--Dark-8b5cf6?style=for-the-badge)
![LLM Integration](https://img.shields.io/badge/AI-Llama--3.2-10b981?style=for-the-badge)

## 🚀 Key Features

- **Master SEO Audit**: Deep-dive analysis of top 40 image rankings across Google & Bing.
- **Winner Title Construction**: AI-generated, click-magnetic titles optimized for 2024.
- **Semantic Gap Analysis**: Identifies high-value keywords missing from competitor titles.
- **Alt-Text Blueprint**: Automated strategy for image indexing and accessibility.
- **High-End Dashboard**: Premium Glassmorphism UI with interactive difficulty gauges and shimmering effects.
- **Clickable SERP Results**: Instantly explore source pages by clicking competitor cards.
- **Secure Architecture**: Environment-based API key management.

## 🛠️ Technology Stack

- **Backend**: Python (Flask, Flask-CORS)
- **Frontend**: Vanilla HTML5, CSS3 (Glassmorphism), JavaScript (ES6+)
- **Analysis Engine**: Local LLM (Llama 3.2 via Ollama)
- **Data Source**: SerpApi (Live India-specific SERPs)

## 📦 Installation & Setup

### 1. Prerequisites
- [Ollama](https://ollama.com/) installed and running.
- Llama 3.2 model pulled: `ollama pull llama3.2`
- SerpApi Key (India region supported).

### 2. Environment Setup
Clone the repository and install dependencies:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install flask requests flask-cors python-dotenv
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
SERP_API_KEY=your_serp_api_key_here
```

### 4. Running the Dashboard
Start the Flask backend:
```bash
python3 app.py
```
Open your browser and navigate to: `http://localhost:5001`

## 📊 Usage

1. **Enter Keyword**: Type your target keyword (e.g., "Fintech Startups India").
2. **Press Enter**: The AI will orchestrate a semantic analysis across Google and Bing.
3. **Analyze Results**: View your **Winner Title**, **Missing Keywords**, and the **Alt-Text strategy**.
4. **Export**: Copy the JSON-LD Schema code or download a full CSV Strategy Report.

## 📄 License
MIT License - Developed by Atharva Interactives

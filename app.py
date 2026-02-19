from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import csv
import re
import os

app = Flask(__name__)
CORS(app)

# --- REUSE EXISTING LOGIC ---
SERP_API_KEY = "b9b6c464b5a0e6068004e475b8b1e838c5d14d2141b0e14cc0e17cc23f089348"

class DeepLLMAnalyzer:
    def __init__(self, keyword, google_results, bing_results):
        self.keyword = keyword
        self.titles = [r['title'] for r in google_results] + [r['title'] for r in bing_results]

    def analyze(self):
        print(f"🤖 SEO-Centric Audit starting for '{self.keyword}'...")
        prompt = f"""
        Role: Master SEO Architect
        Task: Analyze 40 image titles for '{self.keyword}' and construct a title that will CRUSH the competition.
        
        Titles to Audit:
        {chr(10).join(self.titles)}
        
        Provide:
        1. Intent: [User search intent: e.g., Informational, Transactional]
        2. Winner: [The superior, click-magnetic title for 2024. Must be better than the top 10.]
        3. Gap_Keywords: [3-4 high-value keywords missing from current titles]
        4. Difficulty: [Score 1-100 based on keyword saturation]
        5. Alt_Optimization: [Recommended Alt Text strategy]
        6. Summary: [3-sentence strategy summary]
        7. Drivers: [Driver1|Driver2|...|Driver40]
        """
        try:
            payload = {"model": "llama3.2", "prompt": prompt, "stream": False}
            r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
            text = r.json().get("response", "")
            
            data = {
                "intent": "Checking...", "winner": "Constructing Title...", 
                "gap": "Evaluating...", "difficulty": "50", 
                "alt": "Optimizing...", "summary": "N/A", "drivers": []
            }
            
            def clean_val(val):
                # Aggressively strip markdown bolding, italics, and leading numbering
                v = re.sub(r'^\d+\.\s*', '', val) # Remove leading "1. "
                v = v.replace('**', '').replace('*', '').strip()
                return v

            lines = text.split('\n')
            for line in lines:
                l_strip = line.strip().lower()
                if "intent:" in l_strip: data["intent"] = clean_val(line.split(':', 1)[-1])
                elif "winner:" in l_strip: data["winner"] = clean_val(line.split(':', 1)[-1])
                elif "gap_keywords:" in l_strip: data["gap"] = clean_val(line.split(':', 1)[-1])
                elif "difficulty:" in l_strip: data["difficulty"] = clean_val(line.split(':', 1)[-1]).replace('%', '')
                elif "alt_optimization:" in l_strip: data["alt"] = clean_val(line.split(':', 1)[-1])
                elif "summary:" in l_strip: data["summary"] = clean_val(line.split(':', 1)[-1])
                elif "drivers:" in l_strip:
                    drivers_raw = clean_val(line.split(':', 1)[-1])
                    data["drivers"] = [d.strip() for d in drivers_raw.split('|')]
            
            return data
        except Exception as e:
            print(f"Llama Error: {e}")
            return {
                "intent": "SEO", "winner": f"Optimized {self.keyword} 2024",
                "gap": "Missing Context", "difficulty": "40",
                "alt": "Focus Keywords", "summary": "N/A", 
                "drivers": ["Direct Match"] * 40
            }

def fetch_rankings(keyword):
    results = {"Google": [], "Bing": []}
    engines = [
        {"name": "Google", "engine": "google_images", "key_num": "num", "extra": {"gl": "in", "hl": "en"}},
        {"name": "Bing", "engine": "bing_images", "key_num": "count", "extra": {"cc": "IN"}}
    ]
    for se in engines:
        params = {"engine": se["engine"], "q": keyword, "api_key": SERP_API_KEY, se["key_num"]: 20}
        params.update(se["extra"])
        try:
            r = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
            images = r.json().get("images_results", [])
            for img in images[:20]:
                results[se["name"]].append({
                    "title": img.get("title") or "Untitled",
                    "source": img.get("source") or "Unknown",
                    "thumbnail": img.get("thumbnail"),
                    "link": img.get("link")
                })
        except: pass
    return results

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    keyword = data.get('keyword')
    if not keyword: return jsonify({"error": "No keyword"}), 400
    
    results = fetch_rankings(keyword)
    analyzer = DeepLLMAnalyzer(keyword, results["Google"], results["Bing"])
    analysis = analyzer.analyze()
    
    drivers = analysis.get("drivers", [])
    for i, res in enumerate(results["Google"]):
        res["driver"] = drivers[i] if i < len(drivers) else "Keyword Synergy"
    for i, res in enumerate(results["Bing"]):
        idx = i + 20
        res["driver"] = drivers[idx] if idx < len(drivers) else "Semantic Alignment"
    
    clean_kw = re.sub(r'[^\w\s-]', '', keyword).strip().replace(' ', '_').lower()
    csv_filename = f"results_{clean_kw}.csv"
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["MASTER SEO AUDIT: " + keyword])
        writer.writerow(["Recommended Title", analysis['winner']])
        writer.writerow(["Difficulty Score", analysis.get('difficulty')])
        writer.writerow(["Visual Style", analysis.get('visual_theme')])
        writer.writerow(["Color Palette", analysis.get('palette')])
        writer.writerow([])
        writer.writerow(["RANKINGS DATA"])
        writer.writerow(["Rank", "Engine", "Title", "Ranking Driver", "Source", "Link"])
        for i, res in enumerate(results["Google"]):
            writer.writerow([i+1, "Google", res['title'], res['driver'], res['source'], res['link']])
        for i, res in enumerate(results["Bing"]):
            writer.writerow([i+1, "Bing", res['title'], res['driver'], res['source'], res['link']])

    return jsonify({
        "results": results,
        "analysis": analysis,
        "csv": csv_filename
    })

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('.', filename, as_attachment=True)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(port=5001, debug=True)

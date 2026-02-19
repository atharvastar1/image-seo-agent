from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import csv
import re
import os

from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

# --- REUSE EXISTING LOGIC ---
SERP_API_KEY = os.getenv("SERP_API_KEY")

class DeepLLMAnalyzer:
    def __init__(self, keyword, google_results, bing_results):
        self.keyword = keyword
        self.titles = [r['title'] for r in google_results] + [r['title'] for r in bing_results]

    def analyze(self):
        print(f"🤖 Elite Professional Audit starting for '{self.keyword}'...")
        prompt = f"""
        Role: Senior SEO & Semantic Data Scientist
        Task: Perform an ELITE competitive audit for '{self.keyword}'.
        
        Analyze these 40 titles:
        {chr(10).join(self.titles)}
        
        Provide the following precise data points:
        1. Intent: [User Search Intent]
        2. Winner: [The Optimized Winner Title for 2024]
        3. Gap_Keywords: [Keywords missing from competition but high value]
        4. Heatmap: [List 4-6 primary keywords. Format: keyword:weight (weight 1-10, 10=hottest competition, 1=easy gap)]
        5. Difficulty: [Score 1-100]
        6. Alt_Text: [Perfect Alt Optimization string]
        7. Summary: [2-sentence implementation strategy]
        8. Drivers: [Driver1|Driver2|...|Driver40]
        """
        try:
            payload = {"model": "llama3.2", "prompt": prompt, "stream": False}
            r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
            text = r.json().get("response", "")
            
            data = {
                "intent": "Checking...", "winner": "Constructing Title...", 
                "gap": "Evaluating...", "difficulty": "50", 
                "alt": "Optimizing...", "summary": "N/A", "drivers": [],
                "heatmap": [] # [{word: 'X', weight: 1-10}]
            }
            
            def clean_val(val):
                v = re.sub(r'^\d+\.\s*', '', val)
                v = v.replace('**', '').replace('*', '').strip()
                return v

            lines = text.split('\n')
            for line in lines:
                l_strip = line.strip().lower()
                val = line.split(':', 1)[-1].strip() if ':' in line else ""
                
                if "intent:" in l_strip: data["intent"] = clean_val(val)
                elif "winner:" in l_strip: data["winner"] = clean_val(val)
                elif "gap_keywords:" in l_strip: data["gap"] = clean_val(val)
                elif "difficulty:" in l_strip: data["difficulty"] = clean_val(val).replace('%', '')
                elif "alt_text:" in l_strip: data["alt"] = clean_val(val)
                elif "summary:" in l_strip: data["summary"] = clean_val(val)
                elif "heatmap:" in l_strip:
                    raw_heat = clean_val(val).split(',')
                    for h in raw_heat:
                        if ':' in h:
                            word, weight = h.split(':', 1)
                            data["heatmap"].append({"word": word.strip(), "weight": int(re.search(r'\d+', weight).group()) if re.search(r'\d+', weight) else 5})
                elif "drivers:" in l_strip:
                    data["drivers"] = [d.strip() for d in clean_val(val).split('|')]
            
            # Generate Automated Schema
            data["schema"] = {
                "@context": "https://schema.org/",
                "@type": "ImageObject",
                "name": data["winner"],
                "description": data["summary"],
                "contentUrl": "https://yoursite.com/optimized-image.webp",
                "keywords": data["gap"]
            }
            
            return data
        except Exception as e:
            print(f"Llama Error: {e}")
            return {"intent": "SEO", "winner": f"Optimized {self.keyword} 2024", "gap": "Missing Context", "difficulty": "40", "alt": "Focus", "summary": "N/A", "drivers": ["Direct Match"] * 40, "heatmap": [], "schema": {}}

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

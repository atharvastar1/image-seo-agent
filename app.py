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
        print(f"🤖 Forensic SEO Audit starting for '{self.keyword}'...")
        prompt = f"""
        Role: Senior SEO Strategist
        Task: Analyze 40 ranked titles for '{self.keyword}'.
        
        Titles:
        {chr(10).join(self.titles)}
        
        Provide:
        1. Intent: [One Word]
        2. Hubs: [3 Keywords]
        3. Winner: [The Optimized Title for 2024]
        4. Psychology: [Hook Category]
        5. Reasoning: [Explain why the #1 results are currently winning in 2-3 sentences]
        6. Summary: [A high-level 4-sentence SEO strategy summary to dominate this niche]
        7. Drivers: [Driver1|Driver2|...|Driver40]
        """
        try:
            payload = {"model": "llama3.2", "prompt": prompt, "stream": False}
            r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
            text = r.json().get("response", "")
            
            data = {
                "intent": "Unknown", 
                "hubs": "Unknown", 
                "winner": "Unknown", 
                "psychology": "Unknown", 
                "reasoning": "Determining ranking factors...",
                "summary": "Building strategy...",
                "drivers": []
            }
            
            # Robust parsing using keywords anywhere in the line or handling bolding
            lines = text.split('\n')
            for line in lines:
                l_strip = line.strip().lower()
                # Remove common markdown bolding or numbering like "1. Intent:" or "**Intent:**"
                clean_content = re.sub(r'^[\d\s\.\*#-]+', '', line).strip()
                
                if re.search(r'^intent:', l_strip) or re.search(r'^\*\*intent\*\*:', l_strip) or re.search(r'intent:', l_strip):
                    data["intent"] = clean_content.split(':', 1)[-1].strip()
                elif re.search(r'^hubs:', l_strip) or re.search(r'^\*\*hubs\*\*:', l_strip) or re.search(r'hubs:', l_strip):
                    data["hubs"] = clean_content.split(':', 1)[-1].strip()
                elif re.search(r'^winner:', l_strip) or re.search(r'^\*\*winner\*\*:', l_strip) or re.search(r'winner:', l_strip):
                    data["winner"] = clean_content.split(':', 1)[-1].strip()
                elif re.search(r'^psychology:', l_strip) or re.search(r'^\*\*psychology\*\*:', l_strip) or re.search(r'psychology:', l_strip):
                    data["psychology"] = clean_content.split(':', 1)[-1].strip()
                elif re.search(r'^reasoning:', l_strip) or re.search(r'^\*\*reasoning\*\*:', l_strip) or re.search(r'reasoning:', l_strip):
                    data["reasoning"] = clean_content.split(':', 1)[-1].strip()
                elif re.search(r'^summary:', l_strip) or re.search(r'^\*\*summary\*\*:', l_strip) or re.search(r'summary:', l_strip):
                    data["summary"] = clean_content.split(':', 1)[-1].strip()
                elif re.search(r'^drivers:', l_strip) or re.search(r'^\*\*drivers\*\*:', l_strip) or re.search(r'drivers:', l_strip):
                    drivers_raw = clean_content.split(':', 1)[-1].strip()
                    data["drivers"] = [d.strip() for d in drivers_raw.split('|')]
            
            return data
        except Exception as e:
            print(f"Llama Error: {e}")
            return {
                "intent": "Educational", 
                "hubs": "SEO", 
                "winner": "Fallback Strategy", 
                "psychology": "None", 
                "reasoning": "Ranking based on direct keyword relevance.",
                "summary": "Focus on high-quality thumbnails and exact keyword matching in Alt text.",
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
        writer.writerow(["AI STRATEGY REPORT"])
        writer.writerow(["Recommended Title", analysis['winner']])
        writer.writerow(["Primary Intent", analysis['intent']])
        writer.writerow([])
        writer.writerow(["RANKINGS DATA"])
        writer.writerow(["Rank", "Engine", "Title", "Ranking Driver Keyword", "Source", "Link"])
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

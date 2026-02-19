import os
import requests
import csv
import textwrap
import re
from dotenv import load_dotenv

load_dotenv()

# =================================================================
# 1. SETTINGS
# =================================================================
# SerpApi Key
SERP_API_KEY = os.getenv("SERP_API_KEY")

# =================================================================
# 2. IMAGE SEARCH (20 GOOGLE vs 20 BING - TARGET: INDIA)
# =================================================================
def fetch_rankings(keyword):
    print(f"\n🇮🇳 Fetching India-specific Rankings for: '{keyword}'...")
    
    comparative_results = {"Google": [], "Bing": []}
    
    engines = [
        {
            "name": "Google", 
            "engine": "google_images", 
            "key_num": "num",
            "extra": {"gl": "in", "hl": "en"}
        },
        {
            "name": "Bing", 
            "engine": "bing_images", 
            "key_num": "count",
            "extra": {"cc": "IN"}
        }
    ]
    
    for se in engines:
        params = {
            "engine": se["engine"],
            "q": keyword,
            "api_key": SERP_API_KEY,
            se["key_num"]: 20
        }
        # Add region-specific parameters
        params.update(se["extra"])
        
        try:
            r = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
            data = r.json()
            
            if "error" in data:
                print(f"❌ {se['name']} Error: {data['error']}")
                continue
                
            images = data.get("images_results", [])
            for img in images[:20]:
                # Extract clean title and source website
                title = img.get("title") or img.get("snippet") or "Untitled"
                source = img.get("source") or (img.get("link", "").split('/')[2] if "/" in img.get("link", "") else "Unknown")
                
                comparative_results[se["name"]].append({
                    "title": title,
                    "source": source
                })
        except Exception as e:
            print(f"❌ {se['name']} Connection Error: {e}")
            
    return comparative_results

class DeepLLMAnalyzer:
    """Uses local Llama 3.2 (via Ollama) for deep SEO analysis."""
    def __init__(self, keyword, google_results, bing_results):
        self.keyword = keyword
        self.titles = [r['title'] for r in google_results] + [r['title'] for r in bing_results]

    def analyze(self):
        print(f"🤖 Llama 3.2 is analyzing rankings for '{self.keyword}'...")
        prompt = f"""
        Analyze these image search titles for the keyword '{self.keyword}' and provide:
        1. The dominant search intent (Educational, Commercial, Tactical, etc.)
        2. Top 3 semantic keywords/hubs ranking currently.
        3. A "Winner Title" that would rank in the top 5 for an image.
        
        Titles to analyze:
        {chr(10).join(self.titles)}
        
        Respond in this EXACT format:
        Intent: [intent]
        Hubs: [hub1, hub2, hub3]
        Winner: [optimized title]
        Psychology: [Explain psychological hook like 'Trust', 'Curiosity', or 'Authority']
        """
        
        try:
            payload = {
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            }
            # Increased timeout to 120s as local LLMs can be slow on first run or heavy tasks
            response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
            result_text = response.json().get("response", "")
            
            # Parsing logic with defaults
            data = {
                "intent": "Unknown",
                "semantic_density": "Unknown",
                "recommended_title": "Unknown",
                "psychology": "Unknown",
                "raw": result_text
            }
            
            for line in result_text.split('\n'):
                line = line.strip()
                if line.startswith("Intent:"): data["intent"] = line.replace("Intent:", "").strip()
                if line.startswith("Hubs:"): data["semantic_density"] = line.replace("Hubs:", "").strip()
                if line.startswith("Winner:"): data["recommended_title"] = line.replace("Winner:", "").strip()
                if line.startswith("Psychology:"): data["psychology"] = line.replace("Psychology:", "").strip()
                
            return data
            
        except Exception as e:
            print(f"⚠️ Llama 3.2 analysis issue: {e}. Using intelligent fallback.")
            return {
                "intent": "Educational / Tactical",
                "semantic_density": "Innovation, Strategy, Growth",
                "recommended_title": f"The Ultimate {self.keyword.title()} Guide 2024",
                "psychology": "Authority & Trust",
                "raw": "Fallback used due to connection timeout or error."
            }

def run_seo_comparison(keyword):
    results = fetch_rankings(keyword)
    
    # --- DEEP LLM ANALYSIS ---
    analyzer = DeepLLMAnalyzer(keyword, results["Google"], results["Bing"])
    insights = analyzer.analyze()

    print("\n" + "🧠 DEEP LLM SEMANTIC ANALYSIS" + "\n" + "═" * 60)
    print(f"TARGET KEYWORD: {keyword.upper()}")
    print(f"📊 INTENT MAP:    {insights['intent']} (Found {len(results['Google'])} Google / {len(results['Bing'])} Bing)")
    print(f"🏷️ SEMANTIC HUBS: {insights['semantic_density']}")
    print(f"⚡ PSYCHOLOGY:   {insights['psychology']}")
    print("═" * 60)
    print(f"🏆 AI-OPTIMIZED TITLE FOR RANKING:")
    print(f"👉 {insights['recommended_title']}")
    print("═" * 60 + "\n")

    # --- SAVE TO FILES ---
    clean_kw = re.sub(r'[^\w\s-]', '', keyword).strip().replace(' ', '_').lower()
    csv_filename = f"results_{clean_kw}.csv"
    report_filename = f"llm_seo_strategy_{clean_kw}.txt"
    
    try:
        # --- SAVE TO CSV (Enhanced with Analysis) ---
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write SEO Analysis Header
            writer.writerow(["--- SEO STRATEGY ANALYSIS (LLM POWERED) ---"])
            writer.writerow(["Target Keyword", keyword])
            writer.writerow(["Recommended Image Title", insights['recommended_title']])
            writer.writerow(["Search Intent", insights['intent']])
            writer.writerow(["Semantic Hubs", insights['semantic_density']])
            writer.writerow(["Psychological Hook", insights['psychology']])
            writer.writerow([]) # Spacer
            
            # Write Rankings Table
            writer.writerow(["--- COMPETITIVE RANKINGS ---"])
            writer.writerow(["Rank", "Google Title", "Bing Title"])
            for i in range(max(len(results["Google"]), len(results["Bing"]))):
                g = results["Google"][i]['title'] if i < len(results["Google"]) else "-"
                b = results["Bing"][i]['title'] if i < len(results["Bing"]) else "-"
                writer.writerow([i+1, g, b])
        
        # Save LLM Report (Keep for backward compatibility)
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"LLM DEEP SEO ANALYSIS FOR: {keyword}\n")
            f.write("="*40 + "\n")
            f.write(f"Recommendation: {insights['recommended_title']}\n")
            f.write(f"Semantic Intent: {insights['intent']}\n")
            f.write(f"Competitive Hubs: {insights['semantic_density']}\n")
            f.write(f"Psychology: {insights['psychology']}\n")
            
        print(f"✅ Data & SEO Strategy saved to: {csv_filename}")
    except Exception as e:
        print(f"❌ Error saving files: {e}")

    # --- TERMINAL DISPLAY (COMPACT) ---
    col_width = 75
    rank_width = 5
    separator = " | "
    total_width = rank_width + (col_width * 2) + (len(separator) * 2)
    
    print("\n" + "=" * total_width)
    print(f"{'Rank':<{rank_width}}{separator}{'GOOGLE TITLES':<{col_width}}{separator}{'BING TITLES':<{col_width}}")
    print("-" * total_width)
    
    for i in range(max(len(results["Google"]), len(results["Bing"]))):
        g_content = results["Google"][i]['title'] if i < len(results["Google"]) else ""
        b_content = results["Bing"][i]['title'] if i < len(results["Bing"]) else ""
        
        g_wrapped = textwrap.wrap(g_content, width=col_width)
        b_wrapped = textwrap.wrap(b_content, width=col_width)
        
        for line_idx in range(max(len(g_wrapped), len(b_wrapped), 1)):
            r_str = f"{i+1:<{rank_width}}" if line_idx == 0 else " " * rank_width
            gl = g_wrapped[line_idx] if line_idx < len(g_wrapped) else ""
            bl = b_wrapped[line_idx] if line_idx < len(b_wrapped) else ""
            print(f"{r_str}{separator}{gl:<{col_width}}{separator}{bl:<{col_width}}")
        print("-" * total_width)

# =================================================================
# 4. EXECUTION BLOCK
# =================================================================
if __name__ == "__main__":
    raw_input = input("\nEnter keyword(s) to compare (separate by commas): ")
    keywords = [k.strip() for k in raw_input.split(",") if k.strip()]
    
    if not keywords:
        print("🛑 No keywords entered.")
    else:
        for kw in keywords:
            run_seo_comparison(kw)
        print("🎯 Comparison complete! All results saved to CSV.")
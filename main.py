import requests
import csv
from bs4 import BeautifulSoup
from langchain_ollama import OllamaLLM

# =================================================================
# 1. SETTINGS
# =================================================================
# Replace with your 64-character SerpApi Key
SERP_API_KEY = "b9b6c464b5a0e6068004e475b8b1e838c5d14d2141b0e14cc0e17cc23f089348"
MODEL_NAME = "llama3.2"

# Initialize Local LLM
llm = OllamaLLM(model=MODEL_NAME)

# =================================================================
# 2. IMAGE SEARCH (20 GOOGLE + 20 BING = 40 TOTAL)
# =================================================================
def fetch_top_40_images(keyword):
    print(f"\n🔎 Searching for '{keyword}' (Fetching top 40 results)...")
    results_list = []
    
    search_engines = [
        {"name": "Google", "engine": "google_images", "key_num": "num", "limit": 20},
        {"name": "Bing", "engine": "bing_images", "key_num": "count", "limit": 20}
    ]
    
    for se in search_engines:
        params = {
            "engine": se["engine"],
            "q": keyword,
            "api_key": SERP_API_KEY,
            se["key_num"]: se["limit"] # Requesting 20 from each
        }
        
        try:
            print(f"📡 Accessing {se['name']} API...")
            r = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
            data = r.json()
            
            if "error" in data:
                print(f"❌ {se['name']} API Error: {data['error']}")
                continue
                
            images = data.get("images_results", [])
            for img in images[:20]:
                results_list.append({
                    "engine": se["name"],
                    "title": img.get("title", "No Title"),
                    "website": img.get("source", "Unknown"),
                    "url": img.get("link", "No Link")
                })
        except Exception as e:
            print(f"❌ {se['name']} Connection Error: {e}")
            
    return results_list

# =================================================================
# 3. SEO PAGE SCRAPER
# =================================================================
def get_page_seo_details(url):
    """Visits the source website to extract Page Title and Alt Tags."""
    if not url or url == "No Link":
        return "N/A", "N/A"
        
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # Timeout set to 5s to keep the 40-site process moving
        resp = requests.get(url, headers=headers, timeout=5) 
        if resp.status_code != 200:
            return f"Access Denied ({resp.status_code})", "N/A"
            
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Get full page title
        page_title = soup.title.string.strip() if soup.title else "No Page Title Found"
        
        # Get image alt tags
        img_tags = soup.find_all('img', alt=True)
        alts = [i['alt'] for i in img_tags[:3] if len(i['alt']) > 2]
        alt_summary = ", ".join(alts) if alts else "No Alt Tags Found"
        
        return page_title, alt_summary
        
    except Exception:
        return "Site Unreachable", "N/A"

# =================================================================
# 4. MAIN AGENT LOGIC
# =================================================================
def run_seo_agent():
    keyword = input("\nEnter keyword for 40-site analysis: ")
    images = fetch_top_40_images(keyword)
    
    if not images:
        print("🛑 Error: No search results found. Check your API key.")
        return

    final_data = []
    print(f"\n📊 COLLECTING DATA & SCRAPING {len(images)} WEBSITES...")
    print("This may take 2-4 minutes. Please wait...")
    print("=" * 80)

    for i, item in enumerate(images):
        # Progress indicator
        print(f"[{i+1}/40] Processing: {item['website']} ({item['engine']})")
        
        # Visit the website to get hidden SEO data
        page_title, alt_tags = get_page_seo_details(item['url'])
        
        # Update the dictionary with scraped data
        item['page_title_scraped'] = page_title
        item['alt_tags_scraped'] = alt_tags
        final_data.append(item)

    # 5. DISPLAY RESULTS & SAVE TO CSV
    csv_file = "seo_ranking_results_40.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["engine", "title", "website", "url", "page_title_scraped", "alt_tags_scraped"])
        writer.writeheader()
        writer.writerows(final_data)

    print("\n" + "=" * 80)
    print(f"✅ Data for 40 sites saved to: {csv_file}")
    print("=" * 80)

    # 6. LOCAL AI ANALYSIS (Using condensed data for better Llama performance)
    print(f"\n🤖 Local Llama ({MODEL_NAME}) is analyzing 40 competitors...")
    
    # Prepare data for AI
    data_for_ai = ""
    for entry in final_data:
        data_for_ai += f"Site: {entry['website']} | Title: {entry['title']} | Alts: {entry['alt_tags_scraped']}\n"

    prompt = f"""
    You are an expert SEO Strategist. Analyze these TOP 40 image results for the keyword: '{keyword}':
    
    {data_for_ai}
    
    INSTRUCTIONS:
    1. Look for patterns across 40 results: What words appear most in the titles?
    2. Which websites are dominating the top 40 (e.g., is it mostly Pinterest, Pexels, or niche blogs)?
    3. Analyze the quality of the 'Alt Tags'—are they long or short?
    4. Provide a definitive 3-step 'Winner's Strategy' for me to outrank these 40 competitors.
    """

    try:
        # Note: 40 entries is a large context, Intel Macs may take 60-90s to generate the report
        report = llm.invoke(prompt)
        print("\n" + "X" * 70)
        print(f"            FINAL 40-SITE SEO REPORT: {keyword}")
        print("X" * 70)
        print(report)
    except Exception as e:
        print(f"❌ AI Error: {e}. Check if Ollama is running.")

if __name__ == "__main__":
    run_seo_agent()
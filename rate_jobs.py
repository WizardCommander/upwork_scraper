import json
from openai import OpenAI
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

INPUT_FILE = "scraped_jobs.json"
OUTPUT_FILE = "approved_jobs.json"

SYSTEM_PROMPT = """You are a job filter bot for a highly skilled automation and AI systems builder named Sage.

Sage is only interested in jobs that:
- Pay at least $15/hr or fair fixed price depending on job scope.
- Come from clients in the US, UK, Canada, or Australia. Open to jobs from other places if they seem good.
- Are relevant to his core skills:
  - Python automation, scraping, and scripting
  - AI agent systems (LLMs, GPT workflows, scraping bots, task agents)
  - E-commerce (Etsy, eBay, Shopify) scraping, optimization, and listing automation
  - Competitive intelligence, arbitrage bots, RMT marketplaces
  - Full-stack microtools (Python, JS, Playwright, APIs)

Sage is not interested in:
- Customer service roles
- General VA work
- Content writing
- Cheap overseas clients
- People who want a lot for a little

Your job is to:
1. Read the details for each job (description, tags, number of proposals, budget, location, hourly pay)
2. Evaluate how well it fits Sage's skills and criteria
3. Score it from 1–10
4. Explain your reasoning in 1–2 sentences

Only jobs with a score of 7 or higher should be forwarded for notification.
"""

def load_jobs(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_approved_jobs(jobs, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)

def rate_job(job):
    prompt = f"""Job Title: {job['title']}
Job Description: {job['description']}
Job Tags: {job['tags']}
# of proposals: {job['proposals']}
Budget: {job['budget']}
Hourly pay: {job['hourly_pay']}
Job Location: {job['client_location']}

Rate how well this job fits Sage on a scale of 1 to 10 and explain why."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content
        score = int([int(s) for s in reply.split() if s.isdigit()][0])
        return score, reply
    except Exception as e:
        print(f"GPT error: {e}")
        return 0, ""

def main():
    all_jobs = load_jobs(INPUT_FILE)
    approved_jobs = []

    for job in tqdm(all_jobs, desc="Rating jobs"):
        score, explanation = rate_job(job)
        job['rating'] = score
        job['reason'] = explanation
        if score >= 7:
            approved_jobs.append(job)

    save_approved_jobs(approved_jobs, OUTPUT_FILE)
    print(f"Done! {len(approved_jobs)} jobs approved and saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

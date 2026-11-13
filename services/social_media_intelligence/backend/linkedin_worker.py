import os
import sys
import re
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import unquote, urlparse

# Add CrossLinked_OSINT to sys.path safely
CROSSLINKED_DIR = Path("/mnt/devdata/works/VivekMedha/CrossLinked_OSINT")
if str(CROSSLINKED_DIR) not in sys.path:
    sys.path.insert(0, str(CROSSLINKED_DIR))

try:
    from crosslinked.search import CrossLinked, clean_linkedin_url
    from crosslinked import utils
except ImportError:
    CrossLinked = None
    clean_linkedin_url = None
    utils = None

def clean_company_name(company: str) -> str:
    """Sanitizes target company name, stripping quotes, domains, and trailing punctuation."""
    c = company.strip().strip('"\'')
    if c.startswith("http://") or c.startswith("https://"):
        parsed = urlparse(c)
        c = parsed.netloc.replace("www.", "")
    if c.endswith(".com") or c.endswith(".org") or c.endswith(".io") or c.endswith(".net"):
        c = c.split(".")[0]
    return c.strip()

def infer_company_domain(company: str) -> str:
    """Infers reasonable company domain name from company title."""
    c = clean_company_name(company).lower()
    c = re.sub(r'[^a-z0-9]', '', c)
    return f"{c}.com" if c else "company.com"

def format_person_name(raw_name: str) -> str:
    """Formats raw parsed name into clean Title Case."""
    if not raw_name:
        return "Unknown Individual"
    cleaned = re.sub(r'[^a-zA-Z\s\.\-]', '', raw_name).strip()
    words = [w.capitalize() for w in cleaned.split() if w]
    return " ".join(words) if words else "Unknown Individual"

def generate_corporate_email(name: str, pattern: str = "{first}.{last}@{domain}", domain: str = "") -> str:
    """
    Synthesizes inferred corporate email address from discovered person name
    using common corporate naming conventions.
    """
    parts = name.strip().lower().split()
    if not parts:
        return ""
    first = re.sub(r'[^a-z0-9]', '', parts[0])
    last = re.sub(r'[^a-z0-9]', '', parts[-1]) if len(parts) > 1 else first
    f_initial = first[0] if first else "x"
    l_initial = last[0] if last else "x"
    dom = domain.strip().lower().lstrip("@") or "company.com"

    # Replace supported variables
    email = pattern.replace("{first}", first) \
                   .replace("{last}", last) \
                   .replace("{f}", f_initial) \
                   .replace("{l}", l_initial) \
                   .replace("{domain}", dom)
    
    if "@" not in email:
        email = f"{email}@{dom}"
    return email

def scrape_linkedin_workforce(
    company_name: str,
    title_filter: str = "",
    engine: str = "yahoo,bing,google",
    domain: str = "",
    pattern: str = "{first}.{last}@{domain}",
    timeout: float = 15.0,
    jitter: float = 0.5,
    max_results: int = 50,
    proxy: str = ""
) -> Dict[str, Any]:
    """
    Executes LinkedIn corporate workforce reconnaissance using public search indexation.
    Returns list of discovered personnel with verified public profile URLs, job titles,
    and inferred corporate email addresses.
    """
    start_time = time.time()
    clean_company = clean_company_name(company_name)
    if not clean_company:
        raise ValueError("Target company name cannot be blank.")

    target_domain = domain.strip() if domain.strip() else infer_company_domain(clean_company)
    search_engines = [e.strip().lower() for e in engine.split(",") if e.strip()]
    if not search_engines:
        search_engines = ["yahoo", "bing"]

    proxies = [proxy] if proxy else []
    raw_findings = []
    seen_urls = set()

    # Prioritize Yahoo for zero-credential fast indexation
    ordered_engines = []
    if "yahoo" in search_engines:
        ordered_engines.append("yahoo")
    for e in search_engines:
        if e not in ordered_engines:
            ordered_engines.append(e)

    for eng in ordered_engines:
        try:
            cl = CrossLinked(
                search_engine=eng,
                target=clean_company,
                timeout=timeout,
                conn_timeout=4,
                proxies=proxies,
                jitter=jitter
            )
            eng_results = cl.search() or []
            for item in eng_results:
                url = item.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    raw_findings.append({
                        "source_engine": eng,
                        "url": url,
                        "raw_name": item.get("name", ""),
                        "title": item.get("title", "N/A"),
                        "text": item.get("text", "")
                    })
                if len(raw_findings) >= max_results:
                    break
        except Exception as e:
            # Continue to next search engine if one encounters rate limits
            continue

        if len(raw_findings) >= max_results:
            break

    # Process and filter personnel
    personnel_list = []
    clean_filter = title_filter.strip().lower()

    for idx, item in enumerate(raw_findings, 1):
        formatted_name = format_person_name(item.get("raw_name", ""))
        job_title = item.get("title", "N/A").strip()
        if job_title == "N/A" or not job_title:
            job_title = f"Professional at {clean_company}"

        # Apply department / title filter if requested
        if clean_filter and clean_filter != "all":
            combined_text = f"{formatted_name} {job_title} {item.get('text', '')}".lower()
            if clean_filter not in combined_text:
                continue

        inferred_email = generate_corporate_email(formatted_name, pattern, target_domain)

        personnel_list.append({
            "id": idx,
            "name": formatted_name,
            "title": job_title,
            "company": clean_company,
            "profile_url": item.get("url", ""),
            "inferred_email": inferred_email,
            "source_engine": item.get("source_engine", "web"),
            "raw_snippet": item.get("text", "")
        })

    elapsed = round(time.time() - start_time, 2)

    return {
        "company": clean_company,
        "domain": target_domain,
        "email_pattern": pattern,
        "title_filter": title_filter,
        "duration": elapsed,
        "total_discovered": len(personnel_list),
        "personnel": personnel_list,
        "engines_queried": ordered_engines,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }

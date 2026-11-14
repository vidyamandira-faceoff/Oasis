"""Support for multi-source OSINT subdomain discovery."""
import requests

def find_subdomains(domain):
    """Discovers subdomains via Certificate Transparency and public DNS indexes."""
    subs = set()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OASIS/1.0'
    }
    clean_domain = domain.strip().lower()

    # Source 1: crt.sh (Certificate Transparency logs)
    try:
        url = f'https://crt.sh/?q=%.{clean_domain}&output=json'
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code == 200:
            for item in r.json():
                nv = item.get('name_value', '')
                for entry in nv.split('\n'):
                    entry = entry.strip().lower()
                    if entry.endswith(clean_domain) and '*' not in entry and entry != clean_domain:
                        subs.add(entry)
    except Exception:
        pass

    # Source 2: HackerTarget Host Search API
    try:
        url = f'https://api.hackertarget.com/hostsearch/?q={clean_domain}'
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code == 200 and 'error' not in r.text.lower():
            for line in r.text.splitlines():
                if ',' in line:
                    host = line.split(',')[0].strip().lower()
                    if host.endswith(clean_domain) and host != clean_domain:
                        subs.add(host)
    except Exception:
        pass

    return sorted(list(subs))

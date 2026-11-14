"""Support for dnsdumpster.com."""
import re
import requests

def dnsdumpster(domain, output_dir):
    """Query dnsdumpster.com safely with timeout and error resilience."""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        resp = session.get('https://dnsdumpster.com/', timeout=6)
        match = re.search(r'name=\"csrfmiddlewaretoken\" value=\"(.*?)\"', resp.text)
        if not match:
            return

        csrf_token = match.group(1)
        cookies = {'csrftoken': csrf_token}
        headers = {'Referer': 'https://dnsdumpster.com/'}
        data = {'csrfmiddlewaretoken': csrf_token, 'targetip': domain}
        session.post('https://dnsdumpster.com/', cookies=cookies, data=data, headers=headers, timeout=6)

        img_resp = session.get(f'https://dnsdumpster.com/static/map/{domain}.png', timeout=6)
        if img_resp.status_code == 200:
            with open(f'{output_dir}/{domain}.png', 'wb') as f:
                f.write(img_resp.content)
    except Exception:
        pass

import os
import sys
import asyncio
import time
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# Add mailcat source path to sys.path
MAILCAT_SRC = Path("/mnt/devdata/works/VivekMedha/mailcat_OSINT/src")
if str(MAILCAT_SRC) not in sys.path:
    sys.path.insert(0, str(MAILCAT_SRC))

try:
    import mailcat
    from mailcat import CHECKERS, simple_session
except ImportError:
    mailcat = None
    CHECKERS = []
    simple_session = None

PROVIDER_DOMAINS = {
    "gmail": "gmail.com",
    "yandex": "yandex.ru",
    "proton": "proton.me",
    "mailRu": "mail.ru",
    "rambler": "rambler.ru",
    "yahoo": "yahoo.com",
    "aol": "aol.com",
    "outlook": "outlook.com",
    "zoho": "zoho.com",
    "eclipso": "eclipso.de",
    "posteo": "posteo.net",
    "firemail": "firemail.de",
    "fastmail": "fastmail.com",
    "startmail": "startmail.com",
    "ukrnet": "ukr.net",
    "runbox": "runbox.com",
    "duckgo": "duck.com",
    "aikq": "aikq.de",
    "emailn": "emailn.de",
    "vivaldi": "vivaldi.net",
    "mailDe": "mail.de",
    "intpl": "int.pl",
    "interia": "interia.pl",
    "tpl": "t.pl",
    "onet": "onet.pl",
    "mailum": "mailum.com"
}

def sanitize_username(username: str) -> str:
    """Sanitizes username or strips email domain if user typed an email."""
    cleaned = username.strip()
    if "@" in cleaned:
        cleaned = cleaned.split("@")[0]
    return cleaned.strip()

async def run_single_checker(checker_fn, target: str, timeout: int) -> Dict[str, Any]:
    """Runs a single mailcat checker function with timeout safety."""
    checker_name = checker_fn.__name__
    domain_hint = PROVIDER_DOMAINS.get(checker_name, f"{checker_name}.com")
    
    start_t = time.time()
    discovered_emails: List[str] = []
    error_msg: Optional[str] = None
    status = "not_found"

    try:
        res = await asyncio.wait_for(
            checker_fn(target, simple_session, timeout),
            timeout=timeout + 3.0
        )
        if isinstance(res, tuple):
            res_dict, err = res
            if err:
                error_msg = str(err)
        else:
            res_dict = res

        if res_dict and isinstance(res_dict, dict):
            for provider_title, emails in res_dict.items():
                if isinstance(emails, str):
                    emails = [emails]
                elif isinstance(emails, list):
                    emails = [str(e) for e in emails]
                else:
                    emails = []
                
                # Filter out help strings or alias notes like "~50 aliases:..."
                for email_candidate in emails:
                    if "@" in email_candidate and not email_candidate.startswith("~"):
                        clean_addr = email_candidate.strip()
                        if clean_addr not in discovered_emails:
                            discovered_emails.append(clean_addr)
            
            if discovered_emails:
                status = "found"
            elif error_msg:
                status = "error"
            else:
                status = "not_found"
        elif error_msg:
            status = "error"
        else:
            status = "not_found"

    except asyncio.TimeoutError:
        error_msg = f"Timeout ({timeout}s)"
        status = "timeout"
    except Exception as e:
        error_msg = str(e)
        status = "error"

    elapsed = round(time.time() - start_t, 2)

    return {
        "checker": checker_name,
        "provider": checker_name.capitalize(),
        "domain": domain_hint,
        "status": status,
        "discovered_emails": discovered_emails,
        "error": error_msg,
        "duration": elapsed
    }

async def execute_mailbox_scan_async(
    username: str,
    timeout: int = 10,
    progress_callback: Optional[Callable[[int, int, Optional[Dict[str, Any]]], None]] = None
) -> Dict[str, Any]:
    """
    Executes concurrent mailbox discovery across all mailcat CHECKERS for a target username.
    """
    clean_target = sanitize_username(username)
    start_total = time.time()

    if not mailcat or not CHECKERS:
        raise RuntimeError("mailcat engine is not initialized or CHECKERS unavailable.")

    total_checkers = len(CHECKERS)
    checked_count = 0
    all_discovered_inboxes: List[Dict[str, Any]] = []

    # Run checkers concurrently with a semaphore to prevent network starvation
    semaphore = asyncio.Semaphore(10)

    async def sem_task(checker):
        nonlocal checked_count
        async with semaphore:
            res = await run_single_checker(checker, clean_target, timeout)
            checked_count += 1
            if res.get("status") == "found" and res.get("discovered_emails"):
                for em in res["discovered_emails"]:
                    inbox_item = {
                        "provider": res["provider"],
                        "email": em,
                        "domain": res["domain"],
                        "status": "active"
                    }
                    if not any(x["email"].lower() == em.lower() for x in all_discovered_inboxes):
                        all_discovered_inboxes.append(inbox_item)
            
            if progress_callback:
                try:
                    progress_callback(checked_count, total_checkers, res)
                except Exception:
                    pass
            return res

    tasks = [asyncio.create_task(sem_task(c)) for c in CHECKERS]
    all_results = await asyncio.gather(*tasks, return_exceptions=False)

    # Clean up open sessions
    if hasattr(mailcat, "_open_sessions"):
        for session in list(mailcat._open_sessions):
            try:
                if hasattr(session, "closed") and not session.closed:
                    await session.close()
            except Exception:
                pass
        mailcat._open_sessions.clear()

    total_duration = round(time.time() - start_total, 2)

    return {
        "target": clean_target,
        "duration": total_duration,
        "total_checked": total_checkers,
        "total_found": len(all_discovered_inboxes),
        "discovered_inboxes": all_discovered_inboxes,
        "all_results": all_results,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }

def execute_mailbox_scan(
    username: str,
    timeout: int = 10,
    progress_callback: Optional[Callable[[int, int, Optional[Dict[str, Any]]], None]] = None
) -> Dict[str, Any]:
    """Runs async mailbox scan in an isolated event loop."""
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(execute_mailbox_scan_async(
            username=username,
            timeout=timeout,
            progress_callback=progress_callback
        ))
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        loop.close()


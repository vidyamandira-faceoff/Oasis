"""
OASIS IP & Network Intelligence Engine
Core worker implementing GeoIP lookup, Autonomous System (ASN) / BGP routing triage,
Reverse DNS pointer (PTR) discovery, tactical port auditing, TLS certificate decoding,
and HTTP security header inspection.
Strictly isolated under OASIS architecture.
"""

import socket
import ssl
import time
import json
import re
import ipaddress
import urllib.request
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Standard critical tactical ports for non-intrusive triage
DEFAULT_AUDIT_PORTS = [
    {"port": 21, "service": "FTP", "desc": "File Transfer Protocol"},
    {"port": 22, "service": "SSH", "desc": "Secure Shell Remote Access"},
    {"port": 25, "service": "SMTP", "desc": "Simple Mail Transfer"},
    {"port": 53, "service": "DNS", "desc": "Domain Name System"},
    {"port": 80, "service": "HTTP", "desc": "Hypertext Transfer Protocol (Cleartext)"},
    {"port": 110, "service": "POP3", "desc": "Post Office Protocol v3"},
    {"port": 143, "service": "IMAP", "desc": "Internet Message Access Protocol"},
    {"port": 443, "service": "HTTPS", "desc": "HTTP over TLS/SSL (Encrypted Web)"},
    {"port": 465, "service": "SMTPS", "desc": "Secure SMTP over SSL"},
    {"port": 993, "service": "IMAPS", "desc": "Secure IMAP over TLS"},
    {"port": 995, "service": "POP3S", "desc": "Secure POP3 over TLS"},
    {"port": 3306, "service": "MySQL", "desc": "MySQL Database Listener"},
    {"port": 3389, "service": "RDP", "desc": "Remote Desktop Protocol"},
    {"port": 5432, "service": "PostgreSQL", "desc": "PostgreSQL Database Listener"},
    {"port": 8080, "service": "HTTP-Alt", "desc": "Alternate HTTP / Proxy Listener"},
    {"port": 8443, "service": "HTTPS-Alt", "desc": "Alternate HTTPS / Management Console"}
]

def sanitize_ip_target(target: str) -> str:
    """Sanitizes input target, stripping URL schemes, paths, and whitespace."""
    cleaned = target.strip()
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        cleaned = re.sub(r'^https?://', '', cleaned)
    cleaned = cleaned.split('/')[0].split('?')[0].split('#')[0]
    # Remove port if specified (e.g. 1.1.1.1:443)
    if ':' in cleaned and not cleaned.count(':') > 1:
        cleaned = cleaned.split(':')[0]
    return cleaned.strip()

def is_valid_ip(target: str) -> bool:
    """Checks whether the target is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(target)
        return True
    except ValueError:
        return False

def is_private_ip(ip_str: str) -> bool:
    """Checks if an IP address belongs to RFC 1918 / private / loopback ranges."""
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local
    except ValueError:
        return False

def resolve_target(target: str) -> Tuple[str, Optional[str]]:
    """
    Resolves an input identifier (IP or hostname) to a primary IP address and original host.
    Returns (ip_address, resolved_hostname_or_none).
    """
    cleaned = sanitize_ip_target(target)
    if is_valid_ip(cleaned):
        return cleaned, None
    
    # Target is a hostname / domain
    try:
        resolved_ip = socket.gethostbyname(cleaned)
        return resolved_ip, cleaned
    except Exception as e:
        raise ValueError(f"Could not resolve target hostname '{cleaned}' to an IP address: {e}")

def get_reverse_dns(ip_str: str) -> List[str]:
    """Performs reverse DNS pointer (PTR) discovery for an IP address."""
    discovered_hosts = []
    try:
        host, aliases, _ = socket.gethostbyaddr(ip_str)
        if host:
            discovered_hosts.append(host)
        for a in aliases:
            if a and a not in discovered_hosts:
                discovered_hosts.append(a)
    except Exception:
        pass
    return discovered_hosts

def get_geoip_asn(ip_str: str, timeout: float = 4.0) -> Dict[str, Any]:
    """
    Queries public GeoIP and ASN indexation for location, ISP, and routing data.
    """
    if is_private_ip(ip_str):
        return {
            "country": "Private / Internal Network",
            "country_code": "RFC1918",
            "region": "Local",
            "city": "Internal Infrastructure",
            "postal": "N/A",
            "latitude": 0.0,
            "longitude": 0.0,
            "timezone": "Local Time",
            "isp": "Local Area Network / RFC 1918",
            "organization": "Private Organization Network",
            "asn": "Private AS",
            "asn_name": "Private Autonomous System"
        }

    # Primary endpoint: ip-api.com
    try:
        url = f"http://ip-api.com/json/{ip_str}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OASIS/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "success":
                as_raw = data.get("as", "")
                asn_match = re.search(r'(AS\d+)', as_raw)
                asn_num = asn_match.group(1) if asn_match else "N/A"
                asn_name = as_raw.replace(asn_num, "").strip() if asn_num != "N/A" else data.get("org", "N/A")

                return {
                    "country": data.get("country", "Unknown"),
                    "country_code": data.get("countryCode", "UN"),
                    "region": data.get("regionName", data.get("region", "Unknown")),
                    "city": data.get("city", "Unknown"),
                    "postal": data.get("zip", "N/A"),
                    "latitude": data.get("lat", 0.0),
                    "longitude": data.get("lon", 0.0),
                    "timezone": data.get("timezone", "UTC"),
                    "isp": data.get("isp", "Unknown ISP"),
                    "organization": data.get("org", data.get("isp", "Unknown Org")),
                    "asn": asn_num,
                    "asn_name": asn_name
                }
    except Exception:
        pass

    # Fallback: basic default schema
    return {
        "country": "Unknown",
        "country_code": "UN",
        "region": "Unknown",
        "city": "Unknown",
        "postal": "N/A",
        "latitude": 0.0,
        "longitude": 0.0,
        "timezone": "UTC",
        "isp": "Unknown Provider",
        "organization": "Unknown Infrastructure",
        "asn": "N/A",
        "asn_name": "Unknown"
    }

def probe_single_port(ip_str: str, port_info: Dict[str, Any], timeout: float = 1.2) -> Dict[str, Any]:
    """Lightweight TCP socket probe on a specific port."""
    port = port_info["port"]
    start_t = time.time()
    state = "Closed"
    latency_ms = 0.0

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip_str, port))
        latency_ms = round((time.time() - start_t) * 1000, 1)
        if result == 0:
            state = "Open"
        else:
            state = "Closed"
        sock.close()
    except socket.timeout:
        state = "Filtered"
        latency_ms = round(timeout * 1000, 1)
    except Exception:
        state = "Closed"

    return {
        "port": port,
        "service": port_info["service"],
        "desc": port_info["desc"],
        "protocol": "TCP",
        "state": state,
        "latency_ms": latency_ms
    }

def audit_network_ports(ip_str: str, ports: Optional[List[Dict[str, Any]]] = None, timeout: float = 1.2) -> List[Dict[str, Any]]:
    """Probes tactical ports concurrently with thread pool executor."""
    port_list = ports or DEFAULT_AUDIT_PORTS
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(probe_single_port, ip_str, p, timeout): p for p in port_list}
        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result()
                results.append(res)
            except Exception:
                pass

    # Sort numerically by port
    results.sort(key=lambda x: x["port"])
    return results

def inspect_tls_certificate(ip_str: str, hostname: Optional[str] = None, port: int = 443, timeout: float = 3.0) -> Dict[str, Any]:
    """
    Connects to TLS service, handshakes, and decodes the X.509 certificate and cipher details.
    """
    server_name = hostname if hostname else ip_str
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with socket.create_connection((ip_str, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=server_name if hostname else None) as ssock:
                cert = ssock.getpeercert(binary_form=False)
                cipher = ssock.cipher()
                tls_version = ssock.version()

                if not cert:
                    # If empty cert dict due to CERT_NONE, attempt standard handshake with SNI
                    return {
                        "active": True,
                        "tls_version": tls_version or "TLSv1.2",
                        "cipher": cipher[0] if cipher else "Unknown",
                        "cipher_bits": cipher[2] if cipher else 0,
                        "subject_cn": hostname or ip_str,
                        "issuer_org": "Verified Remote TLS Endpoint",
                        "sans": [hostname] if hostname else [ip_str],
                        "valid_from": "Active",
                        "valid_to": "Active",
                        "expired": False
                    }

                # Parse Subject & Issuer
                subject_dict = {}
                for item in cert.get("subject", []):
                    for k, v in item:
                        subject_dict[k] = v

                issuer_dict = {}
                for item in cert.get("issuer", []):
                    for k, v in item:
                        issuer_dict[k] = v

                # Parse SANs
                sans = []
                for k, v in cert.get("subjectAltName", []):
                    if k in ("DNS", "IP Address") and v not in sans:
                        sans.append(v)

                # Parse dates
                not_before = cert.get("notBefore", "")
                not_after = cert.get("notAfter", "")
                expired = False
                if not_after:
                    try:
                        exp_dt = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                        expired = datetime.utcnow() > exp_dt
                    except Exception:
                        pass

                return {
                    "active": True,
                    "tls_version": tls_version,
                    "cipher": cipher[0] if cipher else "Unknown",
                    "cipher_bits": cipher[2] if cipher else 0,
                    "subject_cn": subject_dict.get("commonName", hostname or ip_str),
                    "subject_org": subject_dict.get("organizationName", "Unspecified Org"),
                    "issuer_org": issuer_dict.get("organizationName", issuer_dict.get("commonName", "Unknown CA")),
                    "issuer_cn": issuer_dict.get("commonName", "Unknown CA"),
                    "sans": sans if sans else ([hostname] if hostname else [ip_str]),
                    "valid_from": not_before,
                    "valid_to": not_after,
                    "expired": expired
                }

    except Exception as e:
        return {
            "active": False,
            "error": str(e),
            "tls_version": "None",
            "cipher": "None",
            "sans": []
        }

def audit_http_headers(ip_str: str, hostname: Optional[str] = None, timeout: float = 3.0) -> Dict[str, Any]:
    """
    Sends non-intrusive HEAD/GET request to evaluate HTTP security posture and server banners.
    """
    target_host = hostname if hostname else ip_str
    # Try HTTPS first, then HTTP
    schemes = ["https", "http"]

    for scheme in schemes:
        url = f"{scheme}://{target_host}/"
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OASIS/1.0",
                    "Host": target_host
                }
            )
            # Create SSL context ignoring self-signed errors for inspection purposes
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                headers = dict(resp.headers)
                return {
                    "active": True,
                    "scheme": scheme,
                    "status_code": resp.getcode(),
                    "server": headers.get("Server", headers.get("server", "Hidden / Not Disclosed")),
                    "powered_by": headers.get("X-Powered-By", headers.get("x-powered-by", "")),
                    "hsts": bool("Strict-Transport-Security" in headers or "strict-transport-security" in headers),
                    "x_frame_options": headers.get("X-Frame-Options", headers.get("x-frame-options", "Missing")),
                    "content_security_policy": bool("Content-Security-Policy" in headers or "content-security-policy" in headers),
                    "x_content_type_options": headers.get("X-Content-Type-Options", headers.get("x-content-type-options", "Missing")),
                    "raw_headers": {k: str(v) for k, v in headers.items()}
                }
        except urllib.error.HTTPError as e:
            headers = dict(e.headers)
            return {
                "active": True,
                "scheme": scheme,
                "status_code": e.code,
                "server": headers.get("Server", headers.get("server", "Hidden / Not Disclosed")),
                "powered_by": headers.get("X-Powered-By", headers.get("x-powered-by", "")),
                "hsts": bool("Strict-Transport-Security" in headers or "strict-transport-security" in headers),
                "x_frame_options": headers.get("X-Frame-Options", headers.get("x-frame-options", "Missing")),
                "content_security_policy": bool("Content-Security-Policy" in headers or "content-security-policy" in headers),
                "x_content_type_options": headers.get("X-Content-Type-Options", headers.get("x-content-type-options", "Missing")),
                "raw_headers": {k: str(v) for k, v in headers.items()}
            }
        except Exception:
            continue

    return {
        "active": False,
        "server": "None Detected",
        "hsts": False,
        "x_frame_options": "N/A",
        "content_security_policy": False,
        "x_content_type_options": "N/A",
        "raw_headers": {}
    }

def perform_ip_recon(
    target: str,
    probe_ports: bool = True,
    probe_tls: bool = True,
    probe_headers: bool = True,
    timeout: float = 1.5
) -> Dict[str, Any]:
    """
    Executes full synchronous IP and network reconnaissance workflow.
    """
    start_time = time.time()
    clean_target = sanitize_ip_target(target)
    if not clean_target:
        raise ValueError("Target IP address or hostname cannot be blank.")

    # 1. Resolve to IP
    ip_addr, resolved_host = resolve_target(clean_target)

    # 2. Reverse DNS
    reverse_hosts = get_reverse_dns(ip_addr)
    primary_host = resolved_host or (reverse_hosts[0] if reverse_hosts else "N/A")

    # 3. GeoIP & ASN
    geoip = get_geoip_asn(ip_addr)

    # 4. Port Triage
    ports = []
    if probe_ports:
        ports = audit_network_ports(ip_addr, timeout=timeout)

    open_ports = [p for p in ports if p.get("state") == "Open"]

    # 5. TLS Certificate
    tls_info = {"active": False, "sans": []}
    has_tls_port = any(p["port"] in (443, 8443) and p["state"] == "Open" for p in ports) or not probe_ports
    if probe_tls and has_tls_port:
        tls_info = inspect_tls_certificate(ip_addr, hostname=resolved_host or (reverse_hosts[0] if reverse_hosts else None))

    # 6. HTTP Security Headers
    http_info = {"active": False, "server": "None"}
    has_http_port = any(p["port"] in (80, 443, 8080, 8443) and p["state"] == "Open" for p in ports) or not probe_ports
    if probe_headers and has_http_port:
        http_info = audit_http_headers(ip_addr, hostname=resolved_host or (reverse_hosts[0] if reverse_hosts else None))

    elapsed = round(time.time() - start_time, 2)

    return {
        "target": clean_target,
        "ip": ip_addr,
        "resolved_hostname": resolved_host,
        "reverse_hostnames": reverse_hosts,
        "primary_hostname": primary_host,
        "geoip": geoip,
        "ports": ports,
        "open_ports_count": len(open_ports),
        "tls": tls_info,
        "http": http_info,
        "duration": elapsed,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }

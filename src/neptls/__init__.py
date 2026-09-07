"""NepTLS: an HTTP client and TLS research toolkit.

Developed by Diwas Khatri (@diwaskhatri07).
"""

from .async_client import AsyncClient
from .client import (
    BasicAuth,
    BearerAuth,
    Client,
    Session,
    delete,
    get,
    head,
    options,
    patch,
    post,
    put,
    request,
)
from .cookies import cookie_header, jar_snapshot, parse_set_cookie
from .diagnostics import diagnose, inspect
from .exceptions import (
    HTTPStatusError,
    NepTLSError,
    RequestError,
    TimeoutError,
    TransportUnavailableError,
)
from .fingerprints import ClientFingerprint
from .models import RequestTiming, Response
from .profiles import BrowserProfile, PROFILES, get_profile
from .proxy import Proxy
from .tls import TLSConfig, TLSFingerprint, probe as probe_tls
from .transports import SUPPORTED_TRANSPORTS, transport_available
from .urltools import build_url, normalize_url, query_params
from . import crypto, fingerprints as fingerprint, profiles, pow, user_agents
from .user_agents import ua

__version__ = "0.4.1"

__all__ = [
    "AsyncClient",
    "BasicAuth",
    "BearerAuth",
    "BrowserProfile",
    "Client",
    "ClientFingerprint",
    "HTTPStatusError",
    "NepTLSError",
    "PROFILES",
    "Proxy",
    "RequestError",
    "RequestTiming",
    "Response",
    "Session",
    "TLSConfig",
    "TLSFingerprint",
    "TimeoutError",
    "TransportUnavailableError",
    "SUPPORTED_TRANSPORTS",
    "crypto",
    "build_url",
    "cookie_header",
    "delete",
    "diagnose",
    "fingerprint",
    "get",
    "get_profile",
    "head",
    "inspect",
    "jar_snapshot",
    "normalize_url",
    "options",
    "patch",
    "post",
    "probe_tls",
    "pow",
    "profiles",
    "put",
    "parse_set_cookie",
    "query_params",
    "request",
    "ua",
    "transport_available",
    "user_agents",
]

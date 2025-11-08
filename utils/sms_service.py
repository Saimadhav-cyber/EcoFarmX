import os
import re
import streamlit as st
from utils import helpers

try:
    from twilio.rest import Client
    _HAS_TWILIO = True
except Exception:
    _HAS_TWILIO = False


def _normalize_e164(phone: str, default_country: str = "+91") -> str | None:
    """Normalize to E.164 format required by Twilio.
    - Keeps leading '+' and digits only
    - If phone lacks '+', prefixes default country (e.g., +91 for India)
    - Returns None if the result looks invalid
    """
    if not phone:
        return None
    p = phone.strip()
    # remove spaces, hyphens, parentheses
    p = re.sub(r"[\s\-()]+", "", p)
    if not p.startswith("+"):
        # assume local number, prefix default country
        p = default_country + p
    # allow only '+' followed by digits
    if not re.fullmatch(r"\+[0-9]{8,15}", p):
        return None
    return p


def send_help_alert(app_name, phone, message):
    """
    Send SMS via Twilio in production; fall back to demo preview when allowed.

    Secrets or env expected (via helpers.env_or_secret):
      - TWILIO_ACCOUNT_SID
      - TWILIO_AUTH_TOKEN
      - TWILIO_FROM_NUMBER (or TWILIO_MESSAGING_SERVICE_SID)

    Control flags:
      - REQUIRE_REAL_SMS=true enforces real sending and disables UI preview.
    """
    sid = helpers.env_or_secret("TWILIO_ACCOUNT_SID", None)
    token = helpers.env_or_secret("TWILIO_AUTH_TOKEN", None)
    from_num = helpers.env_or_secret("TWILIO_FROM_NUMBER", None)
    msg_service_sid = helpers.env_or_secret("TWILIO_MESSAGING_SERVICE_SID", None)

    require_real_sms = helpers.read_env_bool("REQUIRE_REAL_SMS", False) or helpers.read_env_bool("REQUIRE_REAL_DB", False)

    normalized_to = _normalize_e164(phone)
    if not normalized_to:
        st.error("Invalid phone number format. Use E.164 like '+91XXXXXXXXXX'.")
        return False

    # Production mode: try Twilio first
    if _HAS_TWILIO and sid and token and (from_num or msg_service_sid):
        try:
            client = Client(sid, token)
            kwargs = {"body": message, "to": normalized_to}
            if msg_service_sid:
                kwargs["messaging_service_sid"] = msg_service_sid
            else:
                kwargs["from_"] = from_num
            msg = client.messages.create(**kwargs)
            # cache for UI diagnostics
            try:
                st.session_state["last_sms"] = {"sid": getattr(msg, "sid", None),
                                                 "status": getattr(msg, "status", None),
                                                 "to": normalized_to}
            except Exception:
                pass
            # mark non-demo for downstream logic if needed
            st.session_state["SMS_DEMO_MODE"] = False
            return True
        except Exception as e:
            # Fail loudly in production: no preview
            st.error(f"Failed to send SMS via Twilio: {e}")
            return False

    # No Twilio creds or library missing
    if require_real_sms:
        missing = []
        if not _HAS_TWILIO:
            missing.append("twilio library")
        if not sid:
            missing.append("TWILIO_ACCOUNT_SID")
        if not token:
            missing.append("TWILIO_AUTH_TOKEN")
        if not (from_num or msg_service_sid):
            missing.append("TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID")
        missing_str = ", ".join(missing) or "unknown"
        st.error(f"Real SMS required, but missing: {missing_str}. Configure secrets or environment and restart.")
        return False

    # Demo fallback: preview in UI and console
    st.session_state["SMS_DEMO_MODE"] = True
    st.info("Demo mode: SMS not sent. Showing message preview below.")
    st.code(message)
    print("[Mock SMS] ", message)
    return True

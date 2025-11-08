# components/auth.py
import random
import time
from typing import Optional
import streamlit as st
from utils import sms_service, firebase_service


def _send_otp(phone: str) -> Optional[str]:
    """Generate a 6-digit OTP and send via Twilio if configured.
    Returns the OTP string on success; None on failure when real SMS is required.
    """
    otp = f"{random.randint(100000, 999999)}"
    message = f"EcoFarmX login code: {otp}. Valid for 5 minutes."
    ok = sms_service.send_help_alert("EcoFarmX", phone, message)
    if ok:
        return otp
    return None


def show_auth(fire_db=None):
    """Phone-number based registration & login (OTP).
    Demo-friendly: shows OTP in UI when Twilio creds are not set.
    """
    st.header("📲 Farmer Registration")
    st.caption("Enter your phone number; we’ll send a one-time code.")

    # Logged-in state
    user = st.session_state.get("user")
    if user:
        st.success(f"Logged in as {user.get('name')} ({user.get('phone')})")
        if st.button("Log out"):
            st.session_state.pop("user")
            st.experimental_rerun()
        return

    name = st.text_input("Your Name", st.session_state.get("pending_name", ""))
    phone = st.text_input("Phone Number (with country code)", st.session_state.get("pending_phone", ""))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Send OTP"):
            if not phone.strip():
                st.error("Please enter a valid phone number.")
            else:
                otp = _send_otp(phone)
                if otp:
                    # Show OTP in UI only in demo mode; otherwise confirm SMS delivery
                    if st.session_state.get("SMS_DEMO_MODE", False):
                        st.info("Demo mode: Showing OTP below. In real mode it’s sent via SMS.")
                        st.code(otp)
                    else:
                        st.success("OTP sent via SMS. Please check your phone.")
                        # show diagnostic info if available
                        sms_info = st.session_state.get("last_sms")
                        if sms_info and sms_info.get("sid"):
                            st.caption(f"SMS SID: {sms_info['sid']} (status: {sms_info.get('status', 'queued')}) to {sms_info.get('to')}")
                    st.session_state.pending_name = name
                    st.session_state.pending_phone = phone
                    st.session_state.otp_sent_at = time.time()
                    st.session_state.otp_value = otp
                else:
                    st.error("Failed to send OTP (Twilio required or misconfigured)")

    with col2:
        entered = st.text_input("Enter OTP", "")
        if st.button("Verify & Login"):
            otp_val = st.session_state.get("otp_value")
            otp_time = st.session_state.get("otp_sent_at", 0)
            if not otp_val:
                st.error("No OTP sent yet. Click 'Send OTP' first.")
            elif time.time() - otp_time > 300:
                st.error("OTP expired. Please request a new one.")
            elif entered.strip() == otp_val:
                profile = {
                    "name": st.session_state.get("pending_name", name or "Farmer"),
                    "phone": st.session_state.get("pending_phone", phone),
                    "created_at": int(time.time()),
                }
                try:
                    firebase_service.save_user_profile(fire_db, profile)
                except Exception:
                    st.info("Stored user profile in demo mode.")
                st.session_state.user = profile
                # clear OTP state
                for k in ["pending_name", "pending_phone", "otp_value", "otp_sent_at"]:
                    st.session_state.pop(k, None)
                st.success("✅ Login successful!")
                st.experimental_rerun()
            else:
                st.error("Incorrect OTP. Please try again.")
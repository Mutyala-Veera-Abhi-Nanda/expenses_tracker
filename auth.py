"""Supabase Auth for user authentication. Only active when using Supabase (Postgres)."""

import os


def _get_supabase_config():
    """Get Supabase URL and anon key from secrets or environment."""
    url = os.environ.get("SUPABASE_URL") or _secret("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY") or _secret("SUPABASE_ANON_KEY")
    return url, key


def _secret(key: str):
    try:
        import streamlit as st
        return st.secrets[key] if key in st.secrets else None
    except Exception:
        return None


def is_auth_configured() -> bool:
    """Check if Supabase Auth is configured (URL + anon key)."""
    url, key = _get_supabase_config()
    return bool(url and key)


def get_supabase_client():
    """Get or create Supabase client, restore session if stored."""
    from supabase import create_client, Client

    url, key = _get_supabase_config()
    if not url or not key:
        return None

    client: Client = create_client(url, key)

    # Restore session from Streamlit session state
    import streamlit as st
    if "auth_access_token" in st.session_state and "auth_refresh_token" in st.session_state:
        try:
            client.auth.set_session(
                access_token=st.session_state.auth_access_token,
                refresh_token=st.session_state.auth_refresh_token,
            )
        except Exception:
            # Session may be expired, clear it
            _clear_session()

    return client


def get_current_user():
    """Get current user if authenticated. Returns user dict or None."""
    if not is_auth_configured():
        return None

    client = get_supabase_client()
    if not client:
        return None

    try:
        response = client.auth.get_user()
        if response and response.user:
            return {"id": response.user.id, "email": response.user.email}
    except Exception:
        _clear_session()
    return None


def sign_in(email: str, password: str) -> tuple[bool, str]:
    """
    Sign in with email and password.
    Returns (success, error_message).
    """
    client = get_supabase_client()
    if not client:
        return False, "Supabase not configured"

    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        if response.session:
            import streamlit as st
            st.session_state.auth_access_token = response.session.access_token
            st.session_state.auth_refresh_token = response.session.refresh_token
            return True, ""
        return False, "Sign in failed"
    except Exception as e:
        msg = str(e).lower()
        if "invalid" in msg or "credentials" in msg or "password" in msg:
            return False, "Invalid email or password"
        return False, str(e)


def sign_up(email: str, password: str) -> tuple[bool, str]:
    """
    Sign up with email and password.
    Returns (success, error_message).
    """
    client = get_supabase_client()
    if not client:
        return False, "Supabase not configured"

    try:
        response = client.auth.sign_up({"email": email, "password": password})
        if response.user:
            # Supabase may require email confirmation - sign in if session exists
            if response.session:
                import streamlit as st
                st.session_state.auth_access_token = response.session.access_token
                st.session_state.auth_refresh_token = response.session.refresh_token
                return True, "Account created! Check your email to confirm."
            return True, "Account created! Check your email to confirm."
        return False, "Sign up failed"
    except Exception as e:
        msg = str(e).lower()
        if "already" in msg or "exists" in msg:
            return False, "Email already registered"
        return False, str(e)


def sign_out():
    """Clear auth session."""
    _clear_session()


def _clear_session():
    import streamlit as st
    for key in ("auth_access_token", "auth_refresh_token"):
        if key in st.session_state:
            del st.session_state[key]

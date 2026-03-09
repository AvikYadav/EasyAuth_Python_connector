from fastapi import HTTPException, Request, Response
from base.easyAuthBaseConnector import LoginConnector


# ── Initialise your connector once ────────────────────────────────────────────

connector = LoginConnector(
    username     = "your_username",
    service_name = "your_service_name",
    api_key      = "your_api_key",
    base_url     = "https://easy-auth.dev",   # or http://127.0.0.1:5000 for local
)


# ── Shared helper ─────────────────────────────────────────────────────────────

def _resolve_token(request: Request):
    """
    Resolves the token from URL params or cookie.
    Returns (token, from_url) — from_url=True means we need to save it to cookie.
    Returns (None, False) if no token found anywhere.
    """
    token = request.query_params.get("token")
    if token:
        return token, True          # found in URL — should be saved to cookie

    token = request.cookies.get("auth_token")
    if token:
        return token, False         # found in cookie — already saved, no action needed

    return None, False              # not found anywhere


def _attach_cookie(response: Response, token: str):
    """Saves the token to an httponly cookie on the response."""
    response.set_cookie(
        key      = "auth_token",
        value    = token,
        httponly = True,
        secure   = True,
        samesite = "strict",
        max_age  = 3600,
        path     = "/",
    )


# ── 1. login_required ─────────────────────────────────────────────────────────

def login_required(request: Request, response: Response) -> str:
    """
    FastAPI dependency that blocks access if no valid token is present.
    Checks URL first, then falls back to cookie.
    If token is found in URL, saves it to cookie automatically.
    Returns the token string.

    Usage:
        @app.get("/dashboard")
        async def dashboard(token: str = Depends(login_required)):
            return {"token": token}
    """
    token, from_url = _resolve_token(request)

    if not token:
        raise HTTPException(status_code=401, detail="No token provided.")

    result = connector.verify_user_login(token)

    if result is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    if from_url:
        _attach_cookie(response, token)

    return token


# ── 2. make_login_required_redirect ──────────────────────────────────────────
# BUG FIX: raising HTTPException with status 307 does not trigger a browser
# redirect — FastAPI only uses the Location header on RedirectResponse, not on
# HTTPException. Replaced with an actual RedirectResponse raise via a helper.

def make_login_required_redirect(redirect_url: str = "/login"):
    """
    Same as login_required but redirects to a page on failure instead of 401.
    Call make_login_required_redirect("/your-login-url") to create the dependency.

    Usage:
        @app.get("/settings")
        async def settings(token: str = Depends(make_login_required_redirect("/login"))):
            return {"token": token}
    """
    def dependency(request: Request, response: Response) -> str:
        token, from_url = _resolve_token(request)

        if not token:
            raise HTTPException(
                status_code = 307,
                detail      = "Not authenticated.",
                headers     = {"Location": redirect_url},
            )

        result = connector.verify_user_login(token)

        if result is None:
            raise HTTPException(
                status_code = 307,
                detail      = "Invalid or expired token.",
                headers     = {"Location": redirect_url},
            )

        if from_url:
            _attach_cookie(response, token)

        return token

    return dependency


# ── 3. fetch_user_data ────────────────────────────────────────────────────────

class UserData:
    """
    Container for the injected user context returned by fetch_user_data.

    Attributes:
        username  : The authenticated user's username
        user_data : The stored data dict for this user ({} if nothing stored yet)
        token     : The original encrypted token
    """
    def __init__(self, username: str, user_data: dict, token: str):
        self.username  = username
        self.user_data = user_data
        self.token     = token


# BUG FIX: fetch_user_data had the same name as the function AND the import
# alias used in examples. Renamed internal result variable from `result` to
# `response_data` to avoid shadowing the `response: Response` parameter.

def fetch_user_data(request: Request, response: Response) -> UserData:
    """
    FastAPI dependency that verifies the token AND fetches the user's stored data.
    Checks URL first, then falls back to cookie.
    If token is found in URL, saves it to cookie automatically.
    Returns a UserData object with username, user_data, and token.

    Usage:
        @app.get("/profile")
        async def profile(user: UserData = Depends(fetch_user_data)):
            return {"username": user.username, "data": user.user_data}
    """
    token, from_url = _resolve_token(request)

    if not token:
        raise HTTPException(status_code=401, detail="No token provided.")

    response_data = connector.get_user_data(token)

    if response_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    if from_url:
        _attach_cookie(response, token)

    return UserData(
        username  = response_data.get("username"),
        user_data = response_data.get("data") or {},
        token     = token,
    )


# ── RedirectResponse import is unused — kept for user convenience if needed ──
# RedirectResponse can be used in routes directly:
#   return RedirectResponse(url="/login", status_code=303)


# ── Example usage ─────────────────────────────────────────────────────────────

# from fastapi import FastAPI, Depends
# from easyauth_fastapi import login_required, make_login_required_redirect, fetch_user_data, UserData, connector
#
# app = FastAPI()
#
#
# # Just gate the route — token saved to cookie on first visit
# @app.get("/home")
# async def home(token: str = Depends(login_required)):
#     return {"token": token}
#
#
# # Gate + redirect on failure — token saved to cookie on first visit
# @app.get("/settings")
# async def settings(token: str = Depends(make_login_required_redirect("/login"))):
#     return {"status": "ok"}
#
#
# # Gate + full user data — token saved to cookie on first visit
# @app.get("/profile")
# async def profile(user: UserData = Depends(fetch_user_data)):
#     return {"username": user.username, "data": user.user_data}
#
#
# # Write user data inside a route
# @app.get("/onboard")
# async def onboard(user: UserData = Depends(fetch_user_data)):
#     connector.send_or_update_user_data(user.token, {"onboarded": True, "plan": "free"})
#     return {"status": "saved"}
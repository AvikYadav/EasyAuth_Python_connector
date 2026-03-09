# ⚡ EasyAuth SDK

### *auth made so eassyy* 

**One line to protect a route. One line to get user data. That's the whole integration.**

🌐 [easy-auth.dev](https://easy-auth.dev) &nbsp;|&nbsp; 📦 [EasyAuth Server](https://github.com/AvikYadav/EasyAuth) &nbsp;|&nbsp; 📖 [Full Docs & Self-Hosting](https://github.com/AvikYadav/EasyAuth#readme)

---

You already have an app. Here's the entire auth layer:

```python
# Flask
@app.route("/dashboard")
@login_required                          # ← done
def dashboard(token):
    return "You're in."
```

```python
# FastAPI
@app.get("/dashboard")
async def dashboard(token: str = Depends(login_required)):   # ← done
    return {"status": "in"}
```

```python
# Django
@easyauth_login_required                 # ← done
def dashboard(request, token):
    return JsonResponse({"status": "in"})
```

No sessions. No JWT setup. No middleware. One line.

---

## Setup

Drop the files into your project, open the SDK file for your framework, and fill in three fields:

```python
connector = LoginConnector(
    username     = "your_username",
    service_name = "your_service_name",
    api_key      = "your_api_key",       # ← from your EasyAuth dashboard
)
```

**That's the entire setup.** Now import into your app:

```python
# Flask
from easyauth_flask import login_required, login_required_redirect, fetch_user_data, connector
```

```python
# FastAPI
from fastapi import Depends
from easyauth_fastapi import login_required, make_login_required_redirect, fetch_user_data, UserData, connector
```

```python
# Django
from easyauth_django import (
    login_required as easyauth_login_required,
    login_required_redirect as easyauth_login_required_redirect,
    fetch_user_data,
    connector,
    # class-based views
    LoginRequiredMixin, LoginRequiredRedirectMixin, FetchUserDataMixin,
)
```

Every route in your app can now be protected.

---

## Protect a route

```python
@login_required
def dashboard(token):
    ...
```

Unauthenticated → `401`. Authenticated → gets through. Token injected automatically.

---

## Get user data

```python
@fetch_user_data
def profile(username, user_data, token):
    return jsonify({"hello": username, "data": user_data})
```

`username`, `user_data`, and `token` — all injected. No API calls, no parsing, just use them.

---

## Redirect instead of 401?

```python
@login_required_redirect(redirect_url="/login")
def dashboard(token):
    ...
```

Same thing, just sends the user to your login page instead.

---

## Tokens? Handled.

```
First visit        →  token arrives in URL  →  saved to cookie automatically
Every visit after  →  cookie used silently  →  nothing to do
Token expires      →  401 or redirect       →  user logs in again
```

You never touch a cookie or a session.

---

## Write user data

```python
connector.send_or_update_user_data(token, {"plan": "pro", "onboarded": True})
```

One call. Comes back in `user_data` on every `@fetch_user_data` request.

---

> ⚠️ **Django note:** Django ships its own `login_required`. Always import with an alias:
> `from easyauth_django import login_required as easyauth_login_required`

---

## Want to know more?

The [EasyAuth server repo](https://github.com/AvikYadav/EasyAuth) has the full picture — how the auth flow works, security details, self-hosting guide, and API reference if you want to build your own integration.

---

*auth made so eassyy ⚡*
"""Application Flask du Dashboard de Monitoring des Actions Auditées."""

from __future__ import annotations

import sys
from pathlib import Path

# Permet `python dashboard/app.py` depuis la racine du projet
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import csv
import io
import json
import os
import queue
import threading
import time
from pathlib import Path

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
    stream_with_context,
)

from dashboard.auth import (
    REDIRECT_URI,
    get_current_user,
    init_auth,
    login_required,
    oauth,
)
from dashboard.audit_reader import (
    compute_stats,
    filter_entries,
    get_unique_values,
    read_audit_log,
    tail_audit_log,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", os.urandom(32).hex())

init_auth(app)

# --- SSE: file d'attente des subscribers ---
_sse_subscribers: list[queue.Queue] = []
_sse_lock = threading.Lock()


def _notify_sse(entry: dict) -> None:
    """Envoie une entrée audit à tous les subscribers SSE."""
    data = json.dumps(entry, ensure_ascii=False)
    with _sse_lock:
        dead = []
        for q in _sse_subscribers:
            try:
                q.put_nowait(data)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _sse_subscribers.remove(q)


def _watch_audit_log() -> None:
    """Thread daemon qui surveille le fichier audit.log et notifie les SSE."""
    audit_path = Path(__file__).resolve().parent.parent / os.getenv("AUDIT_LOG_FILE", "audit.log")
    last_ts = 0.0
    while True:
        time.sleep(1)
        if not audit_path.exists():
            continue
        new_entries = tail_audit_log(last_ts)
        for entry in new_entries:
            last_ts = entry.get("ts", last_ts)
            _notify_sse(entry)


_watcher = threading.Thread(target=_watch_audit_log, daemon=True)
_watcher.start()


# ============================================================
# ROUTES D'AUTHENTIFICATION
# ============================================================

@app.route("/login")
def login():
    if "user" in session:
        return redirect(url_for("dashboard_view"))
    return render_template("login.html")


@app.route("/auth/start")
def auth_start():
    return oauth.keycloak.authorize_redirect(REDIRECT_URI)


@app.route("/callback")
def auth_callback():
    try:
        token = oauth.keycloak.authorize_access_token()
        user_info = oauth.keycloak.userinfo()
    except Exception as exc:
        app.logger.error("Callback OIDC échoué: %s (%s)", exc.__class__.__name__, exc)
        return redirect(url_for("login"))
    session["user"] = {
        "username": user_info.get("preferred_username", "unknown"),
        "email": user_info.get("email", ""),
        "name": user_info.get("name", ""),
        "roles": user_info.get("realm_access", {}).get("roles", []),
    }
    session["access_token"] = token.get("access_token")
    return redirect(url_for("dashboard_view"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================================================
# ROUTES PRINCIPALES (PAGES)
# ============================================================

@app.route("/")
@login_required
def dashboard_view():
    entries = read_audit_log()
    stats = compute_stats(entries)
    user = get_current_user()
    return render_template("dashboard.html", stats=stats, user=user, active="dashboard")


@app.route("/timeline")
@login_required
def timeline_view():
    user = get_current_user()
    entries = read_audit_log()
    tools = get_unique_values(entries, "tool")
    users_list = get_unique_values(entries, "user")
    verdicts = get_unique_values(entries, "verdict")
    statuses = get_unique_values(entries, "status")
    return render_template(
        "timeline.html",
        tools=tools,
        users=users_list,
        verdicts=verdicts,
        statuses=statuses,
        user=user,
        active="timeline",
    )


# ============================================================
# ROUTES API (données JSON)
# ============================================================

@app.route("/api/entries")
@login_required
def api_entries():
    entries = read_audit_log()
    filtered = filter_entries(
        entries,
        tool=request.args.get("tool"),
        user=request.args.get("user"),
        verdict=request.args.get("verdict"),
        status=request.args.get("status"),
        date_from=request.args.get("date_from"),
        date_to=request.args.get("date_to"),
        search=request.args.get("search"),
    )
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page
    return jsonify({
        "entries": filtered[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    })


@app.route("/api/stats")
@login_required
def api_stats():
    entries = read_audit_log()
    stats = compute_stats(entries)
    return jsonify(stats)


@app.route("/api/export")
@login_required
def api_export():
    entries = read_audit_log()
    filtered = filter_entries(
        entries,
        tool=request.args.get("tool"),
        user=request.args.get("user"),
        verdict=request.args.get("verdict"),
        status=request.args.get("status"),
        date_from=request.args.get("date_from"),
        date_to=request.args.get("date_to"),
        search=request.args.get("search"),
    )
    fmt = request.args.get("format", "json")
    if fmt == "csv":
        output = io.StringIO()
        if filtered:
            writer = csv.DictWriter(output, fieldnames=filtered[0].keys())
            writer.writeheader()
            writer.writerows(filtered)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_export.csv"},
        )
    return jsonify(filtered)


@app.route("/api/events")
@login_required
def api_events():
    """Server-Sent Events pour les alertes temps réel."""
    def stream():
        q: queue.Queue = queue.Queue(maxsize=100)
        with _sse_lock:
            _sse_subscribers.append(q)
        try:
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            while True:
                try:
                    data = q.get(timeout=30)
                    yield f"data: {data}\n\n"
                except queue.Empty:
                    yield f": keepalive\n\n"
        except GeneratorExit:
            pass
        finally:
            with _sse_lock:
                if q in _sse_subscribers:
                    _sse_subscribers.remove(q)

    return Response(
        stream_with_context(stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# ROUTES CONSOLE MCP (exécution d'outils)
# ============================================================

@app.route("/tools")
@login_required
def tools_view():
    user = get_current_user()
    return render_template("tools.html", user=user, active="tools")


@app.route("/api/tools/list")
@login_required
def api_tools_list():
    token = session.get("access_token")
    if not token:
        return jsonify({"error": "No access token — reconnect to Keycloak."}), 401
    try:
        from dashboard.mcp_client import list_tools
        tools = list_tools(token)
        slim = []
        for t in tools:
            slim.append({
                "name": t.get("name"),
                "description": (t.get("description") or "").split("\n")[0][:120],
                "inputSchema": t.get("inputSchema", {}),
                "annotations": t.get("annotations", {}),
            })
        return jsonify({"tools": slim})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.route("/api/tools/call", methods=["POST"])
@login_required
def api_tools_call():
    token = session.get("access_token")
    if not token:
        return jsonify({"error": "No access token."}), 401
    data = request.get_json(force=True) or {}
    tool_name = data.get("tool")
    arguments = data.get("arguments", {})
    call_id = data.get("callId", f"{tool_name}-{int(__import__('time').time())}")
    if not tool_name:
        return jsonify({"error": "Missing 'tool' field."}), 400
    arguments["token"] = token
    try:
        from dashboard.mcp_client import call_tool, pre_approve_elicitation
        if data.get("preApprove"):
            pre_approve_elicitation(call_id, "APPROVE")
        result = call_tool(token, tool_name, arguments, call_id=call_id)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"isError": True, "content": [{"type": "text", "text": str(exc)}]}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

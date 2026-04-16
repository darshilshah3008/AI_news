from __future__ import annotations

import html
from pathlib import Path
from urllib.parse import parse_qs

from wsgiref.simple_server import make_server

from . import db
from .models import ProjectProfile
from .services import build_timeline, build_weekly_brief, export_markdown, get_recommendations, ingest_dir, seed_projects


def startup() -> None:
    db.init_db()
    if not db.get_projects():
        seed_projects()
    if not db.list_articles():
        ingest_dir(Path("reports"))


def layout(body: str) -> str:
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>AI Signal OS</title><link rel='stylesheet' href='/static/style.css'></head><body><header class='topbar'><a class='brand' href='/'>AI Signal OS</a><nav><a href='/projects/new'>New Project</a></nav></header><main class='container'>{body}</main></body></html>"""


def parse_post(environ) -> dict[str, str]:
    length = int(environ.get("CONTENT_LENGTH") or 0)
    raw = environ["wsgi.input"].read(length).decode("utf-8") if length else ""
    return {k: v[0] for k, v in parse_qs(raw).items()}


def resp(start_response, body: str, status: str = "200 OK", ctype: str = "text/html; charset=utf-8"):
    start_response(status, [("Content-Type", ctype)])
    return [body.encode("utf-8")]


def redirect(start_response, location: str):
    start_response("303 See Other", [("Location", location)])
    return [b""]


def app(environ, start_response):
    startup()
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    qs = parse_qs(environ.get("QUERY_STRING", ""))

    if path == "/static/style.css":
        css = Path("aisignal/static/style.css").read_text(encoding="utf-8")
        return resp(start_response, css, ctype="text/css")

    if path == "/":
        projects = db.get_projects()
        cards = "".join(f"<a class='card' href='/dashboard?project_id={p['id']}'><h3>{html.escape(p['name'])}</h3><p>{html.escape(p['description'] or '')}</p></a>" for p in projects)
        body = """
        <section class='hero card'><h1>Stop tracking AI news. Start knowing what to build next.</h1>
        <p>Turn AI noise into product decisions. See what matters for your project.</p>
        <div class='cta-row'><a class='btn' href='/projects/new'>Create project profile</a></div></section>
        <h2>Demo profiles</h2><div class='grid'>""" + cards + "</div>"
        return resp(start_response, layout(body))

    if path == "/projects/new" and method == "GET":
        body = """
        <h1>Create your project profile</h1><form method='post' class='card form-grid'>
        <label>Project name<input name='name' required></label>
        <label>Description<textarea name='description'></textarea></label>
        <label>Hardware target<input name='hardware_target' value='NVIDIA Orin Nano'></label>
        <label>Deployment style<input name='deployment_style' value='edge/local'></label>
        <label>Offline requirement<input name='offline_requirement' value='high'></label>
        <label>Latency sensitivity<input name='latency_sensitivity' value='high'></label>
        <label>Power sensitivity<input name='power_sensitivity' value='medium'></label>
        <label>Memory constraints<input name='memory_constraints' value='8GB'></label>
        <label>Preferred frameworks<input name='preferred_frameworks' value='TensorRT,ONNX Runtime,CUDA'></label>
        <label>Excluded technologies<input name='excluded_technologies'></label>
        <label>Categories of interest<input name='categories_of_interest' value='Research,Developer'></label>
        <label>Goals<textarea name='goals'></textarea></label>
        <label>Evaluation priorities<textarea name='evaluation_priorities'></textarea></label>
        <button class='btn' type='submit'>Save profile</button></form>
        """
        return resp(start_response, layout(body))

    if path == "/projects/new" and method == "POST":
        form = parse_post(environ)
        profile = ProjectProfile(
            name=form.get("name", "New Project"), description=form.get("description", ""),
            hardware_target=form.get("hardware_target", ""), deployment_style=form.get("deployment_style", ""),
            offline_requirement=form.get("offline_requirement", "medium"), latency_sensitivity=form.get("latency_sensitivity", "medium"),
            power_sensitivity=form.get("power_sensitivity", "medium"), memory_constraints=form.get("memory_constraints", ""),
            preferred_frameworks=[x.strip() for x in form.get("preferred_frameworks", "").split(",") if x.strip()],
            excluded_technologies=[x.strip() for x in form.get("excluded_technologies", "").split(",") if x.strip()],
            categories_of_interest=[x.strip() for x in form.get("categories_of_interest", "").split(",") if x.strip()],
            goals=form.get("goals", ""), evaluation_priorities=form.get("evaluation_priorities", ""),
        )
        pid = db.save_project(profile)
        return redirect(start_response, f"/dashboard?project_id={pid}")

    if path == "/dashboard":
        pid = int((qs.get("project_id") or ["1"])[0])
        project = db.get_project(pid)
        if not project:
            return resp(start_response, "Project not found", "404 Not Found", "text/plain")
        recs = get_recommendations(pid, 50)
        cards = "".join(
            f"<div class='card'><span class='pill {r['action'].lower()}'>{r['action']}</span><h3>{html.escape(r['title'])}</h3><p>{html.escape(r['summary'] or '')}</p><p><b>Relevance</b> {r['relevance_score']} | <b>Importance</b> {r['importance_score']}</p><p><b>Why</b> {html.escape(r['reasoning'])}</p><a target='_blank' href='{r['url']}'>Source</a></div>"
            for r in recs[:8]
        )
        relevant = "".join(f"<li>[{r['action']}] {html.escape(r['title'])}</li>" for r in recs if r["action"] in {"BUILD", "TEST"})
        ignore = "".join(f"<li>[{r['action']}] {html.escape(r['title'])}</li>" for r in recs if r["action"] in {"WATCH", "IGNORE"})
        body = f"<h1>{html.escape(project['name'])}</h1><p>{html.escape(project['description'] or '')}</p><div class='cta-row'><a class='btn secondary' href='/signals?project_id={pid}'>Signal Feed</a><a class='btn secondary' href='/weekly-brief?project_id={pid}'>Weekly Brief</a><a class='btn secondary' href='/timeline?project_id={pid}'>Timeline</a></div><h2>Top signals today</h2><div class='grid'>{cards}</div><h2>Recommended actions this week</h2><ul class='card'>{relevant}</ul><h2>Noise to ignore</h2><ul class='card'>{ignore}</ul>"
        return resp(start_response, layout(body))

    if path == "/signals":
        pid = int((qs.get("project_id") or ["1"])[0])
        action = (qs.get("action") or [""])[0]
        recs = get_recommendations(pid, 120)
        if action:
            recs = [r for r in recs if r["action"] == action]
        items = "".join(f"<div class='card'><span class='pill {r['action'].lower()}'>{r['action']}</span><h3>{html.escape(r['title'])}</h3><p>{html.escape(r['summary'] or '')}</p><p>Relevance {r['relevance_score']} | Confidence {r['confidence_score']}</p><p>{html.escape(r['reasoning'])}</p><a href='{r['url']}' target='_blank'>Read</a></div>" for r in recs)
        body = f"<h1>Signal Feed</h1><div class='cta-row'><a class='btn secondary' href='/signals?project_id={pid}'>All</a><a class='btn secondary' href='/signals?project_id={pid}&action=BUILD'>BUILD</a><a class='btn secondary' href='/signals?project_id={pid}&action=TEST'>TEST</a><a class='btn secondary' href='/signals?project_id={pid}&action=IGNORE'>IGNORE</a></div>{items}"
        return resp(start_response, layout(body))

    if path == "/weekly-brief":
        pid = int((qs.get("project_id") or ["1"])[0])
        brief = html.escape(build_weekly_brief(pid))
        body = f"<h1>Weekly Brief</h1><div class='cta-row'><a class='btn' href='/export/project?project_id={pid}'>Export project brief</a></div><pre class='card pre'>{brief}</pre>"
        return resp(start_response, layout(body))

    if path == "/timeline":
        pid = int((qs.get("project_id") or ["1"])[0])
        content = html.escape(build_timeline(pid))
        body = f"<h1>Project Timeline</h1><div class='cta-row'><a class='btn' href='/export/timeline?project_id={pid}'>Export timeline</a></div><pre class='card pre'>{content}</pre>"
        return resp(start_response, layout(body))

    if path == "/export/project":
        pid = int((qs.get("project_id") or ["1"])[0])
        path = export_markdown(build_weekly_brief(pid), f"project_{pid}_brief.md")
        return resp(start_response, f"Exported project brief to {path}", ctype="text/plain")

    if path == "/export/timeline":
        pid = int((qs.get("project_id") or ["1"])[0])
        path = export_markdown(build_timeline(pid), f"project_{pid}_timeline.md")
        return resp(start_response, f"Exported timeline to {path}", ctype="text/plain")

    return resp(start_response, "Not found", "404 Not Found", "text/plain")


def run_server(host: str = "127.0.0.1", port: int = 8000):
    startup()
    with make_server(host, port, app) as httpd:
        print(f"AI Signal OS running at http://{host}:{port}")
        httpd.serve_forever()

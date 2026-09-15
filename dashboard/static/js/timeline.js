/* Timeline : chargement paginé, filtres, recherche, export, détail. */

(function () {
    "use strict";

    const table = document.getElementById("timeline-table");
    const tbody = table ? table.querySelector("tbody") : null;
    const pagination = document.getElementById("pagination");
    const resultCount = document.getElementById("result-count");
    const form = document.getElementById("filter-form");
    let currentPage = 1;

    const badgeVerdict = { SAFE: "success", SUSPICIOUS: "warning", BLOCKED: "danger", UNKNOWN: "secondary" };
    const badgeStatus = {
        OK: "success", DRY_RUN: "info", EXECUTED: "primary",
        BLOCKED: "danger", DECLINED: "secondary", CANCELLED: "secondary",
        DENIED: "dark", ERROR: "danger", APPROVED: "primary",
    };

    function esc(text) {
        if (text === null || text === undefined) return "";
        const div = document.createElement("div");
        div.textContent = String(text);
        return div.innerHTML;
    }

    function formatTime(ts) {
        if (!ts) return "—";
        const date = new Date(ts);
        if (isNaN(date)) return ts;
        return date.toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "medium" });
    }

    function params() {
        const data = new FormData(form);
        const qs = new URLSearchParams();
        for (const [k, v] of data) {
            if (v) qs.set(k, v);
        }
        return qs;
    }

    function loadEntries(page) {
        currentPage = page || 1;
        const qs = params();
        qs.set("page", currentPage);
        qs.set("per_page", document.getElementById("per-page").value);

        fetch(`/api/entries?${qs}`)
            .then((r) => r.json())
            .then((data) => {
                renderRows(data.entries);
                if (resultCount) resultCount.textContent = data.total;
                renderPagination(data);
            })
            .catch((e) => console.error("Erreur chargement:", e));
    }

    function renderRows(entries) {
        if (!tbody) return;
        if (!entries.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">Aucune action trouvée.</td></tr>';
            return;
        }
        tbody.innerHTML = entries.map((e) => {
            const vBadge = badgeVerdict[e.verdict] || "secondary";
            const sBadge = badgeStatus[e.status] || "secondary";
            const detail = (e.detail || "");
            return `
            <tr>
                <td>${e.dry_run ? '<span class="badge bg-info" title="Simulation">DRY</span>' : '<span class="badge bg-light text-dark" title="Réel">LIVE</span>'}</td>
                <td class="text-nowrap small">${formatTime(e.timestamp)}</td>
                <td><code class="text-info">${esc(e.tool)}</code></td>
                <td><i class="bi bi-person-circle me-1"></i>${esc(e.user || "anonyme")}</td>
                <td><span class="badge text-bg-${vBadge}">${esc(e.verdict || "?")}</span></td>
                <td><span class="badge text-bg-${sBadge}">${esc(e.status || "?")}</span></td>
                <td class="small text-truncate" style="max-width: 240px;" title="${esc(detail)}">${esc(detail)}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-light" title="Voir le détail" data-detail='${esc(JSON.stringify(e))}'>
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            </tr>`;
        }).join("");

        tbody.querySelectorAll("[data-detail]").forEach((btn) => {
            btn.addEventListener("click", () => showDetail(JSON.parse(btn.dataset.detail)));
        });
    }

    function renderPagination(data) {
        if (!pagination) return;
        if (data.pages <= 1) {
            pagination.innerHTML = "";
            return;
        }
        const links = [];
        const addBtn = (page, label, disabled, active) => {
            links.push(`<li class="page-item ${disabled ? "disabled" : ""} ${active ? "active" : ""}">
                <button class="page-link bg-dark text-light border-secondary" data-page="${page}">${label}</button></li>`);
        };
        addBtn(data.page - 1, "&laquo;", data.page <= 1, false);
        const start = Math.max(1, data.page - 2);
        const end = Math.min(data.pages, data.page + 2);
        for (let p = start; p <= end; p++) addBtn(p, p, false, p === data.page);
        addBtn(data.page + 1, "&raquo;", data.page >= data.pages, false);
        pagination.innerHTML = links.join("");
        pagination.querySelectorAll("button[data-page]").forEach((btn) => {
            btn.addEventListener("click", () => loadEntries(parseInt(btn.dataset.page, 10)));
        });
    }

    function showDetail(e) {
        const body = document.getElementById("detail-body");
        const rows = (paramsObj, title) => {
            if (!paramsObj) return `<tr><td colspan="2" class="text-muted">—</td></tr>`;
            return Object.entries(paramsObj).map(([k, v]) =>
                `<tr><td class="text-nowrap small text-muted">${esc(k)}</td><td class="small" style="word-break:break-word;"><code>${esc(v)}</code></td></tr>`
            ).join("");
        };
        let paramsStr;
        try { paramsStr = JSON.parse(e.params || "null"); } catch { paramsStr = e.params || null; }

        body.innerHTML = `
            <table class="table table-dark align-middle mb-0">
                <tbody>
                    <tr><td class="text-muted" style="width:30%">Horodatage</td><td>${formatTime(e.timestamp)}</td></tr>
                    <tr><td class="text-muted">Outil</td><td><code class="text-info">${esc(e.tool)}</code></td></tr>
                    <tr><td class="text-muted">Utilisateur</td><td>${esc(e.user || "anonyme")}</td></tr>
                    <tr><td class="text-muted">Mode</td><td>${e.dry_run ? '<span class="badge bg-info">DRY-RUN</span>' : '<span class="badge bg-light text-dark">RÉEL</span>'}</td></tr>
                    <tr><td class="text-muted">Verdict</td><td><span class="badge text-bg-${badgeVerdict[e.verdict] || "secondary"}">${esc(e.verdict)}</span></td></tr>
                    <tr><td class="text-muted">Statut</td><td><span class="badge text-bg-${badgeStatus[e.status] || "secondary"}">${esc(e.status)}</span></td></tr>
                    <tr><td class="text-muted">Détail</td><td class="small">${esc(e.detail || "—")}</td></tr>
                </tbody>
            </table>
            <h6 class="mt-3"><i class="bi bi-sliders"></i> Paramètres</h6>
            <table class="table table-dark table-sm align-middle mb-0">
                <tbody>${rows(paramsStr)}</tbody>
            </table>`;
        new bootstrap.Modal(document.getElementById("detailModal")).show();
    }

    // Événements
    if (form) form.addEventListener("submit", (e) => { e.preventDefault(); loadEntries(1); });
    document.getElementById("per-page").addEventListener("change", () => loadEntries(1));
    document.getElementById("btn-reset").addEventListener("click", () => { form.reset(); loadEntries(1); });

    document.getElementById("btn-export-csv").addEventListener("click", (e) => {
        e.preventDefault();
        const qs = params(); qs.set("format", "csv");
        window.location.href = `/api/export?${qs}`;
    });
    document.getElementById("btn-export-json").addEventListener("click", (e) => {
        e.preventDefault();
        const qs = params(); qs.set("format", "json");
        window.location.href = `/api/export?${qs}`;
    });

    // Temps réel : ajouter les nouvelles entrées en tête
    window.addEventListener("audit:new", () => loadEntries(1));

    loadEntries(1);
})();
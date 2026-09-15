/* Server-Sent Events : alertes temps réel sur les nouvelles actions auditées. */

(function () {
    "use strict";

    const connectionStatus = document.getElementById("connection-status");

    function showToast(entry) {
        const isBlocked = entry.verdict === "BLOCKED";
        const isSuspicious = entry.verdict === "SUSPICIOUS";
        if (!isBlocked && !isSuspicious) return;

        const title = isBlocked ? "Action bloquée" : "Action suspecte";
        const cls = isBlocked ? "danger" : "warning";
        const icon = isBlocked ? "bi-shield-x" : "bi-exclamation-triangle";
        const time = entry.timestamp || new Date().toISOString();

        const el = document.createElement("div");
        el.className = `toast align-items-center text-bg-${cls} border-0`;
        el.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong><i class="bi ${icon} me-1"></i>${title}</strong>
                    <div class="small mt-1">
                        <span class="badge bg-light bg-opacity-25">${(entry.user || "anonyme")}</span>
                        <span class="badge bg-light bg-opacity-25">${entry.tool || "?"}</span>
                        <span class="text-truncate d-block mt-1">${(entry.detail || "")}</span>
                        <span class="opacity-75">${time}</span>
                    </div>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>`;

        const container = document.getElementById("toast-container");
        if (!container) return;
        container.appendChild(el);
        const toast = new bootstrap.Toast(el, { delay: 5000 });
        toast.show();
        el.addEventListener("hidden.bs.toast", () => el.remove());

        // Toast sans Bootstrap si l'objet n'existe pas
        setTimeout(() => el.remove(), 6000);
    }

    function connect() {
        const es = new EventSource("/api/events");
        es.onopen = () => {
            if (connectionStatus) {
                connectionStatus.className = "badge bg-success";
                connectionStatus.innerHTML = "<i class='bi bi-broadcast'></i> Temps réel";
            }
        };
        es.onerror = () => {
            es.close();
            if (connectionStatus) {
                connectionStatus.className = "badge bg-danger";
                connectionStatus.innerHTML = "<i class='bi bi-hdd'></i> Reconnexion…";
            }
            setTimeout(connect, 3000);
        };
        es.onmessage = (evt) => {
            try {
                const data = JSON.parse(evt.data);
                if (data.type === "connected") return;
                showToast(data);
                // Événement custom pour les pages qui veulent rafraichir
                window.dispatchEvent(new CustomEvent("audit:new", { detail: data }));
            } catch (e) { /* ignore */ }
        };
    }

    connect();
})();
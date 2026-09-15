/* Dashboard : KPIs + graphiques Chart.js + filtres temporels. */

(function () {
    "use strict";

    const colors = {
        primary: "#0d6efd",
        danger: "#dc3545",
        warning: "#ffc107",
        success: "#198754",
        info: "#0dcaf0",
        secondary: "#6c757d",
        grid: "rgba(255,255,255,0.08)",
        text: "#adb5bd",
    };

    const charts = {};

    function refreshStats() {
        fetch("/api/stats")
            .then((r) => r.json())
            .then((stats) => {
                document.getElementById("kpi-total").textContent = stats.total;
                document.getElementById("kpi-blocked").textContent = stats.blocked;
                document.getElementById("kpi-suspicious").textContent = stats.suspicious;
                document.getElementById("kpi-users").textContent = stats.active_users;
                renderCharts(stats);
            })
            .catch((e) => console.error("Erreur stats:", e));
    }

    function renderCharts(stats) {
        // Activité par jour (line)
        const days = stats.by_day.map((d) => d.date);
        const counts = stats.by_day.map((d) => d.count);

        if (charts.activity) charts.activity.destroy();
        if (charts.verdict) charts.verdict.destroy();
        if (charts.tools) charts.tools.destroy();
        if (charts.hour) charts.hour.destroy();

        const ctxAct = document.getElementById("chart-activity");
        if (ctxAct) {
            charts.activity = new Chart(ctxAct, {
                type: "line",
                data: {
                    labels: days,
                    datasets: [{
                        label: "Actions",
                        data: counts,
                        borderColor: colors.info,
                        backgroundColor: "rgba(13,202,240,0.15)",
                        fill: true,
                        tension: 0.3,
                        pointRadius: 2,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: colors.text } },
                        tooltip: { mode: "index", intersect: false },
                    },
                    scales: {
                        x: { ticks: { color: colors.text, maxTicksLimit: 10 }, grid: { color: colors.grid } },
                        y: { ticks: { color: colors.text, precision: 0 }, grid: { color: colors.grid } },
                    },
                },
            });
        }

        // Pie chart verdicts
        const verdictLabels = Object.keys(stats.by_verdict);
        const verdictData = Object.values(stats.by_verdict);
        const ctxVerdict = document.getElementById("chart-verdict");
        if (ctxVerdict) {
            const palette = { SAFE: colors.success, SUSPICIOUS: colors.warning, BLOCKED: colors.danger, UNKNOWN: colors.secondary };
            charts.verdict = new Chart(ctxVerdict, {
                type: "doughnut",
                data: {
                    labels: verdictLabels,
                    datasets: [{
                        data: verdictData,
                        backgroundColor: verdictLabels.map((l) => palette[l] || colors.secondary),
                        borderWidth: 1,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "bottom", labels: { color: colors.text } },
                    },
                },
            });
        }

        // Bar chart outils
        const toolNames = Object.keys(stats.by_tool).slice(0, 10);
        const toolCounts = Object.values(stats.by_tool).slice(0, 10);
        const ctxTools = document.getElementById("chart-tools");
        if (ctxTools) {
            charts.tools = new Chart(ctxTools, {
                type: "bar",
                data: {
                    labels: toolNames,
                    datasets: [{
                        label: "Nombre d'actions",
                        data: toolCounts,
                        backgroundColor: "rgba(13,110,253,0.6)",
                        borderRadius: 4,
                    }],
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: colors.text, precision: 0 }, grid: { color: colors.grid } },
                        y: { ticks: { color: colors.text }, grid: { color: colors.grid } },
                    },
                },
            });
        }

        // Bar chart heures
        const ctxHour = document.getElementById("chart-hour");
        if (ctxHour) {
            charts.hour = new Chart(ctxHour, {
                type: "bar",
                data: {
                    labels: stats.by_hour.map((h) => h.hour),
                    datasets: [{
                        label: "Actions",
                        data: stats.by_hour.map((h) => h.count),
                        backgroundColor: "rgba(25,135,84,0.6)",
                        borderRadius: 4,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: colors.text, maxTicksLimit: 12 }, grid: { color: colors.grid } },
                        y: { ticks: { color: colors.text, precision: 0 }, grid: { color: colors.grid } },
                    },
                },
            });
        }
    }

    // Filtres temporels
    document.querySelectorAll(".range-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".range-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            // Envoyer un événement pour que timeline.js mette à jour si présent
            window.dispatchEvent(new CustomEvent("range:change", { detail: { hours: parseInt(btn.dataset.hours, 10) } }));
        });
    });

    // Mise à jour temps réel
    window.addEventListener("audit:new", () => refreshStats());

    // Rafraîchissement initial puis périodique
    refreshStats();
    setInterval(refreshStats, 30000);
})();
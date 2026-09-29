/* Console MCP — liste, formulaire et exécution des outils. */
(function () {
    "use strict";

    let TOOLS = [];
    let currentTool = null;
    let pendingCallId = null;

    const sel = document.getElementById("tool-select");
    const desc = document.getElementById("tool-desc");
    const form = document.getElementById("param-form");
    const executeBtn = document.getElementById("btn-execute");
    const hitlCard = document.getElementById("hitl-card");
    const resultOut = document.getElementById("result-output");

    // ── Chargement des outils ──────────────────────────────────────
    async function loadTools() {
        try {
            const res = await fetch("/api/tools/list");
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || "Erreur serveur");
            TOOLS = data.tools || [];
            sel.innerHTML = '<option value="">— Choisir un outil —</option>';
            for (const t of TOOLS) {
                const opt = document.createElement("option");
                opt.value = t.name;
                opt.textContent = t.name;
                sel.appendChild(opt);
            }
            if (TOOLS.length === 0) {
                sel.innerHTML = '<option value="">Aucun outil disponible</option>';
            }
        } catch (err) {
            sel.innerHTML = `<option value="">⚠ Serveur MCP injoignable</option>`;
            desc.textContent = err.message;
        }
    }

    // ── Formulaire dynamique depuis l'inputSchema ──────────────────
    function renderForm(tool) {
        form.innerHTML = "";
        const schema = tool.inputSchema || {};
        const props = schema.properties || {};
        const required = new Set(schema.required || []);
        const entries = Object.entries(props).filter(([k]) => k !== "token");

        if (entries.length === 0) {
            form.innerHTML = '<div class="col-12 text-muted">Aucun paramètre requis (hors token).</div>';
            return;
        }

        for (const [name, prop] of entries) {
            const col = document.createElement("div");
            col.className = "col-md-6";
            const label = document.createElement("label");
            label.className = "form-label";
            label.textContent = `${name}${required.has(name) ? " *" : ""}`;

            const ptype = prop.type === "integer" || prop.type === "number" ? "number"
                : prop.type === "boolean" ? "checkbox"
                : prop.enum ? "select" : "text";

            let input;
            if (ptype === "select") {
                input = document.createElement("select");
                input.className = "form-select";
                for (const e of prop.enum) {
                    const o = document.createElement("option");
                    o.value = e;
                    o.textContent = e;
                    input.appendChild(o);
                }
            } else if (ptype === "boolean") {
                input = document.createElement("input");
                input.type = "checkbox";
                input.className = "form-check-input ms-1";
                input.checked = prop.default === true;
                col.className = "col-md-6";
                label.className = "form-check-label ms-2";
                const wrap = document.createElement("div");
                wrap.className = "form-check";
                wrap.appendChild(input);
                wrap.appendChild(label);
                input.dataset.pname = name;
                input.dataset.pbool = "1";
                col.appendChild(wrap);
                form.appendChild(col);
                continue;
            } else {
                input = document.createElement("input");
                input.type = "number";
                input.step = "any";
                input.className = "form-control";
                if (prop.default !== undefined) input.value = prop.default;
            }
            input.dataset.pname = name;
            col.appendChild(label);
            col.appendChild(input);
            form.appendChild(col);
        }

        const helpRow = document.createElement("div");
        helpRow.className = "col-12";
        helpRow.innerHTML = '<small class="text-muted">Les champs requis sont marqués d\'une astérisque.</small>';
        form.appendChild(helpRow);
    }

    // ── Collecte des arguments ─────────────────────────────────────
    function collectArgs(tool) {
        const args = {};
        form.querySelectorAll("[data-pname]").forEach((el) => {
            const name = el.dataset.pname;
            const isBool = el.dataset.pbool === "1";
            if (isBool) {
                args[name] = el.checked;
                return;
            }
            if (el.type === "number") {
                args[name] = el.value === "" ? undefined : Number(el.value);
                return;
            }
            args[name] = el.value || undefined;
        });
        return args;
    }

    // ── Exécution ──────────────────────────────────────────────────
    function isDestructive(tool) {
        const descText = (tool.description || "").toLowerCase();
        const name = (tool.name || "").toLowerCase();
        const ann = tool.annotations || {};
        if (ann.destructiveHint) return true;
        return /destruct|rollback|suppress|delete|trigger_pipeline/.test(name + " " + descText);
    }

    function renderResult(result) {
        const text = (result.content || [])
            .filter((c) => c.type === "text")
            .map((c) => c.text)
            .join("\n");
        const isErr = result.isError === true;
        resultOut.innerHTML = "";
        if (isErr) {
            resultOut.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle"></i> ${escapeHtml(text) || "Erreur"}</span>`;
        } else {
            resultOut.textContent = text;
        }
    }

    async function run(args, dryRun, callId, preApprove) {
        executeBtn.disabled = true;
        executeBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Exécution…';
        resultOut.textContent = "(exécution en cours…)";
        try {
            const res = await fetch("/api/tools/call", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tool: currentTool.name,
                    arguments: args,
                    callId,
                    preApprove: preApprove === true,
                    dryRun: dryRun === true,
                }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error((data.content && data.content[0] && data.content[0].text) || data.error || "Erreur");
            renderResult(data);
        } catch (err) {
            resultOut.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle"></i> ${escapeHtml(err.message)}</span>`;
        } finally {
            executeBtn.disabled = false;
            executeBtn.innerHTML = '<i class="bi bi-play-fill"></i> Exécuter';
        }
    }

    // ── Événements ────────────────────────────────────────────────
    sel.addEventListener("change", () => {
        currentTool = TOOLS.find((t) => t.name === sel.value) || null;
        if (!currentTool) {
            desc.textContent = "";
            form.innerHTML = '<div class="col-12 text-muted">Sélectionnez un outil.</div>';
            executeBtn.classList.add("d-none");
            hitlCard.classList.add("d-none");
            return;
        }
        desc.textContent = currentTool.description;
        renderForm(currentTool);
        executeBtn.classList.remove("d-none");
        hitlCard.classList.add("d-none");
    });

    executeBtn.addEventListener("click", () => {
        if (!currentTool) return;
        let args = collectArgs(currentTool);
        const props = (currentTool.inputSchema || {}).properties || {};
        if (props.dry_run) {
            args.dry_run = true;
        }
        const cid = `${currentTool.name}-${Date.now()}`;
        pendingCallId = cid;
        run(args, true, cid, false);
        if (isDestructive(currentTool)) {
            hitlCard.classList.remove("d-none");
        }
    });

    document.getElementById("btn-hilt-approve").addEventListener("click", () => {
        hitlCard.classList.add("d-none");
        let args = collectArgs(currentTool);
        const props = (currentTool.inputSchema || {}).properties || {};
        if (props.dry_run) {
            args.dry_run = false;
        }
        run(args, false, pendingCallId, true);
    });

    document.getElementById("btn-hilt-decline").addEventListener("click", () => {
        hitlCard.classList.add("d-none");
        resultOut.innerHTML = '<span class="text-warning"><i class="bi bi-shield-x"></i> Action DÉCLINÉE — aucune action destructive exécutée.</span>';
    });

    // ── Helper ────────────────────────────────────────────────────
    function escapeHtml(s) {
        const div = document.createElement("div");
        div.textContent = s;
        return div.innerHTML;
    }

    loadTools();
})();
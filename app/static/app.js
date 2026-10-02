const BASE = location.pathname.replace(/\/static\/.*$/, "");
const API = `${BASE}/api`;

const $ = (sel) => document.querySelector(sel);
const el = (tag, props = {}, children = []) => {
  const node = Object.assign(document.createElement(tag), props);
  for (const child of [].concat(children)) {
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
};

function toast(message, isError = false) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.remove("hidden");
  node.style.borderColor = isError ? "var(--err)" : "var(--line)";
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.add("hidden"), 4000);
}

async function api(path, { method = "GET", body, raw = false } = {}) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) {
    showLogin();
    throw new Error("Not authenticated");
  }
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload.detail || `${res.status} ${res.statusText}`);
  }
  return raw ? res : res.json();
}

const bytes = (value) => {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = Number(value) || 0;
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(index ? 1 : 0)} ${units[index]}`;
};

const uptime = (seconds) => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  return `${days}d ${hours}h`;
};

function table(columns, rows, renderRow) {
  const head = el("tr", {}, columns.map((label) => el("th", { textContent: label })));
  const body = rows.map(renderRow);
  return el("table", {}, [el("thead", {}, head), el("tbody", {}, body)]);
}

function actionButton(label, handler, variant = "ghost") {
  const button = el("button", { textContent: label, className: variant });
  button.onclick = async () => {
    button.disabled = true;
    try {
      await handler();
    } catch (error) {
      toast(error.message, true);
    } finally {
      button.disabled = false;
    }
  };
  return button;
}

const views = {};

views.overview = async (root) => {
  const data = await api("/system/overview");
  const stats = [
    ["CPU", `${data.cpu.percent.toFixed(1)}%`, `${data.cpu.cores} cores`, data.cpu.percent],
    ["Memory", `${data.memory.percent.toFixed(1)}%`, `${bytes(data.memory.used)} / ${bytes(data.memory.total)}`, data.memory.percent],
    ["Load", data.load["1m"].toFixed(2), `pressure ${data.load.pressure}`, Math.min(data.load.pressure * 100, 100)],
    ["Uptime", uptime(data.uptime_seconds), data.os, null],
  ];

  root.append(
    el("div", { className: "grid" }, stats.map(([title, value, note, pct]) => {
      const card = el("div", { className: "stat" }, [
        el("b", { textContent: value }),
        el("span", { textContent: `${title} — ${note}` }),
      ]);
      if (pct !== null) {
        card.append(el("div", { className: "bar" }, [el("i", { style: `width:${pct}%` })]));
      }
      return card;
    })),
  );

  root.append(el("h3", { textContent: "Disks" }));
  root.append(table(["Mount", "Filesystem", "Used", "Total", "%"], data.disks, (disk) =>
    el("tr", {}, [
      el("td", { textContent: disk.mountpoint }),
      el("td", { textContent: disk.fstype }),
      el("td", { textContent: bytes(disk.used) }),
      el("td", { textContent: bytes(disk.total) }),
      el("td", { textContent: `${disk.percent}%` }),
    ])));

  const services = await api("/system/services");
  root.append(el("h3", { textContent: "Services" }));
  root.append(table(["Service", "State", ""], services, (service) =>
    el("tr", {}, [
      el("td", { textContent: service.name }),
      el("td", { textContent: service.state, className: service.state === "active" ? "ok" : "muted" }),
      el("td", {}, ["restart", "reload", "stop", "start"].map((action) =>
        actionButton(action, async () => {
          const result = await api("/system/services", { method: "POST", body: { name: service.name, action } });
          toast(result.message || `${service.name} ${action}`, !result.ok);
          render("overview");
        }))),
    ])));
};

views.sites = async (root) => {
  const form = el("div", { className: "row" });
  const name = el("input", { placeholder: "example.com" });
  const type = el("select", {}, [
    el("option", { value: "static", textContent: "static" }),
    el("option", { value: "php", textContent: "php" }),
    el("option", { value: "proxy", textContent: "proxy" }),
  ]);
  const target = el("input", { placeholder: "http://127.0.0.1:3000" });
  const phpVersion = el("input", { placeholder: "php version e.g. 8.1" });
  form.append(name, type, target, phpVersion, actionButton("Create site", async () => {
    await api("/sites", {
      method: "POST",
      body: {
        name: name.value.trim(),
        site_type: type.value,
        domains: [name.value.trim()],
        proxy_target: target.value.trim(),
        php_version: phpVersion.value.trim(),
      },
    });
    toast(`Site ${name.value} created`);
    render("sites");
  }, ""));
  root.append(form);

  const sites = await api("/sites");
  root.append(table(["Name", "Type", "Root", "Domains", "SSL", "Status", ""], sites, (site) =>
    el("tr", {}, [
      el("td", { textContent: site.name }),
      el("td", { textContent: site.site_type }),
      el("td", { textContent: site.root, className: "muted" }),
      el("td", { textContent: site.domains.join(", ") }),
      el("td", { textContent: site.ssl_enabled ? "on" : "off", className: site.ssl_enabled ? "ok" : "muted" }),
      el("td", { textContent: site.enabled ? "running" : "stopped", className: site.enabled ? "ok" : "muted" }),
      el("td", {}, [
        actionButton(site.enabled ? "stop" : "start", async () => {
          await api(`/sites/${site.id}/${site.enabled ? "stop" : "start"}`, { method: "POST" });
          render("sites");
        }),
        actionButton("issue ssl", async () => {
          const result = await api(`/ssl/${site.id}/issue`, { method: "POST", body: { domains: site.domains, force_https: true } });
          toast(`Certificate issued for ${result.domains}`);
          render("sites");
        }),
        actionButton("config", async () => {
          const config = await api(`/sites/${site.id}/config`);
          showPre(`${site.name} vhost`, config.content || config.rendered);
        }),
        actionButton("backup", async () => {
          const record = await api(`/backups/site/${site.id}`, { method: "POST" });
          toast(`Backup ${bytes(record.size)} created`);
        }),
        actionButton("delete", async () => {
          if (!confirm(`Delete site ${site.name}?`)) return;
          await api(`/sites/${site.id}`, { method: "DELETE" });
          render("sites");
        }, "danger"),
      ]),
    ])));
};

views.databases = async (root) => {
  const status = await api("/databases/status").catch(() => ({ available: false }));
  root.append(el("p", { className: "muted", textContent: `MySQL: ${status.available ? "connected" : "unavailable"}` }));

  const name = el("input", { placeholder: "db name" });
  const note = el("input", { placeholder: "note" });
  root.append(el("div", { className: "row" }, [name, note, actionButton("Create database", async () => {
    const record = await api("/databases", { method: "POST", body: { name: name.value.trim(), note: note.value } });
    toast(`Created ${record.name}`);
    render("databases");
  }, "")]));

  const rows = await api("/databases");
  root.append(table(["Name", "User", "Charset", "Note", ""], rows, (row) =>
    el("tr", {}, [
      el("td", { textContent: row.name }),
      el("td", { textContent: row.username }),
      el("td", { textContent: row.charset }),
      el("td", { textContent: row.note, className: "muted" }),
      el("td", {}, [
        actionButton("password", async () => {
          const creds = await api(`/databases/${row.id}/credentials`);
          showPre(row.name, `user: ${creds.username}\npassword: ${creds.password}`);
        }),
        actionButton("backup", async () => {
          const record = await api(`/backups/database/${row.id}`, { method: "POST" });
          toast(`Dump ${bytes(record.size)} created`);
        }),
        actionButton("drop", async () => {
          if (!confirm(`Drop database ${row.name}?`)) return;
          await api(`/databases/${row.id}`, { method: "DELETE" });
          render("databases");
        }, "danger"),
      ]),
    ])));
};

views.files = async (root) => {
  const { roots } = await api("/files/roots");
  const state = { path: views.files.path || roots[0] };

  const pathInput = el("input", { value: state.path, style: "flex:1;min-width:280px" });
  const reload = async (next) => {
    state.path = next;
    views.files.path = next;
    pathInput.value = next;
    await draw();
  };

  const listing = el("div");
  root.append(el("div", { className: "row" }, [
    pathInput,
    actionButton("Go", () => reload(pathInput.value.trim()), ""),
    actionButton("Up", () => reload(state.path.replace(/\/[^/]+\/?$/, "") || "/")),
  ]), listing);

  async function draw() {
    listing.textContent = "";
    const data = await api(`/files/list?path=${encodeURIComponent(state.path)}`);
    listing.append(table(["Name", "Size", "Mode", "Owner", "Modified", ""], data.entries, (entry) =>
      el("tr", {}, [
        el("td", {}, [
          entry.is_dir
            ? actionButton(`${entry.name}/`, () => reload(entry.path))
            : el("span", { textContent: entry.name }),
        ]),
        el("td", { textContent: entry.is_dir ? "-" : bytes(entry.size) }),
        el("td", { textContent: entry.mode, className: "muted" }),
        el("td", { textContent: `${entry.owner}:${entry.group}`, className: "muted" }),
        el("td", { textContent: entry.modified, className: "muted" }),
        el("td", {}, entry.is_dir ? [] : [
          actionButton("edit", async () => {
            const file = await api(`/files/read?path=${encodeURIComponent(entry.path)}`);
            showEditor(entry.path, file.content);
          }),
          actionButton("delete", async () => {
            if (!confirm(`Delete ${entry.path}?`)) return;
            await api(`/files?path=${encodeURIComponent(entry.path)}`, { method: "DELETE" });
            await draw();
          }, "danger"),
        ]),
      ])));
  }

  await draw();
};

views.cron = async (root) => {
  const name = el("input", { placeholder: "job name" });
  const schedule = el("input", { placeholder: "0 3 * * *" });
  const command = el("input", { placeholder: "command", style: "flex:1;min-width:240px" });
  root.append(el("div", { className: "row" }, [name, schedule, command, actionButton("Add job", async () => {
    await api("/cron", { method: "POST", body: { name: name.value, schedule: schedule.value, command: command.value } });
    toast("Cron job added");
    render("cron");
  }, "")]));

  const jobs = await api("/cron");
  root.append(table(["Name", "Schedule", "Command", "Enabled", ""], jobs, (job) =>
    el("tr", {}, [
      el("td", { textContent: job.name }),
      el("td", { textContent: job.schedule, className: "muted" }),
      el("td", { textContent: job.command }),
      el("td", { textContent: job.enabled ? "yes" : "no", className: job.enabled ? "ok" : "muted" }),
      el("td", {}, [
        actionButton("run", async () => {
          const result = await api(`/cron/${job.id}/run`, { method: "POST" });
          showPre(job.name, result.message || "(no output)");
        }),
        actionButton("logs", async () => {
          const logs = await api(`/cron/${job.id}/logs`);
          showPre(`${job.name} logs`, logs.lines.join("\n") || "(empty)");
        }),
        actionButton(job.enabled ? "disable" : "enable", async () => {
          await api(`/cron/${job.id}`, { method: "PATCH", body: { enabled: !job.enabled } });
          render("cron");
        }),
        actionButton("delete", async () => {
          await api(`/cron/${job.id}`, { method: "DELETE" });
          render("cron");
        }, "danger"),
      ]),
    ])));
};

views.backups = async (root) => {
  const rows = await api("/backups");
  root.append(table(["Kind", "Target", "File", "Size", "Created", ""], rows, (row) =>
    el("tr", {}, [
      el("td", { textContent: row.kind }),
      el("td", { textContent: row.target }),
      el("td", { textContent: row.filename, className: "muted" }),
      el("td", { textContent: bytes(row.size) }),
      el("td", { textContent: row.created_at, className: "muted" }),
      el("td", {}, [
        el("a", { textContent: "download", href: `${API}/backups/${row.id}/download` }),
        actionButton("delete", async () => {
          await api(`/backups/${row.id}`, { method: "DELETE" });
          render("backups");
        }, "danger"),
      ]),
    ])));
};

views.logs = async (root) => {
  const rows = await api("/logs/operations");
  root.append(table(["When", "User", "Action", "Target", "OK"], rows, (row) =>
    el("tr", {}, [
      el("td", { textContent: row.created_at, className: "muted" }),
      el("td", { textContent: row.username }),
      el("td", { textContent: row.action }),
      el("td", { textContent: row.target, className: "muted" }),
      el("td", { textContent: row.success ? "yes" : "no", className: row.success ? "ok" : "error" }),
    ])));
};

views.terminal = async (root) => {
  const output = el("pre", { style: "max-height:62vh" });
  const input = el("input", { placeholder: "command", style: "flex:1" });
  root.append(output, el("div", { className: "row" }, [input]));

  const socket = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}${BASE}/ws/terminal`);
  socket.onmessage = (event) => {
    output.textContent += event.data;
    output.scrollTop = output.scrollHeight;
  };
  socket.onclose = () => output.append("\n[connection closed]\n");
  input.onkeydown = (event) => {
    if (event.key !== "Enter") return;
    socket.send(JSON.stringify({ type: "input", data: `${input.value}\n` }));
    input.value = "";
  };
  views.terminal.socket = socket;
};

function showPre(title, content) {
  const view = $("#view");
  view.textContent = "";
  view.append(el("div", { className: "row" }, [actionButton("← back", () => render(current))]));
  view.append(el("h3", { textContent: title }), el("pre", { textContent: content }));
}

function showEditor(path, content) {
  const view = $("#view");
  const area = el("textarea", { value: content });
  view.textContent = "";
  view.append(
    el("div", { className: "row" }, [
      el("span", { textContent: path, className: "muted" }),
      actionButton("Save", async () => {
        await api("/files/write", { method: "POST", body: { path, content: area.value } });
        toast("Saved");
      }, ""),
      actionButton("← back", () => render("files")),
    ]),
    area,
  );
}

const MENU = [
  ["overview", "Overview"],
  ["sites", "Sites"],
  ["databases", "Databases"],
  ["files", "Files"],
  ["cron", "Cron"],
  ["backups", "Backups"],
  ["logs", "Logs"],
  ["terminal", "Terminal"],
];

let current = "overview";

async function render(name) {
  current = name;
  if (views.terminal.socket && name !== "terminal") {
    views.terminal.socket.close();
    views.terminal.socket = null;
  }

  for (const link of document.querySelectorAll("#nav a")) {
    link.classList.toggle("active", link.dataset.view === name);
  }
  $("#view-title").textContent = MENU.find(([key]) => key === name)[1];

  const view = $("#view");
  view.textContent = "";
  try {
    await views[name](view);
  } catch (error) {
    view.append(el("p", { className: "error", textContent: error.message }));
  }
}

function buildNav() {
  const nav = $("#nav");
  nav.textContent = "";
  for (const [key, label] of MENU) {
    const link = el("a", { textContent: label });
    link.dataset.view = key;
    link.onclick = () => render(key);
    nav.append(link);
  }
}

function showLogin() {
  $("#app").classList.add("hidden");
  $("#login").classList.remove("hidden");
}

async function showApp(username) {
  $("#login").classList.add("hidden");
  $("#app").classList.remove("hidden");
  $("#whoami").textContent = username;
  buildNav();
  await render("overview");
}

$("#login-form").onsubmit = async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  $("#login-error").textContent = "";
  try {
    const result = await api("/auth/login", {
      method: "POST",
      body: {
        username: form.get("username"),
        password: form.get("password"),
        code: form.get("code") || "",
      },
    });
    await showApp(result.username);
  } catch (error) {
    $("#login-error").textContent = error.message;
  }
};

$("#logout").onclick = async () => {
  await api("/auth/logout", { method: "POST" });
  showLogin();
};

api("/auth/me")
  .then((user) => showApp(user.username))
  .catch(() => showLogin());

<script setup>
import { computed, h, onMounted, reactive, ref } from "vue";
import {
  NButton,
  NCard,
  NCheckbox,
  NDataTable,
  NDrawer,
  NDrawerContent,
  NDynamicTags,
  NEmpty,
  NForm,
  NFormItem,
  NGi,
  NGrid,
  NInput,
  NInputGroup,
  NInputNumber,
  NModal,
  NPopconfirm,
  NSelect,
  NSpace,
  NSwitch,
  NTabPane,
  NTabs,
  NTag,
  NText,
  useDialog,
  useMessage,
} from "naive-ui";
import { api } from "../api";
import { datetime, shorten } from "../format";

const message = useMessage();
const dialog = useDialog();

const sites = ref([]);
const groups = ref([]);
const upstreams = ref([]);
const projects = ref([]);
const phpVersions = ref([]);
const rewriteTemplates = ref([]);
const oneClickApps = ref([]);
const loading = ref(false);
const filter = ref("");
const groupFilter = ref(null);

const createOpen = ref(false);
const oneClickOpen = ref(false);
const detailOpen = ref(false);
const detailTab = ref("basics");

const draft = reactive({
  name: "",
  site_type: "php",
  domains: [],
  root: "",
  php_version: "",
  proxy_target: "",
  upstream_name: "",
  project_id: null,
  group_id: null,
  note: "",
});

const oneClick = reactive({ app: "wordpress", site_name: "", domains: [], php_version: "" });

const current = ref(null);
const detail = reactive({
  domains: [],
  redirects: [],
  proxies: [],
  dirAuths: [],
  rewrite: { content: "", suggested: "none" },
  config: { content: "", rendered: "", path: "" },
  ssl: null,
  logs: [],
});

const SITE_TYPES = [
  { label: "PHP", value: "php" },
  { label: "Static", value: "static" },
  { label: "Reverse proxy", value: "proxy" },
  { label: "Load balanced", value: "balance" },
  { label: "Node.js", value: "node" },
  { label: "Python", value: "python" },
  { label: "Java", value: "java" },
  { label: "Go", value: "go" },
  { label: ".NET", value: "dotnet" },
];

const typeLabel = (value) => SITE_TYPES.find((item) => item.value === value)?.label || value;

const filtered = computed(() => {
  const needle = filter.value.trim().toLowerCase();
  return sites.value.filter((site) => {
    if (groupFilter.value && site.group_id !== groupFilter.value) return false;
    if (!needle) return true;
    return (
      site.name.includes(needle) ||
      site.domains.join(" ").includes(needle) ||
      site.root.toLowerCase().includes(needle)
    );
  });
});

const groupOptions = computed(() =>
  groups.value.map((group) => ({ label: group.name, value: group.id })),
);
const upstreamOptions = computed(() =>
  upstreams.value.map((pool) => ({ label: `${pool.name} (${pool.nodes.length} nodes)`, value: pool.name })),
);
const projectOptions = computed(() =>
  projects.value.map((project) => ({ label: `${project.name}:${project.port}`, value: project.id })),
);
const phpOptions = computed(() =>
  phpVersions.value.map((item) => ({ label: item.label, value: item.version })),
);
const rewriteOptions = computed(() =>
  rewriteTemplates.value.map((item) => ({ label: item.label, value: item.key })),
);

async function load() {
  loading.value = true;
  try {
    const [siteRows, groupRows, pools, projectRows, php, templates, apps] = await Promise.all([
      api("/sites"),
      api("/sites/groups").catch(() => []),
      api("/sites/upstreams").catch(() => []),
      api("/projects").catch(() => []),
      api("/php").catch(() => []),
      api("/sites/rewrite-templates").catch(() => []),
      api("/one-click").catch(() => []),
    ]);
    sites.value = siteRows;
    groups.value = groupRows;
    upstreams.value = pools;
    projects.value = projectRows;
    phpVersions.value = php;
    rewriteTemplates.value = templates;
    oneClickApps.value = apps;
    if (!draft.php_version && php.length) draft.php_version = php.at(-1).version;
  } finally {
    loading.value = false;
  }
}

async function createSite() {
  if (!draft.name.trim()) return message.warning("A site name is required");
  try {
    await api("/sites", { method: "POST", body: { ...draft } });
    message.success(`${draft.name} created`);
    createOpen.value = false;
    Object.assign(draft, { name: "", domains: [], root: "", proxy_target: "", note: "" });
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function deploy() {
  if (!oneClick.site_name.trim()) return message.warning("A site name is required");
  try {
    const result = await api("/one-click/deploy", { method: "POST", body: { ...oneClick } });
    message.success(
      result.task_id
        ? `${oneClick.site_name} created, files are downloading (task ${result.task_id})`
        : `${oneClick.site_name} created`,
    );
    oneClickOpen.value = false;
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function toggleSite(site) {
  await api(`/sites/${site.id}/${site.enabled ? "stop" : "start"}`, { method: "POST" });
  message.success(`${site.name} ${site.enabled ? "stopped" : "started"}`);
  await load();
}

function removeSite(site) {
  dialog.warning({
    title: `Delete ${site.name}?`,
    content: "The vhost and panel records go. Tick the box to delete the files too.",
    positiveText: "Delete",
    negativeText: "Cancel",
    action: () => {
      const wipe = ref(false);
      return h(NSpace, {}, {
        default: () => [
          h(NCheckbox, { checked: wipe.value, "onUpdate:checked": (v) => (wipe.value = v) },
            { default: () => "Also delete the site files" }),
          h(NButton, {
            type: "error",
            size: "small",
            onClick: async () => {
              await api(`/sites/${site.id}`, { method: "DELETE", params: { remove_files: wipe.value } });
              message.success(`${site.name} removed`);
              dialog.destroyAll();
              await load();
            },
          }, { default: () => "Delete" }),
        ],
      });
    },
  });
}

async function openDetail(site) {
  current.value = site;
  detailOpen.value = true;
  detailTab.value = "basics";
  await loadDetail();
}

async function loadDetail() {
  const id = current.value.id;
  const [domains, redirects, proxies, dirAuths, rewrite, ssl] = await Promise.all([
    api(`/sites/${id}/domains`).catch(() => []),
    api(`/sites/${id}/redirects`).catch(() => []),
    api(`/sites/${id}/proxies`).catch(() => []),
    api(`/sites/${id}/dir-auth`).catch(() => []),
    api(`/sites/${id}/rewrite`).catch(() => ({ content: "", suggested: "none" })),
    api(`/ssl/${id}`).catch(() => null),
  ]);
  Object.assign(detail, { domains, redirects, proxies, dirAuths, rewrite, ssl });
  current.value = await api(`/sites/${id}`);
}

async function saveBasics() {
  try {
    const site = current.value;
    await api(`/sites/${site.id}`, {
      method: "PATCH",
      body: {
        site_type: site.site_type,
        run_path: site.run_path,
        index_files: site.index_files,
        php_version: site.php_version,
        proxy_target: site.proxy_target,
        upstream_name: site.upstream_name,
        project_id: site.project_id,
        group_id: site.group_id,
        note: site.note,
      },
    });
    message.success("Saved");
    await Promise.all([load(), loadDetail()]);
  } catch (error) {
    message.error(error.message);
  }
}

async function saveHardening() {
  try {
    const site = current.value;
    await api(`/sites/${site.id}`, {
      method: "PATCH",
      body: {
        deny_extensions: site.deny_extensions,
        anti_leech_enabled: site.anti_leech_enabled,
        anti_leech_extensions: site.anti_leech_extensions,
        anti_leech_allow: site.anti_leech_allow,
        anti_leech_return: site.anti_leech_return,
        limit_rate: site.limit_rate,
        limit_conn: site.limit_conn,
        limit_req: site.limit_req,
        client_max_body: site.client_max_body,
        gzip_enabled: site.gzip_enabled,
        cache_enabled: site.cache_enabled,
        cache_expires: site.cache_expires,
        waf_enabled: site.waf_enabled,
        ip_allow: site.ip_allow,
        ip_deny: site.ip_deny,
        extra_headers: site.extra_headers,
        hsts: site.hsts,
        ssl_protocols: site.ssl_protocols,
      },
    });
    message.success("Saved");
    await loadDetail();
  } catch (error) {
    message.error(error.message);
  }
}

const newDomain = ref("");
async function addDomain() {
  if (!newDomain.value.trim()) return;
  try {
    await api(`/sites/${current.value.id}/domains`, {
      method: "POST",
      body: { name: newDomain.value.trim(), port: 80 },
    });
    newDomain.value = "";
    await Promise.all([loadDetail(), load()]);
  } catch (error) {
    message.error(error.message);
  }
}

async function removeDomain(row) {
  try {
    await api(`/sites/${current.value.id}/domains/${row.id}`, { method: "DELETE" });
    await Promise.all([loadDetail(), load()]);
  } catch (error) {
    message.error(error.message);
  }
}

const redirectDraft = reactive({ kind: "path", source: "/", target: "", code: 301, keep_path: true });
async function addRedirect() {
  try {
    await api(`/sites/${current.value.id}/redirects`, { method: "POST", body: { ...redirectDraft } });
    message.success("Redirect added");
    await loadDetail();
  } catch (error) {
    message.error(error.message);
  }
}

const proxyDraft = reactive({
  location: "/api",
  target: "",
  host_header: "$host",
  cache_enabled: false,
  cache_time: 3600,
  websocket: true,
  replace_rules: "",
});
async function addProxy() {
  try {
    await api(`/sites/${current.value.id}/proxies`, { method: "POST", body: { ...proxyDraft } });
    message.success("Proxy added");
    await loadDetail();
  } catch (error) {
    message.error(error.message);
  }
}

const authDraft = reactive({ name: "", location: "/", username: "", password: "" });
async function addDirAuth() {
  try {
    await api(`/sites/${current.value.id}/dir-auth`, { method: "POST", body: { ...authDraft } });
    message.success("Directory protected");
    await loadDetail();
  } catch (error) {
    message.error(error.message);
  }
}

const rewritePick = ref("none");
async function applyRewriteTemplate() {
  const template = await api(`/sites/rewrite-templates/${rewritePick.value}`);
  detail.rewrite.content = template.body;
}

async function saveRewrite() {
  try {
    await api(`/sites/${current.value.id}/rewrite`, {
      method: "POST",
      body: { content: detail.rewrite.content },
    });
    message.success("Rewrite rules saved and nginx reloaded");
  } catch (error) {
    message.error(error.message);
  }
}

async function loadConfig() {
  detail.config = await api(`/sites/${current.value.id}/config`);
}

async function saveConfig() {
  try {
    await api(`/sites/${current.value.id}/config`, {
      method: "POST",
      body: { content: detail.config.content },
    });
    message.success("Config saved and nginx reloaded");
  } catch (error) {
    message.error(error.message);
  }
}

const logKind = ref("access");
async function loadLogs() {
  const result = await api(`/logs/site/${current.value.id}`, { params: { kind: logKind.value, lines: 300 } });
  detail.logs = result.lines;
}

const certDraft = reactive({ fullchain: "", private_key: "" });
async function issueCert() {
  try {
    message.loading("Asking Let's Encrypt…");
    await api(`/ssl/${current.value.id}/issue`, { method: "POST", body: { domains: [], force_https: true } });
    message.success("Certificate issued");
    await loadDetail();
  } catch (error) {
    message.error(error.message);
  }
}

async function uploadCert() {
  try {
    await api(`/ssl/${current.value.id}/upload`, { method: "POST", body: { ...certDraft } });
    message.success("Certificate installed");
    await loadDetail();
  } catch (error) {
    message.error(error.message);
  }
}

async function setForceHttps(value) {
  await api(`/ssl/${current.value.id}/force-https`, { method: "POST", params: { enabled: value } });
  await loadDetail();
}

async function disableSsl() {
  await api(`/ssl/${current.value.id}/disable`, { method: "POST" });
  message.success("SSL disabled");
  await loadDetail();
}

const newGroup = ref("");
async function addGroup() {
  if (!newGroup.value.trim()) return;
  await api("/sites/groups", { method: "POST", body: { name: newGroup.value.trim() } });
  newGroup.value = "";
  await load();
}

const columns = computed(() => [
  {
    title: "Site",
    key: "name",
    render: (row) =>
      h("div", {}, [
        h(NButton, { text: true, type: "primary", onClick: () => openDetail(row) }, { default: () => row.name }),
        h("div", { class: "muted" }, shorten(row.domains.join(", "), 56)),
      ]),
  },
  { title: "Type", key: "site_type", width: 120, render: (row) => typeLabel(row.site_type) },
  {
    title: "PHP",
    key: "php_version",
    width: 80,
    render: (row) => (row.site_type === "php" ? row.php_version || "—" : "—"),
  },
  { title: "Root", key: "root", ellipsis: { tooltip: true } },
  { title: "Group", key: "group_name", width: 110, render: (row) => row.group_name || "—" },
  {
    title: "SSL",
    key: "ssl_enabled",
    width: 110,
    render: (row) =>
      h(
        NTag,
        { size: "small", bordered: false, type: row.ssl_enabled ? "success" : "default" },
        { default: () => (row.ssl_enabled ? (row.force_https ? "forced" : "on") : "off") },
      ),
  },
  {
    title: "Status",
    key: "enabled",
    width: 90,
    render: (row) =>
      h(
        NTag,
        { size: "small", bordered: false, type: row.enabled ? "success" : "warning" },
        { default: () => (row.enabled ? "running" : "stopped") },
      ),
  },
  {
    title: "Actions",
    key: "actions",
    width: 210,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          h(NButton, { size: "tiny", secondary: true, onClick: () => openDetail(row) }, { default: () => "Manage" }),
          h(NButton, { size: "tiny", secondary: true, onClick: () => toggleSite(row) },
            { default: () => (row.enabled ? "Stop" : "Start") }),
          h(NButton, { size: "tiny", type: "error", secondary: true, onClick: () => removeSite(row) },
            { default: () => "Delete" }),
        ],
      }),
  },
]);

const domainColumns = [
  { title: "Domain", key: "name" },
  { title: "Port", key: "port", width: 80 },
  {
    title: "",
    key: "actions",
    width: 90,
    render: (row) =>
      h(NButton, { size: "tiny", type: "error", secondary: true, onClick: () => removeDomain(row) },
        { default: () => "Remove" }),
  },
];

const redirectColumns = [
  { title: "Kind", key: "kind", width: 80 },
  { title: "From", key: "source" },
  { title: "To", key: "target", ellipsis: { tooltip: true } },
  { title: "Code", key: "code", width: 70 },
  {
    title: "",
    key: "actions",
    width: 90,
    render: (row) =>
      h(NButton, {
        size: "tiny", type: "error", secondary: true,
        onClick: async () => {
          await api(`/sites/redirects/${row.id}`, { method: "DELETE" });
          await loadDetail();
        },
      }, { default: () => "Remove" }),
  },
];

const proxyColumns = [
  { title: "Location", key: "location", width: 120 },
  { title: "Target", key: "target", ellipsis: { tooltip: true } },
  { title: "Cache", key: "cache_enabled", width: 80, render: (row) => (row.cache_enabled ? `${row.cache_time}s` : "off") },
  {
    title: "",
    key: "actions",
    width: 90,
    render: (row) =>
      h(NButton, {
        size: "tiny", type: "error", secondary: true,
        onClick: async () => {
          await api(`/sites/proxies/${row.id}`, { method: "DELETE" });
          await loadDetail();
        },
      }, { default: () => "Remove" }),
  },
];

const authColumns = [
  { title: "Name", key: "name" },
  { title: "Location", key: "location", width: 120 },
  { title: "User", key: "username", width: 120 },
  {
    title: "",
    key: "actions",
    width: 90,
    render: (row) =>
      h(NButton, {
        size: "tiny", type: "error", secondary: true,
        onClick: async () => {
          await api(`/sites/dir-auth/${row.id}`, { method: "DELETE" });
          await loadDetail();
        },
      }, { default: () => "Remove" }),
  },
];

onMounted(load);
</script>

<template>
  <div>
    <div class="toolbar">
      <n-button type="primary" @click="createOpen = true">Add site</n-button>
      <n-button secondary @click="oneClickOpen = true">One-click install</n-button>
      <n-input v-model:value="filter" placeholder="Filter by name, domain or root" clearable style="width: 260px" />
      <n-select
        v-model:value="groupFilter"
        :options="groupOptions"
        placeholder="All groups"
        clearable
        style="width: 160px"
      />
      <span class="spacer" />
      <n-text depth="3">{{ filtered.length }} of {{ sites.length }}</n-text>
      <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
    </div>

    <n-card size="small">
      <n-data-table
        :columns="columns"
        :data="filtered"
        :loading="loading"
        :bordered="false"
        :row-key="(row) => row.id"
        size="small"
      />
    </n-card>

    <!-- create ------------------------------------------------------------ -->
    <n-modal v-model:show="createOpen" preset="card" title="Add site" style="max-width: 580px">
      <n-form label-placement="top" size="small">
        <n-grid cols="2" :x-gap="12">
          <n-gi>
            <n-form-item label="Site name">
              <n-input v-model:value="draft.name" placeholder="example.com" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="Type">
              <n-select v-model:value="draft.site_type" :options="SITE_TYPES" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="Extra domains">
          <n-dynamic-tags v-model:value="draft.domains" />
        </n-form-item>
        <n-grid cols="2" :x-gap="12">
          <n-gi>
            <n-form-item label="Document root">
              <n-input v-model:value="draft.root" placeholder="defaults to the www root" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item v-if="draft.site_type === 'php'" label="PHP version">
              <n-select v-model:value="draft.php_version" :options="phpOptions" />
            </n-form-item>
            <n-form-item v-else-if="draft.site_type === 'proxy'" label="Proxy target">
              <n-input v-model:value="draft.proxy_target" placeholder="http://127.0.0.1:8080" />
            </n-form-item>
            <n-form-item v-else-if="draft.site_type === 'balance'" label="Upstream pool">
              <n-select v-model:value="draft.upstream_name" :options="upstreamOptions" />
            </n-form-item>
            <n-form-item v-else label="Bind a project">
              <n-select v-model:value="draft.project_id" :options="projectOptions" clearable />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-grid cols="2" :x-gap="12">
          <n-gi>
            <n-form-item label="Group">
              <n-select v-model:value="draft.group_id" :options="groupOptions" clearable />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="Note">
              <n-input v-model:value="draft.note" />
            </n-form-item>
          </n-gi>
        </n-grid>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="createOpen = false">Cancel</n-button>
          <n-button type="primary" @click="createSite">Create</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- one click --------------------------------------------------------- -->
    <n-modal v-model:show="oneClickOpen" preset="card" title="One-click install" style="max-width: 520px">
      <n-form label-placement="top" size="small">
        <n-form-item label="Application">
          <n-select
            v-model:value="oneClick.app"
            :options="oneClickApps.map((a) => ({ label: a.label, value: a.key }))"
          />
        </n-form-item>
        <p class="muted" style="margin-top: -6px">
          {{ oneClickApps.find((a) => a.key === oneClick.app)?.description }}
        </p>
        <n-form-item label="Site name">
          <n-input v-model:value="oneClick.site_name" placeholder="blog.example.com" />
        </n-form-item>
        <n-form-item label="Extra domains">
          <n-dynamic-tags v-model:value="oneClick.domains" />
        </n-form-item>
        <n-form-item label="PHP version">
          <n-select v-model:value="oneClick.php_version" :options="phpOptions" clearable />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="oneClickOpen = false">Cancel</n-button>
          <n-button type="primary" @click="deploy">Install</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- detail ------------------------------------------------------------ -->
    <n-drawer v-model:show="detailOpen" :width="820" placement="right">
      <n-drawer-content v-if="current" :title="current.name" closable>
        <n-tabs v-model:value="detailTab" type="line" animated>
          <n-tab-pane name="basics" tab="Basics">
            <n-form label-placement="top" size="small">
              <n-grid cols="2" :x-gap="12">
                <n-gi>
                  <n-form-item label="Type">
                    <n-select v-model:value="current.site_type" :options="SITE_TYPES" />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="Run path (relative to root)">
                    <n-input v-model:value="current.run_path" placeholder="/public" />
                  </n-form-item>
                </n-gi>
              </n-grid>
              <n-form-item label="Index files">
                <n-input v-model:value="current.index_files" />
              </n-form-item>
              <n-grid cols="2" :x-gap="12">
                <n-gi>
                  <n-form-item v-if="current.site_type === 'php'" label="PHP version">
                    <n-select v-model:value="current.php_version" :options="phpOptions" />
                  </n-form-item>
                  <n-form-item v-else-if="current.site_type === 'proxy'" label="Proxy target">
                    <n-input v-model:value="current.proxy_target" />
                  </n-form-item>
                  <n-form-item v-else-if="current.site_type === 'balance'" label="Upstream pool">
                    <n-select v-model:value="current.upstream_name" :options="upstreamOptions" />
                  </n-form-item>
                  <n-form-item v-else label="Bound project">
                    <n-select v-model:value="current.project_id" :options="projectOptions" clearable />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="Group">
                    <n-select v-model:value="current.group_id" :options="groupOptions" clearable />
                  </n-form-item>
                </n-gi>
              </n-grid>
              <n-form-item label="Note">
                <n-input v-model:value="current.note" type="textarea" :rows="2" />
              </n-form-item>
              <dl class="kv">
                <dt>Root</dt><dd class="mono">{{ current.root }}</dd>
                <dt>Created</dt><dd>{{ datetime(current.created_at) }}</dd>
              </dl>
              <n-space style="margin-top: 14px">
                <n-button type="primary" size="small" @click="saveBasics">Save</n-button>
              </n-space>
            </n-form>
          </n-tab-pane>

          <n-tab-pane name="domains" tab="Domains">
            <n-input-group style="margin-bottom: 12px">
              <n-input v-model:value="newDomain" placeholder="www.example.com" @keyup.enter="addDomain" />
              <n-button type="primary" @click="addDomain">Add</n-button>
            </n-input-group>
            <n-data-table :columns="domainColumns" :data="detail.domains" size="small" :bordered="false" />
          </n-tab-pane>

          <n-tab-pane name="ssl" tab="SSL">
            <div v-if="detail.ssl">
              <dl class="kv">
                <dt>Status</dt>
                <dd>
                  <n-tag size="small" :bordered="false" :type="detail.ssl.ssl_enabled ? 'success' : 'default'">
                    {{ detail.ssl.ssl_enabled ? "enabled" : "disabled" }}
                  </n-tag>
                </dd>
                <dt>Issuer</dt><dd>{{ detail.ssl.issuer || "—" }}</dd>
                <dt>Expires</dt><dd>{{ datetime(detail.ssl.not_after) || "—" }}</dd>
                <dt>Domains</dt><dd>{{ detail.ssl.domains.join(", ") || "—" }}</dd>
              </dl>
              <n-space style="margin: 14px 0">
                <n-button size="small" type="primary" @click="issueCert">Issue with Let's Encrypt</n-button>
                <n-button size="small" :disabled="!detail.ssl.ssl_enabled"
                  @click="setForceHttps(!detail.ssl.force_https)">
                  {{ detail.ssl.force_https ? "Stop forcing HTTPS" : "Force HTTPS" }}
                </n-button>
                <n-popconfirm @positive-click="disableSsl">
                  <template #trigger>
                    <n-button size="small" type="error" secondary :disabled="!detail.ssl.ssl_enabled">
                      Disable SSL
                    </n-button>
                  </template>
                  The vhost goes back to plain HTTP. The certificate files stay on disk.
                </n-popconfirm>
              </n-space>
              <n-form label-placement="top" size="small">
                <n-form-item label="Or paste your own certificate (fullchain.pem)">
                  <n-input v-model:value="certDraft.fullchain" type="textarea" :rows="4" class="mono" />
                </n-form-item>
                <n-form-item label="Private key (privkey.pem)">
                  <n-input v-model:value="certDraft.private_key" type="textarea" :rows="4" class="mono" />
                </n-form-item>
                <n-button size="small" @click="uploadCert">Install certificate</n-button>
              </n-form>
              <n-form label-placement="top" size="small" style="margin-top: 14px">
                <n-space align="center">
                  <n-switch v-model:value="current.hsts" size="small" />
                  <span>Send HSTS header</span>
                </n-space>
                <n-form-item label="TLS protocols" style="margin-top: 10px">
                  <n-input v-model:value="current.ssl_protocols" />
                </n-form-item>
                <n-button size="small" type="primary" @click="saveHardening">Save</n-button>
              </n-form>
            </div>
          </n-tab-pane>

          <n-tab-pane name="rewrite" tab="Pseudo-static">
            <n-space align="center" style="margin-bottom: 10px">
              <n-select v-model:value="rewritePick" :options="rewriteOptions" style="width: 220px" />
              <n-button size="small" @click="applyRewriteTemplate">Load template</n-button>
              <n-tag v-if="detail.rewrite.suggested && detail.rewrite.suggested !== 'none'"
                size="small" type="info" :bordered="false">
                detected: {{ detail.rewrite.suggested }}
              </n-tag>
            </n-space>
            <n-input v-model:value="detail.rewrite.content" type="textarea" :rows="16" class="mono" />
            <n-button type="primary" size="small" style="margin-top: 10px" @click="saveRewrite">
              Save and reload nginx
            </n-button>
          </n-tab-pane>

          <n-tab-pane name="redirects" tab="Redirects">
            <n-form inline label-placement="top" size="small">
              <n-form-item label="Kind">
                <n-select v-model:value="redirectDraft.kind" style="width: 110px"
                  :options="[{ label: 'Path', value: 'path' }, { label: 'Domain', value: 'domain' }]" />
              </n-form-item>
              <n-form-item label="From"><n-input v-model:value="redirectDraft.source" style="width: 150px" /></n-form-item>
              <n-form-item label="To"><n-input v-model:value="redirectDraft.target" style="width: 220px" placeholder="https://…" /></n-form-item>
              <n-form-item label="Code">
                <n-select v-model:value="redirectDraft.code" style="width: 90px"
                  :options="[301, 302, 307, 308].map((c) => ({ label: String(c), value: c }))" />
              </n-form-item>
              <n-form-item label=" "><n-button size="small" type="primary" @click="addRedirect">Add</n-button></n-form-item>
            </n-form>
            <n-data-table :columns="redirectColumns" :data="detail.redirects" size="small" :bordered="false" />
          </n-tab-pane>

          <n-tab-pane name="proxies" tab="Proxies">
            <n-form label-placement="top" size="small">
              <n-grid cols="3" :x-gap="10">
                <n-gi><n-form-item label="Location"><n-input v-model:value="proxyDraft.location" /></n-form-item></n-gi>
                <n-gi span="2"><n-form-item label="Target"><n-input v-model:value="proxyDraft.target" placeholder="http://127.0.0.1:9000" /></n-form-item></n-gi>
              </n-grid>
              <n-grid cols="3" :x-gap="10">
                <n-gi><n-form-item label="Host header"><n-input v-model:value="proxyDraft.host_header" /></n-form-item></n-gi>
                <n-gi>
                  <n-form-item label="Cache seconds">
                    <n-input-number v-model:value="proxyDraft.cache_time" :min="1" style="width: 100%" />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="Options">
                    <n-space>
                      <n-switch v-model:value="proxyDraft.cache_enabled" size="small" /> cache
                      <n-switch v-model:value="proxyDraft.websocket" size="small" /> ws
                    </n-space>
                  </n-form-item>
                </n-gi>
              </n-grid>
              <n-form-item label="Content replacements (from|to, one per line)">
                <n-input v-model:value="proxyDraft.replace_rules" type="textarea" :rows="2" class="mono" />
              </n-form-item>
              <n-button size="small" type="primary" @click="addProxy">Add proxy</n-button>
            </n-form>
            <n-data-table :columns="proxyColumns" :data="detail.proxies" size="small" :bordered="false" style="margin-top: 12px" />
          </n-tab-pane>

          <n-tab-pane name="hardening" tab="Hardening">
            <n-form label-placement="top" size="small">
              <n-grid cols="2" :x-gap="12">
                <n-gi>
                  <n-form-item label="Blocked extensions">
                    <n-input v-model:value="current.deny_extensions" placeholder="sql,bak,zip" />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="Max upload size">
                    <n-input v-model:value="current.client_max_body" placeholder="50m" />
                  </n-form-item>
                </n-gi>
              </n-grid>
              <n-space align="center" style="margin-bottom: 12px">
                <n-switch v-model:value="current.waf_enabled" size="small" /><span>Request filter (SQLi, scanners, odd methods)</span>
              </n-space>
              <n-space align="center" style="margin-bottom: 12px">
                <n-switch v-model:value="current.gzip_enabled" size="small" /><span>gzip</span>
                <n-switch v-model:value="current.cache_enabled" size="small" /><span>static cache</span>
                <n-input v-model:value="current.cache_expires" size="small" style="width: 90px" />
              </n-space>
              <n-space align="center" style="margin-bottom: 12px">
                <n-switch v-model:value="current.anti_leech_enabled" size="small" /><span>Hotlink protection</span>
              </n-space>
              <n-grid v-if="current.anti_leech_enabled" cols="3" :x-gap="10">
                <n-gi><n-form-item label="Extensions"><n-input v-model:value="current.anti_leech_extensions" /></n-form-item></n-gi>
                <n-gi><n-form-item label="Allowed referers"><n-input v-model:value="current.anti_leech_allow" /></n-form-item></n-gi>
                <n-gi><n-form-item label="Response"><n-input v-model:value="current.anti_leech_return" placeholder="404 or a URL" /></n-form-item></n-gi>
              </n-grid>
              <n-grid cols="3" :x-gap="10">
                <n-gi><n-form-item label="Rate limit (KB/s)"><n-input-number v-model:value="current.limit_rate" :min="0" style="width: 100%" /></n-form-item></n-gi>
                <n-gi><n-form-item label="Max connections / IP"><n-input-number v-model:value="current.limit_conn" :min="0" style="width: 100%" /></n-form-item></n-gi>
                <n-gi><n-form-item label="Requests / second / IP"><n-input-number v-model:value="current.limit_req" :min="0" style="width: 100%" /></n-form-item></n-gi>
              </n-grid>
              <n-grid cols="2" :x-gap="12">
                <n-gi><n-form-item label="Allow only these IPs"><n-input v-model:value="current.ip_allow" placeholder="10.0.0.0/8, 1.2.3.4" /></n-form-item></n-gi>
                <n-gi><n-form-item label="Deny these IPs"><n-input v-model:value="current.ip_deny" /></n-form-item></n-gi>
              </n-grid>
              <n-form-item label="Extra response headers (raw nginx)">
                <n-input v-model:value="current.extra_headers" type="textarea" :rows="3" class="mono"
                  placeholder='add_header X-Frame-Options "SAMEORIGIN";' />
              </n-form-item>
              <n-button type="primary" size="small" @click="saveHardening">Save and reload nginx</n-button>
            </n-form>
          </n-tab-pane>

          <n-tab-pane name="auth" tab="Password">
            <n-form inline label-placement="top" size="small">
              <n-form-item label="Name"><n-input v-model:value="authDraft.name" style="width: 130px" /></n-form-item>
              <n-form-item label="Location"><n-input v-model:value="authDraft.location" style="width: 120px" /></n-form-item>
              <n-form-item label="User"><n-input v-model:value="authDraft.username" style="width: 120px" /></n-form-item>
              <n-form-item label="Password"><n-input v-model:value="authDraft.password" type="password" style="width: 140px" /></n-form-item>
              <n-form-item label=" "><n-button size="small" type="primary" @click="addDirAuth">Protect</n-button></n-form-item>
            </n-form>
            <n-data-table :columns="authColumns" :data="detail.dirAuths" size="small" :bordered="false" />
          </n-tab-pane>

          <n-tab-pane name="config" tab="nginx config" @vue:mounted="loadConfig">
            <n-space style="margin-bottom: 10px">
              <n-button size="small" @click="loadConfig">Reload from disk</n-button>
              <n-button size="small" type="primary" @click="saveConfig">Save and test</n-button>
              <span class="muted mono">{{ detail.config.path }}</span>
            </n-space>
            <n-input v-model:value="detail.config.content" type="textarea" :rows="22" class="mono" />
            <p class="muted" style="margin-top: 8px">
              Saving the site from any other tab regenerates this file from the template.
            </p>
          </n-tab-pane>

          <n-tab-pane name="logs" tab="Logs" @vue:mounted="loadLogs">
            <n-space style="margin-bottom: 10px">
              <n-select v-model:value="logKind" style="width: 130px"
                :options="[{ label: 'Access', value: 'access' }, { label: 'Error', value: 'error' }]"
                @update:value="loadLogs" />
              <n-button size="small" @click="loadLogs">Refresh</n-button>
            </n-space>
            <n-card size="small" embedded>
              <pre class="log-pane mono">{{ detail.logs.join("\n") || "No log lines yet." }}</pre>
            </n-card>
          </n-tab-pane>
        </n-tabs>
      </n-drawer-content>
    </n-drawer>

    <n-card size="small" title="Groups" style="margin-top: 14px">
      <n-space align="center">
        <n-input-group style="width: 280px">
          <n-input v-model:value="newGroup" placeholder="New group name" @keyup.enter="addGroup" />
          <n-button type="primary" @click="addGroup">Add</n-button>
        </n-input-group>
        <n-space v-if="groups.length" class="chip-list">
          <n-tag v-for="group in groups" :key="group.id" closable size="small"
            @close="async () => { await api(`/sites/groups/${group.id}`, { method: 'DELETE' }); await load(); }">
            {{ group.name }}
          </n-tag>
        </n-space>
        <n-empty v-else size="small" description="No groups yet" />
      </n-space>
    </n-card>
  </div>
</template>

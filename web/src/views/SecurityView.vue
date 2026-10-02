<script setup>
import { computed, h, onMounted, reactive, ref } from "vue";
import {
  NAlert, NButton, NCard, NDataTable, NEmpty, NForm, NFormItem, NGi, NGrid, NInput,
  NPopconfirm, NProgress, NSelect, NSpace, NStatistic, NSwitch, NTabPane, NTabs, NTag,
  useDialog, useMessage,
} from "naive-ui";
import { api } from "../api";
import { datetime, number } from "../format";

const message = useMessage();
const dialog = useDialog();

const firewall = ref({ backend: "none", active: false, raw: "" });
const rules = ref([]);
const ipRules = ref([]);
const ports = ref([]);
const ping = ref({ enabled: true });
const ssh = ref(null);
const sshKeys = ref([]);
const sshActivity = ref({ history: [], failed: [], sessions: [] });
const audit = ref(null);
const kernel = ref([]);
const attempts = ref([]);
const sites = ref([]);
const scan = ref(null);
const loading = ref(false);

const portDraft = reactive({ port: "", protocol: "tcp", action: "accept", source: "", name: "" });
const ipDraft = reactive({ address: "", action: "drop", scope: "server", note: "" });
const sshDraft = ref({});
const keyDraft = ref("");
const scanSite = ref(null);

async function load() {
  loading.value = true;
  try {
    const [fw, ruleRows, ipRows, portRows, pingRow, auditRow, kernelRows, attemptRows, siteRows] =
      await Promise.all([
        api("/security/firewall").catch(() => ({ backend: "none", active: false, raw: "" })),
        api("/security/firewall/rules").catch(() => []),
        api("/security/ip-rules").catch(() => []),
        api("/security/firewall/ports").catch(() => []),
        api("/security/ping").catch(() => ({ enabled: true })),
        api("/security/audit").catch(() => null),
        api("/security/kernel").catch(() => []),
        api("/security/login-attempts").catch(() => []),
        api("/sites").catch(() => []),
      ]);
    firewall.value = fw;
    rules.value = ruleRows;
    ipRules.value = ipRows;
    ports.value = portRows;
    ping.value = pingRow;
    audit.value = auditRow;
    kernel.value = kernelRows;
    attempts.value = attemptRows;
    sites.value = siteRows;
  } finally {
    loading.value = false;
  }
}

async function loadSsh() {
  ssh.value = await api("/security/ssh").catch(() => null);
  if (ssh.value) sshDraft.value = { ...ssh.value.values };
  sshKeys.value = await api("/security/ssh/keys").catch(() => []);
  sshActivity.value = await api("/security/ssh/activity").catch(() => ({ history: [], failed: [], sessions: [] }));
}

async function toggleFirewall() {
  try {
    const result = await api("/security/firewall/toggle", {
      method: "POST", params: { enabled: !firewall.value.active },
    });
    result.ok ? message.success("Firewall switched") : message.error(result.message);
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function addPortRule() {
  if (!portDraft.port.trim()) return message.warning("A port is required");
  try {
    await api("/security/firewall/rules", { method: "POST", body: { ...portDraft } });
    message.success("Rule added");
    portDraft.port = "";
    portDraft.source = "";
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function addIpRule() {
  if (!ipDraft.address.trim()) return message.warning("An address is required");
  try {
    await api("/security/ip-rules", { method: "POST", body: { ...ipDraft } });
    message.success("Rule added");
    ipDraft.address = "";
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function saveSsh() {
  try {
    ssh.value = await api("/security/ssh", { method: "POST", body: { values: sshDraft.value } });
    sshDraft.value = { ...ssh.value.values };
    message.success("sshd_config updated — restart sshd to apply it");
  } catch (error) {
    message.error(error.message);
  }
}

async function restartSsh() {
  const result = await api("/security/ssh/restart", { method: "POST" });
  result.ok ? message.success("sshd restarted") : message.error(result.message);
}

async function addKey() {
  try {
    sshKeys.value = await api("/security/ssh/keys", { method: "POST", body: { public_key: keyDraft.value } });
    keyDraft.value = "";
    message.success("Key authorised");
  } catch (error) {
    message.error(error.message);
  }
}

async function runScan() {
  if (!scanSite.value) return message.warning("Pick a site");
  scan.value = await api(`/security/scan/${scanSite.value}`);
  message.success(`${scan.value.scanned} PHP files scanned, ${scan.value.findings.length} flagged`);
}

async function blockIp(address) {
  await api("/security/ip-rules", { method: "POST", body: { address, action: "drop", scope: "server", note: "blocked from Security" } });
  message.success(`${address} blocked`);
  await load();
}

async function setPing(value) {
  const result = await api("/security/ping", { method: "POST", params: { enabled: value } });
  result.ok ? message.success(`ICMP ${value ? "enabled" : "disabled"}`) : message.error(result.message);
  await load();
}

const severityType = (severity) =>
  ({ high: "error", medium: "warning", low: "info" })[severity] || "default";

const ruleColumns = [
  { title: "Port", key: "port", width: 110 },
  { title: "Protocol", key: "protocol", width: 100 },
  {
    title: "Action",
    key: "action",
    width: 100,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.action === "accept" ? "success" : "error" },
        { default: () => row.action }),
  },
  { title: "Source", key: "source", render: (row) => row.source || "anywhere" },
  { title: "Name", key: "name" },
  {
    title: "Enabled",
    key: "enabled",
    width: 90,
    render: (row) =>
      h(NSwitch, {
        value: row.enabled, size: "small",
        "onUpdate:value": async (value) => {
          await api(`/security/firewall/rules/${row.id}/enabled`, { method: "POST", params: { enabled: value } });
          await load();
        },
      }),
  },
  {
    title: "",
    key: "actions",
    width: 90,
    render: (row) =>
      h(NButton, {
        size: "tiny", type: "error", secondary: true,
        onClick: async () => {
          await api(`/security/firewall/rules/${row.id}`, { method: "DELETE" });
          await load();
        },
      }, { default: () => "Remove" }),
  },
];

const ipColumns = [
  { title: "Address", key: "address" },
  {
    title: "Action",
    key: "action",
    width: 100,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.action === "accept" ? "success" : "error" },
        { default: () => row.action }),
  },
  { title: "Scope", key: "scope", width: 100 },
  { title: "Note", key: "note", ellipsis: { tooltip: true } },
  { title: "Added", key: "created_at", width: 150, render: (row) => datetime(row.created_at) },
  {
    title: "",
    key: "actions",
    width: 90,
    render: (row) =>
      h(NButton, {
        size: "tiny", type: "error", secondary: true,
        onClick: async () => {
          await api(`/security/ip-rules/${row.id}`, { method: "DELETE" });
          await load();
        },
      }, { default: () => "Remove" }),
  },
];

const portColumns = [
  { title: "Port", key: "port", width: 90 },
  { title: "Address", key: "address", width: 140 },
  { title: "Process", key: "process" },
  { title: "PID", key: "pid", width: 90 },
  { title: "Family", key: "family", width: 90 },
];

const failedColumns = [
  { title: "Address", key: "ip" },
  { title: "Tried user", key: "username" },
  { title: "Attempts", key: "attempts", width: 110 },
  {
    title: "",
    key: "actions",
    width: 100,
    render: (row) =>
      h(NButton, { size: "tiny", type: "error", secondary: true, onClick: () => blockIp(row.ip) },
        { default: () => "Block" }),
  },
];

const attemptColumns = [
  { title: "Address", key: "ip" },
  { title: "Usernames", key: "usernames", render: (row) => row.usernames.join(", ") || "—" },
  { title: "Attempts", key: "attempts", width: 100 },
  { title: "Last", key: "last", width: 160, render: (row) => datetime(row.last) },
  {
    title: "",
    key: "actions",
    width: 170,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          h(NButton, {
            size: "tiny", secondary: true,
            onClick: async () => {
              await api(`/security/login-attempts/${row.ip}`, { method: "DELETE" });
              message.success(`${row.ip} unblocked`);
              await load();
            },
          }, { default: () => "Unblock" }),
          h(NButton, { size: "tiny", type: "error", secondary: true, onClick: () => blockIp(row.ip) },
            { default: () => "Block" }),
        ],
      }),
  },
];

const siteOptions = computed(() => sites.value.map((site) => ({ label: site.name, value: site.id })));

onMounted(async () => {
  await load();
  await loadSsh();
});
</script>

<template>
  <div>
    <n-tabs type="line" animated>
      <n-tab-pane name="audit" tab="Audit">
        <n-grid v-if="audit" cols="1 l:3" responsive="screen" :x-gap="14" :y-gap="14">
          <n-gi>
            <n-card size="small">
              <div class="score-ring">
                <n-progress type="circle" :percentage="audit.score" :stroke-width="9" style="width: 90px"
                  :status="audit.score >= 75 ? 'success' : audit.score >= 50 ? 'warning' : 'error'" />
                <div>
                  <strong style="font-size: 15px">Security score</strong>
                  <p class="muted" style="margin: 4px 0 0">
                    {{ audit.passed }} of {{ audit.total }} checks pass
                  </p>
                  <n-button size="tiny" secondary style="margin-top: 8px" @click="load">Re-run</n-button>
                </div>
              </div>
            </n-card>
          </n-gi>
          <n-gi span="1 l:2">
            <n-card size="small" title="Kernel hardening">
              <n-data-table size="small" :bordered="false" :data="kernel" :row-key="(row) => row.key"
                :max-height="180"
                :columns="[
                  { title: 'Parameter', key: 'key' },
                  { title: 'Current', key: 'current', width: 110 },
                  { title: 'Wanted', key: 'expected', width: 100 },
                  { title: 'OK', key: 'ok', width: 70, render: (row) => (row.ok ? 'yes' : 'no') },
                ]" />
            </n-card>
          </n-gi>
        </n-grid>

        <n-card v-if="audit" size="small" title="Checks" style="margin-top: 14px">
          <div v-for="check in audit.checks" :key="check.name" class="check">
            <n-tag size="small" :bordered="false" :type="check.ok ? 'success' : severityType(check.severity)">
              {{ check.ok ? "pass" : check.severity }}
            </n-tag>
            <div>
              <strong>{{ check.name }}</strong>
              <p class="muted" style="margin: 2px 0 0">{{ check.detail }}</p>
              <p v-if="!check.ok && check.fix" class="muted" style="margin: 2px 0 0">→ {{ check.fix }}</p>
            </div>
          </div>
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="firewall" tab="Firewall">
        <div class="toolbar">
          <n-tag size="small" :bordered="false" :type="firewall.active ? 'success' : 'warning'">
            {{ firewall.backend }}: {{ firewall.active ? "active" : "inactive" }}
          </n-tag>
          <n-button size="small" :type="firewall.active ? 'error' : 'primary'" secondary
            :disabled="firewall.backend === 'none'" @click="toggleFirewall">
            {{ firewall.active ? "Turn off" : "Turn on" }}
          </n-button>
          <n-space align="center" :size="6">
            <n-switch :value="ping.enabled" size="small" @update:value="setPing" />
            <span>Answer ping</span>
          </n-space>
          <span class="spacer" />
          <n-button quaternary @click="api('/security/firewall/sync', { method: 'POST' }).then(() => { message.success('Rules re-applied'); load(); })">
            Re-apply rules
          </n-button>
        </div>

        <n-alert v-if="firewall.backend === 'none'" type="warning" :bordered="false" style="margin-bottom: 12px">
          No firewall tool was found. Install ufw or firewalld from the App store page.
        </n-alert>

        <n-card size="small" title="Port rules">
          <n-form inline label-placement="top" size="small" style="margin-bottom: 10px">
            <n-form-item label="Port"><n-input v-model:value="portDraft.port" placeholder="80 or 8000:8100" style="width: 130px" /></n-form-item>
            <n-form-item label="Protocol">
              <n-select v-model:value="portDraft.protocol" style="width: 100px"
                :options="['tcp', 'udp', 'both'].map((v) => ({ label: v, value: v }))" />
            </n-form-item>
            <n-form-item label="Action">
              <n-select v-model:value="portDraft.action" style="width: 110px"
                :options="['accept', 'drop'].map((v) => ({ label: v, value: v }))" />
            </n-form-item>
            <n-form-item label="Source"><n-input v-model:value="portDraft.source" placeholder="anywhere" style="width: 150px" /></n-form-item>
            <n-form-item label="Name"><n-input v-model:value="portDraft.name" style="width: 130px" /></n-form-item>
            <n-form-item label=" "><n-button size="small" type="primary" @click="addPortRule">Add</n-button></n-form-item>
          </n-form>
          <n-data-table :columns="ruleColumns" :data="rules" :bordered="false" size="small" :row-key="(row) => row.id" />
        </n-card>

        <n-card size="small" title="Listening ports" style="margin-top: 14px">
          <n-data-table :columns="portColumns" :data="ports" :bordered="false" size="small"
            :max-height="300" :row-key="(row) => `${row.port}-${row.address}`" />
        </n-card>

        <n-card size="small" title="Raw firewall state" style="margin-top: 14px">
          <pre class="log-pane mono">{{ firewall.raw }}</pre>
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="ip" tab="IP rules">
        <n-card size="small">
          <n-form inline label-placement="top" size="small" style="margin-bottom: 10px">
            <n-form-item label="Address"><n-input v-model:value="ipDraft.address" placeholder="1.2.3.4 or 10.0.0.0/8" style="width: 180px" /></n-form-item>
            <n-form-item label="Action">
              <n-select v-model:value="ipDraft.action" style="width: 110px"
                :options="['drop', 'accept'].map((v) => ({ label: v, value: v }))" />
            </n-form-item>
            <n-form-item label="Scope">
              <n-select v-model:value="ipDraft.scope" style="width: 130px"
                :options="[{ label: 'Whole server', value: 'server' }, { label: 'Panel only', value: 'panel' }]" />
            </n-form-item>
            <n-form-item label="Note"><n-input v-model:value="ipDraft.note" style="width: 180px" /></n-form-item>
            <n-form-item label=" "><n-button size="small" type="primary" @click="addIpRule">Add</n-button></n-form-item>
          </n-form>
          <n-data-table :columns="ipColumns" :data="ipRules" :bordered="false" size="small" :row-key="(row) => row.id" />
          <p class="muted" style="margin-top: 8px">
            A panel-scope <em>accept</em> rule turns the panel into allowlist-only: once one exists, every
            other address is refused at the login page.
          </p>
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="ssh" tab="SSH">
        <template v-if="ssh">
          <n-card size="small" title="sshd options">
            <n-grid cols="1 s:2 l:3" responsive="screen" :x-gap="14">
              <n-gi v-for="(choices, key) in ssh.editable" :key="key">
                <n-form-item :label="key" label-placement="top" size="small">
                  <n-select v-if="choices.length" v-model:value="sshDraft[key]"
                    :options="choices.map((v) => ({ label: v, value: v }))" />
                  <n-input v-else v-model:value="sshDraft[key]" class="mono" />
                </n-form-item>
              </n-gi>
            </n-grid>
            <n-space>
              <n-button type="primary" size="small" @click="saveSsh">Save</n-button>
              <n-popconfirm @positive-click="restartSsh">
                <template #trigger><n-button size="small" secondary>Restart sshd</n-button></template>
                Existing sessions survive a restart, but make sure you can still get in.
              </n-popconfirm>
            </n-space>
            <p class="muted mono" style="margin-top: 10px">{{ ssh.path }}</p>
          </n-card>

          <n-card size="small" title="Authorised keys" style="margin-top: 14px">
            <n-space style="margin-bottom: 10px">
              <n-input v-model:value="keyDraft" placeholder="ssh-ed25519 AAAA… you@laptop" style="width: 460px" />
              <n-button size="small" type="primary" @click="addKey">Authorise</n-button>
            </n-space>
            <n-data-table size="small" :bordered="false" :data="sshKeys" :row-key="(row) => row.index"
              :columns="[
                { title: 'Type', key: 'type', width: 150 },
                { title: 'Fingerprint', key: 'fingerprint', ellipsis: { tooltip: true } },
                { title: 'Comment', key: 'comment' },
              ]" />
          </n-card>

          <n-grid cols="1 l:2" responsive="screen" :x-gap="14" :y-gap="14" style="margin-top: 14px">
            <n-gi>
              <n-card size="small" title="Failed SSH logins">
                <n-data-table :columns="failedColumns" :data="sshActivity.failed" :bordered="false"
                  size="small" :max-height="280" :row-key="(row) => `${row.ip}-${row.username}`" />
              </n-card>
            </n-gi>
            <n-gi>
              <n-card size="small" title="Recent logins">
                <n-data-table size="small" :bordered="false" :data="sshActivity.history" :max-height="280"
                  :row-key="(row) => `${row.user}-${row.when}`"
                  :columns="[
                    { title: 'User', key: 'user', width: 110 },
                    { title: 'From', key: 'from' },
                    { title: 'When', key: 'when', ellipsis: { tooltip: true } },
                  ]" />
              </n-card>
            </n-gi>
          </n-grid>
        </template>
        <n-empty v-else description="Could not read sshd_config on this host." />
      </n-tab-pane>

      <n-tab-pane name="panel" tab="Panel access">
        <n-card size="small" title="Login attempts">
          <n-data-table :columns="attemptColumns" :data="attempts" :bordered="false" size="small"
            :row-key="(row) => row.ip" />
          <n-empty v-if="!attempts.length" style="padding: 24px 0"
            description="No failed panel logins in the current window." />
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="scan" tab="Malware scan">
        <n-card size="small">
          <n-space style="margin-bottom: 12px">
            <n-select v-model:value="scanSite" :options="siteOptions" placeholder="Pick a site" style="width: 240px" />
            <n-button size="small" type="primary" @click="runScan">Scan PHP files</n-button>
          </n-space>
          <p class="muted">
            Greps for the shapes web shells take — <code>eval(base64_decode(…))</code>, request-variable
            callbacks, <code>preg_replace</code> with the /e modifier. It is a smoke detector, not a virus scanner.
          </p>

          <template v-if="scan">
            <n-grid cols="3" :x-gap="12" style="margin: 14px 0">
              <n-gi><n-statistic label="Files scanned" :value="number(scan.scanned)" /></n-gi>
              <n-gi><n-statistic label="Flagged" :value="scan.findings.length" /></n-gi>
              <n-gi><n-statistic label="Truncated" :value="scan.truncated ? 'yes' : 'no'" /></n-gi>
            </n-grid>
            <n-data-table v-if="scan.findings.length" size="small" :bordered="false" :data="scan.findings"
              :row-key="(row) => row.path"
              :columns="[
                { title: 'File', key: 'path', ellipsis: { tooltip: true } },
                { title: 'Matched', key: 'pattern', ellipsis: { tooltip: true } },
                { title: 'Size', key: 'size', width: 100 },
              ]" />
            <n-alert v-else type="success" :bordered="false">Nothing suspicious in {{ scan.site }}.</n-alert>
          </template>
        </n-card>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<style scoped>
.check {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 9px 0;
  border-bottom: 1px solid rgba(130, 140, 155, 0.14);
}

.check:last-child {
  border-bottom: none;
}
</style>

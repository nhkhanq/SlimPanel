<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import {
  NAlert, NButton, NCard, NDataTable, NForm, NFormItem, NGi, NGrid, NInput,
  NPopconfirm, NSpace, NSwitch, NTabPane, NTabs, NTag, useMessage,
} from "naive-ui";
import { api } from "../api";
import { datetime } from "../format";
import { state, setUser } from "../store";

const message = useMessage();

const settings = ref(null);
const draft = ref({});
const nginxTest = ref(null);
const nginxConfig = ref(null);
const ssl = ref(null);
const sites = ref([]);
const loading = ref(false);

const passwords = reactive({ old_password: "", new_password: "" });
const totp = ref(null);
const totpCode = ref("");
const certDraft = reactive({ fullchain: "", private_key: "" });
const borrowSite = ref(null);

// How each editable key is rendered: a switch, a comma list, or plain text.
const BOOLEANS = new Set(["monitor_enabled", "recycle_bin"]);
const LISTS = new Set(["file_roots", "managed_services", "panel_ip_allowlist"]);
const SECRETS = new Set(["mysql_password", "redis_password", "pg_password"]);

const GROUPS = [
  { label: "Panel", keys: ["port", "entry_path", "session_max_age", "login_max_attempts", "login_block_minutes", "panel_ip_allowlist"] },
  { label: "Paths", keys: ["www_root", "log_root", "ftp_root", "file_roots", "cron_target"] },
  { label: "Services", keys: ["managed_services", "nginx_bin", "nginx_reload_cmd", "php_fpm_socket", "acme_bin", "acme_email"] },
  { label: "Databases", keys: ["mysql_host", "mysql_port", "mysql_user", "mysql_password", "pg_host", "pg_port", "pg_user", "pg_password", "redis_host", "redis_port", "redis_password", "mongo_uri"] },
  { label: "Behaviour", keys: ["monitor_enabled", "monitor_interval", "monitor_retention_days", "recycle_bin"] },
];

const editable = computed(() => new Set(settings.value?.editable || []));

function groupKeys(group) {
  return group.keys.filter((key) => editable.value.has(key));
}

async function load() {
  loading.value = true;
  try {
    settings.value = await api("/settings");
    draft.value = Object.fromEntries(
      (settings.value.editable || []).map((key) => {
        const value = settings.value[key];
        return [key, LISTS.has(key) ? (Array.isArray(value) ? value.join(", ") : value) : value];
      }),
    );
    ssl.value = await api("/settings/ssl").catch(() => null);
    sites.value = await api("/sites").catch(() => []);
  } finally {
    loading.value = false;
  }
}

async function guard(action, success) {
  try {
    const result = await action();
    if (success) message.success(success);
    return result;
  } catch (error) {
    message.error(error.message);
  }
}

async function saveSettings(keys) {
  const values = Object.fromEntries(keys.map((key) => [key, draft.value[key]]));
  await guard(
    () => api("/settings", { method: "POST", body: { values } }),
    "Saved to slimpanel.json — restart the panel to pick up port and path changes",
  );
  await load();
}

const changePassword = () =>
  guard(async () => {
    await api("/auth/password", { method: "POST", body: { ...passwords } });
    passwords.old_password = "";
    passwords.new_password = "";
  }, "Password changed");

const startTotp = () => guard(async () => (totp.value = await api("/auth/totp/setup", { method: "POST" })));

const enableTotp = () =>
  guard(async () => {
    await api("/auth/totp/enable", { method: "POST", body: { code: totpCode.value } });
    totp.value = null;
    totpCode.value = "";
    setUser(await api("/auth/me"));
  }, "Two-factor enabled");

const disableTotp = () =>
  guard(async () => {
    await api("/auth/totp/disable", { method: "POST" });
    setUser(await api("/auth/me"));
  }, "Two-factor disabled");

async function testNginx() {
  nginxTest.value = await api("/system/nginx/test");
}

async function loadNginxConfig() {
  nginxConfig.value = await api("/system/nginx/config");
}

async function reloadNginx() {
  const result = await api("/system/nginx/reload", { method: "POST" });
  result.ok ? message.success("nginx reloaded") : message.error(result.message);
}

async function selfSigned() {
  ssl.value = await guard(
    () => api("/settings/ssl/self-signed", { method: "POST", body: { common_name: "", days: 3650 } }),
    "Self-signed certificate generated",
  );
}

async function uploadCert() {
  ssl.value = await guard(
    () => api("/settings/ssl/upload", { method: "POST", body: { ...certDraft } }),
    "Certificate installed",
  );
}

async function borrow() {
  if (!borrowSite.value) return message.warning("Pick a site");
  ssl.value = await guard(
    () => api(`/settings/ssl/borrow/${borrowSite.value}`, { method: "POST" }),
    "Certificate copied from the site",
  );
}

async function togglePanelSsl(value) {
  const result = await guard(() => api(`/settings/ssl/enabled/${value}`, { method: "POST" }));
  if (result) {
    ssl.value = result;
    message.warning("Restart the panel for HTTPS to take effect");
  }
}

async function restartPanel() {
  await api("/settings/restart", { method: "POST" });
  message.warning("Restarting — reload the page in a few seconds");
}

onMounted(load);
</script>

<template>
  <div v-if="settings">
    <n-tabs type="line" animated>
      <n-tab-pane name="account" tab="Account">
        <n-grid cols="1 l:2" responsive="screen" :x-gap="14" :y-gap="14">
          <n-gi>
            <n-card size="small" title="Password">
              <n-form label-placement="top" size="small">
                <n-form-item label="Current password">
                  <n-input v-model:value="passwords.old_password" type="password" show-password-on="click" />
                </n-form-item>
                <n-form-item label="New password (8 characters or more)">
                  <n-input v-model:value="passwords.new_password" type="password" show-password-on="click" />
                </n-form-item>
                <n-button type="primary" size="small" @click="changePassword">Change password</n-button>
              </n-form>
            </n-card>
          </n-gi>

          <n-gi>
            <n-card size="small" title="Two-factor authentication">
              <template #header-extra>
                <n-tag size="small" :bordered="false" :type="state.user?.totp_enabled ? 'success' : 'default'">
                  {{ state.user?.totp_enabled ? "enabled" : "off" }}
                </n-tag>
              </template>

              <template v-if="state.user?.totp_enabled">
                <p class="muted">An authenticator code is required at every login.</p>
                <n-popconfirm @positive-click="disableTotp">
                  <template #trigger><n-button size="small" type="error" secondary>Turn off</n-button></template>
                  The panel goes back to password-only login.
                </n-popconfirm>
              </template>

              <template v-else-if="totp">
                <p class="muted">Add this secret to your authenticator, then confirm with a code.</p>
                <n-input :value="totp.secret" readonly class="mono" style="margin-bottom: 8px" />
                <n-input :value="totp.uri" readonly class="mono" style="margin-bottom: 8px" />
                <n-space>
                  <n-input v-model:value="totpCode" placeholder="123456" style="width: 120px" />
                  <n-button size="small" type="primary" @click="enableTotp">Confirm</n-button>
                </n-space>
              </template>

              <template v-else>
                <p class="muted">A second factor is the single biggest win for a panel on the open internet.</p>
                <n-button size="small" type="primary" @click="startTotp">Set up</n-button>
              </template>
            </n-card>
          </n-gi>
        </n-grid>
      </n-tab-pane>

      <n-tab-pane name="panel" tab="Panel settings">
        <n-alert type="info" :bordered="false" style="margin-bottom: 14px">
          Changes are written to <code>slimpanel.json</code>. The port, entry path and data paths only
          take effect after a restart.
        </n-alert>

        <n-card v-for="group in GROUPS" :key="group.label" size="small" :title="group.label"
          style="margin-bottom: 14px">
          <n-grid cols="1 s:2 l:3" responsive="screen" :x-gap="14">
            <n-gi v-for="key in groupKeys(group)" :key="key">
              <n-form-item :label="key" label-placement="top" size="small">
                <n-switch v-if="BOOLEANS.has(key)" v-model:value="draft[key]" />
                <n-input v-else v-model:value="draft[key]" class="mono"
                  :type="SECRETS.has(key) ? 'password' : 'text'" show-password-on="click"
                  :placeholder="LISTS.has(key) ? 'comma separated' : ''" />
              </n-form-item>
            </n-gi>
          </n-grid>
          <n-button size="small" type="primary" @click="saveSettings(groupKeys(group))">
            Save {{ group.label.toLowerCase() }}
          </n-button>
        </n-card>

        <n-card size="small" title="Restart">
          <n-space align="center">
            <n-popconfirm @positive-click="restartPanel">
              <template #trigger><n-button size="small" secondary>Restart the panel</n-button></template>
              The systemd unit is restarted. Sites keep serving; only the panel blinks.
            </n-popconfirm>
            <span class="muted">Needed after changing the port, entry path or HTTPS setting.</span>
          </n-space>
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="https" tab="Panel HTTPS">
        <n-card v-if="ssl" size="small" title="Certificate">
          <dl class="kv">
            <dt>HTTPS</dt>
            <dd>
              <n-space align="center" :size="8">
                <n-switch :value="ssl.enabled" size="small" @update:value="togglePanelSsl" />
                <span>{{ ssl.enabled ? "on" : "off" }}</span>
              </n-space>
            </dd>
            <dt>Certificate</dt><dd>{{ ssl.cert_exists ? ssl.cert_path : "none installed" }}</dd>
            <dt>Subject</dt><dd>{{ ssl.subject || "—" }}</dd>
            <dt>Expires</dt><dd>{{ datetime(ssl.not_after) || "—" }}</dd>
            <dt>Self-signed</dt><dd>{{ ssl.self_signed ? "yes" : "no" }}</dd>
          </dl>

          <n-space style="margin: 14px 0">
            <n-button size="small" @click="selfSigned">Generate self-signed</n-button>
            <n-space align="center" :size="6">
              <n-select v-model:value="borrowSite" style="width: 200px" placeholder="Copy from a site"
                :options="sites.filter((s) => s.ssl_enabled).map((s) => ({ label: s.name, value: s.name }))" />
              <n-button size="small" @click="borrow">Use it</n-button>
            </n-space>
          </n-space>

          <n-form label-placement="top" size="small">
            <n-form-item label="Or paste a certificate (fullchain.pem)">
              <n-input v-model:value="certDraft.fullchain" type="textarea" :rows="4" class="mono" />
            </n-form-item>
            <n-form-item label="Private key">
              <n-input v-model:value="certDraft.private_key" type="textarea" :rows="4" class="mono" />
            </n-form-item>
            <n-button size="small" @click="uploadCert">Install</n-button>
          </n-form>
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="nginx" tab="nginx" @vue:mounted="loadNginxConfig">
        <n-card size="small" title="Wiring">
          <p class="muted">
            SlimPanel writes its vhosts to its own directory. Add this include to your nginx.conf
            <code>http</code> block, then reload.
          </p>
          <n-input :value="settings.nginx_include_snippet" readonly type="textarea" :rows="2" class="mono" />
          <n-space style="margin-top: 12px">
            <n-button size="small" @click="testNginx">Test config</n-button>
            <n-button size="small" type="primary" @click="reloadNginx">Reload nginx</n-button>
          </n-space>
          <n-alert v-if="nginxTest" :type="nginxTest.ok ? 'success' : 'error'" :bordered="false"
            style="margin-top: 12px">
            <pre class="mono" style="margin: 0; white-space: pre-wrap">{{ nginxTest.message }}</pre>
          </n-alert>
        </n-card>

        <n-card v-if="nginxConfig" size="small" title="nginx.conf" style="margin-top: 14px">
          <template #header-extra>
            <n-tag size="small" :bordered="false" :type="nginxConfig.includes_slimpanel ? 'success' : 'warning'">
              {{ nginxConfig.includes_slimpanel ? "include present" : "include missing" }}
            </n-tag>
          </template>
          <p class="muted mono">{{ nginxConfig.path || "not found" }}</p>
          <pre class="log-pane mono">{{ nginxConfig.content }}</pre>
          <p class="muted" style="margin-top: 8px">Read-only — the panel never rewrites your nginx.conf.</p>
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="about" tab="About">
        <n-card size="small" title="Effective configuration">
          <n-data-table
            size="small"
            :bordered="false"
            :max-height="520"
            :data="Object.entries(settings).filter(([key]) => key !== 'editable').map(([key, value]) => ({ key, value: Array.isArray(value) ? value.join(', ') : String(value) }))"
            :row-key="(row) => row.key"
            :columns="[
              { title: 'Key', key: 'key', width: 240 },
              { title: 'Value', key: 'value', ellipsis: { tooltip: true } },
            ]"
          />
        </n-card>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

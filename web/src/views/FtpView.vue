<script setup>
import { h, onMounted, reactive, ref } from "vue";
import {
  NAlert, NButton, NCard, NDataTable, NEmpty, NForm, NFormItem, NGi, NGrid, NInput,
  NInputNumber, NModal, NSpace, NSwitch, NTag, useDialog, useMessage,
} from "naive-ui";
import { api } from "../api";

const message = useMessage();
const dialog = useDialog();

const status = ref(null);
const users = ref([]);
const logs = ref([]);
const loading = ref(false);
const createOpen = ref(false);
const draft = reactive({ username: "", password: "", home: "", quota_mb: 0, note: "" });

async function load() {
  loading.value = true;
  try {
    const [statusRow, rows] = await Promise.all([
      api("/ftp/status"),
      api("/ftp").catch(() => []),
    ]);
    status.value = statusRow;
    users.value = rows;
  } finally {
    loading.value = false;
  }
}

async function loadLogs() {
  logs.value = (await api("/ftp/logs", { params: { lines: 200 } })).lines;
}

async function create() {
  if (!draft.username.trim()) return message.warning("A username is required");
  try {
    const row = await api("/ftp", { method: "POST", body: { ...draft } });
    message.success(`${row.username} created with password ${row.password}`);
    createOpen.value = false;
    Object.assign(draft, { username: "", password: "", home: "", quota_mb: 0, note: "" });
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function newPassword(row) {
  const result = await api(`/ftp/${row.id}/password`, { method: "POST", body: { password: "" } });
  dialog.info({
    title: `${result.username} password`,
    content: () => h("code", { class: "mono" }, result.password),
    positiveText: "Close",
  });
  await load();
}

function remove(row) {
  dialog.warning({
    title: `Delete ${row.username}?`,
    content: "The FTP account goes. The home directory stays on disk.",
    positiveText: "Delete",
    negativeText: "Cancel",
    onPositiveClick: async () => {
      await api(`/ftp/${row.id}`, { method: "DELETE" });
      message.success("Removed");
      await load();
    },
  });
}

async function serviceAction(action) {
  const result = await api(`/ftp/service/${action}`, { method: "POST" });
  result.ok ? message.success(`FTP ${action}ed`) : message.error(result.message);
  await load();
}

const columns = [
  { title: "User", key: "username" },
  { title: "Home", key: "home", ellipsis: { tooltip: true } },
  { title: "Quota", key: "quota_mb", width: 100, render: (row) => (row.quota_mb ? `${row.quota_mb} MB` : "unlimited") },
  { title: "Password", key: "password", width: 150, render: (row) => h("code", { class: "mono" }, row.password) },
  {
    title: "Enabled",
    key: "enabled",
    width: 90,
    render: (row) =>
      h(NSwitch, {
        value: row.enabled, size: "small",
        "onUpdate:value": async (value) => {
          await api(`/ftp/${row.id}/enabled`, { method: "POST", params: { enabled: value } });
          await load();
        },
      }),
  },
  {
    title: "Actions",
    key: "actions",
    width: 200,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          h(NButton, { size: "tiny", secondary: true, onClick: () => newPassword(row) }, { default: () => "New password" }),
          h(NButton, { size: "tiny", type: "error", secondary: true, onClick: () => remove(row) }, { default: () => "Delete" }),
        ],
      }),
  },
];

onMounted(async () => {
  await load();
  await loadLogs().catch(() => {});
});
</script>

<template>
  <div>
    <div class="toolbar">
      <n-button type="primary" :disabled="!status?.available" @click="createOpen = true">Add FTP user</n-button>
      <n-button v-for="action in ['start', 'restart', 'stop']" :key="action" secondary
        :disabled="!status?.available" @click="serviceAction(action)">
        {{ action }}
      </n-button>
      <span class="spacer" />
      <n-tag v-if="status" size="small" :bordered="false" :type="status.available ? 'success' : 'warning'">
        {{ status.backend }}
      </n-tag>
      <n-tag v-if="status" size="small" :bordered="false"
        :type="status.state === 'active' ? 'success' : 'default'">{{ status.state }}</n-tag>
      <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
    </div>

    <n-alert v-if="status && !status.available" type="info" :bordered="false" style="margin-bottom: 12px">
      No FTP server is installed. Install Pure-FTPd from the App store page, then come back here.
    </n-alert>

    <n-card size="small">
      <n-data-table :columns="columns" :data="users" :loading="loading" :bordered="false"
        :row-key="(row) => row.id" size="small" />
      <n-empty v-if="!users.length && !loading" style="padding: 26px 0"
        description="No FTP users yet. Each one is a virtual account locked to its own directory." />
    </n-card>

    <n-card v-if="logs.length" size="small" title="Transfer log" style="margin-top: 14px">
      <template #header-extra><n-button size="tiny" @click="loadLogs">Refresh</n-button></template>
      <pre class="log-pane mono">{{ logs.join("\n") }}</pre>
    </n-card>

    <n-modal v-model:show="createOpen" preset="card" title="Add FTP user" style="max-width: 480px">
      <n-form label-placement="top" size="small">
        <n-form-item label="Username"><n-input v-model:value="draft.username" /></n-form-item>
        <n-form-item label="Password"><n-input v-model:value="draft.password" placeholder="generated if blank" /></n-form-item>
        <n-form-item label="Home directory"><n-input v-model:value="draft.home" placeholder="defaults to the FTP root" /></n-form-item>
        <n-grid cols="2" :x-gap="12">
          <n-gi>
            <n-form-item label="Quota (MB, 0 = unlimited)">
              <n-input-number v-model:value="draft.quota_mb" :min="0" style="width: 100%" />
            </n-form-item>
          </n-gi>
          <n-gi><n-form-item label="Note"><n-input v-model:value="draft.note" /></n-form-item></n-gi>
        </n-grid>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="createOpen = false">Cancel</n-button>
          <n-button type="primary" @click="create">Create</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

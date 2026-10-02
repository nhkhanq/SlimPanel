<script setup>
import { computed, h, onMounted, reactive, ref } from "vue";
import {
  NAlert, NButton, NCard, NDataTable, NEmpty, NForm, NFormItem, NGi, NGrid, NInput, NModal, NPopconfirm, NSelect, NSpace, NStatistic, NSwitch, NTabPane,
  NTabs, NTag, useDialog, useMessage,
} from "naive-ui";
import { api, downloadUrl } from "../api";
import { bytes, datetime } from "../format";

const message = useMessage();
const dialog = useDialog();

const records = ref([]);
const sites = ref([]);
const databases = ref([]);
const targets = ref([]);
const kinds = ref([]);
const usage = ref(null);
const loading = ref(false);
const kindFilter = ref("");

const targetOpen = ref(false);
const targetDraft = reactive({ name: "", kind: "local", config: {} });

const FIELDS = {
  local: [["path", "/mnt/backup"]],
  s3: [["bucket", "my-bucket"], ["access_key", ""], ["secret_key", ""], ["region", "us-east-1"], ["endpoint", "optional, for S3-compatible"], ["prefix", "slimpanel"]],
  ftp: [["host", "ftp.example.com"], ["port", "21"], ["username", ""], ["password", ""], ["prefix", "slimpanel"]],
  sftp: [["host", "backup.example.com"], ["port", "22"], ["username", ""], ["path", "/backups"], ["key_file", "optional"]],
  rsync: [["destination", "user@host:/backups/"], ["options", "-az"]],
  webdav: [["url", "https://dav.example.com/backups"], ["username", ""], ["password", ""], ["prefix", "slimpanel"]],
};

const fields = computed(() => FIELDS[targetDraft.kind] || []);
const kindOptions = computed(() =>
  kinds.value.map((item) => ({
    label: item.available ? item.label : `${item.label} — needs ${item.tool}`,
    value: item.key,
  })),
);
const targetOptions = computed(() => targets.value.map((t) => ({ label: `${t.name} (${t.kind})`, value: t.id })));

async function load() {
  loading.value = true;
  try {
    const [recordRows, siteRows, dbRows, targetRows, kindRows, usageRow] = await Promise.all([
      api("/backups", { params: { kind: kindFilter.value } }),
      api("/sites").catch(() => []),
      api("/databases").catch(() => []),
      api("/backups/targets").catch(() => []),
      api("/backups/targets/kinds").catch(() => []),
      api("/system/storage").catch(() => null),
    ]);
    records.value = recordRows;
    sites.value = siteRows;
    databases.value = dbRows;
    targets.value = targetRows;
    kinds.value = kindRows;
    usage.value = usageRow;
  } finally {
    loading.value = false;
  }
}

const siteChoice = ref(null);
const dbChoice = ref(null);
const uploadAfter = ref(false);

async function backupSite() {
  if (!siteChoice.value) return message.warning("Pick a site");
  try {
    const record = await api(`/backups/site/${siteChoice.value}`, {
      method: "POST", params: { upload: uploadAfter.value },
    });
    message.success(`Archived ${bytes(record.size)}`);
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function backupDatabase() {
  if (!dbChoice.value) return message.warning("Pick a database");
  try {
    const record = await api(`/backups/database/${dbChoice.value}`, {
      method: "POST", params: { upload: uploadAfter.value },
    });
    message.success(`Dumped ${bytes(record.size)}`);
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function backupAll() {
  try {
    const result = await api("/backups/all", { method: "POST", params: { upload: uploadAfter.value } });
    const failed = result.errors.length;
    failed
      ? message.warning(`${result.records.length} archives, ${failed} failed`)
      : message.success(`${result.records.length} archives written`);
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function prune() {
  const result = await api("/backups/prune", { method: "POST", params: { keep: 7, kind: kindFilter.value } });
  message.success(result.message);
  await load();
}

function restore(row) {
  const options = row.kind === "site" ? sites.value : databases.value;
  const match = options.find((item) => item.name === row.target);
  dialog.warning({
    title: `Restore ${row.target}?`,
    content: match
      ? row.kind === "site"
        ? `The site root is replaced by this archive. A pre-restore copy is written first.`
        : `The dump is replayed into ${row.target}.`
      : `No ${row.kind} named ${row.target} exists any more; recreate it first.`,
    positiveText: match ? "Restore" : "OK",
    negativeText: match ? "Cancel" : undefined,
    onPositiveClick: async () => {
      if (!match) return;
      try {
        const endpoint = row.kind === "site"
          ? `/backups/${row.id}/restore-site/${match.id}`
          : `/backups/${row.id}/restore-database/${match.id}`;
        const result = await api(endpoint, { method: "POST" });
        message.success(result.message);
      } catch (error) {
        message.error(error.message);
      }
    },
  });
}

async function uploadTo(row, targetId) {
  const task = await api(`/backups/${row.id}/upload/${targetId}`, { method: "POST" });
  message.success(`Uploading (task ${task.id})`);
}

function openTarget() {
  targetDraft.config = {};
  targetOpen.value = true;
}

async function createTarget() {
  try {
    await api("/backups/targets", { method: "POST", body: { ...targetDraft } });
    message.success("Target added");
    targetOpen.value = false;
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function testTarget(row) {
  try {
    const result = await api(`/backups/targets/${row.id}/test`, { method: "POST" });
    message.success(`Probe uploaded to ${result.target}`);
  } catch (error) {
    message.error(error.message);
  }
}

const columns = computed(() => [
  {
    title: "Kind",
    key: "kind",
    width: 110,
    render: (row) => h(NTag, { size: "small", bordered: false }, { default: () => row.kind }),
  },
  { title: "Target", key: "target" },
  { title: "File", key: "filename", ellipsis: { tooltip: true } },
  { title: "Size", key: "size", width: 110, render: (row) => bytes(row.size) },
  { title: "Created", key: "created_at", width: 160, render: (row) => datetime(row.created_at) },
  {
    title: "Actions",
    key: "actions",
    width: 300,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          h(NButton, {
            size: "tiny", secondary: true,
            onClick: () => window.open(downloadUrl(`/backups/${row.id}/download`), "_blank"),
          }, { default: () => "Download" }),
          h(NButton, { size: "tiny", secondary: true, onClick: () => restore(row) }, { default: () => "Restore" }),
          targets.value.length
            ? h(NSelect, {
                size: "tiny", style: "width: 110px", placeholder: "Upload",
                options: targetOptions.value,
                onUpdateValue: (value) => uploadTo(row, value),
              })
            : null,
          h(NButton, {
            size: "tiny", type: "error", secondary: true,
            onClick: async () => {
              await api(`/backups/${row.id}`, { method: "DELETE" });
              await load();
            },
          }, { default: () => "Delete" }),
        ],
      }),
  },
]);

const targetColumns = [
  { title: "Name", key: "name" },
  { title: "Kind", key: "kind", width: 110 },
  {
    title: "Config",
    key: "config",
    render: (row) =>
      h("span", { class: "mono muted" },
        Object.entries(row.config).map(([k, v]) => `${k}=${v}`).join("  ")),
  },
  {
    title: "Enabled",
    key: "enabled",
    width: 90,
    render: (row) =>
      h(NSwitch, {
        value: row.enabled, size: "small",
        "onUpdate:value": async (value) => {
          await api(`/backups/targets/${row.id}`, { method: "PATCH", body: { enabled: value } });
          await load();
        },
      }),
  },
  {
    title: "Actions",
    key: "actions",
    width: 160,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          h(NButton, { size: "tiny", secondary: true, onClick: () => testTarget(row) }, { default: () => "Test" }),
          h(NButton, {
            size: "tiny", type: "error", secondary: true,
            onClick: async () => {
              await api(`/backups/targets/${row.id}`, { method: "DELETE" });
              await load();
            },
          }, { default: () => "Remove" }),
        ],
      }),
  },
];

onMounted(load);
</script>

<template>
  <div>
    <n-grid v-if="usage" cols="2 s:4" responsive="screen" :x-gap="12" :y-gap="12">
      <n-gi><n-card size="small"><n-statistic label="Archives" :value="usage.records" /></n-card></n-gi>
      <n-gi><n-card size="small"><n-statistic label="Recorded size" :value="bytes(usage.bytes)" /></n-card></n-gi>
      <n-gi><n-card size="small"><n-statistic label="On disk" :value="bytes(usage.on_disk)" /></n-card></n-gi>
      <n-gi><n-card size="small"><n-statistic label="Remote targets" :value="targets.length" /></n-card></n-gi>
    </n-grid>

    <n-tabs type="line" animated style="margin-top: 14px">
      <n-tab-pane name="archives" tab="Archives">
        <n-card size="small" title="Make a backup" style="margin-bottom: 14px">
          <n-space align="center" :wrap="true">
            <n-select v-model:value="siteChoice" placeholder="Site" style="width: 190px" clearable
              :options="sites.map((s) => ({ label: s.name, value: s.id }))" />
            <n-button size="small" type="primary" @click="backupSite">Archive site</n-button>
            <n-select v-model:value="dbChoice" placeholder="Database" style="width: 190px" clearable
              :options="databases.map((d) => ({ label: d.name, value: d.id }))" />
            <n-button size="small" type="primary" @click="backupDatabase">Dump database</n-button>
            <n-button size="small" secondary @click="backupAll">Everything</n-button>
            <n-space align="center" :size="6">
              <n-switch v-model:value="uploadAfter" size="small" :disabled="!targets.length" />
              <span class="muted">push to remote targets</span>
            </n-space>
          </n-space>
        </n-card>

        <div class="toolbar">
          <n-select v-model:value="kindFilter" style="width: 160px" @update:value="load"
            :options="[
              { label: 'All kinds', value: '' },
              { label: 'Sites', value: 'site' },
              { label: 'MySQL', value: 'database' },
              { label: 'PostgreSQL', value: 'postgres' },
            ]" />
          <n-popconfirm @positive-click="prune">
            <template #trigger><n-button secondary>Keep newest 7</n-button></template>
            Older archives in this view are deleted from disk.
          </n-popconfirm>
          <span class="spacer" />
          <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
        </div>

        <n-card size="small">
          <n-data-table :columns="columns" :data="records" :bordered="false" size="small" :row-key="(row) => row.id" />
          <n-empty v-if="!records.length && !loading" style="padding: 30px 0" description="No backups yet." />
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="targets" tab="Remote storage">
        <div class="toolbar">
          <n-button type="primary" @click="openTarget">Add target</n-button>
          <span class="spacer" />
          <n-button quaternary @click="load">Refresh</n-button>
        </div>
        <n-alert type="info" :bordered="false" style="margin-bottom: 12px">
          A target is a place finished archives get copied to. Testing one uploads a tiny probe file,
          so credentials are checked before a real backup depends on them.
        </n-alert>
        <n-card size="small">
          <n-data-table :columns="targetColumns" :data="targets" :bordered="false" size="small"
            :row-key="(row) => row.id" />
          <n-empty v-if="!targets.length" style="padding: 26px 0"
            description="No remote targets. Backups stay on this server until you add one." />
        </n-card>
      </n-tab-pane>
    </n-tabs>

    <n-modal v-model:show="targetOpen" preset="card" title="Add backup target" style="max-width: 500px">
      <n-form label-placement="top" size="small">
        <n-grid cols="2" :x-gap="12">
          <n-gi><n-form-item label="Name"><n-input v-model:value="targetDraft.name" /></n-form-item></n-gi>
          <n-gi><n-form-item label="Kind"><n-select v-model:value="targetDraft.kind" :options="kindOptions" /></n-form-item></n-gi>
        </n-grid>
        <n-form-item v-for="[key, hint] in fields" :key="key" :label="key">
          <n-input v-model:value="targetDraft.config[key]" :placeholder="hint"
            :type="['password', 'secret_key'].includes(key) ? 'password' : 'text'" show-password-on="click" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="targetOpen = false">Cancel</n-button>
          <n-button type="primary" @click="createTarget">Add</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

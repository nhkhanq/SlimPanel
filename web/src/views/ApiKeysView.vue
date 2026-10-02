<script setup>
import { h, onMounted, reactive, ref } from "vue";
import {
  NAlert, NButton, NCard, NDataTable, NEmpty, NForm, NFormItem, NInput, NModal,
  NSpace, NSwitch, useMessage,
} from "naive-ui";
import { api } from "../api";
import { datetime, relative } from "../format";

const message = useMessage();
const keys = ref([]);
const loading = ref(false);
const createOpen = ref(false);
const secretOpen = ref(false);
const created = ref(null);
const draft = reactive({ name: "", allow_ips: "" });

async function load() {
  loading.value = true;
  try {
    keys.value = await api("/api-keys");
  } finally {
    loading.value = false;
  }
}

async function create() {
  if (!draft.name.trim()) return message.warning("A name is required");
  try {
    created.value = await api("/api-keys", { method: "POST", body: { ...draft } });
    createOpen.value = false;
    secretOpen.value = true;
    draft.name = "";
    draft.allow_ips = "";
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

const example = (key) => `curl -H "X-Api-Key: ${key?.key_id}" \\
     -H "X-Api-Secret: ${key?.secret}" \\
     https://your-panel:8899/api/sites`;

const columns = [
  { title: "Name", key: "name" },
  { title: "Key id", key: "key_id", render: (row) => h("code", { class: "mono" }, row.key_id) },
  { title: "Fingerprint", key: "fingerprint", render: (row) => h("code", { class: "mono" }, row.fingerprint) },
  { title: "Allowed IPs", key: "allow_ips", render: (row) => row.allow_ips || "anywhere" },
  { title: "Last used", key: "last_used_at", width: 130, render: (row) => relative(row.last_used_at) || "never" },
  { title: "Created", key: "created_at", width: 150, render: (row) => datetime(row.created_at) },
  {
    title: "Enabled",
    key: "enabled",
    width: 90,
    render: (row) =>
      h(NSwitch, {
        value: row.enabled, size: "small",
        "onUpdate:value": async (value) => {
          await api(`/api-keys/${row.id}/enabled`, { method: "POST", params: { enabled: value } });
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
          await api(`/api-keys/${row.id}`, { method: "DELETE" });
          message.success("Key removed");
          await load();
        },
      }, { default: () => "Revoke" }),
  },
];

onMounted(load);
</script>

<template>
  <div>
    <div class="toolbar">
      <n-button type="primary" @click="createOpen = true">Create key</n-button>
      <span class="spacer" />
      <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
    </div>

    <n-alert type="info" :bordered="false" style="margin-bottom: 14px">
      A key authenticates either with <code>X-Api-Key</code> plus <code>X-Api-Secret</code> over HTTPS,
      or with a signature — <code>X-Api-Signature</code> is
      <code>HMAC-SHA256(secret, "key_id:timestamp")</code> and stays valid for five minutes.
    </n-alert>

    <n-card size="small">
      <n-data-table :columns="columns" :data="keys" :bordered="false" size="small" :row-key="(row) => row.id" />
      <n-empty v-if="!keys.length && !loading" style="padding: 30px 0"
        description="No API keys. Create one to drive the panel from a script." />
    </n-card>

    <n-modal v-model:show="createOpen" preset="card" title="Create API key" style="max-width: 460px">
      <n-form label-placement="top" size="small">
        <n-form-item label="Name"><n-input v-model:value="draft.name" placeholder="deploy script" /></n-form-item>
        <n-form-item label="Allowed IPs (comma separated, blank = anywhere)">
          <n-input v-model:value="draft.allow_ips" placeholder="203.0.113.4, 10.0.0.0/8" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="createOpen = false">Cancel</n-button>
          <n-button type="primary" @click="create">Create</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="secretOpen" preset="card" title="Copy the secret now" style="max-width: 580px">
      <n-alert type="warning" :bordered="false" style="margin-bottom: 12px">
        This is the only time the secret is shown. The panel keeps a salted digest of it.
      </n-alert>
      <dl v-if="created" class="kv">
        <dt>Key id</dt><dd class="mono">{{ created.key_id }}</dd>
        <dt>Secret</dt><dd class="mono">{{ created.secret }}</dd>
      </dl>
      <n-card size="small" embedded style="margin-top: 12px">
        <pre class="mono" style="margin: 0; white-space: pre-wrap">{{ example(created) }}</pre>
      </n-card>
      <template #footer>
        <n-space justify="end"><n-button type="primary" @click="secretOpen = false">Done</n-button></n-space>
      </template>
    </n-modal>
  </div>
</template>

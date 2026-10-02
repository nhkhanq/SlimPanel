<script setup>
import { h, onMounted, reactive, ref } from "vue";
import {
  NButton,
  NCard,
  NCheckbox,
  NCode,
  NDataTable,
  NDrawer,
  NDrawerContent,
  NForm,
  NFormItem,
  NInput,
  NInputGroup,
  NModal,
  NSelect,
  NSpace,
  NTag,
  useDialog,
  useMessage,
} from "naive-ui";
import { api } from "../api";
import { datetime } from "../format";

const message = useMessage();
const dialog = useDialog();

const sites = ref([]);
const loading = ref(false);
const showCreate = ref(false);
const showConfig = ref(false);
const configText = ref("");
const detail = ref(null);
const newDomain = ref("");

const typeOptions = [
  { label: "Static", value: "static" },
  { label: "PHP", value: "php" },
  { label: "Reverse proxy", value: "proxy" },
];

const form = reactive({
  name: "",
  site_type: "static",
  proxy_target: "",
  php_version: "8.1",
  root: "",
  note: "",
});

const edit = reactive({ run_path: "", index_files: "", proxy_target: "", php_version: "", note: "" });

async function load() {
  loading.value = true;
  try {
    sites.value = await api("/sites");
  } finally {
    loading.value = false;
  }
}

async function guard(action, success) {
  try {
    await action();
    if (success) message.success(success);
    await load();
  } catch (exc) {
    message.error(exc.message);
  }
}

function create() {
  const body = {
    name: form.name.trim(),
    site_type: form.site_type,
    domains: [form.name.trim()],
    root: form.root.trim(),
    note: form.note,
    proxy_target: form.site_type === "proxy" ? form.proxy_target.trim() : "",
    php_version: form.site_type === "php" ? form.php_version.trim() : "",
  };
  guard(
    async () => {
      await api("/sites", { method: "POST", body });
      showCreate.value = false;
      form.name = "";
      form.proxy_target = "";
      form.root = "";
      form.note = "";
    },
    "Site created",
  );
}

async function openDetail(site) {
  detail.value = await api(`/sites/${site.id}`);
  Object.assign(edit, {
    run_path: detail.value.run_path,
    index_files: detail.value.index_files,
    proxy_target: detail.value.proxy_target,
    php_version: detail.value.php_version,
    note: detail.value.note,
  });
}

function saveDetail() {
  guard(
    async () => {
      detail.value = await api(`/sites/${detail.value.id}`, { method: "PATCH", body: { ...edit } });
    },
    "Site updated",
  );
}

function addDomain() {
  const name = newDomain.value.trim();
  if (!name) return;
  guard(
    async () => {
      await api(`/sites/${detail.value.id}/domains`, { method: "POST", body: { name } });
      detail.value = await api(`/sites/${detail.value.id}`);
      newDomain.value = "";
    },
    "Domain added",
  );
}

function issueCert(site) {
  dialog.info({
    title: `Issue a certificate for ${site.name}`,
    content: "Let's Encrypt must be able to reach this domain over port 80.",
    positiveText: "Issue",
    negativeText: "Cancel",
    onPositiveClick: () =>
      guard(
        () =>
          api(`/ssl/${site.id}/issue`, {
            method: "POST",
            body: { domains: site.domains, force_https: true },
          }),
        "Certificate issued",
      ),
  });
}

function removeSite(site) {
  const withFiles = ref(false);
  dialog.warning({
    title: `Delete ${site.name}`,
    content: () =>
      h(NCheckbox, {
        checked: withFiles.value,
        "onUpdate:checked": (value) => (withFiles.value = value),
      }, { default: () => "Also delete the site directory" }),
    positiveText: "Delete",
    negativeText: "Cancel",
    onPositiveClick: () =>
      guard(
        () => api(`/sites/${site.id}`, { method: "DELETE", params: { remove_files: withFiles.value } }),
        "Site deleted",
      ),
  });
}

async function showVhost(site) {
  const config = await api(`/sites/${site.id}/config`);
  configText.value = config.content || config.rendered;
  showConfig.value = true;
}

const columns = [
  {
    title: "Name",
    key: "name",
    render: (row) => h(NButton, { text: true, onClick: () => openDetail(row) }, { default: () => row.name }),
  },
  {
    title: "Type",
    key: "site_type",
    width: 110,
    render: (row) => h(NTag, { size: "small", bordered: false }, { default: () => row.site_type }),
  },
  { title: "Domains", key: "domains", render: (row) => row.domains.join(", ") },
  {
    title: "SSL",
    key: "ssl_enabled",
    width: 90,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.ssl_enabled ? "success" : "default" }, {
        default: () => (row.ssl_enabled ? "on" : "off"),
      }),
  },
  {
    title: "Status",
    key: "enabled",
    width: 110,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.enabled ? "success" : "warning" }, {
        default: () => (row.enabled ? "serving" : "parked"),
      }),
  },
  { title: "Created", key: "created_at", width: 180, render: (row) => datetime(row.created_at) },
  {
    title: "Actions",
    key: "actions",
    width: 300,
    render: (row) =>
      h(NSpace, { size: 6 }, {
        default: () => [
          h(NButton, {
            size: "tiny",
            secondary: true,
            onClick: () =>
              guard(() => api(`/sites/${row.id}/${row.enabled ? "stop" : "start"}`, { method: "POST" })),
          }, { default: () => (row.enabled ? "stop" : "start") }),
          h(NButton, { size: "tiny", secondary: true, onClick: () => issueCert(row) }, { default: () => "ssl" }),
          h(NButton, { size: "tiny", secondary: true, onClick: () => showVhost(row) }, { default: () => "config" }),
          h(NButton, {
            size: "tiny",
            secondary: true,
            onClick: () => guard(() => api(`/backups/site/${row.id}`, { method: "POST" }), "Backup created"),
          }, { default: () => "backup" }),
          h(NButton, { size: "tiny", type: "error", secondary: true, onClick: () => removeSite(row) }, {
            default: () => "delete",
          }),
        ],
      }),
  },
];

onMounted(load);
</script>

<template>
  <div>
    <div class="toolbar">
      <n-button type="primary" @click="showCreate = true">Add site</n-button>
      <n-button secondary @click="load">Refresh</n-button>
    </div>

    <n-card size="small">
      <n-data-table :columns="columns" :data="sites" :loading="loading" :bordered="false" size="small" />
    </n-card>

    <n-modal v-model:show="showCreate" preset="card" title="Add site" style="width: 520px">
      <n-form>
        <n-form-item label="Domain">
          <n-input v-model:value="form.name" placeholder="example.com" />
        </n-form-item>
        <n-form-item label="Type">
          <n-select v-model:value="form.site_type" :options="typeOptions" />
        </n-form-item>
        <n-form-item v-if="form.site_type === 'proxy'" label="Upstream">
          <n-input v-model:value="form.proxy_target" placeholder="http://127.0.0.1:3000" />
        </n-form-item>
        <n-form-item v-if="form.site_type === 'php'" label="PHP version">
          <n-input v-model:value="form.php_version" placeholder="8.1" />
        </n-form-item>
        <n-form-item label="Document root">
          <n-input v-model:value="form.root" placeholder="leave empty for /www/wwwroot/<domain>" />
        </n-form-item>
        <n-form-item label="Note">
          <n-input v-model:value="form.note" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreate = false">Cancel</n-button>
          <n-button type="primary" @click="create">Create</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showConfig" preset="card" title="nginx configuration" style="width: 760px">
      <n-code :code="configText" language="nginx" word-wrap class="log-pane" />
    </n-modal>

    <n-drawer :show="!!detail" :width="520" @update:show="detail = null">
      <n-drawer-content v-if="detail" :title="detail.name" closable>
        <n-form>
          <n-form-item label="Run path">
            <n-input v-model:value="edit.run_path" placeholder="public" />
          </n-form-item>
          <n-form-item label="Index files">
            <n-input v-model:value="edit.index_files" />
          </n-form-item>
          <n-form-item v-if="detail.site_type === 'proxy'" label="Upstream">
            <n-input v-model:value="edit.proxy_target" />
          </n-form-item>
          <n-form-item v-if="detail.site_type === 'php'" label="PHP version">
            <n-input v-model:value="edit.php_version" />
          </n-form-item>
          <n-form-item label="Note">
            <n-input v-model:value="edit.note" />
          </n-form-item>
          <n-form-item label="Domains">
            <n-space vertical style="width: 100%">
              <n-tag v-for="domain in detail.domains" :key="domain" size="small" :bordered="false">
                {{ domain }}
              </n-tag>
              <n-input-group>
                <n-input v-model:value="newDomain" placeholder="www.example.com" />
                <n-button @click="addDomain">Add</n-button>
              </n-input-group>
            </n-space>
          </n-form-item>
        </n-form>
        <template #footer>
          <n-button type="primary" @click="saveDetail">Save</n-button>
        </template>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

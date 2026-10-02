<script setup>
import { h, onMounted, reactive, ref } from "vue";
import {
  NAlert,
  NButton,
  NCard,
  NDataTable,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NSpace,
  useDialog,
  useMessage,
} from "naive-ui";
import { api } from "../api";
import { bytes, datetime } from "../format";

const message = useMessage();
const dialog = useDialog();

const rows = ref([]);
const status = ref({ available: false, server_databases: [] });
const loading = ref(false);
const showCreate = ref(false);
const credentials = ref(null);
const form = reactive({ name: "", username: "", password: "", note: "" });

async function load() {
  loading.value = true;
  try {
    [rows.value, status.value] = await Promise.all([api("/databases"), api("/databases/status")]);
  } catch (exc) {
    message.error(exc.message);
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
  guard(
    async () => {
      await api("/databases", { method: "POST", body: { ...form } });
      showCreate.value = false;
      Object.assign(form, { name: "", username: "", password: "", note: "" });
    },
    "Database created",
  );
}

function drop(row) {
  dialog.error({
    title: `Drop ${row.name}`,
    content: "The database and its user are removed from MySQL. This cannot be undone.",
    positiveText: "Drop",
    negativeText: "Cancel",
    onPositiveClick: () => guard(() => api(`/databases/${row.id}`, { method: "DELETE" }), "Dropped"),
  });
}

const columns = [
  { title: "Name", key: "name" },
  { title: "User", key: "username" },
  { title: "Charset", key: "charset", width: 100 },
  { title: "Note", key: "note", ellipsis: { tooltip: true } },
  { title: "Created", key: "created_at", width: 160, render: (row) => datetime(row.created_at) },
  {
    title: "Actions",
    key: "actions",
    width: 280,
    render: (row) =>
      h(NSpace, { size: 6 }, {
        default: () => [
          h(NButton, {
            size: "tiny",
            secondary: true,
            onClick: async () => (credentials.value = await api(`/databases/${row.id}/credentials`)),
          }, { default: () => "credentials" }),
          h(NButton, {
            size: "tiny",
            secondary: true,
            onClick: () =>
              guard(() => api(`/databases/${row.id}/password`, { method: "POST", body: { password: "" } }), "Password reset"),
          }, { default: () => "reset password" }),
          h(NButton, {
            size: "tiny",
            secondary: true,
            onClick: () =>
              guard(async () => {
                const record = await api(`/backups/database/${row.id}`, { method: "POST" });
                message.success(`Dump ${bytes(record.size)}`);
              }),
          }, { default: () => "dump" }),
          h(NButton, { size: "tiny", type: "error", secondary: true, onClick: () => drop(row) }, {
            default: () => "drop",
          }),
        ],
      }),
  },
];

onMounted(load);
</script>

<template>
  <div>
    <n-alert v-if="!status.available" type="warning" :bordered="false" style="margin-bottom: 14px">
      MySQL is not reachable. Check <code>mysql_user</code> and <code>mysql_password</code> in slimpanel.json.
    </n-alert>

    <div class="toolbar">
      <n-button type="primary" @click="showCreate = true">Add database</n-button>
      <n-button secondary @click="load">Refresh</n-button>
      <span class="spacer" />
      <span style="opacity: 0.6">{{ status.server_databases.length }} databases on the server</span>
    </div>

    <n-card size="small">
      <n-data-table :columns="columns" :data="rows" :loading="loading" :bordered="false" size="small" />
    </n-card>

    <n-modal v-model:show="showCreate" preset="card" title="Add database" style="width: 460px">
      <n-form>
        <n-form-item label="Name">
          <n-input v-model:value="form.name" placeholder="app_db" />
        </n-form-item>
        <n-form-item label="User">
          <n-input v-model:value="form.username" placeholder="defaults to the database name" />
        </n-form-item>
        <n-form-item label="Password">
          <n-input v-model:value="form.password" placeholder="generated when empty" />
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

    <n-modal
      :show="!!credentials"
      preset="card"
      title="Credentials"
      style="width: 420px"
      @update:show="credentials = null"
    >
      <n-form v-if="credentials">
        <n-form-item label="Database"><n-input :value="credentials.name" readonly /></n-form-item>
        <n-form-item label="User"><n-input :value="credentials.username" readonly /></n-form-item>
        <n-form-item label="Password"><n-input :value="credentials.password" readonly /></n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

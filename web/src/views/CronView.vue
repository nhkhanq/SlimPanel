<script setup>
import { h, onMounted, reactive, ref } from "vue";
import {
  NButton,
  NCard,
  NDataTable,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NSpace,
  NSwitch,
  NTag,
  useDialog,
  useMessage,
} from "naive-ui";
import { api } from "../api";
import { datetime } from "../format";

const message = useMessage();
const dialog = useDialog();

const jobs = ref([]);
const loading = ref(false);
const showCreate = ref(false);
const output = ref(null);
const form = reactive({ name: "", schedule: "0 3 * * *", command: "" });

async function load() {
  loading.value = true;
  try {
    jobs.value = await api("/cron");
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
      await api("/cron", { method: "POST", body: { ...form } });
      showCreate.value = false;
      Object.assign(form, { name: "", schedule: "0 3 * * *", command: "" });
    },
    "Job created",
  );
}

const columns = [
  { title: "Name", key: "name" },
  {
    title: "Schedule",
    key: "schedule",
    width: 140,
    render: (row) => h("code", { class: "mono" }, row.schedule),
  },
  { title: "Command", key: "command", ellipsis: { tooltip: true } },
  {
    title: "Last run",
    key: "last_run_at",
    width: 160,
    render: (row) => datetime(row.last_run_at) || "—",
  },
  {
    title: "Enabled",
    key: "enabled",
    width: 90,
    render: (row) =>
      h(NSwitch, {
        value: row.enabled,
        size: "small",
        "onUpdate:value": (value) =>
          guard(() => api(`/cron/${row.id}`, { method: "PATCH", body: { enabled: value } })),
      }),
  },
  {
    title: "Actions",
    key: "actions",
    width: 220,
    render: (row) =>
      h(NSpace, { size: 6 }, {
        default: () => [
          h(NButton, {
            size: "tiny",
            secondary: true,
            onClick: async () => {
              const result = await api(`/cron/${row.id}/run`, { method: "POST" });
              output.value = { title: row.name, text: result.message || "(no output)" };
              await load();
            },
          }, { default: () => "run now" }),
          h(NButton, {
            size: "tiny",
            secondary: true,
            onClick: async () => {
              const logs = await api(`/cron/${row.id}/logs`);
              output.value = { title: `${row.name} logs`, text: logs.lines.join("\n") || "(empty)" };
            },
          }, { default: () => "logs" }),
          h(NButton, {
            size: "tiny",
            type: "error",
            secondary: true,
            onClick: () =>
              dialog.warning({
                title: `Delete ${row.name}`,
                positiveText: "Delete",
                negativeText: "Cancel",
                onPositiveClick: () => guard(() => api(`/cron/${row.id}`, { method: "DELETE" }), "Deleted"),
              }),
          }, { default: () => "delete" }),
        ],
      }),
  },
];

onMounted(load);
</script>

<template>
  <div>
    <div class="toolbar">
      <n-button type="primary" @click="showCreate = true">Add job</n-button>
      <n-button secondary @click="load">Refresh</n-button>
      <n-button
        secondary
        @click="guard(() => api('/cron/sync', { method: 'POST' }), 'Crontab written')"
      >
        Sync crontab
      </n-button>
      <span class="spacer" />
      <n-tag size="small" :bordered="false">written to /etc/cron.d/slimpanel</n-tag>
    </div>

    <n-card size="small">
      <n-data-table :columns="columns" :data="jobs" :loading="loading" :bordered="false" size="small" />
    </n-card>

    <n-modal v-model:show="showCreate" preset="card" title="Add cron job" style="width: 520px">
      <n-form>
        <n-form-item label="Name">
          <n-input v-model:value="form.name" placeholder="nightly backup" />
        </n-form-item>
        <n-form-item label="Schedule">
          <n-input v-model:value="form.schedule" placeholder="0 3 * * *" />
        </n-form-item>
        <n-form-item label="Command">
          <n-input v-model:value="form.command" type="textarea" :rows="3" />
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
      :show="!!output"
      preset="card"
      :title="output?.title"
      style="width: 760px"
      @update:show="output = null"
    >
      <pre class="mono log-pane">{{ output?.text }}</pre>
    </n-modal>
  </div>
</template>

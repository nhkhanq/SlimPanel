<script setup>
import { h, onMounted, ref } from "vue";
import { NButton, NCard, NDataTable, NSpace, NTag, useDialog, useMessage } from "naive-ui";
import { api, downloadUrl } from "../api";
import { bytes, datetime } from "../format";

const message = useMessage();
const dialog = useDialog();

const rows = ref([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    rows.value = await api("/backups");
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

const columns = [
  {
    title: "Kind",
    key: "kind",
    width: 110,
    render: (row) => h(NTag, { size: "small", bordered: false }, { default: () => row.kind }),
  },
  { title: "Target", key: "target" },
  { title: "File", key: "filename", ellipsis: { tooltip: true } },
  { title: "Size", key: "size", width: 110, render: (row) => bytes(row.size) },
  { title: "Created", key: "created_at", width: 170, render: (row) => datetime(row.created_at) },
  {
    title: "Actions",
    key: "actions",
    width: 190,
    render: (row) =>
      h(NSpace, { size: 6 }, {
        default: () => [
          h("a", { href: downloadUrl(`/backups/${row.id}/download`) },
            h(NButton, { size: "tiny", secondary: true }, { default: () => "download" })),
          h(NButton, {
            size: "tiny",
            type: "error",
            secondary: true,
            onClick: () => guard(() => api(`/backups/${row.id}`, { method: "DELETE" }), "Deleted"),
          }, { default: () => "delete" }),
        ],
      }),
  },
];

function prune() {
  dialog.warning({
    title: "Prune backups",
    content: "Keeps the 7 most recent backups and deletes the rest.",
    positiveText: "Prune",
    negativeText: "Cancel",
    onPositiveClick: () =>
      guard(() => api("/backups/prune", { method: "POST", params: { keep: 7 } }), "Pruned"),
  });
}

onMounted(load);
</script>

<template>
  <div>
    <div class="toolbar">
      <n-button secondary @click="load">Refresh</n-button>
      <n-button secondary @click="prune">Prune to 7</n-button>
    </div>
    <n-card size="small">
      <n-data-table :columns="columns" :data="rows" :loading="loading" :bordered="false" size="small" />
    </n-card>
  </div>
</template>

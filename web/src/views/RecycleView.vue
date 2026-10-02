<script setup>
import { h, onMounted, ref } from "vue";
import {
  NAlert, NButton, NCard, NDataTable, NEmpty, NPopconfirm, NSpace, NStatistic, NGi, NGrid,
  useMessage,
} from "naive-ui";
import { api } from "../api";
import { bytes, datetime } from "../format";

const message = useMessage();
const items = ref([]);
const usage = ref(null);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    const [rows, usageRow] = await Promise.all([api("/recycle"), api("/recycle/usage")]);
    items.value = rows;
    usage.value = usageRow;
  } finally {
    loading.value = false;
  }
}

async function restore(row, overwrite = false) {
  try {
    const result = await api(`/recycle/${row.id}/restore`, { method: "POST", params: { overwrite } });
    message.success(`Restored to ${result.restored}`);
    await load();
  } catch (error) {
    if (error.status === 409) {
      message.warning(`${row.original_path} exists again — use Replace to overwrite it.`);
    } else {
      message.error(error.message);
    }
  }
}

async function purge(row) {
  await api(`/recycle/${row.id}`, { method: "DELETE" });
  message.success("Permanently removed");
  await load();
}

async function empty() {
  const result = await api("/recycle", { method: "DELETE" });
  message.success(result.message);
  await load();
}

const columns = [
  { title: "Original path", key: "original_path", ellipsis: { tooltip: true } },
  { title: "Kind", key: "is_dir", width: 100, render: (row) => (row.is_dir ? "directory" : "file") },
  { title: "Size", key: "size", width: 110, render: (row) => bytes(row.size) },
  { title: "Deleted", key: "deleted_at", width: 160, render: (row) => datetime(row.deleted_at) },
  {
    title: "Actions",
    key: "actions",
    width: 250,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          h(NButton, { size: "tiny", type: "primary", secondary: true, onClick: () => restore(row) },
            { default: () => "Restore" }),
          h(NButton, { size: "tiny", secondary: true, onClick: () => restore(row, true) },
            { default: () => "Replace" }),
          h(NButton, { size: "tiny", type: "error", secondary: true, onClick: () => purge(row) },
            { default: () => "Delete" }),
        ],
      }),
  },
];

onMounted(load);
</script>

<template>
  <div>
    <n-grid v-if="usage" cols="2 s:4" responsive="screen" :x-gap="12" :y-gap="12">
      <n-gi><n-card size="small"><n-statistic label="Items" :value="usage.count" /></n-card></n-gi>
      <n-gi><n-card size="small"><n-statistic label="Size" :value="bytes(usage.bytes)" /></n-card></n-gi>
      <n-gi>
        <n-card size="small">
          <n-statistic label="Untracked" :value="bytes(usage.orphan_bytes || 0)" />
          <span class="muted">{{ usage.orphans || 0 }} stored copies with no record</span>
        </n-card>
      </n-gi>
      <n-gi><n-card size="small"><n-statistic label="Bin" :value="usage.enabled ? 'on' : 'off'" /></n-card></n-gi>
    </n-grid>

    <n-alert v-if="usage && !usage.enabled" type="info" :bordered="false" style="margin: 14px 0">
      The recycle bin is switched off, so file deletions are immediate. Turn <code>recycle_bin</code>
      back on under Settings to catch mistakes.
    </n-alert>

    <div class="toolbar" style="margin-top: 14px">
      <n-popconfirm @positive-click="empty">
        <template #trigger><n-button type="error" secondary :disabled="!items.length">Empty the bin</n-button></template>
        Everything in the bin is deleted for good, including untracked copies.
      </n-popconfirm>
      <span class="spacer" />
      <span class="muted mono">{{ usage?.path }}</span>
      <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
    </div>

    <n-card size="small">
      <n-data-table :columns="columns" :data="items" :bordered="false" size="small" :row-key="(row) => row.id" />
      <n-empty v-if="!items.length && !loading" style="padding: 30px 0"
        description="The bin is empty. Files deleted from the file manager land here first." />
    </n-card>
  </div>
</template>

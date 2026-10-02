<script setup>
import { h, reactive, ref } from "vue";
import {
  NAlert,
  NButton,
  NCard,
  NCheckbox,
  NDataTable,
  NDescriptions,
  NDescriptionsItem,
  NForm,
  NFormItem,
  NInput,
  NSpace,
  NTag,
  useDialog,
  useMessage,
} from "naive-ui";
import { api } from "../api";

const message = useMessage();
const dialog = useDialog();

const form = reactive({
  panel_dir: "/www/server/panel",
  cron_dir: "/www/server/cron",
  activate: false,
});

const report = ref(null);
const loading = ref(false);

async function run(endpoint) {
  loading.value = true;
  try {
    report.value = await api(`/import/aapanel/${endpoint}`, { method: "POST", body: { ...form } });
  } catch (exc) {
    message.error(exc.message);
  } finally {
    loading.value = false;
  }
}

function apply() {
  dialog.warning({
    title: "Import from aaPanel",
    content: form.activate
      ? "Imported sites will be served by SlimPanel immediately. Make sure aaPanel's nginx include is removed first."
      : "Imported sites are parked, so nginx keeps serving aaPanel until you switch over.",
    positiveText: "Import",
    negativeText: "Cancel",
    onPositiveClick: async () => {
      await run("apply");
      message.success("Import finished");
    },
  });
}

const columns = [
  {
    title: "Kind",
    key: "kind",
    width: 110,
    render: (row) => h(NTag, { size: "small", bordered: false }, { default: () => row.kind }),
  },
  { title: "Name", key: "name", width: 220 },
  {
    title: "Action",
    key: "action",
    width: 110,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.action === "import" ? "success" : "default" }, {
        default: () => row.action,
      }),
  },
  { title: "Note", key: "reason", ellipsis: { tooltip: true } },
];

const counts = (kind) => report.value?.summary?.[kind] || {};
</script>

<template>
  <div>
    <n-alert type="info" :bordered="false" style="margin-bottom: 14px">
      aaPanel is only ever read. Preview changes nothing — nothing is written until you press Import.
    </n-alert>

    <n-card size="small" title="Source">
      <n-form inline>
        <n-form-item label="aaPanel directory">
          <n-input v-model:value="form.panel_dir" style="width: 260px" />
        </n-form-item>
        <n-form-item label="Cron directory">
          <n-input v-model:value="form.cron_dir" style="width: 220px" />
        </n-form-item>
        <n-form-item>
          <n-checkbox v-model:checked="form.activate">Serve imported sites immediately</n-checkbox>
        </n-form-item>
      </n-form>
      <n-space>
        <n-button :loading="loading" @click="run('preview')">Preview</n-button>
        <n-button type="primary" :loading="loading" :disabled="!report" @click="apply">Import</n-button>
      </n-space>
    </n-card>

    <n-card v-if="report" size="small" title="Result" style="margin-top: 12px">
      <n-descriptions :column="3" label-placement="top" style="margin-bottom: 14px">
        <n-descriptions-item v-for="kind in ['site', 'database', 'cron']" :key="kind" :label="kind">
          {{ counts(kind).import || 0 }} to import · {{ counts(kind).skip || 0 }} skipped
        </n-descriptions-item>
      </n-descriptions>
      <n-data-table :columns="columns" :data="report.items" :bordered="false" size="small" />
    </n-card>
  </div>
</template>

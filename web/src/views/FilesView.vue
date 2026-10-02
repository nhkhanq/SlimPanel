<script setup>
import { h, onMounted, ref } from "vue";
import {
  NBreadcrumb,
  NBreadcrumbItem,
  NButton,
  NCard,
  NDataTable,
  NIcon,
  NInput,
  NInputGroup,
  NModal,
  NSelect,
  NSpace,
  NUpload,
  useDialog,
  useMessage,
} from "naive-ui";
import { DocumentOutline, FolderOutline } from "@vicons/ionicons5";
import { api, downloadUrl, uploadFile } from "../api";
import { bytes, datetime } from "../format";

const message = useMessage();
const dialog = useDialog();

const roots = ref([]);
const path = ref("");
const entries = ref([]);
const loading = ref(false);
const editor = ref(null);

async function load(target) {
  if (target) path.value = target;
  loading.value = true;
  try {
    const data = await api("/files/list", { params: { path: path.value } });
    path.value = data.path;
    entries.value = data.entries;
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

const crumbs = () => {
  const parts = path.value.split("/").filter(Boolean);
  return parts.map((part, index) => ({ label: part, path: `/${parts.slice(0, index + 1).join("/")}` }));
};

function promptNew(kind) {
  const name = ref("");
  dialog.create({
    title: kind === "dir" ? "New folder" : "New file",
    content: () =>
      h(NInput, {
        value: name.value,
        placeholder: "name",
        "onUpdate:value": (value) => (name.value = value),
      }),
    positiveText: "Create",
    negativeText: "Cancel",
    onPositiveClick: () => {
      if (!name.value.trim()) return;
      const target = `${path.value.replace(/\/$/, "")}/${name.value.trim()}`;
      return guard(
        () => api(kind === "dir" ? "/files/mkdir" : "/files/write", {
          method: "POST",
          body: { path: target, content: "" },
        }),
        "Created",
      );
    },
  });
}

function promptRename(row) {
  const name = ref(row.name);
  dialog.create({
    title: `Rename ${row.name}`,
    content: () =>
      h(NInput, { value: name.value, "onUpdate:value": (value) => (name.value = value) }),
    positiveText: "Rename",
    negativeText: "Cancel",
    onPositiveClick: () =>
      guard(
        () =>
          api("/files/move", {
            method: "POST",
            body: { source: row.path, target: `${path.value.replace(/\/$/, "")}/${name.value.trim()}` },
          }),
        "Renamed",
      ),
  });
}

function promptChmod(row) {
  const mode = ref(row.mode);
  dialog.create({
    title: `Permissions for ${row.name}`,
    content: () => h(NInput, { value: mode.value, "onUpdate:value": (value) => (mode.value = value) }),
    positiveText: "Apply",
    negativeText: "Cancel",
    onPositiveClick: () =>
      guard(() => api("/files/chmod", { method: "POST", body: { path: row.path, mode: mode.value } }), "Updated"),
  });
}

async function openEditor(row) {
  try {
    const file = await api("/files/read", { params: { path: row.path } });
    editor.value = { path: file.path, content: file.content };
  } catch (exc) {
    message.error(exc.message);
  }
}

function saveEditor() {
  guard(
    async () => {
      await api("/files/write", { method: "POST", body: { ...editor.value } });
      editor.value = null;
    },
    "Saved",
  );
}

function remove(row) {
  dialog.warning({
    title: `Delete ${row.name}`,
    content: row.is_dir ? "The folder and everything in it is removed." : "This cannot be undone.",
    positiveText: "Delete",
    negativeText: "Cancel",
    onPositiveClick: () =>
      guard(() => api("/files", { method: "DELETE", params: { path: row.path } }), "Deleted"),
  });
}

async function onUpload({ file, onFinish, onError }) {
  try {
    await uploadFile(path.value, file.file);
    message.success("Uploaded");
    await load();
    onFinish();
  } catch (exc) {
    message.error(exc.message);
    onError();
  }
}

const columns = [
  {
    title: "Name",
    key: "name",
    render: (row) =>
      h(NSpace, { size: 6, align: "center", wrap: false }, {
        default: () => [
          h(NIcon, { component: row.is_dir ? FolderOutline : DocumentOutline, depth: 3 }),
          h(NButton, {
            text: true,
            onClick: () => (row.is_dir ? load(row.path) : openEditor(row)),
          }, { default: () => row.name }),
        ],
      }),
  },
  { title: "Size", key: "size", width: 110, render: (row) => (row.is_dir ? "—" : bytes(row.size)) },
  { title: "Mode", key: "mode", width: 80 },
  { title: "Owner", key: "owner", width: 140, render: (row) => `${row.owner}:${row.group}` },
  { title: "Modified", key: "modified", width: 185, render: (row) => datetime(row.modified) },
  {
    title: "Actions",
    key: "actions",
    width: 290,
    render: (row) =>
      h(NSpace, { size: 6 }, {
        default: () => [
          !row.is_dir &&
            h("a", { href: downloadUrl("/files/download", { path: row.path }) },
              h(NButton, { size: "tiny", secondary: true }, { default: () => "download" })),
          h(NButton, { size: "tiny", secondary: true, onClick: () => promptRename(row) }, { default: () => "rename" }),
          h(NButton, { size: "tiny", secondary: true, onClick: () => promptChmod(row) }, { default: () => "chmod" }),
          h(NButton, { size: "tiny", type: "error", secondary: true, onClick: () => remove(row) }, {
            default: () => "delete",
          }),
        ].filter(Boolean),
      }),
  },
];

onMounted(async () => {
  const data = await api("/files/roots");
  roots.value = data.roots;
  await load(data.roots[0]);
});
</script>

<template>
  <div>
    <div class="toolbar">
      <n-select
        :value="roots.find((root) => path.startsWith(root)) || null"
        :options="roots.map((root) => ({ label: root, value: root }))"
        style="width: 200px"
        @update:value="load"
      />
      <n-input-group style="flex: 1; min-width: 280px">
        <n-input v-model:value="path" @keyup.enter="load()" />
        <n-button @click="load()">Go</n-button>
      </n-input-group>
      <n-button secondary @click="load(path.replace(/\/[^/]+\/?$/, '') || '/')">Up</n-button>
      <n-button secondary @click="promptNew('dir')">Folder</n-button>
      <n-button secondary @click="promptNew('file')">File</n-button>
      <n-upload :custom-request="onUpload" :show-file-list="false" style="width: auto">
        <n-button type="primary">Upload</n-button>
      </n-upload>
    </div>

    <n-breadcrumb style="margin-bottom: 12px">
      <n-breadcrumb-item
        v-for="crumb in crumbs()"
        :key="crumb.path"
        :clickable="true"
        @click="load(crumb.path)"
      >
        {{ crumb.label }}
      </n-breadcrumb-item>
    </n-breadcrumb>

    <n-card size="small">
      <n-data-table
        :columns="columns"
        :data="entries"
        :loading="loading"
        :bordered="false"
        size="small"
        :max-height="560"
        virtual-scroll
      />
    </n-card>

    <n-modal
      :show="!!editor"
      preset="card"
      :title="editor?.path"
      style="width: 900px"
      @update:show="editor = null"
    >
      <n-input v-if="editor" v-model:value="editor.content" type="textarea" :rows="24" class="mono" />
      <template #footer>
        <n-space justify="end">
          <n-button @click="editor = null">Close</n-button>
          <n-button type="primary" @click="saveEditor">Save</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, h, onMounted, reactive, ref } from "vue";
import {
  NBreadcrumb, NBreadcrumbItem, NButton, NCard, NCheckbox, NDataTable, NDropdown, NEmpty,
  NForm, NFormItem, NGi, NGrid, NIcon, NInput, NInputGroup, NModal, NProgress, NSelect,
  NSpace, NTag, NUpload, useDialog, useMessage,
} from "naive-ui";
import { DocumentOutline, FolderOutline, LinkOutline } from "@vicons/ionicons5";
import { api, downloadUrl, uploadFile } from "../api";
import { bytes, datetime } from "../format";

const message = useMessage();
const dialog = useDialog();

const roots = ref({ roots: [], www_root: "", log_root: "", recycle_bin: true });
const path = ref("");
const entries = ref([]);
const checked = ref([]);
const loading = ref(false);
const editor = ref(null);
const usage = ref(null);

const searchOpen = ref(false);
const searchDraft = reactive({ pattern: "*", contains: "" });
const searchResult = ref(null);

const remoteOpen = ref(false);
const remoteDraft = reactive({ url: "", filename: "" });

const archiveOpen = ref(false);
const archiveTarget = ref("");

async function load(target) {
  if (target) path.value = target;
  loading.value = true;
  try {
    const data = await api("/files/list", { params: { path: path.value } });
    path.value = data.path;
    entries.value = data.entries;
    checked.value = [];
    usage.value = null;
  } catch (error) {
    message.error(error.message);
  } finally {
    loading.value = false;
  }
}

async function guard(action, success) {
  try {
    await action();
    if (success) message.success(success);
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

const crumbs = computed(() => {
  const parts = path.value.split("/").filter(Boolean);
  return parts.map((part, index) => ({ label: part, path: `/${parts.slice(0, index + 1).join("/")}` }));
});

const selected = computed(() => entries.value.filter((row) => checked.value.includes(row.path)));

function join(name) {
  return `${path.value.replace(/\/$/, "")}/${name}`;
}

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
      return guard(
        () =>
          api(kind === "dir" ? "/files/mkdir" : "/files/write", {
            method: "POST",
            body: { path: join(name.value.trim()), content: "" },
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
    content: () => h(NInput, { value: name.value, "onUpdate:value": (value) => (name.value = value) }),
    positiveText: "Rename",
    negativeText: "Cancel",
    onPositiveClick: () =>
      guard(
        () => api("/files/move", { method: "POST", body: { source: row.path, target: join(name.value.trim()) } }),
        "Renamed",
      ),
  });
}

function promptChmod(row) {
  const mode = ref(row.mode);
  const recursive = ref(false);
  dialog.create({
    title: `Permissions for ${row.name}`,
    content: () =>
      h(NSpace, { vertical: true }, {
        default: () => [
          h(NInput, { value: mode.value, placeholder: "755", "onUpdate:value": (value) => (mode.value = value) }),
          row.is_dir
            ? h(NCheckbox, {
                checked: recursive.value,
                "onUpdate:checked": (value) => (recursive.value = value),
              }, { default: () => "Apply to everything inside" })
            : null,
        ],
      }),
    positiveText: "Apply",
    negativeText: "Cancel",
    onPositiveClick: () =>
      guard(
        () => api("/files/chmod", {
          method: "POST",
          body: { path: row.path, mode: mode.value, recursive: recursive.value },
        }),
        "Permissions updated",
      ),
  });
}

function promptChown(row) {
  const owner = ref(row.owner);
  const group = ref(row.group);
  const recursive = ref(false);
  dialog.create({
    title: `Owner of ${row.name}`,
    content: () =>
      h(NSpace, { vertical: true }, {
        default: () => [
          h(NInput, { value: owner.value, placeholder: "owner", "onUpdate:value": (v) => (owner.value = v) }),
          h(NInput, { value: group.value, placeholder: "group", "onUpdate:value": (v) => (group.value = v) }),
          row.is_dir
            ? h(NCheckbox, {
                checked: recursive.value,
                "onUpdate:checked": (v) => (recursive.value = v),
              }, { default: () => "Apply to everything inside" })
            : null,
        ],
      }),
    positiveText: "Apply",
    negativeText: "Cancel",
    onPositiveClick: () =>
      guard(
        () => api("/files/chown", {
          method: "POST",
          body: { path: row.path, owner: owner.value, group: group.value, recursive: recursive.value },
        }),
        "Owner updated",
      ),
  });
}

async function openEditor(row) {
  try {
    const data = await api("/files/read", { params: { path: row.path } });
    editor.value = { ...data, name: row.name };
  } catch (error) {
    message.error(error.message);
  }
}

async function saveEditor() {
  await guard(
    () => api("/files/write", { method: "POST", body: { path: editor.value.path, content: editor.value.content } }),
    "Saved",
  );
  editor.value = null;
}

function removeOne(row) {
  dialog.warning({
    title: `Delete ${row.name}?`,
    content: roots.value.recycle_bin
      ? "It moves to the recycle bin, where you can restore it."
      : "The recycle bin is off, so this is immediate.",
    positiveText: "Delete",
    negativeText: "Cancel",
    onPositiveClick: () =>
      guard(() => api("/files", { method: "DELETE", params: { path: row.path } }), "Deleted"),
  });
}

function removeSelected() {
  dialog.warning({
    title: `Delete ${selected.value.length} items?`,
    content: roots.value.recycle_bin
      ? "They move to the recycle bin."
      : "The recycle bin is off, so this is immediate.",
    positiveText: "Delete",
    negativeText: "Cancel",
    onPositiveClick: async () => {
      const results = await api("/files/delete-many", {
        method: "POST",
        body: { paths: selected.value.map((row) => row.path) },
      });
      const failed = results.filter((row) => !row.ok);
      failed.length
        ? message.warning(`${results.length - failed.length} deleted, ${failed.length} failed`)
        : message.success(`${results.length} deleted`);
      await load();
    },
  });
}

async function compress() {
  if (!archiveTarget.value.trim()) return message.warning("Give the archive a name");
  await guard(
    () => api("/files/compress", {
      method: "POST",
      body: { paths: selected.value.map((row) => row.path), target: join(archiveTarget.value.trim()) },
    }),
    "Archive created",
  );
  archiveOpen.value = false;
}

async function extract(row) {
  const target = row.name.replace(/\.(zip|tar|tar\.gz|tgz|tar\.bz2|tbz2|tar\.xz|txz)$/i, "");
  await guard(
    () => api("/files/extract", { method: "POST", body: { archive: row.path, target: join(target) } }),
    `Extracted into ${target}`,
  );
}

async function peek(row) {
  const result = await api("/files/archive", { params: { path: row.path, limit: 300 } });
  dialog.info({
    title: `${row.name} — ${result.total} entries`,
    style: { width: "680px" },
    content: () =>
      h("pre", { class: "log-pane mono" },
        result.entries.map((entry) => `${entry.is_dir ? "d" : "-"} ${bytes(entry.size).padStart(10)}  ${entry.name}`).join("\n")),
    positiveText: "Close",
  });
}

async function runSearch() {
  try {
    searchResult.value = await api("/files/search", {
      method: "POST",
      body: { root: path.value, pattern: searchDraft.pattern, contains: searchDraft.contains, max_results: 300 },
    });
  } catch (error) {
    message.error(error.message);
  }
}

async function remoteDownload() {
  if (!remoteDraft.url.trim()) return message.warning("A URL is required");
  try {
    const result = await api("/files/remote-download", {
      method: "POST",
      body: { path: path.value, url: remoteDraft.url.trim(), filename: remoteDraft.filename.trim() },
    });
    message.success(`Downloading to ${result.target} (task ${result.task_id})`);
    remoteOpen.value = false;
    remoteDraft.url = "";
    remoteDraft.filename = "";
  } catch (error) {
    message.error(error.message);
  }
}

async function loadUsage() {
  usage.value = await api("/files/usage", { params: { path: path.value } });
}

async function upload({ file }) {
  try {
    await uploadFile(path.value, file.file);
    message.success(`${file.name} uploaded`);
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function duplicate(row) {
  await guard(() => api("/files/duplicate", { method: "POST", params: { path: row.path } }), "Duplicated");
}

const isArchive = (name) => /\.(zip|tar|tar\.gz|tgz|tar\.bz2|tbz2|tar\.xz|txz)$/i.test(name);

const columns = computed(() => [
  { type: "selection" },
  {
    title: "Name",
    key: "name",
    render: (row) =>
      h(NSpace, { align: "center", size: 8, wrap: false }, {
        default: () => [
          h(NIcon, { component: row.is_link ? LinkOutline : row.is_dir ? FolderOutline : DocumentOutline, size: 16 }),
          row.is_dir
            ? h(NButton, { text: true, type: "primary", onClick: () => load(row.path) }, { default: () => row.name })
            : h(NButton, { text: true, onClick: () => openEditor(row) }, { default: () => row.name }),
        ],
      }),
  },
  { title: "Size", key: "size", width: 110, render: (row) => (row.is_dir ? "—" : bytes(row.size)) },
  { title: "Mode", key: "mode", width: 80, render: (row) => h("code", { class: "mono" }, row.mode) },
  { title: "Owner", key: "owner", width: 150, render: (row) => `${row.owner}:${row.group}` },
  { title: "Modified", key: "modified", width: 160, render: (row) => datetime(row.modified) },
  {
    title: "Actions",
    key: "actions",
    width: 130,
    render: (row) =>
      h(NDropdown, {
        trigger: "click",
        options: [
          { label: "Rename", key: "rename" },
          { label: "Duplicate", key: "duplicate" },
          { label: "Permissions", key: "chmod" },
          { label: "Owner", key: "chown" },
          ...(row.is_dir ? [] : [{ label: "Download", key: "download" }]),
          ...(isArchive(row.name) ? [
            { label: "List archive", key: "peek" },
            { label: "Extract here", key: "extract" },
          ] : []),
          { type: "divider", key: "d" },
          { label: "Delete", key: "delete" },
        ],
        onSelect: (key) => {
          if (key === "rename") promptRename(row);
          else if (key === "duplicate") duplicate(row);
          else if (key === "chmod") promptChmod(row);
          else if (key === "chown") promptChown(row);
          else if (key === "download") window.open(downloadUrl("/files/download", { path: row.path }), "_blank");
          else if (key === "peek") peek(row);
          else if (key === "extract") extract(row);
          else if (key === "delete") removeOne(row);
        },
      }, { default: () => h(NButton, { size: "tiny", secondary: true }, { default: () => "Actions" }) }),
  },
]);

onMounted(async () => {
  roots.value = await api("/files/roots");
  await load(roots.value.www_root || roots.value.roots[0]);
});
</script>

<template>
  <div>
    <div class="toolbar">
      <n-select
        :value="null"
        :options="roots.roots.map((root) => ({ label: root, value: root }))"
        placeholder="Jump to a root"
        style="width: 220px"
        @update:value="load"
      />
      <n-button secondary @click="promptNew('dir')">New folder</n-button>
      <n-button secondary @click="promptNew('file')">New file</n-button>
      <n-upload :show-file-list="false" :custom-request="upload">
        <n-button secondary>Upload</n-button>
      </n-upload>
      <n-button secondary @click="remoteOpen = true">Remote download</n-button>
      <n-button secondary @click="searchOpen = true">Search</n-button>
      <n-button secondary @click="loadUsage">Disk usage</n-button>
      <span class="spacer" />
      <template v-if="selected.length">
        <n-tag size="small" :bordered="false" type="info">{{ selected.length }} selected</n-tag>
        <n-button size="small" secondary @click="archiveOpen = true">Compress</n-button>
        <n-button size="small" type="error" secondary @click="removeSelected">Delete</n-button>
      </template>
      <n-button quaternary :loading="loading" @click="load()">Refresh</n-button>
    </div>

    <n-card size="small" style="margin-bottom: 12px">
      <n-space align="center" :size="10">
        <n-breadcrumb>
          <n-breadcrumb-item @click="load('/')">/</n-breadcrumb-item>
          <n-breadcrumb-item v-for="crumb in crumbs" :key="crumb.path" @click="load(crumb.path)">
            {{ crumb.label }}
          </n-breadcrumb-item>
        </n-breadcrumb>
        <span class="spacer" />
        <n-input-group style="width: 360px">
          <n-input v-model:value="path" class="mono" @keyup.enter="load()" />
          <n-button @click="load()">Go</n-button>
        </n-input-group>
      </n-space>
    </n-card>

    <n-card v-if="usage" size="small" title="Disk usage" style="margin-bottom: 12px">
      <template #header-extra><strong>{{ bytes(usage.total) }}</strong></template>
      <n-grid cols="1 s:2 l:3" responsive="screen" :x-gap="14" :y-gap="6">
        <n-gi v-for="row in usage.entries.slice(0, 12)" :key="row.path">
          <n-space align="center" :size="8" :wrap="false">
            <span class="truncate" style="width: 160px">{{ row.name }}</span>
            <n-progress
              :percentage="usage.total ? Math.round((row.size / usage.total) * 100) : 0"
              :height="10"
              style="flex: 1"
            />
            <span class="muted" style="width: 72px; text-align: right">{{ bytes(row.size) }}</span>
          </n-space>
        </n-gi>
      </n-grid>
    </n-card>

    <n-card size="small">
      <n-data-table
        v-model:checked-row-keys="checked"
        :columns="columns"
        :data="entries"
        :loading="loading"
        :bordered="false"
        :row-key="(row) => row.path"
        size="small"
        :max-height="560"
      />
      <n-empty v-if="!entries.length && !loading" style="padding: 30px 0" description="This directory is empty." />
    </n-card>

    <!-- editor -->
    <n-modal
      :show="!!editor"
      preset="card"
      :title="editor?.name"
      style="max-width: 1000px"
      @update:show="(value) => !value && (editor = null)"
    >
      <template v-if="editor">
        <n-space align="center" style="margin-bottom: 8px">
          <n-tag size="small" :bordered="false">{{ editor.mode }}</n-tag>
          <span class="muted mono">{{ editor.path }}</span>
        </n-space>
        <n-input v-model:value="editor.content" type="textarea" :rows="26" class="mono" />
      </template>
      <template #footer>
        <n-space justify="end">
          <n-button @click="editor = null">Cancel</n-button>
          <n-button type="primary" @click="saveEditor">Save</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- search -->
    <n-modal v-model:show="searchOpen" preset="card" title="Search this directory" style="max-width: 760px">
      <n-form inline label-placement="top" size="small">
        <n-form-item label="Filename pattern"><n-input v-model:value="searchDraft.pattern" placeholder="*.php" style="width: 160px" /></n-form-item>
        <n-form-item label="Containing text"><n-input v-model:value="searchDraft.contains" placeholder="optional" style="width: 220px" /></n-form-item>
        <n-form-item label=" "><n-button size="small" type="primary" @click="runSearch">Search</n-button></n-form-item>
      </n-form>
      <p class="muted mono">{{ path }}</p>
      <template v-if="searchResult">
        <p class="muted">
          {{ searchResult.matches.length }} matches from {{ searchResult.scanned }} files
          <span v-if="searchResult.truncated">(truncated)</span>
        </p>
        <n-data-table
          size="small"
          :bordered="false"
          :max-height="360"
          :data="searchResult.matches"
          :row-key="(row) => row.path"
          :columns="[
            { title: 'Path', key: 'path', ellipsis: { tooltip: true } },
            { title: 'Size', key: 'size', width: 100, render: (row) => bytes(row.size) },
            { title: 'Modified', key: 'modified', width: 160, render: (row) => datetime(row.modified) },
          ]"
        />
      </template>
    </n-modal>

    <!-- remote download -->
    <n-modal v-model:show="remoteOpen" preset="card" title="Download a URL to this directory" style="max-width: 500px">
      <n-form label-placement="top" size="small">
        <n-form-item label="URL"><n-input v-model:value="remoteDraft.url" placeholder="https://…" /></n-form-item>
        <n-form-item label="Save as"><n-input v-model:value="remoteDraft.filename" placeholder="taken from the URL" /></n-form-item>
      </n-form>
      <p class="muted mono">{{ path }}</p>
      <template #footer>
        <n-space justify="end">
          <n-button @click="remoteOpen = false">Cancel</n-button>
          <n-button type="primary" @click="remoteDownload">Download</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- compress -->
    <n-modal v-model:show="archiveOpen" preset="card" title="Compress selection" style="max-width: 460px">
      <n-form label-placement="top" size="small">
        <n-form-item label="Archive name (.zip, .tar.gz, .tar.xz …)">
          <n-input v-model:value="archiveTarget" placeholder="backup.tar.gz" class="mono" />
        </n-form-item>
      </n-form>
      <p class="muted">{{ selected.length }} items into {{ path }}</p>
      <template #footer>
        <n-space justify="end">
          <n-button @click="archiveOpen = false">Cancel</n-button>
          <n-button type="primary" @click="compress">Create</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

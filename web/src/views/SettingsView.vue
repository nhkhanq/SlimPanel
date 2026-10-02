<script setup>
import { onMounted, reactive, ref } from "vue";
import {
  NAlert,
  NButton,
  NCard,
  NDescriptions,
  NDescriptionsItem,
  NForm,
  NFormItem,
  NInput,
  NSpace,
  NTabPane,
  NTabs,
  NTag,
  useMessage,
} from "naive-ui";
import { api } from "../api";
import { state, setUser } from "../store";

const message = useMessage();

const settings = ref(null);
const nginxTest = ref(null);
const passwords = reactive({ old_password: "", new_password: "" });
const totp = ref(null);
const totpCode = ref("");

async function load() {
  settings.value = await api("/system/settings");
}

async function guard(action, success) {
  try {
    await action();
    if (success) message.success(success);
  } catch (exc) {
    message.error(exc.message);
  }
}

const changePassword = () =>
  guard(async () => {
    await api("/auth/password", { method: "POST", body: { ...passwords } });
    passwords.old_password = "";
    passwords.new_password = "";
  }, "Password changed");

const startTotp = () => guard(async () => (totp.value = await api("/auth/totp/setup", { method: "POST" })));

const enableTotp = () =>
  guard(async () => {
    await api("/auth/totp/enable", { method: "POST", body: { code: totpCode.value } });
    totp.value = null;
    totpCode.value = "";
    setUser(await api("/auth/me"));
  }, "Two-factor enabled");

const disableTotp = () =>
  guard(async () => {
    await api("/auth/totp/disable", { method: "POST" });
    setUser(await api("/auth/me"));
  }, "Two-factor disabled");

const testNginx = () => guard(async () => (nginxTest.value = await api("/system/nginx/test")));

const reloadNginx = () =>
  guard(async () => {
    const result = await api("/system/nginx/reload", { method: "POST" });
    result.ok ? message.success("nginx reloaded") : message.error(result.message);
  });

onMounted(load);
</script>

<template>
  <n-tabs type="line" animated>
    <n-tab-pane name="account" tab="Account">
      <n-card size="small" title="Change password" style="max-width: 460px">
        <n-form>
          <n-form-item label="Current password">
            <n-input v-model:value="passwords.old_password" type="password" show-password-on="click" />
          </n-form-item>
          <n-form-item label="New password">
            <n-input v-model:value="passwords.new_password" type="password" show-password-on="click" />
          </n-form-item>
        </n-form>
        <n-button type="primary" @click="changePassword">Update</n-button>
      </n-card>

      <n-card size="small" title="Two-factor authentication" style="max-width: 460px; margin-top: 12px">
        <n-space vertical>
          <n-tag :type="state.user?.totp_enabled ? 'success' : 'default'" :bordered="false" size="small">
            {{ state.user?.totp_enabled ? "enabled" : "disabled" }}
          </n-tag>

          <template v-if="!state.user?.totp_enabled">
            <n-button secondary @click="startTotp">Generate secret</n-button>
            <template v-if="totp">
              <n-alert type="info" :bordered="false">
                Add this secret to your authenticator app, then confirm with a code.
              </n-alert>
              <n-input :value="totp.secret" readonly class="mono" />
              <n-input v-model:value="totpCode" placeholder="6-digit code" />
              <n-button type="primary" @click="enableTotp">Enable</n-button>
            </template>
          </template>
          <n-button v-else type="error" secondary @click="disableTotp">Disable</n-button>
        </n-space>
      </n-card>
    </n-tab-pane>

    <n-tab-pane name="panel" tab="Panel">
      <n-card v-if="settings" size="small" title="Configuration">
        <n-descriptions :column="2" label-placement="left" bordered size="small">
          <n-descriptions-item label="Port">{{ settings.port }}</n-descriptions-item>
          <n-descriptions-item label="Entry path">{{ settings.entry_path || "/" }}</n-descriptions-item>
          <n-descriptions-item label="Data directory">{{ settings.data_dir }}</n-descriptions-item>
          <n-descriptions-item label="Web root">{{ settings.www_root }}</n-descriptions-item>
          <n-descriptions-item label="Log root">{{ settings.log_root }}</n-descriptions-item>
          <n-descriptions-item label="Dry run">{{ settings.dry_run }}</n-descriptions-item>
          <n-descriptions-item label="File roots" :span="2">
            {{ settings.file_roots.join(", ") }}
          </n-descriptions-item>
          <n-descriptions-item label="Managed services" :span="2">
            {{ settings.managed_services.join(", ") }}
          </n-descriptions-item>
          <n-descriptions-item label="nginx include" :span="2">
            <code class="mono">{{ settings.nginx_include_snippet }}</code>
          </n-descriptions-item>
        </n-descriptions>
      </n-card>

      <n-card size="small" title="nginx" style="margin-top: 12px">
        <n-space>
          <n-button secondary @click="testNginx">Test configuration</n-button>
          <n-button secondary @click="reloadNginx">Reload</n-button>
        </n-space>
        <pre v-if="nginxTest" class="mono log-pane" style="margin-top: 12px">{{ nginxTest.message }}</pre>
      </n-card>
    </n-tab-pane>
  </n-tabs>
</template>

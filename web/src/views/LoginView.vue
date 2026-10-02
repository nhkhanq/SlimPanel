<script setup>
import { ref } from "vue";
import { NAlert, NButton, NCard, NForm, NFormItem, NIcon, NInput } from "naive-ui";
import { LayersOutline } from "@vicons/ionicons5";
import { api } from "../api";
import { setUser } from "../store";

const form = ref({ username: "", password: "", code: "" });
const error = ref("");
const loading = ref(false);

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    const result = await api("/auth/login", { method: "POST", body: form.value });
    setUser({ username: result.username, totp_enabled: result.totp_enabled });
  } catch (exc) {
    error.value = exc.message;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-screen">
    <n-card class="login-card">
      <div class="masthead">
        <n-icon size="26" :component="LayersOutline" />
        <div>
          <h1>SlimPanel</h1>
          <p>Server control panel</p>
        </div>
      </div>
      <n-form @submit.prevent="submit">
        <n-form-item label="Username">
          <n-input v-model:value="form.username" placeholder="admin" @keyup.enter="submit" />
        </n-form-item>
        <n-form-item label="Password">
          <n-input
            v-model:value="form.password"
            type="password"
            show-password-on="click"
            @keyup.enter="submit"
          />
        </n-form-item>
        <n-form-item label="Two-factor code">
          <n-input v-model:value="form.code" placeholder="optional" @keyup.enter="submit" />
        </n-form-item>
        <n-alert v-if="error" type="error" :bordered="false" style="margin-bottom: 14px">
          {{ error }}
        </n-alert>
        <n-button type="primary" block :loading="loading" @click="submit">Sign in</n-button>
      </n-form>
    </n-card>
  </div>
</template>

<style scoped>
.login-screen {
  height: 100vh;
  display: grid;
  place-items: center;
  padding: 16px;
}

.login-card {
  width: min(380px, 100%);
}

.masthead {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.masthead h1 {
  margin: 0;
  font-size: 19px;
  font-weight: 600;
}

.masthead p {
  margin: 0;
  font-size: 12.5px;
  opacity: 0.6;
}
</style>

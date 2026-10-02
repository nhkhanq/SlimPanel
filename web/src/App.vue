<script setup>
import { computed, h, onMounted, ref } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import {
  NButton,
  NConfigProvider,
  NDialogProvider,
  NDropdown,
  NGlobalStyle,
  NIcon,
  NLayout,
  NLayoutHeader,
  NLayoutSider,
  NLoadingBarProvider,
  NMenu,
  NMessageProvider,
  NSpace,
  darkTheme,
} from "naive-ui";
import {
  LayersOutline,
  MoonOutline,
  PersonCircleOutline,
  SunnyOutline,
} from "@vicons/ionicons5";
import { api, setUnauthorizedHandler } from "./api";
import { menu } from "./router";
import { state, setUser, toggleTheme } from "./store";
import { darkOverrides, lightOverrides } from "./theme";
import LoginView from "./views/LoginView.vue";

const route = useRoute();
const router = useRouter();
const collapsed = ref(false);

const isDark = computed(() => state.theme === "dark");
const theme = computed(() => (isDark.value ? darkTheme : null));
const overrides = computed(() => (isDark.value ? darkOverrides : lightOverrides));

const renderIcon = (component) => () => h(NIcon, null, { default: () => h(component) });

const menuOptions = computed(() =>
  menu.map((item) => ({
    key: item.path,
    icon: renderIcon(item.icon),
    label: () => h(RouterLink, { to: item.path }, { default: () => item.name }),
  })),
);

const userOptions = [
  { key: "settings", label: "Account settings" },
  { key: "logout", label: "Sign out" },
];

async function onUserAction(key) {
  if (key === "logout") {
    await api("/auth/logout", { method: "POST" });
    setUser(null);
    return;
  }
  router.push("/settings");
}

setUnauthorizedHandler(() => setUser(null));

onMounted(async () => {
  try {
    setUser(await api("/auth/me"));
  } catch {
    setUser(null);
  } finally {
    state.ready = true;
  }
});
</script>

<template>
  <n-config-provider :theme="theme" :theme-overrides="overrides">
    <n-global-style />
    <n-loading-bar-provider>
      <n-message-provider>
        <n-dialog-provider>
          <login-view v-if="state.ready && !state.user" />

          <n-layout v-else-if="state.ready" has-sider position="absolute">
            <n-layout-sider
              bordered
              collapse-mode="width"
              :collapsed="collapsed"
              :collapsed-width="64"
              :width="216"
              show-trigger
              @collapse="collapsed = true"
              @expand="collapsed = false"
            >
              <div class="brand">
                <n-icon size="20" :component="LayersOutline" />
                <span v-if="!collapsed">SlimPanel</span>
              </div>
              <n-menu
                :collapsed="collapsed"
                :collapsed-width="64"
                :collapsed-icon-size="20"
                :options="menuOptions"
                :value="route.path"
              />
            </n-layout-sider>

            <n-layout>
              <n-layout-header bordered class="header">
                <strong>{{ route.name }}</strong>
                <n-space align="center" :size="8">
                  <n-button quaternary circle @click="toggleTheme">
                    <template #icon>
                      <n-icon :component="isDark ? SunnyOutline : MoonOutline" />
                    </template>
                  </n-button>
                  <n-dropdown :options="userOptions" @select="onUserAction">
                    <n-button quaternary>
                      <template #icon>
                        <n-icon :component="PersonCircleOutline" />
                      </template>
                      {{ state.user?.username }}
                    </n-button>
                  </n-dropdown>
                </n-space>
              </n-layout-header>

              <n-layout position="absolute" style="top: 52px" :native-scrollbar="false">
                <router-view v-slot="{ Component }">
                  <component :is="Component" class="page" />
                </router-view>
              </n-layout>
            </n-layout>
          </n-layout>
        </n-dialog-provider>
      </n-message-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<style scoped>
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
}

.header {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
</style>

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
  NNotificationProvider,
  NSpace,
  NTag,
  darkTheme,
} from "naive-ui";
import {
  MoonOutline,
  PersonCircleOutline,
  SearchOutline,
  SunnyOutline,
} from "@vicons/ionicons5";
import { api, setUnauthorizedHandler } from "./api";
import { brandIcon, flatMenu, menu } from "./router";
import { state, setUser, toggleTheme } from "./store";
import { darkOverrides, lightOverrides } from "./theme";
import LoginView from "./views/LoginView.vue";
import CommandPalette from "./components/CommandPalette.vue";

const route = useRoute();
const router = useRouter();
const collapsed = ref(false);
const paletteOpen = ref(false);

const isDark = computed(() => state.theme === "dark");
const theme = computed(() => (isDark.value ? darkTheme : null));
const overrides = computed(() => (isDark.value ? darkOverrides : lightOverrides));

const renderIcon = (component) => () => h(NIcon, null, { default: () => h(component) });

const menuOptions = computed(() =>
  menu.map((group) => ({
    type: "group",
    key: group.key,
    label: group.label,
    children: group.children.map((item) => ({
      key: item.path,
      icon: renderIcon(item.icon),
      label: () => h(RouterLink, { to: item.path }, { default: () => item.name }),
    })),
  })),
);

const title = computed(
  () => flatMenu.find((item) => item.path === route.path)?.name || route.name || "SlimPanel",
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

function onKeydown(event) {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    paletteOpen.value = true;
  }
}

setUnauthorizedHandler(() => setUser(null));

onMounted(async () => {
  window.addEventListener("keydown", onKeydown);
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
        <n-notification-provider>
          <n-dialog-provider>
            <login-view v-if="state.ready && !state.user" />

            <n-layout v-else-if="state.ready" has-sider position="absolute">
              <n-layout-sider
                bordered
                collapse-mode="width"
                :collapsed="collapsed"
                :collapsed-width="64"
                :width="224"
                :native-scrollbar="false"
                show-trigger
                @collapse="collapsed = true"
                @expand="collapsed = false"
              >
                <div class="sider-brand">
                  <span class="dot"><n-icon size="15" color="#fff" :component="brandIcon" /></span>
                  <span v-if="!collapsed">SlimPanel</span>
                </div>
                <n-menu
                  :collapsed="collapsed"
                  :collapsed-width="64"
                  :collapsed-icon-size="20"
                  :indent="18"
                  :options="menuOptions"
                  :value="route.path"
                />
              </n-layout-sider>

              <n-layout>
                <n-layout-header bordered class="header">
                  <n-space align="center" :size="10">
                    <strong>{{ title }}</strong>
                    <n-tag v-if="state.user?.totp_enabled" size="small" type="success" :bordered="false">
                      2FA on
                    </n-tag>
                  </n-space>

                  <n-space align="center" :size="6">
                    <n-button quaternary size="small" @click="paletteOpen = true">
                      <template #icon><n-icon :component="SearchOutline" /></template>
                      Search
                    </n-button>
                    <n-button quaternary circle @click="toggleTheme">
                      <template #icon>
                        <n-icon :component="isDark ? SunnyOutline : MoonOutline" />
                      </template>
                    </n-button>
                    <n-dropdown :options="userOptions" @select="onUserAction">
                      <n-button quaternary>
                        <template #icon><n-icon :component="PersonCircleOutline" /></template>
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

            <command-palette v-model:show="paletteOpen" />
          </n-dialog-provider>
        </n-notification-provider>
      </n-message-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<style scoped>
.header {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
}
</style>

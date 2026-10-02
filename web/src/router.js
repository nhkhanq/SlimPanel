import { createRouter, createWebHashHistory } from "vue-router";
import {
  ArchiveOutline,
  DownloadOutline,
  FolderOpenOutline,
  GlobeOutline,
  ReaderOutline,
  ServerOutline,
  SettingsOutline,
  SpeedometerOutline,
  TerminalOutline,
  TimeOutline,
} from "@vicons/ionicons5";

export const menu = [
  { path: "/overview", name: "Overview", icon: SpeedometerOutline, component: () => import("./views/OverviewView.vue") },
  { path: "/sites", name: "Sites", icon: GlobeOutline, component: () => import("./views/SitesView.vue") },
  { path: "/databases", name: "Databases", icon: ServerOutline, component: () => import("./views/DatabasesView.vue") },
  { path: "/files", name: "Files", icon: FolderOpenOutline, component: () => import("./views/FilesView.vue") },
  { path: "/cron", name: "Cron", icon: TimeOutline, component: () => import("./views/CronView.vue") },
  { path: "/backups", name: "Backups", icon: ArchiveOutline, component: () => import("./views/BackupsView.vue") },
  { path: "/terminal", name: "Terminal", icon: TerminalOutline, component: () => import("./views/TerminalView.vue") },
  { path: "/logs", name: "Logs", icon: ReaderOutline, component: () => import("./views/LogsView.vue") },
  { path: "/import", name: "Import", icon: DownloadOutline, component: () => import("./views/ImportView.vue") },
  { path: "/settings", name: "Settings", icon: SettingsOutline, component: () => import("./views/SettingsView.vue") },
];

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", redirect: "/overview" },
    ...menu.map(({ path, name, component }) => ({ path, name, component })),
    { path: "/:pathMatch(.*)*", redirect: "/overview" },
  ],
});

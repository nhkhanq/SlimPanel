import { createRouter, createWebHashHistory } from "vue-router";
import {
  AppsOutline,
  ArchiveOutline,
  BuildOutline,
  CloudDownloadOutline,
  CodeSlashOutline,
  CubeOutline,
  DocumentTextOutline,
  FolderOpenOutline,
  GlobeOutline,
  KeyOutline,
  LayersOutline,
  ListOutline,
  LockClosedOutline,
  NotificationsOutline,
  PulseOutline,
  RocketOutline,
  ServerOutline,
  SettingsOutline,
  SpeedometerOutline,
  SwapVerticalOutline,
  TerminalOutline,
  TimeOutline,
  TrashOutline,
} from "@vicons/ionicons5";

// Grouped the way aaPanel groups its sidebar.
export const menu = [
  {
    key: "main",
    label: "Overview",
    children: [
      { path: "/overview", name: "Dashboard", icon: SpeedometerOutline, component: () => import("./views/OverviewView.vue") },
      { path: "/monitor", name: "Monitor", icon: PulseOutline, component: () => import("./views/MonitorView.vue") },
    ],
  },
  {
    key: "hosting",
    label: "Hosting",
    children: [
      { path: "/sites", name: "Websites", icon: GlobeOutline, component: () => import("./views/SitesView.vue") },
      { path: "/projects", name: "Projects", icon: RocketOutline, component: () => import("./views/ProjectsView.vue") },
      { path: "/databases", name: "Databases", icon: ServerOutline, component: () => import("./views/DatabasesView.vue") },
      { path: "/ftp", name: "FTP", icon: SwapVerticalOutline, component: () => import("./views/FtpView.vue") },
      { path: "/files", name: "Files", icon: FolderOpenOutline, component: () => import("./views/FilesView.vue") },
      { path: "/recycle", name: "Recycle bin", icon: TrashOutline, component: () => import("./views/RecycleView.vue") },
    ],
  },
  {
    key: "platform",
    label: "Platform",
    children: [
      { path: "/apps", name: "App store", icon: AppsOutline, component: () => import("./views/AppsView.vue") },
      { path: "/php", name: "PHP", icon: CodeSlashOutline, component: () => import("./views/PhpView.vue") },
      { path: "/docker", name: "Docker", icon: CubeOutline, component: () => import("./views/DockerView.vue") },
      { path: "/toolbox", name: "Toolbox", icon: BuildOutline, component: () => import("./views/ToolboxView.vue") },
    ],
  },
  {
    key: "operations",
    label: "Operations",
    children: [
      { path: "/security", name: "Security", icon: LockClosedOutline, component: () => import("./views/SecurityView.vue") },
      { path: "/cron", name: "Cron", icon: TimeOutline, component: () => import("./views/CronView.vue") },
      { path: "/backups", name: "Backups", icon: ArchiveOutline, component: () => import("./views/BackupsView.vue") },
      { path: "/notify", name: "Alerts", icon: NotificationsOutline, component: () => import("./views/NotifyView.vue") },
      { path: "/tasks", name: "Tasks", icon: ListOutline, component: () => import("./views/TasksView.vue") },
      { path: "/logs", name: "Logs", icon: DocumentTextOutline, component: () => import("./views/LogsView.vue") },
    ],
  },
  {
    key: "system",
    label: "System",
    children: [
      { path: "/terminal", name: "Terminal", icon: TerminalOutline, component: () => import("./views/TerminalView.vue") },
      { path: "/api-keys", name: "API keys", icon: KeyOutline, component: () => import("./views/ApiKeysView.vue") },
      { path: "/import", name: "Import", icon: CloudDownloadOutline, component: () => import("./views/ImportView.vue") },
      { path: "/settings", name: "Settings", icon: SettingsOutline, component: () => import("./views/SettingsView.vue") },
    ],
  },
];

export const brandIcon = LayersOutline;

export const flatMenu = menu.flatMap((group) => group.children);

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", redirect: "/overview" },
    ...flatMenu.map(({ path, name, component }) => ({ path, name, component })),
    { path: "/:pathMatch(.*)*", redirect: "/overview" },
  ],
});

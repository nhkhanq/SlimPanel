// aaPanel's palette: a green primary with a cool grey chrome.
export const lightOverrides = {
  common: {
    primaryColor: "#20a53a",
    primaryColorHover: "#1c9134",
    primaryColorPressed: "#17802c",
    primaryColorSuppl: "#20a53a",
    infoColor: "#2a78d6",
    successColor: "#20a53a",
    warningColor: "#f0a020",
    errorColor: "#e34948",
    borderRadius: "6px",
    bodyColor: "#f1f3f6",
    cardColor: "#ffffff",
    fontSize: "14px",
    textColor1: "#1f2328",
    textColor2: "#4b5563",
    textColor3: "#8b929e",
    borderColor: "#e3e7ee",
  },
  Layout: { siderColor: "#1d2531", headerColor: "#ffffff", color: "#f1f3f6" },
  Menu: {
    itemColorActive: "rgba(32,165,58,0.16)",
    itemColorActiveHover: "rgba(32,165,58,0.22)",
    itemTextColor: "#b7c0cd",
    itemTextColorHover: "#ffffff",
    itemTextColorActive: "#5fd47a",
    itemTextColorActiveHover: "#5fd47a",
    itemIconColor: "#8c99aa",
    itemIconColorHover: "#ffffff",
    itemIconColorActive: "#5fd47a",
    itemIconColorActiveHover: "#5fd47a",
    arrowColor: "#8c99aa",
    groupTextColor: "#6c7888",
  },
  Card: { borderRadius: "8px" },
  Tabs: { tabFontWeightActive: 600 },
};

export const darkOverrides = {
  common: {
    primaryColor: "#2fb94c",
    primaryColorHover: "#3cc959",
    primaryColorPressed: "#249c3d",
    primaryColorSuppl: "#2fb94c",
    infoColor: "#3987e5",
    successColor: "#2fb94c",
    warningColor: "#d99014",
    errorColor: "#e66767",
    borderRadius: "6px",
    bodyColor: "#0e1116",
    cardColor: "#161a21",
    modalColor: "#161a21",
    popoverColor: "#1d222b",
    borderColor: "#262c37",
    fontSize: "14px",
  },
  Layout: { siderColor: "#12161c", headerColor: "#141920", color: "#0e1116" },
  Menu: {
    itemColorActive: "rgba(47,185,76,0.18)",
    itemColorActiveHover: "rgba(47,185,76,0.24)",
    itemTextColor: "#9aa4b2",
    itemTextColorActive: "#5fd47a",
    itemTextColorActiveHover: "#5fd47a",
    itemIconColorActive: "#5fd47a",
    itemIconColorActiveHover: "#5fd47a",
    groupTextColor: "#657085",
  },
  Card: { borderRadius: "8px", color: "#161a21" },
  Tabs: { tabFontWeightActive: 600 },
};

export const seriesColors = {
  light: {
    cpu: "#20a53a",
    memory: "#2a78d6",
    swap: "#9b59b6",
    load: "#f0a020",
    net_up: "#e34948",
    net_down: "#2a78d6",
    surface: "#ffffff",
    grid: "#e6eaf1",
    text: "#6b7280",
  },
  dark: {
    cpu: "#2fb94c",
    memory: "#3987e5",
    swap: "#a569bd",
    load: "#d99014",
    net_up: "#e66767",
    net_down: "#3987e5",
    surface: "#161a21",
    grid: "#242a34",
    text: "#8b94a3",
  },
};

export const gaugeColors = (percent) => {
  if (percent >= 90) return "#e34948";
  if (percent >= 75) return "#f0a020";
  return "#20a53a";
};

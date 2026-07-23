import axiosClient from "./axiosClient";

export interface PluginItem {
  plugin_id: string;
  name: string;
  description: string;
  version: string;
  category: string;
  is_installed: boolean;
  is_enabled: boolean;
}

export const pluginsApi = {
  listPlugins: async () => {
    const res = await axiosClient.get<PluginItem[]>("/plugins");
    return res.data;
  },

  installPlugin: async (pluginId: string) => {
    const res = await axiosClient.post("/plugins/install", { plugin_id: pluginId });
    return res.data;
  },

  togglePlugin: async (pluginId: string, isEnabled: boolean) => {
    const res = await axiosClient.post(`/plugins/${pluginId}/toggle`, { is_enabled: isEnabled });
    return res.data;
  },
};

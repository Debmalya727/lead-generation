import axiosClient from "./axiosClient";

export interface NotificationItem {
  notification_id: string;
  recipient_id: string;
  title: string;
  message: string;
  type: string;
  event_type?: string;
  data: Record<string, any>;
  is_read: boolean;
  created_at: string;
}

export const notificationsApi = {
  listNotifications: async (unreadOnly: boolean = false) => {
    const res = await axiosClient.get<NotificationItem[]>("/notifications", { params: { unread_only: unreadOnly } });
    return res.data;
  },

  markRead: async (notificationIds: string[]) => {
    const res = await axiosClient.post<{ marked_count: number }>("/notifications/read", { notification_ids: notificationIds });
    return res.data;
  },
};

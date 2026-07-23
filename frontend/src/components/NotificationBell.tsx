import React, { useEffect, useState } from "react";
import { notificationsApi, NotificationItem } from "../api/notifications";

export const NotificationBell: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    fetchNotifications();
    const timer = setInterval(fetchNotifications, 10000);
    return () => clearInterval(timer);
  }, []);

  const fetchNotifications = async () => {
    try {
      const data = await notificationsApi.listNotifications(false);
      setNotifications(data);
    } catch {}
  };

  const handleMarkAllRead = async () => {
    const unreadIds = notifications.filter(n => !n.is_read).map(n => n.notification_id);
    if (unreadIds.length === 0) return;
    try {
      await notificationsApi.markRead(unreadIds);
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch {}
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div style={{ position: "relative" }}>
      <button onClick={() => setOpen(!open)} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#a5b4fc", padding: "0.4rem 0.8rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
        🔔 Notifications
        {unreadCount > 0 && (
          <span style={{ background: "#ef4444", color: "#fff", fontSize: "0.7rem", fontWeight: 800, padding: "0.15rem 0.45rem", borderRadius: "100px" }}>{unreadCount}</span>
        )}
      </button>

      {open && (
        <div style={{ position: "absolute", top: "45px", right: 0, width: "360px", background: "rgba(15,23,42,0.95)", border: "1px solid rgba(99,102,241,0.3)", borderRadius: "10px", padding: "1rem", boxShadow: "0 10px 25px rgba(0,0,0,0.5)", backdropFilter: "blur(12px)", zIndex: 200, display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(99,102,241,0.15)", paddingBottom: "0.5rem" }}>
            <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#e2e8f0" }}>Notifications ({unreadCount} new)</div>
            {unreadCount > 0 && (
              <button onClick={handleMarkAllRead} style={{ background: "none", border: "none", color: "#6366f1", fontSize: "0.75rem", cursor: "pointer" }}>Mark all read</button>
            )}
          </div>

          <div style={{ maxHeight: "300px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {notifications.length === 0 ? (
              <div style={{ color: "#64748b", fontSize: "0.8rem", textAlign: "center", padding: "1rem" }}>No notifications</div>
            ) : (
              notifications.map(n => (
                <div key={n.notification_id} style={{ padding: "0.6rem 0.75rem", borderRadius: "6px", background: n.is_read ? "rgba(30,41,59,0.3)" : "rgba(99,102,241,0.12)", border: `1px solid ${n.is_read ? "rgba(99,102,241,0.1)" : "rgba(99,102,241,0.3)"}` }}>
                  <div style={{ fontSize: "0.78rem", fontWeight: 700, color: n.is_read ? "#cbd5e1" : "#a5b4fc" }}>{n.title}</div>
                  <div style={{ fontSize: "0.72rem", color: "#94a3b8", marginTop: "0.2rem" }}>{n.message}</div>
                  <div style={{ fontSize: "0.65rem", color: "#64748b", marginTop: "0.25rem" }}>{new Date(n.created_at).toLocaleTimeString()}</div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

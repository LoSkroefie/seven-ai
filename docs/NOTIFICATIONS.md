# Native Desktop Notifications

Seven submits native per-user notifications through:

- Windows: WinRT toast via PowerShell
- Linux: freedesktop `notify-send`
- macOS: Notification Center through `osascript`

The `notification_status` and `notify_desktop` tools expose availability and submission. Notification text is passed through environment variables on Windows so message content is not embedded in process command lines. XML escaping occurs inside the PowerShell adapter.

Successful state is called `submitted`, never “viewed” or “read”; desktop APIs do not prove that the user saw a notification.

## Reminder delivery

When talk mode is active, due reminders use Seven's speech/output callback. When no callback exists and `SEVEN_NOTIFICATIONS=1` (default), the heartbeat submits a native desktop notification. A reminder is marked delivered only after the backend accepts it. Failed/unavailable submissions increment attempts and remain due.

Set `SEVEN_NOTIFICATIONS=0` to retain due reminders until an interactive talk session.

Automated tests prove command/environment contracts and failure semantics. A visible-notification manual matrix for each supported desktop session remains required.

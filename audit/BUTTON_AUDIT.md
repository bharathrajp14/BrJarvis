# BRJARVIS Button Audit

| Line | Label / aria-label | Handler | Permanent disabled |
|---:|---|---|---|
| 164 | setMobileOpen(false)} aria-label="Close navigation"> | PASS | NO |
| 177 | setToast('Settings are managed through the local server configuration.')} aria-l | PASS | NO |
| 180 | setMobileOpen(false)} aria-label="Close navigation" />} | PASS | NO |
| 183 | setMobileOpen(true)} aria-label="Open navigation"> | PASS | NO |
| 184 | setSearchOpen(true)}> Search anything ⌘ K | PASS | NO |
| 184 | selectView('operations')} aria-label="Open notifications" title= live notificati | PASS | NO |
| 184 | setLightMode((value) => !value)} aria-label= title= > | PASS | NO |
| 200 | setToast(null)} aria-label="Dismiss"> | PASS | NO |
| 207 | : } | PASS | NO |
| 211 | New command | PASS | NO |
| 220 | onView('tasks')}> View active execution | PASS | NO |
| 220 | onView('workspace')}> Explore workspace | PASS | NO |
| 221 | fileInput.current?.click()}> | PASS | NO |
| 221 | setMode(item)}> | PASS | NO |
| 221 | setPrivacy(privacy === 'balanced' ? 'local_only' : 'balanced')}> | PASS | NO |
| 221 | icon/button | PASS | NO |
| 222 | onView('tasks')}>Open task board | PASS | NO |
| 229 | Open task board | PASS | NO |
| 229 | Open full timeline | PASS | NO |
| 231 | void refresh()} aria-label="Refresh events" disabled= title="Refresh live events | PASS | NO |
| 233 | setFilter(item)}> | PASS | NO |
| 233 | onView('command')}> New task | PASS | NO |
| 251 | resolve(approval.id, approval.taskId, false)}> Reject | PASS | NO |
| 251 | resolve(approval.id, approval.taskId, true)}> Approve action | PASS | NO |
| 274 | void selectEntry(entry)}> | PASS | NO |
| 277 | openPreview(artifact)}>Preview | PASS | NO |
| 277 | setPreview(null)} aria-label="Close preview"> | PASS | NO |
| 292 | Save memory | MISSING | NO |
| 292 | void remove(memory)} disabled= aria-label= `} title="Delete memory"> | PASS | NO |
| 295 | icon/button | PASS | NO |
| 303 | icon/button | MISSING | NO |
| 309 | onView('integrations')}> Configure providers | PASS | NO |
| 309 | onView('memory')}>Manage records | PASS | NO |
| 309 | onView('workspace')}>Open workspace | PASS | NO |
| 312 | onNavigate(item.id)}> ↵ | PASS | NO |

**Total button elements found:** 35
**Missing handlers:** 2
**Permanent disabled buttons:** 0

A button with no handler or a permanent disabled state is a review item. Navigation and form-submit buttons are considered functional when their parent handler is explicit.

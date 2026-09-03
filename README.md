<div align="center">

# Felix WhatsApp Api Frappe and ERPnext

**A cost-effective, native WhatsApp integration for ERPNext / Frappe — powered by Felix WhatApp Api.**

Send WhatsApp text messages and PDF attachments straight from any DocType, track message delivery logs, and automate notifications with significantly lower operational costs.

[![Frappe](https://img.shields.io/badge/Frappe-v15%20%7C%20v16-0089FF)](https://frappeframework.com)
[![ERPNext](https://img.shields.io/badge/ERPNext-v15%20%7C%20v16-2490EF)](https://erpnext.com)
[![Provider](https://img.shields.io/badge/Provider-Felix-WhatsApp-Api-25D366)](https://)
[![Python](https://img.shields.io/badge/Python-%E2%89%A53.10-3776AB)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](license.txt)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Why Felix WhatsApp Api ERPNext?](#-why-waapifrappe)
- [Key Features](#-key-features)
- [How It Works](#-how-it-works)
- [Data Model (DocTypes)](#-data-model-doctypes)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Enabling the Send Button (Notification Setup)](#-enabling-the-send-button-notification-setup)
- [Anti‑Ban & Safety](#-anti-ban--safety)
- [API Reference](#-api-reference)
- [Acknowledgements & Credits](#-acknowledgements--credits)
- [License](#-license)

---

## 🧭 Overview

**Felix-WhatsApp-Api-ERPNext** extends ERPNext's native **Notification** engine to integrate **WhatsApp** as a standard delivery channel. Instead of building a complex parallel notification system, it overrides the standard `Notification` DocType to let you use your existing ERPNext workflow (conditions, recipients, events, Jinja templates, print formats) — delivering messages directly over WhatsApp via [Felix WhatsApp Api]

Every dispatched message is logged inside ERPNext, linked back to its source document (Sales Invoice, Customer, Order, etc.), and recorded for auditing.

---

## 💡 Why Felix-WhatsApp-Api-ERPNext?

* 💰 **75% Cost Reduction:** Designed specifically as an affordable alternative to high-cost WhatsApp integration providers (reducing operational costs from ~$39/month down to ~$10/month).
* ⚙️ **Native Integration:** Fully leverages Frappe's standard Notification mechanism without modifying core files.
* 🚀 **Lightweight & Fast:** Optimized for smooth PDF generation and direct payload processing.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Send from Any DocType** | A WhatsApp action button appears automatically on any document type that has an active Felix WhatsApp Api notification configured. |
| **Text & PDF Attachments** | Send plain text or attach rendered document PDFs (supports both Chrome Headless and `wkhtmltopdf`). |
| **Direct Document Linkage** | All sent messages are stored in a dedicated log linked to the source document via dynamic reference. |
| **Duplicate‑Send Protection** | Prompts the user for confirmation if a message has already been sent for the active document. |
| **Multi‑Notification Picker** | Displays a selection dialog if multiple WhatsApp notifications exist for a single DocType. |
| **Anti‑Ban Safeguards** | Built-in randomized delays between messages, optional daily caps, and resilient retry sessions. |
| **Smart Phone Normalization** | Auto-formats phone numbers (removes international `00`, handles leading zeroes, and formats country codes). |

---

## ⚙️ How It Works 
```
┌──────────────┐     Notification (channel = Felix-WhatsApp-Api-ERPNext) ┌──────────────────────────────────────────┐
│  ERPNext Doc │ ──────────────────────────────────────────▶            │ Felix-WhatsApp-Api-ERPNext application   │
│ (Invoice...) │   on save/submit OR manual "Send" button                │ Notification                             │
└──────────────┘                                                         │  override                                │
                                                                         └──────┬───────────────────────────────────┘
                                                                                │  POST (text/PDF)
                                                                                ▼
                                                                            ┌───────────────┐
                                                                            │  Waapi API    │
                                                                            └──────┬────────┘
                                                                                   │  delivers to WhatsApp
                                                                                   │
                                        ┌──────────────────────────────────────────┘
                                        ▼
                               ┌─────────────────────┐        every 4h reconciliation
                               │ For Whats Messages  │ ◀───────────────────────────────
                               │        Log          │   (safety net for missed events)
                               └─────────────────────┘
```

1. **Trigger** — Dispatched automatically on Notification events (*New / Save / Submit*) or manually via the form's WhatsApp button.
2. **Dispatch** — `Felix-WhatsApp-Api-ERPNextNotification` renders the Jinja message template, normalizes the recipient phone number, generates the document PDF, and posts it to Felix-WhatsApp-Api-ERPNext.
3. **Log** — Each successful transmission is recorded in **Felix-WhatsApp-Api-ERPNext Messages Log** with full reference linkage.

---

## 🗂️ Data Model (DocTypes)

Felix-WhatsApp-Api-ERPNext ships with the following DocTypes:

### 1. `Felix-WhatsApp-Api-ERPNext Configuration` (Single)

Holds your global Felix-WhatsApp-Api-ERPNext credentials and default configuration settings.

| Field | Type | Required | Description |
|---|---|:---:|---|
| `api_url` | Data | ✅ | Base API URL (e.g. `http://localhost:8000/api/v1/messages/send-text`). |
| `instance_id` | Data | ✅ | Your Felix-WhatsApp-Api-ERPNext Instance ID (e.g. `inst_abcdef12345`). |
| `token` | Data | ✅ | Your Felix-WhatsApp-Api-ERPNext Bearer Token. |
| `pdf_generator` | Select | — | Preferred PDF rendering engine (`chrome` or `wkhtmltopdf`). |

### 2. `Felix-WhatsApp-Api-ERPNext Messages Log`

The central audit trail recording dispatched messages.

| Field | Type | Description |
|---|---|---|
| `felix_waapi_id` | Data | The reference ID returned by Felix-WhatsApp-Api-ERPNext. |
| `to_number` | Data | Recipient phone number. |
| `message_body` | Small Text | Rendered message body or media caption. |
| `status` | Select | Status indicator (`sent` · `failed`). |
| `reference_doctype` | Link → DocType | Source document type (e.g., `Sales Invoice`). |
| `reference_name` | Dynamic Link | Exact source document name. |

---

## 💾 Installation

Install on your bench using the **bench CLI**:

```bash
cd $PATH_TO_YOUR_BENCH

# Fetch the repository
bench get-app https://github.com/its4nas/Felix-Whatsapp-Api-ERPNext --branch main

# Install it on your site
bench --site your-site.local install-app Felix-Whatsapp-Api-ERPNext
```

**Requirements:**
ERPNext / Frappe v15 → Python ≥ 3.10
ERPNext / Frappe v16 → Python 3.14 (>=3.14,<3.15) and Node.js 24

## 🔧 Configuration

Open Felix-Whatsapp-Api-ERPNext Configuration in ERPNext.
Enter your API URL (http://localhost:8000/api/v1/messages/send-text), Instance ID, and Bearer Token obtained from your Felix-Whatsapp-Api-ERPNext dashboard.
Save the configuration.

## 🔔 Enabling the Send Button (Notification Setup)

Felix-Whatsapp-Api-ERPNext does not add a new DocType for sending — it relies on Frappe's standard **Notification** DocType after overriding it. So all sending options are configured by creating a **Notification** from: (Settings → Notifications / `Notification`).

Below is a complete reference for every field on the screen, with its relation to Felix-Whatsapp-Api-ERPNext.

### Core Fields

| Field | Fieldname | Description |
|---|---|---|
| **Enabled** | `enabled` | Enables the notification. Must be on for the WhatsApp button to appear and for sending to work. |
| **Is Standard** | `is_standard` | Usually set for notifications shipped with apps (developers). Leave it off for notifications you create manually. |
| **Channel** | `channel` | **Must be set to `Felix-Whatsapp-Api-ERPNext`** — this is the channel that enables WhatsApp sending. |
| **Document Type** | `document_type` | The document type the button appears on and the notification is sent from (Sales Invoice, Customer, etc.). |
| **Send System Notification** | `send_system_notification` | If enabled, the notification also appears in the notifications dropdown at the top‑right of ERPNext. |

### When Is It Sent? (Send Alert On)

The **`event`** field defines what automatically triggers sending:

| Option | Meaning |
|---|---|
| **New** | When a new document is created. |
| **Save** | When the document is saved. |
| **Submit** | When the document is submitted. |
| **Cancel** | When the document is cancelled. |
| **Days After / Days Before** | A number of days after/before a given date field. |
| **Minutes After / Minutes Before** | A number of minutes after/before a given datetime field. |
| **Value Change** | When a specific field's value changes. |
| **Method / Custom** | On a custom programmatic call. |

> Besides automatic event‑based sending, you can always send **manually** via the WhatsApp button on the document.

### Recipients

A child table that defines who receives the message, with the same logic as standard ERPNext notifications:

| Column | Fieldname | Purpose |
|---|---|---|
| **Receiver By Document Field** | `receiver_by_document_field` | The field on the document that holds the recipient's **phone number** (e.g. `custom_customer_phone`). This is the key one for WhatsApp sending. |
| **Receiver By Role** | `receiver_by_role` | (Optional) send to all users holding a given role. |
| **Condition** | `condition` | (Optional) a condition specific to this recipient row. |

### Message

The **`message`** field is the message template and supports **Jinja** to access document fields. Example:

```html
<h3>Invoice Notification</h3>
<p>Dear {{ doc.customer }},</p>
<p>Your invoice <b>{{ doc.name }}</b> for the amount of <b>{{ doc.fmt_grand_total }}</b> has been processed.</p>
```

### Attachment Settings

| Field | Fieldname | Description |
|---|---|---|
| **Attach Print** | `attach_print` | Enable to send the document as a **PDF** alongside the message (the message text is used as the caption). |
| **Print Format** | `print_format` | Determines **which print format is sent over WhatsApp** as a PDF. If left empty, the document's default format is used. |
| **Attach Files** | `attach_files` | Attach the document's files: **From Field** (a specific field) or **All** (all attachments). |

### After Saving

Once the notification is saved, a green **WhatsApp** icon button appears on the chosen DocType. Clicking it:
1. Checks whether a message was already sent for the document (and asks before re‑sending).
2. Sends the single matching notification directly, or shows a picker if several exist for the same document.
3. Displays a spinner while sending, then a success/failure alert.



## 🛡️ Anti‑Ban & Safety

To keep your WhatsApp account safe from automated spam detection, Felix-Whatsapp-Api-ERPNext provides built-in protections:

| Feature | Default | Purpose |
|---|---|---|
| **Randomized delay** | 3.0 – 8.0 seconds between messages | Prevents robotic, rapid-fire message bursts. |
| **Daily cap counter** | Configurable via Redis | Optional daily message limit per instance. |
| **Session Retries** | 3 attempts with backoff | Handles temporary network blips or rate limits. |


## 📡 API Reference

Whitelisted methods you can call from the client or other apps:

| Method | Purpose |
|---|---|
| `...notifications.send_whatsapp_file` | Triggers immediate direct sending for a specific document and notification. |
| `...notifications.get_all_doctypes` | Returns all DocTypes configured with active Felix-Whatsapp-Api-ERPNext notifications. |
| `...notifications.get_whatsapp_notifications` | Fetches active WhatsApp notifications for a given DocType. |
| `...notifications.gw_already_sent` | Checks if a message was previously sent for a given document. |

*(Full path prefix: `felix_waapi.overrides` / `felix_waapi.felix_waapi.doctype.for_whats_net_configuration`.)*

## Acknowledgements & Credits

Special thanks to [@EliasALshaibani](https://github.com/EliasALshaibani/) . The structure and conceptual implementation of this app were inspired by his open-source work on ERPNext WhatsApp integration, providing a foundation for adapting and extending support to Felix-Whatsapp-Api-ERPNext.

## 📄 License

Released under the **MIT License**. See [license.txt](license.txt) for details. 

---
<div align="center">
  
Developed with 💚 by [@its4nas](https://github.com/its4nas/) for the Frappe & ERPNext Community.

</div>

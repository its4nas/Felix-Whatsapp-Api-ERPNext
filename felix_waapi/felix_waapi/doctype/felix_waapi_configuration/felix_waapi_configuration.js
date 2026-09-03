// Copyright (c) 2026, Anas Al-Dharei and contributors
// For license information, please see license.txt

frappe.ui.form.on("felix_waapi Configuration", {
	refresh(frm) {
        // زرّ: نسخ رابط الـ webhook
        if (frm.doc.webhook_url) {
            frm.add_custom_button(__("Copy Webhook URL"), () => {
                frappe.utils.copy_to_clipboard(frm.doc.webhook_url);
                frappe.show_alert({ message: __("Webhook URL copied"), indicator: "green" });
            });
        }

        // زرّ: إعادة توليد السرّ
        frm.add_custom_button(__("Regenerate Secret"), () => {
            frappe.confirm(
                __("This will change the secret. You must update the URL in UltraMsg afterwards. Continue?"),
                () => {
                    frappe.call({
                        method: "felix_waapi.felix_waapi.doctype.felix_waapi_configuration.felix_waapi_configuration.regenerate_webhook_secret",
                        callback: (r) => {
                            if (r.message) {
                                frappe.show_alert({ message: __("Secret regenerated"), indicator: "green" });
                                frm.reload_doc();
                            }
                        },
                    });
                }
            );
        });
	},
});

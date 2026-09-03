# Copyright (c) 2026, Anas Al-Dharei and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

WEBHOOK_METHOD = "felix_waapi.overrides.felix_waapi_sync.ultramsg_webhook"

class felix_waapiConfiguration(Document):
	def validate(self):
		# ولّد السرّ تلقائيًا أول مرة لو كان فارغًا
		if not self.webhook_secret:
			self.webhook_secret = frappe.generate_hash(length=32)
		# ابنِ رابط الـ webhook الكامل (للعرض والنسخ)
		self.webhook_url = self._build_webhook_url()
	
	def _build_webhook_url(self):
		base = frappe.utils.get_url()  # رابط الموقع الحالي
		return f"{base}/api/method/{WEBHOOK_METHOD}?key={self.webhook_secret}"


@frappe.whitelist()
def regenerate_webhook_secret():
    """يعيد توليد السرّ ويحدّث الرابط. يستدعيها الزرّ في الواجهة."""
    doc = frappe.get_single("felix_waapi Configuration")
    doc.webhook_secret = frappe.generate_hash(length=32)
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"webhook_secret": doc.webhook_secret, "webhook_url": doc.webhook_url}

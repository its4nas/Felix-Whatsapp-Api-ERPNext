import frappe
from frappe import _
from frappe.email.doctype.notification.notification import Notification, get_context, json
import requests
from requests.adapters import HTTPAdapter
import os
import time
import random
from urllib.parse import unquote

try:
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover
    Retry = None


GW_HTTP_TIMEOUT = 30          # HTTP request timeout for Felix API.

# Anti-ban protection: random delay between messages.
GW_DELAY_MIN = 3.0            # Minimum delay between messages (in seconds).
GW_DELAY_MAX = 8.0            # Maximum delay between messages (in seconds).

# Daily limit per number (0 = disabled).
GW_DAILY_CAP = 0

GW_PDF_GENERATOR = "chrome"


def _gw_build_session():
    # Shared requests session with automatic retries.
    session = requests.Session()
    if Retry is not None:
        retry = Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["POST"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
    return session


class felix_waapiNotification(Notification):
    def validate(self):
        self.validate_for_whats_settings()
        super(felix_waapiNotification, self).validate()

    def validate_for_whats_settings(self):
        settings = frappe.get_doc("felix_waapi Configuration")
        # التحقق من إعدادات Felix API
        api_key = getattr(settings, "api_key", None) or getattr(settings, "token", None)
        api_url = getattr(settings, "server_url", None) or getattr(settings, "api_url", None)
        
        if self.enabled and self.channel == "felix_waapi":
            if not api_key or not api_url or not settings.instance_id:
                frappe.throw(_("يرجى إعداد بيانات الربط لبوابة الواتساب (Server URL, Instance ID, API Key)"))

    def send(self, doc):
        context = get_context(doc)
        context = {"doc": doc, "alert": self, "comments": None}
        if doc.get("_comments"):
            context["comments"] = json.loads(doc.get("_comments"))

        if self.is_standard:
            self.load_standard_properties(context)

        try:
            if self.channel == 'felix_waapi':
                self.send_whatsapp_msg(doc, context)
        except Exception:
            frappe.log_error(title='Failed to send notification', message=frappe.get_traceback())

        super(felix_waapiNotification, self).send(doc)

    def send_whatsapp_msg(self, doc, context):
        settings = frappe.get_doc("felix_waapi Configuration")
        recipients = self.get_receiver_list(doc, context)
        sent_numbers = []
        failed_numbers = []

        session = _gw_build_session()

        # توليد ملف الـ PDF لمرة واحدة قبل الدخول في الحلقة التكرارية
        shared_pdf_path = None
        if self.attach_print:
            shared_pdf_path = self.generate_pdf(doc)
            if not shared_pdf_path:
                frappe.msgprint(_("تعذر توليد ملف الـ PDF"), alert=True)

        try:
            for idx, receipt in enumerate(recipients):
                number = receipt
                if not number:
                    frappe.log_error("Recipient is empty or None", "Recipient Error")
                    continue

                if "{" in number:
                    number = frappe.render_template(receipt, context)

                message = frappe.render_template(self.message, context)
                phone_number = self.get_receiver_phone_number(number)

                # التحقق من الحد اليومي
                if GW_DAILY_CAP and not self._gw_within_daily_cap(settings):
                    frappe.msgprint(
                        _("تم الوصول إلى الحد اليومي للإرسال عبر واتساب."),
                        alert=True,
                    )
                    break

                # الإرسال عبر Felix API
                if self.attach_print:
                    if shared_pdf_path:
                        success = self.send_pdf_via_whatsapp(settings, phone_number, shared_pdf_path, doc.name, message, session=session)
                    else:
                        success = False
                else:
                    success = self.send_text_via_whatsapp(settings, phone_number, message, session=session)

                if success:
                    sent_numbers.append(phone_number)
                    self._gw_log_sent(doc, phone_number, message, success)
                    if GW_DAILY_CAP:
                        self._gw_incr_daily_count(settings)
                else:
                    failed_numbers.append(phone_number)

                # فاصل زمني عشوائي بين الرسائل للحماية
                if idx < len(recipients) - 1:
                    time.sleep(random.uniform(GW_DELAY_MIN, GW_DELAY_MAX))
        finally:
            if shared_pdf_path:
                self._gw_cleanup_temp(shared_pdf_path)
            session.close()

        if sent_numbers:
            frappe.msgprint(_("تم إرسال رسالة الواتساب إلى: {0}").format(", ".join(sent_numbers)))
        if failed_numbers:
            frappe.msgprint(
                _("فشل الإرسال إلى: {0}. راجع سجل الأخطاء.").format(", ".join(failed_numbers)),
                alert=True,
            )

    def _gw_log_sent(self, doc, phone_number, message, felix_waapi_id=None):
        try:
            frappe.get_doc({
                "doctype": "felix_waapi Messages Log",
                "to_number": phone_number,
                "message_body": message,
                "status": "sent",
                "reference_doctype": doc.doctype,
                "reference_name": doc.name,
                "felix_waapi_id": str(felix_waapi_id) if felix_waapi_id and felix_waapi_id is not True else None,
            }).insert(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "WhatsApp Log Insert Error")

    def _gw_daily_key(self, settings):
        return f"gw_daily_count:{settings.instance_id}:{frappe.utils.today()}"

    def _gw_within_daily_cap(self, settings):
        try:
            current = frappe.cache().get_value(self._gw_daily_key(settings)) or 0
            return int(current) < GW_DAILY_CAP
        except Exception:
            return True

    def _gw_incr_daily_count(self, settings):
        try:
            key = self._gw_daily_key(settings)
            current = int(frappe.cache().get_value(key) or 0) + 1
            frappe.cache().set_value(key, current, expires_in_sec=86400)
        except Exception:
            pass

    def generate_pdf(self, doc):
        try:
            print_format = self.print_format or None
            pdf_kwargs = dict(
                doctype=doc.doctype,
                name=doc.name,
                print_format=print_format,
                as_pdf=True,
                no_letterhead=0,
            )

            try:
                settings = frappe.get_cached_doc("felix_waapi Configuration")
                preferred = getattr(settings, "pdf_generator", None) or GW_PDF_GENERATOR
            except Exception:
                preferred = GW_PDF_GENERATOR

            generators = [preferred, "wkhtmltopdf" if preferred == "chrome" else "chrome"]

            last_err = None
            for gen in generators:
                try:
                    try:
                        pdf_content = frappe.get_print(pdf_generator=gen, **pdf_kwargs)
                    except TypeError:
                        pdf_content = frappe.get_print(**pdf_kwargs)
                    if pdf_content:
                        return self._gw_write_temp(doc, pdf_content)
                except Exception as e:
                    last_err = e
                    continue

            if last_err:
                raise last_err
            return None
        except Exception:
            frappe.log_error(frappe.get_traceback(), "PDF Generation Error")
            return None

    def _gw_write_temp(self, doc, pdf_content):
        file_name = f"{doc.name.replace('/', '-')}.pdf"
        temp_path = frappe.utils.get_site_path("private", "files", file_name)
        with open(temp_path, "wb") as f:
            f.write(pdf_content)
        return temp_path

    def _gw_cleanup_temp(self, file_path):
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "PDF Cleanup Error")

    # ================================================================
    # دالة إرسال الرسائل النصية المربوطة بـ Felix API
    # ================================================================
    def send_text_via_whatsapp(self, settings, phone_number, message, session=None):
        try:
            base_url = (getattr(settings, "server_url", None) or getattr(settings, "api_url", "http://127.0.0.1:3000")).rstrip('/')
            api_key = getattr(settings, "api_key", None) or getattr(settings, "token", "")
            instance_id = str(settings.instance_id).strip()

            endpoint = f"{base_url}/api/v1/messages/send-text"

            headers = {
                "X-Instance-Id": instance_id,
                "X-Api-Key": str(api_key).strip(),
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            payload = {
                "phone": phone_number,
                "message": message
            }

            http_client = session if session else requests
            resp = http_client.post(endpoint, json=payload, headers=headers, timeout=GW_HTTP_TIMEOUT)

            res_json = {}
            try:
                res_json = resp.json()
            except Exception:
                pass

            if resp.status_code != 200 or not res_json.get("status"):
                frappe.log_error(title="Felix API Send Error", message=f"Status {resp.status_code}: {resp.text}")
                return False

            frappe.logger().info(f"Text message sent successfully via Felix API to {phone_number}")
            return res_json.get("data", {}).get("message_uuid") or True

        except Exception as e:
            frappe.log_error(title="Felix API Connection Error", message=f"Failed to send text to {phone_number}: {str(e)}")
            return False

    # ================================================================
    # دالة إرسال الوسائط والمستندات (PDF) المربوطة بـ Felix API
    # ================================================================
    def send_pdf_via_whatsapp(self, settings, phone_number, file_path, doc_name, message, session=None):
        import shutil
        try:
            # 1. نسخ الملف إلى المجلد العام ليتاح برابط مباشر
            clean_doc_name = doc_name.replace('/', '-')
            file_name = f"{clean_doc_name}.pdf"
            public_file_path = frappe.utils.get_site_path("public", "files", file_name)

            if file_path != public_file_path and os.path.exists(file_path):
                shutil.copy(file_path, public_file_path)

            site_url = frappe.utils.get_url().rstrip('/')
            public_media_url = f"{site_url}/files/{file_name}"

            base_url = (getattr(settings, "server_url", None) or getattr(settings, "api_url", "http://127.0.0.1:8000")).rstrip('/')
            api_key = getattr(settings, "api_key", None) or getattr(settings, "token", "")
            instance_id = str(settings.instance_id).strip()

            endpoint = f"{base_url}/api/v1/messages/send-media"

            headers = {
                "X-Instance-Id": instance_id,
                "X-Api-Key": str(api_key).strip(),
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            payload = {
                "phone": phone_number,
                "media_url": public_media_url,
                "media_name": f"{clean_doc_name}.pdf",
                "caption": message if message else ""
            }

            http_client = session if session else requests
            resp = http_client.post(endpoint, json=payload, headers=headers, timeout=GW_HTTP_TIMEOUT)

            res_json = {}
            try:
                res_json = resp.json()
            except Exception:
                pass

            if resp.status_code != 200 or not res_json.get("status"):
                frappe.log_error(title="Felix API Media Error", message=f"Status: {resp.status_code}, Response: {resp.text}")
                return False

            frappe.logger().info(f"PDF sent via Felix API to {phone_number}: {public_media_url}")
            return res_json.get("data", {}).get("message_uuid") or True

        except Exception as e:
            frappe.log_error(title="Felix API Document Exception", message=f"Failed to send doc to {phone_number}: {str(e)}")
            return False

    def get_receiver_phone_number(self, number):
        if not number:
            frappe.log_error("No phone number provided", "Phone Number Error")
            return ''

        num = ''.join(c for c in str(number) if c.isdigit())

        if num.startswith('00'):
            num = num[2:]
        elif num.startswith('7') and len(num) == 9:
            num = '967' + num

        return num


@frappe.whitelist()
def get_all_doctypes():
    return list(set(
        d.document_type for d in frappe.get_all("Notification",
            filters={"channel": "felix_waapi"}, fields=["document_type"])))

@frappe.whitelist()
def get_whatsapp_notifications(doctype):
    return frappe.get_all("Notification",
        filters={"channel": "felix_waapi", "document_type": doctype},
        fields=["name", "subject"])

@frappe.whitelist()
def get_whatsapp_events(doctype):
    rows = frappe.get_all(
        "Notification",
        filters={"channel": "felix_waapi", "document_type": doctype, "enabled": 1},
        fields=["event"],
    )
    return list({(r.event or "").strip() for r in rows if r.event})


@frappe.whitelist()
def send_whatsapp_file(docname, doctype, notification_name):
    try:
        if not frappe.has_permission(doctype, "read", doc=docname):
            frappe.throw(_("ليس لديك صلاحية لعرض هذا المستند."))

        doc = frappe.get_doc(doctype, docname)
        notification_doc = frappe.get_doc("Notification", notification_name)
        notification = felix_waapiNotification(notification_doc.as_dict())

        if notification.channel != "felix_waapi":
            frappe.throw(_("قناة التنبيه غير صحيحة."))

        notification.send_whatsapp_msg(doc, {"doc": doc, "alert": notification})
        return _("تم إرسال رسالة الواتساب بنجاح.")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "WhatsApp Notification Error")
        frappe.throw(_("حدث خطأ أثناء الإرسال. يرجى مراجعة المسؤول."))

@frappe.whitelist()
def gw_already_sent(doctype, docname):
    count = frappe.db.count(
        "felix_waapi Messages Log",
        filters={
            "reference_doctype": doctype,
            "reference_name": docname,
            "status": "sent",
        },
    )
    return {"already_sent": count > 0, "count": count}
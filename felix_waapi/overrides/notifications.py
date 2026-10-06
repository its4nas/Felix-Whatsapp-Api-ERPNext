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


GW_HTTP_TIMEOUT = 30          # مهلة طلبات HTTP
GW_DELAY_MIN = 2.0            # الحد الأدنى للتأخير بين الرسائل
GW_DELAY_MAX = 5.0            # الحد الأقصى للتأخير بين الرسائل
GW_DAILY_CAP = 0              # الحد اليومي للرسائل (0 يعني معطل)
GW_PDF_GENERATOR = "chrome"


def _gw_build_session():
    """إنشاء Session مع دعم إعادة المحاولة الآلية"""
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
        if self.enabled and self.channel == "felix_waapi":
            if not settings.token:
                frappe.throw(_("Please configure Felix API Token in felix_waapi Configuration"))

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
            frappe.log_error(title='Failed to send WhatsApp notification', message=frappe.get_traceback())

        super(felix_waapiNotification, self).send(doc)

    def send_whatsapp_msg(self, doc, context):
        settings = frappe.get_doc("felix_waapi Configuration")
        recipients = self.get_receiver_list(doc, context)
        sent_numbers = []
        failed_numbers = []

        session = _gw_build_session()

        # توليد الـ PDF مرة واحدة ومشاركته لجميع المستلمين
        shared_pdf_path = None
        if self.attach_print:
            shared_pdf_path = self.generate_pdf(doc)
            if not shared_pdf_path:
                frappe.msgprint(_("Failed to generate PDF"), alert=True)

        try:
            for idx, receipt in enumerate(recipients):
                number = receipt
                if not number:
                    continue

                if "{" in number:
                    number = frappe.render_template(receipt, context)

                message = frappe.render_template(self.message, context)
                phone_number = self.get_receiver_phone_number(number)

                if not phone_number:
                    continue

                # فحص السقف اليومي إذا كان مفعلاً
                if GW_DAILY_CAP and not self._gw_within_daily_cap(settings):
                    frappe.msgprint(
                        _("Daily WhatsApp limit reached. Remaining messages skipped."),
                        alert=True,
                    )
                    break

                res_data = None
                if self.attach_print:
                    if shared_pdf_path:
                        success, res_data = self.send_pdf_via_whatsapp(
                            settings, phone_number, shared_pdf_path, doc.name, message, session=session
                        )
                    else:
                        success = False
                else:
                    success, res_data = self.send_text_via_whatsapp(
                        settings, phone_number, message, session=session
                    )

                if success:
                    sent_numbers.append(phone_number)
                    msg_id = (res_data.get("data") or {}).get("message_uuid") if isinstance(res_data, dict) else None
                    self._gw_log_sent(doc, phone_number, message, msg_id)
                    if GW_DAILY_CAP:
                        self._gw_incr_daily_count(settings)
                else:
                    failed_numbers.append(phone_number)

                # تأخير زمني لحماية الحساب من الحظر
                if idx < len(recipients) - 1:
                    time.sleep(random.uniform(GW_DELAY_MIN, GW_DELAY_MAX))
        finally:
            if shared_pdf_path:
                self._gw_cleanup_temp(shared_pdf_path)
            session.close()

        if sent_numbers:
            frappe.msgprint(
                _("WhatsApp sent to: {0}").format(", ".join(sent_numbers))
            )
        if failed_numbers:
            frappe.msgprint(
                _("Failed for: {0}. Check Error Log.").format(", ".join(failed_numbers)),
                alert=True,
            )

    # ================================================================
    # تكامل Felix API (Headers & URLs)
    # ================================================================

    def get_base_url(self, settings):
        url = getattr(settings, "api_url", None) or getattr(settings, "base_url", None)
        if not url:
            url = "http://felix_api.test"
        return url.rstrip("/")

    def get_headers(self, settings):
        # 1. محاولة جلب التوكن سواء كان حقلاً عادياً أو حقل كلمة مرور مشفر
        token = ""
        try:
            token = settings.get_password("token")
        except Exception:
            token = ""

        if not token:
            token = getattr(settings, "token", "") or getattr(settings, "api_key", "") or ""

        token = str(token).strip()

        # طباعة تشخيصية في Error Log للتأكد من القيمة التي تم جلبها
        if not token:
            frappe.log_error(
                title="Felix Token Missing",
                message=f"Settings doc fields: {settings.as_dict()}"
            )

        headers = {
            "Accept": "application/json",
            "User-Agent": "ERPNext-FelixAPI/1.0",
            "x-api-key": token,
            "X-API-KEY": token,
            "Authorization": f"Bearer {token}",
        }
        return headers

    def send_text_via_whatsapp(self, settings, phone_number, message, session=None):
        try:
            base_url = self.get_base_url(settings)
            # استخدام مسار Laravel الذي تم اختباره ونجح بـ curl
            text_url = f"{base_url}/api/v1/messages/send"

            headers = self.get_headers(settings)
            headers["Content-Type"] = "application/json"

            payload = {
                "phone": str(phone_number).strip(),
                "message": message
            }

            # نمرر session أو requests
            http_client = session if session else requests
            resp = http_client.post(text_url, json=payload, headers=headers, timeout=30)

            if resp.status_code not in [200, 201]:
                frappe.log_error(title="Felix API Send Error", message=f"Status {resp.status_code}: {resp.text}")
                return False, None

            frappe.logger().info(f"WhatsApp text sent to {phone_number}")
            return True, resp.json()

        except Exception as e:
            frappe.log_error(title="Felix API Connection Error", message=f"Failed to send text to {phone_number}: {str(e)}")
            return False, None

    def send_pdf_via_whatsapp(self, settings, phone_number, file_path, doc_name, message="", session=None):
        try:
            base_url = self.get_base_url(settings)
            media_url = f"{base_url}/api/v1/messages/send-media"
            
            headers = self.get_headers(settings)
            file_name = f"{doc_name}.pdf"
            http_client = session if session else requests

            with open(file_path, "rb") as f:
                files = {
                    'file': (file_name, f, 'application/pdf')
                }
                data = {
                    'phone': str(phone_number).strip(),
                    'caption': message[:1024] if message else "",
                    'filename': file_name
                }
                if hasattr(settings, "instance_id") and settings.instance_id:
                    data['instance_id'] = str(settings.instance_id).strip()

                resp = http_client.post(media_url, data=data, files=files, headers=headers, timeout=45)

            if resp.status_code not in [200, 201]:
                frappe.log_error(
                    title="Felix API Media Error", 
                    message=f"Status {resp.status_code}: {resp.text}"
                )
                return False, None

            return True, resp.json()
            
        except Exception as e:
            frappe.log_error(
                title="Felix API Document Error", 
                message=f"Failed to send PDF to {phone_number}: {str(e)}"
            )
            return False, None

    # ================================================================
    # إدارة السجلات والأمان
    # ================================================================

    def _gw_log_sent(self, doc, phone_number, message, message_uuid=None):
        try:
            frappe.get_doc({
                "doctype": "For Whats Messages Log",
                "to_number": phone_number,
                "message_body": message,
                "status": "sent",
                "reference_doctype": doc.doctype,
                "reference_name": doc.name,
                "ultramsg_id": str(message_uuid) if message_uuid else None,
            }).insert(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "WhatsApp Log Insert Error")

    def _gw_daily_key(self, settings):
        instance = getattr(settings, "instance_id", "default")
        return f"gw_daily_count:{instance}:{frappe.utils.today()}"

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

    # ================================================================
    # توليد ملفات PDF
    # ================================================================

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

    def get_receiver_phone_number(self, number):
        if not number:
            return ''

        num = ''.join(c for c in str(number) if c.isdigit())

        if num.startswith('00'):
            num = num[2:]
        elif num.startswith('7') and len(num) == 9:
            num = '967' + num

        return num


# ================================================================
# Whitelisted Methods
# ================================================================

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
            frappe.throw(_("You do not have permission."))

        doc = frappe.get_doc(doctype, docname)
        notification_doc = frappe.get_doc("Notification", notification_name)
        notification = felix_waapiNotification(notification_doc.as_dict())

        if notification.channel != "felix_waapi":
            frappe.throw(_("Invalid notification channel."))

        notification.send_whatsapp_msg(doc, {"doc": doc, "alert": notification})
        return _("WhatsApp message sent.")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "WhatsApp Notification Error")
        frappe.throw(_("An error occurred. Contact admin."))

@frappe.whitelist()
def gw_already_sent(doctype, docname):
    count = frappe.db.count(
        "For Whats Messages Log",
        filters={
            "reference_doctype": doctype,
            "reference_name": docname,
            "status": "sent",
        },
    )
    return {"already_sent": count > 0, "count": count}
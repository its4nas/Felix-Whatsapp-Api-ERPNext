app_name = "felix_waapi"
app_title = "felix_waapi"
app_publisher = "Anas Al-Dharei"
app_description = "Frappe App that helps users to use felix_waapi to link Whatsapp accounts with thier system"
app_email = "anasaldharei@gmail.com"
app_license = "mit"

fixtures = [
    {
        "dt": "Property Setter",
        "filters": [
            [
                "doc_type", "=", "Notification Recipient"
            ],
            [
                "field_name", "=", "receiver_by_document_field"
            ],
            [
                "property", "=", "fieldtype"
            ]
        ]
    },
    {
        "dt": "Property Setter",
        "filters": [
            [
                "name", "in", [
                    "Notification-channel-options",
                ]
            ]
        ]
    }
]

app_include_css = "/assets/felix_waapi/css/whatsapp_loader.css"
app_include_js = "/assets/felix_waapi/js/button_send_whatsapp.js"
override_doctype_class = {
    "Notification": "felix_waapi.overrides.notifications.felix_waapiNotification"
}
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/felix_waapi/css/felix_waapi.css"
# app_include_js = "/assets/felix_waapi/js/felix_waapi.js"

# include js, css files in header of web template
# web_include_css = "/assets/felix_waapi/css/felix_waapi.css"
# web_include_js = "/assets/felix_waapi/js/felix_waapi.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "felix_waapi/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "felix_waapi/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "felix_waapi.utils.jinja_methods",
# 	"filters": "felix_waapi.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "felix_waapi.install.before_install"
# after_install = "felix_waapi.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "felix_waapi.uninstall.before_uninstall"
# after_uninstall = "felix_waapi.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "felix_waapi.utils.before_app_install"
# after_app_install = "felix_waapi.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "felix_waapi.utils.before_app_uninstall"
# after_app_uninstall = "felix_waapi.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "felix_waapi.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"felix_waapi.tasks.all"
# 	],
# 	"daily": [
# 		"felix_waapi.tasks.daily"
# 	],
# 	"hourly": [
# 		"felix_waapi.tasks.hourly"
# 	],
# 	"weekly": [
# 		"felix_waapi.tasks.weekly"
# 	],
# 	"monthly": [
# 		"felix_waapi.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "felix_waapi.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "felix_waapi.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "felix_waapi.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["felix_waapi.utils.before_request"]
# after_request = ["felix_waapi.utils.after_request"]

# Job Events
# ----------
# before_job = ["felix_waapi.utils.before_job"]
# after_job = ["felix_waapi.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"felix_waapi.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


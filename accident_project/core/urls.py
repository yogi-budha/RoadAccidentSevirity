from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from records import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("login/", auth_views.LoginView.as_view(
        template_name="records/login.html"), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("entry/", views.accident_entry, name="entry"),
    path("records/", views.records_list, name="records_list"),
    path("alerts/", views.alerts_list, name="alerts"),
    path("alerts/read/", views.alerts_read_all, name="alerts_read"),
    path("analysis/", views.analysis, name="analysis"),
    path("map/", views.hotspot_map, name="hotspot_map"),
    path("risk/", views.risk_calculator, name="risk_calculator"),
    path("predict/", views.predict_severity, name="predict"),
    path("emergency/", views.emergency_lookup, name="emergency"),
    path("bulk/", views.bulk_upload, name="bulk_upload"),
    path("bulk/template/", views.download_template, name="download_template"),
    path("retrain/", views.retrain_model, name="retrain"),
]

    
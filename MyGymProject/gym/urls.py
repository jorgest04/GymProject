from django.urls import path

from . import views

app_name = "gym"

urlpatterns = [
    path("", views.home, name="home"),
    path("entrar/", views.vista_login, name="login"),
    path("salir/", views.vista_logout, name="logout"),
    path("admin-panel/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/asistencia/nueva/", views.admin_asistencia_nueva, name="admin_asistencia_nueva"),
    path("admin-panel/asistencias/", views.admin_asistencias_lista, name="admin_asistencias"),
    path(
        "admin-panel/asistencias/resumen/",
        views.admin_asistencias_por_alumno,
        name="admin_asistencias_resumen",
    ),
    path("admin-panel/plan/nuevo/", views.admin_plan_pago_nuevo, name="admin_plan_nuevo"),
    path("admin-panel/planes/", views.admin_planes_lista, name="admin_planes"),
    path("admin-panel/cuota/<int:pk>/pagar/", views.admin_cuota_marcar_pagada, name="admin_cuota_pagar"),
    path("admin-panel/alumno/<int:user_id>/evaluacion/", views.admin_evaluacion_alumno, name="admin_evaluacion_alumno"),
    path("admin-panel/alumno/<int:user_id>/editar/", views.admin_editar_alumno, name="admin_editar_alumno"),
    path("admin-panel/alumno/nuevo/", views.admin_crear_alumno, name="admin_crear_alumno"),
    path("mi-gimnasio/", views.alumno_portal, name="alumno_portal"),
    path("mi-gimnasio/perfil/", views.alumno_perfil, name="alumno_perfil"),
    path("mi-gimnasio/congelar/", views.alumno_congelar, name="alumno_congelar"),
    path("mi-gimnasio/descongelar/", views.alumno_descongelar, name="alumno_descongelar"),
]

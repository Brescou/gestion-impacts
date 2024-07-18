from django.urls import path
from netbox.views.generic import ObjectChangeLogView
from . import views, models

app_name = 'gestion_impacts'

urlpatterns = [
    path('impacts/', views.ImpactListView.as_view(), name='impact_list'),
    path('impacts/add/', views.ImpactEditView.as_view(), name='impact_add'),
    path('impacts/delete/', views.ImpactBulkDeleteView.as_view(), name='impact_bulk_delete'),
    path('impacts/<int:pk>/', views.ImpactView.as_view(), name='impact'),
    path('impacts/<int:pk>/edit/', views.ImpactEditView.as_view(), name='impact_edit'),
    path('impacts/edit/', views.ImpactBulkEditView.as_view(), name='impact_bulk_edit'),
    path('impacts/<int:pk>/delete/', views.ImpactDeleteView.as_view(), name='impact_delete'),
    path('impacts/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='impact_changelog',
         kwargs={'model': models.Impact}),
    path('impacts/import/', views.ImpactBulkImportView.as_view(), name='impact_import'),
]

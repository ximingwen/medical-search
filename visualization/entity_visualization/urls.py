"""entity_visualization URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from add_mark import views
from django.conf.urls import url

urlpatterns = [
    path(r'^admin/', admin.site.urls),
    url(r'^$',views.home,name='home'),
    url(r'^tree/',views.tree,name='tree'),
    url(r'^collocation_cui/',views.collocation_cui,name='collocation_cui'),
    url(r'^collocation_snomed/',views.collocation_snomed,name='collocation_snomed'),
    url(r'^snomed_hierarchy/',views.snomed_hierarchy,name='snomed_hierarchy'),
    url(r'^snomed_three_layer_tree/',views.snomed_three_layer_tree,name='snomed_hierarchy_three_layer_tree'),
    url(r'^snomed_four_layer_tree/',views.snomed_four_layer_tree,name='snomed_hierarchy_four_layer_tree'),
    url(r'^page/',views.paginator_view,name='page'),
    url(r'^frequent_itemset/',views.frequent_itemset,name='frequent_itemset'),
    url(r'^tf_idf/',views.tf_idf,name='tf_idf')

]

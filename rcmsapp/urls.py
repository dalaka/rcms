from django.urls import path, include
from rest_framework import routers

from rcmsapp.views import UserView, CompanyViews, TranxViews, ConfigViews, ItemViews, ReportViews

router = routers.DefaultRouter()
router.register('user',  UserView,'user')
router.register('company',  CompanyViews,'company')
router.register('tranx',  TranxViews,'tranx')
router.register('config',  ConfigViews,'config')
router.register('item',  ItemViews,'item')
router.register('report',  ReportViews,'report')

urlpatterns = [

    path('api/', include(router.urls)),

]
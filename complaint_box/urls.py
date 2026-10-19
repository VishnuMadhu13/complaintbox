"""complaint_box URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from . import views
from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.first),
    path('index', views.index),
    path('login', views.login),
    path('registeri', views.registeri),
    path('complaint1', views.complaint1),
    path('userregistration', views.userregistration),
    path('loginuser',views.loginuser),
    path('logout', views.logout),
    path('profileuser', views.profileuser),
    path('viewprofileuser', views.viewprofileuser),
    path('adminviewprofile', views.adminviewprofile),
    path('trainerviewprofile', views.trainerviewprofile),
    path('update/<int:id>', views.update, name='update'),
    path('update/updates/<int:id>', views.updates, name='updates'),
    path('sendcomplaint',views.sendcompaint),
    path('complaintview',views.complaintview),
    path('complaintviewall',views.complaintviewall),
    path('sendack', views.sendack),
    path('ackview',views.ackview),
    path('registerview',views.registerview),
    path('admindelete/<int:id>', views.admindelete, name='admindelete'),
    path('addfaculty',views.addfaculty),
    path('facultyview',views.facultyview),
    path('updatestatus/<int:id>', views.updatestatus, name='updatestatus'),
    path('updatestatus/statusupdate/<int:id>', views.statusupdate, name='statusupdate'),
    path('facultydelete/<int:id>', views.facultydelete, name='facultydelete'),
    path('ackadmin',views.ackadmin),
    path('ackadminviewall',views.ackadminviewall),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

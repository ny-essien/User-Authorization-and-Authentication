from django.urls import path
from . import views

urlpatterns = [

    path("", views.home, name = "home"),
    path("register/", views.registrationPage, name = "register"),
    path("login/", views.loginPage, name = "signin"),
    path("signout/", views.logoutRequest, name = "signout"),

    #CRUD OPREATION
    path("userslist/", views.userList, name="users-list"),
    path("deleteuser/<int:pk>/" , views.deleteUser, name ="delete-user"),
    path("updateuser/<int:pk>/" , views.updateProfile, name = "update"),

    #USER PROFILE
    path("profile/", views.viewProfile, name="profile"),

    #CHANGE PASSWORD
    path("profile/changepassword/", views.changePassword, name =  "change-password"),

    #SEARCH USERS
    path("search-user/", views.searchUser, name = "search-user"),

    #ACTIVATE ACCOUNT
    path('activate/<uid64>/<token>/', views.activate_account, name = 'activate'),
]
from rest_framework import permissions


class UserPermission(permissions.IsAuthenticated):
   pass

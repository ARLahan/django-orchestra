from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from orchestra.api import router, SetPasswordApiMixin
from orchestra.apps.accounts.api import AccountApiMixin

from .models import Database, DatabaseUser
from .serializers import DatabaseSerializer, DatabaseUserSerializer


class DatabaseViewSet(AccountApiMixin, viewsets.ModelViewSet):
    model = Database
    serializer_class = DatabaseSerializer
    filter_fields = ('name',)


class DatabaseUserViewSet(AccountApiMixin, SetPasswordApiMixin, viewsets.ModelViewSet):
    model = DatabaseUser
    serializer_class = DatabaseUserSerializer
    filter_fields = ('username',)


router.register(r'databases', DatabaseViewSet)
router.register(r'databaseusers', DatabaseUserViewSet)

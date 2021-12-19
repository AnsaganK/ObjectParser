from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from parsing.models import Query, Place, Tag
from api.serializers import QuerySerializer, PlaceSerializer, UserSerializer
from parsing.serializers import TagSerializer


class QueryAPI(APIView):
    def get(self, request, user_id, format=None):
        queries = Query.objects.all(user__id=user_id)
        tags = Tag.objects.filter(queries__in=queries).distinct()
        query_serializer_data = QuerySerializer(queries, many=True)
        tags_serializer_data = TagSerializer(tags, many=True)
        return Response({'queries': query_serializer_data, 'tags': tags_serializer_data})


class QueryDetailAPI(APIView):
    def get(self, request, pk, format=None):
        query = Query.objects.filter(pk=pk).first()
        if query:
            serializer = QuerySerializer(query)
            return Response(serializer.data)
        return Response({'message': 'Не найдено'}, status=status.HTTP_404_NOT_FOUND)


class PlaceAPI(APIView):
    def get(self, request, type_id, format=None):
        places = Place.objects.filter(type__id=type_id)
        serializer = PlaceSerializer(places, many=True)
        return Response(serializer.data)


class PlaceDetailAPI(APIView):
    authentication_classes = (JWTAuthentication,)
    def get(self, request, pk, format=None):
        place = Place.objects.filter(pk=pk).first()
        if place:
            serializer = QuerySerializer(place)
            return Response(serializer.data)
        return Response({'message': 'Не найдено'}, status=status.HTTP_404_NOT_FOUND)


class UserDetailApi(APIView):
    def get(self, request, format=None):
        if request.GET:
            username = request.GET.get('username')
            password = request.GET.get('password')
            user = User.objects.filter(username=username).first()
            if user:
                checked = check_password(password, user.password)
                if checked:
                    serializer = UserSerializer(user)
                    return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)



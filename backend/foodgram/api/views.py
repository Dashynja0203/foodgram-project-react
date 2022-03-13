from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.db import models
from django.http.response import HttpResponse

from djoser.views import UserViewSet as DjoserUserViewSet

from recipes.models import AmountIngredient, Ingredient, Recipe, Tag
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


from .mixins import AddDelViewMixin
from .paginators import PageNumberPaginatorModified
from .permissions import AdminOrReadOnly, AuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeSerializer,
                          RecipeShortSerializer, TagSerializer,
                          UserSubscribeSerializer)

User = get_user_model()

incorrect_layout = str.maketrans(
    'qwertyuiop[]asdfghjkl;\'zxcvbnm,./',
    'йцукенгшщзхъфывапролджэячсмитьбю.'
)


class UserViewSet(DjoserUserViewSet, AddDelViewMixin):
    pagination_class = PageNumberPaginatorModified
    add_serializer = UserSubscribeSerializer

    @action(methods=('get', 'post', 'delete',), detail=True)
    def subscribe(self, request, id):
        return self.add_del_obj(id, 'subscribe')

    @action(methods=('get',), detail=False)
    def subscriptions(self, request):
        user = self.request.user
        if user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        authors = user.subscribe.all()
        pages = self.paginate_queryset(authors)
        serializer = UserSubscribeSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrReadOnly,)

    def get_queryset(self):
        name = self.request.query_params.get('name')
        queryset = self.queryset
        if name:
            if name[0] == '%':
                name = unquote(name)
            else:
                name = name.translate(incorrect_layout)
            name = name.lower()
            stw_queryset = list(queryset.filter(name__startswith=name))
            cnt_queryset = queryset.filter(name__contains=name)
            stw_queryset.extend(
                [i for i in cnt_queryset if i not in stw_queryset]
            )
            queryset = stw_queryset
        return queryset


class RecipeViewSet(viewsets.ModelViewSet, AddDelViewMixin):
    queryset = Recipe.objects.select_related('author')
    serializer_class = RecipeSerializer
    permission_classes = (AuthorOrReadOnly,)
    pagination_class = PageNumberPaginatorModified
    add_serializer = RecipeShortSerializer

    def get_queryset(self):
        queryset = self.queryset

        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(
                tags__slug__in=tags).distinct()

        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author=author)

        user = self.request.user
        if user.is_anonymous:
            return queryset

        is_in_shopping = self.request.query_params.get('is_in_shopping_cart')
        if is_in_shopping in ('1', 'true',):
            queryset = queryset.filter(cart=user.id)
        elif is_in_shopping in ('0', 'false',):
            queryset = queryset.exclude(cart=user.id)

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited in ('1', 'true',):
            queryset = queryset.filter(favorite=user.id)
        if is_favorited in ('0', 'false',):
            queryset = queryset.exclude(favorite=user.id)

        return queryset

    @action(methods=('get', 'post', 'delete',), detail=True)
    def favorite(self, request, pk):
        return self.add_del_obj(pk, 'favorite')

    @action(methods=('get', 'post', 'delete',), detail=True)
    def shopping_cart(self, request, pk):
        return self.add_del_obj(pk, 'shopping_cart')

    @action(methods=('get',), detail=False)
    def download_shopping_cart(self, request):
        user = self.request.user
        if not user.carts.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ingredients = AmountIngredient.objects.filter(
            recipe__in=(user.carts.values('id'))
        ).values(
            ingredient=models.F('ingredients__name'),
            measure=models.F('ingredients__measurement_unit')
        ).annotate(amount=models.Sum('amount'))

        filename = f'{user.username}_shopping_list.txt'
        shopping_list = (
            f'Список покупок для:\n\n{user.first_name}\n\n'
        )
        for ing in ingredients:
            shopping_list += (
                f'{ing["ingredient"]}: {ing["amount"]} {ing["measure"]}\n'
            )

        response = HttpResponse(
            shopping_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

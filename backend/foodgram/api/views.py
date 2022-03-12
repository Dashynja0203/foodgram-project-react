from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (Favorite, Ingredient, IngredientRecipe,
                            PurchaseList, Recipe, Subscribe, Tag)

from .filter import RecipeFilter, SearchFilter
from .paginator import PageNumberPaginatorModified
from .permissions import AuthorOrReadOnly
from .serializers import (CreateRecipeSerializer, FavoriteSerializer,
                          IngredientSerializer, PurchaseListSerializer,
                          RecipeListSerializer, SubscribersSerializer,
                          SubscribeSerializer, TagSerializer)

User = get_user_model()


class UserViewSet(UserViewSet):
    pagination_class = PageNumberPaginatorModified
    add_serializer = SubscribeSerializer

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
        serializer = SubscribeSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = CreateRecipeSerializer
    permission_classes = [AuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filter_class = RecipeFilter
    queryset = Recipe.objects.all()

    pagination_class = PageNumberPaginatorModified

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeListSerializer
        return CreateRecipeSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny, ]
    filter_backends = [SearchFilter]
    search_fields = ['name', ]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


@api_view(['get'])
@permission_classes([IsAuthenticated])
def show_subscribs(request):
    user_obj = User.objects.filter(following__user=request.user)
    paginator = PageNumberPagination()
    paginator.page_size = 10
    result_page = paginator.paginate_queryset(user_obj, request)
    serializer = SubscribersSerializer(
        result_page,
        many=True,
        context={'current_user': request.user}
    )
    return paginator.get_paginated_response(serializer.data)


class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = request.user
        data = {
            'user': user.id,
            'author': user_id
        }
        serializer = SubscribeSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        user = request.user
        follow = get_object_or_404(
            Subscribe,
            user=user,
            author_id=user_id
        )
        follow.delete()
        return Response('Подписка удалена', status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, recipe_id):
        user = request.user.id
        data = {
            'user': user,
            'recipe': recipe_id
        }
        serializer = FavoriteSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        user = request.user
        favorite_recipe = get_object_or_404(
            Favorite,
            user=user,
            recipe__id=recipe_id
        )
        favorite_recipe.delete()
        return Response(
            'Рецепт удален из избранного',
            status.HTTP_204_NO_CONTENT
        )


class PurchaseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, recipe_id):
        user = request.user.id
        data = {
            'user': user,
            'recipe': recipe_id
        }
        serializer = PurchaseListSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        user = request.user
        purchace_list_recipe = get_object_or_404(
            PurchaseList,
            user=user,
            recipe__id=recipe_id
        )
        purchace_list_recipe.delete()
        return Response(
            'Рецепт удален из списка покупок',
            status.HTTP_204_NO_CONTENT
        )


class DownloadPurchaseList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recipes = request.user.purchases.all().values_list('recipe', flat=True)
        ingredients = IngredientRecipe.objects.filter(
            recipe__in=recipes).all().values_list('ingredient', flat=True)
        purchase_list = {}

        for ingredient in ingredients:
            name = ingredient.ingredient.name
            amount = ingredient.amount
            unit = ingredient.ingredient.measurement_unit
            if name not in purchase_list:
                purchase_list[name] = {
                    'amount': amount,
                    'unit': unit
                }
            else:
                purchase_list[name]['amount'] = (
                        purchase_list[name]['amount'] + amount
                )
        wishlist = []
        for item in purchase_list:
            wishlist.append(f'{item} ({purchase_list[item]["unit"]}) — '
                            f'{purchase_list[item]["amount"]} \n')
        wishlist.append('')
        wishlist.append('Хороших покупок!')
        response = HttpResponse(wishlist, 'Content-Type: application/pdf')
        response['Content-Disposition'] = 'attachment; filename="wishlist.pdf"'
        return response

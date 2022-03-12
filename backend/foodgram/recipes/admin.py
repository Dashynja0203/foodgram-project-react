from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientRecipe, PurchaseList,
                     Recipe, Subscribe, Tag)


class IngredientRecipeInLine(admin.TabularInline):
    model = IngredientRecipe
    extra = 1


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color',)
    search_fields = ('name', 'color',)
    list_filter = ('color',)


class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'recipe',)
    list_select_related = ('ingredient', 'recipe',)
    search_fields = ('recipe', 'ingredient',)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    list_select_related = ('user', 'recipe',)


class IngredientAdmin(admin.ModelAdmin):
    inlines = (IngredientRecipeInLine,)
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientRecipeInLine,)
    list_display = ('author', 'name')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-пусто-'

    def is_favorite(self, obj):
        return obj.favorites.count()


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientRecipe, IngredientRecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(PurchaseList)
admin.site.register(Subscribe)

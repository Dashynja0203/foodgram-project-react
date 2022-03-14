from recipes.models import AmountIngredient

from rest_framework.serializers import ValidationError


def calc_ingredients_amount(recipe, ingredients):
    for ingredient in ingredients:
        AmountIngredient.objects.get_or_create(
            recipe=recipe,
            ingredients=ingredient['ingredient'],
            amount=ingredient['amount']
        )


def check_value_validate(value, clas=None):
    if int(value) <= 0:
        raise ValidationError(
            'Вес ингредиента: Убедитесь, что это значение больше либо равно 1.'
        )
    if not str(value).isdecimal():
        raise ValidationError(
            f'{value} должен содержать цифру'
        )
    if clas:
        obj = clas.objects.filter(id=value)
        if not obj:
            raise ValidationError(
                f'{value} не существует'
            )
        return obj[0]

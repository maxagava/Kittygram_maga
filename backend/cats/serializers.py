import base64
import datetime as dt

import webcolors
from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import Achievement, AchievementCat, Cat


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class AchievementSerializer(serializers.ModelSerializer):
    achievement_name = serializers.CharField(source='name')

    class Meta:
        model = Achievement
        fields = ('id', 'achievement_name')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        print('IMAGE RAW TYPE:', type(data))
        if isinstance(data, str):
            print('IMAGE RAW START:', data[:80])

        if isinstance(data, str) and data.startswith('data:image'):
            format_data, imgstr = data.split(';base64,')
            ext = format_data.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')

        result = super().to_internal_value(data)
        print('IMAGE INTERNAL VALUE:', result)
        return result

    def to_representation(self, value):
        if not value:
            return None
        return value.url


class CatSerializer(serializers.ModelSerializer):
    achievements = AchievementSerializer(required=False, many=True)
    color = Hex2NameColor()
    age = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Cat
        fields = (
            'id',
            'name',
            'color',
            'birth_year',
            'achievements',
            'owner',
            'age',
            'image',
        )
        read_only_fields = ('owner',)

    def get_age(self, obj):
        return dt.datetime.now().year - obj.birth_year

    def to_internal_value(self, data):
        print('REQUEST DATA IN SERIALIZER:', data)
        return super().to_internal_value(data)

    def create(self, validated_data):
        print('VALIDATED DATA IN CREATE:', validated_data)
        achievements = validated_data.pop('achievements', [])
        cat = Cat.objects.create(**validated_data)

        for achievement in achievements:
            current_achievement, _ = Achievement.objects.get_or_create(**achievement)
            AchievementCat.objects.create(
                achievement=current_achievement,
                cat=cat
            )

        print('CREATED CAT IMAGE:', cat.image)
        return cat

    def update(self, instance, validated_data):
        print('VALIDATED DATA IN UPDATE:', validated_data)

        instance.name = validated_data.get('name', instance.name)
        instance.color = validated_data.get('color', instance.color)
        instance.birth_year = validated_data.get('birth_year', instance.birth_year)
        instance.image = validated_data.get('image', instance.image)

        if 'achievements' in validated_data:
            achievements_data = validated_data.pop('achievements')
            achievements_list = []
            for achievement in achievements_data:
                current_achievement, _ = Achievement.objects.get_or_create(**achievement)
                achievements_list.append(current_achievement)
            instance.achievements.set(achievements_list)

        instance.save()
        print('UPDATED CAT IMAGE:', instance.image)
        return instance

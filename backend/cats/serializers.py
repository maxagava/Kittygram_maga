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
        if isinstance(data, str) and data.startswith('data:image'):
            format_data, imgstr = data.split(';base64,')
            ext = format_data.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)


class CatSerializer(serializers.ModelSerializer):
    achievements = AchievementSerializer(required=False, many=True)
    color = Hex2NameColor()
    age = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    uploaded_image = Base64ImageField(write_only=True, required=False, allow_null=True)

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
            'uploaded_image',
        )
        read_only_fields = ('owner',)

    def get_age(self, obj):
        return dt.datetime.now().year - obj.birth_year

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def create(self, validated_data):
        uploaded_image = validated_data.pop('uploaded_image', None)
        achievements = validated_data.pop('achievements', [])

        cat = Cat.objects.create(**validated_data)

        if uploaded_image is not None:
            cat.image = uploaded_image
            cat.save()

        for achievement in achievements:
            current_achievement, _ = Achievement.objects.get_or_create(**achievement)
            AchievementCat.objects.create(
                achievement=current_achievement,
                cat=cat
            )

        return cat

    def update(self, instance, validated_data):
        uploaded_image = validated_data.pop('uploaded_image', None)
        achievements_data = validated_data.pop('achievements', None)

        instance.name = validated_data.get('name', instance.name)
        instance.color = validated_data.get('color', instance.color)
        instance.birth_year = validated_data.get('birth_year', instance.birth_year)

        if uploaded_image is not None:
            instance.image = uploaded_image

        if achievements_data is not None:
            achievements_list = []
            for achievement in achievements_data:
                current_achievement, _ = Achievement.objects.get_or_create(**achievement)
                achievements_list.append(current_achievement)
            instance.achievements.set(achievements_list)

        instance.save()
        return instance

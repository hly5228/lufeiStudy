from rest_framework import serializers
from api import models


class CourseSerializer(serializers.ModelSerializer):
    level = serializers.CharField(source='get_level_display')
    course_type = serializers.CharField(source='get_course_type_display')

    class Meta:
        model = models.Course
        fields = '__all__'


class CourseDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='course.name')
    img = serializers.CharField(source='course.course_img')
    level = serializers.CharField(source='course.get_level_display')

    # m2m
    recommends = serializers.SerializerMethodField()

    chapters = serializers.SerializerMethodField()

    class Meta:
        model = models.CourseDetail
        # fields = "__all__"
        fields = ["id", "name", "img", "level", "hours","course_slogan", "why_study", "recommends", "chapters"]
        depth = 1

    def get_recommends(self, obj):
        # obj是下面使用CourseDetailSerializer(instance=obj, many=False) 里的参数obj
        querysets = obj.recommend_course.all()
        return [{"id": course.id, "name": course.name} for course in querysets]

    def get_chapters(self, obj):
        # 反向查询两种方法
        # querysets = obj.course.coursechapter_set.all()
        querysets = obj.course.coursechapters.all()
        return [{"id": chapter.id, "chapter": chapter.chapter, "name": chapter.name} for chapter in querysets]
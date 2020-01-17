from rest_framework.viewsets import ViewSetMixin, GenericViewSet
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework import mixins

from api.serializers.news import *
from django.db.models import F, Q
from datetime import datetime

# class NewsView(ViewSetMixin, APIView):
#     def list(self, request, *args, **kwargs):
#         ret = {"code": 1000, "data": None}
#         try:
#             queryset = models.Article.objects.all().order_by("order")
#             ser = NewsSerializer(instance=queryset, many=True)
#             ret['data'] = ser.data
#         except Exception as e:
#             ret['code'] = 1001
#             ret['error'] = '获取数据失败!'
#         return Response(ret)
#
#     def retrieve(self, request, *args, **kwargs):
#         pass


class NewsView(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    queryset = models.Article.objects.all().order_by("order").reverse()
    serializer_class = NewsSerializer


class NewsAgreeView(ViewSetMixin, APIView):
    def post(self, request, *args, **kwargs):
        """
        点赞
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = {'code': 1000, 'data': None}
        try:
            pk = kwargs.get('pk')
            # 方式一：更新赞数
            # obj = models.Article.objects.filter(id=pk).first()
            # obj.agree_num = obj.agree_num + 1
            # obj.save()
            # 方式二：更新赞数
            # F，更新数据库字段
            # Q, 构造复杂条件
            from django.db.models import F,Q
            v = models.Article.objects.filter(id=pk).update(agree_num=F("agree_num") + 1)
            print(v)
            ret['data'] = v
        except Exception as e:
            ret['code'] = 1001
            ret['error'] = '点赞失败'
        return Response(ret)


class NewsCommentView(ViewSetMixin, APIView):
    def retrieve(self, request, *args, **kwargs):
        '''
        某文章的所有评论列表
        :param request:
        :param args:
        :param kwargs:
        :return:
        '''
        ret = {"code": 1000, "data": None}
        try:
            pk = kwargs["pk"]
            obj = models.Article.objects.get(id=pk)
            print("obj", obj)
            # queryset = models.Comment.objects.filter(content_type='article', object_id=pk)
            queryset = obj.comment_list.all()
            print("queryset", queryset)
            ser = CommentSerializer(instance=queryset, many=True)
            ret['data'] = ser.data
        except Exception as e:
            ret['code'] = 1001
            ret['error'] = '获取数据失败!'
        return Response(ret)

    def post(self, request, *args, **kwargs):
        '''
        评论，更新文章的评论数和插入评论表
        :param request:
        :param args:
        :param kwargs:
        :return:
        '''
        ret = {'code': 1000, 'data': None}
        try:
            pk = kwargs.get('pk')
            content = request.data.get('comment_content')
            p_node = request.data.get('p_node')
            account = request.data.get('account')
            disagree_number = request.data.get('disagree_number')
            agree_number = request.data.get('agree_number')

            obj = models.Article.objects.get(id=pk)
            # update只能用于queryset对象，前面要用filter不能用get
            v = models.Article.objects.filter(id=pk).update(comment_num=F("comment_num") + 1)
            ret['data'] = obj.comment_num
            print(obj.comment_num)

            models.Comment.objects.create(
                content_object=models.Article.objects.get(id=pk),
                p_node_id=p_node,
                content=content,
                account_id=account,
                disagree_number=disagree_number,
                agree_number=agree_number,
            )
        except Exception as e:
            ret['code'] = 1001
            ret['error'] = '评论失败'
        return Response(ret)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer,BrowsableAPIRenderer
from rest_framework.versioning import QueryParameterVersioning,URLPathVersioning,AcceptHeaderVersioning
from api import models
from rest_framework.viewsets import GenericViewSet
from api.serializers.course import CourseSerializer, CourseDetailSerializer


# class CourseView(APIView):
#     # 可以再settins里设置为全局的
#     # renderer_classes = [JSONRenderer,]
#
#     versioning_class = URLPathVersioning
#
#     def get(self, request, *args, **kwargs):
#
#         # self.dispatch
#         # print(request.version)
#         # ret = {
#         #     'code': 1000,
#         #     'data': [
#         #       {'id':1, 'title':"python全栈", 'imgSrc': "../src/assets/logo.png"},
#         #       {'id':2, 'title':"Linux运维", 'imgSrc': "../src/assets/logo.png"},
#         #       {'id':3, 'title':"金融分析", 'imgSrc': "../src/assets/logo.png"},
#         #       {'id':4, 'title':"爬虫", 'imgSrc': "../src/assets/logo.png"},
#         #     ]
#         # }
#         # return Response(ret)
#
#         ret = {"code": 1000, "data": None}
#         try:
#             queryset = models.Course.objects.all()
#             ser = CourseSerializer(instance=queryset, many=True)
#             ret['data'] = ser.data
#         except Exception as e:
#             ret['code'] = 1001
#             ret['error'] = '获取数据失败!'
#         return Response(ret)


class CourseView(GenericViewSet):
    # 可以再settins里设置为全局的
    # renderer_classes = [JSONRenderer,]

    def list(self, request, *args, **kwargs):
        '''
        课程列表接口
        :param request:
        :param args:
        :param kwargs:
        :return:
        '''
        ret = {"code": 1000, "data": None}
        try:
            queryset = models.Course.objects.all().order_by("course_type")
            ser = CourseSerializer(instance=queryset, many=True)
            ret['data'] = ser.data
        except Exception as e:
            ret['code'] = 1001
            ret['error'] = '获取数据失败!'
        return Response(ret)

    def retrieve(self,request, *args, **kwargs):
        '''
        课程详细接口
        :param request:
        :param args:
        :param kwargs:
        :return:
        '''
        ret = {"code": 1000, "data": None}
        try:
            pk = kwargs["pk"]
            obj = models.CourseDetail.objects.filter(course_id=pk).first()
            ser = CourseDetailSerializer(instance=obj, many=False)
            ret['data'] = ser.data
        except Exception as e:
            ret['code'] = 1001
            ret['error'] = '获取数据失败!'
        return Response(ret)

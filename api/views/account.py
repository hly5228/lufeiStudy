from rest_framework.views import APIView
from rest_framework.response import Response
from api import models
import uuid
from api.utils.auth import LuffyAuth


class AuthView(APIView):
    def post(self,request, *args, **kwargs):
        """用户登录"""
        print(request.data)
        ret = {"code":1000}
        user = request.data.get("user")
        pwd = request.data.get("pwd")
        user = models.Account.objects.filter(user=user, password=pwd).first()
        if not user:
            ret["code"] = 1001
            ret["error"] = "用户名或密码错误"
        else:
            uid = str(uuid.uuid4())
            models.UserAuthToken.objects.update_or_create(user=user, defaults={"token": uid})
            ret["user"] = {"nickname": user.nickname, "token": uid}
        return Response(ret)


class MicroView(APIView):
    authentication_classes = [LuffyAuth,]

    def get(self,request,*args,**kwargs):
        '''微职位页面获取，需要用户先登录'''
        # 认证放入认证组件
        # token = request.GET.get("token")  # 新request.GET === 旧request.GET
        # token2 = request.query_params.get("token")   # 新request.query_params === request._request.GET
        # user = models.UserToken.objects.filter(token=token).first()
        # if not user:
        #     return Response("认证失败")

        return Response("微职位")
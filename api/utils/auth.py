from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from api import models


# 使用认证组件
class LuffyAuth(BaseAuthentication):

    def authenticate(self, request):
        # 固定方法名
        # 假设将token放在请求头里（url里）
        token = request.query_params.get("token")  # 新request.query_params === request._request.GET
        user = models.UserAuthToken.objects.filter(token=token).first()
        if not user:
            raise AuthenticationFailed({'code': 1001, 'error': '认证失败'})

        # 返回两个值的元组放入request.user, request.auth
        return user.user.nickname, user


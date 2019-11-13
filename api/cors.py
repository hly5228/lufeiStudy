from django.utils.deprecation import MiddlewareMixin


class CORSMiddleware(MiddlewareMixin):

    def process_response(self,request,response):
        # 添加响应头

        # 允许的域名：  多个的话通过逗号隔开
        # response["Access-Control-Allow-Origin"] = "http://localhost:8080/,xxxx"
        response["Access-Control-Allow-Origin"] = "*"

        # 允许你携带Content-Type请求头
        if request.method == "OPTIONS":
            response['Access-Control-Allow-Headers'] = "Content-Type,K1"

        # 允许你发送DELETE,PUT
        response['Access-Control-Allow-Methods'] = "DELETE,PUT"

        return response




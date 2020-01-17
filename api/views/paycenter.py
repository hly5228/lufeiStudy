import json
import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from django_redis import get_redis_connection

from api import models
from django.conf import settings
from api.utils.auth import LuffyAuth
from api.utils.response import BaseResponse
from api.utils.exception import CourseNotExistInCar


class PayCenterView(APIView):
    """
    结算中心内容仍然保存在redis,因为数据往往是暂时的
    """
    authentication_classes = [LuffyAuth, ]
    conn = get_redis_connection("default")  # default为在settings里配置的redis下名“default"的配置 类里的全局变量，下面使用加self

    def post(self, request, *args, **kwargs):
        """
        购物车里勾选的几项提交，去结算，传courseids过来,
        放redis里:
        pay_center_userid:{
            courses:[id1,id2]
        }
        展示内容时，根据courseid去redis里shopping_car拿
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        # print("version",request.version)
        # print("auth:",request.auth.user)
        ret = BaseResponse()
        try:
            user_id = request.auth.user_id
            course_id_list = request.data.get("courseids")

            # 将结算单放置redis里
            # payid = int(time.time())
            pay_center_key = settings.PAY_CENTER_KEY % user_id
            for course_id in course_id_list:
                shopping_car_key = settings.SHOPPING_CAR_KEY % (user_id, course_id)
                # 判断是否存在redis(购物车里）
                if not self.conn.exists(shopping_car_key):
                    raise CourseNotExistInCar(settings.ERROR_CODE[5001])
            self.conn.hset(pay_center_key, 'courses', course_id_list)

        except CourseNotExistInCar as e:
            ret.code = 5001
            ret.error = e.msg
        except Exception as e:
            ret.code = 1001
            ret.error = "订单生成失败"
        return Response(ret.dict)

    def get(self, request, *args, **kwargs):
        """
        查看订单中的所有数据
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = BaseResponse()
        try:
            user_id = request.auth.user_id
            pay_center_key = settings.PAY_CENTER_KEY % user_id
            course_id_list = self.conn.hget(pay_center_key, 'courses')
            pay_center_list=[]
            for course_id in course_id_list:
                shopping_car_key = settings.SHOPPING_CAR_KEY %(user_id,course_id)
                policy_dict = json.loads(self.conn.hget(shopping_car_key, "policy").encode('utf-8'))
                select_policy = int(self.conn.hget(shopping_car_key, "default_policy").encode('utf-8'))
                course_dict={
                    "course_id":course_id,
                    "title": self.conn.hget(shopping_car_key, "title").encode('utf-8'),
                    "img": self.conn.hget(shopping_car_key, "img").encode('utf-8'),
                    "policy_name": policy_dict.get(select_policy).get("name"),
                    "policy_price": policy_dict.get(select_policy).get("price")
                }
                pay_center_list.append(course_dict)
                self.conn.rpush(pay_center_key,json.dumps(course_dict))
            ret.data = pay_center_list
        except Exception as e:
            ret.code = 1001
            ret.error = "购物车加载失败"
        return Response(ret.dict)

    def getCoupon_course(self,request):
        pass

    def getCoupon_all(self,request):
        pass


class PaymentView(APIView):
    authentication_classes = [LuffyAuth, ]
    conn = get_redis_connection("default")

    def post(self, request, *args, **kwargs):
        '''*args 必须存在，是因为总urls里放着版本号的参数'''
        ret = BaseResponse()
        try:
            # 1.根据课程id在redis获取课程（含价格）
            course_id_list = request.data.get("courseids")
            payment_dict = {}
            for course_id in course_id_list:
                shopping_car_key = settings.SHOPPING_CAR_KEY % (request.auth.user_id,course_id)
                # 判断是否存在redis(购物车里）
                if not self.conn.exists(shopping_car_key):
                    raise CourseNotExistInCar(settings.ERROR_CODE[5001])
                policy_dict = json.loads(self.conn.hget(shopping_car_key, "policy").encode('utf-8'))
                select_policy = int(self.conn.hget(shopping_car_key, "default_policy").encode('utf-8'))
                course_dict = {
                    "title": self.conn.hget(shopping_car_key, "title").encode('utf-8'),
                    "img": self.conn.hget(shopping_car_key, "img").encode('utf-8'),
                    "policy_name": policy_dict.get(select_policy).get("name"),
                    "policy_price": policy_dict.get(select_policy).get("price"),
                    "coupon": {},
                    "default_coupon": 0
                }
                # 上面可以用 course_dict.update(policy_dict[select_policy]) 把两个字典合起来

                payment_dict[int(course_id)] = course_dict

            # 2.获取用户所有可用优惠券
            # 筛选用户，未使用状态，在有效期
            ctime = datetime.date.today()  # 注意比日期的时候不要使用now带时间
            coupon_records_object = models.CouponRecord.objects.filter(account=request.auth.user, status=0,
                                                                       coupon__valid_begin_date__lte=ctime,
                                                                       coupon__valid_end_date__gte=ctime)
            coupons_object = [coupon_record.coupon for coupon_record in coupon_records_object]
            global_coupon_dict = dict()
            for coupon in coupons_object:
                if coupon.content_object:
                    course_id = coupon.content_object.id
                    if course_id in payment_dict:
                        payment_dict[course_id]["coupon"][coupon.id]={
                            "name": "%s(%s)" % (coupon.get_coupon_type_display(), coupon.name),
                            "coupon_type": coupon.coupon_type,
                            "money_equivalent_value": coupon.money_equivalent_value,
                            "off_percent": coupon.off_percent,
                            "minimum_consume": coupon.minimum_consume,
                        }
                else:
                    global_coupon_dict[coupon.id] = {
                            "name": "%s(%s)" % (coupon.get_coupon_type_display(), coupon.name),
                            "coupon_type": coupon.coupon_type,
                            "money_equivalent_value": coupon.money_equivalent_value,
                            "off_percent": coupon.off_percent,
                            "minimum_consume": coupon.minimum_consume,
                    }

            payment_dict.update(global_coupon_dict)

            ret.data = payment_dict
        except CourseNotExistInCar as e:
            ret.code = 5001
            ret.error = e.msg
        except Exception as e:
            ret.code = 1001
            ret.error = "订单生成失败"
        return Response(ret.dict)
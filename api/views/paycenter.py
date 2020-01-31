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


class PaymentView(APIView):
    authentication_classes = [LuffyAuth, ]
    conn = get_redis_connection("default")

    def post(self, request, *args, **kwargs):
        '''*args 必须存在，是因为总urls里放着版本号的参数'''
        """
            payment_dict = {
                '2': {
                    'course_id':2,
                    ...}
                '1': {
                    'course_id':2,
                    'title': '爬虫开发-专题', 
                    'img': '爬虫开发-专题.jpg', 
                    'policy_id': '2', 
                    'coupon': {
                        4: {'coupon_type': 0, 'coupon_display': '立减券', 'money_equivalent_value': 40}, 
                        6: {'coupon_type': 1, 'coupon_display': '满减券', 'money_equivalent_value': 60, 'minimum_consume': 100}
                    }, 
                    'default_coupon': 0, 
                    'period': 60, 
                    'period_display': '2个月', 
                    'price': 599.0}
            }
            global_coupon_dict = {
                'coupon': {
                    2: {'coupon_type': 1, 'coupon_display': '满减券', 'money_equivalent_value': 200, 'minimum_consume': 500}
                    3: {'coupon_type': 2, 'coupon_display': '通用券', 'money_equivalent_value': 20}
                }, 
                'default_coupon': 0
            }
        """
        """
            redis = {
                payment_1_2:{
                    'course_id':2,
                    ... 
                },
                payment_1_1:{
                    'course_id':1,
                    'title': '爬虫开发-专题', 
                    'img': '爬虫开发-专题.jpg', 
                    'policy_id': '2', 
                    'coupon': {
                        4: {'coupon_type': 0, 'coupon_display': '立减券', 'money_equivalent_value': 40}, 
                        6: {'coupon_type': 1, 'coupon_display': '满减券', 'money_equivalent_value': 60, 'minimum_consume': 100}
                    }, 
                    'default_coupon': 0, 
                    'period': 60, 
                    'period_display': '2个月', 
                    'price': 599.0}
                },
                payment_global_coupon_1:{
                    'coupon': {
                        2: {'coupon_type': 1, 'coupon_display': '满减券', 'money_equivalent_value': 200, 'minimum_consume': 500}
                    }, 
                    'default_coupon': 0
                }
            }
        """
        ret = BaseResponse()
        try:
            # 提交结算数据时，先清空该用户有的结算数据。结算是个很暂时的界面
            redis_key = settings.PAY_CENTER_KEY % (request.auth.user_id, '*')
            key_list = [payment_key for payment_key in self.conn.scan_iter(redis_key)]
            key_list.append(settings.PAY_CENTER_GLOBAL_COUPON_KEY % (request.auth.user_id, ))
            self.conn.delete(*key_list)

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
                    "course": int(course_id),
                    "title": self.conn.hget(shopping_car_key, "title").encode('utf-8'),
                    "img": self.conn.hget(shopping_car_key, "img").encode('utf-8'),
                    "policy_name": policy_dict.get(select_policy).get("name"),
                    "policy_price": policy_dict.get(select_policy).get("price"),
                    "coupon": {},
                    "default_coupon": 0
                }
                # 上面可以用 course_dict.update(policy_dict[select_policy]) 把两个字典合起来
                payment_dict[str(course_id)] = course_dict

            # 2.获取用户所有可用优惠券
            # 筛选用户，未使用状态，在有效期
            ctime = datetime.date.today()  # 注意比日期的时候不要使用now带时间
            coupon_records_object = models.CouponRecord.objects.filter(account=request.auth.user, status=0,
                                                                       coupon__valid_begin_date__lte=ctime,
                                                                       coupon__valid_end_date__gte=ctime)
            coupons_object = [coupon_record.coupon for coupon_record in coupon_records_object]
            global_coupon_dict = dict()
            for coupon in coupons_object:
                if coupon.object_id:
                    course_id = str(coupon.content_object.id)
                    if course_id in payment_dict:
                        payment_dict[course_id]["coupon"][coupon.id]={
                            "name": "%s(%s)" % (coupon.get_coupon_type_display(), coupon.name),
                            "coupon_type": coupon.coupon_type,
                            "money_equivalent_value": coupon.money_equivalent_value,
                            "off_percent": coupon.off_percent,
                            "minimum_consume": coupon.minimum_consume,
                        }

                else:
                    global_coupon_dict["coupon"][coupon.id] = {
                            "name": "%s(%s)" % (coupon.get_coupon_type_display(), coupon.name),
                            "coupon_type": coupon.coupon_type,
                            "money_equivalent_value": coupon.money_equivalent_value,
                            "off_percent": coupon.off_percent,
                            "minimum_consume": coupon.minimum_consume,
                    }
            global_coupon_dict["default_coupon"] = 0

            # 3. 放入redis
            for cid,cinfo in payment_dict.items():
                payment_key = settings.PAY_CENTER_KEY % (request.auth.user_id, cid)
                cinfo['coupon'] = json.dumps(cinfo['coupon'])  # 不使用json.dumps,redis会让其变为字符串，但取时无法通过json.loads变回字典使用
                self.conn.hmset(payment_key, cinfo)

            global_coupon_dict['coupon'] = json.dumps(global_coupon_dict['coupon'])
            coupon_key = settings.PAY_CENTER_GLOBAL_COUPON_KEY % (request.auth.user_id,)
            self.conn.hmset(coupon_key,global_coupon_dict)

            ret.data = payment_dict
        except CourseNotExistInCar as e:
            ret.code = 5001
            ret.error = e.msg
        except Exception as e:
            ret.code = 1001
            ret.error = "订单生成失败"
        return Response(ret.dict)

    def patch(self, request, *args, **kwargs):
        """只能更改选择的优惠券，如果是全局优惠券前端不传课程id"""
        ret = BaseResponse()
        try:
            course= request.data.get("courseid")
            course_id = int(course) if course else course  # course若为null不能int
            coupon_id = int(request.data.get("couponid"))

            global_coupon_key = settings.PAY_CENTER_GLOBAL_COUPON_KEY % (request.auth.user_id,)

            # 更新全局优惠券
            if not course_id:
                if coupon_id == 0:
                    # 不使用优惠券
                    self.conn.hset(global_coupon_key, 'default_coupon', coupon_id)
                    ret.data = "修改成功"
                    return Response(ret.dict)
                # 判断优惠券id是否合法
                coupon_dict = json.loads(self.conn.hget(global_coupon_key,'coupon').decode('utf-8'))
                if coupon_id not in coupon_dict:
                    ret.code = 2001
                    ret.data = "所选优惠价不合法"
                    return Response(ret.dict)

                self.conn.hset(global_coupon_key,'default_coupon',coupon_id)
                ret.data = "修改成功"
                return Response(ret.dict)

            # 更新课程优惠券
            payment_key = settings.PAY_CENTER_KEY % (request.auth.user_id, course_id)
            if coupon_id == 0:
                # 不使用优惠券
                self.conn.hset(payment_key, 'default_coupon', coupon_id)
                ret.data = "修改成功"
                return Response(ret.dict)
            # 判断优惠券id是否合法
            coupon_dict = json.loads(self.conn.hget(payment_key, 'coupon').decode('utf-8'))
            if coupon_id not in coupon_dict:
                ret.code = 2001
                ret.data = "所选优惠价不合法"
                return Response(ret.dict)

            self.conn.hset(payment_key, 'default_coupon', coupon_id)
            ret.data = "修改成功"

        except Exception as e:
            ret.code = 1001
            ret.data = "修改优惠券失败"
        return Response(ret.dict)

    def get(self, request, *args, **kwargs):
        """获取redis里payment_key,和global_coupon_key信息"""
        ret = BaseResponse()
        try:
            payment_keys = settings.PAY_CENTER_KEY % (request.auth.user_id, "*")
            global_coupon_key = settings.PAY_CENTER_GLOBAL_COUPON_KEY % (request.auth.user_id,)

            pay_center_list = []

            for key in self.conn.scan_iter(payment_keys):
                redis_dict = self.conn.hgetall(key)  # key,val都是btyes类型的字典
                pay_course_info = {}
                for k,v in redis_dict.item():
                    if k.decode('utf-8') == 'coupon':
                        pay_course_info[k.decode('utf-8')] = json.loads(v.decode('utf-8'))
                    else:
                        pay_course_info[k.decode('utf-8')] = v.decode('utf-8')
                pay_center_list.append(pay_course_info)

            global_coupon_dict = {
                "coupon": json.loads(self.conn.hget(global_coupon_key, 'coupon').decode('utf-8')),
                "default_coupon": self.conn.hget(global_coupon_key, 'default_coupon').decode('utf-8')
            }

            ret.data = {
                "pay_course_info": pay_center_list,
                "global_coupon": global_coupon_dict
            }
        except Exception as e:
            ret.code = 1001
            ret.data = "数据获取失败"
        return Response(ret.dict)


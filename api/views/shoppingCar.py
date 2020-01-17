from rest_framework.views import APIView
from rest_framework.response import Response
from api.utils.auth import LuffyAuth
from api.utils.response import BaseResponse
from django_redis import get_redis_connection
from django.core.exceptions import ObjectDoesNotExist
from api.utils.exception import PricePolicyInvalid
from django.conf import settings
from api import models
import json


class ShoppingCarView(APIView):
    '''
        购物车内容保存至redis
        保存结构1：操作会很复杂
        redis-->
        shopping_car:{
            用户ID:{
                课程1:{
                    title:'金融量化分析入门',
                    img:'/xx/xx/xx.png',
                    policy:{
                        10: {'name':'有效期1个月','price':599},
                        11: {'name':'有效期3个月','price':1599},
                        13: {'name':'有效期6个月','price':2599},
                        },
                    default_policy:12
                },

                课程2:{
                    title:'金融量化分析进阶',
                    img:'/xx/xx/xx.png',
                    policy:{……},
                    default_policy:13
                    }
            },
            用户ID:{...},
        }
    '''
    '''
    保存结构2：
        shopping_car_用户ID_课程ID:{
            title:'金融量化分析入门',
            img:'/xx/xx/xx.png',
            policy:{
                10: {'name':'有效期1个月','price':599},
                11: {'name':'有效期3个月','price':1599},
                13: {'name':'有效期6个月','price':2599},
            },
            default_policy:12
        },
        shopping_car_用户ID2_课程ID2:{
            title:'金融量化分析入门2',
            img:'/xx/xx/xx.png',
            policy:{..},
            default_policy:15
        },
    '''
    authentication_classes = [LuffyAuth, ]
    conn = get_redis_connection("default")  # default为在settings里配置的redis下名“default"的配置 类里的全局变量，下面使用加self

    # def create(self, request, *args, **kwargs):
    #     """购物车中添加一条数据(方式一）"""
    #     user_id = request.auth.id
    #     course_id = request.data.get('course_id')
    #     policy_id = request.data.get('course_id')
    #     course_obj = models.Course.objects.get(id=course_id)
    #
    #     conn = redis.Redis(host='', port=6379, password='')
    #     if not conn.hget('shopping_car', user_id):
    #         # 购物车第一条记录
    #         data_dict = {
    #             course_id:{
    #                 "title": course_obj.name,
    #                 "img": course_obj.course_img,
    #                 "policy": course_obj.price_policy.all(),
    #                 "default_policy_id": policy_id
    #             }
    #         }
    #         conn.hset('shopping_car', user_id, json.dumps(data_dict))
    #         return Response(data_dict)
    #
    #     # 购物车存在记录，再添加
    #     car = conn.hget('shopping_car', user_id)  # bytes字符串
    #     car_str = car.encode('utf-8')  # car_str = str(car,encoding='utf-8)
    #     car_dict = json.loads(car_str)
    #     car_dict[course_id]={
    #         "title": course_obj.name,
    #         "img": course_obj.course_img,
    #         "policy": course_obj.price_policy.all(),
    #         "default_policy_id": policy_id
    #     }
    #
    #     conn.hset('shopping_car', user_id, json.dumps(car_dict))
    #     return Response(car_dict)

    def post(self, request, *args, **kwargs):
        """购物车中添加一条数据(方式二）"""
        ret = BaseResponse()
        try:
            # print(request.data)
            # print(request.auth.id)
            user_id = request.auth.user_id
            course_id = int(request.data.get("courseid"))  # 保证前端传str传int都不报错
            policy_id = int(request.data.get("policyid"))

            # 获取课程信息
            course_obj = models.Course.objects.get(id=course_id)
            # ser = CourseSerializer(instance=course_obj, many=False)
            # car_dict = ser.data
            # car_dict["default_policy"] = policy_id
            # print(car_dict)
            # print(car_dict["course_price_policy"])
            # # 判断所给价格策略是否合理
            # flag = False
            # for policy_obj in car_dict["course_price_policy"]:
            #     if policy_id == policy_obj["id"]:
            #         flag = True
            # if not flag:
            #     raise PricePolicyInvalid('价格策略不合法')

            # 按设计格式处理课程信息
            policy_price_list = course_obj.price_policy.all()
            policy_price_dict = {}
            for item in policy_price_list:
                policy_price_dict[item.id]={
                    "valid_period_choice":item.valid_period,
                    "valid_period":item.get_valid_period_display(),
                    "price":item.price,
                }
            # 判断所给价格策略是否合理
            # policy_price_dict做成字典将id作为key的好处就是下面的判断一句话就可实现，否则需循环全部判断
            if policy_id not in policy_price_dict:
                raise PricePolicyInvalid('价格策略不合法')

            redis_key = settings.SHOPPING_CAR_KEY % (user_id, course_id)
            car_dict = {
                "title": course_obj.name,
                "img": course_obj.course_img,
                "policy": json.dumps(policy_price_dict),
                "default_policy_id": policy_id
            }

            self.conn.hmset(redis_key, car_dict)
            # print(conn.keys())
            ret.data = "购物车添加成功"

        except PricePolicyInvalid as e:
            ret.code = 3001
            ret.error = e.msg
        except ObjectDoesNotExist as e:
            ret.code = 2001
            ret.error = "课程不存在"
        except Exception as e:
            ret.code = 1001
            ret.error = "购物车添加失败"
        return Response(ret.dict)

    def delete(self, request, *args, **kwargs):
        """
        删除购物车中的数据,可全选删除，传递删除课程id的列表
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = BaseResponse()
        try:
            course_id_list = request.data.get("courseids")
            # key_list = []
            # for course_id in course_id_list:
            #     key = settings.SHOPPING_CAR_KEY % (request.auth.user_id, course_id)
            #     key_list.append(key)
            # 上面的可以写成下面一行
            key_list = [settings.SHOPPING_CAR_KEY % (request.auth.user_id, course_id) for course_id in course_id_list]

            self.conn.delete(*key_list)
            ret.data = "购物车删除成功"
        except Exception as e:
            ret.code = 1001
            ret.error = "删除失败"
        return Response(ret.dict)

    def patch(self, request, *args, **kwargs):
        """
        更新价格策略,购买课程特殊性购物车没有数量，更新只会更新价格策略，在购物车里一门课只能选一个价格策略
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = BaseResponse()
        try:
            course_id = int(request.data.get("courseid"))
            policy_id = str(request.data.get("policyid"))
            redis_key = settings.SHOPPING_CAR_KEY % (request.auth.user_id, course_id)

            # 判断购物车中是否有所给课程
            if not self.conn.exists(redis_key):
                ret.code = 2001
                ret.error = "购物车中不存在此课程"
                return Response(ret.dict)  # 这里同样可使用exception

            # 判断所给价格策略是否是该课程可用策略
            # b'{
            #     "10": {'name': '有效期1个月', 'price': 599},
            #     "11": {'name': '有效期3个月', 'price': 1599},
            #     "13": {'name': '有效期6个月', 'price': 2599},
            # }, bytes-->str-->dict, 且dict里的key类型是str
            policy_dict = json.loads(str(self.conn.hget(redis_key, "policy"),encoding='utf-8'))
            if policy_id not in policy_dict:
                ret.code = 3001
                ret.error = "价格策略不合法"
                return Response(ret.dict)

            # 所传数据无误，修改
            self.conn.hset(redis_key, "default_policy_id", policy_id)
            ret.data = "购物车修改成功"
        except Exception as e:
            ret.code = 1001
            ret.error = "购物车修改失败"
        return Response(ret.dict)

    def get(self, request, *args, **kwargs):
        """
        查看自己购物车中的所有数据
        课程ID:{
            title:'金融量化分析入门',
            img:'/xx/xx/xx.png',
            policy:{
                10: {'name':'有效期1个月','price':599},
                11: {'name':'有效期3个月','price':1599},
                13: {'name':'有效期6个月','price':2599},
            },
            default_policy:12
        },...
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = BaseResponse()
        try:
            user_id = request.auth.user_id
            redis_key = settings.SHOPPING_CAR_KEY % (user_id, "*")
            # self.conn.keys(redis_key)
            shopping_car_dict={}
            for item in self.conn.scan_iter(redis_key):
                li = item.rsplit('_', 1)
                shopping_car_dict[li[1]]={
                    "title":self.conn.hget(item, "title").encode('utf-8'),
                    "img":self.conn.hget(item, "img").encode('utf-8'),
                    "default_policy":self.conn.hget(item, "default_policy").encode('utf-8'),
                    "policy":json.loads(self.conn.hget(item, "policy").encode('utf-8'))
                }
            ret.data = shopping_car_dict
        except Exception as e:
            ret.code = 1001
            ret.error = "购物车加载失败"
        return Response(ret.dict)
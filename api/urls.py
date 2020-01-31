from django.conf.urls import url,include

from api.views import course, account, news, shoppingCar, paycenter, order
urlpatterns = [

    url(r'^course/$', course.CourseView.as_view({'get': 'list'})),
    url(r'^coursedetail/(?P<pk>\d+)/$', course.CourseView.as_view({'get': 'retrieve'})),

    url(r'^auth/$', account.AuthView.as_view()),
    url(r'^micro/$', account.MicroView.as_view()),

    url(r'^news/$', news.NewsView.as_view({'get': 'list'})),
    url(r'^news/(?P<pk>\d+)/$', news.NewsView.as_view({'get': 'retrieve'})),

    url(r'^news/agree/(?P<pk>\d+)/$', news.NewsAgreeView.as_view({'post': 'post'})),
    url(r'^news/comment/(?P<pk>\d+)/$', news.NewsCommentView.as_view({'get': 'retrieve', 'post': 'post'})),

    url(r'^shoppingcar/$', shoppingCar.ShoppingCarView.as_view()),  # 不使用多条url对应时，没必要继承ViewSetMixin，直接通过请求方式对应方法
    url(r'^paycenter/$', paycenter.PaymentView.as_view()),
    url(r'^order/$', order.OrderViewSet.as_view()),
]

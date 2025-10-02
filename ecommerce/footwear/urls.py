
from django.contrib import admin
from django.urls import path
from .import views

urlpatterns = [
    path('', views.index, name='index'),
    path('wishlist', views.wishlist, name='wishlist'),
    path('add_to_wishlist/<int:product_id>', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove_from_wishlist/<int:item_id>', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart_minus/<int:item_id>/', views.cart_minus, name='cart_minus'),
    path('cart_plus/<int:item_id>/', views.cart_plus, name='cart_plus'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout', views.checkout, name='checkout'),  
    path('save_addresses/', views.save_addresses, name='save_addresses'), 
    path('order_complete/', views.order_complete, name='order_complete'),
    path('orders', views.orders, name='orders'),
    path('about/', views.about, name='about'),
    path('support', views.support, name='support'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('contact', views.contact, name='contact'),
    path('men/', views.men, name='men'),
    path('men/<int:id>', views.men, name='men'),
    path('order_complete', views.order_complete, name='order_complete'),
    path('product_details/<int:id>', views.product_detail, name='product_details'),
    path('submit_review/<int:id>', views.submit_review, name='submit_review'),
    path('women', views.women, name='women'),
    path('women/<int:id>', views.women, name='women'),
    path('remove_coupon', views.remove_coupon, name='remove_coupon'),
    path('login/', views.login, name='login'),
    path('register', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    path('forget_password/', views.forget_password, name='forget_password'),
    path('razorpay_payment/', views.razorpay_payment, name='razorpay_payment'),
]

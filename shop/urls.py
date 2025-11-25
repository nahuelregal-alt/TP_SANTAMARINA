from django.urls import path
from . import views

urlpatterns = [
    # Productos
    path('', views.product_list, name='product_list'),
    path('producto/<int:product_id>/', views.product_detail, name='product_detail'),
    path('agregar-producto/', views.create_product, name='create_product'),
    
    # Carrito
    path('carrito/', views.cart_view, name='cart_view'),
    path('carrito/agregar/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('carrito/actualizar/<int:product_id>/', views.update_cart, name='update_cart'),
    path('carrito/eliminar/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('carrito/vaciar/', views.clear_cart, name='clear_cart'),
    path('carrito/aplicar-cupon/', views.apply_coupon, name='apply_coupon'),
    path('carrito/remover-cupon/', views.remove_coupon, name='remove_coupon'),
    
    # Usuarios
    path('registro/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.profile_view, name='profile'),
    path('mis-compras/', views.order_history, name='order_history'),
    
    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    
    # Notificaciones
    path('notificaciones/', views.notifications_view, name='notifications'),
    path('notificaciones/leer/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notificaciones/leer-todas/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notificaciones/count/', views.get_unread_count, name='get_unread_count'),
    
    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('orden/<int:order_id>/confirmacion/', views.order_confirmation, name='order_confirmation'),
    path('orden/<int:order_id>/pdf/', views.export_order_pdf, name='export_order_pdf'),
    
    # MercadoPago
    path('pago/<int:order_id>/', views.mercadopago_checkout, name='mercadopago_checkout'),
    path('pago/<int:order_id>/exito/', views.mercadopago_success, name='mercadopago_success'),
    path('pago/<int:order_id>/error/', views.mercadopago_failure, name='mercadopago_failure'),
    
    # Admin Dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
]

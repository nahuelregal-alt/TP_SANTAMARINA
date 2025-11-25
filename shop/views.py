from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.template.loader import get_template
from .models import Product, Category, Order, OrderItem, Profile, Review, Wishlist, Coupon, Notification
from .forms import ProductForm, RegisterForm, ProfileForm, CheckoutForm, ReviewForm
import logging
import json

logger = logging.getLogger(__name__)

# ===== PRODUCTOS =====

def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    # Wishlist del usuario
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(request.user.wishlists.values_list('product_id', flat=True))
    
    return render(request, 'shop/product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'search': search or '',
        'wishlist_ids': wishlist_ids,
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()
    user_review = None
    can_review = False
    in_wishlist = False
    
    if request.user.is_authenticated:
        user_review = Review.objects.filter(product=product, user=request.user).first()
        can_review = not user_review
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    
    if request.method == 'POST' and request.user.is_authenticated and can_review:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, '¡Gracias por tu review!')
            return redirect('product_detail', product_id=product_id)
    else:
        form = ReviewForm()
    
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form,
        'user_review': user_review,
        'can_review': can_review,
        'in_wishlist': in_wishlist,
    })

def create_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'shop/create_product.html', {"form": form})

# ===== CARRITO =====

def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    quantity = int(request.POST.get('quantity', 1))
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    request.session['cart'] = cart
    messages.success(request, 'Producto agregado al carrito')
    return redirect('product_list')

def cart_view(request):
    cart = request.session.get('cart', {})
    coupon_code = request.session.get('coupon_code')
    items = []
    subtotal = 0
    
    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        item_subtotal = product.price * qty
        subtotal += item_subtotal
        items.append({'product': product, 'quantity': qty, 'subtotal': item_subtotal})
    
    # Aplicar cupón si existe
    discount = 0
    coupon = None
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_valid() and subtotal >= coupon.min_purchase:
                discount = coupon.calculate_discount(subtotal)
        except Coupon.DoesNotExist:
            pass
    
    total = subtotal - discount
    
    return render(request, 'shop/cart.html', {
        'items': items,
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'coupon': coupon,
    })

def update_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart[str(product_id)] = quantity
        else:
            cart.pop(str(product_id), None)
        request.session['cart'] = cart
    return redirect('cart_view')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    messages.success(request, 'Producto eliminado del carrito')
    return redirect('cart_view')

def clear_cart(request):
    request.session['cart'] = {}
    request.session.pop('coupon_code', None)
    messages.success(request, 'Carrito vaciado')
    return redirect('cart_view')

@require_POST
def apply_coupon(request):
    code = request.POST.get('coupon_code', '').strip().upper()
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.error(request, 'Tu carrito está vacío')
        return redirect('cart_view')
    
    try:
        coupon = Coupon.objects.get(code=code)
        if coupon.is_valid():
            request.session['coupon_code'] = code
            messages.success(request, f'¡Cupón "{code}" aplicado!')
        else:
            messages.error(request, 'Este cupón no es válido o ha expirado')
    except Coupon.DoesNotExist:
        messages.error(request, 'Cupón no encontrado')
    
    return redirect('cart_view')

def remove_coupon(request):
    request.session.pop('coupon_code', None)
    messages.success(request, 'Cupón removido')
    return redirect('cart_view')

# ===== USUARIOS =====

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            # Notificación de bienvenida
            Notification.objects.create(
                user=user,
                notification_type='system',
                title='¡Bienvenido!',
                message='Gracias por registrarte en nuestra tienda. ¡Esperamos que disfrutes tu experiencia!'
            )
            login(request, user)
            messages.success(request, '¡Registro exitoso!')
            return redirect('product_list')
    else:
        form = RegisterForm()
    return render(request, 'shop/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.username}!')
            return redirect('product_list')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    return render(request, 'shop/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Sesión cerrada')
    return redirect('product_list')

@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.email = form.cleaned_data.get('email', '')
            request.user.save()
            messages.success(request, 'Perfil actualizado')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })
    
    return render(request, 'shop/profile.html', {'form': form})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_history.html', {'orders': orders})

# ===== WISHLIST =====

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'shop/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        wishlist_item.delete()
        messages.success(request, 'Producto eliminado de tu lista de deseos')
    else:
        messages.success(request, 'Producto agregado a tu lista de deseos')
    
    # Si es AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'added': created})
    
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

# ===== NOTIFICACIONES =====

@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()[:20]
    return render(request, 'shop/notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('notifications')

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(read=False).update(read=True)
    messages.success(request, 'Todas las notificaciones marcadas como leídas')
    return redirect('notifications')

@login_required
def get_unread_count(request):
    count = request.user.notifications.filter(read=False).count()
    return JsonResponse({'count': count})

# ===== CHECKOUT =====

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Tu carrito está vacío')
        return redirect('cart_view')
    
    items = []
    subtotal = 0
    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        item_subtotal = product.price * qty
        subtotal += item_subtotal
        items.append({'product': product, 'quantity': qty, 'subtotal': item_subtotal})
    
    # Cupón
    coupon_code = request.session.get('coupon_code')
    discount = 0
    coupon = None
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_valid() and subtotal >= coupon.min_purchase:
                discount = coupon.calculate_discount(subtotal)
        except Coupon.DoesNotExist:
            pass
    
    total = subtotal - discount
    
    profile, _ = Profile.objects.get_or_create(user=request.user)
    initial_data = {
        'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        'address': profile.address,
        'city': profile.city,
        'phone': profile.phone,
    }
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            
            # Crear la orden
            order = Order.objects.create(
                user=request.user,
                full_name=form.cleaned_data['full_name'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                phone=form.cleaned_data['phone'],
                payment_method=payment_method,
                coupon=coupon,
                discount=discount,
                subtotal=subtotal,
                total=total
            )
            
            for pid, qty in cart.items():
                product = get_object_or_404(Product, id=pid)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price=product.price
                )
            
            # Incrementar uso de cupón
            if coupon:
                coupon.times_used += 1
                coupon.save()
            
            # Si es MercadoPago, redirigir a pago
            if payment_method == 'mercadopago':
                return redirect('mercadopago_checkout', order_id=order.id)
            
            # Marcar como confirmado para otros métodos
            order.status = 'confirmed'
            order.save()
            
            # Notificación
            Notification.objects.create(
                user=request.user,
                notification_type='order',
                title=f'Orden #{order.id} confirmada',
                message=f'Tu orden por ${order.total} ha sido confirmada. ¡Gracias por tu compra!'
            )
            
            # Simular email
            logger.info(f"📧 EMAIL: Orden #{order.id} confirmada para {request.user.email}")
            
            # Limpiar carrito y cupón
            request.session['cart'] = {}
            request.session.pop('coupon_code', None)
            
            return redirect('order_confirmation', order_id=order.id)
    else:
        form = CheckoutForm(initial=initial_data)
    
    return render(request, 'shop/checkout.html', {
        'form': form,
        'items': items,
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'coupon': coupon,
    })

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_confirmation.html', {
        'order': order,
        'email_sent': True
    })

# ===== MERCADOPAGO =====

@login_required
def mercadopago_checkout(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Simulación de MercadoPago - En producción usar el SDK real
    # pip install mercadopago
    # import mercadopago
    # sdk = mercadopago.SDK("ACCESS_TOKEN")
    
    # Simular creación de preferencia
    preference_id = f"MP-{order.id}-{timezone.now().timestamp()}"
    order.mp_preference_id = preference_id
    order.save()
    
    return render(request, 'shop/mercadopago_checkout.html', {
        'order': order,
        'preference_id': preference_id,
    })

@login_required
def mercadopago_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Simular pago exitoso
    order.status = 'paid'
    order.mp_payment_id = f"PAY-{timezone.now().timestamp()}"
    order.save()
    
    # Notificación
    Notification.objects.create(
        user=request.user,
        notification_type='order',
        title=f'Pago recibido - Orden #{order.id}',
        message=f'Tu pago de ${order.total} fue procesado exitosamente.'
    )
    
    # Limpiar carrito
    request.session['cart'] = {}
    request.session.pop('coupon_code', None)
    
    messages.success(request, '¡Pago procesado exitosamente!')
    return redirect('order_confirmation', order_id=order.id)

@login_required
def mercadopago_failure(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.status = 'cancelled'
    order.save()
    messages.error(request, 'El pago fue rechazado. Intenta nuevamente.')
    return redirect('cart_view')

# ===== EXPORTAR PDF =====

@login_required
def export_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Generar HTML para el PDF
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Orden #{order.id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; }}
            .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px; }}
            .header h1 {{ margin: 0; color: #e94560; }}
            .info {{ margin-bottom: 20px; }}
            .info p {{ margin: 5px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background: #f5f5f5; }}
            .total {{ text-align: right; font-size: 1.3em; margin-top: 20px; }}
            .footer {{ margin-top: 40px; text-align: center; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>👟 Tienda de Zapatillas</h1>
            <h2>Orden #{order.id}</h2>
        </div>
        
        <div class="info">
            <p><strong>Fecha:</strong> {order.created_at.strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Cliente:</strong> {order.full_name}</p>
            <p><strong>Dirección:</strong> {order.address}, {order.city}</p>
            <p><strong>Teléfono:</strong> {order.phone}</p>
            <p><strong>Estado:</strong> {order.get_status_display()}</p>
            <p><strong>Método de pago:</strong> {order.get_payment_method_display()}</p>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Producto</th>
                    <th>Cantidad</th>
                    <th>Precio Unit.</th>
                    <th>Subtotal</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for item in order.items.all():
        html_content += f"""
                <tr>
                    <td>{item.product.name}</td>
                    <td>{item.quantity}</td>
                    <td>${item.price}</td>
                    <td>${item.subtotal}</td>
                </tr>
        """
    
    html_content += f"""
            </tbody>
        </table>
        
        <div class="total">
            <p>Subtotal: ${order.subtotal}</p>
            {"<p>Descuento: -$" + str(order.discount) + "</p>" if order.discount > 0 else ""}
            <p><strong>Total: ${order.total}</strong></p>
        </div>
        
        <div class="footer">
            <p>Gracias por tu compra!</p>
        </div>
    </body>
    </html>
    """
    
    # Devolver como HTML descargable (para PDF real, usar weasyprint o xhtml2pdf)
    response = HttpResponse(html_content, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="orden_{order.id}.html"'
    return response

# ===== ADMIN DASHBOARD =====

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, 'No tenés permisos para acceder a esta página')
        return redirect('product_list')
    
    # Estadísticas
    today = timezone.now().date()
    
    total_orders = Order.objects.count()
    orders_today = Order.objects.filter(created_at__date=today).count()
    total_revenue = Order.objects.filter(status__in=['paid', 'confirmed', 'shipped', 'delivered']).aggregate(Sum('total'))['total__sum'] or 0
    revenue_today = Order.objects.filter(created_at__date=today, status__in=['paid', 'confirmed', 'shipped', 'delivered']).aggregate(Sum('total'))['total__sum'] or 0
    
    total_products = Product.objects.count()
    total_users = Profile.objects.count()
    
    # Órdenes recientes
    recent_orders = Order.objects.order_by('-created_at')[:10]
    
    # Productos más vendidos
    top_products = OrderItem.objects.values('product__name').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]
    
    # Órdenes por estado
    orders_by_status = Order.objects.values('status').annotate(count=Count('id'))
    
    return render(request, 'shop/admin_dashboard.html', {
        'total_orders': total_orders,
        'orders_today': orders_today,
        'total_revenue': total_revenue,
        'revenue_today': revenue_today,
        'total_products': total_products,
        'total_users': total_users,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'orders_by_status': orders_by_status,
    })

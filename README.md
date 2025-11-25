# TP_SANTAMARINA
TP DE E-COMMERCE[readme_tienda_django.md](https://github.com/user-attachments/files/23757131/readme_tienda_django.md)
# 🛒 Tienda de Zapatillas – Proyecto Django

Este documento explica **paso a paso** cómo instalar, configurar y ejecutar el proyecto Django de carrito de compras basado en zapatillas deportivas.

---

# ✅ 1. Requisitos previos
- Python 3.8+ instalado
- PowerShell o terminal
- Editor (VS Code recomendado)

Verificar Python:
```
python --version
```

---

# ✅ 2. Crear carpeta y entorno virtual
```
mkdir TIENDA
cd TIENDA
python -m venv venv
venv\Scripts\activate
```
Debés ver `(venv)` en la consola.

---

# ✅ 3. Instalar Django
```
pip install django
```

---

# ✅ 4. Crear proyecto y app
Desde la carpeta TIENDA:
```
django-admin startproject tienda .
python manage.py startapp shop
```

Estructura esperada:
```
TIENDA/
 ├─ manage.py
 ├─ tienda/
 └─ shop/
```

---

# ✅ 5. Configurar settings.py
Editar `tienda/settings.py`:
- Agregar `shop` en INSTALLED_APPS.
- Configurar STATIC y MEDIA:

```
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'shop' / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

---

# ✅ 6. Crear modelo Product
En `shop/models.py`:
```
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return self.name
```

---

# ✅ 7. Migraciones
```
python manage.py makemigrations
python manage.py migrate
```

---

# ✅ 8. Formularios (crear productos)
Crear `shop/forms.py`:
```
from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image']
```

---

# ✅ 9. Crear vistas (carrito y productos)
En `shop/views.py`:
```
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from .forms import ProductForm

def product_list(request):
    products = Product.objects.all()
    return render(request, 'shop/product_list.html', {'products': products})

def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return redirect('cart_view')

def cart_view(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0
    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        subtotal = product.price * qty
        total += subtotal
        items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
    return render(request, 'shop/cart.html', {'items': items, 'total': total})

def clear_cart(request):
    request.session['cart'] = {}
    return redirect('cart_view')

def create_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'shop/create_product.html', {'form': form})
```

---

# ✅ 10. Crear URLs
Archivo `shop/urls.py`:
```
from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('create/', views.create_product, name='create_product'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart_view'),
    path('clear/', views.clear_cart, name='clear_cart'),
]
```

Y en `tienda/urls.py`:
```
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('shop.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

# ✅ 11. Crear templates
Carpeta: `shop/templates/shop/`

### product_list.html, cart.html, create_product.html
(Se agregan según lo provisto en el proyecto.)

---

# ✅ 12. CSS simple
Crear carpeta:
```
shop/static/shop/
```
Archivo: `styles.css`
```
body { font-family: Arial; background:#f4f4f4; }
.container { max-width: 800px; margin:auto; padding:20px; background:white; }
.product-item, .cart-item { padding:12px; margin-bottom:12px; background:#fafafa; border-radius:6px; }
.btn { background:#28a745; padding:8px 12px; color:white; text-decoration:none; border-radius:6px; }
```

---

# ✅ 13. Ejecutar el servidor
```
python manage.py runserver
```
Entrar a:
- Tienda → `http://127.0.0.1:8000/`
- Crear producto → `http://127.0.0.1:8000/create/`
- Carrito → `http://127.0.0.1:8000/cart/`

---

# ✅ 14. Subir imágenes
Desde el formulario `/create/` podés cargar fotos → quedan en `media/products/`.

---

# 📌 Con esto tenés un proyecto Django funcional, simple y listo para entregar.


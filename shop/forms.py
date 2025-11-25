from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product, Order, Profile, Review

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image', 'category']

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100, required=False)
    email = forms.EmailField(required=False)
    
    class Meta:
        model = Profile
        fields = ['phone', 'address', 'city']

class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=200, label='Nombre completo')
    address = forms.CharField(max_length=300, label='Dirección')
    city = forms.CharField(max_length=100, label='Ciudad')
    phone = forms.CharField(max_length=50, label='Teléfono')
    payment_method = forms.ChoiceField(
        choices=[
            ('cash', '💵 Efectivo'),
            ('card', '💳 Tarjeta de Crédito'),
            ('transfer', '🏦 Transferencia'),
            ('mercadopago', '🔵 MercadoPago'),
        ],
        label='Método de pago',
        widget=forms.RadioSelect
    )
    coupon_code = forms.CharField(max_length=50, required=False, label='Código de cupón')

class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f'{i} ⭐') for i in range(1, 6)],
        widget=forms.RadioSelect,
        label='Calificación'
    )
    
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Contanos tu experiencia con este producto...'}),
        }
        labels = {
            'comment': 'Tu comentario'
        }

class CouponForm(forms.Form):
    code = forms.CharField(max_length=50, label='Código de cupón')

from django.shortcuts import render, HttpResponse, redirect
from .models import *
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from datetime import date, timedelta
from django.contrib import messages
import random
from django.core.mail import send_mail
from django.conf import settings
import razorpay


def get_logged_in_user(request):
    if request.session.get("is_logged_in"):
        return User.objects.get(id=request.session["uid"])
    return None


def index(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    request.session['user_name']=user.name
    if not user:
        return redirect('login')
    search_query = request.GET.get('search')
    wishlist_products = Wishlist.objects.filter(user=user).values_list('product_id', flat=True)
    
    show_page = None
    # is_search = True    

    if search_query:
        # is_search = True
        products = Products.objects.filter(
            Q(name__icontains=search_query)|
            Q(description__icontains=search_query)|
            Q(detail__icontains=search_query)|
            Q(brand__brand__icontains=search_query)|
            Q(colors__color__icontains=search_query)
        ).distinct()
    else:
        products = Products.objects.all()   
        page_num = request.GET.get('page')                 
        paginatior = Paginator(products, 8)
        products = paginatior.get_page(page_num)
        show_page = paginatior.get_elided_page_range(number=products.number, on_each_side=1, on_ends=1)
    
    con = {
        'products':products,
        'show_page':show_page,
        'wishlist_products':wishlist_products, 
        # 'is_search':is_search,
        'search_query':search_query,      
    }


    return render(request, 'index.html', con)


def cart(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    total = 0
    cart_items = Cart.objects.filter(user=user)    

    for i in cart_items:
        total += i.total_price

    discount = 0
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupons.objects.get(id=coupon_id)
            discount = coupon.coupon_amount
        except Coupons.DoesNotExist:
            pass
    
    final_amount = 0
    coupon_codes = Coupons.objects.all()
    coupons = Coupons.objects.values_list('coupon_code')
    msg = ""    
    if request.POST:
        cc = request.POST['coupon']
        if cc not in coupons:
            msg = "Coupon doesn't exist"    
        for i in coupon_codes:
            if cc.upper() == i.coupon_code:                
                if Applied_coupons.objects.filter(applied_user=user, applied_coupon_code=i).exists():
                    msg="coupon already used"
                else:    
                    cc_from = i.valid_from
                    cc_to = i.valid_to
                    todays_date = date.today()
                    if todays_date <= cc_to and todays_date >= cc_from :      
                        if total >= i.minimum_total:          
                            Applied_coupons.objects.create(applied_user=user, applied_coupon_code=i)
                            discount = i.coupon_amount
                            request.session['coupon_id']=i.id
                            msg = "coupon applied successfully"
                            return redirect('cart')
                        else:
                            msg = f"minimum spend of {i.minimum_total} is required"
                    else:
                        msg = "coupon expired"           
    
    
    final_amount = total - discount

    con = { 
        'cart_items':cart_items,
        'total':total,
        'discount':discount,
        'final_amount':final_amount,
        'msg':msg, 
        'coupon_id':coupon_id,
    }
    return render(request, 'cart.html', con)


def remove_coupon(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    coupon_id = request.session.get('coupon_id')
    applied_coupon = Applied_coupons.objects.filter(applied_coupon_code_id=coupon_id, applied_user=user)
    applied_coupon.delete()
    request.session.pop('coupon_id', None)
    return redirect('cart')


def save_addresses(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    if request.method == "POST":
        full_name = request.POST['full_name']
        email = request.POST['email']
        phone_no = request.POST['phone_no']
        village_city = request.POST['village_city']
        sub_district = request.POST['sub_district']
        district = request.POST['district']
        state = request.POST['state']
        zip_pin = request.POST['zip_pin']
        address_text = request.POST['address']
        address_id = request.POST.get('address_id')  

        if address_id:
            addr = Adresses.objects.get(id=address_id, user=user)
            addr.name = full_name
            addr.email = email
            addr.phone_no = phone_no
            addr.village_city = village_city
            addr.sub_district = sub_district
            addr.district = district
            addr.state = state
            addr.zip_pin = zip_pin
            addr.address = address_text
            addr.save()
        else:
            Adresses.objects.create(
                user=user,
                name=full_name,
                email=email,
                phone_no=phone_no,
                village_city=village_city,
                sub_district=sub_district,
                district=district,
                state=state,
                zip_pin=zip_pin,
                address=address_text
            )

    return redirect('checkout')


def checkout(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    total = 0
    
    cart_items = Cart.objects.filter(user=user)
    if not cart_items:
        con = {
            'msg':"cart is empty!"
        }
        return render(request, 'cart.html', con)
    addresses = Adresses.objects.filter(user=user)

    for i in cart_items:
        total += i.total_price    
    if total > 0:
        shipping_cost = 50
    else:
        shipping_cost = 0
    
    discount = 0
    coupon_id = request.session.get('coupon_id')
    if coupon_id:  
        try:      
            coupon = Coupons.objects.get(id=coupon_id)
            discount = coupon.coupon_amount
        except Coupons.DoesNotExist:
            pass

    final_amount = total - discount + shipping_cost
    
    client = razorpay.Client(auth=('rzp_test_uqhoYnBzHjbvGF', 'jEhBs6Qp9hMeGfq5FyU45cVi'))
    razorpay_order = client.order.create({
        'amount': int(final_amount * 100), 
        'currency': 'INR',
        'payment_capture': 1
    })
    
    context = {
        "cart_items": cart_items,
        "total": total,
        "shipping_cost": shipping_cost,
        "final_amount": final_amount,
        "addresses": addresses,
        "discount":discount,
        "razorpay_order": razorpay_order,
        "razorpay_key": 'rzp_test_uqhoYnBzHjbvGF',
    }
    return render(request, "checkout.html", context)


def add_to_cart(request, product_id):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    product = Products.objects.filter(id=product_id).first()
    if not product:
        return redirect('index') 

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        color_id = request.POST.get("color")
        size_id = request.POST.get("size")
        width_id = request.POST.get("width")

        color = Colors.objects.filter(id=color_id).first() if color_id else product.colors.first()

        if size_id and width_id:
            size = Size.objects.filter(id=size_id).first()
            width = Width.objects.filter(id=width_id).first()
        else:
            stock_entry = product.stocks.first()
            size = stock_entry.size if stock_entry else None
            width = stock_entry.width if stock_entry else None
    else:
        quantity = 1
        color = product.colors.first()
        stock_entry = product.stocks.first()
        size = stock_entry.size if stock_entry else None
        width = stock_entry.width if stock_entry else None

    cart_item = Cart.objects.filter(
        user=user,
        product=product,
        color=color,
        size=size,
        width=width
    ).first()

    if cart_item:
        cart_item.quantity += quantity
        cart_item.save()
    else:
        Cart.objects.create(
            user=user,
            product=product,
            color=color,
            size=size,
            width=width,
            quantity=quantity
        )

    return redirect('index')


def remove_from_cart(request, item_id):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    cart_item = Cart.objects.get(user=user, id=item_id)
    cart_item.delete()

    return redirect('cart')


def cart_minus(request, item_id):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    cart_item = Cart.objects.get(user=user, id=item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart')


def cart_plus(request, item_id):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    cart_item = Cart.objects.get(user=user, id=item_id)
    cart_item.quantity += 1
    cart_item.save()

    return redirect('cart')    


def wishlist(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    
    wishlist_items = Wishlist.objects.filter(user=user)
    con = {
        'wishlist_items':wishlist_items,
    }
    return render(request, 'wishlist.html', con)


def add_to_wishlist(request, product_id):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    try:
        wishlist_item = Wishlist.objects.get(user=user, product_id=product_id)
        wishlist_item.delete()
    except Wishlist.DoesNotExist:
        Wishlist.objects.create(
            user=user,
            product_id=product_id,
        )

    return redirect('index') 


def remove_from_wishlist(request, item_id):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    
    wishlist_item = Wishlist.objects.get(
        user=user,
        id=item_id
    )
    wishlist_item.delete()
    
    return redirect('wishlist')


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


def contact(request):
    if request.POST:
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        subject =  request.POST['subject']
        message = request.POST['message']

        if Contacts.objects.filter(email=email).first():
            con = {
                'msg1':'this email is already used!'
            }
            return render(request, 'contact.html', con)
        else:
            Contacts.objects.create(
                first_name = first_name,
                last_name = last_name,
                email = email,
                subject = subject, 
                message = message
            )

            full_message = f"Message from {first_name} {last_name} <{email}>:\n\n{message}"
            send_mail(
                subject=f"New Contact Message: {subject}",
                message=full_message,
                from_email=email,          
                recipient_list=[settings.EMAIL_HOST_USER],    
                fail_silently=False,                  
            )
            con = {
                'msg':'Message Sent Successfully!'
            }
            return render(request, 'contact.html', con)
            
    return render(request, 'contact.html')


def men(request, id=None):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
        
    sub_category = Sub_Categories.objects.filter(main_category__name='MEN')
    wishlist_products = Wishlist.objects.filter(user=user).values_list('product_id', flat=True)
    colors = Colors.objects.all()
    brands = Brand.objects.all()

    if id:
        products = Products.objects.filter(sub_category_id=id, main_category__name='MEN')
        heading = Sub_Categories.objects.get(id=id).name
    else:
        products = Products.objects.filter(main_category__name='MEN')
        heading = "All"

    brand_id = request.GET.get('brand')
    if brand_id:
        products = products.filter(brand_id=brand_id)

    color_id = request.GET.get('color')
    if color_id:
        products = products.filter(colors__id=color_id)

    from_date = request.GET.get('latest_products')
    if from_date is not None:
        week_ago = date.today() - timedelta(days=3)
        products = products.filter(date_added__gte=week_ago)
    
    max_price = request.GET.get('max_price')
    min_price = request.GET.get('min_price')
    if max_price:
        products = products.filter(price__lte=max_price)
    if min_price:
        products = products.filter(price__gte=min_price)

    extended_width = request.GET.get('extended_width')
    if extended_width:
        products = products.filter(stocks__width__value=extended_width).distinct()


    best_sellers = request.GET.get('best_sellers')
    if best_sellers:
        products = (
            products
            .annotate(total_sales=Sum("order_items__quantity"))
            .filter(total_sales__gte=0)
            .order_by("-total_sales") 
        )

    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(detail__icontains=search_query) |
            Q(brand__brand__icontains=search_query) |
            Q(colors__color__icontains=search_query)
        ).distinct()

    sort_option = request.GET.get('sort')
    if sort_option == 'low_to_high':
        products = products.order_by('price')
    elif sort_option == 'high_to_low':
        products = products.order_by('-price')
    elif sort_option == 'a_to_z':
        products = products.order_by('name')
    elif sort_option == 'z_to_a':
        products = products.order_by('-name')

    paginator = Paginator(products, 6)
    page_num = request.GET.get('page')
    products = paginator.get_page(page_num)
    show_page = paginator.get_elided_page_range(number=products.number, on_each_side=1, on_ends=1)

    con = {
        'products':products,
        'sub_category':sub_category,
        'heading':heading,
        'colors':colors,
        'brands':brands,
        'max_price':max_price,
        'min_price':min_price,
        'search_query':search_query,
        'show_page':show_page,
        'wishlist_products':wishlist_products,
    }
    return render(request, 'men.html', con)


def submit_review(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    try:
        product = Products.objects.get(id=id)
    except Products.DoesNotExist:
        return redirect('index') 

    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        comment = request.POST.get("comment")
        Review.objects.create(
            product=product,
            user=user,
            rating=rating,
            comment=comment
        )
    return redirect('product_details', id=product.id)


def product_detail(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')

    product = Products.objects.get(id=id)
    carousel_images = product.carousel_images.all()
    sizes = Size.objects.filter(product_sizes__product=product).distinct()
    widths = Width.objects.filter(product_widths__product=product).distinct()
    reviews = product.reviews.all().order_by('-created_at')

    con = {
        'products': product,
        'carousel_images': carousel_images,
        'sizes': sizes,
        'widths': widths,
        'reviews': reviews,
        'average_rating': product.average_rating(),
        'review_count': product.review_count(),
        'distribution': product.rating_distribution(),
    }
    return render(request, 'product_detail.html', con)


def order_complete(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    
    if request.method == 'POST':
        # Handle form submission for placing order
        if 'btn_place_order' in request.POST:
            address_id = request.POST.get("selected_address")
            payment_method = request.POST.get("payment_method")

            if not address_id or not payment_method:
                messages.error(request, "Please select address and payment method.")
                return redirect('checkout')

            cart_items = Cart.objects.filter(user=user)
            if not cart_items:
                messages.error(request, "Your cart is empty.")
                return redirect('cart')

            subtotal = sum(item.total_price for item in cart_items)

            discount = 0
            shipping_cost = 50 if subtotal > 0 else 0
            coupon_id = request.session.get('coupon_id')
            if coupon_id:
                try:
                    coupon = Coupons.objects.get(id=coupon_id)
                    discount = coupon.coupon_amount
                except Coupons.DoesNotExist:
                    pass

            final_amount = subtotal - discount + shipping_cost
            
            address = Adresses.objects.get(id=address_id, user=user)

            # Handle Cash on Delivery
            if payment_method == 'cashondelivery':
                order = Orders.objects.create(
                    user=user,
                    address=address,
                    payment_method=payment_method,
                    payment_status=False,
                    final_amount=final_amount,
                    discount=discount                        
                )


                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price,
                        color=item.color,
                        size=item.size,
                        width=item.width
                    )

                cart_items.delete()
                request.session.pop('coupon_id', None)
                con = {
                    'msg':'Your order has been placed successfully!',
                }
                return render(request, "order_complete.html", con)
            
            # Handle Razorpay payment - redirect to payment page
            elif payment_method == 'razorpay':
                # Store order details in session
                request.session['order_data'] = {
                    'address_id': address_id,
                    'payment_method': payment_method,
                    'final_amount': float(final_amount)
                }
                return redirect('razorpay_payment')
        
        # Handle Razorpay payment success callback
        elif 'razorpay_payment_id' in request.POST:
            payment_id = request.POST.get('razorpay_payment_id')
            order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')
            
            # Verify payment signature
            client = razorpay.Client(auth=('rzp_test_uqhoYnBzHjbvGF', 'jEhBs6Qp9hMeGfq5FyU45cVi'))
            
            try:
                # Verify signature
                client.utility.verify_payment_signature({
                    'razorpay_payment_id': payment_id,
                    'razorpay_order_id': order_id,
                    'razorpay_signature': signature
                })
                
                # Get order data from session
                order_data = request.session.get('order_data')
                if not order_data:
                    messages.error(request, "Order data not found.")
                    return redirect('checkout')
                
                cart_items = Cart.objects.filter(user=user)
                address = Adresses.objects.get(id=order_data['address_id'], user=user)
                
                # Create order with successful payment
                order = Orders.objects.create(
                    user=user,
                    address=address,
                    payment_method='razorpay',
                    payment_status=True,
                    final_amount=order_data['final_amount'],  
                    discount=discount,                      
                )

                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price,
                        color=item.color,
                        size=item.size,
                        width=item.width
                    )

                cart_items.delete()
                
                # Clear session data
                if 'order_data' in request.session:
                    del request.session['order_data']
                
                con = {
                    'msg': 'Your order has been placed successfully! Payment completed.',
                }
                return render(request, "order_complete.html", con)
                
            except Exception as e:
                messages.error(request, "Payment verification failed.")
                return redirect('checkout')
    
    # GET request - should redirect to checkout
    return redirect('checkout')


def razorpay_payment(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    
    order_data = request.session.get('order_data')
    if not order_data:
        messages.error(request, "Order data not found.")
        return redirect('checkout')
    
    cart_items = Cart.objects.filter(user=user)
    subtotal = sum(item.total_price for item in cart_items)
    shipping_cost = 50 if subtotal > 0 else 0
    final_amount = subtotal + shipping_cost
    
    # Create Razorpay order
    client = razorpay.Client(auth=('rzp_test_uqhoYnBzHjbvGF', 'jEhBs6Qp9hMeGfq5FyU45cVi'))
    razorpay_order = client.order.create({
        'amount': int(final_amount * 100),
        'currency': 'INR',
        'payment_capture': 1
    })
    
    context = {
        'razorpay_order': razorpay_order,
        'razorpay_key': 'rzp_test_uqhoYnBzHjbvGF',
        'final_amount': final_amount,
        'user': user,
    }
    return render(request, 'razorpay_payment.html', context)


def women(request, id=None):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    
    sub_category = Sub_Categories.objects.filter(main_category__name='WOMEN')
    wishlist_products = Wishlist.objects.filter(user=user).values_list('product_id', flat=True)
    brands = Brand.objects.all()
    colors = Colors.objects.all()
    current_subcategory_id = None

    products = Products.objects.filter(main_category__name='WOMEN')

    if id:
        products = products.filter(sub_category__id=id)
        heading = Sub_Categories.objects.get(id=id).name
        current_subcategory_id = id
    else:
        heading = "ALL"

    brand_id = request.GET.get('brand')
    if brand_id:
        products = products.filter(brand_id=brand_id)

    color_id = request.GET.get('color')
    if color_id:
        products = products.filter(colors__id=color_id)

    max_price = request.GET.get('max_price')
    min_price = request.GET.get('min_price')
    if max_price:
        products = products.filter(price__lte=max_price)
    if min_price:
        products = products.filter(price__gte=min_price)

    from_date = request.GET.get('latest_products')
    if from_date is not None:
        week_ago = date.today() - timedelta(days=3)
        products = products.filter(date_added__gte=week_ago)

    extended_width = request.GET.get('extended_width')
    if extended_width:
        products = products.filter(stocks__width__value=extended_width).distinct()
    
    best_sellers = request.GET.get('best_sellers')
    if best_sellers:
        products = (
            products
            .annotate(total_sales=Sum("order_items__quantity"))
            .filter(total_sales__gte=0)
            .order_by("-total_sales") 
        )

    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(detail__icontains=search_query) |
            Q(brand__brand__icontains=search_query) |
            Q(colors__color__icontains=search_query)
        ).distinct()

    sort_option = request.GET.get('sort')
    if sort_option == 'low_to_high':
        products = products.order_by('price')
    elif sort_option == 'high_to_low':
        products = products.order_by('-price')
    elif sort_option == 'a_to_z':
        products = products.order_by('name')
    elif sort_option == 'z_to_a':
        products = products.order_by('-name')

    paginator = Paginator(products, 6)
    page_num = request.GET.get('page')
    products = paginator.get_page(page_num)
    show_page = paginator.get_elided_page_range(number=products.number, on_each_side=1, on_ends=1)

    context = {
        'sub_category': sub_category,
        'products': products,
        'heading': heading,
        'brands': brands,
        'colors': colors,
        'current_subcategory_id': current_subcategory_id,
        'max_price':max_price,        
        'show_page':show_page,
        'wishlist_products':wishlist_products,
        'search_query':search_query,
    }
    return render(request, 'women.html', context)


def about(request):
    return render(request, 'about.html')


def register(request):
    if request.POST:
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            con = {
                'msg':'password and confirm password must match',
            }
            return render(request, 'register.html', con)
        try:   
            uid = User.objects.get(email=email)
            con = {
                'msg1':'use another email, this already in use.',
            }
            return render(request, 'register.html', con)
        except User.DoesNotExist:      
            User.objects.create(
                name=name,
                email=email,
                password=password,
                )
            return redirect('login')
    else:
        return render(request, 'register.html')


def login(request):
    if request.POST:
        email = request.POST['email']
        password = request.POST['password']

        try:
            uid = User.objects.get(email=email)

            if email == uid.email:
                if password == uid.password:
                    request.session['uid'] = uid.id
                    request.session['is_logged_in'] = True

                    return redirect('index')
                else:
                    con = {
                        'msg':'wrong password',
                    }
                    return render(request, 'login.html', con)
            else:
                con = {
                    'msg1':'email not found',
                }
                return render(request, 'login.html', con)
        except User.DoesNotExist:
            con = {
                'msg1':'email not found',
            }
            return render(request, 'login.html', con)
    else:
        return render(request, 'login.html')  


def logout(request):
    request.session.flush()
    return redirect('login')


def orders(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect('login')
    
    orders = Orders.objects.filter(user=user).order_by('-created_at')
    shipping_cost = 50
    con = {
        'orders':orders,
        'shipping_cost':shipping_cost,
    }

    return render(request, 'orders.html', con)


def forget_password(request):
    if request.method == "POST":
        # STEP 1: Send OTP
        if "send_otp" in request.POST:
            email = request.POST.get('email')
            try:
                user = User.objects.get(email=email)
                otp = random.randint(1000, 9999)
                user.otp = otp
                user.save()

                send_mail(
                    "OTP Verification",
                    f"Your OTP is: {otp}",
                    'your@gmail.com',
                    [email],
                )

                return render(request, "forget_password.html", {"email": email, "otp_sent": True})

            except User.DoesNotExist:
                return render(request, "forget_password.html", {"msg": "This email is not registered"})

        # STEP 2: Verify OTP
        elif "verify_otp" in request.POST:
            email = request.POST.get('email')
            otp = request.POST.get('otp')

            try:
                user = User.objects.get(email=email, otp=otp)
                return render(request, "forget_password.html", {"email": email, "otp_verified": True})
            except User.DoesNotExist:
                return render(request, "forget_password.html", {"msg": "Invalid OTP", "email": email, "otp_sent": True})

        # STEP 3: Reset Password
        elif "reset_password" in request.POST:
            email = request.POST.get('email')
            new_password = request.POST.get('new_password')

            try:
                user = User.objects.get(email=email)
                user.password = new_password
                user.otp = None  # clear OTP
                user.save()
                return redirect("login")
            except User.DoesNotExist:
                return render(request, "forget_password.html", {"msg": "Something went wrong"})
    
    return render(request, "forget_password.html")


def support(request):
    return render(request, 'support.html')



from django.db import models

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    otp = models.IntegerField(blank=True, null=True)
    password = models.TextField()

    def __str__(self):
        return self.name
    
class Main_Categories(models.Model):
    name = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def __str__(self):
        return self.name

class Sub_Categories(models.Model):
    main_category = models.ForeignKey(Main_Categories, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, blank=True,null=True)
    image = models.ImageField(upload_to='subcategory/', blank=True, null=True)

    def __str__(self):
        return self.name    
    
class Size(models.Model):
    value = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.value
    
class Width(models.Model):
    value = models.CharField(max_length=2, blank=True, null=True)

    def __str__(self):
        return self.value
    
class Brand(models.Model):
    brand = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.brand
    
class Colors(models.Model):
    color = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.color

class Products(models.Model):
    main_category = models.ForeignKey(Main_Categories, on_delete=models.CASCADE, blank=True, null=True)
    sub_category = models.ForeignKey(Sub_Categories, on_delete=models.CASCADE, blank=True, null=True)    
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, blank=True, null=True)
    colors = models.ManyToManyField(Colors, blank=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cancel_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_added = models.DateTimeField(auto_now_add=True)
    main_image = models.ImageField(upload_to="images/", blank=True, null=True)
    rating = models.IntegerField(default=0)
    detail = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    manufacturer = models.TextField(blank=True, null=True)

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0

    def review_count(self):
        return self.reviews.count()

    def rating_distribution(self):
        """Return dict of star counts {5: x, 4: y, ...}"""
        return {i: self.reviews.filter(rating=i).count() for i in range(1, 6)}

    def __str__(self):
        return self.name

class ProductStock(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='stocks')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, related_name='product_sizes')
    width = models.ForeignKey(Width, on_delete=models.CASCADE, related_name='product_widths')
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size', 'width')

    def __str__(self):
        return f"{self.product.name} | Size: {self.size.value} | Width: {self.width.value} | Stock: {self.stock}"

class ProductImages(models.Model):
    products = models.ForeignKey(Products, on_delete=models.CASCADE, related_name="carousel_images")
    images = models.ImageField(upload_to="images/")

    def __str__(self):
        return f"Extra image for {self.images} : { self.products.name}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart")
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    color = models.ForeignKey(Colors, on_delete=models.CASCADE, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True, blank=True)
    width = models.ForeignKey(Width, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'color', 'size', 'width')

    def __str__(self):
        return f"{self.product.name} ({self.quantity}) - {self.user.name}"

    @property
    def total_price(self):
        return self.product.price * self.quantity
        
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user} - {self.product.name}"
    
class Coupons(models.Model):
    coupon_code = models.CharField(max_length=10)
    coupon_amount = models.IntegerField()
    valid_from = models.DateField(blank=True, null=True)
    valid_to = models.DateField(blank=True, null=True)
    minimum_total = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.coupon_code

class Applied_coupons(models.Model):
    applied_user = models.ForeignKey(User, on_delete=models.CASCADE)
    applied_coupon_code = models.ForeignKey(Coupons, on_delete=models.CASCADE)

    def __str__(self):
        return "user : " + self.applied_user.name + ", Coupon code : " + self.applied_coupon_code.coupon_code
    
class Adresses(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone_no = models.IntegerField()
    village_city = models.CharField(max_length=20)
    sub_district = models.CharField(max_length=20)
    district = models.CharField(max_length=20)
    state = models.CharField(max_length=20)
    zip_pin = models.IntegerField()
    address = models.TextField()

    def __str__(self):
        return self.name + "  " + self.address
    
class Orders(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Adresses, on_delete=models.CASCADE) 
    payment_method = models.CharField(max_length=100)
    payment_status = models.BooleanField(default=False)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Orders, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Products, related_name="order_items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  
    color = models.ForeignKey(Colors, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    width = models.ForeignKey(Width, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Contacts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    subject = models.CharField(max_length=100)
    message = models.TextField()

    def __str__(self):
        return self.first_name + self.last_name

class Review(models.Model):
    product = models.ForeignKey(Products, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.product.name} ({self.rating})"
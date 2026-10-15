from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# Create your models here.


class users(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=20)
    Address = models.TextField()
    gender = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile_pic = models.FileField(upload_to='workers_pic/')

    def __str__(self):
        return self.admin.username

    @property
    def get_profile_pic_url(self):
        if self.profile_pic:
            try:
                return self.profile_pic.url
            except ValueError:
                pass
        return None


class workers(models.Model):
    admin = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=20)
    dob = models.DateField(null=True, blank=True)
    Address = models.TextField()
    city = models.CharField(max_length=255)
    gender = models.CharField(max_length=250)
    designation = models.CharField(max_length=255)
    profile_pic = models.FileField(upload_to='workers_pic/')
    acc_activation = models.BooleanField(default=False)
    avalability_status = models.BooleanField(default=True)
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    service_areas = models.ManyToManyField('City', blank=True, related_name='assigned_workers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.admin.username

    def serves_city(self, city):
        """Checks if the worker covers the given City."""
        if not city:
            return False
        if self.service_areas.exists():
            if hasattr(city, 'id'):
                return self.service_areas.filter(id=city.id).exists()
            return self.service_areas.filter(name__iexact=str(city)).exists()
        # Fallback for existing workers: check city text field
        if self.city:
            city_name = city.name if hasattr(city, 'name') else str(city)
            return self.city.strip().lower() == city_name.strip().lower()
        return True

    def get_service_areas_display(self):
        """Returns comma-separated list of service area names."""
        areas = list(self.service_areas.values_list('name', flat=True))
        if areas:
            return ", ".join(areas)
        return self.city or "All Areas"

    @property
    def get_profile_pic_url(self):
        if self.profile_pic:
            try:
                return self.profile_pic.url
            except ValueError:
                pass
        return None


class Country(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.name} ({self.country.name})"


class City(models.Model):
    state = models.CharField(max_length=150)
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class ServiceCatogarys(models.Model):
    img = models.ImageField(upload_to='catogry_imgs')
    Name = models.CharField(max_length=255)
    Description = models.TextField()
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=300.00)

    def __str__(self):
        return f"{self.Name} (৳{self.hourly_rate}/hr)"

    @property
    def get_img_url(self):
        if self.img:
            try:
                return self.img.url
            except ValueError:
                pass
        return "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=600&q=80"


class ServiceAddOn(models.Model):
    """Optional add-ons/materials customer can select during booking (e.g. Gas Refill, Master Wash)."""
    service = models.ForeignKey(ServiceCatogarys, on_delete=models.CASCADE, related_name='addons')
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.service.Name} - {self.name} (+৳{self.price})"


class ServiceRequests(models.Model):
    user = models.ForeignKey(users, on_delete=models.CASCADE)
    Problem_Description = models.TextField()
    service = models.ForeignKey(ServiceCatogarys, on_delete=models.CASCADE)
    Address = models.TextField()
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    pin = models.CharField(max_length=10)
    House_No = models.CharField(max_length=20)
    landmark = models.TextField(null=True, blank=True)
    contact = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    status = models.BooleanField(default=False)
    dateofrequest = models.DateTimeField(auto_now_add=True)
    
    # Selected Service Add-ons & Extra materials
    selected_addons = models.ManyToManyField(ServiceAddOn, blank=True, related_name='requests')
    addons_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.admin.username} - {self.service.Name}"


class Response(models.Model):
    requests = models.ForeignKey(ServiceRequests, on_delete=models.CASCADE)
    assigned_worker = models.ForeignKey(workers, on_delete=models.CASCADE)
    Date = models.DateField(auto_now=True)
    status = models.BooleanField(default=False)

    # Status Timeline (Requested -> Accepted -> On the Way -> In Progress -> Completed -> Paid)
    job_status = models.CharField(
        max_length=30,
        choices=[
            ('Accepted', 'Accepted'),
            ('On the Way', 'On the Way'),
            ('In Progress', 'In Progress'),
            ('Completed', 'Completed'),
            ('Cancelled', 'Cancelled'),
        ],
        default='Accepted'
    )
    on_the_way_at = models.DateTimeField(null=True, blank=True)
    in_progress_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Live GPS Technician Moving Tracking (Pathao/Uber style)
    worker_latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    worker_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)

    # Billing & Payment fields (10% admin platform commission, 90% worker payout)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=300.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    admin_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    worker_earning = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Paid', 'Paid')],
        default='Pending'
    )
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.requests} - {self.assigned_worker}"

    def get_progress_percentage(self):
        if self.job_status == 'Accepted':
            return 25
        elif self.job_status == 'On the Way':
            return 50
        elif self.job_status == 'In Progress':
            return 75
        elif self.job_status == 'Completed':
            return 100 if self.payment_status == 'Paid' else 90
        elif self.job_status == 'Cancelled':
            return 0
        return 25

    def calculate_bill(self, hours):
        from decimal import Decimal
        self.hours_worked = Decimal(str(hours))
        self.hourly_rate = self.requests.service.hourly_rate or Decimal("300.00")
        hourly_total = self.hours_worked * self.hourly_rate
        addon_total = Decimal(str(self.requests.addons_total or "0.00"))
        self.total_amount = (hourly_total + addon_total).quantize(Decimal("0.01"))
        self.admin_commission = (self.total_amount * Decimal("0.10")).quantize(Decimal("0.01"))
        self.worker_earning = self.total_amount - self.admin_commission


class Feedback(models.Model):
    Rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    Description = models.TextField()
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    # User=models.ForeignKey(users,on_delete=models.CASCADE)
    Employ = models.ForeignKey(workers, on_delete=models.CASCADE)
    Date = models.DateField()

    def __str__(self):
        return f"{self.User.username} - {self.Rating}"

    @property
    def star_range(self):
        try:
            r = int(self.Rating or 0)
            return range(max(0, min(5, r)))
        except (ValueError, TypeError):
            return range(0)

    @property
    def empty_star_range(self):
        try:
            r = int(self.Rating or 0)
            return range(5 - max(0, min(5, r)))
        except (ValueError, TypeError):
            return range(5)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    forget_token = models.CharField(max_length=1000)

    def __str__(self):
        return self.user.username


class WithdrawalRequest(models.Model):
    worker = models.ForeignKey(workers, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('bKash', 'bKash'),
            ('Nagad', 'Nagad'),
            ('Rocket', 'Rocket'),
            ('Bank Transfer', 'Bank Transfer'),
        ],
        default='bKash'
    )
    account_number = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Approved', 'Approved'),
            ('Rejected', 'Rejected'),
        ],
        default='Pending'
    )
    admin_notes = models.TextField(blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.worker.admin.get_full_name()} - ৳{self.amount} ({self.status})"


class ChatMessage(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.message[:30]}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    notification_type = models.CharField(
        max_length=50,
        choices=[
            ('booking', 'Booking'),
            ('status', 'Status Update'),
            ('chat', 'Chat Message'),
            ('payment', 'Payment'),
            ('wallet', 'Wallet / Payout'),
            ('system', 'System Alert'),
        ],
        default='system'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.notification_type}] {self.user.username}: {self.title}"

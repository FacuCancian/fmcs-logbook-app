from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import timedelta


class Driver(models.Model):
    """Driver profile linked to Django User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    driver_number = models.CharField(max_length=20, unique=True, verbose_name="Driver ID")
    home_terminal = models.CharField(max_length=100, verbose_name="Home Terminal")
    truck_license = models.CharField(max_length=20, verbose_name="Truck License Plate")

    class Meta:
        verbose_name = "Driver"
        verbose_name_plural = "Drivers"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.driver_number})"


class LogDay(models.Model):
    """Work day - Logbook header"""
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='log_days')
    date = models.DateField(verbose_name="Date")

    # Driver information for this day
    driver_number = models.CharField(max_length=20, verbose_name="Driver ID")
    initials = models.CharField(max_length=10, verbose_name="Initials")
    signature = models.CharField(max_length=100, verbose_name="Signature")
    co_driver = models.CharField(max_length=100, default='N/A', verbose_name="Co-driver")
    home_terminal = models.CharField(max_length=100, verbose_name="Home Terminal")
    truck_license = models.CharField(max_length=20, verbose_name="Truck License")

    # Trailers (up to 4)
    trailer_1 = models.CharField(max_length=20, blank=True, default='N/A', verbose_name="Trailer 1")
    trailer_2 = models.CharField(max_length=20, blank=True, default='N/A', verbose_name="Trailer 2")
    trailer_3 = models.CharField(max_length=20, blank=True, default='N/A', verbose_name="Trailer 3")
    trailer_4 = models.CharField(max_length=20, blank=True, default='N/A', verbose_name="Trailer 4")

    # Shipment data
    shipper = models.CharField(max_length=100, verbose_name="Shipper")
    commodity = models.CharField(max_length=100, verbose_name="Commodity")
    load_id_1 = models.CharField(max_length=50, blank=True, default='N/A', verbose_name="Load ID 1")
    load_id_2 = models.CharField(max_length=50, blank=True, default='N/A', verbose_name="Load ID 2")
    load_id_3 = models.CharField(max_length=50, blank=True, default='N/A', verbose_name="Load ID 3")
    load_id_4 = models.CharField(max_length=50, blank=True, default='N/A', verbose_name="Load ID 4")

    # Auto-calculated totals
    total_driving_hours = models.FloatField(default=0, verbose_name="Total Driving Hours")
    total_on_duty_hours = models.FloatField(default=0, verbose_name="Total On-Duty Hours")

    class Meta:
        unique_together = ['driver', 'date']
        verbose_name = "Work Day"
        verbose_name_plural = "Work Days"

    def __str__(self):
        return f"{self.driver} - {self.date}"


class DutySegment(models.Model):
    """Activity segment - Each line on the grid"""

    STATUS_CHOICES = [
        ('OFF', 'Off Duty'),
        ('SB', 'Sleeper Berth'),
        ('D', 'Driving'),
        ('ON', 'On Duty (Not Driving)'),
    ]

    log_day = models.ForeignKey(LogDay, on_delete=models.CASCADE, related_name='segments')

    # Time (in 15-minute increments)
    start_time = models.DateTimeField(verbose_name="Start Time")
    end_time = models.DateTimeField(verbose_name="End Time")

    # Status
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, verbose_name="Status")

    # Location (required)
    location_city = models.CharField(max_length=100, verbose_name="City")
    location_state = models.CharField(max_length=2, verbose_name="State")

    # Extra remarks (optional)
    remarks_extra = models.TextField(blank=True, verbose_name="Additional Remarks")

    class Meta:
        verbose_name = "Activity Segment"
        verbose_name_plural = "Activity Segments"
        ordering = ['start_time']

    def __str__(self):
        return f"{self.log_day.date} - {self.get_status_display()} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"

    @property
    def duration_hours(self):
        """Duration in hours (decimal)"""
        delta = self.end_time - self.start_time
        return round(delta.total_seconds() / 3600, 2)

    @property
    def is_valid_quarter_hour(self):
        """Check if minutes are 00, 15, 30, or 45"""
        for dt in [self.start_time, self.end_time]:
            if dt.minute % 15 != 0:
                return False
        return True

    @property
    def remarks_display(self):
        """Generate Remarks text in FMCSA format"""
        return f"{self.location_city}, {self.location_state}"

    def clean(self):
        """Validations before saving"""
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")

        if self.start_time.date() != self.end_time.date():
            raise ValidationError("Segments cannot cross midnight. Split into two.")

        if not self.is_valid_quarter_hour:
            raise ValidationError("Times must be in 15-minute increments (00, 15, 30, 45)")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
import os


class Profile(models.Model):
    ROLE_CHOICES = [
        ('learner', 'Learner'),
        ('teacher', 'Teacher'),
        ('both', 'Both'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(default='default_avatar.png', upload_to='profile_pics')
    website = models.URLField(max_length=200, blank=True)
    linkedin = models.URLField(max_length=200, blank=True)
    github = models.URLField(max_length=200, blank=True)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='learner')
    is_approved_teacher = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Wallet & Payment
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.avatar and self.avatar.name != 'default_avatar.png':
            try:
                img_path = self.avatar.path
                if os.path.exists(img_path):
                    img = Image.open(img_path)
                    if img.height > 300 or img.width > 300:
                        img.thumbnail((300, 300))
                        img.save(img_path)
            except (FileNotFoundError, OSError):
                pass

    def get_average_rating(self):
        from skills.models import Review
        reviews = Review.objects.filter(reviewee=self)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0.0

    def get_total_reviews(self):
        from skills.models import Review
        return Review.objects.filter(reviewee=self).count()

    def get_active_offers_count(self):
        return self.offers.filter(is_active=True).count()

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from users.models import Profile


class SkillCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-code')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Skill Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('skill-category-detail', kwargs={'pk': self.pk})


class Skill(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(SkillCategory, on_delete=models.CASCADE, related_name='skills')
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('skill-detail', kwargs={'pk': self.pk})

    def get_difficulty_display(self):
        """Return the human-readable difficulty level."""
        return dict(self.DIFFICULTY_CHOICES).get(self.difficulty, self.difficulty)


class SkillOffer(models.Model):
    teacher = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='offers')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='offers')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True)
    available_days = models.CharField(max_length=100, default='Mon-Fri')
    available_times = models.CharField(max_length=100, default='9 AM - 6 PM')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['teacher', 'skill']

    def __str__(self):
        return f'{self.teacher.user.username} teaches {self.skill.name}'

    def get_absolute_url(self):
        return reverse('offer-detail', kwargs={'pk': self.pk})

    def get_average_rating(self):
        completed_sessions = self.teacher.teaching_sessions.filter(
            skill=self.skill, status='completed'
        )
        reviews = Review.objects.filter(session__in=completed_sessions)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0.0


class Session(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    teacher = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='teaching_sessions')
    learner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='learning_sessions')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='sessions')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration = models.IntegerField(default=60, help_text='Duration in minutes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    # AI-generated summary stored after session completes
    ai_summary = models.TextField(blank=True, help_text='AI-generated session summary')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_date', 'scheduled_time']

    def __str__(self):
        return f'{self.learner.user.username} learns {self.skill.name} from {self.teacher.user.username}'

    def get_absolute_url(self):
        return reverse('session-detail', kwargs={'pk': self.pk})

    def get_total_cost(self):
        try:
            offer = SkillOffer.objects.get(teacher=self.teacher, skill=self.skill)
            hours = self.duration / 60
            return round(float(offer.hourly_rate) * hours, 2)
        except SkillOffer.DoesNotExist:
            return 0.0


class Review(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='given_reviews')
    reviewee = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 (worst) to 5 (best)'
    )
    comment = models.TextField(blank=True)
    # AI moderation flags
    ai_flagged = models.BooleanField(default=False)
    ai_flag_reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.rating}★ by {self.reviewer.user.username} for {self.reviewee.user.username}'
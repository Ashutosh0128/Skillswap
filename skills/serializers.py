from rest_framework import serializers
from django.utils import timezone
from django.db import models
from .models import SkillCategory, Skill, SkillOffer, Session, Review
from users.serializers import ProfileSerializer
from users.models import Profile


class SkillCategorySerializer(serializers.ModelSerializer):
    skill_count = serializers.IntegerField(source='skills.count', read_only=True)
    active_offer_count = serializers.SerializerMethodField()

    class Meta:
        model = SkillCategory
        fields = ['id', 'name', 'description', 'icon', 'skill_count', 'active_offer_count']

    def get_active_offer_count(self, obj):
        return SkillOffer.objects.filter(skill__category=obj, is_active=True).count()


class NestedSkillSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Skill
        fields = ['id', 'name', 'category_name', 'difficulty']


class SkillSerializer(serializers.ModelSerializer):
    category = SkillCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=SkillCategory.objects.all(), source='category', write_only=True
    )
    offer_count = serializers.IntegerField(source='offers.count', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)

    class Meta:
        model = Skill
        fields = [
            'id', 'name', 'category', 'category_id', 'description',
            'difficulty', 'difficulty_display', 'offer_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class SkillOfferSerializer(serializers.ModelSerializer):
    teacher = ProfileSerializer(read_only=True)
    skill = NestedSkillSerializer(read_only=True)
    skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), source='skill', write_only=True
    )
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = SkillOffer
        fields = [
            'id', 'teacher', 'skill', 'skill_id',
            'hourly_rate', 'description', 'available_days', 'available_times',
            'is_active', 'average_rating', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_average_rating(self, obj):
        return obj.get_average_rating()

    def validate_hourly_rate(self, value):
        if value < 0:
            raise serializers.ValidationError('Hourly rate cannot be negative.')
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request:
            validated_data['teacher'] = request.user.profile
        return super().create(validated_data)


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.user.username', read_only=True)
    reviewee_name = serializers.CharField(source='reviewee.user.username', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'session_id', 'reviewer_name', 'reviewee_name',
            'rating', 'comment', 'ai_flagged', 'created_at',
        ]
        read_only_fields = ['ai_flagged', 'created_at']


class SessionSerializer(serializers.ModelSerializer):
    teacher = ProfileSerializer(read_only=True)
    learner = ProfileSerializer(read_only=True)
    skill = NestedSkillSerializer(read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.username', read_only=True)
    learner_name = serializers.CharField(source='learner.user.username', read_only=True)
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_cost = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    review = ReviewSerializer(read_only=True)

    class Meta:
        model = Session
        fields = [
            'id', 'teacher', 'teacher_name', 'learner', 'learner_name',
            'skill', 'skill_name', 'scheduled_date', 'scheduled_time',
            'duration', 'status', 'status_display', 'notes', 'ai_summary',
            'total_cost', 'is_upcoming', 'review',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['ai_summary', 'created_at', 'updated_at']

    def get_total_cost(self, obj):
        return obj.get_total_cost()

    def get_is_upcoming(self, obj):
        from datetime import datetime
        dt = timezone.make_aware(datetime.combine(obj.scheduled_date, obj.scheduled_time))
        return dt > timezone.now()


class SessionCreateSerializer(serializers.ModelSerializer):
    offer_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Session
        fields = ['offer_id', 'scheduled_date', 'scheduled_time', 'duration', 'notes']

    def validate(self, data):
        offer_id = data.pop('offer_id')
        try:
            offer = SkillOffer.objects.get(id=offer_id, is_active=True)
        except SkillOffer.DoesNotExist:
            raise serializers.ValidationError({'offer_id': 'Invalid or inactive offer.'})

        request = self.context.get('request')
        if request and request.user == offer.teacher.user:
            raise serializers.ValidationError({'offer_id': 'Cannot book your own offer.'})

        if request:
            existing = Session.objects.filter(
                teacher=offer.teacher,
                learner=request.user.profile,
                skill=offer.skill,
                status__in=['pending', 'confirmed']
            ).exists()
            if existing:
                raise serializers.ValidationError({
                    'offer_id': 'You already have an active session with this teacher.'
                })
            data['teacher'] = offer.teacher
            data['learner'] = request.user.profile

        data['skill'] = offer.skill

        if 'scheduled_date' in data and 'scheduled_time' in data:
            from datetime import datetime
            dt = timezone.make_aware(datetime.combine(data['scheduled_date'], data['scheduled_time']))
            if dt < timezone.now():
                raise serializers.ValidationError({'scheduled_date': 'Cannot book in the past.'})
        return data

    def create(self, validated_data):
        return Session.objects.create(**validated_data)


class SessionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['status', 'notes']

    def validate_status(self, value):
        instance = self.instance
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': [],
        }
        if instance and value not in valid_transitions.get(instance.status, []):
            raise serializers.ValidationError(
                f"Cannot change status from '{instance.status}' to '{value}'."
            )
        return value


class ReviewCreateSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Review
        fields = ['session_id', 'rating', 'comment']

    def validate(self, data):
        session_id = data.pop('session_id')
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            raise serializers.ValidationError({'session_id': 'Invalid session.'})

        if session.status != 'completed':
            raise serializers.ValidationError({'session_id': 'Can only review completed sessions.'})

        request = self.context.get('request')
        if request and session.learner.user != request.user:
            raise serializers.ValidationError({'session_id': 'Only the learner can review.'})

        if hasattr(session, 'review'):
            raise serializers.ValidationError({'session_id': 'Review already exists.'})

        if request:
            data['reviewer'] = request.user.profile
        data['session'] = session
        data['reviewee'] = session.teacher
        return data

    def create(self, validated_data):
        return Review.objects.create(**validated_data)
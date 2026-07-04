import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillswap.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Profile
from skills.models import SkillCategory, Skill, SkillOffer, Session, Review
from datetime import date, time, timedelta
from django.utils import timezone

def add_sample_data():
    print("Adding sample data...")
    
    # Create sample users if they don't exist
    users_data = [
        {'username': 'john_teacher', 'email': 'john@example.com', 'password': 'password123', 'first_name': 'John', 'last_name': 'Smith'},
        {'username': 'jane_learner', 'email': 'jane@example.com', 'password': 'password123', 'first_name': 'Jane', 'last_name': 'Doe'},
        {'username': 'mike_teacher', 'email': 'mike@example.com', 'password': 'password123', 'first_name': 'Mike', 'last_name': 'Johnson'},
        {'username': 'sarah_learner', 'email': 'sarah@example.com', 'password': 'password123', 'first_name': 'Sarah', 'last_name': 'Williams'},
    ]
    
    created_users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
            }
        )
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f"Created user: {user.username}")
        created_users.append(user)
    
    # Update profiles with roles
    for user in created_users:
        profile = user.profile
        if 'teacher' in user.username:
            profile.role = 'teacher'
            profile.is_approved_teacher = True
            profile.bio = f"Experienced {user.first_name} with 5+ years of teaching experience. Passionate about sharing knowledge!"
            profile.location = "New York, USA"
        else:
            profile.role = 'learner'
            profile.bio = f"{user.first_name} is eager to learn new skills and grow professionally."
            profile.location = "Los Angeles, USA"
        profile.save()
        print(f"Updated profile for: {user.username}")
    
    # Create skill categories
    categories_data = [
        {'name': 'Programming', 'description': 'Learn coding and software development', 'icon': 'fas fa-code'},
        {'name': 'Design', 'description': 'Graphic design, UI/UX, and creative skills', 'icon': 'fas fa-palette'},
        {'name': 'Business', 'description': 'Marketing, finance, and entrepreneurship', 'icon': 'fas fa-chart-line'},
        {'name': 'Music', 'description': 'Learn instruments, vocals, and music production', 'icon': 'fas fa-music'},
        {'name': 'Language', 'description': 'Learn new languages and communication skills', 'icon': 'fas fa-language'},
    ]
    
    categories = {}
    for cat_data in categories_data:
        category, created = SkillCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        categories[cat_data['name']] = category
        print(f"Created category: {category.name}")
    
    # Create skills
    skills_data = [
        {'name': 'Python Programming', 'category': 'Programming', 'difficulty': 'beginner', 'description': 'Learn Python from scratch - perfect for beginners!'},
        {'name': 'JavaScript Development', 'category': 'Programming', 'difficulty': 'intermediate', 'description': 'Master JavaScript and build web applications'},
        {'name': 'UI/UX Design', 'category': 'Design', 'difficulty': 'intermediate', 'description': 'Learn user interface and user experience design principles'},
        {'name': 'Digital Marketing', 'category': 'Business', 'difficulty': 'beginner', 'description': 'Master SEO, social media, and content marketing'},
        {'name': 'Guitar Basics', 'category': 'Music', 'difficulty': 'beginner', 'description': 'Learn to play guitar from experienced musicians'},
        {'name': 'Spanish Language', 'category': 'Language', 'difficulty': 'beginner', 'description': 'Learn conversational Spanish quickly'},
        {'name': 'Data Science', 'category': 'Programming', 'difficulty': 'advanced', 'description': 'Advanced data analysis and machine learning'},
        {'name': 'Video Editing', 'category': 'Design', 'difficulty': 'intermediate', 'description': 'Learn Adobe Premiere Pro and video production'},
    ]
    
    skills = {}
    for skill_data in skills_data:
        skill, created = Skill.objects.get_or_create(
            name=skill_data['name'],
            defaults={
                'category': categories[skill_data['category']],
                'difficulty': skill_data['difficulty'],
                'description': skill_data['description']
            }
        )
        skills[skill_data['name']] = skill
        print(f"Created skill: {skill.name}")
    
    # Create skill offers (teaching offers)
    teacher_users = User.objects.filter(username__contains='teacher')
    offers_data = [
        {'teacher': 'john_teacher', 'skill': 'Python Programming', 'hourly_rate': 50, 'description': 'Expert Python tutor with 5 years experience. I teach Python for web development, data science, and automation.'},
        {'teacher': 'john_teacher', 'skill': 'Data Science', 'hourly_rate': 75, 'description': 'Advanced data science training including pandas, numpy, and machine learning.'},
        {'teacher': 'mike_teacher', 'skill': 'JavaScript Development', 'hourly_rate': 60, 'description': 'Full-stack JavaScript developer. Learn React, Node.js, and modern web development.'},
        {'teacher': 'mike_teacher', 'skill': 'UI/UX Design', 'hourly_rate': 55, 'description': 'Professional UI/UX designer. Learn Figma, Adobe XD, and design thinking.'},
    ]
    
    for offer_data in offers_data:
        teacher = User.objects.get(username=offer_data['teacher'])
        skill = skills[offer_data['skill']]
        offer, created = SkillOffer.objects.get_or_create(
            teacher=teacher.profile,
            skill=skill,
            defaults={
                'hourly_rate': offer_data['hourly_rate'],
                'description': offer_data['description'],
                'available_days': 'Monday to Friday',
                'available_times': '9 AM - 6 PM EST',
                'is_active': True
            }
        )
        if created:
            print(f"Created offer: {teacher.username} teaching {skill.name}")
    
    # Create sessions (booked sessions)
    learner_users = User.objects.filter(username__contains='learner')
    teacher_users_list = list(teacher_users)
    learner_users_list = list(learner_users)
    
    # Create some past sessions
    for i in range(5):
        if teacher_users_list and learner_users_list:
            teacher = teacher_users_list[i % len(teacher_users_list)]
            learner = learner_users_list[i % len(learner_users_list)]
            skill = list(skills.values())[i % len(skills)]
            
            session_date = timezone.now().date() - timedelta(days=i)
            session_time = time(10, 0)
            
            session, created = Session.objects.get_or_create(
                teacher=teacher.profile,
                learner=learner.profile,
                skill=skill,
                scheduled_date=session_date,
                scheduled_time=session_time,
                defaults={
                    'duration': 60,
                    'status': 'completed',
                    'notes': f'Session {i+1} - Great learning experience!'
                }
            )
            if created:
                print(f"Created session: {teacher.username} teaching {learner.username} - {skill.name}")
    
    # Create reviews
    for session in Session.objects.filter(status='completed')[:3]:
        if not hasattr(session, 'review'):
            review, created = Review.objects.get_or_create(
                session=session,
                defaults={
                    'reviewer': session.learner,
                    'reviewee': session.teacher,
                    'rating': 4 + (session.id % 2),  # 4 or 5 stars
                    'comment': f"Excellent session! {session.teacher.user.username} is a great teacher. Very knowledgeable and patient."
                }
            )
            if created:
                print(f"Created review for session: {session.id}")
    
    print("\n" + "="*50)
    print("SAMPLE DATA ADDED SUCCESSFULLY!")
    print("="*50)
    print("\nYou can now login with:")
    print("Teacher accounts: john_teacher / password123")
    print("                 mike_teacher / password123")
    print("\nLearner accounts: jane_learner / password123")
    print("                  sarah_learner / password123")
    print("\nAdmin: createsuperuser credentials you created earlier")
    print("\nVisit: http://127.0.0.1:8000/ to see your frontend!")

if __name__ == '__main__':
    add_sample_data()



# Teacher Login:
# Username: john_teacher
# Password: password123

# Learner Login:
# Username: jane_learner  
# Password: password123
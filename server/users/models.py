import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from shortuuid.django_fields import ShortUUIDField
from django.db.models.signals import post_save
from django.utils.html import mark_safe
from django.conf import settings
from django.contrib.admin.models import LogEntry


class User(AbstractUser):
    # groups = models.ManyToManyField(
    #     Group,
    #     related_name='custom_user_set',  # Change this to avoid conflict
    #     blank=True,
    #     help_text='The groups this user belongs to.',
    #     verbose_name='groups',
    # )
    # user_permissions = models.ManyToManyField(
    #     Permission,
    #     related_name='custom_user_permissions_set',  # Change this to avoid conflict
    #     blank=True,
    #     help_text='Specific permissions for this user.',
    #     verbose_name='user permissions',
    # )
    
    username = models.CharField(unique=True, max_length=100)
    email = models.EmailField(unique=True)
    full_name = models.CharField(unique=True, max_length=100)
    phone = models.CharField(unique=True, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        email_username, mobile = self.email.split('@')
        if self.full_name == "" or self.full_name == None:
             self.full_name = self.email
        if self.username == "" or self.username == None:
             self.username = email_username
        super(User, self).save(*args, **kwargs)


    # def delete(self, *args, **kwargs):
    #     # Delete log entries related to this user
    #     LogEntry.objects.filter(user_id=self.pk).delete()
    #     super(User, self).delete(*args, **kwargs)


GENDER = (
    ("female", "Female"),
    ("male", "Male"),
)

class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profiles')
    image = models.ImageField(upload_to='accounts/users', default='default/default-user.jpg', null=True, blank=True)
    full_name = models.CharField(max_length=1000, null=True, blank=True)
    about = models.TextField( null=True, blank=True)
    
    gender = models.CharField(max_length=500, choices=GENDER, null=True, blank=True)
    country = models.CharField(max_length=1000, null=True, blank=True)
    city = models.CharField(max_length=500, null=True, blank=True)
    state = models.CharField(max_length=500, null=True, blank=True)
    address = models.CharField(max_length=1000, null=True, blank=True)
    newsletter = models.BooleanField(default=False)
    # wishlist = models.ManyToManyField("store.Product", blank=True)
    type = models.CharField(max_length=500, choices=GENDER, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    pid = ShortUUIDField(length=10, max_length=50, alphabet="abcdefghijklmnopqrstuvxyz", default=uuid.uuid4)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        if self.full_name:
            return str(self.full_name)
        else:
            return str(self.user.full_name)
    
    def save(self, *args, **kwargs):
        if self.full_name == "" or self.full_name == None:
             self.full_name = self.user.full_name
        
        super(Profile, self).save(*args, **kwargs)

    def thumbnail(self):
        return mark_safe('<img src="/media/%s" width="50" height="50" object-fit:"cover" style="border-radius: 30px; object-fit: cover;" />' % (self.image))



def create_user_profile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)

# def save_user_profile(sender, instance, **kwargs):
# 	instance.profile.save()

def save_user_profile(sender, instance, **kwargs):
    try:
        # Get the first related Profile object
        profile = Profile.objects.filter(user=instance).first()
        if profile:
            profile.save()
    except Profile.DoesNotExist:
        # This case shouldn't occur as we create the profile during user creation
        pass

post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)
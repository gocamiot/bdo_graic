from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType
import getpass
import re

User = get_user_model()

class Command(BaseCommand):
    help = 'Create an audit user with specific permissions.'

    def validate_email(self, email):
        regex_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(regex_pattern, email)

    def handle(self, *args, **options):

        while True:
            username = input("Username: ")
            if username.strip() == "":
                print("\033[91mUsername cannot be empty\033[0m")
            elif User.objects.filter(username=username).exists():
                print("\033[91mUsername already exists\033[0m")
            else:
                break
        
        email = ""
        while True:
            email = input("Email: ")
            if email.strip() == "":
                break
            elif not self.validate_email(email):
                print("\033[91mInvalid email address\033[0m")
            elif User.objects.filter(email=email).exists():
                print("\033[91mEmail address already exists\033[0m")
            else:
                break
        
        while True:
            password = getpass.getpass("Password: ")
            if password.strip() == "":
                print("\033[91mPassword cannot be empty\033[0m")
            else:
                confirm_password = getpass.getpass("Re-type Password: ")
                if confirm_password.strip() == "":
                    print("\033[91mConfirmation password cannot be empty\033[0m")
                elif password != confirm_password:
                    print("\033[91mPasswords do not match\033[0m")
                else:
                    break
        

        user = User.objects.create_superuser(
            username=username, 
            email=email,
            is_audituser=True
        )
        user.set_password(password)
        user.save()

        content_type = ContentType.objects.get_for_model(User)
        permission, created = Permission.objects.get_or_create(
            codename='can_see_tamper_reports',
            content_type=content_type,
            defaults={'name': 'Can see tamper reports'}
        )
        user.user_permissions.add(permission)

        print("Audit user created successfully")



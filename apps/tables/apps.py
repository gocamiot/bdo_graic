from django.apps import AppConfig
from django.db import OperationalError, connection

class TablesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tables"
    def ready(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
                cursor.execute('CREATE EXTENSION IF NOT EXISTS "postgis";')
        except Exception as e:
            print(f"⚠️ Could not ensure PostgreSQL extensions: {e}")

        from background_task.models import Task
        from .tasks import encrypt_existing_fields
        def table_exists(table_name):
            with connection.cursor() as cursor:
                if connection.vendor == 'postgresql':
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT 1 
                            FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """, [table_name])
                    return cursor.fetchone()[0]
                elif connection.vendor == 'sqlite':
                    cursor.execute("""
                        SELECT name 
                        FROM sqlite_master 
                        WHERE type='table' 
                        AND name=%s
                    """, [table_name])
                    return cursor.fetchone() is not None
                elif connection.vendor == 'mssql':
                    cursor.execute("""
                        SELECT CASE 
                            WHEN EXISTS (
                                SELECT 1 
                                FROM INFORMATION_SCHEMA.TABLES 
                                WHERE TABLE_NAME = %s
                            ) THEN 1 ELSE 0 END
                    """, [table_name])
                    return cursor.fetchone()[0] == 1

        try:
            if table_exists('background_task') and not Task.objects.filter(task_name='apps.tables.tasks.encrypt_existing_fields').exists():
                encrypt_existing_fields(repeat=1800) 
        except OperationalError:
            pass
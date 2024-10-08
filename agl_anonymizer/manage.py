#!/nix/store/lpi16513bai8kg2bd841745vzk72475x-python3-3.11.9/bin/python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agl_anonymizer.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
        # Override default port for `runserver` command
    from django.core.management.commands.runserver import Command as runserver
    runserver.default_port = "8081"
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

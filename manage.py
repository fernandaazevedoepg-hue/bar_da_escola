#!/usr/bin/env python
import os, sys
def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'personal_page.settings')
    from django.core.management import execute_from_command_line
    from django.core.management.commands.runserver import Command as runserver
    runserver.default_port = "5000"
    execute_from_command_line(sys.argv)
if __name__ == '__main__':
    main()

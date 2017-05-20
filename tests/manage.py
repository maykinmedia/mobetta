#!/usr/bin/env python
import os
import sys

# add parent dir to sys path
pardir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir)
)
sys.path.insert(0, pardir)

if __name__ == "__main__":
    os.environ["DJANGO_SETTINGS_MODULE"] = "settings"

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

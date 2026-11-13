import os
import shlex
import shutil
import subprocess


def sync_dependencies(config):
    command = [shutil.which('uv') or 'uv', 'sync', '--locked', '--no-dev', '--inexact']
    if os.name == 'nt':
        command = subprocess.list2cmdline(command)
    else:
        command = ' '.join(shlex.quote(argument) for argument in command)
    config.execute(command)

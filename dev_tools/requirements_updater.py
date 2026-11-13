import os
import subprocess

import tomli

from deploy.AidLux.requirements_generator import aidlux_requirements_generate
from deploy.docker.requirements_generator import docker_requirements_generate
from deploy.headless.requirements_generator import headless_requirements_generate

# Ensure running in Alas root folder
os.chdir(os.path.join(os.path.dirname(__file__), '../'))


def requirements_export():
    subprocess.run([
        'uv', 'export', '--locked', '--no-dev', '--no-hashes', '--no-annotate',
        '--no-emit-project', '--output-file', 'requirements.txt',
    ], check=True, stdout=subprocess.DEVNULL)
    with open('pyproject.toml', 'rb') as file:
        dependencies = tomli.load(file)['project']['dependencies']
    with open('requirements-in.txt', 'w', encoding='utf-8', newline='\n') as file:
        file.write('# Generated from pyproject.toml by uv run python -m dev_tools.requirements_updater\n')
        for dependency in dependencies:
            file.write(dependency.split(';', 1)[0].strip() + '\n')


def _requirements_modify(text: str) -> str:
    """
    Modify dependency names
    zope-event -> zope.event
    zope-interface -> zope.interface

    zope-event and zope-interface will cause errors in low version of pip.

    ERROR: Could not install packages due to an EnvironmentError:
    [WinError 5] Access is denied: '....\\zope\\interface\\_zope_interface_coptimizations.cp37-win_amd64.pyd'
    Consider using the `--user` option or check the permissions.
    """
    text = text.replace('zope-event', 'zope.event')
    text = text.replace('zope-interface', 'zope.interface')
    return text


def requirements_modify(file='requirements.txt'):
    print(f'requirements_modify: {file}')
    with open(file, 'r', encoding='utf-8') as f:
        text = f.read()

    text = _requirements_modify(text)

    with open(file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


if __name__ == '__main__':
    requirements_export()
    requirements_modify()
    aidlux_requirements_generate()
    docker_requirements_generate()
    headless_requirements_generate()

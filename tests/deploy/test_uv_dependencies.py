import os
import shlex
import subprocess
from unittest.mock import Mock, patch

import pytest

from deploy.pip import PipManager
from deploy.Windows.pip import PipManager as WindowsPipManager
from deploy.uv import sync_dependencies


@pytest.mark.parametrize('manager_class', [PipManager, WindowsPipManager])
def test_default_dependencies_use_uv_lock(manager_class):
    manager = object.__new__(manager_class)
    manager.InstallDependencies = True
    manager.RequirementsFile = 'requirements.txt'
    manager.execute = Mock()
    with patch('deploy.uv.sync_dependencies') as sync:
        manager.pip_install()
    sync.assert_called_once_with(manager)
    manager.execute.assert_not_called()


@pytest.mark.parametrize('manager_class', [PipManager, WindowsPipManager])
def test_disabled_dependencies_do_not_sync(manager_class):
    manager = object.__new__(manager_class)
    manager.InstallDependencies = False
    manager.execute = Mock()
    with patch('deploy.uv.sync_dependencies') as sync:
        manager.pip_install()
    sync.assert_not_called()
    manager.execute.assert_not_called()


def test_uv_command_quotes_executable_and_preserves_development_packages():
    config = Mock()
    executable = 'C:/Program Files/uv/uv.exe'
    command = [executable, 'sync', '--locked', '--no-dev', '--inexact']
    expected = subprocess.list2cmdline(command) if os.name == 'nt' else shlex.join(command)
    with patch('deploy.uv.shutil.which', return_value=executable):
        sync_dependencies(config)
    config.execute.assert_called_once_with(expected)

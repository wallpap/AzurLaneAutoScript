"""确保更新始终跟随 fork，并保留用户指定的其它仓库。"""
import unittest

from deploy.config import DeployConfig
from deploy.Windows.config import DeployConfig as WindowsDeployConfig

FORK = "https://github.com/wallpap/AzurLaneAutoScript"


class RepositoryDefaultsTest(unittest.TestCase):
    def redirect(self, cls, repository):
        config = object.__new__(cls)
        config.config = {"Repository": repository}
        config.Repository = repository
        config.config_redirect()
        return config

    def test_fork_is_default_for_both_installers(self):
        for cls in (DeployConfig, WindowsDeployConfig):
            self.assertEqual(cls.Repository, FORK)

    def test_old_sources_and_aliases_migrate_to_fork(self):
        for cls in (DeployConfig, WindowsDeployConfig):
            for repository in ("global", "cn", "https://github.com/LmeSzinc/AzurLaneAutoScript",
                               "git://git.lyoko.io/AzurLaneAutoScript"):
                config = self.redirect(cls, repository)
                self.assertEqual(config.Repository, FORK)
                self.assertEqual(config.config["Repository"], FORK)
                self.assertFalse(config.GitOverCdn)

    def test_custom_repository_is_preserved(self):
        custom = "https://github.com/example/custom-alas"
        for cls in (DeployConfig, WindowsDeployConfig):
            self.assertEqual(self.redirect(cls, custom).Repository, custom)


if __name__ == "__main__":
    unittest.main()

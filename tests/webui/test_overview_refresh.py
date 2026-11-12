"""验证自动刷新只修改发生变化的任务和日志。"""
import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

from module.webui.app import AlasGUI
from module.webui.widgets import RichLog


class OverviewRefreshTest(unittest.TestCase):
    def setUp(self):
        self.a = SimpleNamespace(command="Commission", next_run="2026-11-13 01:00:00")
        self.b = SimpleNamespace(command="Research", next_run="2026-11-13 02:00:00")
        self.config = SimpleNamespace(
            load=Mock(), get_next_task=Mock(), pending_task=[self.a, self.b], waiting_task=[])
        self.gui = SimpleNamespace(
            visible=True, alas_config=self.config, alas=SimpleNamespace(alive=False),
            _overview_task_cache={}, alas_set_group=Mock())
        self.scope = self.enterContext(patch("module.webui.app.use_scope", side_effect=lambda *a, **k: nullcontext()))
        self.button = self.enterContext(patch("module.webui.app.put_button"))
        self.remove = self.enterContext(patch("module.webui.app.remove"))
        self.js = self.enterContext(patch("module.webui.app.run_js"))
        self.text = self.enterContext(patch("module.webui.app.put_text"))
        self.enterContext(patch("module.webui.app.put_scope"))
        self.enterContext(patch("module.webui.app.t", side_effect=lambda text: text))
        self.refresh()
        for mock in (self.scope, self.button, self.remove, self.js, self.text):
            mock.reset_mock()

    # Python 3.7 的 unittest 没有 enterContext。
    def enterContext(self, manager):
        result = manager.__enter__()
        self.addCleanup(manager.__exit__, None, None, None)
        return result

    def refresh(self):
        AlasGUI.alas_update_overview_task(self.gui)

    def test_unchanged_tasks_produce_no_output(self):
        self.refresh()
        for mock in (self.scope, self.button, self.remove, self.js, self.text):
            mock.assert_not_called()

    def test_changed_time_updates_only_one_task(self):
        self.a.next_run = "2026-11-13 03:00:00"
        self.refresh()
        self.button.assert_called_once()
        cleared = [call[0][0] for call in self.scope.call_args_list if call[1].get("clear")]
        self.assertEqual(cleared, ["overview-task_pending_Commission"])
        self.js.assert_not_called()

    def test_reordering_preserves_task_contents(self):
        self.config.pending_task.reverse()
        self.refresh()
        self.button.assert_not_called()
        self.remove.assert_not_called()
        self.js.assert_called_once()

    def test_moving_task_updates_only_source_and_destination(self):
        self.config.pending_task = [self.b]
        self.config.waiting_task = [self.a]
        self.refresh()
        self.remove.assert_any_call("overview-task_pending_Commission")
        self.button.assert_called_once()
        self.assertEqual(self.gui._overview_task_cache["waiting"], [(self.a.command, self.a.next_run)])


class LogResizeTest(unittest.TestCase):
    def test_resize_reflows_only_log_and_unchanged_width_does_nothing(self):
        log = object.__new__(RichLog)
        log.console = SimpleNamespace(width=80)
        log._requested_width = None
        log._observe_width = Mock()
        log.replace = Mock()
        log.extend = Mock()
        log.render = lambda text: text
        pm = SimpleNamespace(renderables=["first"], renderables_max_length=100)
        stream = log.put_log(pm)
        next(stream)
        next(stream)
        log.replace.assert_called_once_with("first")
        log.replace.reset_mock()
        next(stream)
        log.replace.assert_not_called()
        log._requested_width = 40
        next(stream)
        self.assertEqual(log.console.width, 40)
        log.replace.assert_called_once_with("first")
        log.replace.reset_mock()
        next(stream)
        log.replace.assert_not_called()
        pm.renderables.append("second")
        next(stream)
        log.extend.assert_called_once_with("second")


if __name__ == "__main__":
    unittest.main()

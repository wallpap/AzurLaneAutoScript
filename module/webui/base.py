from pywebio.output import clear, put_button, put_html, put_scope, put_text, use_scope
from pywebio.session import defer_call, info, run_js

from module.webui.lang import t
from module.webui.utils import Icon, WebIOTaskHandler, set_localstorage


class Base:
    def __init__(self) -> None:
        self.alive = True
        # Whether window is visible
        self.visible = True
        # Device type
        self.is_mobile = info.user_agent.is_mobile
        # Task handler
        self.task_handler = WebIOTaskHandler()
        defer_call(self.stop)

    def stop(self) -> None:
        self.alive = False
        self.task_handler.stop()


class Frame(Base):
    def __init__(self) -> None:
        super().__init__()
        self.page = "Home"

    def init_aside(self, expand_menu: bool = True, name: str = None) -> None:
        """
        Call this in aside button callback function.
        Args:
            expand_menu: expand menu
            name: button name(label) to be highlight
        """
        self.visible = True
        self.task_handler.remove_pending_task()
        clear("menu")
        if expand_menu:
            self.expand_menu()
        if name:
            self.active_button("aside", name)
            set_localstorage("aside", name)

    def init_menu(self, collapse_menu: bool = True, name: str = None) -> None:
        """
        Call this in menu button callback function.
        Args:
            collapse_menu: collapse menu
            name: button name(label) to be highlight
        """
        self.visible = True
        self.page = name
        run_js("document.body.classList.remove('settings-view', 'overview-view', 'home-view', 'tool-view')")
        self.task_handler.remove_pending_task()
        clear("content")
        if collapse_menu:
            self.collapse_menu()
        if name:
            self.active_button("menu", name)

    @staticmethod
    @use_scope("ROOT", clear=True)
    def _show() -> None:
        run_js("document.body.classList.remove('settings-view', 'overview-view', 'home-view', 'tool-view', 'alas-manage', 'navigation-open')")
        put_scope(
            "header",
            [
                put_html(Icon.ALAS).style("--header-icon--"),
                put_text("Alas").style("--header-text--"),
                put_scope("header_title"),
                put_scope("header_status"),
            ],
        )
        put_scope(
            "contents",
            [
                put_scope("navigation", [put_scope("aside"), put_scope("menu")]),
                put_scope("content"),
            ],
        )
        with use_scope("header_title"):
            put_button(t("Gui.Workbench.Navigation"), onclick=Frame.toggle_navigation, color="menu").style("--navigation-toggle: 1;")
        Frame.init_navigation()

    @staticmethod
    def init_navigation():
        run_js("""
            const button = document.querySelector('[style*="--navigation-toggle:"] button');
            if (button) {
                button.setAttribute('aria-controls', 'pywebio-scope-navigation');
                button.setAttribute('aria-expanded', String(document.body.classList.contains('navigation-open')));
            }
            if (window.alasNavigationKeydown) document.removeEventListener('keydown', window.alasNavigationKeydown);
            window.alasNavigationKeydown = event => {
                if (event.key === 'Escape' && document.body.classList.contains('navigation-open')) {
                    document.body.classList.remove('navigation-open');
                    const toggle = document.querySelector('[style*="--navigation-toggle:"] button');
                    if (toggle) { toggle.setAttribute('aria-expanded', 'false'); toggle.focus(); }
                }
            };
            document.addEventListener('keydown', window.alasNavigationKeydown);
        """)

    @staticmethod
    def toggle_navigation():
        run_js("const open = document.body.classList.toggle('navigation-open');"
               "document.querySelectorAll('[style*=\"--navigation-toggle:\"] button').forEach(button => {"
               "button.setAttribute('aria-expanded', String(open));"
               "button.setAttribute('aria-controls', 'pywebio-scope-navigation'); });")

    @staticmethod
    @use_scope("header_title", clear=True)
    def set_title(text=""):
        put_text(text)
        put_button(t("Gui.Workbench.Navigation"), onclick=Frame.toggle_navigation, color="menu").style("--navigation-toggle: 1;")
        Frame.init_navigation()

    @staticmethod
    def collapse_menu() -> None:
        run_js(
            "document.body.classList.remove('navigation-open');"
            "document.querySelectorAll('[style*=\"--navigation-toggle:\"] button').forEach(button => button.setAttribute('aria-expanded', 'false'));"
        )

    @staticmethod
    def expand_menu() -> None:
        run_js(
            "if (window.matchMedia('(max-width: 760px)').matches) {"
            "document.body.classList.add('navigation-open');"
            "document.querySelectorAll('[style*=\"--navigation-toggle:\"] button').forEach(button => button.setAttribute('aria-expanded', 'true')); }"
        )

    @staticmethod
    def active_button(position, value) -> None:
        run_js(
            f"""
            $("button.btn-{position}").removeClass("btn-{position}-active");
            $("div[style*='--{position}-{value}--']>button").addClass("btn-{position}-active");
        """
        )

    @staticmethod
    def pin_set_invalid_mark(keys) -> None:
        if isinstance(keys, str):
            keys = [keys]
        keys = ["_".join(key.split(".")) for key in keys]
        js = "".join(
            [
                f"""$(".form-control[name='{key}']").addClass('is-invalid');"""
                for key in keys
            ]
        )
        if js:
            run_js(js)
        # for key in keys:
        #     pin_update(key, valid_status=False)

    @staticmethod
    def pin_remove_invalid_mark(keys) -> None:
        if isinstance(keys, str):
            keys = [keys]
        keys = ["_".join(key.split(".")) for key in keys]
        js = "".join(
            [
                f"""$(".form-control[name='{key}']").removeClass('is-invalid');"""
                for key in keys
            ]
        )
        if js:
            run_js(js)
        # for key in keys:
        # pin_update(key, valid_status=0)

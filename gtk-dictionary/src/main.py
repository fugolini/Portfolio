import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib

from ui import DictionaryUI


class DictionaryApp(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id="it.vocabolario.app", flags=Gio.ApplicationFlags.FLAGS_NONE
        )

    def do_startup(self) -> None:
        """Startup"""
        Gtk.Application.do_startup(self)
        self.logger = setup_logging()

        GLib.set_prgname("vocabolario")
        Gtk.Window.set_default_icon_name("vocabolario")
        GLib.set_application_name("Vocabolario")

        self.logger.info("--- Session started ---")

    def do_activate(self) -> None:
        """Main system handler"""
        # If a window is open bring focus back to it
        win = self.get_active_window()
        if not win:
            win = DictionaryUI(self)
        win.present()


if __name__ == "__main__":
    from config import setup_logging

    setup_logging()

    app = DictionaryApp()
    sys.exit(app.run(sys.argv))

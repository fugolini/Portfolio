from pathlib import Path
from typing import Optional
import logging

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gtk, Gdk, WebKit2, GObject

from config import PLACEHOLDER_PATH, GTK_CSS_PATH
from database import DictionaryDAO
from history_manager import HistoryManager

logger = logging.getLogger(__name__)


class DictionaryResultRow(Gtk.ListBoxRow):
    """Custom ListBoxRow to store additional attributes"""

    def __init__(self, headword: str, filename: str) -> None:
        super().__init__()
        self.headword = headword
        self.filename = filename

        label = Gtk.Label(label=headword, xalign=0)
        label.get_style_context().add_class("results-entry")

        self.add(label)
        # Gtk widgets are hidden by default
        self.show_all()


class DictionaryUI(Gtk.ApplicationWindow):
    """The main user interface"""

    def __init__(self, app: Gtk.Application) -> None:

        super().__init__(application=app, title="Vocabolario")
        self.set_default_size(900, 600)

        # Create the dictionary data access object
        self.dictionary_dao = DictionaryDAO()
        # Create history
        self.history = HistoryManager()
        # The current entry regardless of whether it will be saved
        # in the history (necessary for internal links)
        self.current_filename = None
        # The placeholder for the HTML view
        self.html_placeholder = PLACEHOLDER_PATH.read_text(encoding="utf-8")

        self._build_interface()
        self._inject_js()
        self._create_keyboard_shortcuts()

    # --- Main interface builders ---
    def _build_interface(self) -> None:
        """Draw the interface as a whole"""
        # Load the provider that manages Gtk's CSS
        self._load_css_provider()
        # Draw main vertical box (the main canvas) and add it to the window
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Draw horizontal box (results + HTML)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Draw all widgets
        top_bar = self._draw_top_bar()
        results_scroll = self._draw_results_scroll()
        bottom_right_pane = self._draw_bottom_right_pane()

        # Position bottom panes in the horizontal box
        hbox.pack_start(results_scroll, False, True, 0)
        hbox.pack_start(bottom_right_pane, True, True, 0)

        # Position top and bottom panes
        vbox.pack_start(top_bar, False, False, 0)
        vbox.pack_start(hbox, True, True, 0)

        # Show all widgets
        self.show_all()

        logger.info("Interface built correctly")

    def _draw_bottom_right_pane(self) -> Gtk.Box:
        """Manage the layout of the bottom-right section"""
        # The bottom-right box in its entirety
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        # The header box above the HTML view
        header_box = self._draw_header_box()

        # ABOVE: the widgets in the header bar
        self._draw_history_arrows()
        separator = self._draw_separator()
        # Spacer that expands dynamically and pushes sticher to the right
        spacer = Gtk.Box()
        stack_switcher = self._draw_stack_switcher()

        # Place arrows, separator, spacer and switcher (tabs) in the header bar
        header_box.pack_start(self.back_arrow, False, False, 0)
        header_box.pack_start(separator, False, False, 6)
        header_box.pack_start(self.forward_arrow, False, False, 0)
        header_box.pack_start(spacer, True, True, 0)
        header_box.pack_start(stack_switcher, False, False, 0)
        header_box.pack_start(self.stack, False, False, 0)

        # BELOW: the HTML view
        self._draw_html_view()

        # Place the header box and the HTML view in the bottom-right box
        right_box.pack_start(header_box, False, False, 0)
        right_box.pack_start(self.html_view, True, True, 0)

        return right_box

    def _draw_header_box(self) -> Gtk.Box:
        """Draw the header box to fit arrows and switcher (dictionary tabs)"""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_margin_start(6)
        header_box.set_margin_end(12)
        header_box.set_margin_top(2)

        return header_box

    def _draw_html_view(self) -> None:
        """Draw the HTML browser"""
        # The content manager that handles JS and CSS
        self.content_manager = WebKit2.UserContentManager()
        # Create the HTML view and assign the content manager to it
        self.html_view = WebKit2.WebView.new_with_user_content_manager(
            self.content_manager
        )

        self.html_view.set_background_color(Gdk.RGBA(0, 0, 0, 0))
        self._set_placeholder(
            "Type a word to begin", animation="fadeIn 1s ease-out"
        )
        # Connect the HTML viewer to the internal links handler
        self.html_view.connect("decide-policy", self._on_webview_decide_policy)

    def _draw_separator(self) -> Gtk.Separator:
        """Draw the separator between arrows
        NOTE: unlike a Gtk.Box(), the spacer does not expand dinamically
        """
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_top(6)
        sep.set_margin_bottom(6)
        sep.set_margin_start(20)
        sep.set_margin_end(10)

        return sep

    def _draw_history_arrows(self) -> None:
        """Draw forward and backward arrows"""

        self.back_arrow = Gtk.Button()
        self.back_arrow.set_relief(Gtk.ReliefStyle.NONE)
        self.back_arrow.add(
            Gtk.Image.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        )
        self.back_arrow.get_style_context().add_class("nav-button")

        self.forward_arrow = Gtk.Button()
        self.forward_arrow.set_relief(Gtk.ReliefStyle.NONE)
        self.forward_arrow.add(
            Gtk.Image.new_from_icon_name("go-next-symbolic", Gtk.IconSize.BUTTON)
        )
        self.forward_arrow.get_style_context().add_class("nav-button")
        # Makes row insensitive upon creation
        self.back_arrow.set_sensitive(False)
        self.forward_arrow.set_sensitive(False)

        # Connect arrows to handlers
        self.back_arrow.connect("clicked", self._on_go_back)
        self.forward_arrow.connect("clicked", self._on_go_forward)

    def _draw_stack_switcher(self) -> Gtk.StackSwitcher:
        """Draw the stack switcher that controls the stack"""
        self._create_stack()

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(self.stack)
        stack_switcher.set_halign(Gtk.Align.START)
        stack_switcher.set_valign(Gtk.Align.CENTER)
        stack_switcher.get_style_context().add_class("dict-switcher")

        for dictionary in self.dictionary_dao.dictionaries:
            tab_box = Gtk.Box()
            self.stack.add_titled(tab_box, dictionary["name"], dictionary["label"])

        # Set the first visible tab
        self.stack.set_visible_child_name(self.dictionary_dao.dictionaries[0]["name"])

        return stack_switcher

    def _create_stack(self) -> None:
        """Create the stack"""
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)
        self.stack.connect("notify::visible-child", self._on_stack_changed)

    def _draw_top_bar(self) -> Gtk.Box:
        """Draw the top bar (search area)"""
        search_box = self._draw_search_box()
        results_label = self._draw_results_label()

        # The search entry
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Cerca...")
        self.search_entry.set_width_chars(30)
        # Connect the search entry to its handler
        self.search_entry.connect("changed", self._on_search_changed)

        # Position label and search entry in the search box
        search_box.pack_start(results_label, False, False, 0)
        search_box.pack_end(self.search_entry, False, False, 0)

        return search_box

    def _draw_search_box(self) -> Gtk.Box:
        """Draw the box for the search entry"""
        # Build the box
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        # Position of the box
        search_box.set_margin_start(12)
        search_box.set_margin_end(12)
        search_box.set_margin_top(35)
        search_box.set_margin_bottom(8)
        # Separator between navigation and tabs
        search_box.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 6
        )

        return search_box

    def _draw_results_label(self) -> Gtk.Label:
        """Draw the label above the results scroll"""
        results_label = Gtk.Label(label="lemmi")
        # Center the text within the label's allocated 200px space
        results_label.set_xalign(0.5)
        results_label.set_yalign(0.5)
        results_label.set_size_request(200, -1)
        results_label.set_halign(Gtk.Align.CENTER)
        results_label.set_valign(Gtk.Align.CENTER)
        results_label.get_style_context().add_class("lemmi-tag")  # For CSS styling
        results_label.set_markup('<span size="13288">L</span>emmata')

        return results_label

    def _draw_results_scroll(self) -> Gtk.ScrolledWindow:
        """Draw the area where search results are displayed"""
        # Build the container for the list of results
        results_scroll = Gtk.ScrolledWindow()
        results_scroll.set_name("results-pane")
        results_scroll.set_min_content_width(200)

        # The result list itself
        self.results_list = Gtk.ListBox()
        # Connect the result list to its handler
        self.results_list.connect("row-activated", self._on_row_activated)

        # Place the result list in the result container
        results_scroll.add(self.results_list)

        return results_scroll

    # --- Interface helpers ---
    def _load_css_provider(self) -> None:
        """Load the provider that will style the widgets via CSS"""
        provider = Gtk.CssProvider()
        provider.load_from_data(self._load_gtk_css())

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _load_gtk_css(self) -> Optional[str]:
        """Load the CSS that styles the window"""
        try:
            with open(GTK_CSS_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.exception("GTK CSS not found")
        except Exception as e:
            logger.exception(f"Unforeseen event: {e}")

    def _inject_js(self) -> None:
        """Add dictionary-specific CSS and JS"""
        styles = self.dictionary_dao.get_current_styles()

        user_script = WebKit2.UserScript(
            styles["js"],
            WebKit2.UserContentInjectedFrames.ALL_FRAMES,
            WebKit2.UserScriptInjectionTime.END,
        )

        self.content_manager.add_script(user_script)

    def _set_placeholder(self, message: str, animation="none") -> None:
        """Display all placeholders (styled)"""
        placeholder = self.html_placeholder.replace("{{MESSAGE}}", message).replace(
            "{{ANIMATION}}", animation
        )
        self.html_view.load_html(placeholder, "file://")

    def _clear_rows(self) -> None:
        """Clear the rows of the results scroll"""
        for row in self.results_list.get_children():
            self.results_list.remove(row)

    # --- Core functionalities ---
    def _display_entry(self, filename: str, add_to_history=True) -> None:
        """Display an entry and assess whether to add it to the history"""
        # Retrieve entry HTML and fielpath as URI from the DAO
        html_data = self.dictionary_dao.fetch_word_html(filename)

        if html_data:
            self.current_filename = filename
            if add_to_history:
                self.history.add(filename)

            # html_data[0] = HTML content (styled)
            # html_data[1] = filepath
            self.html_view.load_html(html_data[0], html_data[1])
            # Update history buttons
            self._update_history_buttons()

    def _switch_dictionary(self, name: str) -> None:
        """Switch database path, CSS and JS"""
        # If the dictionary is the same
        if name == self.dictionary_dao.current_dictionary["name"]:
            return

        self.history.clear_history()

        dictionary = next(
            d for d in self.dictionary_dao.dictionaries if d["name"] == name
        )

        self.dictionary_dao.current_dictionary = dictionary
        # Open the new dictionary
        self.dictionary_dao.open_dictionary()

        # Flush previously injected JS
        self.content_manager.remove_all_scripts()
        # Add new CSS and JS
        self._inject_js()
        # Search the word and redraw the rows
        self._on_search_changed()

    def _update_history_buttons(self) -> None:
        # Update history buttons according to history
        self.back_arrow.set_sensitive(self.history.can_go_back())
        self.forward_arrow.set_sensitive(self.history.can_go_forward())

    # --- Signals handlers ---
    def _on_go_back(self, button: Gtk.Button) -> None:
        """Handle the back arrow"""
        filename = self.history.back()
        if filename:
            self._display_entry(filename, add_to_history=False)
        self._update_history_buttons()

    def _on_go_forward(self, button: Gtk.Button):
        """Handle the forward arrow"""
        filename = self.history.forward()
        if filename:
            self._display_entry(filename, add_to_history=False)
        self._update_history_buttons()

    def _on_row_activated(self, listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        """Handle the results scroll"""
        self._display_entry(row.filename)

    def _on_search_changed(self, *args) -> None:
        """Update the results whenever the text in the search entry changes
        NOTE: a second argument is necessary as Gtk signature
        """
        query = self.search_entry.get_text().strip()

        # Clear old results
        self._clear_rows()

        # If the search entry is empty
        if not query:
            return

        results = self.dictionary_dao.search(query)

        if not results:
            self._set_placeholder("No results found")
            return

        # Populate results list
        for headword, filename in results:
            row = DictionaryResultRow(headword, filename)
            self.results_list.add(row)

        self.results_list.show_all()
        top_file = results[0][1]
        # html_entry, filepath = self.dictionary_dao.fetch_word_html(top_file, add_to_history=False)
        self._display_entry(top_file, add_to_history=False)

    def _on_focus_search(self, *args) -> bool:
        self.search_entry.grab_focus()
        self.search_entry.select_region(0, -1)
        return True

    def _on_stack_changed(self, stack: Gtk.Stack, pspec: GObject.ParamSpec) -> None:
        """
        Detect changes in the stack (tabs)
        NOTE: pspec is part of the Gtk signal-function signature
        """
        name = stack.get_visible_child_name()
        self._switch_dictionary(name)

    def _on_cycle_tabs(self, *args) -> bool:
        """Cycle through dictionary tabs"""
        children = self.stack.get_children()
        if not children:
            return True

        current_visible = self.stack.get_visible_child()

        # Find the current tab and jump to the next one
        try:
            current_idx = children.index(current_visible)
            # Modulo, e.g.: (0 + 1) % 3 = 1 --> jump to first tab, etc.
            next_idx = (current_idx + 1) % len(children)

            # Activate new tab
            self.stack.set_visible_child(children[next_idx])

            # Bring focus back to the search entry
            self.search_entry.grab_focus()
        except ValueError:
            pass

        return True

    def _on_key_pressed(self, widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        """Intercepts the TAB key"""
        # Gdk.KEY_Tab è il nome della costante per il tasto Tab
        if event.keyval == Gdk.KEY_Tab:
            # Eseguiamo il ciclo dei dizionari
            self._on_cycle_tabs()
            # IMPORTANTE: restituendo True, fermiamo la propagazione.
            # GTK non sposterà il focus tra i widget.
            return True

        return False

    def _on_webview_decide_policy(
        self,
        webview: WebKit2.WebView,
        decision: WebKit2.PolicyDecision,
        decision_type: WebKit2.PolicyDecisionType,
    ) -> bool:
        """Handle x-dictionary:d: cross references (internal links)"""
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            nav_action = decision.get_navigation_action()
            request = nav_action.get_request()
            uri = request.get_uri()

            # Handle the custom dictionary scheme
            if uri.startswith("x-dictionary:d:"):
                # Get the referenced word
                word = uri.split(":")[-1]

                results = self.dictionary_dao.search(word)
                if results:
                    # Select first result
                    best_filename = results[0][1]
                    last_saved = None
                    if self.history.storage:
                        last_saved = self.history.storage[self.history.index]

                    if (
                        getattr(self, "current_filename", None)
                        and self.current_filename != last_saved
                    ):
                        self.history.add(self.current_filename)

                    self._display_entry(best_filename, add_to_history=True)
                else:
                    self._set_placeholder("No results found")
                return True
        # Let WebKit handle other URLs normally
        return False

    # --- Shortcuts ---
    def _create_keyboard_shortcuts(self) -> None:
        """Define keyboard shortcuts"""
        self.accel_group = Gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        # CTRL + F to jump to the search box
        key, mod = Gtk.accelerator_parse("<Primary>f")
        self.accel_group.connect(
            key, mod, Gtk.AccelFlags.VISIBLE, self._on_focus_search
        )

        # CTRL + TAB (Cycle Dictionaries)
        # Note: TAB has absolute priority in GTK, hence an accel group won't do it
        self.connect("key-press-event", self._on_key_pressed)

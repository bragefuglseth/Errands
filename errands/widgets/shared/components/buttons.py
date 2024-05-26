# Copyright 2024 Vlad Krupinskii <mrvladus@yandex.ru>
# SPDX-License-Identifier: MIT


from typing import Callable

from gi.repository import Gtk, GObject  # type:ignore


class ErrandsButton(Gtk.Button):
    def __init__(self, on_click: Callable = None, **kwargs) -> None:
        super().__init__(**kwargs)
        if on_click:
            self.connect("clicked", on_click)


class ErrandsCheckButton(Gtk.CheckButton):
    def __init__(self, on_toggle: Callable = None, **kwargs) -> None:
        super().__init__(**kwargs)
        if on_toggle:
            self.connect("toggled", on_toggle)


class ErrandsToggleButton(Gtk.ToggleButton):
    def __init__(self, on_toggle: Callable = None, **kwargs) -> None:
        super().__init__(**kwargs)
        if on_toggle:
            self.connect("toggled", on_toggle)


class ErrandsSpinButton(Gtk.SpinButton):
    def __init__(self, on_value_changed: Callable = None, **kwargs) -> None:
        super().__init__(**kwargs)
        if on_value_changed:
            self.connect("value-changed", on_value_changed)


class ErrandsInfoButton(Gtk.MenuButton):
    """Button with text inside a popover"""

    def __init__(self, info_text: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_valign(Gtk.Align.CENTER)
        self.set_icon_name("errands-info-symbolic")
        self.set_tooltip_text(_("Info"))
        self.add_css_class("flat")
        self.set_popover(
            Gtk.Popover(
                child=Gtk.Label(
                    label=info_text,
                    use_markup=True,
                    wrap_mode=0,
                    wrap=True,
                    max_width_chars=20,
                    margin_bottom=6,
                    margin_top=6,
                    margin_end=3,
                    margin_start=3,
                )
            )
        )


class ErrandsSearchButton(Gtk.ToggleButton):
    def __init__(self, search_bar: Gtk.SearchBar, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_icon_name("errands-search-symbolic")
        self.set_tooltip_text(_("Toggle Search"))
        self.bind_property(
            "active",
            search_bar,
            "search-mode-enabled",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )
        shortcut_ctrl = Gtk.ShortcutController(scope=Gtk.ShortcutScope.GLOBAL)
        shortcut_ctrl.add_shortcut(
            Gtk.Shortcut(
                action=Gtk.ShortcutAction.parse_string("activate"),
                trigger=Gtk.ShortcutTrigger.parse_string("<Control>f"),
            )
        )
        self.add_controller(shortcut_ctrl)

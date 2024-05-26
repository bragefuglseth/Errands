# Copyright 2024 Vlad Krupinskii <mrvladus@yandex.ru>
# SPDX-License-Identifier: MIT


from typing import Callable

from gi.repository import Adw, Gtk

from errands.state import State  # type:ignore


class ErrandsEntryRow(Adw.EntryRow):
    def __init__(self, on_entry_activated: Callable, **kwargs) -> None:
        super().__init__(**kwargs)
        self.connect("entry-activated", on_entry_activated)


class ErrandsEntry(Gtk.Entry):
    def __init__(self, on_activate: Callable, **kwargs) -> None:
        super().__init__(**kwargs)
        self.connect("activate", on_activate)


class ErrandsSearchBar(Gtk.SearchBar):
    def __init__(self, on_search_changed: Callable, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_key_capture_widget(State.task_list_page)
        search_entry = Gtk.SearchEntry(
            hexpand=True,
            search_delay=100,
            placeholder_text=_("Search by text, notes or tags"),
        )
        search_entry.connect("search-changed", on_search_changed)
        self.set_child(
            Adw.Clamp(child=search_entry, maximum_size=1000, tightening_threshold=300)
        )
        self.connect_entry(search_entry)

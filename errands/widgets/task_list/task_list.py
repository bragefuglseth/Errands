# Copyright 2024 Vlad Krupinskii <mrvladus@yandex.ru>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from gi.repository import Adw, Gtk, GLib, GObject, Gio  # type:ignore

from errands.lib.animation import scroll
from errands.lib.data import TaskData, TaskDataGObject, UserData
from errands.lib.gsettings import GSettings
from errands.lib.logging import Log
from errands.lib.sync.sync import Sync
from errands.lib.utils import get_children
from errands.state import State
from errands.widgets.shared.components.buttons import ErrandsButton, ErrandsToggleButton
from errands.widgets.shared.components.header_bar import ErrandsHeaderBar
from errands.widgets.shared.components.entries import ErrandsEntryRow
from errands.widgets.shared.components.toolbar_view import ErrandsToolbarView
from errands.widgets.shared.titled_separator import TitledSeparator
from errands.widgets.task import Task

if TYPE_CHECKING:
    from errands.widgets.task_list.task_list_sidebar_row import TaskListSidebarRow


class TaskList(Adw.Bin):
    def __init__(self, sidebar_row: TaskListSidebarRow) -> None:
        super().__init__()
        self.list_uid: str = sidebar_row.uid
        self.sidebar_row: TaskListSidebarRow = sidebar_row
        self.__build_ui()
        # self.__load_tasks()

    # ------ PRIVATE METHODS ------ #

    def __repr__(self) -> str:
        return f"<class 'TaskList' {self.list_uid}>"

    def __build_ui(self) -> None:
        # Title
        self.title = Adw.WindowTitle()

        # Toggle completed btn
        self.toggle_completed_btn: ErrandsToggleButton = ErrandsToggleButton(
            icon_name="errands-check-toggle-symbolic",
            valign=Gtk.Align.CENTER,
            tooltip_text=_("Toggle Completed Tasks"),
            on_toggle=self._on_toggle_completed_btn_toggled,
        )

        # Delete completed btn
        self.delete_completed_btn: ErrandsButton = ErrandsButton(
            icon_name="errands-delete-all-symbolic",
            valign=Gtk.Align.CENTER,
            tooltip_text=_("Delete Completed Tasks"),
            on_click=self._on_delete_completed_btn_clicked,
        )
        self.toggle_completed_btn.bind_property(
            "active",
            self.delete_completed_btn,
            "visible",
            GObject.BindingFlags.SYNC_CREATE,
        )

        # Scroll up btn
        self.scroll_up_btn: ErrandsButton = ErrandsButton(
            icon_name="errands-up-symbolic",
            visible=False,
            valign=Gtk.Align.CENTER,
            tooltip_text=_("Scroll Up"),
            on_click=self._on_scroll_up_btn_clicked,
        )

        self.task_list_model = Gio.ListStore(item_type=TaskDataGObject)
        for task in [t for t in UserData.tasks if t.list_uid == self.list_uid]:
            self.task_list_model.append(TaskDataGObject(task))

        self.tasks_list: Gtk.ListBox = Gtk.ListBox(
            margin_bottom=32,
            selection_mode=Gtk.SelectionMode.NONE,
            css_classes=["transparent"],
        )
        self.tasks_list.bind_model(
            self.task_list_model,
            lambda task: Gtk.ListBoxRow(
                child=Task(task.data, self), activatable=False, css_classes=["task"]
            ),
        )

        def header_func(row: Gtk.ListBoxRow, before: Gtk.ListBoxRow):
            if not before:
                row.set_header(None)
            else:
                row_cmp: int = int(row.get_child().task_data.completed)
                beffore_cmp: int = int(before.get_child().task_data.completed)
                if beffore_cmp < row_cmp:
                    row.set_header(TitledSeparator(_("Completed"), (24, 24, 0, 0)))
                else:
                    row.set_header(None)

        self.tasks_list.set_header_func(header_func)

        # Scrolled window
        self.scrl: Gtk.ScrolledWindow = Gtk.ScrolledWindow(
            child=Adw.Clamp(
                tightening_threshold=300, maximum_size=1000, child=self.tasks_list
            )
        )

        # Adjustment
        adj: Gtk.Adjustment = Gtk.Adjustment()
        adj.connect("value-changed", self._on_scroll)
        self.scrl.set_vadjustment(adj)

        # Drop controller
        self.dnd_ctrl: Gtk.DropControllerMotion = Gtk.DropControllerMotion()
        self.dnd_ctrl.connect("motion", self._on_dnd_scroll, adj)
        self.add_controller(self.dnd_ctrl)

        self.set_child(
            ErrandsToolbarView(
                top_bars=[
                    ErrandsHeaderBar(
                        start_children=[
                            self.toggle_completed_btn,
                            self.delete_completed_btn,
                        ],
                        title_widget=self.title,
                    ),
                    Adw.Clamp(
                        maximum_size=1000,
                        tightening_threshold=300,
                        child=ErrandsEntryRow(
                            margin_top=3,
                            margin_bottom=3,
                            margin_end=12,
                            margin_start=12,
                            title=_("Add new Task"),
                            activatable=False,
                            height_request=60,
                            css_classes=["card"],
                            on_entry_activated=self._on_task_added,
                        ),
                    ),
                ],
                content=self.scrl,
            )
        )

    def __load_tasks(self) -> None:
        Log.info(f"Task List {self.list_uid}: Load Tasks")

        tasks: list[TaskData] = [
            t for t in UserData.get_tasks_as_dicts(self.list_uid, "") if not t.deleted
        ]
        for task in tasks:
            new_task = Task(task, self)
            if task.completed:
                self.completed_task_list.append(new_task)
            else:
                self.uncompleted_task_list.append(new_task)

        self.toggle_completed_btn.set_active(
            UserData.get_list_prop(self.list_uid, "show_completed")
        )
        self.update_title()

    # ------ PROPERTIES ------ #

    @property
    def tasks(self) -> list[Task]:
        """Top-level Tasks"""

        return get_children(self.tasks_list)

    @property
    def all_tasks(self) -> list[Task]:
        """All tasks in the list"""

        all_tasks: list[Task] = []

        def __add_task(tasks: list[Task]) -> None:
            for task in tasks:
                all_tasks.append(task)
                __add_task(task.tasks)

        __add_task(self.tasks)
        return all_tasks

    # ------ PUBLIC METHODS ------ #

    def add_task(self, task: TaskData):
        Log.info(f"Task List: Add task '{task.uid}'")

        if GSettings.get("task-list-new-task-position-top"):
            self.task_list_model.insert(0, TaskDataGObject(task))
        else:
            self.task_list_model.append(TaskDataGObject(task))

    def purge(self) -> None:
        State.sidebar.list_box.select_row(self.sidebar_row.get_prev_sibling())
        State.sidebar.list_box.remove(self.sidebar_row)
        State.view_stack.remove(self)
        self.sidebar_row.run_dispose()
        self.run_dispose()

    # - UPDATE UI FUNCTIONS - #

    def update_title(self) -> None:
        Log.debug(f"Task List '{self.list_uid}': Update title")
        # Update title
        self.title.set_title(UserData.get_list_prop(self.list_uid, "name"))

        n_total, n_completed = UserData.get_status(self.list_uid)

        # Update headerbar subtitle
        self.title.set_subtitle(
            _("Completed:") + f" {n_completed} / {n_total}" if n_total > 0 else ""
        )

        # Update sidebar item counter
        n_uncompleted: int = n_total - n_completed
        self.sidebar_row.size_counter.set_label(
            str(n_uncompleted) if n_uncompleted > 0 else ""
        )

        # Update delete completed button
        self.delete_completed_btn.set_sensitive(n_completed > 0)

        # Update separator
        # toplevel_tasks: list[TaskData] = [
        #     t
        #     for t in UserData.get_tasks_as_dicts(self.list_uid, "")
        #     if not t.deleted and not t.trash
        # ]
        # n_completed: int = len([t for t in toplevel_tasks if t.completed])
        # n_total: int = len(toplevel_tasks)
        # self.task_lists_separator.get_child().set_visible(
        #     n_completed > 0 and n_completed != n_total
        # )

    def update_tasks(self) -> None:
        # Update tasks
        tasks: list[TaskData] = [
            t for t in UserData.get_tasks_as_dicts(self.list_uid, "") if not t.deleted
        ]
        tasks_uids: list[str] = [t.uid for t in tasks]
        widgets_uids: list[str] = [t.uid for t in self.tasks]

        # Add tasks
        for task in tasks:
            if task.uid not in widgets_uids:
                self.add_task(task)

        for task in self.tasks:
            # Remove task
            if task.uid not in tasks_uids:
                task.purge()
            # Move task to completed tasks
            elif task.task_data.completed and task in self.uncompleted_tasks:
                if (
                    len(self.uncompleted_tasks) > 1
                    and task.uid != self.uncompleted_tasks[-1].uid
                ):
                    UserData.move_task_after(
                        self.list_uid,
                        task.uid,
                        self.uncompleted_tasks[-1].uid,
                    )
                self.uncompleted_task_list.remove(task)
                self.completed_task_list.prepend(task)
            # Move task to uncompleted tasks
            elif not task.task_data.completed and task in self.completed_tasks:
                if (
                    len(self.uncompleted_tasks) > 0
                    and task.uid != self.uncompleted_tasks[-1].uid
                ):
                    UserData.move_task_after(
                        self.list_uid,
                        task.uid,
                        self.uncompleted_tasks[-1].uid,
                    )
                self.completed_task_list.remove(task)
                self.uncompleted_task_list.append(task)
            if not task.get_reveal_child() and not task.task_data.trash:
                task.toggle_visibility(True)

    def update_ui(self) -> None:
        self.update_title()
        self.update_tasks()

    # ------ SIGNAL HANDLERS ------ #

    def _on_delete_completed_btn_clicked(self, btn: Gtk.Button) -> None:
        """Hide completed tasks and move them to trash"""

        Log.info(f"Task List '{self.list_uid}': Delete completed tasks")
        for task in self.all_tasks:
            if not task.task_data.trash and task.task_data.completed:
                task.delete()
        self.update_ui()

    def _on_toggle_completed_btn_toggled(self, btn: Gtk.ToggleButton) -> None:
        if not hasattr(self, "completed_task_list"):
            return
        self.completed_task_list.set_visible(btn.get_active())
        for task in self.all_tasks:
            task.completed_task_list.set_visible(btn.get_active())
        UserData.update_list_prop(self.list_uid, "show_completed", btn.get_active())

    def _on_scroll_up_btn_clicked(self, btn: Gtk.ToggleButton) -> None:
        scroll(self.scrl, False)

    def _on_dnd_scroll(self, _motion, _x, y: float, adj: Gtk.Adjustment) -> None:
        def __auto_scroll(scroll_up: bool) -> bool:
            """Scroll while drag is near the edge"""
            if not self.scrolling or not self.dnd_ctrl.contains_pointer():
                return False
            adj.set_value(adj.get_value() - (2 if scroll_up else -2))
            return True

        MARGIN: int = 100
        if y < MARGIN:
            self.scrolling = True
            GLib.timeout_add(100, __auto_scroll, True)
        elif y > self.get_height() - MARGIN:
            self.scrolling = True
            GLib.timeout_add(100, __auto_scroll, False)
        else:
            self.scrolling = False

    def _on_scroll(self, adj: Gtk.Adjustment) -> None:
        self.scroll_up_btn.set_visible(adj.get_value() > 0)

    def _on_task_added(self, entry: Adw.EntryRow) -> None:
        text: str = entry.get_text()
        if text.strip(" \n\t") == "":
            return
        self.add_task(
            UserData.add_task(
                list_uid=self.list_uid,
                text=text,
            )
        )
        entry.set_text("")
        scroll(self.scrl, not GSettings.get("task-list-new-task-position-top"))

        self.update_title()
        Sync.sync()

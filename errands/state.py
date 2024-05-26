# Copyright 2024 Vlad Krupinskii <mrvladus@yandex.ru>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from gi.repository import Adw, Gio  # type:ignore

from errands.lib.utils import get_children

if TYPE_CHECKING:
    from errands.application import ErrandsApplication
    from errands.lib.notifications import ErrandsNotificationsDaemon
    from errands.widgets.loading_page import ErrandsLoadingPage
    from errands.widgets.shared.task_toolbar import (
        ErrandsAttachmentsWindow,
        ErrandsDateTimeWindow,
        ErrandsNotesWindow,
    )
    from errands.widgets.sidebar import Sidebar
    from errands.widgets.tags.tags import Tags
    from errands.widgets.tags.tags_sidebar_row import TagsSidebarRow
    from errands.widgets.task import Task
    from errands.widgets.task_list_page import ErrandsTaskListPage
    from errands.widgets.task_list_sidebar_row import ErrandsTaskListSidebarRow
    from errands.widgets.today.today import Today
    from errands.widgets.today.today_sidebar_row import TodaySidebarRow
    from errands.widgets.trash.trash import Trash
    from errands.widgets.trash.trash_sidebar_row import TrashSidebarRow
    from errands.widgets.window import Window


class State:
    """Application's state class for accessing core widgets globally
    and some utils for quick access to deeper nested widgets"""

    # --- Constants --- #

    PROFILE: str | None = None
    APP_ID: str | None = None
    VERSION: str | None = None

    # --- Daemons --- #

    # Notifications
    notifications_daemon: ErrandsNotificationsDaemon | None = None

    # --- Widgets --- #

    # Application
    application: ErrandsApplication | None = None

    # Main window
    main_window: Window | None = None
    split_view: Adw.NavigationSplitView | None = None

    # View Stack
    view_stack: Adw.ViewStack | None = None
    loading_page: ErrandsLoadingPage | None = None
    today_page: Today | None = None
    tags_page: Tags | None = None
    trash_page: Trash | None = None
    task_list_page: ErrandsTaskListPage | None = None

    # Sidebar
    sidebar: Sidebar | None = None
    today_sidebar_row: TodaySidebarRow | None = None
    tags_sidebar_row: TagsSidebarRow | None = None
    trash_sidebar_row: TrashSidebarRow | None = None

    # Notes window
    notes_window: ErrandsNotesWindow | None = None

    # Date and time window
    datetime_window: ErrandsDateTimeWindow | None = None

    # Attachments window
    attachments_window: ErrandsAttachmentsWindow | None = None

    # --- Models --- #

    tasks_model: Gio.ListStore | None

    @classmethod
    def init(cls) -> None:
        # Create windows widgets
        from errands.widgets.shared.task_toolbar import (
            ErrandsAttachmentsWindow,
            ErrandsDateTimeWindow,
            ErrandsNotesWindow,
        )

        cls.notes_window = ErrandsNotesWindow()
        cls.datetime_window = ErrandsDateTimeWindow()
        cls.attachments_window = ErrandsAttachmentsWindow()

        # Create models
        from errands.lib.data import UserData
        from errands.widgets.task import Task

        cls.tasks_model = Gio.ListStore(item_type=Task)
        for task in UserData.tasks:
            cls.tasks_model.append(Task(task))

    @classmethod
    def get_tasks(cls) -> list[Task]:
        """All Tasks in all Task Lists"""

        return cls.task_list_page.all_tasks

    @classmethod
    def get_task(cls, list_uid: str, uid: str) -> Task:
        for task in cls.get_tasks():
            if task.uid == uid and task.list_uid == list_uid:
                return task

    @classmethod
    def get_sidebar_row(cls, list_uid: str) -> ErrandsTaskListSidebarRow:
        for row in cls.sidebar.task_lists_rows:
            if row.list_data.uid == list_uid:
                return row

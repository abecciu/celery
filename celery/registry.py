"""celery.registry"""
import re
from celery import discovery
from UserDict import UserDict

RE_ILLEGAL_CLASS_CHARS = re.compile(r"[\W_]")


class NotRegistered(Exception):
    """The task is not registered."""


class AlreadyRegistered(Exception):
    """The task is already registered."""


def name_to_clsname(name):
    return "".join(map(str.capitalize, RE_ILLEGAL_CLASS_CHARS.split(name)))


class TaskRegistry(UserDict):
    """Site registry for tasks."""

    AlreadyRegistered = AlreadyRegistered
    NotRegistered = NotRegistered

    def __init__(self):
        self.data = {}

    def autodiscover(self):
        """Autodiscovers tasks using :func:`celery.discovery.autodiscover`."""
        discovery.autodiscover()

    def register(self, task, name=None):
        """Register a task in the task registry.

        Task can either be a regular function, or a class inheriting
        from :class:`celery.task.Task`.

        :keyword name: By default the :attr:`Task.name` attribute on the
            task is used as the name of the task, but you can override it
            using this option.

        :raises AlreadyRegistered: if the task is already registered.

        """
        is_class = hasattr(task, "run")

        if not name:
            name = getattr(task, "name")

        if name in self.data:
            raise self.AlreadyRegistered(
                    "Task with name %s is already registered." % name)

        if is_class:
            taskcls = task
        else:
            from celery.task.base import Task
            clsname = name_to_clsname(name)
            def runmethod(self, *args, **kwargs):
                return task(*args, **kwargs)
            taskcls = type(clsname, (Task, ), {"name": name,
                                               "type": "regular",
                                               "run": runmethod})()

        self.data[name] = taskcls() # instantiate Task class

    def unregister(self, name):
        """Unregister task by name.

        :param name: name of the task to unregister, or a
            :class:`celery.task.Task` class with a valid ``name`` attribute.

        :raises NotRegistered: if the task has not been registered.

        """
        if hasattr(name, "run"):
            name = name.name
        if name not in self.data:
            raise self.NotRegistered(
                    "Task with name %s is not registered." % name)
        del self.data[name]

    def get_all(self):
        """Get all task types."""
        return self.data

    def filter_types(self, type):
        """Return all tasks of a specific type."""
        return dict((task_name, task)
                        for task_name, task in self.data.items()
                            if task.type == type)

    def get_all_regular(self):
        """Get all regular task types."""
        return self.filter_types(type="regular")

    def get_all_periodic(self):
        """Get all periodic task types."""
        return self.filter_types(type="periodic")

    def get_task(self, name):
        """Get task by name."""
        return self.data[name]

"""
.. data:: tasks

    The global task registry.

"""
tasks = TaskRegistry()

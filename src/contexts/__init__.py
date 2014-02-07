import sys
from . import core
from .plugin_discovery import load_plugins
from .tools import catch, set_trace, time


__all__ = [
    'run', 'main',
    'catch', 'set_trace', 'time'
]


def main(*args, **kwargs):
    """
    Call contexts.run() with the sepcified arguments,
    exiting with code 0 if the test run was successful,
    code 1 if unsuccessful.
    """
    exit_code = run(*args, **kwargs)
    sys.exit(exit_code)


# FIXME: run() currently assumes you're running on the cmd line
def run(plugin_list=None):
    """
    Polymorphic test-running function.

    run() - run all the test classes in the main module
    run(class) - run the test class
    run(module) - run all the test classes in the module
    run(file_path:string) - run all the test classes found in the file
    run(folder_path:string) - run all the test classes found in the folder and subfolders
    run(package_path:string) - run all the test classes found in the package and subfolders

    Returns: exit code as an integer.
        The default behaviour (which may be overridden by plugins) is to return a 0
        exit code if the test run succeeded, and 1 if it failed.
    """
    if plugin_list is None:  # default list of plugins
        plugin_list = load_plugins()

    composite = core.PluginComposite(plugin_list)

    to_run = composite.call_plugins("get_object_to_run")

    test_run = core.TestRun(to_run, composite)
    test_run.run()

    return composite.call_plugins('get_exit_code')

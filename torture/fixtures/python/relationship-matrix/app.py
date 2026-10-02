from lib import Child, Special, Worker, helper as h


def direct_alias() -> str:
    return h()


def construct() -> Worker:
    return Worker()


def typed_receiver(worker: Worker) -> str:
    return worker.process_item()


def inherited(child: Child) -> str:
    return child.hook()


def unique_fallback(obj) -> str:
    return obj.special_action()


def ambiguous(obj) -> str:
    return obj.shared_action()


def string_noise() -> str:
    return "helper() Worker.process_item() special_action()"

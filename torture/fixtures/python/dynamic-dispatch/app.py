class Alpha:
    def do_work(self) -> str:
        return "alpha"


class Beta:
    def do_work(self) -> str:
        return "beta"


def dispatch(service):
    return service.do_work()

from functools import wraps


class RevokeChainRequested(Exception):
    def __init__(self, return_value):
        Exception.__init__(self, '')
        self.return_value = return_value


def revoke_chain_authority(shared_task):
    """
    Decorator that adds ability to revoke all subsequent task in chain
    on shared task revoke
    :param shared_task: a @shared_task(bind=True) celery function
    :return:
    """
    @wraps(shared_task)
    def inner(self, *args, **kwargs):
        try:
            return shared_task(self, *args, **kwargs)
        except RevokeChainRequested as e:
            # Drop subsequent tasks in chain (if not in EAGER mode)
            if self.request.callbacks:
                self.request.callbacks[:] = []
            return e.return_value

    return inner

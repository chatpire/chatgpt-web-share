import asyncio
import re
import threading
from threading import Lock
from typing import Type, TypeVar

T = TypeVar("T")


def singleton_with_lock(cls: Type[T]):
    instances = {}
    lock = Lock()

    def get_instance(*args, **kwargs) -> T:
        with lock:
            if cls not in instances:
                instances[cls] = cls(*args, **kwargs)
            return instances[cls]

    return get_instance


def async_wrap_iter(it):
    """Wrap blocking iterator into an asynchronous one"""
    loop = asyncio.get_event_loop()
    q = asyncio.Queue(1)
    exception = None
    _END = object()

    async def yield_queue_items():
        while True:
            next_item = await q.get()
            if next_item is _END:
                break
            yield next_item
        if exception is not None:
            # the iterator has raised, propagate the exception
            raise exception

    def iter_to_queue():
        nonlocal exception
        try:
            for item in it:
                # This runs outside the event loop thread, so we
                # must use thread-safe API to talk to the queue.
                asyncio.run_coroutine_threadsafe(q.put(item), loop).result()
        except Exception as e:
            exception = e
        finally:
            asyncio.run_coroutine_threadsafe(q.put(_END), loop).result()

    threading.Thread(target=iter_to_queue).start()
    return yield_queue_items()


def desensitize(text):
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    url_regex = r'(http[s]?://[A-Za-z0-9]{2})[A-Za-z0-9./?=%&_-]*'

    def replace_email(match):
        email = match.group(0)
        name, domain = email.split('@')
        masked_email = f'{name[0]}***@*.{domain.split(".")[1]}'
        return masked_email

    def replace_url(match):
        url = match.group(1)
        return url + '***'

    text = re.sub(email_regex, replace_email, text)
    text = re.sub(url_regex, replace_url, text)

    return text

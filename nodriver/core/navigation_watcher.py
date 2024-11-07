import asyncio
import typing
from typing import Optional
from .. import cdp

if typing.TYPE_CHECKING:
    from . import tab


class LoadingFailed(Exception):
    pass


class NavigationTimeout(Exception):
    pass


class NavigationWatcher:

    def __init__(self, tab_: "tab.Tab", timeout: int = 30):
        """
        Detect the navigation request and wait for the response

        :param tab_: The tab/page to monitor for the  navigation request/response
        :type tab_: tab.Tab
        :param timeout: time to wait for navigation response
        :type timeout: int
        """
        self.main_frame_id = tab_.target.target_id
        self.timeout = timeout
        self.nav_request: Optional[cdp.network.RequestWillBeSent] = None
        self.nav_response: Optional[cdp.network.ResponseReceived] = None
        self.nav_response_error: Optional[cdp.network.LoadingFailed] = None
        self.wait_nav_response: asyncio.Event = asyncio.Event()
        tab_.add_handler(
            cdp.network.ResponseReceived, lambda e: self.on_response_received(e)
        )
        tab_.add_handler(cdp.network.RequestWillBeSent, lambda e: self.on_request(e))
        tab_.add_handler(cdp.network.LoadingFailed, lambda e: self.on_loading_failed(e))

    def on_response_received(self, event: cdp.network.ResponseReceived):
        if (
            self.nav_request is not None
            and self.nav_request.request_id == event.request_id
        ):
            self.wait_nav_response.set()
            self.nav_response = event

    def on_request(self, event: cdp.network.RequestWillBeSent):
        if self.is_navigation_request(event) and self.main_frame_id == event.frame_id:
            self.nav_request = event
            self.wait_nav_response.clear()
            # self.wait_nav_response.start()

    def on_loading_failed(self, event: cdp.network.LoadingFailed):
        if (
            self.nav_request is not None
            and self.nav_request.request_id == event.request_id
        ):
            print(f"Loading Failed: {event}")
            self.wait_nav_response.set()
            self.nav_response_error = event

    async def get_nav_response(self):
        try:
            await asyncio.wait_for(self.wait_nav_response.wait(), self.timeout)
        except asyncio.TimeoutError:
            self.wait_nav_response.set()
            raise NavigationTimeout()
        finally:
            if self.nav_response_error is not None:
                raise LoadingFailed(
                    f"Failed to load: {self.nav_request.request.url} Reason: {self.nav_response_error.error_text}"
                )
            return self.nav_response.response

    @staticmethod
    def is_navigation_request(event) -> bool:
        if (
            event.request_id == event.loader_id
            and event.type_ == cdp.network.ResourceType.DOCUMENT
        ):
            return True
        return False

from fastapi import Response


class ForcedResponse(Exception):
    """The application must return the given response.

    This allows interrupting the flow of execution from outside route functions,
    for example when a dependency needs to prompt the user to re-authenticate.

    """

    def __init__(self, response: Response) -> None:
        self.response = response

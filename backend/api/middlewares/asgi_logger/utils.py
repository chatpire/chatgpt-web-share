from urllib.parse import quote

from asgiref.typing import HTTPScope


def get_client_addr(scope: HTTPScope):
    if scope["client"] is None:
        return "-"  # pragma: no cover
    return f"{scope['client'][0]}:{scope['client'][1]}"


def get_path_with_query_string(scope: HTTPScope) -> str:
    path_with_query_string = quote(scope.get("root_path", "") + scope["path"])
    if scope["query_string"]:  # pragma: no cover
        return f"{path_with_query_string}?{scope['query_string'].decode('ascii')}"
    return path_with_query_string
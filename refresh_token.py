import random
import socket
import webbrowser


class TokenException(Exception):
    """Exception raised when error acquiring refresh token"""


def authorize_token(reddit):
    """
    Opens the web browser to ask for refresh token.
    Authorizes a refresh token for given reddit instance.

    :param reddit: Reddit instance to authorize
    :return: Refresh token returned from authorization
    """
    state = str(random.randint(0, 65000))
    url = reddit.auth.url(['identity', 'edit', 'read', 'history'],
                          state, 'permanent')
    input("Press ENTER to open web browser to authenticate with OAuth...")
    webbrowser.open(url)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", 8080))
    server.listen(1)
    client = server.accept()[0]
    server.close()
    data = client.recv(1024).decode('utf-8')
    client.close()
    param_tokens = data.split(' ', 2)[1].split('?', 1)[1].split('&')
    params = {
        key: value for (key, value) in [token.split('=') for token in param_tokens]
    }
    if state != params["state"]:
        raise TokenException(f"State mismatch. Expected: {state} ",
                             f"Received: {params['state']}")
    elif "error" in params:
        raise TokenException(params['error'])
    reddit.auth.authorize(params["code"])
    return params['code']

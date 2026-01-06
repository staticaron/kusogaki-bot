import jwt


class TokenResponse:
    def __init__(
        self, error: bool = False, error_msg: str = '', user_id: int = 0
    ) -> None:
        self.error = error
        self.error_msg = error_msg
        self.user_id = user_id


async def get_id_from_token(token: str) -> TokenResponse:
    """Returns the aniList Id from token"""

    try:
        data = jwt.decode(token, options={'verify_signature': False})
    except Exception:
        return TokenResponse(True, 'Invalid Token')

    return TokenResponse(False, '', data['sub'])

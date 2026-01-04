from discord import Embed, File, Forbidden, HTTPException, User


class SendDMResponse:
    def __init__(
        self,
        error: bool = False,
        error_msg: str = '',
    ) -> None:
        self.error = error
        self.error_msg = error_msg


class SendDM:
    def __init__(self) -> None:
        pass

    async def send_user_message(
        self,
        user: User,
        msg: str = '',
        embd: Embed | None = None,
        file: File | None = None,
    ) -> SendDMResponse:
        try:
            if file is None:
                if embd is None:
                    await user.send(msg)
                else:
                    await user.send(msg, embed=embd)
            else:
                await user.send(
                    msg,
                    file=file,
                )
            return SendDMResponse()

        except Forbidden:
            return SendDMResponse(True, 'Forbidden Error')

        except HTTPException:
            return SendDMResponse(True, 'HTTPException')

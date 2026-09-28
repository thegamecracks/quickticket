# https://fastapi.tiangolo.com/advanced/settings/
from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, IPvAnyAddress, NameEmail, Secret, model_validator
from pydantic_extra_types.domain import DomainStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    smtp: SMTPSettings | None


class SMTPSettings(BaseSettings):
    host: DomainStr | IPvAnyAddress
    """The mail server's hostname to connect to."""
    port: int = Field(gt=0, lt=65536)
    """The mail server port to connect to."""
    tls: Literal["off", "implicit", "starttls"] | None = None
    """Whether SSL/TLS should be used.

    If None, it is inferred from the port, 465 => implicit and 587 => starttls.
    If neither port, an error is raised.

    """
    username: Secret[str]
    """The username for authenticating to the mail server."""
    password: Secret[str]
    """The password for authenticating to the mail server."""
    from_email: NameEmail
    """The default email address to send emails from in RFC 5322 format,
    such as "foobar@example.com" or "Foo Bar <foobar@example.com>.
    """

    @model_validator(mode="after")
    def infer_tls_from_port(self) -> Self:
        if self.tls is not None:
            return self
        elif self.port == 465:
            self.tls = "implicit"
        elif self.port == 587:
            self.tls = "starttls"
        else:
            raise ValueError(
                "Cannot infer SMTP TLS mode from port, please specify "
                "'off', 'implicit', or 'starttls'"
            )
        return self


if __name__ == "__main__":
    import json

    print(json.dumps(Settings.model_json_schema(), indent=4))

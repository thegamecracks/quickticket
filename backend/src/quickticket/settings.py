# https://fastapi.tiangolo.com/advanced/settings/
from typing import Literal, Self

from fastapi.datastructures import URL
from pydantic import (
    AnyUrl,
    Field,
    HttpUrl,
    IPvAnyAddress,
    NameEmail,
    Secret,
    model_validator,
)
from pydantic_extra_types.domain import DomainStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class CacheSettings(BaseSettings):
    url: Secret[AnyUrl] = Secret(AnyUrl("sqlite:///quickticket-cache.db"))
    """The connection string to use for caching.

    This supports ``sqlite://`` and ``redis://`` schemes.

    .. note::

       For sqlite, the supported URL syntax is simplified and does **not**
       follow the same URL syntax supported by :attr:`DatabaseSettings.url`.

    """


class DatabaseSettings(BaseSettings):
    url: Secret[AnyUrl] = Secret(AnyUrl("sqlite+aiosqlite:///quickticket.db"))
    """The SQLAlchemy connection string to use for the database connection.

    https://docs.sqlalchemy.org/en/21/core/engines.html

    Examples:
    - sqlite+aiosqlite:///path/to/quickticket.db
    - sqlite+aiosqlite:///file::memory:?cache=shared&uri=true
    - postgresql+psycopg://username:password@localhost:5432/mydatabase?sslmode=verify-full

    .. note::

       For PostgreSQL with psycopg, query parameters are passed to the underlying libpq
       library. See https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
       for more information.

    """


class FrontendSettings(BaseSettings):
    redirect_uris: list[HttpUrl] = [
        HttpUrl("http://127.0.0.1:5173/*"),
        HttpUrl("http://localhost:5173/*"),
    ]
    """A list of URL glob patterns allowed to be used in ``/auth/*?redirect_uri=``
    query parameters.

    The base URLs are automatically added to CORS headers.

    """

    @property
    def origins(self) -> list[str]:
        """A list of allowed frontend origins."""
        return [
            str(URL(scheme=uri.scheme, hostname=uri.host, port=uri.port))
            for uri in self.redirect_uris
            if uri.host is not None
        ]


class OpenIDSettings(BaseSettings):
    client_id: Secret[str]
    """The client ID for the OpenID Connect provider."""
    client_secret: Secret[str]
    """The client secret for the OpenID Connect provider."""
    discovery_url: AnyUrl
    """The OpenID Connect provider's auto-discovery URL.

    Example: https://example.com/.well-known/openid-configuration

    """


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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        env_prefix="backend__",
        extra="ignore",
    )

    cache: CacheSettings = Field(default_factory=CacheSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    frontend: FrontendSettings = Field(default_factory=FrontendSettings)
    openid: OpenIDSettings | None = None
    smtp: SMTPSettings | None = None


if __name__ == "__main__":
    import json

    print(json.dumps(Settings.model_json_schema(), indent=4))

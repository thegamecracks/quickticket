# https://fastapi.tiangolo.com/advanced/settings/
from fnmatch import fnmatch
from typing import Literal, Self

from fastapi.datastructures import URL
from pydantic import (
    AnyUrl,
    Field,
    HttpUrl,
    NameEmail,
    Secret,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from quickticket.logging import LogVerbosity


class CacheSettings(BaseSettings):
    url: Secret[AnyUrl] = Secret(AnyUrl("sqlite:///quickticket-cache.db"))
    """The connection string to use for caching.

    This supports ``sqlite://``, ``redis://``, and  ``rediss://`` (SSL) schemes.

    Examples:
    - sqlite:///quickticket-cache.db
    - redis://default:password@localhost:6379
    - rediss://default:password@localhost:6379

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
    builtin: bool = True
    """If True, a minimal frontend will be served on root.

    This is intended only for testing and should be disabled in production!
    ``BACKEND__FRONTEND__BUILTIN=0``

    """
    default_redirect_uri: HttpUrl | None = None
    """The default URL to redirect if no origin is specified.

    Must be matched by one of the patterns in :attr:`redirect_uris`.
    If None, the redirect URI will be dynamically set to the request's origin.

    """
    redirect_uris: list[HttpUrl] = [
        HttpUrl("http://127.0.0.1:5173/*"),
        HttpUrl("http://localhost:5173/*"),
        HttpUrl("http://127.0.0.1:8000/*"),
        HttpUrl("http://localhost:8000/*"),
    ]
    """A list of URL glob patterns allowed to be used in ``/auth/*?redirect_uri=``
    query parameters.

    URL origins are automatically added to CORS headers.

    """

    @property
    def origins(self) -> list[str]:
        """A list of allowed frontend origins."""
        return [
            str(URL(scheme=uri.scheme, hostname=uri.host, port=uri.port))
            for uri in self.redirect_uris
            if uri.host is not None
        ]

    def match_redirect_uri(self, uri: str | URL | AnyUrl) -> AnyUrl | None:
        """Return the first origin that matches the URL, if any."""
        return next(
            (pat for pat in self.redirect_uris if fnmatch(str(uri), str(pat))),
            None,
        )

    @model_validator(mode="after")
    def is_matching_default_redirect_uri(self) -> Self:
        if self.default_redirect_uri is None:
            pass
        elif not self.match_redirect_uri(self.default_redirect_uri):
            raise ValueError("default_redirect_uri does not match any pattern in redirect_uris")
        return self


class LogSettings(BaseSettings):
    debug: bool = True
    """Enable Starlette's debug mode, which includes tracebacks in error responses.

    This is intended only for testing and should be disabled in production!
    ``BACKEND__LOG__DEBUG=0``

    """
    profiling: bool = True
    """Enable profiling the application by specifying ``?profile=1`` in requests.

    This is intended only for testing and should be disabled in production!
    ``BACKEND__LOG__PROFILING=0``

    """
    verbosity: LogVerbosity = LogVerbosity.PROJECT_DEBUG
    """The logging verbosity starting from 0, where larger numbers mean greater verbosity."""


class OpenAPISettings(BaseSettings):
    url: str | None = "/openapi.json"
    """The route where the OpenAPI schema will be hosted.

    If empty, the route will be disabled, and the Swagger UI docs and ReDoc will also be disabled.

    """
    swagger_url: str = "/docs"
    """The route where Swagger UI documentation will be hosted."""
    redoc_url: str = "/redoc"
    """The route where ReDoc documentation will be hosted."""


class OpenIDSettings(BaseSettings):
    client_id: Secret[str]
    """The client ID for the OpenID Connect provider."""
    client_secret: Secret[str]
    """The client secret for the OpenID Connect provider."""
    discovery_url: AnyUrl
    """The OpenID Connect provider's auto-discovery URL.

    Example: https://example.com/.well-known/openid-configuration

    """
    admin_group: str | None = None
    """The group claim required for administrator privileges.

    If None, administrator privileges will not be linked to the provider.
    Existing administrators can be revoked by removing this claim on the provider.

    """


class S3Settings(BaseSettings):
    url: Secret[str]
    """The endpoint to connect to S3 storage.

    Examples:
    - http://s3:3900
    - https://s3.dualstack.ca-central-1.amazonaws.com

    See also: https://docs.aws.amazon.com/general/latest/gr/s3.html

    """
    access_key: Secret[str]
    """The access key used for authentication."""
    secret_key: Secret[str]
    """The secret key used for authentication."""


class SecuritySettings(BaseSettings):
    # TODO: validate host / host:port / [ipv6]:port
    allowed_hosts: list[str] = ["127.0.0.1", "localhost"]
    """A list of allowed origins for the Host header.

    If ["*"] is given, all hosts are allowed. Not safe!

    """
    trusted_proxies: list[str] = ["127.0.0.1"]
    """A list of trusted proxy addresses to accept ``X-Forwarded-*`` headers from.

    If ["*"] is given, all hosts are allowed. Not safe!

    """
    csrf_secret: Secret[str] = Secret("insecure_qt9u0SCF3DuSJ69ZrqvzlJGTWxx7C5wh")
    """The secret to use for ``csrftoken`` double submit cookies / ``x-csrf-token`` headers."""
    cookie_encryption_secrets: list[Secret[str]] = [
        Secret("Qfw1bmzNtFba8qLxYZzxtEDfgd4P58LCDKiuMezO6lU=")
    ]
    """The secrets to use for encrypting cookies.

    Each secret must be a random, 256-bit (32 bytes) base64-encoded string.
    You can generate a valid secret with::

        uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

    The first-most secret is used for encrypting cookies, and extra secrets
    can be given to allow decrypting older cookies.
    For example, to set a new secret in your dev environment without losing existing cookies::

        BACKEND__SECURITY__COOKIE_ENCRYPTION_SECRETS=["my-new-base64-secret", "Qfw1bmzNtFba8qLxYZzxtEDfgd4P58LCDKiuMezO6lU="]

    """
    token_leeway: int = 30
    """The tolerance for time desync between the OpenID provider and the backend.

    For example, given a newly minted access token with ``"iat": 3600`` and a leeway
    of 30 seconds, the server can be at most 30 seconds behind the provider's time.
    If this is exceeded, :exc:`joserfc.errors.InvalidClaimError` will be raised
    during validation.

    """


class SMTPSettings(BaseSettings):
    host: str  # TODO: validate host / host:port / [ipv6]:port
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

    root_path: str = ""
    """The path prefix to prepend when returning URLs for the application,
    for example, ``/backend``.

    This is needed when running behind a reverse proxy that serves
    the application under a subpath.

    """

    cache: CacheSettings = Field(default_factory=CacheSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    frontend: FrontendSettings = Field(default_factory=FrontendSettings)
    log: LogSettings = Field(default_factory=LogSettings)
    openapi: OpenAPISettings = Field(default_factory=OpenAPISettings)
    openid: OpenIDSettings | None = None
    s3: S3Settings | None = None
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    smtp: SMTPSettings | None = None


if __name__ == "__main__":
    print(Settings().model_dump_json(indent=4))

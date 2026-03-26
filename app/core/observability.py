import sentry_sdk
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.config import Settings


def configure_observability(application: FastAPI, settings: Settings) -> None:
    _configure_metrics(application, settings)
    _configure_sentry(settings)


def _configure_metrics(application: FastAPI, settings: Settings) -> None:
    if not settings.METRICS_ENABLED:
        return

    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=[settings.METRICS_PATH],
    ).instrument(
        application,
        metric_namespace=settings.METRICS_NAMESPACE,
        metric_subsystem=settings.METRICS_SUBSYSTEM,
    ).expose(
        application,
        include_in_schema=False,
        should_gzip=True,
        endpoint=settings.METRICS_PATH,
    )


def _configure_sentry(settings: Settings) -> None:
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENV,
        send_default_pii=settings.SENTRY_SEND_DEFAULT_PII,
        enable_logs=settings.SENTRY_ENABLE_LOGS,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profile_session_sample_rate=settings.SENTRY_PROFILE_SESSION_SAMPLE_RATE,
        profile_lifecycle="trace",
        integrations=[
            StarletteIntegration(
                transaction_style="endpoint",
                middleware_spans=True,
                failed_request_status_codes=set(range(500, 600)),
            ),
            FastApiIntegration(
                transaction_style="endpoint",
                middleware_spans=True,
                failed_request_status_codes=set(range(500, 600)),
            ),
        ],
    )

from flask import current_app

from iot_app.auth.providers.azure_easy_auth import AzureEasyAuthProvider
from iot_app.auth.providers.dev import DevAuthProvider


def get_auth_provider():
    """AUTH_TYPE に基づき AuthProvider インスタンスを生成する"""
    auth_type = current_app.config['AUTH_TYPE']

    providers = {
        'azure': AzureEasyAuthProvider,
        'dev': DevAuthProvider,
    }

    provider_class = providers.get(auth_type)
    if not provider_class:
        raise ValueError(f"Unknown AUTH_TYPE: {auth_type}")

    return provider_class()

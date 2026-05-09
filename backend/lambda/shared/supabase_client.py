"""Supabase client factory for Lambda functions."""

from supabase import create_client, Client
import importlib as _il

_config = _il.import_module("lambda.shared.config")
SUPABASE_URL = _config.SUPABASE_URL
SUPABASE_KEY = _config.SUPABASE_KEY


def get_supabase_client() -> Client:
    """Create and return a Supabase client instance."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY environment variables must be set"
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)

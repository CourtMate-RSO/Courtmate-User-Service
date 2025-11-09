import os
from supabase import create_client, ClientOptions
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def user_supabase_client(jwt: str):
    """
    Create a Supabase client that runs queries as the given user (RLS aware).
    """
    options = ClientOptions(
        auto_refresh_token=False,
        persist_session=False,
    )
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY, options=options)
    client.auth.set_session(access_token=jwt, refresh_token="")
    return client

def admin_supabase_client():
    """
    Create a Supabase client that runs queries with admin privileges (bypassing RLS).
    """
    SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    options = ClientOptions(
        auto_refresh_token=False,
        persist_session=False,
    )
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, options=options)
    return client

def anon_supabase_client():
    """
    Create a Supabase client that runs queries as an anonymous user.
    """
    options = ClientOptions(
        auto_refresh_token=False,
        persist_session=False,
    )
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY, options=options)
    return client
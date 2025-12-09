from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")


def get_graphql_client(token: str):
    """Create GraphQL client with authentication"""
    transport = RequestsHTTPTransport(
        url=f"{SUPABASE_URL}/graphql/v1",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    return Client(transport=transport, fetch_schema_from_transport=False)


def get_user_by_id_graphql(user_id: str, token: str):
    """Get user by ID using GraphQL"""
    client = get_graphql_client(token)
    
    query = gql("""
        query GetUser($id: UUID!) {
            users_dataCollection(filter: {id: {eq: $id}}) {
                edges {
                    node {
                        id
                        email
                        full_name
                        phone
                        role
                        first_login
                        created_at
                    }
                }
            }
        }
    """)
    
    result = client.execute(query, variable_values={"id": user_id})
    
    edges = result.get("users_dataCollection", {}).get("edges", [])
    if not edges:
        return None
    
    return edges[0]["node"]

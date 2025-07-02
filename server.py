from fastmcp import FastMCP
from pydantic import Field
import requests
import os
from utils.platforms import Platform
from utils.query import IDENTITY_QUERY, INTROSPECTION_QUERY
from dotenv import load_dotenv
from typing import Annotated, Dict
from utils.simple_cache import SimpleCache
from utils.schema import SchemaInfo

mcp = FastMCP("relate-account")
load_dotenv()

url = os.getenv("DATA_API_URL", "https://graph.web3.bio/graphql")
cache = SimpleCache()
schemas: Dict[str, SchemaInfo] = {}

def execute_graphql_query(query_obj: dict, url: str, timeout: int = 10000) -> dict:
	headers = {
		"Content-Type": "application/json",
		"User-Agent": "relate-account-mcp/3.0.0",
	}
	access_token = os.getenv("ACCESS_TOKEN")
	if access_token:
		headers["Authorization"] = access_token
	try:
		response = requests.post(
			url,
			json=query_obj,
			headers=headers,
			timeout=timeout
		)
		if not response.ok:
			raise Exception(f"HTTP {response.status_code}: {response.reason}")
		json_data = response.json()
		if "errors" in json_data:
			raise Exception(
				"GraphQL errors: " + ", ".join(e.get("message", str(e)) for e in json_data["errors"])
			)
		return json_data.get("data", {})
	except Exception as e:
		return {"error": f"Query failed: {e}"}
	
def create_cache_key(platform: str, identity: str) -> str:
	cache_key = f"{platform}:{identity}".lower()
	return cache_key


@mcp.tool(
		name="get-related-address",
		description="Retrieves all related identities associated with a specific platform identity. This tool helps discover cross-platform connections for the same person or entity. Use cases include: 1) Finding all accounts (Lens, Farcaster, ENS, etc.) belonging to the same person, 2) Resolving domain names to their underlying addresses (ENS domains, Lens handles, etc.)",
)
def relate_account(
	platform: Annotated[Platform, Field(description="The platform of a specific identity, e.g.: Ethereum, Farcaster, lens, ens")],
	identity: Annotated[str, Field(min_length=1, max_length=256, description="User's identity")],
) -> str:
	# Query account info via GraphQL
	query_obj = {
		"query": IDENTITY_QUERY,
		"variables": {"platform": platform.value, "identity": identity}
	}
	cache_key = create_cache_key(platform.value, identity)
	cached_data = cache.get(cache_key)
	if cached_data is not None:
		return str(cached_data)

	data = execute_graphql_query(query_obj, url)
	cache.set(cache_key, data)
	return str(data)

@mcp.tool(
	name="discover-query-schema",
	description="Discover the query schema for the given endpoint, the given endpoint is provided by web3.bio which is used as a crypto-related identity graph service provider. Users can use web3.bio to query all identity information of a specific platform identity. You should first use this tool to discover the query schema for the given endpoint to help build the query statement before you execute the query.",
)
def discover_query_schema() -> str:
	query_obj = {
		"query": INTROSPECTION_QUERY,
	}
	data = execute_graphql_query(query_obj, url)
	schemas["web3.bio"] = SchemaInfo("web3.bio", url, data)
	return str(data)

@mcp.tool(
	name="analyze-schema",
	description="Analyze the schema of the given endpoint, the given endpoint is provided by web3.bio which is used as a crypto-related identity graph service provider. This tool will be used to parse the fetched schema data and formalize it into a standard format for future use (etc. build query statement and execute the query).",
)
def analyze_schema() -> str:
	schema_info = schemas["web3.bio"]

	types = schema_info.schema.get("__schema", {}).get("types", [])
	# Filter out internal types
	filtered_types = [t for t in types if not t.get("name", "").startswith("__")]
	
	analysis = {
		"schema_name": "web3.bio",
		"endpoint": schema_info.endpoint,
		"type_count": len(filtered_types),
		"object_types": [t.get("name") for t in filtered_types if t.get("kind") == "OBJECT"],
		"scalar_types": [t.get("name") for t in filtered_types if t.get("kind") == "SCALAR"],
		"enum_types": [t.get("name") for t in filtered_types if t.get("kind") == "ENUM"],
	}
	return str(analysis)

if __name__ == "__main__":
	mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")
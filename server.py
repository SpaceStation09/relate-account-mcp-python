from fastmcp import FastMCP
from pydantic import Field
import requests
import os
from utils.platforms import Platform
from utils.query import IDENTITY_QUERY
from dotenv import load_dotenv
from typing import Annotated
from utils.simple_cache import SimpleCache

mcp = FastMCP("relate-account")
load_dotenv()

url = os.getenv("DATA_API_URL", "https://graph.web3.bio/graphql")
cache = SimpleCache()

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

if __name__ == "__main__":
	mcp.run(transport="http", host="127.0.0.1", port=8000, path="/relate-account")
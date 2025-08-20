#!/usr/bin/env python3
"""
RFC 7591 Dynamic Client Registration Implementation
"""

import argparse
import json
import requests
import sys
from typing import Dict, Optional


class RFC7591Client:
    """Client for OAuth 2.0 Dynamic Client Registration (RFC 7591)"""

    def __init__(self, registration_endpoint: str):
        self.registration_endpoint = registration_endpoint
        self.session = requests.Session()

    def register_client(self, client_name: str, **kwargs) -> Dict:
        """
        Register a new OAuth client according to RFC 7591

        Args:
            client_name: The human-readable name of the client
            **kwargs: Additional client metadata

        Returns:
            Dictionary containing the registration response
        """
        payload = {
            "client_name": client_name,
            "redirect_uris": kwargs.get("redirect_uris", ["http://localhost:8080/dynamic_application_callback"]),
            "grant_types": kwargs.get("grant_types", ["authorization_code"]),
            "response_types": kwargs.get("response_types", ["code"]),
            "scope": kwargs.get("scope", "openid profile email"),
            "token_endpoint_auth_method": kwargs.get("token_endpoint_auth_method", "client_secret_basic")
        }

        # Add any additional client metadata
        for key, value in kwargs.items():
            if key not in payload:
                payload[key] = value

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = self.session.post(
                self.registration_endpoint,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Client registration failed: {e}")

    def get_client_info(self, client_id: str, access_token: str) -> Dict:
        """
        Retrieve client information using the registration access token

        Args:
            client_id: The client identifier
            access_token: The registration access token

        Returns:
            Dictionary containing client information
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        url = f"{self.registration_endpoint}/{client_id}"

        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to retrieve client info: {e}")


def main():
    """Main function for command line execution"""
    parser = argparse.ArgumentParser(
        description="RFC 7591 OAuth Dynamic Client Registration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --endpoint https://auth.example.com/register --client-name "My App"
  %(prog)s --endpoint https://auth.example.com/register --client-name "Test Client" --scope "read write"
        """
    )

    parser.add_argument(
        "--endpoint",
        required=True,
        help="The client registration endpoint URL"
    )

    parser.add_argument(
        "--client-name",
        required=True,
        help="The human-readable name of the client to register"
    )

    parser.add_argument(
        "--redirect-uris",
        nargs="+",
        default=["http://localhost:8080/callback"],
        help="Redirect URIs for the client (default: http://localhost:8080/callback)"
    )

    parser.add_argument(
        "--grant-types",
        nargs="+",
        default=["authorization_code"],
        help="Grant types supported by the client (default: authorization_code)"
    )

    parser.add_argument(
        "--response-types",
        nargs="+",
        default=["code"],
        help="Response types supported by the client (default: code)"
    )

    parser.add_argument(
        "--scope",
        default="openid profile email",
        help="Scope values for the client (default: 'openid profile email')"
    )

    parser.add_argument(
        "--token-auth-method",
        default="client_secret_basic",
        help="Token endpoint authentication method (default: client_secret_basic)"
    )

    parser.add_argument(
        "--output",
        choices=["json", "pretty"],
        default="pretty",
        help="Output format (default: pretty)"
    )

    args = parser.parse_args()

    try:
        client = RFC7591Client(args.endpoint)

        result = client.register_client(
            client_name=args.client_name,
            redirect_uris=args.redirect_uris,
            grant_types=args.grant_types,
            response_types=args.response_types,
            scope=args.scope,
            token_endpoint_auth_method=args.token_auth_method
        )

        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            print("Client Registration Successful!")
            print(f"Dynamic Client ID: {result.get('client_id')}")
            print(f"Dynamic Client Secret: {result.get('client_secret')}")
            print(f"Dynamic Client Name: {result.get('client_name')}")
            if result.get('registration_client_uri'):
                print(f"Registration URI: {result.get('registration_client_uri')}")
            if result.get('registration_access_token'):
                print(f"Access Token: {result.get('registration_access_token')}")
            print()
            print(f"export DYNAMIC_CLIENT_ID={result.get('client_id')}")
            print(f"export DYNAMIC_CLIENT_SECRET={result.get('client_secret')}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

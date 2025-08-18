# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository demonstrates OIDC Dynamic Application Registration (RFC 7591) with Auth0. It contains three main components:

1. **RFC 7591 Client** (`create_rfc7591_client.py`) - Script to register dynamic OAuth clients
2. **Main App** (`mainapp/`) - Flask web application demonstrating OAuth authentication
3. **OAuth Client Example** (`oauth_dynamic_application.py`) - Standalone OAuth flow implementation with CLI

## Architecture

### Core Components

- `create_rfc7591_client.py` - RFC 7591 compliant client registration utility with CLI interface
- `oauth_dynamic_application.py` - Complete OAuth2 flow implementation with local callback server
- `mainapp/server.py` - Flask web app using Authlib for OAuth integration
- `mainapp/requirements.txt` - Python dependencies (Flask, Authlib, requests, python-dotenv)

### Key Classes

- `RFC7591Client` in `create_rfc7591_client.py:13` - Handles dynamic client registration
- `OAuth2Client` in `oauth_dynamic_application.py:77` - Manages OAuth authentication flow  
- `CallbackServer` in `oauth_dynamic_application.py:154` - Local HTTP server for OAuth callbacks

## Development Commands

### Running the Main Flask App
```bash
cd mainapp
python server.py
```
The app runs on http://0.0.0.0:3000 by default.

### Creating Dynamic Clients
```bash
python create_rfc7591_client.py \
  --endpoint https://${AUTH0_DOMAIN}/oidc/register \
  --client-name "${USER}-app" \
  --redirect-uris http://127.0.0.1:8080/callback
```

### Running OAuth Client Example
```bash
python oauth_dynamic_application.py \
  --client-id ${DYNAMIC_CLIENT_ID} \
  --client-secret ${DYNAMIC_CLIENT_SECRET} \
  --auth0-domain ${AUTH0_DOMAIN} \
  [--port 8080] [--verbose]
```

This script:
- Starts a local callback server on the specified port (default: 8080)
- Opens browser for authentication
- Handles OAuth callback and token exchange
- Displays user information upon successful authentication

### Docker Operations (Main App)
```bash
cd mainapp
./docker-build.sh    # Build Docker image
./docker-run.sh      # Run with .env file
```

## Configuration

### Main Flask App
Requires `.env` file in `mainapp/` directory with:
```
AUTH0_CLIENT_ID=your_main_app_client_id
AUTH0_CLIENT_SECRET=your_main_app_client_secret
AUTH0_DOMAIN=your_domain.auth0.com
APP_SECRET_KEY=your_secret_key
```

### OAuth Client Example
Requires credentials passed as command line arguments:
- `--client-id`: Dynamic client ID (from RFC 7591 registration)
- `--client-secret`: Dynamic client secret
- `--auth0-domain`: Your Auth0 domain

### Prerequisites
- Auth0 account with OIDC Dynamic Application Registration enabled
- Management API access for promoting social connections to domain-level
- GitHub social connection configured in Auth0

## Authentication Flow

### Dynamic Client Registration (RFC 7591)
1. POST request to `https://${AUTH0_DOMAIN}/oidc/register`
2. Receives client credentials (`client_id`, `client_secret`)
3. Client appears in Auth0 dashboard

### OAuth2 Flow
1. Authorization code flow (no PKCE in current implementation)
2. Local callback server handles redirect URI
3. Token exchange using client credentials
4. User info retrieval with access token
5. Graceful shutdown with Ctrl+C handling

### Key Features
- Configurable callback port
- Verbose logging option
- Browser auto-launch for authentication
- Proper error handling and cleanup
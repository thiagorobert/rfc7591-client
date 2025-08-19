# OIDC Dynamic Application Registration example

This repo exemplifies using OIDC Dynamic Application Registration (aka, [rfc7591](https://datatracker.ietf.org/doc/html/rfc7591) dynamic clients) with [auth0.com](https://auth0.com/).

## Step 1 - auth0 set up

1. Create a [auth0.com](https://auth0.com/) account
   * using the free tier will work (but it expires in 21 days)

1. Enable `OIDC Dynamic Application Registration` in auth0
   * Setting -> Advanced

1. Enable Management API
   * doc https://auth0.com/docs/api/management/v2
   * Applications -> APIs

1. Get a management API access token
   * Applications -> APIs > Auth0 Management API -> API Explorer

1. Promote Github social connection to domain-level
   * doc https://auth0.com/docs/authenticate/identity-providers/promote-connections-to-domain-level
    ```
    curl --request PATCH \
        --url 'https://rfc7591-test.us.auth0.com/api/v2/connections/${GITHUB_CONNECTION_ID}' \
        --header 'authorization: Bearer ${AUTH0_MGMT_API_ACCESS_TOKEN}' \
        --header 'cache-control: no-cache' \
        --header 'content-type: application/json' \
        --data '{ "is_domain_connection": true }'
    ```

## Step 2 - create main app

1. doc: https://auth0.com/docs/quickstart/webapp/python/interactive

1. use auth0's [example code](https://github.com/auth0-samples/auth0-python-web-app/tree/master/01-Login) or the version in `mainapp`

1. create a `.venv` and install requirements
```
python -m venv .venv --prompt rfc7591-client
source .venv/bin/activate
pip install -r mainapp/requirements.txt
```

1. create a `.env` file or export the following environment variables:
```
AUTH0_CLIENT_ID
AUTH0_CLIENT_SECRET
AUTH0_DOMAIN
APP_SECRET_KEY
```

1. run the app locally and ensure you can login/logout successfully using Github
```
python mainapp/server.py
```

1. Log in using Github

## Step 3 - create dynamic application

1. using helper script
```
python create_rfc7591_client.py \
    --endpoint https://${AUTH0_DOMAIN}/oidc/register \
    --client-name "${USER}-app" \
    --redirect-uris http://127.0.0.1:8080/callback
```

1. Note down `client_id` and `client_secret`

1. Verify the appliation in auth0 dashboard in 'Applications -> Applications'


## Step 4 - login using the dynamic application's credentials

1. Regular OAuth using the dynamic application's `client_id` and `client_secret`
1. The redirect URI provided will be used for the OAuth callback
   * you can configure other URIs via auth0's UI
1. Use  helper script provided to perform OAuth - it starts a server to handle the callback
```
python oauth_dynamic_application.py \
    --client-id ${DYNAMIC_CLIENT_ID} \
    --client-secret ${DYNAMIC_CLIENT_SECRET} \
    --auth0-domain ${AUTH0_DOMAIN} \
    [--port 8080] [--verbose]
```

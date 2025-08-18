# OIDC Dynamic Application Registration example

This repo exemplifies using OIDC Dynamic Application Registration (aka, [rfc7591](https://datatracker.ietf.org/doc/html/rfc7591) dynamic clients) with [auth0.com](https://auth0.com/).


## Step 1 - main app

1. Create a [auth0.com](https://auth0.com/) account
   * using the free tier will work (but it expires in 21 days)

1. Create a main application
   * doc: https://auth0.com/docs/quickstart/webapp/python/interactive
   * use auth0's [example code](https://github.com/auth0-samples/auth0-python-web-app/tree/master/01-Login) or the version in `mainapp`
   * run the app locally and ensure you can login/logout successfully using Github
   ```
   python server.py
   ```

## Step 2 - required auth0 configuration

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

## Step 3 - create a rfc7591 dynamic clients

1. Ensure you are logged in using Github

1. Create a dynamic application
   * doc https://datatracker.ietf.org/doc/html/rfc7591
   * using helper script
   ```
   python create_rfc7591_client.py \
   --endpoint https://${AUTH0_DOMAIN}/oidc/register \
   --client-name "${USER}-app" \
   --redirect-uris http://localhost:8080/callback
   ```
   * using curl
   ```
   curl --request POST \
     --url "https://${AUTH0_DOMAIN}/oidc/register" \
     --header "content-type: application/json" \
     --data "{\"client_name\":\"${USER}-otherapp\",\"redirect_uris\": [\"http://127.0.0.1:3000/callback\"]}"
   ```
   * note down `client_id` and `client_secret`

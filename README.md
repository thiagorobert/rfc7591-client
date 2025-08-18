# OIDC Dynamic Application Registration example

This repo exemplifies using OIDC Dynamic Application Registration (aka, [rfc7591](https://datatracker.ietf.org/doc/html/rfc7591) dynamic clients) with auth0.com.


## Step 1 - auth0 set up

1. Create a auth0.com account
   * using the free tier will work (but it expires in 21 days)

1. Create a main application
   * doc: https://auth0.com/docs/quickstart/webapp/python/interactive
   * use auth0's [example code](https://github.com/auth0-samples/auth0-python-web-app/tree/master/01-Login) or the version in `mainapp`
   * run the app locally and ensure you can login/logout successfully using Github
   ```
   python server.py
   ```

# How to Obtain GCM_CLIENT_SECRET from Keycloak

This guide explains how to retrieve the OAuth2 client secret (`GCM_CLIENT_SECRET`) from GCM's internal Keycloak instance.

## Prerequisites

- Access to the Kubernetes/OpenShift cluster where GCM is deployed
- `kubectl` or `oc` CLI tool configured
- Administrator access to GCM's Keycloak instance

## Overview

GCM uses Keycloak as its OIDC (OpenID Connect) provider for authentication. The `GCM_CLIENT_SECRET` is the OAuth2 client secret for the `gcmclient` (or your configured client ID) in Keycloak's `gcmrealm` realm.

## Step 1: Get Keycloak Admin Credentials

### For Kubernetes/K3s Deployments

```bash
# Get the Keycloak admin secret
kubectl get secret oidc-admin-secret -n gcmapp -o yaml

# Decode the Base64 values
echo "<KC_BOOTSTRAP_ADMIN_USERNAME_base64>" | base64 -d
echo "<KC_BOOTSTRAP_ADMIN_PASSWORD_base64>" | base64 -d
```

**Example:**
```bash
# Get the secret
kubectl get secret oidc-admin-secret -n gcmapp -o jsonpath='{.data.KC_BOOTSTRAP_ADMIN_USERNAME}' | base64 -d
kubectl get secret oidc-admin-secret -n gcmapp -o jsonpath='{.data.KC_BOOTSTRAP_ADMIN_PASSWORD}' | base64 -d
```

### For OpenShift Deployments

```bash
# Get the Keycloak admin secret
oc get secret oidc-admin-secret -n gcmapp -o yaml

# Decode the Base64 values
echo "<KC_BOOTSTRAP_ADMIN_USERNAME_base64>" | base64 -d
echo "<KC_BOOTSTRAP_ADMIN_PASSWORD_base64>" | base64 -d
```

**Note**: On Windows, you can use PowerShell to decode Base64:
```powershell
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("<base64_string>"))
```

## Step 2: Access Keycloak Admin Console

### Keycloak URL

The Keycloak admin console URL depends on your deployment type:

- **Kubernetes/K3s**: `https://<your-gcm-ip>:30443`
- **OpenShift**: `https://oidc.<your-domain>`

**Example URLs:**
- `https://192.168.1.100:30443`
- `https://oidc.gcm.example.com`

### Login to Keycloak

1. Open the Keycloak URL in your web browser
2. Click **"Administration Console"**
3. Enter the admin username and password from Step 1
4. Click **"Sign In"**

**Security Note**: If using a self-signed certificate, you may need to accept the security warning in your browser.

## Step 3: Switch to GCM Realm

After logging in:

1. Look for the **realm selector** dropdown in the top-left corner
   - It may show "master" by default
2. Click the dropdown and select **"gcmrealm"**
   - This is the realm where GCM's OAuth2 clients are configured

**Important**: Make sure you're in the `gcmrealm` realm, not the `master` realm.

## Step 4: Navigate to Clients

1. In the left sidebar, click **"Clients"**
2. You'll see a list of OAuth2/OIDC clients configured in GCM

## Step 5: Find Your Client

1. In the clients list, find the client with ID **"gcmclient"** (or your custom client ID)
   - This is the default client ID used by GCM
   - If you've configured a custom `GCM_CLIENT_ID`, search for that instead

2. Click on the client ID to open its configuration

## Step 6: Get the Client Secret

1. Click the **"Credentials"** tab
2. Look for the **"Client Secret"** field
3. The secret will be displayed (may be masked with asterisks)
4. Click the **"Copy"** button or **"Show"** button to reveal the secret
5. Copy the client secret value

**This is your `GCM_CLIENT_SECRET`** - use it in your `.env` file:

```bash
GCM_CLIENT_SECRET=<the-secret-you-copied>
```

> **Note**: The `gcmclient` configuration is automatically set up by IBM's GCM installer. You only need to retrieve the client secret - no configuration changes are required.

## Security Best Practices

### Protecting the Client Secret

1. **Never commit to version control**
   ```bash
   # Add to .gitignore
   .env
   config/relay.toml  # If it contains secrets
   ```

2. **Use environment variables**
   ```bash
   # In .env file (gitignored)
   GCM_CLIENT_SECRET=your-secret-here
   ```

3. **Restrict file permissions**
   ```bash
   chmod 600 .env
   ```

## Troubleshooting

### Cannot Access Keycloak Admin Console

**Problem**: Browser shows "Connection refused" or "Unable to connect"

**Solutions**:
- Verify the Keycloak URL and port
- Check if Keycloak pod is running: `kubectl get pods -n gcmapp | grep oidc`
- Check firewall rules allow access to port 30443
- For OpenShift, verify the route: `oc get route -n gcmapp`

### Invalid Credentials

**Problem**: "Invalid username or password" error

**Solutions**:
- Re-decode the Base64 values (ensure no extra whitespace)
- Verify you're using the correct secret: `oidc-admin-secret`
- Check the secret exists: `kubectl get secret oidc-admin-secret -n gcmapp`

### Client Not Found

**Problem**: Cannot find "gcmclient" in the clients list

**Solutions**:
- Verify you're in the `gcmrealm` realm (not `master`)
- Check if GCM is fully deployed and initialized
- Look for alternative client names (may vary by GCM version)

### Client Secret Not Visible

**Problem**: Client secret field is empty or shows "Not configured"

**Solutions**:
- The `gcmclient` should be pre-configured by GCM installer
- If the secret is missing, contact your GCM administrator
- Do not modify client settings unless instructed by IBM Support

## References

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OAuth 2.0 Client Credentials](https://oauth.net/2/grant-types/client-credentials/)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)
- [GCM MCP Server Documentation](https://www.ibm.com/docs/en/guardium-cm/2.0.0?topic=building-agents-guardium-cryptography-manager-using-inbuilt-mcp-server)

## Support

If you encounter issues not covered in this guide:

1. Check GCM documentation for your specific version
2. Verify Keycloak logs: `kubectl logs -n gcmapp <oidc-pod-name>`
3. Contact your GCM administrator
4. Refer to IBM Support documentation

---

**Security Reminder**: The client secret is a sensitive credential. Treat it with the same care as a password. Never share it in public channels, commit it to version control, or log it in application logs.
# GCM MCP Relay - Tools Reference

Complete reference for the 26 tools provided by IBM Guardium Cryptography Manager (GCM) MCP Relay.

## 📊 Tools Overview

- **Total Tools**: 26
- **Read-Only Tools**: 22 (safe)
- **State-Changing Tools**: 4 (use with caution)

---

## 1️⃣ Policy Management

Tools for searching, viewing, and creating security policies.

### Read-Only Tools

#### `search_policies`
Search and filter policies by policy type, active status, creator, and more.

**Use Cases**: List policies, search by specific criteria

#### `fetch_policy_by_id`
Retrieve detailed information for a specific policy by its ID.

**Use Cases**: View individual policy details, verify policy configuration

### State-Changing Tools

#### `create_policy` ⚠️ **HIGH RISK**
Create a new security policy.

**Use Cases**: Define and register new policies
**Warning**: Affects system-wide security configuration. Requires appropriate GCM user permissions.

---

## 2️⃣ Violation Management

Tools for querying policy violations and managing tickets.

### Read-Only Tools

#### `get_violation_by_id`
Retrieve detailed information for a specific violation by its ID.

**Use Cases**: View individual violation details, analyze violation content

#### `fetch_policy_violations_ticket`
Search and list tickets related to policy violations.

**Use Cases**: Manage violation tickets, track ticket status

#### `policy_violations_dashboard`
Retrieve violation statistics and dashboard data.

**Use Cases**: Get overall violation overview, generate reports

### State-Changing Tools

#### `create_violation_ticket` ⚠️ **MODERATE RISK**
Create a ticket for a policy violation. Integrates with external systems like Jira and ServiceNow.

**Use Cases**: Track violations, manage remediation actions
**Warning**: Creates records in external ticketing systems. Requires appropriate GCM user permissions.

---

## 3️⃣ IT Asset Management

Tools for managing IT assets such as databases, servers, and applications.

### Read-Only Tools

#### `get_filters_by_it_assets`
Retrieve available filter criteria for IT asset searches.

**Use Cases**: Verify search criteria, build dynamic filters

#### `fetch_detailed_asset_list_by_it_assets`
Retrieve a filtered list of IT assets with pagination support.

**Use Cases**: List assets, inventory management

#### `fetch_individual_asset_detail_by_it_assets`
Retrieve detailed information for specific IT assets. Supports bulk retrieval.

**Use Cases**: View individual asset details, verify asset attributes

#### `get_category_metadata_by_it_assets`
Retrieve metadata information for IT asset categories.

**Use Cases**: Understand asset attributes, retrieve schema information

---

## 4️⃣ Crypto Object Management

Tools for managing cryptographic objects such as certificates, keys, and protocols.

### Read-Only Tools

#### `get_filters_by_crypto_objects`
Retrieve available filter criteria for crypto object searches.

**Use Cases**: Verify search criteria, classify crypto assets

#### `fetch_detailed_asset_list_by_crypto_objects`
Retrieve a filtered list of crypto objects including certificates, keys, and protocols.

**Use Cases**: List crypto assets, crypto inventory management

#### `fetch_individual_asset_detail_by_crypto_objects`
Retrieve detailed information for specific crypto objects.

**Use Cases**: View individual crypto object details, verify certificates/keys

#### `get_category_metadata_by_crypto_objects`
Retrieve metadata information for crypto object categories.

**Use Cases**: Understand crypto object attributes, retrieve schema information

#### `fetch_bulk_vulnerable_crypto_objects`
Retrieve vulnerable crypto objects in bulk with violation information and ticket creation eligibility.

**Use Cases**: Vulnerability scanning, risk assessment

#### `get_vulnerable_crypto_objects_count`
Retrieve counts of vulnerable crypto objects by type.

**Use Cases**: Vulnerability statistics, dashboard display

---

## 5️⃣ Asset Management

Tools for managing asset groups and metadata.

### Read-Only Tools

#### `get_asset_groups`
Retrieve all available asset groups.

**Use Cases**: List asset groups, group management

#### `fetch_asset_metadata`
Retrieve metadata for specific asset categories.

**Use Cases**: Understand asset attributes, verify data model

---

## 6️⃣ Certificate Lifecycle Management

Tools for certificate permission management and renewal.

### Read-Only Tools

#### `get_certificate_permissions`
Retrieve permission information for a specific certificate.

**Use Cases**: Verify access control, permission auditing

#### `get_vault_details`
Retrieve detailed information for Vault integration.

**Use Cases**: Verify Vault configuration, validate integration status

#### `get_certificate_details`
Retrieve detailed information for a certificate by its ID.

**Use Cases**: View certificate information, monitor expiration dates

### State-Changing Tools

#### `renew_ca_signed_certificate` ⚠️ **HIGH RISK**
Renew a CA-signed certificate with auto-deploy option.

**Use Cases**: Certificate renewal, certificate lifecycle management
**Warning**: Affects production certificates. Requires appropriate GCM user permissions.

#### `renew_self_signed_certificate` ⚠️ **HIGH RISK**
Create or renew a self-signed certificate.

**Use Cases**: Self-signed certificate management, test environment certificate creation
**Warning**: Executes certificate creation/renewal. Requires appropriate GCM user permissions.

---

## 7️⃣ Integration Management

Tools for managing external system integration configurations.

### Read-Only Tools

#### `get_all_intergration`
Retrieve all integration configurations with pagination.

**Use Cases**: List integrations, verify integration types

---

## 8️⃣ User Management

Tools for querying user information.

### Read-Only Tools

#### `get_user_details_by_username`
Retrieve user details by username or email address.

**Use Cases**: View user information, account verification

---

## 🔒 Security and Access Control

### Risk Levels

All access control is enforced by GCM's built-in RBAC (Role-Based Access Control). The relay does not implement additional authorization layers.

- **SAFE** (22 tools): Read-only data access, no system state changes
- **MODERATE** (1 tool): Limited state changes such as ticket creation
- **HIGH** (3 tools): Critical state changes such as policy creation and certificate renewal

**Note**: Tool access permissions are managed through GCM user roles, not by the relay.

---

## 📝 Usage Examples

### Basic Queries
```bash
# Search policies
/gcm search for active policies

# Get certificate details
/gcm get certificate information
```

### Violation Management
```bash
# Display violation dashboard
/gcm show violation statistics

# Create violation ticket (ops/admin)
/gcm create a new violation ticket
```

### Certificate Management
```bash
# Renew certificate (admin)
/gcm renew CA-signed certificate
```

---

## 🔍 Technical Details

- **Authentication**: OAuth2/OIDC (via Keycloak)
- **Transport**: stdio (Phase 1) / HTTP (Phase 2)
- **Audit**: All operations logged to `/logs/audit.jsonl`
- **Deployment**: Via Docker Compose

---

**Created**: 2026-04-06  
**Version**: 1.0  
**Target**: gcm-mcp-relay Phase 1
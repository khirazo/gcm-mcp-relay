#!/bin/bash
# MCP Server Test Script for GCM MCP Relay
# Tests stdio mode by sending JSON-RPC requests in sequence to a single container instance

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== GCM MCP Relay Test Script ===${NC}"
echo ""
echo -e "${YELLOW}Testing MCP protocol with sequential requests in a single session${NC}"
echo ""

# Create a temporary file for requests
REQUESTS_FILE=$(mktemp)

# Write all requests to the file (one per line)
# MCP 2024-11-05 protocol version
cat > "$REQUESTS_FILE" << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF

echo -e "${GREEN}Sending requests:${NC}"
echo -e "${BLUE}1. initialize (MCP 2024-11-05)${NC}"
echo -e "${BLUE}2. tools/list${NC}"
echo ""

echo -e "${YELLOW}Starting GCM MCP Relay and sending requests...${NC}"
echo ""

# Send all requests to the server and capture output
OUTPUT=$(cat "$REQUESTS_FILE" | docker compose run --rm -T gcm-mcp-relay 2>&1)

# Clean up temp file
rm "$REQUESTS_FILE"

# Extract JSON responses (lines starting with {)
RESPONSES=$(echo "$OUTPUT" | grep -E '^\{')

# Parse and display each response
echo -e "${GREEN}=== Test Results ===${NC}"
echo ""

# Response 1: Initialize
echo -e "${BLUE}Test 1: Initialize${NC}"
INIT_RESPONSE=$(echo "$RESPONSES" | sed -n '1p')
if echo "$INIT_RESPONSE" | jq -e '.result' > /dev/null 2>&1; then
    echo "$INIT_RESPONSE" | jq '{protocolVersion: .result.protocolVersion, serverInfo: .result.serverInfo, capabilities: .result.capabilities}'
else
    echo "$INIT_RESPONSE" | jq '.'
fi
echo ""

# Response 2: Tools List
echo -e "${BLUE}Test 2: List Tools${NC}"
TOOLS_RESPONSE=$(echo "$RESPONSES" | sed -n '2p')
if echo "$TOOLS_RESPONSE" | jq -e '.result.tools' > /dev/null 2>&1; then
    TOOL_COUNT=$(echo "$TOOLS_RESPONSE" | jq '.result.tools | length')
    echo -e "${GREEN}Found $TOOL_COUNT tools${NC}"
    echo ""
    echo "$TOOLS_RESPONSE" | jq '.result.tools[] | {name: .name, description: .description}' | head -20
    if [ "$TOOL_COUNT" -gt 10 ]; then
        echo -e "${YELLOW}... (showing first 10 tools)${NC}"
    fi
else
    echo "$TOOLS_RESPONSE" | jq '.'
fi
echo ""

echo -e "${GREEN}=== All tests completed ===${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "- Initialize: $(echo "$RESPONSES" | sed -n '1p' | jq -r 'if .result then "✓ Success" else "✗ Failed" end')"
echo "- Tools List: $(echo "$RESPONSES" | sed -n '2p' | jq -r 'if .result.tools then "✓ Success (" + (.result.tools | length | tostring) + " tools)" else "✗ Failed" end')"
echo ""
echo -e "${YELLOW}Note: GCM MCP Relay exposes all tools from GCM built-in MCP server${NC}"
echo -e "${YELLOW}      Access control is enforced by GCM's RBAC (user-based permissions)${NC}"

# Made with Bob
#!/bin/bash
# Script to display environment variables formatted for Railway

echo "=========================================="
echo "Environment Variables for Railway"
echo "=========================================="
echo ""
echo "Copy and paste these into Railway dashboard:"
echo "(Go to: Railway Dashboard → Your Service → Variables tab)"
echo ""
echo "---"
cat backend/.env
echo "---"
echo ""
echo "📋 Tip: Select and copy all lines above (between the --- markers)"
echo ""
echo "Then in Railway:"
echo "1. Click 'New Variable' or 'Raw Editor'"
echo "2. Paste all lines"
echo "3. Click 'Add' or 'Save'"
echo "4. Wait for auto-redeploy (2-3 minutes)"
echo ""

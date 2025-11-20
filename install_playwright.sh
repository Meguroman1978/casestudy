#!/bin/bash
# Install Playwright browsers for production deployment
echo "Installing Playwright browsers..."
playwright install --with-deps chromium
echo "Playwright installation complete"

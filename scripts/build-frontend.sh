#!/bin/bash

# VaultSentinel Frontend Build Script
# This script builds the TypeScript React frontend for production

set -e

echo "🏗️ Building VaultSentinel Frontend..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the VaultSentinel root directory"
    exit 1
fi

# Navigate to UI directory
cd packages/ui

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed. Please install npm first."
    exit 1
fi

echo "📦 Installing dependencies..."
npm install

echo "🔧 Setting up environment..."
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
fi

echo "🎨 Building for production..."
npm run build

echo "✅ Frontend built successfully!"
echo "📁 Build output: packages/ui/dist/"
echo "🌐 The built frontend will be served by the FastAPI backend at http://localhost:8000"

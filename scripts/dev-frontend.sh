#!/bin/bash

# VaultSentinel Frontend Development Script
# This script sets up and runs the TypeScript React frontend in development mode

set -e

echo "🚀 Starting VaultSentinel Frontend Development..."

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
    echo "✅ Created .env file. You may need to adjust the API URL."
fi

echo "🎨 Starting development server..."
echo "🌐 Frontend will be available at: http://localhost:3000"
echo "🔗 Make sure the backend is running on: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the development server"
echo ""

npm run dev

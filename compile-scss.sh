#!/bin/bash

# Simple script to compile SCSS using the installed sass package

echo "Compiling SCSS to CSS..."
cd /Users/l/work/ulwazi

# Check if we have sass available
if command -v sass &> /dev/null; then
    echo "Using global sass..."
    sass ulwazi/theme/ulwazi/static/css/main.scss ulwazi/theme/ulwazi/static/css/vanilla-main.css
elif [ -f "node_modules/.bin/sass" ]; then
    echo "Using local sass..."
    ./node_modules/.bin/sass ulwazi/theme/ulwazi/static/css/main.scss ulwazi/theme/ulwazi/static/css/vanilla-main.css
else
    echo "Error: sass not found. Please install sass first."
    exit 1
fi

echo "SCSS compilation complete!"

#!/bin/bash

# Build frontend and copy to Django static files
echo "Building frontend..."
cd frontend
npm run build
cd ..

if [ $? -eq 0 ]; then
    echo "Build successful. Copying files to Django staticfiles directory..."
    # Clean old assets and copy new ones
    rm -rf backend/staticfiles/assets
    cp -r frontend/dist/* backend/staticfiles/
    
    echo "✅ Frontend build complete! You can now run: python manage.py runserver"
else
    echo "❌ Build failed. Please check the error messages above."
    exit 1
fi

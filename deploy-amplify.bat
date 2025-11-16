@echo off
REM AWS Amplify Deployment Script for AgentMarket (Windows)
REM Quick reference for manual deployment testing

setlocal enabledelayedexpansion

echo.
echo ============================================
echo 🚀 AgentMarket AWS Amplify Deployment Setup
echo ============================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js is not installed. Please install Node.js first.
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i

echo ✅ Node.js version: %NODE_VERSION%
echo ✅ npm version: %NPM_VERSION%
echo.

REM Install dependencies
echo 📦 Installing dependencies...
call npm ci
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install dependencies
    exit /b 1
)
echo ✅ Dependencies installed
echo.

REM Run type check
echo 🔍 Running TypeScript type check...
call npm run type-check
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Type check failed
    exit /b 1
)
echo ✅ Type check passed
echo.

REM Build for production
echo 🔨 Building for production...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Build failed
    exit /b 1
)
echo ✅ Build completed successfully
echo.

REM List build output
echo 📂 Build artifacts:
dir /s /b .next\
echo.

echo ✅ Ready for AWS Amplify deployment!
echo.
echo Next steps:
echo 1. Commit these changes: git add . ^&^& git commit -m "Ready for AWS Amplify deployment"
echo 2. Push to GitHub: git push origin main
echo 3. Go to https://console.aws.amazon.com/amplify/ and connect your repo
echo 4. Amplify will automatically deploy using amplify.yml
echo.
echo The app will be available at: https://main.xxxxx.amplifyapp.com
echo.

pause

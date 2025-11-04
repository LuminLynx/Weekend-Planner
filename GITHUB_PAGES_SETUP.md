# GitHub Pages Setup

## Status
✅ GitHub Pages has been configured for the Weekend Planner repository.

## URL
The GitHub Pages site will be available at:
**https://luminlynx.github.io/Weekend-Planner/**

## What Was Done

1. **Created Documentation Site** (`docs/index.html`)
   - Professional landing page with project information
   - Responsive design with gradient styling
   - Key features and technology stack overview
   - Quick start guide
   - Links to GitHub repository

2. **Added GitHub Actions Workflow** (`.github/workflows/pages.yml`)
   - Automatic deployment on push to main/master branch
   - Manual workflow dispatch option
   - Uses official GitHub Pages actions for deployment

3. **Jekyll Configuration** (`docs/.nojekyll`)
   - Disables Jekyll processing for faster deployment

## Activation Steps

To make the GitHub Pages site live, a repository administrator needs to:

1. Go to the repository **Settings** > **Pages**
2. Under "Build and deployment":
   - Source: Select "GitHub Actions"
3. The workflow will automatically deploy when changes are merged to the main branch

Alternatively, if using branch-based deployment:
1. Go to repository **Settings** > **Pages**
2. Under "Build and deployment":
   - Source: Select "Deploy from a branch"
   - Branch: Select "main" (or "master") and "/docs" folder
3. Click **Save**

## Verification

Once enabled, the site should be accessible at:
- **Primary URL**: https://luminlynx.github.io/Weekend-Planner/
- Status can be checked in repository Settings > Pages

The landing page includes:
- Project overview and description
- Key features showcase
- Quick start instructions
- Technology stack information
- Links to GitHub repository

## Notes

- The GitHub Actions workflow will deploy automatically on every push to the main branch
- Custom domain can be configured in repository settings if desired
- The site is static HTML and requires no server-side processing

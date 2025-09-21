# 🎤 mcpypi Guest Book Website

A beautiful, interactive guest book built with Astro that showcases the mcpypi community!

## ✨ Features

- **Responsive Design** - Looks great on all devices
- **Dynamic Stats** - Auto-calculated community metrics
- **Structured Data** - YAML frontmatter for easy management
- **Search & Filter** - Find signatures by tags, packages, or features
- **ASCII Art Gallery** - Beautiful retro-style signatures
- **GitHub Integration** - Direct links to contributor profiles

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 📁 Structure

```
docs/
├── src/
│   ├── content/
│   │   ├── config.ts          # Content collection schema
│   │   └── guestbook/         # Symlink to ../guestbook/
│   ├── layouts/
│   │   └── Layout.astro       # Base page layout
│   ├── pages/
│   │   └── index.astro        # Guest book homepage
│   └── components/            # Reusable components
├── package.json
└── astro.config.mjs
```

## 🎨 Customization

### Colors & Theme
The site uses a purple-to-blue gradient theme with accent colors:
- **Primary**: Yellow/Orange gradient
- **Secondary**: Purple, Blue, Green
- **Background**: Dark gradient (purple → blue → indigo)

### Adding Features
1. **Search**: Add search functionality in `src/components/Search.astro`
2. **Filters**: Create filter components for tags/packages
3. **Analytics**: Track popular features and packages

## 🛠️ Development

### Content Collections
Signatures use structured YAML frontmatter:

```yaml
---
name: "Developer Name"
title: "Cool Title"
github: "username"
date: "2025-09-06"
packages: ["package1", "package2"]
mcpypi_features_used: ["security_scanning", "health_scoring"]
tags: ["python", "fastapi", "security"]
signature_number: 1
---
```

### Auto-deployment
- Pushes to `main` automatically deploy to GitHub Pages
- Changes to `guestbook/` or `docs/` trigger rebuilds
- Uses GitHub Actions for CI/CD

## 📊 Analytics

The site automatically calculates:
- Total signatures
- PyPI packages mentioned
- mcpypi features used
- ASCII art pieces

## 🎯 Future Enhancements

- [ ] Search functionality
- [ ] Tag-based filtering
- [ ] Package popularity charts
- [ ] mcpypi feature usage analytics
- [ ] Contributor timeline
- [ ] ASCII art gallery page

---

*Built with ❤️ using Astro and Tailwind CSS*
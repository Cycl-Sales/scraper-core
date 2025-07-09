# Cycl Sales Dashboard - Frontend Only

A modern, responsive sales dashboard built with React, TypeScript, and Tailwind CSS. This is a frontend-only version of the original Cycl Sales Dashboard that was designed to integrate with GoHighLevel CRM.

## Recent Cleanup (January 2025)

This project has been cleaned up to improve maintainability and reduce technical debt:

### Files Removed
- **Temporary files**: `temp.html`, `generate-backend-docs.js`, `generate-pdf.js`
- **Generated documentation**: `backend-development-plan.html`, `backend-implementation-guide.html`
- **Generated assets**: `generated-icon.png`
- **Screenshot assets**: `attached_assets/` directory with 6 PNG files
- **System files**: `.DS_Store` files

### Dependencies Cleaned
- **Removed unused dependencies**: `@jridgewell/trace-mapping`, `next-themes`, `react-router-dom`
- **Fixed routing**: Standardized on `wouter` for routing (removed conflicting `react-router-dom`)
- **Updated schema**: Replaced Drizzle ORM schema with TypeScript interfaces for frontend-only usage

### Code Quality Improvements
- **TypeScript fixes**: Resolved all type errors and improved type safety
- **Consistent routing**: Fixed routing inconsistencies across components
- **Enhanced .gitignore**: Added comprehensive patterns for better version control
- **Build optimization**: Removed unused asset references from Vite config

### Current Status
✅ All TypeScript errors resolved  
✅ Project builds successfully  
✅ No unused dependencies  
✅ Clean project structure  
✅ Consistent routing implementation  

## Features

- **Modern UI**: Built with React 18, TypeScript, and Tailwind CSS
- **Interactive Charts**: Beautiful data visualizations using Recharts
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Dark Theme**: Sleek dark interface optimized for data visualization
- **Mock Data**: Realistic demo data for showcasing the dashboard

## Pages

- **Dashboard**: Overview with KPI cards and charts
- **Contacts**: Contact management with search and filtering
- **Calls**: Call tracking and analytics
- **AI Assistant**: AI-powered features (demo)
- **Automation Rules**: Workflow automation (demo)
- **Response Templates**: Email/SMS templates (demo)
- **AI Training**: AI model training interface (demo)

## Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS
- **UI Components**: Radix UI, Lucide React icons
- **Charts**: Recharts for data visualization
- **Routing**: Wouter for client-side routing
- **Build Tool**: Vite for fast development and building

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cycl-sales-dashboard-main
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to `http://localhost:3000`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run check` - Type checking

## Project Structure

```
client/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Page components
│   ├── lib/           # Utilities and mock data
│   └── hooks/         # Custom React hooks
shared/
└── schema.ts          # TypeScript type definitions
```

## Mock Data

The application uses realistic mock data to demonstrate the dashboard functionality:

- **Dashboard Metrics**: KPI data including contacts, opportunities, revenue
- **Contacts**: Sample contact records with various sources and tags
- **Opportunities**: Sales pipeline data
- **Chart Data**: Call volume, engagement, and pipeline performance data

## Customization

### Adding Real Data

To integrate with real data sources:

1. Replace the mock API calls in `client/src/lib/mockData.ts`
2. Update the data fetching logic in components
3. Modify the schema types in `shared/schema.ts` as needed

### Styling

The application uses Tailwind CSS for styling. You can customize:

- Colors in `tailwind.config.ts`
- Component styles in individual component files
- Global styles in `client/src/index.css`

## Deployment

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Deploy to Static Hosting

You can deploy to any static hosting service:

- **Vercel**: `vercel --prod`
- **Netlify**: `netlify deploy --prod`
- **GitHub Pages**: Configure GitHub Actions
- **AWS S3**: Upload `dist/` contents to S3 bucket

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For questions or issues, please open an issue on GitHub. 
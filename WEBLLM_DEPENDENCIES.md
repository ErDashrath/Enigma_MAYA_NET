# 📦 **WebLLM Dependencies & Setup**

## 🚀 **Minimal Setup (Just WebLLM)**

For the most basic WebLLM implementation, you only need:

### **Zero Dependencies**
The `MINIMAL_WEBLLM_SERVICE.ts` requires **NO npm packages**! It uses:
- Browser's native APIs
- Dynamic import of WebLLM from CDN
- LocalStorage for caching
- Standard TypeScript/JavaScript

```bash
# No npm install needed for minimal setup!
# Just copy MINIMAL_WEBLLM_SERVICE.ts to your project
```

---

## 🎨 **With UI Components**

If you want the full UI experience from EchoLearn:

### **Core UI Dependencies**
```bash
npm install react react-dom typescript
npm install framer-motion lucide-react clsx
```

### **For Advanced UI Components**
```bash
npm install @radix-ui/react-dialog @radix-ui/react-progress
npm install @radix-ui/react-select @radix-ui/react-tooltip
npm install @radix-ui/react-switch @radix-ui/react-toast
```

### **For Styling (if using Tailwind)**
```bash
npm install tailwindcss tailwind-merge class-variance-authority
npm install -D @tailwindcss/typography autoprefixer postcss
```

---

## 🛠️ **Development Dependencies**

### **TypeScript Setup**
```bash
npm install -D typescript @types/react @types/react-dom
npm install -D @typescript-eslint/eslint-plugin @typescript-eslint/parser
```

### **Build Tools**
```bash
npm install -D vite @vitejs/plugin-react
```

---

## 📋 **Package.json Example**

### **Minimal React + WebLLM**
```json
{
  "name": "my-webllm-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.539.0",
    "framer-motion": "^12.23.12"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.0.2",
    "vite": "^5.4.19",
    "@vitejs/plugin-react": "^4.7.0"
  }
}
```

### **Full Featured Setup**
```json
{
  "name": "my-webllm-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "framer-motion": "^12.23.12",
    "lucide-react": "^0.539.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^3.3.1",
    "@radix-ui/react-dialog": "^1.1.14",
    "@radix-ui/react-progress": "^1.1.7",
    "@radix-ui/react-toast": "^1.2.14",
    "@radix-ui/react-tooltip": "^1.2.7"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.0.2",
    "vite": "^5.4.19",
    "@vitejs/plugin-react": "^4.7.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.24"
  }
}
```

---

## 🎯 **Dependency Explanations**

### **Core Runtime**
- **react/react-dom**: UI framework
- **typescript**: Type safety

### **WebLLM Specific**
- **None!** WebLLM loads dynamically from CDN
- Uses browser's native IndexedDB and localStorage

### **UI Enhancement**
- **framer-motion**: Smooth animations for download progress
- **lucide-react**: Icons (download, settings, etc.)
- **clsx/tailwind-merge**: Conditional styling utilities

### **Advanced UI**
- **@radix-ui/react-\***: Accessible UI components
- **tailwindcss**: Utility-first CSS framework

### **Development**
- **vite**: Fast build tool
- **@vitejs/plugin-react**: React support for Vite
- **@types/\***: TypeScript definitions

---

## 🚀 **Quick Start Commands**

### **Option 1: Minimal Setup**
```bash
# Create new project
npm create vite@latest my-webllm-app -- --template react-ts
cd my-webllm-app

# Copy MINIMAL_WEBLLM_SERVICE.ts to src/
# Start using WebLLM immediately!

npm run dev
```

### **Option 2: Full Setup**
```bash
# Create project with full dependencies
npm create vite@latest my-webllm-app -- --template react-ts
cd my-webllm-app

# Install dependencies
npm install framer-motion lucide-react clsx tailwind-merge
npm install @radix-ui/react-dialog @radix-ui/react-progress

# Copy desired files from EchoLearn
# Adapt import paths and start building!

npm run dev
```

---

## 🔧 **Vite Configuration**

### **vite.config.ts**
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // Enable top-level await for WebLLM
  optimizeDeps: {
    esbuildOptions: {
      target: 'es2022'
    }
  },
  build: {
    target: 'es2022'
  }
})
```

---

## 🌐 **CDN Alternative**

You can also include WebLLM directly in HTML:

```html
<!DOCTYPE html>
<html>
<head>
  <script type="module">
    import { MLCEngine } from 'https://esm.run/@mlc-ai/web-llm';
    // Use WebLLM directly without any build tools
  </script>
</head>
</html>
```

---

## ✅ **Summary**

- **Minimal**: Copy `MINIMAL_WEBLLM_SERVICE.ts` + basic React setup
- **Enhanced**: Add UI libraries for better UX
- **Full**: Copy EchoLearn components + all dependencies
- **CDN**: Use WebLLM directly in browser without bundlers

Choose the approach that fits your project's complexity! 🎯
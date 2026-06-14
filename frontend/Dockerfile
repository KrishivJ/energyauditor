# Stage 1 dev image: runs the Vite dev server with HMR and an /api proxy to the
# backend service. For production you would `npm run build` and serve dist/ via
# a static host (Vercel/Netlify) — noted in DESIGN.md.
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]

cd src/types;
wget http://127.0.0.1:8000/openapi.json -O openapi.json;
npx openapi-typescript openapi.json --output ./openapi.ts;
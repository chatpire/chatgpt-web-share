wget http://127.0.0.1:8000/openapi.json -O src/types/openapi.json;
npx openapi-typescript src/types/openapi.json --output src/types/openapi.ts;

cd ../backend;
python manage.py get_config_schema > ../frontend/src/types/config_schema.json;
python manage.py get_credentials_schema > ../frontend/src/types/credentials_schema.json;
echo "Updated API schemas."
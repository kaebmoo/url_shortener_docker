# https://stackoverflow.com/questions/74307126/uvicorn-run-on-specified-python-version
python -m uvicorn shortener_app.main:app --reload
pm2 start uvicorn --name shortener_app -- shortener_app.main:app
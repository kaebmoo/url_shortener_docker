cd shortener_app
docker build -t kaebmoo/shortener_app:nt .
docker run --name shortener_app -p 8000:8000 kaebmoo/shortener_app:nt

cd user_management
docker build -t kaebmoo/user_management:nt .
docker run --name user_management -p 8080:5000 kaebmoo/user_management:nt

cd web_scan
docker build -t kaebmoo/web_scan:nt .
docker run --name web_scan kaebmoo/web_scan:nt

รัน container ใน network เดียวกัน
docker run -d --name shortener_app --env-file ./config.env --network nt-network -p 8000:8000 kaebmoo/shortener_app:nt

docker run -d --name shortener_app --network nt-network -p 8000:8000 kaebmoo/shortener_app:nt
docker run -d --name user_management --network nt-network -p 8080:5000 kaebmoo/user_management:nt
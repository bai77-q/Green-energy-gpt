echo 'production mode...'
gunicorn app.main:app --workers 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:7000 --keyfile=../ai.f2ee.com_nginx/ai.f2ee.com.key --certfile=../ai.f2ee.com_nginx/ai.f2ee.com_bundle.crt  &>> /home/ubuntu/server.log

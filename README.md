## **Учебный проект: Веб-приложение "Продуктовый помощник"..**
![example workflow](https://github.com/Dashynja0203foodgram-project-react/.github/workflows/foodgram_workflow.yml/badge.svg)
### Где посмотреть проект 
Посмотреть проект можно по адресу: 51.250.30.119
### **Как запустит проект**

1. Клонировать его из репозитория.
`git clone ...`
2. Создать файл `.env` в папке `infra` и определетить _свои_ следующие переменные :
```
SECRET_KEY 
EMAIL_HOST 
DB_ENGINE= # указываем, с чем рабоатем
DB_NAME= # имя базы данных
POSTGRES_USER= # логин для подключения к базе данных
POSTGRES_PASSWORD= # пароль для подключения к БД (установите свой)
DB_HOST=# название сервиса (контейнера)
DB_PORT=# порт для подключения к БД
```
3. Запускаем сборку из папки с файлом **docker-compose.yaml**: 
`docker-compose up -d --build `
4. Выполните по очереди команды:
```
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --no-input 
```
Готово! проект запущен на локальном хосте.


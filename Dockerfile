FROM python:latest

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
ENV TZ=Europe/Moscow
ENV REMINDER_BOT_ADMINS=156302877
ENV REMINDER_BOT_CONNECTION_STRING=postgresql+asyncpg://postgress:hunter2@db/reminder_bot_db
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


COPY ./source /app
EXPOSE 8000
CMD ["python", "bot.py"]
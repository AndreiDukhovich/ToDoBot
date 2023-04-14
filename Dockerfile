FROM python:3.10
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
RUN rm -f /etc/localtime
RUN ln -s /usr/share/zoneinfo/Europe/Minsk /etc/localtime
COPY . /bot
CMD python bot.py
FROM python:3.9.13-bullseye

# Install dumb-init for container init process 
# See more at: https://github.com/Yelp/dumb-init
RUN curl -sSfLo /usr/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.2.5/dumb-init_1.2.5_x86_64
RUN chmod 755 /usr/bin/dumb-init

ADD ./ /dalle-mini-discord/
WORKDIR /dalle-mini-discord

RUN python -m pip install -r requirements.txt

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["python", "bot.py"]
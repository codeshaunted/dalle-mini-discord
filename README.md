# dalle-mini-discord
A simple Discord bot written in Python designed around [DALL-E Mini](https://github.com/borisdayma/dalle-mini).
# Commands
dalle-mini-discord only has one command, `/generate prompt:{prompt}`, which will generate an array of images using the specified DALL-E Mini backend URL.
# Installation
## Prerequisites
dalle-mini-discord requires Python 3.9 or later. First, clone dalle-mini-discord and change directories into the cloned repository. You now must install the required Python libraries, which can be done with the following command:
```
python -m pip install -r requirements.txt
```
## Configuration
Before running dalle-mini-discord, you must first configure the `config.json` file with a Discord bot token in the `BOT_TOKEN` field. There are also configuration options to change the DALL-E Mini backend URL, the collage image format and the image select timeout.
## Running
To run dalle-mini-discord, just run the bot.py file in your Python 3.9+ interpreter:
```
python bot.py
```

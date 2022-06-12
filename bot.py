import asyncio
import base64
import io
import json
import logging

from discord import app_commands
from PIL import Image
import aiohttp
import discord
import numpy


class DALLEMini(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def update_status(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{len(self.guilds)} servers | /generate'))


intents = discord.Intents.default()
client = DALLEMini(intents=intents)
config: object


class ImageSelect(discord.ui.Select):
    def __init__(self, collage: discord.File, images: list[discord.File]):
        options = [discord.SelectOption(label='Image collage')] + [discord.SelectOption(label=f'Image {i + 1}') for i in range(len(images))]
        super().__init__(placeholder='Select an image',
                         min_values=1, max_values=1, options=options)
        self.collage = collage
        self.images = images

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.values[0] == 'Image collage':
            logging.debug(f'{interaction.user} (ID: {interaction.user.id}) requested an image collage')
            self.collage.fp.seek(0)
            await interaction.edit_original_message(attachments=[self.collage])
        else:
            image_index = int(self.values[0].split(' ')[-1]) - 1
            logging.debug(f'{interaction.user} (ID: {interaction.user.id}) requested image #{image_index + 1}')
            self.images[image_index].fp.seek(0)
            await interaction.edit_original_message(attachments=[self.images[image_index]])


class ImageSelectView(discord.ui.View):
    def __init__(self, collage: discord.File, images: list[discord.File], timeout: float):
        super().__init__(timeout=timeout)
        self.add_item(ImageSelect(collage, images))


async def generate_images(prompt: str) -> list[io.BytesIO]:
    async with aiohttp.ClientSession() as session:
        async with session.post(config['DALLE_MINI_BACKEND_URL'], json={'prompt': prompt}) as response:
            if response.status == 200:
                response_data = await response.json()
                images = [io.BytesIO(base64.decodebytes(bytes(image, 'utf-8')))
                          for image in response_data['images']]
                return images
            else:
                return None


def make_collage_sync(images: list[io.BytesIO], wrap: int) -> io.BytesIO:
    image_arrays = [numpy.array(Image.open(image)) for image in images]
    for image in images:
        image.seek(0)
    collage_horizontal_arrays = [numpy.hstack(
        image_arrays[i:i + wrap]) for i in range(0, len(image_arrays), wrap)]
    collage_array = numpy.vstack(collage_horizontal_arrays)
    collage_image = Image.fromarray(collage_array)
    collage = io.BytesIO()
    collage_image.save(collage, format=config['COLLAGE_FORMAT'])
    collage.seek(0)
    return collage


async def make_collage(images: list[io.BytesIO], wrap: int) -> io.BytesIO:
    images = await asyncio.get_running_loop().run_in_executor(None, make_collage_sync, images, wrap)
    return images


@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user} (ID: {client.user.id})')
    await client.update_status()


@client.event
async def on_guild_join(guild: discord.Guild):
    await client.update_status()


@client.tree.command()
async def generate(interaction: discord.Interaction, prompt: str):
    '''Generates images based on prompt given.'''
    logging.info(f'Got request to generate images with prompt "{prompt}" from {interaction.user} (ID: {interaction.user.id})')
    await interaction.response.defer(thinking=True)

    images = None
    attempt = 0
    while not images:
        if attempt > 0:
            logging.warning(f'Image generate request failed on attempt {attempt} for prompt "{prompt}" issued by {interaction.user} (ID: {interaction.user.id})')
        attempt += 1
        images = await generate_images(prompt)

    logging.info(f'Successfully generated images with prompt "{prompt}" from {interaction.user} (ID: {interaction.user.id}) on attempt {attempt}')
    collage = await make_collage(images, 3)
    collage = discord.File(collage, filename=f'collage.{config["COLLAGE_FORMAT"]}')
    images = [discord.File(images[i], filename=f'{i}.jpg') for i in range(len(images))]
    await interaction.followup.send(f'`{prompt}`', file=collage, view=ImageSelectView(collage, images, timeout=config['IMAGE_SELECT_TIMEOUT']))

if __name__ == '__main__':
    logging.basicConfig(filename='dalle-mini-discord.log',
                        encoding='utf-8', level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler())
    with open('config.json', 'r') as file:
        config = json.load(file)
        client.run(config['BOT_TOKEN'])

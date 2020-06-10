import argparse
import configparser
import discord
import asyncio
import requests
from bs4 import BeautifulSoup
from mcstatus import MinecraftServer
from discord.ext import commands
from discord.utils import get

bot = commands.Bot(command_prefix='!', help_command=None)
server = MinecraftServer.lookup('jfssminecraft.digital')

@bot.event
async def on_ready():
    """Prints a startup message."""
    print(str(bot.user) + ' is online.')
    await bot.change_presence(activity=discord.Game(name='!help'))

# Utility function to redirect users to use the bot-commands channel
def redirect():
    emb = discord.Embed(
            description ='Error: Please use this command in #bot-commands.',
            title='Error',
            color=0x9b59b6
        )
    emb.set_footer(text='If you need help joining the server, read #lobby.')
    return emb

# Generates embed error message
def error_response(error_text):
    emb = discord.Embed(
            description=error_text,
            title='Error',
            color=0x9b59b6
        )
    emb.set_footer(text='For more help with commands, use !help.')
    return emb

# Removes shop listing on reaction
@bot.event
async def on_raw_reaction_add(payload):
    channel = bot.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)
    usr = bot.get_user(payload.user_id)
    emote_name = payload.emoji.name
    seller = msg.embeds[0].title
    if emote_name == '✅' and str(usr) == str(seller):
        await msg.delete()

@bot.command()
async def help(ctx):
    # Skip if not used in bot-commands
    if ctx.message.channel.id != int(CHANNEL):
        await ctx.message.channel.send(embed=redirect())
    else:
        emb = discord.Embed(
            title='Help',
            color=0x9b59b6
        )
        emb.set_footer(text='If you need help joining the server, read #lobby.')
        emb.add_field(name='!whitelist {username}', value='Whitelists the username on the server', inline=False)
        emb.add_field(name='!status', value='Display up to 12 names of players on the server', inline=False)
        emb.add_field(name='!listing {buy/sell} {quantity} {price/item} {item name}', value='Creates an item listing in the advertisements channale', inline=False)
        await ctx.channel.send(embed=emb)


@bot.command()
async def whitelist(ctx, minecraftUser):
    # Skip if not used in bot-commands
    if ctx.message.channel.id != int(CHANNEL):
        await ctx.message.channel.send(embed=redirect())
    # Discord SRV integration
    else:
        playerRole = get(ctx.message.guild.roles, name='Player')
        consoleChat = bot.get_channel(717954805678604299)
        whitelistMsg = await consoleChat.send(f'whitelist add {minecraftUser}')
        await ctx.message.author.add_roles(playerRole)
        await whitelistMsg.delete(delay=10)
        emb = discord.Embed(
            description ='{} has been added to the whitelist.'.format(minecraftUser),
            title='Whitelist',
            color=0x3300bd
        )
        emb.set_footer(text='If you need help joining the server, read #lobby.')
        await ctx.channel.send(embed=emb)

@bot.command()
async def status(ctx):
    # Skip if not used in bot-commands
    if ctx.message.channel.id != int(CHANNEL):
        await ctx.message.channel.send(embed=redirect())
    else:
        emb = discord.Embed(
            title='',
        )
        emb.set_thumbnail(url='https://instagram.fybz2-2.fna.fbcdn.net/v/t51.2885-19/s320x320/102372759_252218775872073_7622047837647273984_n.jpg?_nc_ht=instagram.fybz2-2.fna.fbcdn.net&_nc_ohc=V1U_UcQypBEAX-2BAMb&oh=f52cbedebd5000888123c7431a919321&oe=5F065C34')
        emb.set_footer(text='If you need help joining the server, read #lobby.')
        try:
            status = server.status()
            ping = server.ping()
            players = status.players.sample
            emb.title = 'Server is online :green_circle:'
            emb.color=0x00C851
            emb.add_field(name='Ping', value=f'{ping:.2f}ms')
            # At least 1 player on
            if players is not None:
                emb.add_field(name='Total Online', value=f'{status.players.online}/{status.players.max}')
                all_players = ''
                players.sort(key=lambda x:x.name.lower())
                for i in players:
                    all_players += (f'{i.name}\n')
                emb.add_field(name='Players', value=all_players, inline=False)
            else:
                emb.add_field(name='Total Online', value='0')
        # Catch any exception mcstatus throws
        except:
            emb.title = 'Server is offline :red_circle:'
            emb.color=0xff4444
        await ctx.channel.send(embed=emb)


# Create item listing in #advertisement channel
@bot.command()
async def listing(ctx, action='', quantity='', price='', *item):
    # Skip if not used in bot-commands
    if ctx.message.channel.id != int(CHANNEL):
        await ctx.message.channel.send(embed=redirect())
    else:
        author = ctx.message.author
        emb = discord.Embed(
            title=str(author),
            description="Click the ✅ to mark the trade as completed"
        )
        if action.lower() == 'buy':
            emb.add_field(name='Action', value='Buying')
            emb.color = 0x4285F4
        elif action.lower() == 'sell':
            emb.add_field(name='Action', value='Selling')
            emb.color = 0xf04747
        else:
            await ctx.channel.send(embed=error_response("Error: Action must be buy or sell"))
            
        # Join with _ for url retrieval
        item = list(item)
        for i in range(len(item)):
            item[i] = item[i].lower()
        processed_str = '_'.join(item)

        # attempt to get item image
        try:
            content = 'https://gamepedia.cursecdn.com/minecraft_gamepedia/2/21/Missing_Texture_Block.png?version=4ee54be32af8a7e50d994bff56a2778d'
            response = requests.get(f'https://minecraft.gamepedia.com/{processed_str}')
            # Remove _ for display text and image alt text comparison
            processed_str = processed_str.replace('_', ' ')
            processed_str = processed_str.title()
            data = response.text
            soup = BeautifulSoup(data, 'html.parser')
            # Check over all images on current page
            # Breaks upon finding the first image with alt text containing item name
            all_images = soup.findAll('img')
            for image in all_images:
                # Try getting alt text
                try:
                    # Lowercase comparion, spelling must match exactly
                    if processed_str.lower() in image['alt'].lower():
                        content = image['src']
                        break
                # Image contains no alt text
                except:
                    continue
        # Use missing texture as thumbnail
        except:
            content = 'https://gamepedia.cursecdn.com/minecraft_gamepedia/2/21/Missing_Texture_Block.png?version=4ee54be32af8a7e50d994bff56a2778d'

        emb.set_thumbnail(url=content)
        emb.add_field(name='Item', value=processed_str)
        emb.add_field(name='Quantity', value=quantity)
        emb.add_field(name='Price/Item', value=price)
        emb.set_footer(text="For the item image to load properly, you must match the item name exactly. " +
                        "For more information, visit https://www.digminecraft.com/lists/item_id_list_pc.php")
        shop_channel = bot.get_channel(int(SHOP_CHANNEL))
        msg = await shop_channel.send(embed=emb)
        await msg.add_reaction('✅')
        await ctx.message.delete()

def try_config(config, heading, key):
    """Attempt to extract config[heading][key], with error handling.

    This function wraps config access with a try-catch to print out informative
    error messages and then exit."""
    try:
        section = config[heading]
    except KeyError:
        print("Missing config section [{}]".format(heading))
        sys.exit(1)

    try:
        value = section[key]
    except KeyError:
        print("Missing config key '{}' under section '[{}]'".format(
            key, heading))
        sys.exit(1)
    return value

if __name__ == "__main__":
    # Parse command-line arguments for the token and the config file path.
    # It uses a positional argument for the token and a flag -c/--config to
    # specify the path to the config file.
    parser = argparse.ArgumentParser()
    #parser.add_argument("token")
    parser.add_argument(
        "-c", "--config", help="Config file path", default="config.ini")
    args = parser.parse_args()

    # Parse the config file at the given path, erroring out if keys are missing
    # in the config.
    config = configparser.ConfigParser()
    config.read(args.config)
    try:
        TOKEN = try_config(config, "IDs", "Token")
        CHANNEL = try_config(config, "IDs", "Channel")
        SHOP_CHANNEL = try_config(config, "IDs", "Shop_Channel")
    except KeyError:
        sys.exit(1)

    bot.run(TOKEN)

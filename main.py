import argparse
import configparser
import discord
import asyncio
import requests
from mcstatus import MinecraftServer
from discord.ext import commands
from discord.utils import get

bot = commands.Bot(command_prefix='!', help_command=None)
server = MinecraftServer.lookup('jfssminecraft.digital')

@bot.event
async def on_ready():
    """Prints a startup message."""
    print(str(bot.user) + ' is online.')
    await bot.change_presence(activity=discord.Game(name='!whitelist {username}'))

# Utility function to redirect users to use the bot-commands channel
def redirect():
    emb = discord.Embed(
            description ='Error: Please use this command in #bot-commands.',
            title='Error',
            color=0x9b59b6
            )
    emb.set_footer(text='If you need help joining the server, read #lobby.')
    return emb

@bot.command()
async def whitelist(ctx, minecraftUser):
    # Skip if not used in bot-commands
    if ctx.message.channel.id != 718200381301194882:
        await ctx.message.channel.send(embed=redirect())
    # Discord SRV integration
    else:
        playerRole = get(ctx.message.guild.roles, name='Player')
        whitelistMsg = await ctx.send('whitelist add {}'.format(minecraftUser))
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
    if ctx.message.channel.id != 718200381301194882:
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
    except KeyError:
        sys.exit(1)

    bot.run(TOKEN)

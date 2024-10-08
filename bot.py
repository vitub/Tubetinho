import asyncio
import discord
import files
from discord.ext import commands
from youtube_search import YoutubeSearch
import re
import yt_dlp
from pytube import Playlist


# Imported all the components needed to make the bot work

bot = discord.Bot()

yt_dlp.utils.bug_reports_message = lambda: ''


# yt_dlp parameters

yt_dlp_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(yt_dlp_format_options)

global channelstate
global voice_channel
global userchannel
channelstate = False
voice_channel = ''
playing = False
userchannel = ()
queue = []



def search_and_get_url(title):
    results = YoutubeSearch(title , max_results=1).to_dict()
    for v in results:
        h = ('https://www.youtube.com' + v['url_suffix'])
        return h

     

def get_playlist_videos(playlist_url):
    videosurl = Playlist(playlist_url)

    for video in videosurl.videos:
        queue.append(video.watch_url)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)




#Function that assure that the bot will continue playing the queue after a song ends
async def auto_play_queue(ctx):
    global queue
    global playing

    playing = True

    while True:
        if len(queue) == 0:
            playing = False
            return

        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            return

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            await asyncio.sleep(1)
            continue

        try:
            player = await YTDLSource.from_url(queue[0], loop=bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Error: %s' % e))
            link_text = f"[{player.title}]({queue[0]})"
            response_text = f'**⏯️ Tocando agora:** {link_text}'
            embed = discord.Embed(description=response_text)
            await ctx.send(embed=embed)
            del queue[0]
        except Exception as e:
            pass

@bot.command(description='Toca uma música')
async def play(ctx: commands.Context, *, query: str):
    global channelstate
    global userchannel
    global playing
    global queue

    playlistrep = False

    # Check if the user is in a voice channel and if the bot is already connected to another channel
    if channelstate == True:
        if ctx.author.voice.channel != userchannel:
            return
    else:
        pass

   
    # Connect to the user's voice channel if not already connected
    channel = ctx.author.voice.channel
    if channelstate == False:
        await channel.connect()
        await ctx.respond('**Conectando ao seu canal.**')
        userchannel = channel
        channelstate = True
        files
    else:
        pass

    # Check if the query is a valid URL or playlist
    link = re.match(r"https?://(www\.)?youtube\.com/watch\?v=\S+", query)
    playlist = re.match(r'^https?://(www\.)?youtube\.com/playlist\?list=[\w-]+', query)
 
    try:
        if link:
            url = query
        elif playlist:
            get_playlist_videos(query)
            playlistrep = True
        else:
            url = search_and_get_url(query)

        # Add to queue
        if not playlistrep:
            if url and url not in queue:
                if playing == False:
                        queue.append(url)
                        await ctx.respond('**Adicionei a música na fila!**')
                else:
                    queue.append(url)
                    await ctx.respond('**Adicionei a música na fila!**')
                    pass

            elif url in queue:
                pass
            else:
                await ctx.respond('**Não foi possível encontrar a música.**')
                return  # Ensure we don't proceed if the song couldn't be found

    except Exception as e:
        await ctx.respond('**Erro ao tocar a sua música.**')
        print(f"Error in play command: {e}")
        return  # Prevent further execution if there's an error

    # Add playlist songs to the queue
    if playlistrep:
        await ctx.respond('**Adicionei as suas músicas na fila!**')

    
    # Try to play the music from the queue
    try:
        if queue:
            global player
            server = ctx.guild
            voice_channel = server.voice_client
            player = await YTDLSource.from_url(queue[0], loop=bot.loop)
            voice_channel.play(player, after=lambda e: print('Error: %s' % e))

            link_text = f"[{player.title}]({queue[0]})"
            response_text = f'**⏯️ Tocando agora:** {link_text}'
            embed = discord.Embed(description=response_text)
            await ctx.send(embed=embed)
            del queue[0]
            channelstate = True
            playing = True
    except Exception as e:
        await auto_play_queue(ctx)
        pass
    

@bot.command(description='Toca uma música repetidamente')
async def loop(ctx: object, *, music: str):
    global channelstate
    global voice_channel
    global userchannel
    global playing
    if channelstate == True:
        if ctx.author.voice.channel != userchannel:
            return
    else:
        pass


    #Check if the query is a valid URL
    match = re.match(r"https?://(www\.)?youtube\.com/watch\?v=\S+", music)

    try:
        await ctx.defer()
    except Exception as e:
        pass


    try:
        if match:
            url = music

            pass
        else:
            url = search_and_get_url(music)  
            pass
    except TypeError:
        await ctx.send('**Erro ao tocar a sua música.**')

    
    channel = ctx.author.voice.channel
    if channelstate == False:
        await channel.connect()
        await ctx.respond('**Conectando ao seu canal.**')
        await ctx.respond('**Tocarei essa música repetidamente a partir de agora.**')
        userchannel = channel
        channelstate = True
        files
    else:
        await ctx.respond('**Tocarei essa música repetidamente a partir de agora.**')
        pass


    try:
        player = await YTDLSource.from_url(url, loop=bot.loop)
        ctx.voice_client.play(player, after=lambda e: print('Error: %s' % e))
        playing = True
        link_text = f"[{player.title}]({url})"
        response_text = f'**⏯️ Tocando agora:** {link_text}'
        embed = discord.Embed(description=response_text)
        await ctx.send(embed=embed)
    except Exception as e:
        pass

    while playing:
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            return

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            await asyncio.sleep(1)
            continue

        try:
            player = await YTDLSource.from_url(url, loop=bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Error: %s' % e))
        except Exception as e:
            pass




@bot.command(description='Remove o bot da call')
async def leave(ctx):
    global channelstate
    global voice_channel
    global userchannel
    global queue
    global playing
    
    if channelstate == True:
        if ctx.author.voice.channel != userchannel:
            return
    else:
        pass

    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    
    
    if voice.is_connected():
        await voice.disconnect()
        channelstate = False
        voice_channel = ''
        playing = False
        userchannel = ()
        queue = []
        await ctx.respond('**Me desconectei do canal**')
    else:
        await ctx.respond('Eu não estou conectado a nenhum canal')


@bot.command(description='Para a música')
async def stop(ctx):
    global channelstate
    global userchannel
    global playing
    global queue
    
    if channelstate == True:
        if ctx.author.voice.channel != userchannel:
            return
    else:
        pass
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice.stop()
    queue = []
    playing = False
    await ctx.respond('⏸︎')

    


@bot.command(description='Mostra quantas músicas estão na fila')
async def queue_(ctx):
    global channelstate
    global userchannel
    global queue
    
    if channelstate == True:
        if ctx.author.voice.channel != userchannel:
            return
    else:
        pass

    if len(queue) == 1:
        await ctx.respond('**Tem {} música na fila!**'.format(len(queue)))
    else:
        await ctx.respond('**Tem {} músicas na fila!**'.format(len(queue)))

    

@bot.command(description='Pula a música')
async def skip(ctx):
    global channelstate
    global userchannel
    global queue
    global player
    
    if channelstate == True:
        if ctx.author.voice.channel != userchannel:
            return
    await ctx.respond('**Pulando a música**')
    player = ''
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice.stop()
    await ctx.invoke(bot.get_command('play'), query=queue[0])


@bot.command(description='Limpa a fila')
async def clear(ctx):
    global queue
    await ctx.respond('**Limpei a fila!**')
    queue = []
    
#Command used to diagnostics in the queue
#Uncomment with you want to use it

#@bot.command()
#async def status(ctx):
#    await ctx.respond(queue)
#    await ctx.respond(len(queue))
#    await ctx.respond(queue[0])



#Add a function that makes the bot exit a channel if it's alone.
@bot.event
async def on_voice_state_update(member, before, after):
    global channelstate
    global voice_channel
    global userchannel
    global queue
    global playing

    if member.bot:
        return
    if before.channel is None and after.channel is not None:
        return
    if before.channel is not None and after.channel is None:
        voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
        if voice_client is not None and len(before.channel.members) == 1:
            await voice_client.disconnect()
            channelstate = False
            voice_channel = ''
            playing = False
            userchannel = ()
            queue = []

    


# Copy your bot token in the parentesis
# Do no remove the ''
bot.run("TOKEN GOES HERE")
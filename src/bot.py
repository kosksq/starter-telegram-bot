import yt_dlp as youtube_dl
from multiprocessing.dummy import Pool
from multiprocessing import cpu_count
import subprocess
import threading
from telegram.ext.dispatcher import run_async
import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse
import telegram
import logging 
import asyncio
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os.path
from os import path
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
loop = asyncio.get_event_loop()
tasks = []
# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    msg = '\U0001F916 Welcome to MP3 Converter!\n'
    msg += 'You can check out the supported sites list:\n'
    msg += 'https://ytdl-org.github.io/youtube-dl/supportedsites.html\n'
    msg += 'If you found this bot helpful and want to support me to improve it. \nPlease buy me a coffee \uE045 https://www.buymeacoffee.com/mp3converter\n'
    msg += 'disclaimer: /about \n'
    msg += 'You can use @vid <song name> to search for youtube link of that song.\n'
    msg += 'Due to the limitation of file size you should not send video url that longer than 20 mins'
    update.message.reply_text(msg)


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('You should paste supported site url to download mp3')

def about(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Copyright Claims: We respect the intellectual property rights of others. You may not infringe the copyright, trademark or other proprietary informational rights of any party. We may in our sole discretion remove any Content we have reason to believe violates any of the intellectual property rights of others and may terminate your use of the bot if you submit any such Content.')
def echo(update, context):
    must_delete = update.message.reply_text('Processing...(Due to the Heroku terminate free product plans. This bot will no longer provide service after November 28, 2022)')
    youtubeurl = update.message.text
    playlist=[]
    try:
      query = parse_qs(urlparse(youtubeurl).query, keep_blank_values=True)
      playlist_id = query["list"][0]
      youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = "AIzaSyCSOgo99ea6KIlWtB2MZfC1LaA9i11gHCY")
      request = youtube.playlistItems().list(
          part = "snippet",
          playlistId = playlist_id,
          maxResults = 50
      )
      response = request.execute()

      playlist_items = []
      playlist=[]
      while request is not None:
          response = request.execute()
          playlist_items += response["items"]
          request = youtube.playlistItems().list_next(request, response)
      playlist=[ 
        f'https://www.youtube.com/watch?v={t["snippet"]["resourceId"]["videoId"]}'
        for t in playlist_items
    ]
    except:
      playlist.append(youtubeurl)
    # print(f"total: {len(playlist_items)}")
    # print([ 
    #     f'https://www.youtube.com/watch?v={t["snippet"]["resourceId"]["videoId"]}&list={playlist_id}&t=0s'
    #     for t in playlist_items
    # ])
    
    for url_list in playlist:
      url = get_youtubeurl(url_list)
      if url=="Error":
        update.message.reply_text("Error: Unavilible URL or too many request")
        #update.message.reply_text("This bot is affected by the bug that appears on the youtube-dl library. Therefore, the service will resume normal once the bug fixed.")
      else:
        print("The send action")
        print(url)
        context.bot.send_audio(chat_id=update.message.chat_id, audio=open('tmp/'+url+'.mp3', 'rb'))
        context.bot.deleteMessage (message_id = must_delete.message_id, chat_id = update.message.chat_id)
        # update.message.reply_text(str("Done"))
    # except:
    #   url = get_youtubeurl(youtubeurl)
    #   update.message.reply_text(str(url))
    # #down_url = get_youtubeurl(update.message.text)
    #   for a in url:
    #     for b in a:
    #       if b=="Error":
    #         update.message.reply_text("Error: Wrong URL or too many request")
    #       else:
    #         print("The send action")
    #         context.bot.send_audio(chat_id=update.message.chat_id, audio=open('tmp/'+b+'.mp3', 'rb'))
    #         update.message.reply_text(str("Done"))
    # context.bot.sendAudio(chat_id=update.message.chat_id, audio=down_url, title="song")
#  update.message.reply_audio(audio=down_url +'.mp3')
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def get_youtubeurl(url):
    ydl_opts = {
        #'writethumbnail': True,
        'outtmpl':'tmp' + '/%(title)s.%(ext)s',
        'format': 'bestaudio/best',
        'external_downloader':'aria2c',
        'writethumbnail': True,
        #'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'},
            {'key': 'EmbedThumbnail'},
            {'key': 'FFmpegMetadata'},
            
        ],}
    try:
      with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.cache.remove()
        info_dict = ydl.extract_info(url, download=False)
        video_title = info_dict.get('title', None).replace('||','').replace('/','_').replace('*','_').replace('?','').replace('|','_').replace(':',' -').replace('"',"'")
        print(video_title)
        duration = info_dict.get('duration', None)
        if path.exists("tmp/"+video_title+".mp3"):
          print("this is video_title")
          return(str(video_title))
        else:
          with youtube_dl.YoutubeDL(ydl_opts) as ydl:
              if duration < 1800:
                ydl.cache.remove()
                ydl.download([url])
                print("this is video_title")
                return(str(video_title))
              else:
                return("The mp3 longer than 30 mins")
    except:
#         print("ERROR")
        return('Error')
        # send_list.append(e)
    # return(send_list)
def main():
    PORT = int(os.environ.get('PORT', '8443'))
    TOKEN = "1629780235:AAEojaRp1ogzfznNXfJzaZc7hVmmWwkfCW8"
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN)
    bot = telegram.Bot(token=TOKEN)
    print(bot.getMe())
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start,run_async=True))
    dp.add_handler(CommandHandler("help", help,run_async=True))
    dp.add_handler(CommandHandler("about", about,run_async=True))
    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo,run_async=True))
    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
#     updater.start_polling()
    updater.start_webhook(listen="0.0.0.0",port=PORT,url_path=TOKEN,webhook_url="https://telebotdl.herokuapp.com/" + TOKEN)
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
# loop.run_until_complete(asyncio.wait(tasks))
# loop.close()

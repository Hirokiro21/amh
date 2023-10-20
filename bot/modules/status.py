#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex
from psutil import cpu_percent, virtual_memory, disk_usage
from time import time
from asyncio import sleep

from bot import bot_cache, status_reply_dict_lock, download_dict, download_dict_lock, botStartTime, DOWNLOAD_DIR, Interval, config_dict, bot
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import editMessage, sendMessage, deleteMessage, auto_delete_message, sendStatusMessage, update_all_messages, delete_all_messages
from bot.helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time, turn_page, setInterval, new_task
from bot.helper.ext_utils.atrocious_utils import user_info


@new_task
async def mirror_status(_, message):
    async with download_dict_lock:
        count = len(download_dict)
    if count == 0:
        currentTime = get_readable_time(time() - botStartTime)
        free = get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)
        msg = 'No Active Downloads !\n___________________________'
        msg += f"\n<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {free}" \
            f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {currentTime}"
        reply_message = await sendMessage(message, msg)
        await auto_delete_message(message, reply_message)
    else:
        await sendStatusMessage(message)
        await deleteMessage(message)
        async with status_reply_dict_lock:
            if Interval:
                Interval[0].cancel()
                Interval.clear()
                Interval.append(setInterval(
                    config_dict['STATUS_UPDATE_INTERVAL'], update_all_messages))


@new_task
async def status_pages(_, query):
    user_id = query.from_user.id
    data = query.data.split()
    if data[1] == 'ref':
        bot_cache.setdefault('status_refresh', {})
        if user_id in (refresh_status := bot_cache['status_refresh']) and (curr := (time() - refresh_status[user_id])) < 7:
            return await query.answer(f'Already Refreshed! Try after {get_readable_time(7 - curr)}', show_alert=True)
        else:
            refresh_status[user_id] = time()
        await editMessage(query.message, f"{(await user_info(user_id)).mention(style='html')}, Refreshing Status...")
        await sleep(2)
        await update_all_messages(True)
    elif data[1] in ['nex', 'pre']:
        await turn_page(data)
        await update_all_messages(True)
    elif data[1] == 'close':
        await delete_all_messages()
    await query.answer()


bot.add_handler(MessageHandler(mirror_status, filters=command(
    BotCommands.StatusCommand) & CustomFilters.authorized))
bot.add_handler(CallbackQueryHandler(status_pages, filters=regex("^status")))

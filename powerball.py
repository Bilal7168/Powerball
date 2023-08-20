import telebot
import random
import requests
import json
import time
import re
import os

import datetime

import telegram.helpers

from telegram.ext import CallbackQueryHandler, Updater


from telebot import types

from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
import base58
import requests
import hashlib

import threading

import urllib.parse

from eth_account import Account
import secrets
from web3 import Web3

from decimal import Decimal

import functools;

import sys

#bot_token = input("Please enter the bot token here: ")
bot = telebot.TeleBot('6689213581:AAEaaTi0vSxvSUAk6XbCITKoz8n2osav00c')

events = {}; #this dictionary shall also contain wallet addresses and keys -> {event id : [wallet address: '', private_key: '']}

events_to_remove = []

w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/b1f01e1fe09a4802bc64697fc67f8363')) #the ethereum node url to use here

w3_mainnet = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/b1f01e1fe09a4802bc64697fc67f8363'))


#user_id   and     
#callback_data=f"x_func|{event_details}|{event_name}|{event_time}|{user_id}|{duration_options[option]}") for option in duration_options]

data_socket = {}; #user_id: " ", data: {event_details: , event_name:, event_time:  }


import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()
logger.addHandler(logging.FileHandler('test.log', 'a'))

##############_______WALLET GENERATOR CODE AND FUNCTIONS_____________________########
def generate_wallet(event_id):
    print("Start")
    try:
        priv = secrets.token_hex(32)
        private_key = "0x" + priv
        acct = Account.from_key(private_key)
        events[event_id]['bitcoin_address'] = acct.address
        events[event_id]['win_dec'] = False
        events[event_id]['private_key'] = private_key
        events[event_id]['previous_balance'] = int(0); #to check if the previous balance is incraesed or not later on
        print("Wallet generated with address: ", acct.address)
    except Exception as e:
        print("line 54: ", e)

####################################################################################

#API KEY FOR BOT ADDED

# User registration and ticket sales
users = {} #already keeping track if the user has brought the ticket or not
ticket_price = 5300000000000000 # in ether (wei)

@bot.message_handler(commands=['join_me'])
def join_me(message):
    try:
        print("Join me was called by a user!")
        user_id = message.chat.id
        channel_id = 'TAGAIPowerballannouncement'
        community_id = 'tagai_techERC'
        message_text = f"Please join the channel 👉{channel_id} and the community 👉{community_id} before proceeding further🔥"
        message_markup = types.InlineKeyboardMarkup()
        message_markup.add(types.InlineKeyboardButton(text='👉 Join the Channel', url=f'https://t.me/{channel_id}'))
        message_markup.add(types.InlineKeyboardButton(text='👉 Join the Community', url=f'https://t.me/{community_id}'))
        bot.reply_to(message, message_text, reply_markup=message_markup)

    except Exception as e:
        print("line 77: ", e)

@bot.callback_query_handler(func=lambda call: call.data.startswith('/join_event'))
def join_event(callback_query):

    try:
        print("Event name queried")
        user_id = callback_query.message.chat.id
        bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)  #delete the top message
        markup = types.ForceReply(selective=False)
        popup_message = bot.send_message(callback_query.message.chat.id, "🔥Please enter the event id:", reply_markup=markup)
        bot.register_next_step_handler(popup_message, lambda message: process_event_id(message))

    except Exception as e:
        print("line 91: ",e)


@bot.callback_query_handler(func=lambda call: call.data.startswith('/join_event_buy_'))
def join_event_buy(message, event_id):
    try:
        print("Wallet address queried!")
        message = bot.reply_to(message, "Please enter a valid wallet address to pay to this event.")
        bot.register_next_step_handler(message, lambda message: process_wallet_address_join(message, event_id))

    except Exception as e:
        print("line 106: ", e)

def process_event_id(message):
    if message.text.strip() == '/start':
        send_welcome(message)
    else:
        event_id = int(message.text.strip())
        try:
            duration = events[event_id]["duration"]  # Format: d:m:h
            start_date = events[event_id]["start_date"]  # Assuming start_date is in datetime format

            # Split the duration into days, hours, and minutes
            days, hours, minutes = map(int, duration.split(':'))

            # Calculate the end date based on the start date and duration
            end_date = start_date + datetime.timedelta(days=days, hours=hours, minutes=minutes)

            # Get the current date and time
            current_date = datetime.datetime.now()

            # Check if the current date falls within the duration
            if current_date < end_date:
                if event_id not in events:
                    bot.send_message(message.chat.id, "❌ Invalid Event ID. Does not exist. Retry.")
                    return

                event_name = events[event_id]['name']
                duration = events[event_id]['duration']
                event_details = events[event_id]['details']

                bot.send_message(message.chat.id, f"The event name is: 🔥🔥{event_name}🔥🔥 and it's for \nduration: 🔥🔥{duration} days🔥🔥 where its \ndetails are: 🔥🔥{event_details}🔥🔥")
                message = bot.reply_to(message, "🔐 Please provide your wallet address for registration.")
                bot.register_next_step_handler(message, lambda message: process_wallet_address_join(message, event_id))
            else:
                bot.reply_to(
                    message,
                    text="⏰ We are sorry, but you can not buy this ticket anymore. The event is locked. Sales are now off."
                )
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Invalid Event ID. Does not exist. Retry.")
    print("Event details captued successfully. Now wallet address will be asked!")


def generate_temp_wallet_ticket():
    try:
        priv = secrets.token_hex(32)
        private_key = "0x" + priv
        acct = Account.from_key(private_key)
        return [acct.address, private_key] #[0,1]
    except Exception as e:
        print("line 155: ", e)
    print("Temp wallet generated successfuly!")


def has_tokens(user_id, wallet_address, event_id):
    try:
        print("Tokens are checked here")
        contract_addr = events[event_id]['contract_addr']
        contract_abi = events[event_id]['contract_abi']
        amount = events[event_id]['token_amount'] #already kept as integer

        tagi_token = w3_mainnet.eth.contract(address=contract_addr, abi=contract_abi)
        balance = tagi_token.functions.balanceOf(wallet_address).call() #gets the balance

        required_balance = 100 * 10**18
        if balance >= required_balance: #has the balance
            return True
        return False
    except Exception as e:
        bot.send_message(user_id, "There has been exception while processing your tokens. This can be caused by invalid contract addresses, invalid balances or an exception in the processing. Unfortunately, you cannot join this event. We apologize for the inconvenience.")
        print("Line 166: ", e);
        return False

def process_wallet_address_join(message, event_id):
    try:
        if message.text.strip() == '/start':
            send_welcome(message)
            print("Start called")
        else:
            user_id = message.chat.id
            wallet_address = message.text.strip()

            duration = events[event_id]["duration"]  # Format: d:m:h
            start_date = events[event_id]["start_date"]  # Assuming start_date is in datetime format

            # Split the duration into days, hours, and minutes
            days, hours, minutes = map(int, duration.split(':'))

            # Calculate the end date based on the start date and duration
            end_date = start_date + datetime.timedelta(days=days, hours=hours, minutes=minutes)

            # Get the current date and time
            current_date = datetime.datetime.now()

            print("Wallet address for join being processed!")

            # Check if the current date falls within the duration
            if current_date < end_date:
                if not is_valid_wallet_address(wallet_address):
                        message = bot.reply_to(message, "❌ Invalid wallet address. Please enter a valid wallet address🔥.")
                        # Ask for wallet address again
                        bot.register_next_step_handler(message, lambda msg: process_wallet_address_join(msg, event_id))
                        return

                if 'contract_addr' in events[event_id]: #means there is a smart contract already
                    if not has_tokens(user_id, wallet_address, event_id):
                        message = bot.reply_to(message, "❌You donot have enough tokens to buy the ticket to this event.")
                        # Ask for wallet address again
                        bot.register_next_step_handler(message, lambda msg: send_welcome(msg))
                        return

                ret_dat = generate_temp_wallet_ticket();
                eth_adrr = ret_dat[0]
                p_k = ret_dat[1]

                users[user_id] = {'wallet_address': wallet_address, 'b_a' : eth_adrr, 'b_p_k' : p_k, 'tickets': []}
                message_text = f"🎉 Welcome to TAG-AI Powerball Lottery! Your wallet has been registered🔥. To buy a ticket, please pay [0.01 eth] for the event to the address: \n\n {eth_adrr} \n\n to be approved. Click on the wallet address below and copy it for ease."
                logger.info("For creating an event, the payment was made to the address: %s with the private key: %s", eth_adrr, p_k)
                message_markup = types.InlineKeyboardMarkup()

                message_markup.add(types.InlineKeyboardButton(text='Verify Ticket', callback_data=f'/verify_event_{event_id}_j'))

                bot.reply_to(message, message_text, reply_markup=message_markup)

                address_message_text = f"{eth_adrr}"

                bot.send_message(user_id, address_message_text)
                

            else:
                bot.reply_to(
                    message,
                    text="⏰ We are sorry, but you can not buy this ticket anymore. The event is locked. Sales are now off."
                )
    except Exception as e:
        print("line 185", e)

@bot.callback_query_handler(func=lambda call: call.data.startswith('/create_event'))
def create_event(callback_query):
    try:
        user_id = callback_query.message.chat.id

        bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)  # Fixed this line

        markup = types.ForceReply(selective=False)
        if(len(events) < 20):
            print("Entering name of the event done!")
            popup_message = bot.send_message(user_id, "🔥🧠Please enter the name of the event🧠:", reply_markup=markup)
            bot.register_next_step_handler(popup_message, lambda message: process_event_name(message, user_id))

        else:
            print("20 events issue stuck!")
            bot.send_message(user_id, "20 events are already created. You cannot create more at this time.")
            bot.register_next_step_handler(popup_message, lambda message: send_welcome(message))

    except Exception as e:
        print("line 242 : ", e)


def process_event_name(message, user_id):
    try:
        event_name = message.text.strip()
        if(event_name == '/start'):
            send_welcome(message)
            print("Start called")
        else:
            print("Event name is processed. Now details were entered!")
            if not event_name:
                bot.reply_to(message, "📛Please specify the name of the event.")
                return

            # Request for event details using a popup
            markup = types.ForceReply(selective=False)
            popup_message = bot.send_message(user_id, "📇🔥Please enter some details about the event📇:", reply_markup=markup)
            bot.register_next_step_handler(popup_message, lambda message: process_event_details(message, user_id, event_name))

    except Exception as e:
        print("line 261 : ", e)

duration_options = { #d:h:m
    "1 Hour": "0:1:0",
    "2 Hours": "0:2:0",
    "3 Hours": "0:3:0",
    "6 Hours": "0:6:0",
    "1 Day": "1:0:0",
    "2 Days": "2:0:0",
    "3 Days": "3:0:0",
    "1 Week": "7:0:0",
    # Add more time options as needed...
}

def process_event_details(message, user_id, event_name):
    try:
        event_details = message.text.strip()

        if event_details == '/start':
            send_welcome(message)
            print("Start called")
        else:
            print("Event details were entered. Now to choose the event time duration.")
            if not event_details:
                bot.reply_to(message, "📇🔥Please provide some details about the event.")
                return

            new_data = {
                "user_id": user_id,
                "data": {
                    "event_details": event_details,
                    "event_name": event_name,
                    "event_time": "",
                    "duration": ""
                }
            }
            data_socket[new_data["user_id"]] = new_data["data"] #user_id : data
            # Create a list of InlineKeyboardButton objects for all duration options
            buttons = [types.InlineKeyboardButton(option, callback_data=f"x_func|{duration_options[option]}") for option in duration_options]

            # Send the inline keyboard with all duration options in one row
            keyboard = types.InlineKeyboardMarkup(row_width=3)  # row_width set to the number of duration options
            keyboard.add(*buttons)

            bot.send_message(user_id, "⏱️Please choose the event time duration:", reply_markup=keyboard)

    except Exception as e:
        print("line 290: ", e)


@bot.callback_query_handler(func=lambda call: call.data.startswith('x_func|'))
def handle_callback_query(call):
    try:
        print("Check now for either contract_req or process_event_time")
        user_id = call.from_user.id

        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)  # Fixed this line

        if "|" in call.data:
            # The user selected a time option
            event_data = call.data.split("|")  # Split the data using the separator "|"
            print(data_socket)
            event_details = data_socket[user_id]["event_details"]
            event_name = data_socket[user_id]["event_name"]
            event_time = event_data[1]

            if len(event_data) > 2:
                # The user selected a ticket sales duration option
                duration = event_data[2]
                check_contract_req(call.message, user_id, event_name, event_details, event_time, duration)
            else:
                # The user selected the initial event time duration
                process_event_time(call.message, user_id, event_name, event_details, event_time)
        else:
            # Handle other callback queries here if needed
            pass
    except Exception as e:
        print("Line 315: ", e)


def process_event_time(message, user_id, event_name, event_details, event_time):
    try:
        print("Event time processed")
        try:
            pass
        except ValueError:
            bot.reply_to(message, "❌Invalid event time. Please enter a valid number of days.")
            return

        ################
        print("The event time is: ", event_time)
        data_socket[user_id]["event_time"] = event_time #user_id : data
        print("The data socket event time is: ", data_socket[user_id]["event_time"])
        # Create a list of InlineKeyboardButton objects for all duration options
        buttons = [types.InlineKeyboardButton(option, callback_data=f"x_func|pass|{duration_options[option]}") for option in duration_options]

        # Send the inline keyboard with all duration options in one row
        keyboard = types.InlineKeyboardMarkup(row_width=3)  # row_width set to the number of duration options
        keyboard.add(*buttons)

        bot.send_message(user_id, "⏱️Please choose the ticket sales duration:", reply_markup=keyboard)

    except Exception as e:
        print("Line 344: ", e)



req_buts = {  # d:h:m
    "Yes": "yes",
    "No": "no",
}

def check_contract_req(message, user_id, event_name, event_details, event_time, duration):
    try:
        data_socket[user_id]["duration"] = duration
        buttons = [
            types.InlineKeyboardButton(option, callback_data=f"choice|{req_buts[option]}")
            for option in req_buts
        ]
        print("Checking contract requirements. Also, ask if players hold any smart tokens?")
        # Send the inline keyboard with all duration options in one row
        keyboard = types.InlineKeyboardMarkup(row_width=len(req_buts))  # row_width set to the number of duration options
        keyboard.add(*buttons)

        bot.send_message(user_id, "Do you want the players of this event to hold any smart contract tokens?", reply_markup=keyboard)

    except Exception as e:
        print("Line 372: ", e)


@bot.callback_query_handler(func=lambda call: call.data.startswith('choice|'))
def handle_callback_query(call):
    try:
        user_id = call.from_user.id
        dat = call.data.split("|")
        option = dat[1]
        print(data_socket, " and i am here again")
        event_name = data_socket[user_id]["event_name"]
        event_details = data_socket[user_id]["event_details"]
        event_time = data_socket[user_id]["event_time"]
        duration = data_socket[user_id]["duration"]
        print("Asking the user to enter the contract address of tokens! Came here after he/she said Yes or No to if they want smart tokens?")

        if option == 'yes':
            #ask for contract address
            markup = types.ForceReply(selective=False)
            popup_message = bot.send_message(user_id, "Please enter the contract address of the tokens you want your players to have", reply_markup=markup)
            bot.register_next_step_handler(popup_message, lambda message: process_contract_address(message, user_id, event_name, event_details, event_time, duration))
        else:
            process_event_duration(call.message, user_id, event_name, event_details, event_time, duration) #go for processing event duration

        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)  # Fixed this line
    except Exception as e:
        print("Line 388: ", e)


def process_contract_address(message, user_id, event_name, event_details, event_time, duration):
    try:
        if message.text.strip() == '/start':
            send_welcome(message)
            print("Start called")
        else:
            try:
                print("Contract address processed, asked to enter the contract ABI!")
                contract_addr = message.text.strip()
                if not contract_addr:
                    bot.reply_to(message, "📛Please specify the correct address.")
                    return

                markup = types.ForceReply(selective=False)
                popup_message = bot.send_message(user_id, "Please type in the shortened version of the smart contract ABI:", reply_markup=markup)
                bot.register_next_step_handler(popup_message, lambda message: process_contract_abi(message, user_id, event_name, event_details, event_time, duration, contract_addr))

            except Exception as e:
                print("Error occurred:", e)


    except Exception as e:
        print("Line 412: ", e)


def process_contract_abi(message, user_id, event_name, event_details, event_time, duration, contract_addr):
    try:
        if message.text.strip() == '/start':
            send_welcome(message)
            print("Start called")
        else:
            try:
                print("Get the contract ABI, now time to enter the amount of tokens players must contain?")
                contract_abi = message.text.strip() #get the shortened contract abi here
                if not contract_abi:
                    bot.reply_to(message, "📛Please specify the correct ABI (Application Binary Interface).")
                    return

                markup = types.ForceReply(selective=False)
                popup_message = bot.send_message(user_id, "Please enter the amount of tokens your event players must have:", reply_markup=markup)
                bot.register_next_step_handler(popup_message, lambda message: process_token_amount(message, user_id, event_name, event_details, event_time, duration, contract_addr, contract_abi))

            except Exception as e:
                print("Error occurred 436:", e)


    except Exception as e:
        print("Line 436: ", e)

def process_token_amount(message, user_id, event_name, event_details, event_time, duration, contract_addr, contract_abi):
    try:
        if message.text.strip() == '/start':
            send_welcome(message)
            print("Start called")
        else:
            print("Correct Token amounts selected")
            try:
                token_amount = message.text.strip()
                if not token_amount:
                    bot.reply_to(message, "📛Please enter the correct token amount.")
                    return

                markup = types.ForceReply(selective=False)
                popup_message = bot.send_message(user_id, "Type in Ok to go forward", reply_markup=markup)
                bot.register_next_step_handler(popup_message, lambda message: process_event_duration_contract(message, user_id, event_name, event_details, event_time, duration, contract_addr, contract_abi, token_amount))

            except Exception as e:
                print("Error occurred 459:", e)
    except Exception as e:
        print("Line 459: ", e)



def process_event_duration_contract(message, user_id, event_name, event_details, event_time, duration, contract_addr, contract_abi, token_amount):
    try:
        if message.text.strip() == '/start':
            send_welcome(message)
            print("Start called")
        else:
            try:
                pass
                #days, hours, minutes = duration.split(':') //split only when want to use
            except ValueError:
                bot.reply_to(message, "❌Invalid duration. Please enter a valid number of days.")
                return
            print("Event added but asking for wallet address")
            event_id = len(events) + 1
            #duration is ticket-sales-duration, 'time' is event-time
            events[event_id] = {"name": event_name, "duration" : duration, "details": event_details, "creator": user_id, "time": event_time, "start_date" : datetime.datetime.now(), "contract_addr" : contract_addr, "contract_abi" : contract_abi, "token_amount" : int(token_amount), "paid" : False}

            # we will generate a temporary wallet for each customer and check its balance to see if it has been paid or not
            generate_wallet(event_id)

            time_text = {"0:1:0": "1 Hour",
    "0:2:0": "2 Hours",
    "0:3:0": "3 Hours",
    "0:6:0": "6 Hours",
    "1:0:0": "1 Day",
    "2:0:0": "2 Days",
    "3:0:0": "3 Days",
    "7:0:0": "1 Week"}

            event_message = f"Event '{event_name}' created by \nUser @ {user_id} \n at {event_time} for Duration : {duration} \nDetails : {event_details} \n This event requires {token_amount} tokens from its players."
            bot.reply_to(message, event_message)

            ######################################---################################

            # Request for wallet address using a popup
            markup = types.ForceReply(selective=False)
            popup_message = bot.send_message(user_id, "👛🔥Please enter your wallet address:", reply_markup=markup)
            bot.register_next_step_handler(popup_message, lambda message: process_wallet_address(message, event_id))

    except Exception as e:
        print("Line 482: ", e)

def process_event_duration(message, user_id, event_name, event_details, event_time, duration):
    try:
        print("Entering wallet address after processing event duration")
        try:
            pass
        except ValueError:
            bot.reply_to(message, "❌Invalid duration. Please enter a valid number of days.")
            return

        event_id = len(events) + 1
        #duration is ticket-sales-duration, 'time' is event-time
        events[event_id] = {"name": event_name, "duration" : duration, "details": event_details, "creator": user_id, "time": event_time, "start_date" : datetime.datetime.now()}

        # we will generate a temporary wallet for each customer and check its balance to see if it has been paid or not
        generate_wallet(event_id)

        time_text = {"0:1:0": "1 Hour",
                        "0:2:0": "2 Hours",
                        "0:3:0": "3 Hours",
                        "0:6:0": "6 Hours",
                        "1:0:0": "1 Day",
                        "2:0:0": "2 Days",
                        "3:0:0": "3 Days",
                        "7:0:0": "1 Week"}

        event_message = f"Event '{event_name}' created by \nUser ➡️ {user_id} \nAt ➡️ {time_text[event_time]} for \nDuration ➡️ {time_text[duration]} \nDetails ➡️ {event_details}"
        bot.reply_to(message, event_message)


        # Request for wallet address using a popup
        markup = types.ForceReply(selective=False)
        popup_message = bot.send_message(user_id, "👛🔥Please enter your wallet address:", reply_markup=markup)
        bot.register_next_step_handler(popup_message, lambda message: process_wallet_address(message, event_id))

    except Exception as e:
        print("Line 525: ", e)




@bot.message_handler(commands=['start']) #CURRENTLY WORKING ON THESE #add the method for showing the number of days, h and mins left
def send_welcome(message):
    # Register the user for the game
    # Send the image from your desktop

    try:
        user_id = message.chat.id
        payload_pattern = r"/start event_join_(\d+)"
        match = re.match(payload_pattern, message.text)
        if re.match(payload_pattern, message.text):
            # The message text matches the expect
            bot.delete_message(chat_id=user_id, message_id=message.message_id)  # Fixed this line
            bot.send_message(message.chat.id, "🔥To buy a ticket, please type 'Ok' in response:")
            event_id = match.group(1)
            query = "event_join_" + str(event_id)
            print("Starting an event join to an event id")
            bot.register_next_step_handler(message, lambda message: event_join_buy_ver(query, message))
        else:
            mem = 1
            mem_t = 1
            try:
                channel_member = bot.get_chat_member('@TAGAIPowerballannouncement', user_id)
                group_member = bot.get_chat_member('@tagai_techERC', user_id)

                if channel_member.status == 'member' or channel_member.status == 'creator' and group_member.status == 'member' or group_member.status == 'creator':
                    # User is a member of both the channel and the group
                    image_path = './Powerball Logo2.png' # Replace this with the actual path of your image
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as photo:
                            bot.send_photo(message.chat.id, photo, caption="⭐Welcome to TAG AI Powerball, champ! Follow the instructions and win prizes!✨")
                    else:
                        bot.send_message(message.chat.id, "Image not found!")
                    message_markup = types.InlineKeyboardMarkup()
                    message_markup.add(types.InlineKeyboardButton(text='Create Event', callback_data='/create_event'))
                    message_markup.add(types.InlineKeyboardButton(text='Join Event', callback_data='/join_event'))
                    bot.reply_to(message, "Select any of the following options", reply_markup=message_markup)
                else:
                    # User is not a member of both the channel and the group
                    message_text = f"🔥🔥Welcome to TAG-AI Powerball Lottery! Please join the channel 'TagAI_Powerball_Channel' and the group 'TagAI Powerball Community Group' before registration by typing /join_me"
                    message_markup = types.InlineKeyboardMarkup()
                    message_markup.add(types.InlineKeyboardButton(text='Join Me', callback_data='/join_me'))
                    bot.reply_to(message, message_text, reply_markup=message_markup)
            except Exception as e:
                print("Line 557:", e)
                # An error occurred - handle it appropriately
                bot.send_message(user_id, "🔥🔥Welcome to TAG-AI Powerball Lottery! Please join the channel 'TagAI_Powerball_Channel' and the group 'TagAI Powerball Community Group' before registration by typing /join_me")
                pass

        global events_to_remove

        lor = []

        for event_id in events: #for event ids in events given
            if events[event_id]['win_dec'] == False:
                print("If events have no declared winner and they are inside the events.")
                #duration is ticket-sales-duration, 'time' is event-time
                event_duration = events[event_id]['time']  # in format: d:h:m
                ticket_sales_dur = events[event_id]['duration'] # in format: d:h:m

                start_date = events[event_id]['start_date']  # in datetime format

                current_date = datetime.datetime.now()  # current datetime

                # Convert event_duration to timedelta format
                duration_parts = event_duration.split(':')
                days = int(duration_parts[0])
                hours = int(duration_parts[1])
                minutes = int(duration_parts[2])
                duration_timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes)

                #convert ticket sales duration to timedelta format
                ticket_sales_dur_parts = ticket_sales_dur.split(':')
                days_t = int(ticket_sales_dur_parts[0])
                hours_t = int(ticket_sales_dur_parts[1])
                minutes_t = int(ticket_sales_dur_parts[2])
                duration_timedelta_t = datetime.timedelta(days=days_t, hours=hours_t, minutes=minutes_t)

                end_date = start_date + duration_timedelta  # Calculate the end date of the event
                end_date_t = start_date + duration_timedelta_t #Calculate the end date of the ticket sales duration

                time_difference = end_date - current_date  # timedelta object representing the time difference
                time_difference_t = end_date_t - current_date #timedelta object representing the ticket sales duration difference

                # Calculate the remaining days, hours, and minutes
                days = time_difference.days
                hours = time_difference.seconds // 3600
                minutes = (time_difference.seconds % 3600) // 60

                # Calculate the remaining time difference t
                days_t = time_difference_t.days
                hours_t = time_difference_t.seconds // 3600
                minutes_t = (time_difference_t.seconds % 3600) // 60

                if(days_t * -1 != 1): #if days are -1, then multiplying -1  with it will give 1
                    if('contract_addr' in events[event_id]):
                        msg = f"🔥➡️The time left for event {event_id} is: {days} days, {hours} hours, {minutes} minutes.⬅️ and duration for ticket sale is : {days_t} days, {hours_t} hours, {minutes_t} minutes. This event requires players to hold {events[event_id]['token_amount']} tokens of the contract: {events[event_id]['contract_addr']}."
                    else:
                        msg = f"🔥➡️The time left for event {event_id} is: {days} days, {hours} hours, {minutes} minutes.⬅️ and duration for ticket sale is : {days_t} days, {hours_t} hours, {minutes_t} minutes"
                else:
                    if('contract_addr' in events[event_id]):
                        msg = f"🔥➡️The time left for event {event_id} is: {days} days, {hours} hours, {minutes} minutes.⬅️ and ticket sales are over. This event requires players to hold {events[event_id]['token_amount']} tokens of the contract: {events[event_id]['contract_addr']}."
                    else:
                        msg = f"🔥➡️The time left for event {event_id} is: {days} days, {hours} hours, {minutes} minutes.⬅️ and ticket sales are over."

                if(events[event_id]['paid'] is True):
                    if(minutes >= 1):
                        bot.send_message(message.chat.id, msg)
                    else: #if less than 1 minute, the event will enter the annoucement phase and winner will be declared
                        bot.send_message(message.chat.id, f"Event {event_id} has entered the announcement phase. Winners will be declared soon! Good luck!")
            else:
                lor.append(event_id)

        for id in lor:
            events.pop(id);

    except Exception as e:
        print("line 57: ", e)




def send_prize(from_addr, from_pk, to_addr, balance_wei):
    print("Money: ", balance_wei, ' being sent from: ', from_addr, " with priv. key -> ", from_pk, " to address: ", to_addr)
    # Convert the amount to Wei (1 Ether = 1e18 Wei)
    amount_wei = int(balance_wei)
    
    # Get the estimated gas cost for the transaction
    estimated_gas = w3.eth.estimate_gas({
        'from': from_addr,
        'to': to_addr,
        'value': amount_wei,
    })

    print("The estimated gas is: ", estimated_gas)
    
    # Calculate the maximum acceptable gas price based on the remaining balance
    max_gas_price_wei = (amount_wei - estimated_gas) // 21000  # Assuming a gas limit of 21000

    print("The max gas price in wei: ", max_gas_price_wei)
    
    # Get the current gas price
    current_gas_price = w3.eth.gas_price
    
    # Ensure that the gas price does not exceed the maximum acceptable gas price
    gas_price_wei = min(current_gas_price, max_gas_price_wei)

    print("The gas price in wei a min: ", gas_price_wei)
    
    if gas_price_wei <= 0:
        print("Insufficient balance to cover gas cost.")
        return None
    
    # Calculate the remaining balance after deducting gas cost
    remaining_balance_wei = amount_wei - (estimated_gas * (w3.to_wei(40, 'gwei')))
    remaining_balance_str = str(remaining_balance_wei).replace(".", "")  # Convert to string and remove decimal point if present

    nonce = w3.eth.get_transaction_count(from_addr)

    print(gas_price_wei)

    # for winner
    transaction = {
        'from': from_addr,
        'to': to_addr,
        'value': remaining_balance_wei-50000,
        'gas': 21000,
        'gasPrice': w3.to_wei(40, 'gwei'),
        'nonce': nonce,
    }

    try:
        signed_transaction = w3.eth.account.sign_transaction(transaction, from_pk)
    except Exception as e:
        print(str(e))
        return None

    # Send the transaction
    try:
        tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    except Exception as e:
        print(str(e))
        return None

    # Wait for the transaction to be mined
    try:
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    except Exception as e:
        print(str(e))
        return None

    print("Prize sent to winner with receipt: ", tx_receipt)
    return tx_receipt


##########REGISTRATION WALLET ADDRESS NEEDED

@bot.callback_query_handler(func=lambda query: query.data.startswith('/event_join_'))
def event_join(query):
    try:
        event_id = int(query.data.split('_')[2])
        event_details = events[event_id]['details']

        duration = events[event_id]["duration"]  # Format: d:m:h
        start_date = events[event_id]["start_date"]  # Assuming start_date is in datetime format

        # Split the duration into days, hours, and minutes
        days, hours, minutes = map(int, duration.split(':'))

        # Calculate the end date based on the start date and duration
        end_date = start_date + datetime.timedelta(days=days, hours=hours, minutes=minutes)

        # Get the current date and time
        current_date = datetime.datetime.now()
        print("Event joining!")

        # Check if the current date falls within the duration
        if current_date < end_date:
            bot.reply_to(

                query.message,
                text=f'🔥You have clicked on the link for event\n ➡️ {event_id}. The details for the event are: \n ➡️{event_details}\n. 🔥Lets get you a ticket. Please type in Ok to proceed.'
            )
            bot.register_next_step_handler(query.message, lambda message: join_event_buy(message, event_id)) # Now we want to get the wallet address
        else:
            bot.reply_to(
                query.message,
                text="⏰ We are sorry, but you can not buy this ticket anymore. The event is locked. Sales are now off."
            )

        bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)  # Fixed this line

    except Exception as e:
        print("Line 670: ", e)

def event_join_buy_ver(query, message):
    try:
        event_id = int(query.split('_')[2])
        event_details = events[event_id]['details']

        duration = events[event_id]["duration"]  # Format: d:m:h
        start_date = events[event_id]["start_date"]  # Assuming start_date is in datetime format

        # Split the duration into days, hours, and minutes
        days, hours, minutes = map(int, duration.split(':'))

        # Calculate the end date based on the start date and duration
        end_date = start_date + datetime.timedelta(days=days, hours=hours, minutes=minutes)

        # Get the current date and time
        current_date = datetime.datetime.now()
        print("Joining event with the id!, clicked a link or so : Line 707")
        # Prompt the user to buy a ticket for the event
        if current_date < end_date:
            bot.reply_to(
                message,
                text=f'🔥You have clicked on the link for event\n ➡️ {event_id}. The details for the event are: \n ➡️{event_details}\n. 🔥Lets get you a ticket. Please type in Ok to proceed.'

            )
            bot.register_next_step_handler(message, lambda message: join_event_buy(message, event_id))#now we want to get the wallet address
        else:
            bot.reply_to(
                message,
                text="⏰ We are sorry, but you can not buy a ticket to this event anymore. The event is locked. Sales are now off."
            )
        #expect a buy ticket response here

    except Exception as e:
        print("Line 707: ", e)


@bot.callback_query_handler(func=lambda call: call.data.startswith('/verify_event_'))
def verify_event(call):
    try:
        event_id = int(call.data.split('_')[2])
        # Register the user for the game
        user_id = call.message.chat.id
        #GET PREVIOUS BALANCE
        prev_balance = events[event_id]['previous_balance']

        #GET CURRENT BALANCE
        b_addres = '0x97BC47f8169c3a49B46CB4EBe634AbEdB291E047'
        curr_balance = w3.eth.get_balance(b_addres)

        if curr_balance - prev_balance >= 0 : #means paid 0.1 eth #100000000000000000
            deep_link_url = telegram.helpers.create_deep_linked_url(
            bot_username=str('TagAI_Powerball_1_Bot'),
            payload=f'event_join_{event_id}'
            )
            message_markup = types.InlineKeyboardMarkup()
            message_markup.add(types.InlineKeyboardButton(text='Join Event', callback_data=f'/event_join_{event_id}'))
            if(len(call.data.split('_')) == 3):
                payload = f'event_join_{event_id}'
                deep_link_url = f'https://t.me/TagAI_Powerball_1_Bot?start={payload}'
                bot.reply_to(call.message, f"➡️➡️Your payment is accepted. Thank you. Your event is created and the link is: {deep_link_url}", reply_markup=message_markup)
                
                announcement_channel = "@TAGAIPowerballannouncement"  # Replace this with your announcement channel name
                message = f"🎉Event {events[event_id]['name']} created by user: {user_id} for duration : {events[event_id]['duration']}. Click on the following link: {deep_link_url}"

                events[event_id]['paid'] = True #make paid True

                # Send the message to the announcement channel
                bot_token = "6689213581:AAEaaTi0vSxvSUAk6XbCITKoz8n2osav00c"
                base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                data = {"chat_id": announcement_channel, "text": message}

                response = requests.post(base_url, data=data)
            else:
                eth_adrr = users[user_id]['b_a']
                p_k = users[user_id]['b_p_k']
                check_bal = w3.eth.get_balance(eth_adrr)
                if(check_bal >= 0): #0.01 eth = 10000000000000000
                    bot.reply_to(call.message, f"➡️➡️Your payment is accepted. Thank you. You have joined the event, your ticket number will be sent soon. Please type in OK to go forward.")
                    bot.register_next_step_handler(call.message, lambda message: buy_ticket(message, eth_adrr, p_k, event_id)) #now we want to get the wallet address

                    return True
                else:
                    bot.reply_to(call.message, "❌❌Your payment hasnt been approved. Please pay the full amount and verify again.")
                    return False
            return True
        bot.reply_to(call.message, "❌❌Your payment hasnt been approved. Please pay the full amount and verify again.")
        return False
    except Exception as e:
        print("Line 743: ", e)

def process_wallet_address(message, event_id): #for CREATE EVENT
    try:
        if message.text.strip() == '/start':
            send_welcome(message)
            print("Start called")
        else:
            print("Wallet address processed for create_event")
            user_id = message.chat.id
            wallet_address = message.text.strip()

            if not is_valid_wallet_address(wallet_address):
                message = bot.reply_to(message, "❌ Invalid wallet address. Please enter a valid wallet address🔥.")
                    # Ask for wallet address again
                bot.register_next_step_handler(message, lambda msg: process_wallet_address(msg, event_id))
                return


            users[user_id] = {'wallet_address': wallet_address, 'tickets': []}
            message_text = f"➡️Welcome to TAG-AI Powerball Lottery! Your event has been created. Please pay [0.1 Eth] for the event to the address: \n\n 0x97BC47f8169c3a49B46CB4EBe634AbEdB291E047 \n\n to be approved. If paid, click on /verify_event to proceed."
            #update the previous balance of this wallet
            events[event_id]['previous_balance'] = w3.eth.get_balance('0x97BC47f8169c3a49B46CB4EBe634AbEdB291E047')

            message_markup = types.InlineKeyboardMarkup()
            message_markup.add(types.InlineKeyboardButton(text='Verify Event', callback_data=f'/verify_event_{event_id}'))

            #message_markup.add(types.InlineKeyboardButton(text='/check_tickets', callback_data='/check_tickets'))
            x = bot.reply_to(message, message_text, reply_markup=message_markup)

            bot.send_message(user_id, "0x97BC47f8169c3a49B46CB4EBe634AbEdB291E047")


    except Exception as e:
        print("line 797: ", e)

def is_valid_wallet_address(wallet_address):
    try:
        print("This is a valid wallet address")
        if re.match("^0x[0-9a-fA-F]{40}$", wallet_address):
            return True
        else:
            return False
    except Exception as e:
        print('line 850: ', e)
###########################33

# Jackpot prize and charity donations
jackpot_amount = 0.0 #have to add this from the ticket prices recieved from the user

#no charity,
event_creator = 0.15 #15% to event creator
bot_owner = 0.10 #10% to bot owners #bot maintenance wallet

def send_money_wallets(from_addr, from_pk, event_id, balance_wei):
    to_addr = events[event_id]['bitcoin_address']

    print("Money: ", balance_wei, ' being sent from: ', from_addr, " with priv. key -> ", from_pk, " to address: ", to_addr)
    

    amount_wei = int(balance_wei)
    print("The money sent from buying the ticket to the wallet is: ", amount_wei)
    
    # Get the estimated gas cost for the transaction
    estimated_gas = w3.eth.estimate_gas({
        'from': from_addr,
        'to': to_addr,
        'value': amount_wei,
    })

    print("The estimated gas is: ", estimated_gas)
    
    # Calculate the maximum acceptable gas price based on the remaining balance
    max_gas_price_wei = (amount_wei - estimated_gas) // 21000  # Assuming a gas limit of 21000

    print("The max gas price in wei: ", max_gas_price_wei)
    
    # Get the current gas price
    current_gas_price = w3.eth.gas_price
    
    # Ensure that the gas price does not exceed the maximum acceptable gas price
    gas_price_wei = min(current_gas_price, max_gas_price_wei)

    print("The gas price in wei a min: ", gas_price_wei)
    
    if gas_price_wei <= 0:
        print("Insufficient balance to cover gas cost.")
        return None
    
    # Calculate the remaining balance after deducting gas cost
    remaining_balance_wei = amount_wei - (estimated_gas * (w3.to_wei(40, 'gwei')))
    remaining_balance_str = str(remaining_balance_wei).replace(".", "")  # Convert to string and remove decimal point if present


    nonce = w3.eth.get_transaction_count(from_addr)

    print(gas_price_wei)

    # for winner
    transaction = {
        'from': from_addr,
        'to': to_addr,
        'value': remaining_balance_wei-50000, #50000 is extra transaction fees
        'gas': 21000,
        'gasPrice': w3.to_wei(40, 'gwei'),
        'nonce': nonce,
    }

    try:
        signed_transaction = w3.eth.account.sign_transaction(transaction, from_pk)
    except Exception as e:
        print(str(e))
        return None

    # Send the transaction
    try:
        tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    except Exception as e:
        print(str(e))
        return None

    # Wait for the transaction to be mined
    try:
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info("Money was wired to central bitcoin address: %s with the private key: %s", to_addr, events[event_id]['private_key'])
    except Exception as e:
        print(str(e))
        return None

    print("Prize sent to Bitcoin Owner: ", tx_receipt)
    logger.info("Money was wired to central bitcoin address [more verification]: %s with the private key: %s", to_addr, events[event_id]['private_key'])
    return tx_receipt


@bot.message_handler(commands=['buy_ticket']) #CURRENTLY WORKING ON THESE
def buy_ticket(message, eth_addr, p_k, event_id):
    try:
        print("Ticket in the buying process!")
        # Allow the user to buy a ticket with cryptocurrency payment
        user_id = message.chat.id
        ticket_number = random.randint(1000000, 9999999)
        while ticket_number in [t['number'] for t in users[user_id]['tickets']]:
            ticket_number = random.randint(1000000, 9999999)

        users[user_id]['tickets'].append({'event_id' : event_id, 'number': ticket_number, 'eth_addr' : eth_addr, 'priv_key' : p_k, 'paid': True})

        bot.send_message(user_id, f"You will have to wait for the transaction to be processed! This can take upto a minute...")
        #SEND MONEY FROM eth_addr and priv_key to events[event_id]['bitcoin_address']
        curr_balance = w3.eth.get_balance(eth_addr) #money taken from the wallet through which we have to send
        send_money_wallets(eth_addr, p_k, event_id, curr_balance)

        bot.reply_to(message, f"🔥🔥Your ticket number is {ticket_number}.")

        #now what we want to do here is to add a transparency, as to the total amount of jackpot and how much is available as prize

        #the amount is the one we get from the event wallet
        jackpot_amount_show = w3.eth.get_balance(events[event_id]['bitcoin_address']) #get the total money recieved in wei

        event_creator_money = jackpot_amount_show * event_creator
        bot_owner_money = jackpot_amount_show * bot_owner

        jackpot_amount_show -= + event_creator_money + bot_owner_money

        bot.reply_to(message, f"🙌🏻Currently, the jackpot prize stands at a total of: {round(Decimal(jackpot_amount_show/1000000000000000000), 8)} Ether.")
        #calculate the time between the dates
    except Exception as e:
        print("Line 913: ", e)


####CHECK_TRANSACTION_STATUS HANDLER
def check_transaction_status(tran_hash, ticket_price):
    #Write the logic and check if its paid (on the person having the bot)
    return True

@bot.message_handler(commands=['check_tickets'])
def check_tickets(message):
    try:
        # Allow the user to check their own tickets
        user_id = message.chat.id
        if user_id not in users:
            message_text = "❌❌You are not registered for the game. Type /start to register."
            message_markup = types.InlineKeyboardMarkup()
            message_markup.add(types.InlineKeyboardButton(text='/start', callback_data='/start'))
            bot.reply_to(message, message_text, reply_markup=message_markup)
        else:
            if len(users[user_id]['tickets']) == 0:
                bot.reply_to(message, "❌❌You have not purchased any tickets yet.")
            else:
                ticket_numbers = [t['number'] for t in users[user_id]['tickets']]
                bot.reply_to(message, f"✔️✔️Your tickets are available after your purchase was verified. Your ticket numbers are {ticket_numbers}.")
    except Exception as e:
        print(e)



def update_jackpot(event_id):
    try:
        global jackpot_amount
        global ticket_price

        print("L")
        total_tickets = sum(len(user['tickets']) for user in users.values() if any(ticket['event_id'] == event_id for ticket in user['tickets']))
        print("The total tickets are: ", total_tickets)
        print("L2")
        jackpot_amount = w3.eth.get_balance(events[event_id]['bitcoin_address'])   #get the amount in wei

        event_creator_money = jackpot_amount * event_creator
        bot_owner_money = jackpot_amount * bot_owner

        jackpot_amount -= event_creator_money + bot_owner_money
        print("the jackpot amount is: ", jackpot_amount)
    except Exception as e:
        print(e)



# Drawing of the winning numbers
winning_number = 0; #just one ticket
total_tickets_list = []

def draw_numbers(event_id):
    try:
        global total_tickets_list
        global winning_number

        for user_id in users:
            for ticket in users[user_id]['tickets']: #for each ticker one user has #store the ticket number
                if (ticket['event_id'] == event_id):
                    total_tickets_list.append(ticket['number']);

        # Pick one random ticket number from total_tickets_list

        if(len(total_tickets_list) > 0):
            #winning_number = random.choice(total_tickets_list);
            winning_number = total_tickets_list[-1] #always get the last number
            print("The winning number was: ", winning_number);
    except Exception as e:
        print(e)






#event_creator = 0.15 #15% to event creator
#bot_owner = 0.10 #10% to bot owners #bot maintenance wallet
# Distribution of prizes
def calculate_prizes(event_id):
    try:
        global jackpot_amount
        global winning_number
        global ticket_price
        winners = [] #list as in {winner : user_id, ticket# : ticket number , wallet_address = users[user_id][wallet_Address]}
        prize = 0

        winning_user_id = 0

        if events[event_id]['paid'] is True:
            for user_id in users: #for all user_ids
                for ticket in users[user_id]['tickets']: #for all user_id tickets
                    if ticket['event_id'] == event_id and events[event_id]['win_dec'] == False: #if this ticket is for the event requested
                        print("The ticket num is: ", int(ticket['number']), " and the winning_num is : ", int(winning_number) )
                        if int(ticket['number']) == int(winning_number): #if this ticket is the winning number
                            winning_user_id = user_id
                            prize = 0.74 * jackpot_amount #74% of jackpot amount
                            bot.send_message(user_id, f"Congratulations! Your ticket number {ticket['number']} matched all balls and is the winner. You have won the entire jackpot of {round(Decimal(prize/1000000000000000000), 15)} ether!")
                            send_prize(events[event_id]['bitcoin_address'], events[event_id]['private_key'], users[user_id]['wallet_address'], prize) #prize is in wei
                            winners.append({'user_id' : user_id, 'ticket_num' : ticket['number'], 'wallet_address' : users[user_id]['wallet_address']})
                        else: #else this ticket is not the winning number
                            bot.send_message(user_id, f"Your ticket number {ticket['number']} lost in the event {event_id}. Thank you! Please try again. 😊. \n GLOBAL STATISTICS🌐------------------------------\n Total number of players: {sum(len(user['tickets']) for user in users.values() if any(ticket['event_id'] == event_id for ticket in user['tickets']))} 🏈 \n 🏆 \n Total Jackpot: {round(Decimal(jackpot_amount/1000000000000000000),5)} Eth 💰  ")

            try:
                # Send to bot owner
                send_prize(events[event_id]['bitcoin_address'], events[event_id]['private_key'], '0x97BC47f8169c3a49B46CB4EBe634AbEdB291E047', 0.10 * jackpot_amount)
                print("try")
                # Send to event creator
                creator_id = int(events[event_id]['creator'])
                send_prize(events[event_id]['bitcoin_address'], events[event_id]['private_key'],  users[creator_id]['wallet_address'], 0.15 * jackpot_amount)
                
                # disburse the last remaining amount back to the winner
                send_prize(events[event_id]['bitcoin_address'], events[event_id]['private_key'], users[winning_user_id]['wallet_address'], w3.eth.get_balance(events[event_id]['bitcoin_address'])) #prize is in wei

            except Exception as e:
                print("Error coming at sending prizes" , e)


            try:
                announcement_channel = "@TAGAIPowerballannouncement"  # Replace this with your announcement channel name
                for winner in winners:
                    user_id = winner['user_id']
                    ticket_num = winner['ticket_num']
                    wallet_address = winner['wallet_address']
                    message = f"🏆 Winner Announcement 🏆\n\nCongratulations! 🎉 to user @{user_id}\nTicket Number: {ticket_num}\nWinner's Wallet Address: {wallet_address}\n\n🎁 You have won a prize in the TAG-AI Powerball Lottery! 🎉🎊. If, you are unable to recieve the message of losing, it may be due to internet lags in your area."

                    # Send the message to the announcement channel
                    bot_token = "6689213581:AAEaaTi0vSxvSUAk6XbCITKoz8n2osav00c"
                    base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    data = {"chat_id": announcement_channel, "text": message}

                    response = requests.post(base_url, data=data)
            except Exception as e:
                print("Error coming at making the announcement: ", e)

    except Exception as e:
        print("Error in the caclulate_prizes function: ", e)




def check_event_time():
    try:
        global events_to_remove
        current_date = datetime.datetime.now()
        for event_id in events:
            start_date = events[event_id]['start_date']
            duration = events[event_id]['time']  # in format: d:h:m

            # Convert duration to timedelta format
            duration_parts = duration.split(':')
            days = int(duration_parts[0])
            hours = int(duration_parts[1])
            minutes = int(duration_parts[2])
            duration_timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes)

            end_date = start_date + duration_timedelta

            time_difference = end_date - current_date


            # Check if the total seconds is less than or equal to the threshold
            if time_difference.total_seconds() <= 60:  # 80 seconds = 1 minute
                print("Event time is complete. Now declaring winners and announcing prizes.")
                if events[event_id]['win_dec'] == False: #only work if the winners arent declared
                    update_jackpot(event_id) #need to send the event_id to see what event is performed
                    draw_numbers(event_id)
                    calculate_prizes(event_id)
                    events[event_id]['win_dec'] = True
    except Exception as e:
        print(e)


def bot_polling():
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print("The bot polling had an error as : ", e)

#for the separate bot thread in which we see that the event_time() runs separately
def event_time_check_thread():
    try:
        while True:
            check_event_time()
            time.sleep(60)  # Adjust the sleep duration to check every 1 minute
    except Exception as e:
        print("Event time check thread is : ", e)


if __name__ == '__main__':
    while True:  # Loop to retry the try block upon exception
        try:
            print("Bot working")
            bot.delete_webhook()  # Clearing the cache for updation

            channel_info = bot.get_chat('@chan_j_bizman')
            channel_id = channel_info.id

            #-1001964189606
            print(bot.get_chat_members_count(channel_id))

            # Start the bot polling in a separate thread, so that the check_event_time() function is called after every 60 seconds or so and doesnt interrupt
            polling_thread = threading.Thread(target=bot_polling)
            polling_thread.start()

            #start the event check time in another thread
            event_time_thread = threading.Thread(target=event_time_check_thread)
            event_time_thread.start()

            # Wait for both threads to finish (this will never happen as they run infinitely)
            polling_thread.join()
            event_time_thread.join()

        except Exception as e:
            print(e)
            time.sleep(15)  # Add a delay before retrying the try block
            continue  # Jump back to the beginning of the loop to retry the try block









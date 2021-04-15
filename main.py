import json
import requests
import re
from bs4 import BeautifulSoup
from random import randint
import pandas as pd
import yake
from wordfreq import zipf_frequency as zipf
import telebot
from telebot import types
import config
import db
import nltk
import os
import time
from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.support.ui import Select

server = Flask(__name__)
bot = telebot.TeleBot(config.token)
cmd = ['/info','look_up','/reset','/start','/commands', '/video']

chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")


# mark-up for sending buttons
def mark_up(buttons):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True,resize_keyboard=True,row_width=1)
    for text in buttons:
        button = types.KeyboardButton(text)
        markup.add(button)
    return markup


@bot.message_handler(commands=["start"])
def cmd_start(message):
    db.set_id(str(message.chat.id))
    db.del_state(str(message.chat.id), config.DB_cols.LOOKUP.value)
    db.del_state(str(message.chat.id), config.DB_cols.STATE.value)
    bot.send_message(message.chat.id, "Hi, I'm Linguini and I can help you learn new vocabulary.\n"
                                      "I can send videos, exercises and dictionary definitions.\n"
                                      "Let's have some fun watching TEDTalks videos and doing vocabulary exercises!\n"
                                      "Send /video to get a video.\n"
                                      "Type /look_up to look up a word in the dictionary.\n"
                                      "Send /info to know me better.\n"
                                      "Send /commands to list the available commands.\n")
    bot.send_photo(message.chat.id, config.pasta_img[randint(0,4)])
    db.set_property(str(message.chat.id), config.DB_cols.STATE.value, config.States.START.value)
    db.set_property(str(message.chat.id), config.DB_cols.LOOKUP.value, config.LookUp.START.value)


@bot.message_handler(commands=["reset"])
def cmd_reset(message):
    db.del_state(str(message.chat.id), config.DB_cols.LOOKUP.value)
    db.del_state(str(message.chat.id), config.DB_cols.STATE.value)
    bot.send_message(message.chat.id, "Let's start anew.\n"
                                      "Type /video to watch a video and learn some new vocabulary.\n"
                                      "Type /look_up to look up a word in the dictionary.\n"
                                      "Type /info or /commands to rewind what I can I do.")
    db.set_property(str(message.chat.id), config.DB_cols.STATE.value, config.States.START.value)
    db.set_property(str(message.chat.id), config.DB_cols.LOOKUP.value, config.LookUp.START.value)


@bot.message_handler(commands=["info"])
def cmd_info(message):
    bot.send_message(message.chat.id, "I can send videos, dictionary entries and vocabulary exercises.\n"
                                      "I only know TED Talks video platform, all my videos come from there.\n"
                                      "Type /video to get one.\n"
                                      "Then you can give me a link to a TEDTalks video you like "
                                      "or I can choose one for you randomly.\n"
                                      "Mind you, I am a lazy pasta, so if you give me the choice, "
                                      "I will only send short videos under 6 minutes.\n"
                                      "One more thing: the video must have a transcript "
                                      "so that I could send you exercises.\n")
    bot.send_message(message.chat.id, "After you watch the video, tell me if you want to exercise or"
                                      " just to see the transcript.\n"
                                      "If you are in for a work-out, I will send you five fill-the-gap exercises.\n"
                                      "It's simple - you get a sentence from the video with \"______\" instead of a word "
                                      "and the task is to select the correct variant.\n"
                                      "If you get it wrong, I give you the answer straight away.\n")
    bot.send_message(message.chat.id, "At any time you can look up any unknown word in the dictionary.\n"
                                      "I'm friends with Merriam-Webster's Collegiate Dictionary, "
                                      "so it agreed to help us with definitions.\n"
                                      "Type /look_up, enter the word in the base form, then select a part of speech"
                                      " and I'll send you the definition.\n"
                                      "The base form  means: \n"
                                      + u"\U00002714" + "   book   " + u"\U0000274C" + "   books\n"
                                      + u"\U00002714" + "   work   " +  u"\U0000274C" + "   worked\n"
                                      "I hope you love words as much as I do and we can have lots of fun together!\n"
                                      "Type /commands to list the available commands.\n"
                                      "Type /reset to start anew.")

@bot.message_handler(commands=["commands"])
def cmd_commands(message):
    bot.send_message(message.chat.id,  "/start is used to start a new dialogue from the very beginning.\n"
                                        "/info is used to know what I can do for you.\n"
                                        "/look_up is used to look up a word in the dictionary.\n"
                                        "/video is used to get a video with exercises or transcript.\n"
                                        "/commands is used to see the list of commands.\n"
                                        "/reset is used to discard previous selections and start anew.\n")


# send link or choose random video
@bot.message_handler(commands=["video"])
def cmd_video(message):
    db.del_state(str(message.chat.id), config.DB_cols.STATE.value)
    markup = mark_up(['random'])

    bot.send_message(message.chat.id, "Send me a TED Talks video link "
                                      "or press "+"*"+"random"+"*"+" and let me find one for you!",
                     reply_markup=markup, parse_mode='Markdown')
    db.set_property(str(message.chat.id), config.DB_cols.STATE.value, config.States.SEND_LINK.value)


@bot.message_handler(commands=["look_up"])
def cmd_lookup(message):
    db.del_state(str(message.chat.id), config.DB_cols.LOOKUP.value)
    bot.send_message(message.chat.id, "Please enter a word")
    db.set_property(str(message.chat.id), config.DB_cols.LOOKUP.value, config.LookUp.LOOK_UP.value)


# check part-of-speech tags the word has in the dictionary and ask the user which one is needed
def dict_func_get_pos(word):
    my_dicts = requests.get(
        'https://dictionaryapi.com/api/v3/references/collegiate/json/' + word + '?key=' + config.MWkey).json()
    # if a word doesn't exist in the dictionary
    # or if the dictionary returns multiple variants
    # the dictionary tends to return a whole list for words with sp. char like 'k\'i'
    if my_dicts!=list() and any(isinstance(i, str) for i in my_dicts) is False:
        my_pos = []
        for i, pos in enumerate(my_dicts):
            if re.sub(r"\:\d", '', pos["meta"]["id"]) == word:
                my_pos.append(pos['fl'])
        if my_pos != list():
            return set(my_pos)
        else:
            return False
    else:
        return False


def dict_func_get_definition(word, my_pos):

    # remove the formatting tags from dictionary definitions
    def clean_dict_entry(string):
        return re.sub(r'((?<=\})see)|(\{.+?[\|\}])|([\{\|].+?\})|\}', '', string)

    #get word pronunciation mp3
    def get_audio(my_dicts):
        name = my_dicts[0]['hwi']['prs'][0]['sound']['audio']
        # these are directory naming patterns described in MW API
        if re.findall(r'^bix', name):
            subdirectory = 'bix'
        elif re.findall(r'^gg', name):
            subdirectory = 'gg'
        elif re.findall(r'^[1-9_,\.\\\/\?]', name):
            subdirectory = 'number'
        else:
            subdirectory = re.findall(r'^.', name)[0]

        audio = 'https://media.merriam-webster.com/audio/prons/en/us/mp3/' + subdirectory + '/' + name + '.mp3'
        return audio

    # A word definition consists of senses and subsenses
    # Get each sense from JSON received via MW API
    def get_sense(x, tag):
        res = []
        for i in x:
            if i != tag:
                # senses can be nested
                # so we go through the JSON recursively until we get to the tag we want
                if type(i) is list and res == list():
                    res = get_sense(i, tag)
                else:
                    continue
            elif i == tag:
                res = x
        return res

    my_dicts = requests.get(
        'https://dictionaryapi.com/api/v3/references/collegiate/json/' + word + '?key=' + config.MWkey).json()

    audio = get_audio(my_dicts)
    my_def = ''
    # parsing API-generated JSON to get definition
    # the JSON is nested to unknown depth
    # so I call a recursive get_sense function to reach the right tag
    for i, pos in enumerate(my_dicts):
        if re.sub(r"\:\d", '', pos["meta"]["id"]) == word:
            # print(pos,"\n\n")
            if pos['fl'] == my_pos:
                defs = pos['def']
                sseq = defs[0]['sseq']
                for sense in sseq:
                    for subsense in sense:
                        if subsense[0] == 'sense':
                            my_def = my_def + u"\n\U00002022 " + clean_dict_entry(subsense[1]['dt'][0][1].strip())
                        else:
                            s = get_sense(subsense, 'sense')
                            if s != list():
                                my_def = my_def+ u"\n\U00002022 " + clean_dict_entry(s[1]['dt'][0][1].strip())
    if my_def != '':
        return (my_def, audio)
    else:
        return False



@bot.message_handler(func=lambda message: (db.get_current_state(str(message.chat.id), config.DB_cols.LOOKUP.value) == config.LookUp.LOOK_UP.value)
                                          and message.text.strip().lower() != '/look_up')
def dict_enter_word(message):
    db.del_state(str(message.chat.id), config.DB_cols.LOOKUP.value)
    # get available POS-tags from the dictionary and give user the choice
    pos = dict_func_get_pos(message.text.lower().strip())
    if pos:
        # make everything a list as for only POS you get strings
        pos = list(pos)
        markup = mark_up(pos)
        bot.send_message(message.chat.id, "Please select the part of speech:\n", reply_markup = markup)
        db.set_property(str(message.chat.id), config.DB_cols.WORD.value, message.text.lower().strip())
        db.set_property(str(message.chat.id), config.DB_cols.POS.value, ", ".join(pos))
        db.set_property(str(message.chat.id), config.DB_cols.LOOKUP.value, config.LookUp.ENTER_WORD.value)
    else:
        bot.send_message(message.chat.id, "Sorry, I am afraid your word is not in Merriam-Wesbter's Dictionary")
        bot.send_message(message.chat.id, "Type /look_up to search for another word.\n"
                                          "Type /info or /commands to revise what I can do and see my commands.\n"
                                          "Type /reset to start anew.")
        db.set_property(str(message.chat.id), config.DB_cols.LOOKUP.value, config.LookUp.START.value)


@bot.message_handler(func=lambda message: (db.get_current_state(str(message.chat.id), config.DB_cols.LOOKUP.value) == config.LookUp.ENTER_WORD.value)
                                          and message.text.strip().lower() != '/look_up')
def dict_pos(message):
    pos = db.get_current_state(str(message.chat.id), config.DB_cols.POS.value)
    pos_input = message.text.lower().strip()
    # check if input is a correct POS-tag
    if pos_input in pos:
        db.del_state(str(message.chat.id), config.DB_cols.LOOKUP.value)
        word = db.get_current_state(str(message.chat.id), config.DB_cols.WORD.value).strip()
        # get the definition and audio
        my_def, audio = dict_func_get_definition(word, pos_input)
        if my_def:
            bot.send_audio(message.chat.id, audio, '*'+word+'*', parse_mode='Markdown')
            bot.send_message(message.chat.id, my_def)
            db.set_property(str(message.chat.id), config.DB_cols.LOOKUP.value, config.LookUp.START.value)
            bot.send_message(message.chat.id, "Type /look_up to search for another word.\n"
                                              "Type /info or /commands to revise what I can do and see my commands.\n"
                                              "Type /reset to start anew.")
        else:
            bot.send_message(message.chat.id, "Sorry, I am afraid your word is not in Merriam-Webster's Dictionary")
            bot.send_message(message.chat.id, "Type /look_up to search for another word.\n"
                                              "Type /info or /commands to revise what I can do and see my commands.\n"
                                              "Type /reset to start anew.")
            db.set_property(str(message.chat.id), config.DB_cols.LOOKUP.value, config.LookUp.START.value)
    else:
        markup = mark_up(pos.split(','))
        bot.send_message(message.chat.id, "Seems like there was a typo in your input.\n"
                                          "Please, select a part of speech and press the corresponding button."
                         , reply_markup=markup)



# get video url from webpage
def vid_func_get_url(page_url):
    try:
        page = requests.get(page_url).text
        soup = BeautifulSoup(page, 'lxml')
        json_descr = str(soup.find_all('script', {"data-spec": "q"}))
        url = re.search(r'(?<=low\"\:\").+?(?=\")', json_descr)
        if url:
            print('my', str(url.group()))
            return str(url.group())
        else:
            url = re.search(r'(?<=file\"\:\").+?(?=\")', json_descr)
            print('my', str(url.group()))
            return str(url.group())
    except:
        return False


def vid_func_get_transcript(url):
    transcr_url = re.sub(r'(\?language=en)|\/$', '', url) + '/transcript'
    page = requests.get(transcr_url).text
    soup = BeautifulSoup(page, 'lxml')
    transcr_parts = soup.find_all('div', {'class': "Grid__cell flx-s:1 p-r:4"})
    transcript = ''
    for part in transcr_parts:
        transcript = transcript + ' ' + re.sub(r'\s+', ' ', part.text.strip())
    if transcript:
        return transcript
    else:
        return False


# get keywords, cut them out of sentences and generate variants for test
def vid_func_get_exercise(transcript):

# generate variants for test
# first, go to the website which offers interface for 'English GoogleNews Negative300'-traned model
# if nothing found, go to rhymezone to get similar-sounding words
    def gen_variants(words):
        all_vars = {}
        w2v_demo = 'http://bionlp-www.utu.fi/wv_demo/'
        try:
            wv_vars ={}
            driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
            print(0)
            driver.get(w2v_demo)
            print(1)
            model = Select(driver.find_element_by_id('model_select'))
            driver.implicitly_wait(2)
            model.select_by_visible_text('English GoogleNews Negative300')
            field = driver.find_element_by_id('word')
            print(2)
            for word in words.keys():
                field.send_keys(word)
                driver.implicitly_wait(2)
                driver.find_element_by_id('submitword').click()
                time.sleep(0.1)
                wv_output = driver.find_element_by_css_selector('#nearestresult > div').text
                wv_vars[word] = wv_output.lower()
                field.clear()
            driver.close()
            for k, v in wv_vars.items():
                vals = v.split('\n')
                clean_vars = []
                for val in vals:
                    # we don't want phrases or the same word in different number, e.g. wizard-wizards
                    if (k not in val) and (re.sub(r's$','',k) not in val) and ('_' not in val):
                        clean_vars.append(val)
                    # 3 variants is enough
                    if len(clean_vars) == 2:
                        clean_vars.append(k)
                        all_vars[k] = sorted(clean_vars)
        except TypeError:
            print(TypeError.with_traceback())

        if all_vars=={}:
            print("No vectors, go for similar sounds")
            for word in words.keys():
                link = "https://www.rhymezone.com/r/rhyme.cgi?Word=" + word + "&typeofrhyme=sim&org1=syl&org2=l&org3=y"
                print(link)
                try:
                    page = requests.get(link).text
                    soup = BeautifulSoup(page, 'lxml')
                    res = soup.find_all('script', {"language": "javascript"})
                    word = re.findall('word\"\:\"(.+?)".+?tags\"\:\[\"(.+?)\"pron\:', str(res[0]))
                    if word:
                        for w in word[1:]:
                            variants = []
                            if 'prop' not in w[1]:
                                variants.append(w[0].lower().strip())
                                print(w)
                            if len(variants) == 2:
                                variants.append(word)
                                all_vars[word] = sorted(variants)
                                break
                except TypeError:
                    return False

        print(all_vars)
        exercises = {}
        # dict with keywords, sentence exercises and answer variants
        for variant in all_vars.keys():
            exercises[variant] = [words[variant], all_vars[variant]]

        return exercises


    # break text into sentences, then into tokens, then assign POS tags
    sentences = nltk.sent_tokenize(transcript)
    tokens = nltk.word_tokenize(transcript)
    tagged = nltk.pos_tag(tokens)
    print(tagged)

    # n = max phrase length in tokens
    # dedupLim = deduplication_threshold
    # top = number of keywords
    kw_extractor = yake.KeywordExtractor(lan='en', n=1, dedupLim=0.9, top=50, features=None)
    keywords = pd.DataFrame(kw_extractor.extract_keywords(transcript))
    keywords.columns = ['keyword', 'relevance']
    keywords['keyword'].str.replace('’', '\'')
    keywords = keywords[~keywords['keyword'].isin(['n\'t', '\'s', '\'', 'n’t'])]
    print(keywords)
    # we only want more interesting and rare keywords for the exercise
    # so we filter them out by frequency [based on Exquisite Corpus]
    keywords['frequency'] = keywords['keyword'].apply(zipf, lang='en')
    keywords = keywords[keywords['frequency'] < 4.5]
    proper = [i[0].lower().strip() for i in tagged if i[1] == 'NNP']
    keywords = keywords[~keywords['keyword'].isin(proper)]
    keywords = keywords.sort_values(by=['frequency'])
    kw_list = list(keywords['keyword'].head(10))
    print(kw_list)

    # now we need sentences for fill-the-gap task
    # loop through sentences until one of the keywords is found
    # then create kw: sent pair where keyword is cut out of the original sentence
    # remove the added kw and move to the next sentence
    sents = {}
    for i, sent in enumerate(sentences):
        for kw in kw_list:
            if kw in sent:
                sents[kw] = sent.replace(kw, '_______')
                kw_list.remove(kw)
                break
        if len(sents) == 5:
            break
    print(sents)
    return gen_variants(sents)


# send video to the user
@bot.message_handler(func=lambda message: (db.get_current_state(str(message.chat.id), config.DB_cols.STATE.value) == config.States.SEND_LINK.value)
                                          and (db.get_current_state(str(message.chat.id), config.DB_cols.LOOKUP.value) == config.LookUp.START.value)
                                          and message.text.strip().lower() not in cmd)
def vid_send_video(message):
    mg = message.text.lower().strip()
    markup = mark_up(['exercise','transcript'])
    if mg == 'random':
        bot.send_message(message.chat.id, "Great! Give me a moment to find a video.")
        # use our pre-compiled list of urls
        with open('urls.txt', 'r') as file:
            random_urls = [file.readline().strip() for line in file]
        my_random = random_urls[randint(0, len(random_urls))]
        print('my random', my_random)
        url = vid_func_get_url(my_random)
        print('got', url)
        if url:
            bot.send_video(message.chat.id, url)
            bot.send_message(message.chat.id, "After you watch the video press " +"*"+"exercise"+"*"+" to train your vocabulary!"
                                              "You can also just see the full " +"*"+"transcript"+"*"
                             ,reply_markup=markup, parse_mode='Markdown')
            db.set_property(str(message.chat.id), config.DB_cols.URL.value, my_random)
            db.set_property(str(message.chat.id), config.DB_cols.STATE.value, config.States.SEND_EXERCISE.value)

        else:
            mk = mark_up(['random'])
            bot.send_message(message.chat.id, "Sorry, I am afraid I can't access videos now.\n"
                                              "Please send "+"*"+"random"+"*"+" to try again.\n"
                                              "To start anew send /reset"
                             ,reply_markup=mk, parse_mode='Markdown')
    else:
        url = vid_func_get_url(mg)
        print(url)
        if url:
            bot.send_message(message.chat.id, "Great! Give me a moment to find a video.")
            bot.send_video(message.chat.id, url)
            bot.send_message(message.chat.id, "After you watch the video press " +"*"+"exercise"+"*"+" to train your vocabulary!"
                                              "You can also just see the full " +"*"+"transcript"+"*"
                             ,reply_markup=markup, parse_mode='Markdown')
            db.set_property(str(message.chat.id), config.DB_cols.URL.value, mg)
            db.set_property(str(message.chat.id), config.DB_cols.STATE.value, config.States.SEND_EXERCISE.value)
        else:
            mk = mark_up(['random'])
            bot.send_message(message.chat.id, "Sorry, seems like you entered an invalid link\n"
                                              "Please send me a valid link or type "+"*"+"random"+"*"+
                                              " and I will pick one for you!"
                             ,reply_markup=mk, parse_mode='Markdown')


@bot.message_handler(func=lambda message: (db.get_current_state(str(message.chat.id), config.DB_cols.STATE.value) == config.States.SEND_EXERCISE.value)
                                          and (db.get_current_state(str(message.chat.id), config.DB_cols.LOOKUP.value) == config.LookUp.START.value)
                                          and message.text not in cmd)
def vid_transcript_or_exercise(message):
    mg = message.text.strip().lower()
    if mg in ['transcript','exercise']:
        db.del_state(str(message.chat.id), config.DB_cols.STATE.value)
        url = db.get_current_state(str(message.chat.id), config.DB_cols.URL.value)
        transcript = vid_func_get_transcript(url)
        if transcript:
            if mg == 'transcript':
                bot.send_message(message.chat.id, 'OK, transcript\'s coming.')
                # in case transcript is longer than message max length
                # a user can send a link to a very long video
                if len(transcript)>2000:
                    sents = nltk.sent_tokenize(transcript)
                    print(sents)
                    part = ''
                    parts =[]
                    for sent in sents:
                        part = part + ' ' + sent.strip()
                        if len(part) <2000:
                            pass
                        else:
                            parts.append(part)
                            part = ''

                    for p in parts:
                         bot.send_message(message.chat.id, p)

                    bot.send_message(message.chat.id, 'Kind reminder: you can always /look_up a new word.\n'
                                                      'Would you like to /reset?')
                    db.set_property(str(message.chat.id), config.DB_cols.STATE.value, config.States.START.value)
                else:
                    bot.send_message(message.chat.id, transcript)
                    bot.send_message(message.chat.id, 'Kind reminder: you can always /look_up a new word.\n'
                                                      'Would you like to /reset?')
                    db.set_property(str(message.chat.id), config.DB_cols.STATE.value, config.States.START.value)

            elif mg == 'exercise':
                bot.send_message(message.chat.id, 'OK, exercises are on the way.\n'
                                                  'If you don\'t know a word or two -\n'
                                                  ' just  /look_up :-)\n')
                exercises = vid_func_get_exercise(transcript)
                if exercises:
                    exercises = json.dumps(exercises)
                    db.set_property(str(message.chat.id), config.DB_cols.EXERCISES.value, exercises)
                    db.set_property(str(message.chat.id), config.DB_cols.STATE.value, config.States.EXERCISE_CHECKED.value)
                    db.set_property(str(message.chat.id), config.DB_cols.COUNTER.value, "0")
                    vid_send_exercise(message)
                else:
                    bot.send_message(message.chat.id, "I beg your pardon!\n"
                                                      "For some reason no exercises were found.\n"
                                                      "Maybe it's the tricks of Don Rigatoni, he is such a mobster.\n"
                                                      "Anyway, we can always start anew with /reset!")
                    bot.send_photo(message.chat.id, config.rigatoni_img)
                    db.set_property(str(message.chat.id), config.DB_cols.STATE.value,
                                    config.States.START.value)

        else:
            bot.send_message(message.chat.id, "I beg your pardon!\n"
                                              "For some reason no transcript was found.\n"
                                              "Maybe it's the tricks of Don Rigatoni, he is such a mobster.\n"
                                              "But we can always start anew with /reset!")
            bot.send_photo(message.chat.id, config.rigatoni_img)
            db.set_property(str(message.chat.id), config.DB_cols.STATE.value,
                            config.States.START.value)
    else:
        markup = mark_up(['exercise','transcript'])
        bot.send_message(message.chat.id, "Seems like there was a typo in your input.\n"
                                          "Please, press \"exercise\" to train your vocabulary"
                                          "or \"transcript\" to get the transcript."
                                 , reply_markup=markup)


@bot.message_handler(func=lambda message: (db.get_current_state(str(message.chat.id),config.DB_cols.STATE.value) == config.States.EXERCISE_SENT.value)
                                          and (db.get_current_state(str(message.chat.id),config.DB_cols.LOOKUP.value) == config.LookUp.START.value))
def vid_check_exercise(message):
    db.del_state(str(message.chat.id), config.DB_cols.STATE.value)
    correct = db.get_current_state(str(message.chat.id), config.DB_cols.EX_KEY.value)
    if message.text.strip().lower() == correct:
        bot.send_message(message.chat.id, 'Correct!')
        counter = db.get_current_state(str(message.chat.id), config.DB_cols.COUNTER.value) + 1
        db.set_property(str(message.chat.id), config.DB_cols.COUNTER.value, counter)
    else:
        bot.send_message(message.chat.id, 'Sorry, the correct answer is ' + correct)

    if db.get_current_state(str(message.chat.id), config.DB_cols.EXERCISES.value) == '{}':
        counter = db.get_current_state(str(message.chat.id), config.DB_cols.COUNTER.value)
        # if got more than half - well done and get a cat, otherwise - not so well and get a penguin
        if counter>=3:
            bot.send_photo(message.chat.id, config.well_done_img)
            bot.send_message(message.chat.id, '{} out of 5\nGood job!'.format(counter))
        else:
            bot.send_photo(message.chat.id, config.not_so_well_img)
            bot.send_message(message.chat.id, '{} out of 5\nNice, but seems like you got a bit tangled up with words.\n'
                                              'I\'m sure next time will be better!'.format(counter))
        db.set_property(str(message.chat.id), config.DB_cols.STATE.value, config.States.START.value)
        bot.send_message(message.chat.id, 'Would you like to /reset?')
    else:
        db.set_property(message.chat.id, config.DB_cols.STATE.value, config.States.EXERCISE_CHECKED.value)
        vid_send_exercise(message)


@bot.message_handler(func=lambda message: (db.get_current_state(str(message.chat.id), config.DB_cols.STATE.value) == config.States.EXERCISE_CHECKED.value)
                                          and (db.get_current_state(str(message.chat.id), config.DB_cols.LOOKUP.value) == config.LookUp.START.value))
def vid_send_exercise(message):
    exercises = json.loads(db.get_current_state(str(message.chat.id),config.DB_cols.EXERCISES.value))
    for k, v in exercises.items():
        markup = mark_up(v[1])
        # send exercises and variants as buttons (added to markup)
        bot.send_message(message.chat.id, v[0], reply_markup=markup)
        db.set_property(str(message.chat.id),config.DB_cols.EX_KEY.value, k)
        exercises.pop(k)
        break
    #convert to json before putting to db to avoid problems with quotes when retrieving from db
    exercises = json.dumps(exercises)
    db.set_property(str(message.chat.id), config.DB_cols.EXERCISES.value, exercises)
    db.set_property(str(message.chat.id), config.DB_cols.STATE.value, config.States.EXERCISE_SENT.value)


@bot.message_handler(func=lambda message: message.text not in (cmd,'transcript','exercise'))
def sample_message(message):
    bot.send_message(message.chat.id, "Hello again! I can help you learn some new words.\n"
                                      "I can send you a video and some exercises.\n"
                                      "Type /video to get a video.\n"
                                      "Type /info or /commands to know more about me or list available commands.")
    db.set_property(message.chat.id, config.DB_cols.STATE.value, config.States.START.value)
    db.set_property(str(message.chat.id), config.DB_cols.LOOKUP.value, config.LookUp.START.value)


@server.route('/' + config.token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=config.heroku_name + config.token)
    return "!", 200


if __name__ == '__main__':
    #bot.remove_webhook()
    #bot.infinity_polling()
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))


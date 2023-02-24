import requests
import os
import re
from collections import defaultdict
import bs4
import feedparser
import datetime
import json
import time
import telebot
from telebot import types
from telegram import ParseMode

USE_STATEMENTS = True

bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))

def make_multi_choice_markup(info,row_size=6):
    print('make multichoice markup')
    print(info)
    if len(info) > row_size:
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=row_size)
    else:
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = []
    for title in info:
        print('adding title text')
        print(title)
        buttons.append(types.KeyboardButton(title))
        if len(buttons)==row_size:
            print('buttons to markup')
            print(buttons)
            markup.add(*buttons)
            buttons = []
    markup.add(*(buttons))
    return markup

sent_info = defaultdict(set)

def send_in_chunks(chat_id, message_text,reply_markup=None):
    if chat_id is None:
        print('No chat id received')
        return None
    if isinstance(message_text, list):
        print(f'Call send_in_chunks for {message_text} recursively')
        for line in message_text:
            send_in_chunks(chat_id,line,reply_markup)
    else:
        print('call send_in_chunks')
        print(chat_id)
        print(message_text)
        MAX_MESSAGE_LEN = 4096
        if '</a>' in message_text or '</b>' in message_text:
            parse_mode = ParseMode.HTML
        else:
            parse_mode=None
        if message_text[:4] == 'http' and len(message_text)<1280 and validators.url(message_text):
            bot.send_photo(chat_id, message_text)#,reply_markup)
        else:
            if len(message_text)>MAX_MESSAGE_LEN:
                print('Sending in chunks')
                print(message_text)
                message_lines = message_text.split('\n')
                to_send = ''
                for i in range(len(message_lines)):
                    if len('\n'.join([to_send, message_lines[i]])) > MAX_MESSAGE_LEN:
                        try:
                            a=bot.send_message(chat_id, to_send,reply_markup=reply_markup,parse_mode=parse_mode)
                        except:
                            a=bot.send_message(chat_id, to_send,reply_markup=reply_markup,parse_mode=None)
                        print(str(a))
                        to_send = message_lines[i]
                    else:
                        to_send = '\n'.join([to_send, message_lines[i]])
                try:
                    a=bot.send_message(chat_id, to_send,reply_markup=reply_markup,parse_mode=parse_mode)
                except:
                    a=bot.send_message(chat_id, to_send,reply_markup=reply_markup,parse_mode=None)

                print(str(a))
            else:
                print('send in full')
                try:
                    bot.send_message(chat_id,message_text,reply_markup=reply_markup,parse_mode=parse_mode)
                except:
                    bot.send_message(chat_id,message_text,reply_markup=reply_markup,parse_mode=None)


cookies = {
    'session-cookie': '16fc4074932eb66914398a2eb4b53d11372cebbf768d9e4c5b1db3a66279e36753e0585207960e06f90c728ab675dbe0',
    'csrf-token-name': 'csrftoken',
    'csrf-token-value': '16fc4309d8f9b30fac4851f14be15d6e5820cb140d7aa90f1522ce27411755333a73d2cd5fac0d18',
    'JSESSIONID': '3DE6197134148F65DBDF4905A5F4DAED',
}
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:101.0) Gecko/20100101 Firefox/101.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    # Requests sorts cookies= alphabetically
    # 'Cookie': 'session-cookie=16fc4074932eb66914398a2eb4b53d11372cebbf768d9e4c5b1db3a66279e36753e0585207960e06f90c728ab675dbe0; csrf-token-name=csrftoken; csrf-token-value=16fc4309d8f9b30fac4851f14be15d6e5820cb140d7aa90f1522ce27411755333a73d2cd5fac0d18; JSESSIONID=3DE6197134148F65DBDF4905A5F4DAED',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'x-youtube-client-name': '1',
    'x-youtube-client-version': '2.20200529.02.01'
}

def remove_nested_parens(input_str):
    """Returns a copy of 'input_str' with any parenthesized text removed. Nested parentheses are handled."""
    result = ''
    paren_level = 0
    for ch in input_str:
        if ch == '{':
            paren_level += 1
        elif (ch == '}') and paren_level:
            paren_level -= 1
        elif not paren_level:
            result += ch
    return result
def is_telegram_event(event):
    return False

def text_from_message(raw_message):
    text_data = raw_message.split('</div>')[0]
    print(text_data)
    text_data = text_data.replace('<br/><br/>','\n').replace('&quot;','"').replace('&#33;','!')
    text_data = bs4.BeautifulSoup(text_data).get_text().replace('\n','<br>')
    return text_data

def last_telegram_messages_by_link(link, days=7):
    data = requests.get(link).text
    text_datas = data.split('<div class="tgme_widget_message_text js-message_text" dir="auto">')
    end_tag='<span class="tgme_widget_message_meta">'
    text_datas=[k for k in text_datas if 'time datetime' in k]
    times=[k.split('<time datetime="')[1].split('"')[0] for k in text_datas]
    text_datas = [k.split(end_tag)[0] if end_tag in k else '' for k in text_datas]
    times = [datetime.datetime.strptime(time_[:-3],'%Y-%m-%dT%H:%M:%S+%f') for time_ in times]
    texts_to_keep = [text_from_message(msg) for time_,msg in zip(times, text_datas)
    if (times[-1] - time_).days<days]
    return '<br>========<br>'.join(texts_to_keep)

def last_telegram_message_by_link(link,mode='text'):
    data = requests.get(link).text
    image_data = 'http'+data.split("background-image:url(\'http")[-1].split("\'")[0]
    text_datas = data.split('<div class="tgme_widget_message_text js-message_text" dir="auto">')
    text_data = text_from_message(text_datas[-1])
    if '@mod_russia' in text_data.lower():
        date = text_data.split('(')[1].split(')')[0]
        messages_of_date = [raw_message for raw_message in text_datas if date in raw_message]
        texts = [text_from_message(msg) for msg in messages_of_date]
        text_data = '\n'.join(texts)
        text_data=text_data.replace('<br>📄 Читать<br>',' ')
    return text_data


def make_hyperlink(link,text):
    return f'<a href="{link}">{text}</a>\n'


def articles():
    answer = ''
    url='https://papers.labml.ai/'
    
    our_header={'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5','User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0',
                'DNT': '1','Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1','Sec-Fetch-Dest': 'document','Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none','Sec-Fetch-User': '?1','TE':'trailers'}
    our_cookie={'Authorization':requests.post('https://papers.labml.ai/api/v1/auth/user',json=our_header).headers['authorization']}
    daily_papers = []
    for mode in ['recent','daily','weekly','monthly']:
        answer=answer+f'<br> <h4>NLP articles {mode}</h4></br>'
        t=time.time()
        #WE NEED TO LOGING FIRST!
        data=requests.get(f'https://papers.labml.ai/api/v1/papers/?sorted_by={mode}&start=0&end=250',headers=our_header,cookies=our_cookie).text
        paper_list=[]
        always_open=['NLP']
        papers = json.loads(data)['data']['papers']
        daily_paper_keys=[]
        if mode=='daily':
            daily_papers = papers
        else:
            papers = [k for k in papers if k not in daily_papers]
            print(len(papers))
        papers = sorted(papers,key=lambda x:-x['num_tweets'])
        for paper in papers:
            title_name = paper['title']['text']
            category_name = paper['primary_category']
            title = f"{title_name} ({category_name})"
            if 'html' in paper['meta_summary'] and paper['meta_summary']['html']:
                summary = paper['meta_summary']['html'].strip().replace('<p>','')
            else:
                summary = paper['meta_summary']['text'].strip().replace('<p>','')
            n_tweets = paper['num_tweets']
            n_likes = paper['favorite_count']
            n_ret = paper['retweet_count']
            date = time.localtime(paper['published'])
            date = '-'.join([str(s) for s in [date.tm_mday,date.tm_mon,date.tm_year]])
            link=f'https://papers.labml.ai/paper/{paper["paper_key"]}'
            hyperlink=make_hyperlink(link,'вот')
            our_pick=paper['is_our_pick']
            description=f'{date} 🐦 {n_tweets} 🔁 {n_ret} ♥ {n_likes}'
            title = '<br>'.join([title, description])
            if our_pick:
                description = f'👍{description}'
            additional_info = f'{summary}{hyperlink}'
            #if category_name not in always_open and False:
            additional_info = make_spoiler(additional_info,'Открыть')
            paper_info = f'<b>{title}</b><br>{additional_info}'
            paper_list.append(paper_info)
        mode_answer = '<br>'.join(paper_list)
        mode_answer=make_spoiler(mode_answer,'Показать')
        answer = answer+'<br>'+mode_answer
    return answer


def it_news(last_days=0):
    seconds_in_a_day = 86400
    feeds = []
    used_ids=set()
    health = 'https://habr.com/ru/rss/hub/health/all/?fl=ru'
    scipop='https://habr.com/ru/rss/hub/popular_science/all/?fl=ru'
    career='https://habr.com/ru/rss/hub/career/all/?fl=ru'
    ai_feed='https://habr.com/ru/rss/hub/artificial_intelligence/all/?fl=ru/'
    ml_feed = 'https://habr.com/ru/rss/hub/machine_learning/all/?fl=ru'
    python='https://habr.com/ru/rss/hub/python/all/?fl=ru'
    code='https://habr.com/ru/rss/hub/complete_code/all/?fl=ru'
    links = [scipop,health,career,ai_feed,ml_feed,python,code]
    for link in links:
        for entry in feedparser.parse(link)['entries']:
            if entry.id not in used_ids:
                feeds.append(entry)
                used_ids.add(entry.id)
    feeds=sorted(feeds, key=lambda x:x.published_parsed)[::-1]
    last_time=time.mktime(feeds[0].published_parsed)
    answer = ''
    for entry in feeds:
        title = entry.title
        summary = bs4.BeautifulSoup(entry.summary).get_text()
        link = entry.link
        tags = '<i>'+';'.join([k['term'] for k in entry.tags])+'</i>'
        is_recent = (last_time - time.mktime(entry.published_parsed)) < last_days*seconds_in_a_day
        header = f'<h3><u>{title}</u></h3><br>{tags}<br>'
        hyperlink=make_hyperlink(link,'тут')
        if not is_recent:
            full_text = make_spoiler(hyperlink,'Подробнее')
        else:
            data=requests.get(link).text
            v=data.split('<div class="article-formatted-body')[1]
            div_index = v.index('<div')
            v=v[div_index:].split('<div class="tm-article-presenter__meta">')[0]
            v='<br><div'+v+'<br>'+hyperlink
            full_text = make_spoiler(v,'Подробнее')
        info = f'{summary}<br>{full_text}<br>'
        answer=f'{answer}{header}{info}'
    return answer

def weather():
    city_name,city_link='Москва','https://www.iqair.com/ru/russia/moscow'
    mskdata=requests.get(city_link).text
    start='<table _ngcontent-sc246="" class="aqi-forecast__weekly-forecast-table"'
    end='</table>'
    v=mskdata.split('<table _ngcontent-sc246="" class="aqi-forecast__weekly-forecast-table"')[1].split('</table>')[0]
    v1=re.compile(r'<img.*?>').sub('',v)#remove html data
    v1 = v1.replace('Погода','Шанс дождя').replace('AQI США', 'AQI')
    answer=start+v1+end
    return answer


def make_spoiler(info,text='За прошлую неделю'):
    return f'<details><summary>{text}</summary>{info}</details>'

def get_important_laws():
    law_ids=['207803-8','214382-8','206845-8','220951-8','220935-8','259823-8']
    law_names=['Законопроект Авксентьевой(про АГС при мобилизации)','Законопроект СР(про освобождение Вшников)',
               'Законопроект Слуцкого(про мобилизацию только служивших)',
              'Законопроект Матвеева(про мобилизацию только служивших)',
              'Законопроект Матвеева(про освобождение кандидатов наук)',
              'Законопроект Горячевой(про освобождение кандидатов наук и 1 год отсрочки после аспирантуры)']
    answer='<br><h2>Новости отслеживаемых законопроектов</h2><br>'
    def get_date(x):
        x=x['title_detail']['value']
        x=x.split('(')[1].split(')')[0]
        try:
            return datetime.datetime.strptime(x, '%d.%m.%Y %H:%M:%S')
        except:
            return datetime.datetime(year=1970,month=1,day=1)
    for law_id,law_name in zip(law_ids,law_names):
        answer=answer+f'<b>{law_name}</b><br><i>{law_id}</i><br>'
        url=f'https://sozd.duma.gov.ru/bill/{law_id}/rss'
        data=feedparser.parse(requests.get(url).text)
        print(data['entries'])
        data['entries']=sorted(data['entries'],key=lambda x: get_date(x))
        for entry in data['entries']:
            answer=answer+entry['title']+'<br>'+entry['summary']+'<br>'
    return answer

def get_explainrf():
    #return make_spoiler(last_telegram_messages_by_link(f'https://t.me/s/obyasnayemrf'),text='<b>Что пишет Объясняем.РФ</b>')
    return last_telegram_messages_by_link('https://t.me/s/obyasnayemrf')

def get_status_program():
    a=feedparser.parse(requests.get('https://teletype.in/rss/eschulmann').text)['entries']
    last_program=None
    for entry in a:
        title=entry['title']
        date=entry['published_parsed']
        if last_program is None:
            last_program=entry
        elif 'Статус' in title and date>last_program['published_parsed']:
            last_program=entry
    answer= last_program['content'][0]['value']
    title=last_program['title']+f' {last_program["published"]}'
    answer=answer.replace('<br />', ' - <br />')
    answer=bs4.BeautifulSoup(answer).get_text().replace('\n','<br>')
    answer = re.sub(r'http\S+', '', answer)
    answer = 'НАСТОЯЩИЙ МАТЕРИАЛ (ИНФОРМАЦИЯ) ПРОИЗВЕДЕН, РАСПРОСТРАНЕН И (ИЛИ) НАПРАВЛЕН ИНОСТРАННЫМ АГЕНТОМ ШУЛЬМАН ЕКАТЕРИНОЙ МИХАЙЛОВНОЙ, ЛИБО КАСАЕТСЯ ДЕЯТЕЛЬНОСТИ ИНОСТРАННОГО АГЕНТА ШУЛЬМАН ЕКАТЕРИНЫ МИХАЙЛОВНЫ<br>'+answer
    answer=make_spoiler(answer,text=f'<br><br><h4>{title}</h4>' +'(по клику)')
    v='Подписывайтесь на другие соцcети Екатерины Шульман'
    answer=answer.replace(v,'')
    return answer

def get_law_info():
    answer= []
    date=None
    import re
    from collections import defaultdict
    source = 'Информация о новых законах.'
    header_daily = defaultdict(list)
    header_weekly=defaultdict(list)
    for mode in ['Ежедневные','Еженедельные'][:1]:    
        if mode == 'Ежедневные':
            pattern = '/law/review/fed/fd'
            split_pattern1 = '</p>'
            split_pattern2 = '<p class="rev_ann">'
        elif mode== 'Еженедельные':
            pattern = '/law/review/fed/fw'
            split_pattern1 = '</span>'
            split_pattern2 = '<span style="font-weight:bold;">'
        law_info = requests.get('http://www.consultant.ru/law/review/fed/').text.split(pattern)[1]
        pattern = pattern+law_info.split('"')[0]
        if mode=='Ежедневные':
            date=law_info.split('"')[0]
        link='http://www.consultant.ru'+pattern
        remove_tags = lambda x: re.sub('<[^>]*>', '',x).replace('<','').strip()
        laws=requests.get(link).text.replace('&quot;','"')
        laws=laws.replace('doc_empty','doc_link')
        all_links=[k.replace('//static','http://static').split('<a href="')[1].split('">')[0] if 'a href="' in k
                        else link
                        for k in laws.split('<p class="doc_link">')][1:]
        all_links = [k.replace('http://http://','http://').replace('https:http','http') for k in all_links]
        
        in_short = [k[:k.index(split_pattern1)].replace('\r','').strip() for k in laws.split(split_pattern2)][1:]
        in_long = [k[:k.index('a id')] if 'a id' in k else k[:k.index('a href')] for k in laws.split(split_pattern2)][1:]

        in_header = [k[k.index('<h3>'):k.index('</h3>')].split('</a>')[1]
                    if '<h3>' in k else ''  for k in laws.split(split_pattern2)]
        assert len(in_long)==len(in_short)==len(all_links)==len(in_header)-1,str([len(h) for h in [in_long,in_short,all_links,in_header]])
        answer_mode = '<b>'+in_header[0]+'</b>\n'
        current_header = in_header[0]
        for link,text,short_text,after_header in zip(all_links,in_long,in_short,in_header):
            text = remove_tags(text)
            short_text=remove_tags(short_text)
            if mode=='Ежедневные':
                header_daily[current_header].append('<b>'+short_text+'</b><br>'+text+'</br>')
            else:
                header_weekly[current_header].append('<b>'+short_text+'</b><br>'+text+'</br>')
            if after_header:
                current_header = after_header
        for key in header_weekly:
            for key1 in list(header_weekly.keys())+list(header_daily.keys()):
                if key1 in header_weekly[key][-1]:
                    header_weekly[key][-1]=header_weekly[key][-1].replace(key1,'')
        for key in header_daily:
            for key1 in list(header_weekly.keys())+list(header_daily.keys()):
                if key1 in header_daily[key][-1]:
                    header_daily[key][-1]=header_daily[key][-1].replace(key1,'')            
        answer.append(answer_mode)
    answer=f"<br><br><b>НОВЫЕ ЗАКОНЫ {date}</b><br><br>"
    for topic in header_daily:
        answer = answer+f'<h5>{topic}</h5><br><br>'
        daily_data = '<br>'.join(header_daily[topic])
        if topic in header_weekly:
            weekly_data = make_spoiler('<br>'.join(header_weekly[topic]))
        else:
            weekly_data=''
        answer = answer + daily_data + weekly_data
    for topic in header_weekly:
        if topic not in header_daily:
            answer = answer+f'<h5>{topic}</h5><br><br>'
            weekly_data = make_spoiler('<br>'.join(header_weekly[topic]))
            answer = answer + weekly_data
    answer = make_spoiler(answer,'Все новые законы')
    try:
        answer = make_spoiler(get_explainrf(),'Что пишут на Объясняем.рф') + '<br>'+answer
    except Exception as e:
        answer=answer+f'<br>Новости с Объясняем.рф не получены {e}'+'<br>'
    try:
        answer=answer+'<br>'+get_status_program()
    except Exception as e:
        answer=answer+f'<br>Программа Статус не получена {e}<br>'
    return answer

def decode(message,preserve_hyperlinks=True,preserve_speech=True):
    strk=''
    for i in range(0,len(message)):
        if ord(message[i])==208:
            strk=strk+chr(ord(message[i+1])+896)
        elif ord(message[i])==209:
            strk=strk+chr(ord(message[i+1])+960)
        elif ord(message[i])<128:
            strk=strk+message[i]
    strk=strk.replace('<p>','%%%').replace('</p>','%%%')
    strk = bs4.BeautifulSoup(strk,'lxml').get_text()
    strk=strk.replace('%%%','</br>')
    strk='Архив'.join(strk.split('Архив')[:-1])
    return strk 


def weekly_patrio_news():
    link='https://www.время-вперед.рус/blog-feed.xml'
    data=feedparser.parse(requests.get(link).text)['entries']
    title= f"Программа 'Время-Вперёд' {data[0]['published']}"
    content=data[0]['content'][0]['value']
    content=bs4.BeautifulSoup(content).get_text().replace('\n','<br>')
    content=re.sub(r'http\S+', '', content)
    content=content.split('Подписывайтесь на')[0].replace('время-вперед.рус','')
    content=make_spoiler(content,text=f'<br><br><h4>{title}</h4>(по клику)')
    return content

def patrio_news():
    patrio_url = [k for k in requests.get('http://снми.рф').text.split('"') if 'https://' in k ][-1]
    data=requests.get(patrio_url).text 
    data=decode(data,preserve_hyperlinks=False)
    data = make_spoiler(data,'Читать СНМИ')
    other_content = '<br>'.join([make_spoiler(last_telegram_messages_by_link(f'https://t.me/s/{patrio_author}'),
                                 text=name)
                                 for patrio_author, name in zip(
                                     ['vmarahovsky', 'crimsondigest','auantonov'],
                                     ['<b>Что пишет Мараховский</b>','<b>Что пишет Данилов</b>',
                                     '<b>Что пишет Антонов</b>'])])
    try:
        data = data+'<br>'+other_content
    except:
        data = data+'<br>Посты авторов СНМИ не получены'
    try:
        data=data+'<br>'+weekly_patrio_news()+'<br>'
    except:
        data=data+'<br>Программа Время-Вперед не получена <br>'        
    return data

def about_news(news_file='why_news_are_harmful.txt'):
    news_len = open(news_file,'r').readlines()
    headers = []
    messages = []
    for line in news_len:
        if line[0]=='$':
            headers.append(line[1:])
        elif len(messages) < len(headers):
            messages.append(line)
        elif len(line.strip())==0:
            messages[-1] = messages[-1]+'<br><br>'
        else:
            messages[-1]=messages[-1]+' '+line.strip()
    answer='<br>'.join([make_spoiler(message.replace('\n','<br>'), text= f'<b>{header}</b>')
                        for message, header in zip(messages, headers)])
    return answer      

def finance_news():
    link='https://t.me/s/fintraining'
    KOMAROVSKY=False
    t=time.time()
    try:
        if KOMAROVSKY:
            finance_link='https://pikabu.ru/@RationalAnswer'
            #finance_link='https://vc.ru/u/423244-pavel-komarovskiy/entries'
            finance_data=requests.get(finance_link, cookies=cookies, headers=headers).text
            finance_news_url=(finance_data.split('Всё самое важное, что произошло')[0].split('<h2 class="story__title"><a href="')[-1].split('"')[0])
            finance_news_data=requests.get(finance_news_url, cookies=cookies, headers=headers).text
            finance_news_data = finance_news_data.split('<a href="/community/exchange" class="h4">Лига биржевой торговли')[0]
            m=bs4.BeautifulSoup(finance_news_data).get_text()
            m=m.split('\n\n\nЛига биржевой торговли\n\n\n')[1].replace('(Видеоверсия выпуска здесь.)','')
            title = m.split('Всё самое важное')[0].strip()
            text= m[len(title):].strip().replace('\n','<br>')
            if '[моё]' in text:
                text = text.split('[моё]')[0]
            spoiler_title=text.split('<br>')[0]
            text_komarovsky = make_spoiler(text,text=f'<br><b>Еженедельный дайджест от Комаровского - {spoiler_title}</b><br>')
        else:
            text_komarovsky=''
    except:
        try:
            finance_link='https://vc.ru/u/423244-pavel-komarovskiy'
            finance_data=requests.get(finance_link, cookies=cookies, headers=headers).text
            finance_news_url=(finance_data.split('Всё самое важное, что произошло')[0].split('href="')[-1].split('"')[0])
            finance_news_data=requests.get(finance_news_url, cookies=cookies, headers=headers).text
            finance_news_data = finance_news_data.split('<div class="content content--full ">')[-1]
            m=bs4.BeautifulSoup(finance_news_data).get_text()
            m=m.split('{"likeData"')[0]
            m=remove_nested_parens(m)
            m=m.replace('@media (min-width: ','').replace('px)','')
            spoiler_title = m.strip().split('\n')[0]
            m = m.replace('\n','<br>')
            text_komarovsky = make_spoiler(m,text=f'<br><b>Еженедельный дайджест от Комаровского - {spoiler_title}</b><br>') 
        except Exception as e: 
            text_komarovsky = f'ДАЙДЖЕСТ ОТ КОМАРОВСКОГО НЕ ПОЛУЧЕН {e}'
    text_spirin = last_telegram_messages_by_link('https://t.me/s/fintraining')
    text_spirin = make_spoiler(text_spirin, 'Что пишет Спирин')
    #text_spirin = f'<br><b>Последние посты Спирина</b><br>{text_spirin}'
    text = '<br>'.join(['Подать налоговую декларацию',text_spirin, text_komarovsky])
    return text

def get_ru_info():
    ru_link = 'https://t.me/s/mod_russia?q=%D0%A1%D0%B2%D0%BE%D0%B4%D0%BA%D0%B0+%D0%9C%D0%B8%D0%BD%D0%B8%D1%81%D1%82%D0%B5%D1%80%D1%81%D1%82%D0%B2%D0%B0+%D0%BE%D0%B1%D0%BE%D1%80%D0%BE%D0%BD%D1%8B+%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B9%D1%81%D0%BA%D0%BE%D0%B9+%D0%A4%D0%B5%D0%B4%D0%B5%D1%80%D0%B0%D1%86%D0%B8%D0%B8'
    dnr_link='https://t.me/s/TRO_DPR?q=%D0%94%D0%BD%D0%B5%D0%B2%D0%BD%D0%B0%D1%8F+%D1%81%D0%B2%D0%BE%D0%B4%D0%BA%D0%B0+%D0%A8%D1%82%D0%B0%D0%B1%D0%B0+%D1%82%D0%B5%D1%80%D1%80%D0%B8%D1%82%D0%BE%D1%80%D0%B8%D0%B0%D0%BB%D1%8C%D0%BD%D0%BE%D0%B9+%D0%BE%D0%B1%D0%BE%D1%80%D0%BE%D0%BD%D1%8B+%D0%94%D0%9D%D0%A0+%D0%BF%D1%80%D0%B8%D0%B7%D1%8B%D0%B2%D0%B0%D0%B5%D1%82+%D0%BD%D0%B0%D1%81%D0%B5%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5'
    lnr_link='https://t.me/s/millnr?q=%D0%BE%D1%84%D0%B8%D1%86%D0%B8%D0%B0%D0%BB%D1%8C%D0%BD%D0%BE%D0%B3%D0%BE+%D0%BF%D1%80%D0%B5%D0%B4%D1%81%D1%82%D0%B0%D0%B2%D0%B8%D1%82%D0%B5%D0%BB%D1%8F+%D0%9D%D0%9C+%D0%9B%D0%9D%D0%A0'
    ru_msg = last_telegram_message_by_link(ru_link, 'text').replace('\n','<br>')
    if USE_STATEMENTS:
        statement_list = ['[Конашенков] - это один человек, который отвечает за базар. Он один отвечает. Да, он дает цифры. Ну, сомневаешься, -  пожалуйста, можешь каким-то образом для себя сделать не тот вывод, который старается сделать осведомитель. Но это единственная инстанция, которая отвечает за свои слова и говорит: мы официально... Я, Игорь Евгеньевич Конашенков, заявляю официально: 5, 10, 15, 20. Все. А остальные у нас блогеры, включая меня.(c) А.В.Сладков',
                        ' С одной стороны, я, может быть, и скупо об этом говорю, но брифинги Министерства обороны проходят ежедневно, и они там докладывают нашей общественности, стране докладывают о том, что происходит, где происходит, каким образом и так далее.(c)В.В.Путин',
                        'Хочу напомнить вам слова президента о том, что главным и единственным, легитимным, полным источником информации о том, что происходит в ходе специальной военной операции, является Министерство обороны (c) Д.Ю.Песков']
        statements = '<br>'.join(['<i>'+k+'</i>' for k in statement_list])
    else:
        statements = ''
    msg = f'<br><h4> Официальная сводка</h4><br>{statements}<br> <br>{ru_msg} <br>'
    #dnr_msg = last_telegram_messages_by_link(dnr_link, 'text').replace('\n', '<br>')
    #lnr_msg = last_telegram_messages_by_link(lnr_link, 'text').replace('\n', '<br>')
    #msg=f'<br> {dnr_msg} <br><br> {lnr_msg} <br><br>'
    return msg


def get_ua_info():
    ua_operinfo_link = 'https://t.me/s/landforcesofukraine?q=%D0%9E%D0%BF%D0%B5%D1%80%D0%B0%D1%82%D0%B8%D0%B2%D0%BD%D0%B0+%D1%96%D0%BD%D1%84%D0%BE%D1%80%D0%BC%D0%B0%D1%86%D1%96%D1%8F+%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%BC'
    ua_text_data = last_telegram_message_by_link(ua_operinfo_link, 'text')
    ua_rulosses_link = 'https://t.me/s/landforcesofukraine?q=%D0%97%D0%B0%D0%B3%D0%B0%D0%BB%D1%8C%D0%BD%D1%96+%D0%B1%D0%BE%D0%B9%D0%BE%D0%B2%D1%96+%D0%B2%D1%82%D1%80%D0%B0%D1%82%D0%B8+%D0%BF%D1%80%D0%BE%D1%82%D0%B8%D0%B2%D0%BD%D0%B8%D0%BA%D0%B0'
    ua_rulosses_image_and_text = last_telegram_message_by_link(ua_rulosses_link,'text')
    msg = (ua_text_data + '\n'+ua_rulosses_image_and_text).replace('\n','<br>')
    if USE_STATEMENTS:
        statement_list = ['Водночас ми закликаємо громадян користуватися лише перевіреною інформацією із офіційних джерел та не поширювати чутки. (c) СБУ']
        statements = '<br>'.join(['<i>'+k+'</i>' for k in statement_list])
    else:
        statements = ''
    msg = f'<br><h4> Официальная сводка</h4> <br>{statements}<br> <br> {msg}'
    return msg
def get_mob_info():
    today = datetime.date.today()
    defended_until = datetime.date(2023, 8, 31)
    days_defended = (defended_until - today).days
    thr = 30
    if today < defended_until:
        answer = f'<h3> Сводки по мобилизации не показываются, так как бронь действует еще {days_defended} дней</h3>'
        if days_defended < thr:
            answer = f'{answer} <h3>Но бронь скоро закончится, поэтому важно в этом месяце уточнить иные варианты ее иметь</h3>'
        until_submit = (datetime.date(2023, 3, 10)-today).days
        asif_submit = (today - datetime.timedelta(days=until_submit)).strftime("%d.%m.%Y")
        until_submit2 = (datetime.date(2023, 3, 12)-today).days
        asif_submit2=(today - datetime.timedelta(days=until_submit2)).strftime("%d.%m.%Y")

        if until_submit:
            answer = f'{answer} <h2> До сабмита 1 {until_submit} дней. ОН ВАЖНЕЕ. </h2><br>'
            answer = f'{answer} <h3> Это как до {asif_submit}</h3><br>'
        if until_submit2:
            answer = f'{answer} <h2> До сабмита 2 {until_submit2} дней. </h2><br>'
            answer = f'{answer} <h3> Это как до {asif_submit2}</h3>'
        return answer
    else:
        url='https://rz62p2bo5j3vdtuwmcozqfg3bu0grvfc.lambda-url.us-east-1.on.aws/'
        m=requests.post('https://rz62p2bo5j3vdtuwmcozqfg3bu0grvfc.lambda-url.us-east-1.on.aws/https://notes.citeam.org/data/rss').text
        m=[k for k in feedparser.parse(m)['entries'] if 'мобилиз' in k.title.lower()]
        title='<h2>'+m[0]['title']+'(МОЖЕТ СОДЕРЖАТЬ ФЕЙКИ)</h2>'
        content = m[0]['content'][0]['value']
        content = bs4.BeautifulSoup(content,parser='lxml').get_text().replace('\n','<br>')
        content = 'НАСТОЯЩИЙ МАТЕРИАЛ (ИНФОРМАЦИЯ) ПРОИЗВЕДЕН, РАСПРОСТРАНЕН И (ИЛИ) НАПРАВЛЕН ИНОСТРАННЫМ АГЕНТОМ КАРПУК РУСЛАНОМ ЛЕОНИДОВИЧЕМ, ЛИБО КАСАЕТСЯ ДЕЯТЕЛЬНОСТИ ИНОСТРАННОГО АГЕНТА КАРПУК РУСЛАНА ЛЕОНИДОВИЧА<br>'+content
        answer = (title+'<br>'+content)
    return answer

def war_news():
    try:
        info_link='https://informburo.kz/syuzhety/chto-proishodit-v-ukraine'
        t = requests.get(info_link).text.split('"')
        links = [k for k in t if 'https://informburo.kz/novosti/' in k][:2]
        last_news=requests.get(links[0]).text.replace('Читайте также','В прошлом выпуске').replace('Читайте новости без рекламы','Этих новостей должно быть достаточно на данный момент')
        ind0 = last_news.index('<h3 class="article-excerpt">')
        ind1 = last_news.index('Скачайте мобильное приложение informburo.kz')
        last_news=last_news[ind0:ind1]
        if 'glavnoe' not in links[0]:
            prev_news=requests.get(links[1]).text.replace('Читайте также','В прошлом выпуске').replace('Читайте новости без рекламы','Этих новостей должно быть достаточно на данный момент')
            ind0 = prev_news.index('<h3 class="article-excerpt">')
            ind1 = prev_news.index('Скачайте мобильное приложение informburo.kz')
            last_news = last_news + '<br>'+prev_news[ind0:ind1]
        #ind0 = last_news.index('В прошлом выпуске')
        #ind1 = last_news[ind0:].index('<br>')+ind0
        #last_news = last_news[:ind0]+'<h4>'+last_news[ind0:ind1]+'</h4>'+last_news[ind1:]
        war_news = last_news# + previous_news
        war_news = '<html><body>'+war_news+'</body></html>'
        war_news = re.sub(r'<(a|/a).*?>', '', war_news)
        war_news = re.sub('http://\S+|https://\S+', '', war_news)
        total_news = war_news
        total_news = bs4.BeautifulSoup(total_news,'lxml').get_text().replace('\n','<br>')
    except Exception as e:
        total_news = f'ОШИБКА ЗАПРОСА. {e}<br> <br> Данные России<br><br> Данные Украины<br><br>'
    try:
        russia_paste_index=total_news.index('Данные России<br>')+len('Данные России<br>')
        try:
            ru_data = get_ru_info().replace('\n','<br>')
        except Exception as e:    
            ru_data =' Не удалось получить сводку Минобороны РФ. Ошибка запроса {e}'
        ru_data = make_spoiler(ru_data, 'Сводка Минобороны РФ')
        total_news=total_news[:russia_paste_index]+'<br><br>'+ru_data+'<br><br><h4>Официальные заявления</h4><br><br>'+total_news[russia_paste_index:]
    except Exception as e:
        print('Не удалось вставить данные Минобороны РФ. Ошибка запроса {e}')
    
    try:
        ukraine_paste_index=total_news.index('Данные Украины<br>')+len('Данные Украины<br>')
        try:
            ua_data = get_ua_info()
        except Exception as e:    
            ua_data =' Не удалось получить сводку Генштаба ВСУ. Ошибка запроса {e}'
        ua_data = make_spoiler(ua_data, 'Сводка Генштаба ВСУ')
        total_news=total_news[:ukraine_paste_index]+'<br><br>'+ua_data+'<br><br><h4>Официальные заявления</h4><br><br>'+total_news[ukraine_paste_index:]+'<br>'
    except Exception as e:
        print('Не удалось вставить данные Генштаба ВСУ. Ошибка запроса {e}')
    
    if 'Все новости о ситуации в Украине читайте здесь' in total_news:
        total_news=total_news[:total_news.index('Все новости о ситуации в Украине читайте здесь')]
    #try:
    #    total_news=total_news+ get_mob_info()
    #except Exception as e:    
    #    total_news=total_news+f' Не удалось получить сводку о мобилизации. Ошибка запроса {e}'
    total_news = total_news.replace('Данные России','<h2>Данные России</h2>')
    total_news = total_news.replace('Данные Украины','<h2>Данные Украины</h2>')
    total_news = total_news.replace('Реакция мирового сообщества','<h2>Реакция мирового сообщества</h2>')
    total_news = make_spoiler(total_news, 'Новости войны не рекомендуются для психики из-за эффекта дофаминовой петли. Разве они действительно сейчас тебе нужны?')
    return total_news

name_to_function = {#'Погода в Москве':weather,
                    'Статьи из Хабра':it_news,
                    'Научные статьи':articles,
                    #'Общий комментарий про новости':about_news,
                    'Патриотические новости':patrio_news,
                    'Новости законодательства':get_law_info,
                    'Финансовые новости': finance_news,
                    'Новости войны':war_news,
                    'Новости мобилизации':get_mob_info}
markup = make_multi_choice_markup([k.split('(')[0].strip() for k in name_to_function.keys()])

@bot.message_handler(content_types='text')
def message_reply(message):
    try:
        global markup, key_value_pair, one_line
        if message.text in markup:
            info = name_to_function[message.text]()
            info = bs4.BeautifulSoup(info,'lxml').get_text()
            send_in_chunks(message.chat.id, info, markup)
        else:
            send_in_chunks(message.chat.id, 'test', markup)
    except Exception as e:
        print(e)
        raise e

def handler(event, context):
    print(event)
    t0 = time.time()
    answer=''
    global name_to_function
    if is_telegram_event(event):
        message = telebot.types.Update.de_json(event['body'])
        bot.process_new_updates([message])
        return {
        'statusCode': 200,
        'body': '!'
        }
    for name in list(name_to_function):
        try:
            t=time.time()
            function_output = name_to_function[name]()
            if name in ['Новости войны', 'Новости мобилизации']:
                name = name+'(ЭТОТ РАЗДЕЛ МОЖЕТ СОДЕРЖАТЬ ФЕЙКИ)'
            answer = f'{answer}<br><br><h1>{name}</h1><br><br>'
            answer=f'{answer}{function_output}<br> Сгенерировано за {time.time()-t}'
        except Exception as e:
            answer=f'{answer} НЕ ПОЛУЧЕНО: {e}'
    for i in range(6,1,-1):
        answer=answer.replace('<br>'*i,'<br>'*1)
        answer=answer.replace('<br> '*i,'<br>'*1)
    answer = f'{answer} <br> Сайт сгенерирован автоматически за {time.time()-t0}.<br> Автор сайта не проверял вручную результат генерации и не гарантирует его правдивость.'
    return {
        'statusCode': 200,
        'body': answer,
    }
if __name__ == '__main__':
    bot.infinity_polling()

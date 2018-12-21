import json
import os
import re
import urllib.request
import urllib.parse

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = 'xoxb-504131970294-508903683254-cBPHp9saSZJt2Kye9nuJFtqn'
slack_client_id = "504131970294.508901190678"
slack_client_secret = "9642b14b9f5c76e458a61c90e14dce96"
slack_verification = "jFr9zX0YBztPUU34uCCufyjV"
sc = SlackClient(slack_token)


# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    t = text.split(' ')[1]
    url = 'https://search.naver.com/search.naver?where=video&sm=tab_jum&query=' + urllib.parse.quote_plus(t)
    print(url)
    # if t == '축구':
    # print('url:' + url)
    req = urllib.request.Request(url)

    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    # if l == 'EPL':
    #     start = 0
    #     end = 10
    # elif l == '분데스리가':
    #     start = 10
    #     end = 20
    # elif l == '라리가':
    #     start = 20
    #     end = 30
    # else:
    #     start = 30
    #     end = 40
    keywords = []
    keywords1 = []
    # for keyword in soup.find_all('td'):
    #     for j, word in enumerate(keyword.find_all('div', class_='info')):
    #         if j < 9:
    #             keywords1.append(word.get_text().strip())

    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    # print(keywords1)

    for keyword in soup.find_all('ul', class_='video_lst_vertical _video_lst'):
        for word in keyword('li'):
            keywords.append(word.find('a')['href'])

    for keyword in soup.find_all('dt', class_='info_title tit'):
        keywords1.append(keyword.get_text())

    for i in range(len(keywords)):
        keywords[i] = keywords1[i] +" :"+" "+ keywords[i]
        # for word in keyword.find('a'):
        #     keywords.append(word.attrs['src'])
    # eee = soup.find_all('img')

    # for m in eee:
    #     keywords.append(m.get('src'))
            # if j < 3:
                # keywords.append(word.find('a')['href'])
    #한글 지원을 위해 앞에 unicode u를 붙혀준다.
    print(keywords)

    return u'\n'.join(keywords)


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_naver_keywords(text)
        #keywords = 'asdfasdf'
        print(keywords)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )
        print('sad : ' + keywords)
        return make_response("App mention message has been sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)

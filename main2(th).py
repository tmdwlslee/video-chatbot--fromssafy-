# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request
import time
import urllib.parse

# 쓰레드, 큐를 위한 라이브러리 추가
import multiprocessing as mp
from threading import Thread

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = 'xoxb-504131970294-508903683254-cBPHp9saSZJt2Kye9nuJFtqn'
slack_client_id = "504131970294.508901190678"
slack_client_secret = "9642b14b9f5c76e458a61c90e14dce96"
slack_verification = "jFr9zX0YBztPUU34uCCufyjV"
sc = SlackClient(slack_token)

# threading function
def processing_event(queue):
    while True:
        # 큐가 비어있지 않은 경우 로직 실행
        if not queue.empty():
            slack_event = queue.get()

            # Your Processing Code Block gose to here
            channel = slack_event["event"]["channel"]
            text = slack_event["event"]["text"]

            # 챗봇 크롤링 프로세스 로직 함수
            keywords = processing_function(text)

            # 아래에 슬랙 클라이언트 api를 호출하세요
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                text=keywords
            )


# 크롤링 함수
def processing_function(text):
    # 함수를 구현해 주세요
    # keywords = "성공!!~"

    # delay test...
    # TODO: 아래  time.sleep(5) 를 지워주세요! 테스트용 코드입니다.
    time.sleep(3)
    t = text.split(' ')[1]

    url = 'https://search.naver.com/search.naver?where=video&sm=tab_jum&query=' + urllib.parse.quote_plus(t)

    req = urllib.request.Request(url)
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    keywords = []
    keywords1 = []

    for keyword in soup.find_all('ul', class_='video_lst_vertical _video_lst'):
        for word in keyword('li'):
            keywords.append(word.find('a')['href'])

    for keyword in soup.find_all('dt', class_='info_title tit'):
        keywords1.append(keyword.get_text())

    for i in range(len(keywords)):
        keywords[i] = keywords1[i] + " :" + " " + keywords[i]
    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    print(keywords)

    return u'\n'.join(keywords)


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):

    if event_type == "app_mention":
        event_queue.put(slack_event)
        return make_response("App mention message has been sent", 200, )


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
    event_queue = mp.Queue()

    p = Thread(target=processing_event, args=(event_queue,))
    p.start()
    print("subprocess started")

    app.run('0.0.0.0', port=8080)
    p.join()
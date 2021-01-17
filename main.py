from flask import Flask, request, abort, jsonify

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ButtonsTemplate, TemplateSendMessage, MessageTemplateAction,
    ImageComponent, BoxComponent, SeparatorComponent, TextComponent, URIAction,
    FlexSendMessage, BubbleContainer,
    QuickReply, QuickReplyButton, MessageAction,
    CarouselTemplate, CarouselColumn
)
from linebot.models.flex_message import TextComponent as TextComponent2
from linebot.models.flex_message import SpanComponent, ButtonComponent

from utils import get_events, get_news
import re
from datetime import datetime, timedelta

app = Flask(__name__)
app.url_map.strict_slashes = False

line_bot_api = LineBotApi(
    'Channel access token')
handler = WebhookHandler('Channel secret')


def news_template_flex(news_list, events, key, id, isMore, alt_text='推薦新聞'):
    """ Display news data UI with FlexSendMessage.
    Parameters
    ----------
    news_list : list

    Returns
    -------
    res: FlexSendMessage
    """
    news_box_components = []
    for i, news in enumerate(news_list):
        # img = "https://cdn.pixabay.com/photo/2015/12/03/22/16/newspaper-1075795_1280.jpg"
        date = news['date']
        date = re.sub("T.*Z", "", date)
        url = news['url']

        # Add separators between news.
        if i > 0:
            news_box_components.append(SeparatorComponent(margin='lg'))
        # related_news_uri = f"{RELATED_NEWS_LIFF_URI}?cid={news['cid']}&nid={news['nid']}"

        TextComponents = []
        TextComponents.append(TextComponent(
            text=news['title'],
            wrap=True,
            size='md',
            weight='bold',
            action=URIAction(uri=url)
        ))
        TextComponents.append(TextComponent(
            text='{} - {}'.format(news['source'], date),
            wrap=True,
            size='xxs',
            color='#6c757d'
        ))
        words = []
        event_v, event_o = events.split()
        regex = "({}|{})".format(event_v, event_o)
        tokenized_sentence = re.split(regex, news['sentences'][1])
        tokenized_sentence = [t for t in tokenized_sentence if t != ""]
        tokenized_sentence = [news['sentences'][0] + " "] + tokenized_sentence + [" " + news['sentences'][2]]
        for i in tokenized_sentence:
            if i == event_v or i == event_o:
                words.append(SpanComponent(
                    text=i,
                    color="#e86d48"
                ))
            else:
                words.append(SpanComponent(
                    text=i,
                ))
        new_text_componet = TextComponent2(type="text", text="hello, world", contents=words, wrap=True)
        TextComponents.append(new_text_componet)
        TextComponents.append(BoxComponent(
            layout='horizontal',
            spacing='md',
            contents=[
                TextComponent(
                    text='查看這則新聞',
                    size='md',
                    color='#6E7DAB',
                    flex=1,
                    action=URIAction(uri=url),
                ),
            ]
        ))

        news_box_components.append(
            BoxComponent(
                layout='horizontal',
                spacing='md',
                contents=[
                    BoxComponent(
                        layout='vertical',
                        flex=2,
                        spacing='sm',
                        contents=TextComponents
                    )
                ]
            )
        )
    if isMore:
        news_box_components.append(
            ButtonComponent(style="link",
                            # margin="xs",
                            action=MessageTemplateAction(
                                label="more",
                                text="more:" + str(id) + ":" + key + ":" + events
                            )))

    bubble = BubbleContainer(
        body=BoxComponent(
            layout='vertical',
            spacing='lg',
            contents=news_box_components
        )
    )
    return FlexSendMessage(alt_text=alt_text, contents=bubble)


@app.route('/', methods=['HEAD'])
def head_route():
    return ('', 204)


@app.route('/', methods=['GET'])
def root_route():
    return 'OK'


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


def get_template(input_text):
    endDate = datetime.today().strftime('%Y-%m-%d')
    startDate = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    if input_text == "[reset]":
        return TextSendMessage(
            text='你可以輸入任何人名，例如：蔡英文，我就會統計出他/她最近最常發生的事件種類， 並提供進一步查詢。',
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(label="蔡英文", text="蔡英文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="韓國瑜", text="韓國瑜")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="郭台銘", text="郭台銘")
                    )]
            ))

    elif ":" not in input_text:
        events = get_events(input_text, startDate, endDate)
        if len(events) == 0:
            return TextSendMessage(
                text='沒有這個人，或他/她的新聞數太少ＱＡＱ')
        elif len(events) <= 9:
            all_columns = []
            all_actions = []
            for i in range(len(events)):
                all_actions.append(MessageTemplateAction(
                    label="...".join(events[i]['term'].split()) + " (" + str(events[i]["freq"]) + ")",
                    text=input_text + ":" + events[i]['term']
                ))
                if (i + 1) % 3 == 0:
                    all_columns.append(CarouselColumn(
                        title='{}相關新聞事件'.format(input_text),
                        text='點選可獲得相關新聞',
                        actions=all_actions
                    ))
                    all_actions = []
        else:
            events = events[:8]
            all_columns = []
            all_actions = []
            for i in range(9):
                if i == 8:
                    all_actions.append(MessageTemplateAction(
                        label="more",
                        text="更多事件" + ":" + str(8) + ":" + input_text
                    ))
                else:
                    all_actions.append(MessageTemplateAction(
                        label="...".join(events[i]['term'].split()) + " (" + str(events[i]["freq"]) + ")",
                        text=input_text + ":" + events[i]['term']
                    ))

                if (i + 1) % 3 == 0:
                    all_columns.append(CarouselColumn(
                        title='{}相關新聞事件'.format(input_text),
                        text='點選可獲得相關新聞',
                        actions=all_actions
                    ))
                    all_actions = []

        buttons_template = TemplateSendMessage(
            alt_text='Carousel template',
            template=CarouselTemplate(
                columns=all_columns
            )
        )
        return buttons_template

    elif "更多事件" in input_text:
        _, id_event, input_text = input_text.split(":")
        id_event = int(id_event)
        events = get_events(input_text, startDate, endDate)
        action_lst = []
        for i in range(3):
            action_lst.append(MessageTemplateAction(
                label="...".join(events[id_event + i]['term'].split()) + " (" + str(events[id_event]["freq"]) + ")",
                text=input_text + ":" + events[id_event + i]['term']
            ))
        if len(events[id_event + 3:]) > 3:
            action_lst.append(MessageTemplateAction(
                label="more",
                text="更多事件" + ":" + str(id_event + 3) + ":" + input_text
            ))
        buttons_template = TemplateSendMessage(
            alt_text='Buttons Template',
            template=ButtonsTemplate(
                title='{}相關新聞事件'.format(input_text),
                text='點選可獲得相關新聞',
                actions=action_lst
            )
        )
        return buttons_template

    elif "more" in input_text:
        _, id, key, events = input_text.split(":")
        id = int(id)
        news = get_news(key, events, startDate, endDate)
        news_lst = news["data"][id:id + 3]
        id = id + 3
        isMore = len(news["data"][id:]) != 0
        flex_template = news_template_flex(news_lst, events, key, id, isMore)
        return flex_template
    else:
        key, events = input_text.split(":")
        news = get_news(key, events, startDate, endDate)
        news_lst = news["data"][:3]
        id = 3
        isMore = len(news["data"]) > 3
        flex_template = news_template_flex(news_lst, events, key, id, isMore)
        return flex_template


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    input_text = event.message.text
    template = get_template(input_text)
    line_bot_api.reply_message(event.reply_token, template)


@app.route("/internal", methods=['POST'])
def internal_route():
    try:
        user_id = request.json['user_id']
        input_text = request.json['text']
    except:
        raise ValueError('Invalid JSON!')

    template = get_template(input_text)
    ret = template.as_json_dict()
    return jsonify([ret])


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=15002)

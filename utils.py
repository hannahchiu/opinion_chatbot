import requests


def get_events(keyword, startDate, endDate):
    """return: list of dic"""
    query = 'https://ckip.iis.sinica.edu.tw/api/opinion/api/theme?' \
            'startDate={}&endDate={}&' \
            'keyword={}&type=noun&termType=events'.format(startDate, endDate, keyword)
    response = requests.get(query)
    events = response.json()
    return events


def get_news(keyword, event, startDate, endDate):
    query = "https://ckip.iis.sinica.edu.tw/api/opinion/api/tid?" \
            "keyword={}&" \
            "termType=events&term={}&" \
            "startDate={}&endDate={}".format(
        keyword, event, startDate, endDate)
    response = requests.get(query)
    news = response.json()
    return news


if __name__ == '__main__':
    keyword = "柯文哲"
    startDate = "2019-10-09"
    endDate = "2019-11-08"
    events = get_events(keyword, startDate, endDate)
    event = events[0]['term']
    news = get_news(keyword, event, startDate, endDate)

import argparse
import json
import requests
import math

WAKA_API_URL = 'https://wakatime.com/api/v1'
GIST_API_URL = 'https://api.github.com/gists'

NAME_LEN = 10
TIME_LEN = 14
BAR_LEN = 21
PERCENT_LEN = 5


def waka_api_get(url, api_key):
    url = WAKA_API_URL + url
    r = requests.get(url, params={'api_key': api_key})

    return json.loads(r.text)


def get_gist(gist_id, github_token):
    url = f'{GIST_API_URL}/{gist_id}'
    r = requests.get(url, headers={'Authorization': f'token {github_token}'})

    return json.loads(r.text)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Create a Gist box for WakaTime statistics.')
    parser.add_argument('-w',
                        '--waka-api-key',
                        required=True,
                        type=str,
                        help='WakaTime API key')
    parser.add_argument('-g',
                        '--gist-id',
                        required=True,
                        type=str,
                        help='Gist ID')
    parser.add_argument('-t',
                        '--github-token',
                        required=True,
                        type=str,
                        help='GitHub Token')

    return parser.parse_args()


def get_content(stats):
    langs = stats['languages'][:5]
    names = [x['name'] for x in langs]
    names = [
        x.ljust(NAME_LEN) if len(x) < NAME_LEN else x[:NAME_LEN - 1] + '.'
        for x in names
    ]

    texts = [x['text'] for x in langs]
    times = [x.ljust(TIME_LEN) for x in texts]

    percentages = [x['percent'] for x in langs]
    bars = [get_progress_bar(x, BAR_LEN) for x in percentages]
    percentages = [f'{x:.1f}'.rjust(PERCENT_LEN) + '%' for x in percentages]

    return '\n'.join(
        [n + t + b + p for n, t, b, p in zip(names, times, bars, percentages)])


def get_progress_bar(percentage, length):
    bar_length = length - 2
    bar = '#' * int(round(bar_length * percentage / 100.0))
    bar = bar.ljust(bar_length, '.')
    bar = f'[{bar}]'
    return bar


def update_gist(gist_id, github_token, content):
    gist = get_gist(gist_id, github_token)
    filename = list(gist['files'].values())[0]['filename']
    update = dict(description='', files={filename: {'content': content}})

    url = f'{GIST_API_URL}/{gist_id}'
    requests.patch(url,
                   data=json.dumps(update),
                   headers={'Authorization': f'token {github_token}'})


if __name__ == '__main__':
    args = parse_args()
    api_key = args.waka_api_key
    gist_id = args.gist_id
    github_token = args.github_token

    stats = waka_api_get('/users/current/stats/last_7_days', api_key)['data']
    content = get_content(stats)
    update_gist(gist_id, github_token, content)

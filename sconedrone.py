#!/usr/bin/env python3

import os
import datetime

import requests
from bs4 import BeautifulSoup
import boto3


URL = 'http://www.carmascafe.com/'


def mocha_chip_filter(tag):
    return tag.name == 'span' and \
        'mocha chip' in ' '.join(tag.text.strip().split())


def post_has_mocha_chip(post):
    return post.find(mocha_chip_filter) is not None


def month_day_today():
    return datetime.date.today().strftime('%B %-d')


def post_is_today(post):
    title = post.find('h3', class_='entry-title').text.strip()
    return month_day_today() in title


def has_mocha_chip_today():
    html = requests.get(URL).text
    soup = BeautifulSoup(html, 'html.parser')
    posts = soup.find_all('div', class_='post')
    return post_is_today(posts[0]) and post_has_mocha_chip(posts[0])


def read_last_good_month_day(path):
    if os.path.exists(path):
        with open(path) as f:
            last_line = None
            for line in f:
                last_line = line.strip()
            return last_line
    else:
        return None


def write_good_month_day(path):
    with open(path, 'a') as f:
        f.write(month_day_today() + '\n')


def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description='Read the latest post from the Carma\'s Cafe website, '
                    'check if mocha chip scones look like they\'re on the '
                    'menu, and send an AWS SNS message if they are (and if we '
                    'haven\'t already sent one today).',
    )
    parser.add_argument('topic_arn', type=str,
                        help='ARN of AWS SNS topic to publish message to')
    parser.add_argument('--message', type=str, default='mocha chip!',
                        help='Message to send if it looks like they have '
                             'mocha chip scones')
    parser.add_argument('--profile-name', type=str,
                        help='AWS credential profile to use')
    parser.add_argument('--log-path', type=str, default='sconedrone.log',
                        help='Path to file that tracks whether we\'ve already '
                             'sent a notification today')
    args = parser.parse_args()

    last_good_month_day = read_last_good_month_day(args.log_path)
    if last_good_month_day != month_day_today() and has_mocha_chip_today():
        session = boto3.Session(profile_name=args.profile_name)
        client = session.client('sns')
        client.publish(TopicArn=args.topic_arn,
                       Message='{}: {}'.format(month_day_today(),
                                               args.message))
        write_good_month_day(args.log_path)


if __name__ == '__main__':
    main()

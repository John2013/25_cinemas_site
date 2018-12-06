import re
from operator import itemgetter
from os.path import abspath
from urllib.parse import quote
import grequests
import gevent.monkey
import requests
from werkzeug.contrib.cache import FileSystemCache

from bs4 import BeautifulSoup


def fetch_afisha_page():
    gevent.monkey.patch_all()
    return requests.get(
        'https://www.afisha.ru/cherepovec/schedule_cinema/'
    ).content


def parse_afisha_list(raw_html):
    soup = BeautifulSoup(raw_html, features="html.parser")
    names_tags = soup.findAll('h3', class_='card__title')
    return list(
        map(
            lambda tag: tag.string.strip().strip('«»'),
            names_tags
        )
    )


def make_get_url(url, params):
    if len(params) > 0:
        text_params_list = []
        for param, value in params.items():
            text_params_list.append("{}={}".format(quote(param), quote(value)))

        params_text = "&".join(text_params_list)
        return "{}?{}".format(url, params_text)
    return url


def fetch_movie_info_multiple(movie_titles):
    urls = []
    for title in movie_titles:
        urls.append(
            make_get_url(
                'https://www.kinopoisk.ru/index.php',
                {
                    'kp_query': title
                }
            )
        )
    rs = (grequests.get(u) for u in urls)

    raw_htmls_list = list(map(
        lambda result: result.content,
        grequests.map(rs)
    ))

    return zip(movie_titles, raw_htmls_list)


def parse_movie_info_multiple(titles_htmls_tuples_list):
    movies = []
    for title, raw_html in titles_htmls_tuples_list:
        soup = BeautifulSoup(raw_html, features="html.parser")
        rating_tag = soup.select_one('div.element.most_wanted div.rating')
        none_int = 0
        if rating_tag is None:
            rating_tag = soup.select_one('span.rating_ball')
            count_tag = soup.select_one('span.ratingCount')
            rating = float(rating_tag.string) if rating_tag else none_int
            votes_cnt = int(count_tag.string) if count_tag else none_int
            movies.append(
                {"title": title, "rating": rating, "votes_cnt": votes_cnt}
            )
            continue

        rating, votes_cnt = rating_tag['title'].split(' ')
        rating = float(rating)
        votes_cnt = int(re.sub(r'[()\u00a0]', '', votes_cnt))
        movies.append(
            {"title": title, "rating": rating, "votes_cnt": votes_cnt}
        )
    return movies


def output_movies_to_console(movies):
    movies = sorted(movies, key=itemgetter('rating'), reverse=True)[:10]
    for movie in movies:
        print('{title:<50} | {rating} ({votes_cnt})'.format(
            title=movie['title'][:50],
            rating=movie['rating'],
            votes_cnt=movie['votes_cnt']
        ))


def cache_get_or_set(name, function, timeout=86400):
    cache = FileSystemCache(cache_dir=abspath('tmp'))
    result = cache.get(name)
    if result is None:
        result = function()
        cache.set(name, result, timeout=timeout)
    return result


def get_top_10():
    afisha_html = fetch_afisha_page()
    movie_titles = parse_afisha_list(afisha_html)
    movie_titles_htmls = fetch_movie_info_multiple(movie_titles)
    return parse_movie_info_multiple(movie_titles_htmls)


def cached_top_10():
    return cache_get_or_set('top10', get_top_10)


if __name__ == '__main__':
    movies = cached_top_10()
    output_movies_to_console(movies)
    movies = cached_top_10()
    output_movies_to_console(movies)
    movies = cached_top_10()
    output_movies_to_console(movies)

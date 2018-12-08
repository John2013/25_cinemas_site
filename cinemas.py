import re
from operator import itemgetter
from os.path import abspath
from urllib.parse import urlencode
import grequests
import gevent.monkey
import requests
from werkzeug.contrib.cache import FileSystemCache

from bs4 import BeautifulSoup

gevent.monkey.patch_all()


def fetch_afisha_page():
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


def make_get_url(url, params=None):
    if params:
        return "{}?{}".format(url, urlencode(params))
    return url


def fetch_movie_info_multiple(movie_titles):
    urls = []
    for title in movie_titles:
        urls.append(make_get_url(
            'https://www.kinopoisk.ru/index.php', {'kp_query': title}
        ))
    rs = (grequests.get(u) for u in urls)

    raw_htmls_list = list(map(
        lambda result: result.content,
        grequests.map(rs)
    ))

    return zip(movie_titles, raw_htmls_list)


def get_poster_by_id(movie_id):
    return "https://www.kinopoisk.ru/images/sm_film/{}.jpg".format(movie_id)


def get_url_by_id(movie_id):
    return "https://www.kinopoisk.ru/film/{}/".format(movie_id)


def parse_movie_from_self_page(soup, title):
    none_int = 0
    rating_tag = soup.select_one('span.rating_ball')
    count_tag = soup.select_one('span.ratingCount')

    rating = float(rating_tag.string) if rating_tag else none_int
    votes_cnt = int(count_tag.string) if count_tag else none_int

    return {
        "title": title,
        "rating": rating,
        "votes_cnt": votes_cnt,
        "poster": '',
        "url": ''
    }


def parse_movie_info_multiple(titles_htmls_tuples_list):
    movies = []
    for title, raw_html in titles_htmls_tuples_list:
        soup = BeautifulSoup(raw_html, features="html.parser")
        element_tag = soup.select_one('div.element.most_wanted')
        rating_tag = element_tag.select_one('div.rating')
        if rating_tag is None:
            movie = parse_movie_from_self_page(soup, title)
            movies.append(movie)
            continue

        title_tag = element_tag.select_one('a.js-serp-metrika')
        movie_id = title_tag['data-id']
        rating, votes_cnt = rating_tag['title'].split(' ')
        rating = float(rating)
        votes_cnt = int(re.sub(r'[()\u00a0]', '', votes_cnt))

        poster_url = get_poster_by_id(movie_id)
        movie_url = get_url_by_id(movie_id)
        movies.append(
            {
                "title": title,
                "rating": rating,
                "votes_cnt": votes_cnt,
                "poster": poster_url,
                "url": movie_url
            }
        )
    return movies


def sort_movies(movies, by='rating'):
    return sorted(movies, key=itemgetter(by), reverse=True)


def output_movies_to_console(movies):
    movies = sort_movies(movies, 'rating')[:10]
    for movie in movies:
        print('{title:<50} | {rating} ({votes_cnt})'.format(
            title=movie['title'][:50],
            rating=movie['rating'],
            votes_cnt=movie['votes_cnt']
        ))


def cache_get_or_set(cache_name, function, timeout=3600):
    cache = FileSystemCache(cache_dir=abspath('tmp'))
    cache_data = cache.get(cache_name)
    if cache_data is None:
        cache_data = function()
        cache.set(cache_name, cache_data, timeout=timeout)
    return cache_data


def get_top_10():
    afisha_html = fetch_afisha_page()
    movie_titles = parse_afisha_list(afisha_html)
    movie_titles_htmls = fetch_movie_info_multiple(movie_titles)
    movies = parse_movie_info_multiple(movie_titles_htmls)
    return sort_movies(movies)[:10]


def cached_top_10(timeout=3600):
    return cache_get_or_set('top10', get_top_10, timeout)


if __name__ == '__main__':
    movies = cached_top_10()
    output_movies_to_console(movies)

from asyncio import gather
from datetime import datetime
from random import choice, uniform
from typing import Optional

from httpx import AsyncClient, ReadTimeout, RequestError, post


class RecommendationService:
    def __init__(self):
        self.known_manga_recs = {}
        self.known_anime_recs = {}

    async def query_user_statistics(
        self, anilist_username: str, media_type: str
    ) -> Optional[dict]:
        query = f"""
        query User($name: String) {{
          User(name: $name) {{
            statistics {{
              {media_type.lower()} {{
                count
                meanScore
                standardDeviation
                genres {{
                  count
                  genre
                  meanScore
                }}
              }}
            }}
          }}
        }}
        """
        variables = {
            'name': anilist_username,
        }

        try:
            response = post(
                url='https://graphql.anilist.co',
                json={'query': query, 'variables': variables},
            )
        except ReadTimeout:
            return None
        if response.status_code != 200:
            return None
        if not response.json()['data']['User']['statistics'][media_type]['count']:
            return None
        user_statistics = response.json()['data']['User']['statistics'][media_type]

        return user_statistics

    async def query_media_recs(
        self, anilist_username: str, media_type: str, watched_count: int
    ):
        query = """
        query MediaListCollection($userName: String, $type: MediaType, $statusNotIn: [MediaListStatus], $sort: [RecommendationSort], $perPage: Int, $perChunk: Int, $chunk: Int) {
          MediaListCollection(userName: $userName, type: $type, status_not_in: $statusNotIn, perChunk: $perChunk, chunk: $chunk) {
            lists {
              entries {
                score
                media {
                  id
                  popularity
                  recommendations(sort: $sort, perPage: $perPage) {
                    nodes {
                      rating
                      mediaRecommendation {
                        id
                        genres
                        meanScore
                        popularity
                        relations {
                          edges {
                            relationType
                          }
                          nodes {
                            id
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        chunk_size = 100

        async def query_list_recommendations(session: AsyncClient, chunk):
            req_vars = {
                'userName': anilist_username,
                'type': media_type.upper(),
                'statusNotIn': 'PLANNING',
                'perPage': 8,
                'sort': 'RATING_DESC',
                'perChunk': chunk_size,
                'chunk': chunk,
            }
            data = await session.post(
                url='https://graphql.anilist.co',
                json={'query': query, 'variables': req_vars},
                timeout=10,
            )
            return data

        tasks: list = []

        async with AsyncClient() as client:
            for i in range(1, watched_count // chunk_size + 2):
                tasks.append(query_list_recommendations(client, i))

            raw_list_data = await gather(*tasks)

        full_rec_list: list = []
        for data_chunk in raw_list_data:
            if data_chunk.status_code != 200:
                continue
            data_chunk = data_chunk.json()['data']['MediaListCollection']['lists']
            for anime_list in data_chunk:
                anime_list = anime_list['entries']
                full_rec_list += anime_list

        return full_rec_list

    async def fetch_recommendations(
        self, anilist_username: str, media_type: str, requested_genre
    ) -> None:
        user_stats = await self.query_user_statistics(
            anilist_username=anilist_username, media_type=media_type
        )
        list_data = await self.query_media_recs(
            anilist_username=anilist_username,
            media_type=media_type,
            watched_count=user_stats['count'],
        )
        if not list_data or not user_stats:
            raise RequestError('Error obtaining data from anilist.')

        # Obtain max user score, collect watched show info
        max_score = 0
        max_popularity = 0
        seen_show_ids = []
        for entry in list_data:
            seen_show_ids.append(entry['media']['id'])
            if entry['score'] > max_score:
                max_score = entry['score']
            if entry['media']['popularity'] > max_popularity:
                max_popularity = entry['media']['popularity']

        # Get user genre scores
        user_genre_scores = {}
        if not requested_genre:
            for genre in user_stats['genres']:
                genre_name = genre['genre']
                if not genre['meanScore']:
                    user_genre_scores[genre_name] = 0
                user_genre_scores[genre_name] = (
                    genre['meanScore'] - user_stats['meanScore']
                ) / 100

        recommendation_scores = {}

        for entry in list_data:
            if not entry['media']['recommendations']['nodes']:
                continue

            # Weight each show's recommendation by strength of recommendation on the site
            print('test1')
            max_recs = max(8, len(entry['media']['recommendations']['nodes']))
            print('test2')
            max_rec_rating = entry['media']['recommendations']['nodes'][0]['rating']
            if max_rec_rating == 0:
                continue

            for show_rec in entry['media']['recommendations']['nodes'][0:max_recs]:
                # Filter out bad data from anilist
                if show_rec['mediaRecommendation'] is None:
                    continue
                if show_rec['mediaRecommendation']['id'] in seen_show_ids:
                    continue
                if not show_rec['mediaRecommendation']['meanScore']:
                    show_rec['mediaRecommendation']['meanScore'] = 65
                if requested_genre and not any(
                    genre.lower() == requested_genre
                    for genre in show_rec['mediaRecommendation']['genres']
                ):
                    continue

                try:
                    if any(
                        related_show[0]['relationType'] == 'PREQUEL'
                        and related_show[1]['id'] not in seen_show_ids
                        for related_show in zip(
                            show_rec['mediaRecommendation']['relations']['edges'],
                            show_rec['mediaRecommendation']['relations']['nodes'],
                        )
                    ):
                        continue
                except KeyError:
                    pass

                # Scoring
                node_score_weight = 0 if entry['score'] == 0 else 1
                node_score = node_score_weight * (
                    entry['score'] / max_score - user_stats['meanScore'] / 100
                )
                rec_show_score_weight = 1
                rec_show_score = (
                    rec_show_score_weight
                    * (show_rec['mediaRecommendation']['meanScore'] - 65)
                    / 100
                )
                rec_pop_factor = (
                    1 - show_rec['mediaRecommendation']['popularity'] / max_popularity
                )
                rec_pop_factor = rec_pop_factor**1.5 if rec_pop_factor > 0 else 0.1
                rec_genre_score_weight = 0.75
                rec_genre_score = 0
                if not requested_genre:
                    for genre in show_rec['mediaRecommendation']['genres']:
                        try:
                            rec_genre_score += user_genre_scores[genre]
                        except KeyError:
                            continue
                    rec_genre_score *= rec_genre_score_weight

                rec_total_weight = show_rec['rating'] / max_rec_rating
                if show_rec['mediaRecommendation']['id'] not in recommendation_scores:
                    recommendation_scores[show_rec['mediaRecommendation']['id']] = (
                        (node_score + rec_show_score + rec_genre_score)
                        * rec_total_weight
                        * rec_pop_factor
                    )
                else:
                    recommendation_scores[show_rec['mediaRecommendation']['id']] += (
                        (node_score + rec_show_score + rec_genre_score)
                        * rec_total_weight
                        * rec_pop_factor
                    )

        # Sort recommendations by score then take the top 20, add random variation of +-20%
        recommendation_scores = dict(
            sorted(
                recommendation_scores.items(), key=lambda item: item[1], reverse=True
            )
        )
        recommendation_scores = {
            k: v * uniform(0.8, 1.2)
            for i, (k, v) in enumerate(recommendation_scores.items())
            if i < 20 and v >= 0
        }

        # Normalize scores and apply filter for logical percentages
        max_recommendation_score = max(recommendation_scores.values())
        print('test4')
        recommendation_scores = {
            k: (v / max_recommendation_score) ** 0.35 * 100
            for k, v in recommendation_scores.items()
        }

        if media_type.lower() == 'manga':
            self.known_manga_recs[f'{anilist_username}{requested_genre}'] = {
                'date': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                'recs': recommendation_scores,
            }
        else:
            self.known_anime_recs[f'{anilist_username}{requested_genre}'] = {
                'date': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                'recs': recommendation_scores,
            }

        return None

    async def get_recommendation(
        self,
        anilist_username: str,
        requested_genre: str,
        media_type: str,
        force_update: bool = False,
    ) -> str:
        known_recs = (
            self.known_manga_recs if media_type == 'manga' else self.known_anime_recs
        )
        requested_recs = f'{anilist_username}{requested_genre}'
        if requested_recs not in known_recs or force_update:
            try:
                await self.fetch_recommendations(
                    anilist_username=anilist_username,
                    media_type=media_type,
                    requested_genre=requested_genre,
                )
            except RequestError:
                return 'Error fetching recommendations. Please try again later.'
        time_delta = (
            datetime.now()
            - datetime.strptime(known_recs[requested_recs]['date'], '%Y/%m/%d %H:%M:%S')
        ).total_seconds()
        if time_delta > 345600:
            await self.fetch_recommendations(
                anilist_username=anilist_username,
                media_type=media_type,
                requested_genre=requested_genre,
            )

        recs = known_recs[requested_recs]['recs']

        rec_id = choice(tuple(recs.keys()))
        final_rec = f'https://anilist.co/{media_type}/{rec_id}/\nRecommendation Score: {recs[rec_id]:.1f}%'

        return final_rec

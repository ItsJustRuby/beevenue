from queue import PriorityQueue
from typing import FrozenSet, List, Set

from sentry_sdk import start_span
from beevenue.flask import g

from beevenue.flask import BeevenueContext

from ..document_types import TinyMediumDocument


def _find_candidates(
    context: BeevenueContext, medium_id: int, target_tag_names: FrozenSet[str]
) -> Set[TinyMediumDocument]:
    """Find all media that have *some* similarity to the specified one."""
    with start_span(op="http", description="_find_candidates"):
        candidates = set()

        # Maybe add a reverse index (tag => media) so this query is faster
        for medium in g.fast.get_all_tiny():
            if medium.medium_id == medium_id:
                continue

            if context.is_sfw and medium.rating != "s":
                continue

            if context.user_role != "admin" and medium.rating == "e":
                continue

            if len(medium.innate_tag_names & target_tag_names) == 0:
                continue

            candidates.add(medium)

        return candidates


def _get_similarity(
    context: BeevenueContext, medium: TinyMediumDocument
) -> PriorityQueue:
    with start_span(op="http", description="_get_similarity"):
        target_tag_names = medium.innate_tag_names
        candidates = _find_candidates(
            context, medium.medium_id, target_tag_names
        )

        # Keep up to 6 similar items in memory. We eject the least similar
        # once we have more than 5.
        jaccard_indices: PriorityQueue = PriorityQueue(maxsize=5 + 1)

        for candidate in candidates:
            candidate_tags = candidate.innate_tag_names
            intersection_size = len(candidate_tags & target_tag_names)
            union_size = len(candidate_tags | target_tag_names)

            similarity = float(intersection_size) / float(union_size)

            jaccard_indices.put_nowait(
                (
                    similarity,
                    candidate.medium_id,
                )
            )

            if jaccard_indices.full():
                jaccard_indices.get_nowait()

        return jaccard_indices


def similar_media(
    context: BeevenueContext, medium: TinyMediumDocument
) -> List[TinyMediumDocument]:
    with start_span(op="http", description="similar_media"):
        jaccard_indices = _get_similarity(context, medium)

        similar_media_ids = []
        for _ in range(0, 5):
            if jaccard_indices.empty():
                break
            indices = jaccard_indices.get_nowait()
            similar_media_ids.append(indices[1])

        # Since we kept Jaccard indices sorted ascendingly,
        # we have to reverse them here so that media_ids are sorted
        # descendingly (most similar first)
        similar_media_ids.reverse()

        media: List[TinyMediumDocument] = g.fast.get_many_tiny(
            similar_media_ids
        )
        return media

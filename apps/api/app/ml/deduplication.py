import hashlib
import re
from collections import defaultdict
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

DEDUPLICATION_VERSION: Final[str] = "v1.0.0"


class DuplicateGroup(BaseModel):
    """Cluster of exact or near-duplicate reviews assigned a shared group identifier."""

    model_config = ConfigDict(frozen=True)

    group_id: str = Field(description="Deterministic cluster identifier (SHA-256 prefix)")
    review_ids: list[str] = Field(description="IDs of reviews belonging to this cluster")
    canonical_review_id: str = Field(description="Primary representative review for the cluster")
    is_exact_duplicate: bool = Field(
        description="True if all reviews in group share identical normalized text"
    )
    group_size: int = Field(ge=1, description="Total reviews in this cluster")


def compute_exact_hash(text: str) -> str:
    """Compute deterministic SHA-256 hash of normalized text."""
    clean = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()


def compute_character_shingles(text: str, k: int = 4) -> set[str]:
    """Generate k-shingles (character n-grams) for near-duplicate Jaccard estimation."""
    clean = re.sub(r"\s+", " ", text.strip().lower())
    if len(clean) < k:
        return {clean}
    return {clean[i : i + k] for i in range(len(clean) - k + 1)}


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Calculate Jaccard similarity coefficient between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


class ReviewDeduplicator:
    """Detects exact duplicates and near-duplicate clusters to prevent data leakage.

    Enforces ML_SPECIFICATION.md Section 4.5 & Task 12:
    - Identifies identical text copies (common in spam campaigns or copypasta memes).
    - Clusters near-duplicates (e.g. minor typo edits, single-character variations).
    - Assigns stable group identifiers so dataset split algorithms can ensure entire
      duplicate groups remain confined within a single partition.
    """

    def __init__(
        self,
        near_duplicate_threshold: float = 0.85,
        shingle_k: int = 4,
        version: str = DEDUPLICATION_VERSION,
    ) -> None:
        self.near_duplicate_threshold = near_duplicate_threshold
        self.shingle_k = shingle_k
        self.version = version

    def cluster_reviews(self, review_items: list[dict[str, str]]) -> dict[str, DuplicateGroup]:
        """Group a collection of reviews into deduplication clusters.

        review_items: list of dicts with keys 'review_id' and 'normalized_text'.
        Returns: mapping of review_id -> DuplicateGroup.
        """
        if not review_items:
            return {}

        # 1. Exact duplicate grouping via exact hash
        exact_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for item in review_items:
            h = compute_exact_hash(item["normalized_text"])
            exact_groups[h].append(item)

        # 2. Represent each exact group by its canonical representative
        representatives: list[dict[str, str]] = []
        rep_to_exact_members: dict[str, list[str]] = {}
        for _h, members in exact_groups.items():
            rep = members[0]
            rep_id = rep["review_id"]
            representatives.append(rep)
            rep_to_exact_members[rep_id] = [m["review_id"] for m in members]

        # 3. Near-duplicate clustering across representatives
        shingle_cache: dict[str, set[str]] = {
            rep["review_id"]: compute_character_shingles(rep["normalized_text"], k=self.shingle_k)
            for rep in representatives
        }

        parent: dict[str, str] = {rep["review_id"]: rep["review_id"] for rep in representatives}

        def find(x: str) -> str:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x: str, y: str) -> None:
            root_x = find(x)
            root_y = find(y)
            if root_x != root_y:
                parent[root_y] = root_x

        # Compare representatives pairwise for near-duplicate Jaccard similarity
        n = len(representatives)
        for i in range(n):
            id_a = representatives[i]["review_id"]
            shingles_a = shingle_cache[id_a]
            if not shingles_a:
                continue

            for j in range(i + 1, n):
                id_b = representatives[j]["review_id"]
                shingles_b = shingle_cache[id_b]
                if not shingles_b:
                    continue

                # Quick length filter before set intersection
                len_a, len_b = len(shingles_a), len(shingles_b)
                if min(len_a, len_b) / max(len_a, len_b) < self.near_duplicate_threshold:
                    continue

                sim = jaccard_similarity(shingles_a, shingles_b)
                if sim >= self.near_duplicate_threshold:
                    union(id_a, id_b)

        # 4. Assemble merged clusters
        clusters: dict[str, list[str]] = defaultdict(list)
        for rep in representatives:
            root = find(rep["review_id"])
            clusters[root].extend(rep_to_exact_members[rep["review_id"]])

        # 5. Build final DuplicateGroup mapping per review
        review_to_group: dict[str, DuplicateGroup] = {}
        for root, member_ids in clusters.items():
            is_exact = len(member_ids) > 1 and len(clusters[root]) == len(
                rep_to_exact_members.get(root, [])
            )
            group_hash = hashlib.sha256(f"{root}:{len(member_ids)}".encode()).hexdigest()[:16]
            group = DuplicateGroup(
                group_id=f"grp_{group_hash}",
                review_ids=sorted(member_ids),
                canonical_review_id=root,
                is_exact_duplicate=is_exact,
                group_size=len(member_ids),
            )
            for rid in member_ids:
                review_to_group[rid] = group

        return review_to_group

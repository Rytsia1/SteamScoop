"""Deterministic development seed data script for SteamScoop.

Populates PostgreSQL with realistic games, aspects, models, reviews,
predictions, topics, analytics aggregates, and RBAC accounts.

Usage:
    python apps/api/scripts/seed_dev_data.py
    or: make seed / .\\scripts\\dev.ps1 seed
"""

import logging
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Ensure root apps/api is on python path when running standalone
api_root = Path(__file__).resolve().parent.parent
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.analytics import GameAnalytic  # noqa: E402
from app.models.aspect import Aspect, AspectPrediction  # noqa: E402
from app.models.game import Game  # noqa: E402
from app.models.ingestion import CollectionCheckpoint, IngestionBatch, IngestionJob  # noqa: E402
from app.models.ml import MLModel, PipelineRun  # noqa: E402
from app.models.review import Review  # noqa: E402
from app.models.sentiment import SentimentPrediction  # noqa: E402
from app.models.topic import ReviewTopic, Topic  # noqa: E402
from app.models.workspace import Role, User, UserRole  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("steamscoop.seed")


def seed_roles_and_users(db: Session) -> dict[str, User]:
    logger.info("--> Seeding RBAC roles and users...")
    roles = {
        "admin": "System Administrator with full platform operational access",
        "researcher": "Data scientist and intelligence analyst with export privileges",
        "member": "Standard authenticated community member",
    }
    role_entities: dict[str, Role] = {}
    for role_key, desc in roles.items():
        stmt = select(Role).where(Role.role_key == role_key)
        r = db.scalars(stmt).first()
        if not r:
            r = Role(role_key=role_key, description=desc)
            db.add(r)
            db.flush()
        role_entities[role_key] = r

    users_data = [
        ("admin@steamscoop.local", "SteamScoop Admin", "admin"),
        ("analyst@steamscoop.local", "Lead Intelligence Analyst", "researcher"),
    ]
    user_entities: dict[str, User] = {}
    for email, display_name, role_name in users_data:
        stmt = select(User).where(User.email == email)
        u = db.scalars(stmt).first()
        if not u:
            u = User(
                email=email,
                display_name=display_name,
                status="active",
                email_verified_at=datetime.now(UTC),
            )
            db.add(u)
            db.flush()

            ur = UserRole(
                user_id=u.id,
                role_id=role_entities[role_name].id,
                granted_at=datetime.now(UTC),
            )
            db.add(ur)
            db.flush()
        user_entities[role_name] = u

    return user_entities


def seed_aspects(db: Session) -> dict[str, Aspect]:
    logger.info("--> Seeding controlled aspect taxonomy...")
    aspects_data = [
        (
            "gameplay",
            "Gameplay & Mechanics",
            "Core game loop, combat pacing, controls, and challenge",
        ),
        (
            "performance",
            "Performance & Optimization",
            "Frame rates, stutter, memory usage, crashes, and stability",
        ),
        (
            "graphics",
            "Visuals & Art Style",
            "Art design, fidelity, texture work, lighting, and aesthetic",
        ),
        (
            "story",
            "Narrative & Lore",
            "Writing, worldbuilding, character depth, and narrative resolution",
        ),
        ("audio", "Music & Sound Design", "OST, ambient sound, foley work, and voice acting"),
        (
            "price",
            "Price & Value",
            "Cost relative to content volume, replayability, and monetization",
        ),
    ]
    aspect_map: dict[str, Aspect] = {}
    for key, name, desc in aspects_data:
        stmt = select(Aspect).where(Aspect.aspect_key == key)
        asp = db.scalars(stmt).first()
        if not asp:
            asp = Aspect(
                aspect_key=key,
                display_name=name,
                description=desc,
                is_active=True,
            )
            db.add(asp)
            db.flush()
        aspect_map[key] = asp
    return aspect_map


def seed_ml_models(db: Session) -> dict[str, MLModel]:
    logger.info("--> Seeding ML models and registries...")
    models_data = [
        {
            "model_key": "distilbert-sentiment",
            "version": "v1.0.0",
            "task": "sentiment",
            "framework": "transformers",
            "artifact_uri": "s3://steamscoop-artifacts/models/distilbert-sentiment-v1.0.0.tar.gz",
            "language_scope": ["en"],
            "label_schema": {"positive": 0, "negative": 1, "neutral": 2},
            "config": {"batch_size": 32, "max_length": 512},
            "metrics": {"macro_f1": 0.892, "accuracy": 0.904},
            "is_active": True,
        },
        {
            "model_key": "deberta-absa",
            "version": "v1.0.0",
            "task": "absa",
            "framework": "transformers",
            "artifact_uri": "s3://steamscoop-artifacts/models/deberta-absa-v1.0.0.tar.gz",
            "language_scope": ["en"],
            "label_schema": {"positive": 0, "negative": 1, "neutral": 2},
            "config": {"threshold": 0.65},
            "metrics": {"aspect_f1": 0.841, "polarity_f1": 0.825},
            "is_active": True,
        },
        {
            "model_key": "bertopic-steam",
            "version": "v1.0.0",
            "task": "topic",
            "framework": "bertopic",
            "artifact_uri": "s3://steamscoop-artifacts/models/bertopic-steam-v1.0.0.tar.gz",
            "language_scope": ["en"],
            "label_schema": {},
            "config": {"min_topic_size": 15},
            "metrics": {"coherence_c_v": 0.68},
            "is_active": True,
        },
    ]
    model_map: dict[str, MLModel] = {}
    for m in models_data:
        stmt = select(MLModel).where(
            MLModel.model_key == m["model_key"],
            MLModel.version == m["version"],
            MLModel.task == m["task"],
        )
        mod = db.scalars(stmt).first()
        if not mod:
            mod = MLModel(**m)
            db.add(mod)
            db.flush()
        model_map[str(m["task"])] = mod
    return model_map


def seed_topics(db: Session, topic_model: MLModel) -> dict[str, Topic]:
    logger.info("--> Seeding version-scoped topics...")
    topics_data = [
        {
            "topic_key": "combat_mechanics",
            "label": "Combat System & Boss Battles",
            "description": "Feedback discussing combat responsiveness, weapon balance, and boss mechanics.",
            "keywords": ["combat", "boss", "weapon", "mechanic", "dodge", "attack"],
            "representative_terms": ["boss fight", "combat fluidity", "attack timing"],
            "is_outlier": False,
        },
        {
            "topic_key": "narrative_depth",
            "label": "Story, Writing & Lore",
            "description": "Feedback discussing narrative emotional resonance, dialogue, and character arcs.",
            "keywords": ["story", "character", "dialogue", "lore", "writing", "ending"],
            "representative_terms": ["compelling narrative", "voice acting", "lore depth"],
            "is_outlier": False,
        },
        {
            "topic_key": "performance_bugs",
            "label": "Stability, Bugs & Frame Rates",
            "description": "Feedback focused on crashing, technical performance, glitches, and FPS drops.",
            "keywords": ["fps", "crash", "bug", "stutter", "glitch", "optimization"],
            "representative_terms": ["fps drop", "game crash", "stuttering issue"],
            "is_outlier": False,
        },
    ]
    topic_map: dict[str, Topic] = {}
    for t in topics_data:
        stmt = select(Topic).where(
            Topic.ml_model_id == topic_model.id,
            Topic.topic_key == t["topic_key"],
        )
        top = db.scalars(stmt).first()
        if not top:
            top = Topic(ml_model_id=topic_model.id, **t)
            db.add(top)
            db.flush()
        topic_map[str(t["topic_key"])] = top
    return topic_map


def seed_games_and_reviews(
    db: Session,
    admin_user: User,
    models: dict[str, MLModel],
    aspects: dict[str, Aspect],
    topics: dict[str, Topic],
) -> None:
    logger.info("--> Seeding games, reviews, predictions, and analytics...")
    games_data = [
        {
            "steam_app_id": 1145360,
            "name": "Hades",
            "short_description": "Defy the god of the dead as you hack and slash out of the Underworld in this rogue-like dungeon crawler from the creators of Bastion, Transistor, and Pyre.",
            "header_image_url": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1145360/header.jpg",
            "website_url": "https://www.supergiantgames.com/games/hades/",
            "developers": ["Supergiant Games"],
            "publishers": ["Supergiant Games"],
            "genres": ["Action", "Indie", "RPG"],
            "categories": ["Single-player", "Full controller support", "Steam Cloud"],
            "release_date": date(2020, 9, 17),
            "is_free": False,
            "catalog_status": "indexed",
            "is_active": True,
            "metadata_fetched_at": datetime.now(UTC),
            "reviews": [
                {
                    "steam_review_id": 100000001,
                    "review_text": "One of the greatest roguelikes ever made. The combat is responsive, the music is phenomenal, and every run advances the brilliant narrative.",
                    "voted_up": True,
                    "votes_up": 240,
                    "votes_funny": 12,
                    "weighted_vote_score": Decimal("0.96500000"),
                    "comment_count": 8,
                    "playtime_at_review": 3400,
                    "playtime_forever": 5200,
                    "steam_purchase": True,
                    "received_for_free": False,
                    "sentiment_label": "positive",
                    "sentiment_confidence": Decimal("0.98500"),
                    "aspect_sentiment": [
                        ("gameplay", "positive", "The combat is responsive", 38, 62),
                        ("audio", "positive", "the music is phenomenal", 64, 88),
                        ("story", "positive", "brilliant narrative", 118, 137),
                    ],
                    "topic_key": "combat_mechanics",
                    "topic_score": Decimal("0.9100000"),
                },
                {
                    "steam_review_id": 100000002,
                    "review_text": "Beautiful art and incredible voice acting, but after 40 hours the weapon balance feels somewhat repetitive and heat modifiers get frustrating.",
                    "voted_up": True,  # User still recommended on Steam!
                    "votes_up": 95,
                    "votes_funny": 4,
                    "weighted_vote_score": Decimal("0.85000000"),
                    "comment_count": 3,
                    "playtime_at_review": 2400,
                    "playtime_forever": 2800,
                    "steam_purchase": True,
                    "received_for_free": False,
                    "sentiment_label": "neutral",  # Demonstrating recommendation != sentiment decoupling!
                    "sentiment_confidence": Decimal("0.72000"),
                    "aspect_sentiment": [
                        ("graphics", "positive", "Beautiful art", 0, 13),
                        ("audio", "positive", "incredible voice acting", 18, 41),
                        (
                            "gameplay",
                            "negative",
                            "weapon balance feels somewhat repetitive",
                            59,
                            100,
                        ),
                    ],
                    "topic_key": "combat_mechanics",
                    "topic_score": Decimal("0.7800000"),
                },
            ],
        },
        {
            "steam_app_id": 1091500,
            "name": "Cyberpunk 2077",
            "short_description": "Cyberpunk 2077 is an open-world, action-adventure RPG set in the megalopolis of Night City, where you play as a cyberpunk mercenary wrapped up in a do-or-die fight for survival.",
            "header_image_url": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1091500/header.jpg",
            "website_url": "https://www.cyberpunk.net",
            "developers": ["CD PROJEKT RED"],
            "publishers": ["CD PROJEKT RED"],
            "genres": ["Action", "RPG"],
            "categories": [
                "Single-player",
                "Full controller support",
                "Steam Cloud",
                "HDR available",
            ],
            "release_date": date(2020, 12, 10),
            "is_free": False,
            "catalog_status": "indexed",
            "is_active": True,
            "metadata_fetched_at": datetime.now(UTC),
            "reviews": [
                {
                    "steam_review_id": 100000003,
                    "review_text": "With the 2.0 update and Phantom Liberty, this game is finally a masterpiece. Night City looks unbelievable and the story hits right in the feels.",
                    "voted_up": True,
                    "votes_up": 512,
                    "votes_funny": 18,
                    "weighted_vote_score": Decimal("0.98200000"),
                    "comment_count": 22,
                    "playtime_at_review": 6800,
                    "playtime_forever": 8500,
                    "steam_purchase": True,
                    "received_for_free": False,
                    "sentiment_label": "positive",
                    "sentiment_confidence": Decimal("0.97000"),
                    "aspect_sentiment": [
                        ("graphics", "positive", "Night City looks unbelievable", 56, 84),
                        ("story", "positive", "story hits right in the feels", 93, 123),
                        ("performance", "positive", "2.0 update and Phantom Liberty", 9, 39),
                    ],
                    "topic_key": "narrative_depth",
                    "topic_score": Decimal("0.8900000"),
                },
                {
                    "steam_review_id": 100000004,
                    "review_text": "Still suffering from frequent stutter and crashes on mid-range hardware. Driving physics feel floaty and NPC AI breaks constantly.",
                    "voted_up": False,
                    "votes_up": 180,
                    "votes_funny": 45,
                    "weighted_vote_score": Decimal("0.91000000"),
                    "comment_count": 14,
                    "playtime_at_review": 1200,
                    "playtime_forever": 1400,
                    "steam_purchase": True,
                    "received_for_free": False,
                    "sentiment_label": "negative",
                    "sentiment_confidence": Decimal("0.94000"),
                    "aspect_sentiment": [
                        ("performance", "negative", "frequent stutter and crashes", 20, 48),
                        ("gameplay", "negative", "Driving physics feel floaty", 74, 101),
                    ],
                    "topic_key": "performance_bugs",
                    "topic_score": Decimal("0.9300000"),
                },
            ],
        },
        {
            "steam_app_id": 367520,
            "name": "Hollow Knight",
            "short_description": "Forge your own path in Hollow Knight! An epic action adventure through a vast ruined kingdom of insects and heroes.",
            "header_image_url": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/367520/header.jpg",
            "website_url": "https://www.teamcherry.com.au",
            "developers": ["Team Cherry"],
            "publishers": ["Team Cherry"],
            "genres": ["Action", "Adventure", "Indie"],
            "categories": [
                "Single-player",
                "Full controller support",
                "Steam Cloud",
                "Steam Achievements",
            ],
            "release_date": date(2017, 2, 24),
            "is_free": False,
            "catalog_status": "indexed",
            "is_active": True,
            "metadata_fetched_at": datetime.now(UTC),
            "reviews": [
                {
                    "steam_review_id": 100000005,
                    "review_text": "An absolute masterclass in atmosphere, level design, and tight boss combat. Christopher Larkin's soundtrack elevates every moment.",
                    "voted_up": True,
                    "votes_up": 410,
                    "votes_funny": 9,
                    "weighted_vote_score": Decimal("0.97500000"),
                    "comment_count": 11,
                    "playtime_at_review": 4500,
                    "playtime_forever": 6100,
                    "steam_purchase": True,
                    "received_for_free": False,
                    "sentiment_label": "positive",
                    "sentiment_confidence": Decimal("0.99000"),
                    "aspect_sentiment": [
                        ("gameplay", "positive", "tight boss combat", 47, 64),
                        ("audio", "positive", "soundtrack elevates every moment", 88, 120),
                    ],
                    "topic_key": "combat_mechanics",
                    "topic_score": Decimal("0.9500000"),
                },
            ],
        },
    ]

    for gdata in games_data:
        reviews_list = gdata.pop("reviews")
        stmt = select(Game).where(Game.steam_app_id == gdata["steam_app_id"])
        game = db.scalars(stmt).first()
        if not game:
            game = Game(**gdata)
            db.add(game)
            db.flush()
        else:
            for k, v in gdata.items():
                setattr(game, k, v)
            db.flush()

        # Ingestion pipeline run & job state
        stmt_job = select(IngestionJob).where(
            IngestionJob.game_id == game.id,
            IngestionJob.job_type == "historical",
        )
        job = db.scalars(stmt_job).first()
        if not job:
            job = IngestionJob(
                game_id=game.id,
                job_type="historical",
                status="succeeded",
                source_api="steam_user_reviews_v1",
                request_config={"language": "all", "sample_size": 1000},
                requested_by_user_id=admin_user.id,
                scheduled_at=datetime.now(UTC) - timedelta(days=2),
                started_at=datetime.now(UTC) - timedelta(days=2),
                finished_at=datetime.now(UTC) - timedelta(days=2, minutes=-15),
                reviews_seen=len(reviews_list),
                reviews_inserted=len(reviews_list),
                reviews_updated=0,
                pages_processed=1,
            )
            db.add(job)
            db.flush()

            batch = IngestionBatch(
                ingestion_job_id=job.id,
                game_id=game.id,
                batch_number=1,
                cursor_in="*",
                cursor_out="batch_1_complete",
                request_started_at=datetime.now(UTC) - timedelta(days=2),
                request_finished_at=datetime.now(UTC) - timedelta(days=2, seconds=-2),
                http_status=200,
                source_count=len(reviews_list),
                inserted_count=len(reviews_list),
                updated_count=0,
                duplicate_count=0,
                batch_status="succeeded",
            )
            db.add(batch)

            ckpt = CollectionCheckpoint(
                game_id=game.id,
                stream_key="historical:all:all",
                collection_mode="historical",
                cursor="batch_1_complete",
                watermark_at=datetime.now(UTC) - timedelta(days=2),
                last_successful_job_id=job.id,
                last_success_at=datetime.now(UTC) - timedelta(days=2),
                status="idle",
                metadata_={"sample_target": 1000},
            )
            db.add(ckpt)
            db.flush()

        # Pipeline Runs
        nlp_runs: dict[str, PipelineRun] = {}
        for ptype in ["sentiment", "absa", "topic"]:
            m = models[ptype]
            stmt_run = select(PipelineRun).where(
                PipelineRun.game_id == game.id,
                PipelineRun.pipeline_type == ptype,
                PipelineRun.ml_model_id == m.id,
            )
            prun = db.scalars(stmt_run).first()
            if not prun:
                prun = PipelineRun(
                    pipeline_type=ptype,
                    ml_model_id=m.id,
                    game_id=game.id,
                    status="succeeded",
                    input_filter={"game_id": str(game.id)},
                    model_version_snapshot=m.version,
                    started_at=datetime.now(UTC) - timedelta(days=1),
                    finished_at=datetime.now(UTC) - timedelta(days=1, seconds=-30),
                    input_count=len(reviews_list),
                    success_count=len(reviews_list),
                    failure_count=0,
                )
                db.add(prun)
                db.flush()
            nlp_runs[ptype] = prun

        # Insert Reviews & Predictions
        total_reviews = 0
        pos_count = 0
        neg_count = 0
        neu_count = 0
        steam_rec = 0
        steam_not_rec = 0

        for rinfo in reviews_list:
            stmt_rev = select(Review).where(
                Review.game_id == game.id,
                Review.steam_review_id == rinfo["steam_review_id"],
            )
            rev = db.scalars(stmt_rev).first()
            if not rev:
                rev = Review(
                    game_id=game.id,
                    steam_review_id=rinfo["steam_review_id"],
                    language="en",
                    review_text=rinfo["review_text"],
                    voted_up=rinfo["voted_up"],
                    votes_up=rinfo["votes_up"],
                    votes_funny=rinfo["votes_funny"],
                    weighted_vote_score=rinfo["weighted_vote_score"],
                    comment_count=rinfo["comment_count"],
                    steam_playtime_at_review=rinfo["playtime_at_review"],
                    steam_playtime_forever=rinfo["playtime_forever"],
                    steam_purchase=rinfo["steam_purchase"],
                    received_for_free=rinfo["received_for_free"],
                    steam_created_at=datetime.now(UTC) - timedelta(days=30),
                )
                db.add(rev)
                db.flush()

            total_reviews += 1
            if rev.voted_up:
                steam_rec += 1
            else:
                steam_not_rec += 1

            # Sentiment prediction
            if rinfo["sentiment_label"] == "positive":
                pos_count += 1
            elif rinfo["sentiment_label"] == "negative":
                neg_count += 1
            else:
                neu_count += 1

            stmt_sent = select(SentimentPrediction).where(
                SentimentPrediction.review_id == rev.id,
                SentimentPrediction.ml_model_id == models["sentiment"].id,
                SentimentPrediction.pipeline_run_id == nlp_runs["sentiment"].id,
            )
            if not db.scalars(stmt_sent).first():
                sp = SentimentPrediction(
                    review_id=rev.id,
                    ml_model_id=models["sentiment"].id,
                    pipeline_run_id=nlp_runs["sentiment"].id,
                    label=rinfo["sentiment_label"],
                    confidence=rinfo["sentiment_confidence"],
                    probabilities={
                        "positive": float(rinfo["sentiment_confidence"])
                        if rinfo["sentiment_label"] == "positive"
                        else 0.1,
                        "negative": float(rinfo["sentiment_confidence"])
                        if rinfo["sentiment_label"] == "negative"
                        else 0.1,
                        "neutral": float(rinfo["sentiment_confidence"])
                        if rinfo["sentiment_label"] == "neutral"
                        else 0.1,
                    },
                    is_current=True,
                )
                db.add(sp)

            # Aspect predictions
            for akey, alabel, ev_text, start_o, end_o in rinfo.get("aspect_sentiment", []):
                asp_obj = aspects[akey]
                stmt_asp = select(AspectPrediction).where(
                    AspectPrediction.review_id == rev.id,
                    AspectPrediction.aspect_id == asp_obj.id,
                    AspectPrediction.ml_model_id == models["absa"].id,
                    AspectPrediction.pipeline_run_id == nlp_runs["absa"].id,
                )
                if not db.scalars(stmt_asp).first():
                    ap = AspectPrediction(
                        review_id=rev.id,
                        aspect_id=asp_obj.id,
                        ml_model_id=models["absa"].id,
                        pipeline_run_id=nlp_runs["absa"].id,
                        sentiment_label=alabel,
                        confidence=Decimal("0.88000"),
                        evidence_text=ev_text,
                        start_offset=start_o,
                        end_offset=end_o,
                    )
                    db.add(ap)

            # Topic assignment
            top_obj = topics.get(rinfo.get("topic_key", ""))
            if top_obj:
                stmt_rt = select(ReviewTopic).where(
                    ReviewTopic.review_id == rev.id,
                    ReviewTopic.topic_id == top_obj.id,
                    ReviewTopic.pipeline_run_id == nlp_runs["topic"].id,
                )
                if not db.scalars(stmt_rt).first():
                    rt = ReviewTopic(
                        review_id=rev.id,
                        topic_id=top_obj.id,
                        pipeline_run_id=nlp_runs["topic"].id,
                        score=rinfo.get("topic_score", Decimal("0.8000000")),
                        is_primary=True,
                    )
                    db.add(rt)

        db.flush()

        # Precomputed GameAnalytic aggregate for the game
        period_start = date.today() - timedelta(days=7)
        period_end = date.today()
        stmt_agg = select(GameAnalytic).where(
            GameAnalytic.game_id == game.id,
            GameAnalytic.period_type == "week",
            GameAnalytic.period_start == period_start,
            GameAnalytic.model_version_key == "baseline",
        )
        if not db.scalars(stmt_agg).first():
            norm_sentiment = Decimal("0.75000") if pos_count >= neg_count else Decimal("-0.45000")
            ga = GameAnalytic(
                game_id=game.id,
                period_type="week",
                period_start=period_start,
                period_end=period_end,
                model_version_key="baseline",
                review_count=total_reviews,
                positive_count=pos_count,
                negative_count=neg_count,
                neutral_count=neu_count,
                steam_recommended_count=steam_rec,
                steam_not_recommended_count=steam_not_rec,
                sentiment_score=norm_sentiment,
                aspect_summary={"gameplay": {"positive": pos_count, "negative": neg_count}},
                topic_summary={"combat_mechanics": total_reviews},
            )
            db.add(ga)

    db.commit()


def main() -> None:
    logger.info("Starting SteamScoop development database seed process...")
    db = SessionLocal()
    try:
        users = seed_roles_and_users(db)
        aspects = seed_aspects(db)
        models = seed_ml_models(db)
        topics = seed_topics(db, models["topic"])
        seed_games_and_reviews(db, users["admin"], models, aspects, topics)
        logger.info("Database seeding successfully completed!")
    except Exception as exc:
        logger.exception("Seeding failed: %s", exc)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

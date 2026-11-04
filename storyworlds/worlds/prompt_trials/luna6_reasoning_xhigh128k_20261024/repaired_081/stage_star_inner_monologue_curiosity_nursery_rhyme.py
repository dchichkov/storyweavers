#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a child, a stage, and a paper star.

Curiosity and an inner monologue help the young performers notice what is
hiding their star before they choose a gentle, practical repair.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

REPO_ROOT = next(
    (
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "storyworlds" / "results.py").is_file()
    ),
    Path(__file__).resolve().parents[5],
)
sys.path.insert(0, str(REPO_ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    owner: Optional[str] = None
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class StageSite:
    key: str
    stage_phrase: str
    venue: str
    location: str
    has_airflow: bool
    air_source: str
    has_backlight: bool
    light_source: str


@dataclass
class StoryParams:
    stage: str = "willow_hall"
    hero_name: str = "Lina"
    helper_name: str = "Bo"
    incident: str = "blend"
    opening: str = "rhyme"
    seed: Optional[int] = None


class World:
    def __init__(self, site: StageSite) -> None:
        self.site = site
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        if entity.id in self.entities:
            raise StoryError(f"An entity named {entity.id!r} already exists.")
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


STAGE_REGISTRY = {
    "willow_hall": StageSite(
        key="willow_hall",
        stage_phrase="the Willow Hall stage",
        venue="Willow Hall",
        location="the little hall beside the school garden",
        has_airflow=True,
        air_source="the side door",
        has_backlight=True,
        light_source="the lamp behind a cardboard tree",
    ),
    "acorn_school": StageSite(
        key="acorn_school",
        stage_phrase="the Acorn School stage",
        venue="Acorn School",
        location="the school music room",
        has_airflow=False,
        air_source="",
        has_backlight=True,
        light_source="the lamp behind a cardboard tree",
    ),
    "moonbeam_garden": StageSite(
        key="moonbeam_garden",
        stage_phrase="the Moonbeam Garden stage",
        venue="the Moonbeam Garden",
        location="the community garden",
        has_airflow=True,
        air_source="the open garden arch",
        has_backlight=False,
        light_source="",
    ),
}

HERO_NAMES = ["Lina", "Tavi", "Mira", "Nia", "Pip"]
HELPER_NAMES = ["Bo", "Ari", "June", "Tess", "Kit"]

OPENINGS = ("rhyme", "mystery", "quiet", "countdown")

OPENING_LINES = {
    "rhyme": [
        "At {stage_phrase}, tap-tap went the feet and hush fell down. {hero} carried a golden paper star to shine for the little crowd in town.",
        "Tap-tap went the feet on {stage_phrase}; then hush-hush filled the room. {hero} held a golden paper star for the little play's last rhyme.",
    ],
    "mystery": [
        "A golden paper star had a puzzle to solve at {stage_phrase}. {hero} held it up as the children waited for the final verse.",
        "At {stage_phrase}, a tiny golden star seemed to be playing hide-and-seek. {hero} carried it in as the children gathered for their rhyme.",
    ],
    "quiet": [
        "The curtain rested like a blue hill at {stage_phrase}. {hero} held a golden paper star as the room grew still.",
        "At {stage_phrase}, the room grew quiet, and the curtain swayed like a sleepy sea. {hero} brought a golden paper star for the final verse.",
    ],
    "countdown": [
        "One verse, then the last, and the show would begin at {stage_phrase}. {hero} carried the golden paper star to its place.",
        "Soon the children would sing their final rhyme at {stage_phrase}. {hero} had one golden paper star to set in the little show.",
    ],
}

INCIDENTS = {
    "blend": {
        "requires_airflow": False,
        "requires_backlight": False,
        "premise": "The golden paper star nearly vanished against a backdrop crowded with shiny star stickers.",
        "mistake": "{hero} added three more glittering stickers, but the little star blended in even more.",
        "failed_view": "From the last row, the star was only a small blur among the bright dots.",
        "thought": "Why is one golden star hard to find in a sky full of stars?",
        "question": "Why can't the last row find my star?",
        "reply": "Let's try a plain blue card behind it, then look from the back.",
        "test": "They stepped to the last row and held a plain blue card behind the paper star.",
        "clue": "Against the quiet blue, the gold points stood out at once.",
        "insight": "A quiet sky helps gold shine; let's give our star some blue!",
        "change": "They peeled away the extra stickers and fixed a neat midnight-blue patch behind the star.",
        "result": "From the last row, the gold points were easy to spot against the calm blue patch.",
        "lesson": "A bright thing can be easier to see when it has a little quiet space around it",
        "ending": "Blue behind gold, and clear to see: the little star shone merrily.",
    },
    "breeze": {
        "requires_airflow": True,
        "requires_backlight": False,
        "premise": "Each puff slipping in through {air_source} swung the golden paper star behind the curtain.",
        "mistake": "{hero} tied the star's ribbon to the curtain, but the next puff pulled them both out of view.",
        "failed_view": "The star vanished behind the moving curtain whenever the air stirred.",
        "thought": "What is tugging the star away each time it sways?",
        "question": "Why does my star swing out of sight?",
        "reply": "Let's watch a loose ribbon before we tie anything else.",
        "test": "They watched a paper ribbon at the stage edge while the curtain rested free.",
        "clue": "Each puff from {air_source} made the loose ribbon flutter toward the curtain.",
        "insight": "The moving air pulls the curtain, too; let's move the star away from it.",
        "change": "They unclipped the star and set it on a steady stand near center stage, clear of both the curtain and {air_source}.",
        "result": "The ribbon still fluttered, but the star stayed steady in the open, clear of the curtain.",
        "lesson": "Watch where the air travels before tying a decoration to a curtain",
        "ending": "The curtain swayed a soft goodnight; the steady star shone clear and bright.",
    },
    "shadow": {
        "requires_airflow": False,
        "requires_backlight": True,
        "premise": "The light from {light_source} left the golden paper star in the shadow of the cardboard tree.",
        "mistake": "{hero} pushed the star farther behind the tree, hoping to find more light, but its points grew dimmer.",
        "failed_view": "From the seats, only the edge of the star glimmered past the tree's shadow.",
        "thought": "Where does the light go when the star slips behind the tree?",
        "question": "Why does the tree dim my star?",
        "reply": "Let's trace the light with a white card, and leave the lamp alone.",
        "test": "They slid a white card from the bright side of the scenery toward the star, without touching the lamp.",
        "clue": "The card went dark as it passed behind the tree; the scenery, not the star, was blocking the light.",
        "insight": "The tree is making the shadow. We'll put the star in front and leave the lamp just so.",
        "change": "They moved the paper star to the front edge of the scenery, where the lamp could reach it, and left the lamp safely in place.",
        "result": "The star's gold points glowed on the front edge, while the cardboard tree kept its lovely shadow behind.",
        "lesson": "Notice what blocks the light before deciding to move a lamp",
        "ending": "The tree kept shade, the star caught light; both shared the stage before goodnight.",
    },
}


def is_reasonable_pair(stage_key: str, incident_key: str) -> bool:
    """Python gate for stage and incident combinations."""
    site = STAGE_REGISTRY.get(stage_key)
    incident = INCIDENTS.get(incident_key)
    if site is None or incident is None:
        return False

    required_fields = (
        "premise",
        "mistake",
        "failed_view",
        "thought",
        "question",
        "reply",
        "test",
        "clue",
        "insight",
        "change",
        "result",
        "lesson",
        "ending",
    )
    if any(not incident.get(field) for field in required_fields):
        return False
    if incident["requires_airflow"] and not site.has_airflow:
        return False
    if incident["requires_backlight"] and not site.has_backlight:
        return False
    return True


def _valid_person_name(name: str) -> bool:
    if not isinstance(name, str) or not name or name != name.strip() or len(name) > 32:
        return False
    allowed_punctuation = " -'’."
    return (
        any(character.isalpha() for character in name)
        and all(character.isalpha() or character in allowed_punctuation for character in name)
    )


def validate_params(params: StoryParams) -> None:
    if params.stage not in STAGE_REGISTRY:
        raise StoryError(f"Unknown stage: {params.stage!r}.")
    if params.incident not in INCIDENTS:
        raise StoryError(f"Unknown star problem: {params.incident!r}.")
    if params.opening not in OPENINGS:
        raise StoryError(f"Unknown opening style: {params.opening!r}.")
    if not _valid_person_name(params.hero_name):
        raise StoryError("The hero's name must be a short, readable name.")
    if not _valid_person_name(params.helper_name):
        raise StoryError("The helper's name must be a short, readable name.")
    if params.hero_name.casefold() == params.helper_name.casefold():
        raise StoryError("The helper must be a different person from the hero.")

    if not is_reasonable_pair(params.stage, params.incident):
        site = STAGE_REGISTRY[params.stage]
        if INCIDENTS[params.incident]["requires_airflow"] and not site.has_airflow:
            raise StoryError(
                f"The breeze problem needs moving air nearby; {site.stage_phrase} has no draft source."
            )
        if INCIDENTS[params.incident]["requires_backlight"] and not site.has_backlight:
            raise StoryError(
                f"The shadow problem needs a lamp behind the scenery; {site.stage_phrase} has no backlight."
            )
        raise StoryError("That stage and star problem do not make a reasonable story together.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    stage_key = args.stage or rng.choice(list(STAGE_REGISTRY))
    site = STAGE_REGISTRY[stage_key]

    hero_name = args.name or rng.choice(HERO_NAMES)
    if args.helper:
        helper_name = args.helper
    else:
        choices = [name for name in HELPER_NAMES if name.casefold() != hero_name.casefold()]
        if not choices:
            choices = [name for name in HERO_NAMES if name.casefold() != hero_name.casefold()]
        helper_name = rng.choice(choices)

    if hero_name.casefold() == helper_name.casefold():
        raise StoryError("The helper must be a different person from the hero.")

    possible_incidents = [
        key for key in INCIDENTS if is_reasonable_pair(stage_key, key)
    ]
    if args.incident:
        incident = args.incident
        if not is_reasonable_pair(stage_key, incident):
            if INCIDENTS[incident]["requires_airflow"] and not site.has_airflow:
                raise StoryError(
                    f"The breeze problem needs moving air nearby; {site.stage_phrase} has no draft source."
                )
            if INCIDENTS[incident]["requires_backlight"] and not site.has_backlight:
                raise StoryError(
                    f"The shadow problem needs a lamp behind the scenery; {site.stage_phrase} has no backlight."
                )
            raise StoryError("That stage and star problem do not make a reasonable story together.")
    else:
        incident = rng.choice(possible_incidents)

    params = StoryParams(
        stage=stage_key,
        hero_name=hero_name,
        helper_name=helper_name,
        incident=incident,
        opening=args.opening or rng.choice(OPENINGS),
    )
    validate_params(params)
    return params


def _render_text(text: str, params: StoryParams, site: StageSite) -> str:
    return text.format(
        hero=params.hero_name,
        helper=params.helper_name,
        stage_phrase=site.stage_phrase,
        air_source=site.air_source,
        light_source=site.light_source,
    )


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    site = STAGE_REGISTRY[params.stage]
    incident = INCIDENTS[params.incident]
    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.stage}:{params.hero_name}:{params.helper_name}:{params.incident}:{params.opening}"
    )

    world = World(site)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            label=params.hero_name,
            type="child",
            location=site.stage_phrase,
            meters={"attention": 0.55, "confidence": 0.35},
            memes={"curiosity": 0.65, "worry": 0.35, "pride": 0.1},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            label=params.helper_name,
            type="friend",
            location=site.stage_phrase,
            meters={"attention": 0.8, "patience": 0.85},
            memes={"kindness": 0.9, "curiosity": 0.6},
        )
    )

    stage_meters = {
        "airflow": 0.85 if site.has_airflow else 0.05,
        "backdrop_clutter": 0.45,
        "light_obstruction": 0.8 if site.has_backlight else 0.05,
        "star_separation": 0.35,
        "clearance": 1.0,
    }
    star_meters = {
        "visibility": 0.35,
        "stability": 0.85,
        "glow": 0.8,
        "position_forward": 0.1,
    }
    if params.incident == "blend":
        stage_meters["backdrop_clutter"] = 0.78
        star_meters["visibility"] = 0.3
    elif params.incident == "breeze":
        star_meters["stability"] = 0.3
    else:
        star_meters["visibility"] = 0.3
        star_meters["position_forward"] = 0.1

    stage = world.add(
        Entity(
            id="stage",
            kind="place",
            label=site.stage_phrase,
            type="performance_stage",
            location=site.location,
            meters=stage_meters,
            memes={"welcome": 0.85, "anticipation": 0.65},
        )
    )
    star = world.add(
        Entity(
            id="star",
            kind="prop",
            label="golden paper star",
            type="paper_star",
            owner=hero.id,
            location=site.stage_phrase,
            meters=star_meters,
            memes={"hope": 0.8, "delight": 0.35},
        )
    )

    world.say(
        _render_text(
            rng.choice(OPENING_LINES[params.opening]), params, site
        )
    )
    world.say(
        f"Neighbors gathered at {site.venue}, in {site.location}, to hear the children's little play."
    )
    world.say(_render_text(incident["premise"], params, site))

    if params.incident == "blend":
        stage.meters["backdrop_clutter"] = 0.97
        star.meters["visibility"] = 0.14
    elif params.incident == "breeze":
        star.meters["stability"] = 0.12
        star.meters["visibility"] = 0.24
    else:
        star.meters["visibility"] = 0.12
        stage.meters["light_obstruction"] = 0.9

    hero.memes["worry"] = 0.75
    star.memes["hope"] = 0.45
    world.say(_render_text(incident["mistake"], params, site))
    if star.meters["visibility"] < 0.25 or star.meters["stability"] < 0.2:
        world.say(_render_text(incident["failed_view"], params, site))

    world.say(
        f"Curiosity stirred beneath {hero.label}'s worry. In {hero.label}'s thoughts, "
        f"one question brightened: {incident['thought']}"
    )
    world.say(f"“{incident['question']}” {hero.label} asked.")
    world.say(f"“{incident['reply']}” {helper.label} answered.")
    world.say(_render_text(incident["test"], params, site))
    world.say(_render_text(incident["clue"], params, site))
    world.facts["clue_observed"] = True
    hero.memes["curiosity"] = 1.0
    helper.meters["attention"] = 1.0

    world.say(f"“{incident['insight']}” {hero.label} said.")

    if params.incident == "blend":
        stage.meters["backdrop_clutter"] = 0.25
        stage.meters["star_separation"] = 0.92
        star.meters["visibility"] = 0.94
        star.meters["stability"] = 0.95
    elif params.incident == "breeze":
        stage.meters["clearance"] = 0.95
        star.meters["visibility"] = 0.91
        star.meters["stability"] = 0.96
    else:
        star.meters["position_forward"] = 0.95
        star.meters["visibility"] = 0.93
        star.meters["stability"] = 0.95

    solution_sound = (
        world.facts["clue_observed"] is True
        and star.meters["visibility"] >= 0.8
        and star.meters["stability"] >= 0.8
        and stage.meters["clearance"] >= 0.8
    )
    if not solution_sound:
        raise StoryError("The star's repair did not make it visible and secure.")

    star.memes["hope"] = 1.0
    star.memes["delight"] = 0.9
    hero.memes["worry"] = 0.1
    hero.memes["pride"] = 0.9
    hero.meters["confidence"] = 0.9

    world.say(_render_text(incident["change"], params, site))
    if star.meters["visibility"] >= 0.8 and star.meters["stability"] >= 0.8:
        world.say(_render_text(incident["result"], params, site))
    world.say(f"{hero.label} understood why: {incident['lesson']}.")
    world.say(_render_text(incident["ending"], params, site))

    world.facts.update(
        hero=hero,
        helper=helper,
        stage=stage,
        star=star,
        incident=params.incident,
        clue=_render_text(incident["clue"], params, site),
        transformation=_render_text(incident["change"], params, site),
        lesson=incident["lesson"],
        proof=_render_text(incident["result"], params, site),
        transformed=True,
        story_complete=True,
    )

    rendered_clue = _render_text(incident["clue"], params, site)
    rendered_premise = _render_text(incident["premise"], params, site)
    rendered_mistake = _render_text(incident["mistake"], params, site)
    rendered_change = _render_text(incident["change"], params, site)
    rendered_result = _render_text(incident["result"], params, site)
    rendered_ending = _render_text(incident["ending"], params, site)

    prompts = [
        (
            f"Tell a gentle nursery-rhyme-style story about {hero.label} preparing "
            f"a golden paper star for a show at {site.stage_phrase}."
        ),
        (
            f"Show how {hero.label} and {helper.label} investigate this clue: "
            f"{rendered_clue}"
        ),
        (
            f"Include {hero.label}'s private thought, a spoken exchange, a useful "
            f"repair, and this ending image: {rendered_ending}"
        ),
    ]
    story_qa = [
        QAItem(
            question="What made the star hard to see at the beginning?",
            answer=rendered_premise,
        ),
        QAItem(
            question=f"What did {hero.label} try first?",
            answer=rendered_mistake,
        ),
        QAItem(
            question=f"What clue helped {hero.label} and {helper.label} understand the problem?",
            answer=rendered_clue,
        ),
        QAItem(
            question="How did the children change the star's display?",
            answer=rendered_change,
        ),
        QAItem(
            question="What proved that the new display worked?",
            answer=rendered_result,
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer=f"{hero.label} learned that {incident['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a stage?",
            answer="A stage is a raised or marked place where performers can be seen while they sing, speak, or act.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to find out how something works or why something has happened.",
        ),
        QAItem(
            question="What is an inner thought?",
            answer="An inner thought is a question or idea a character has in their mind, even when they do not say it aloud.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


ASP_RULES = r"""
valid_stage(S) :- stage_name(S).
valid_incident(I) :- incident_name(I).

resolved(I) :-
    valid_incident(I),
    has_clue(I),
    has_repair(I),
    has_proof(I).

story_possible(S,I) :-
    valid_stage(S),
    scenario_fits(S,I),
    resolved(I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for stage_key in STAGE_REGISTRY:
        lines.append(asp.fact("stage_name", stage_key))
    for incident_key in INCIDENTS:
        lines.append(asp.fact("incident_name", incident_key))
        lines.append(asp.fact("has_clue", incident_key))
        lines.append(asp.fact("has_repair", incident_key))
        lines.append(asp.fact("has_proof", incident_key))
    for stage_key in STAGE_REGISTRY:
        for incident_key in INCIDENTS:
            if is_reasonable_pair(stage_key, incident_key):
                lines.append(asp.fact("scenario_fits", stage_key, incident_key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except ImportError as exc:
        print(f"ASP verification requires the shared ASP helper and clingo: {exc}", file=sys.stderr)
        return 2

    show = "#show resolved/1.\n#show story_possible/2."
    model = asp.one_model(asp_program(show))
    actual_resolved = set(asp.atoms(model, "resolved"))
    actual_pairs = set(asp.atoms(model, "story_possible"))

    expected_resolved = {
        (incident_key,)
        for incident_key in INCIDENTS
        if all(
            INCIDENTS[incident_key].get(field)
            for field in ("clue", "change", "result")
        )
    }
    expected_pairs = {
        (stage_key, incident_key)
        for stage_key in STAGE_REGISTRY
        for incident_key in INCIDENTS
        if is_reasonable_pair(stage_key, incident_key)
    }

    if actual_resolved != expected_resolved or actual_pairs != expected_pairs:
        print("MISMATCH between ASP and Python reasonableness.")
        print("ASP resolved:", sorted(actual_resolved))
        print("PY  resolved:", sorted(expected_resolved))
        print("ASP pairs:", sorted(actual_pairs))
        print("PY  pairs:", sorted(expected_pairs))
        return 1

    index = 0
    try:
        for stage_key, incident_key in sorted(expected_pairs):
            sample = generate(
                StoryParams(
                    stage=stage_key,
                    hero_name="Lina",
                    helper_name="Bo",
                    incident=incident_key,
                    opening="rhyme",
                    seed=4000 + index,
                )
            )
            index += 1
            if (
                sample.world is None
                or not sample.world.facts.get("story_complete")
                or not sample.world.facts.get("transformed")
                or sample.story.count("“") < 2
                or sample.story.count("”") < 2
                or "Curiosity" not in sample.story
                or "thoughts" not in sample.story
                or not sample.story_qa
                or not sample.world_qa
            ):
                raise StoryError(
                    f"Generated-story checks failed for {stage_key}/{incident_key}."
                )
    except StoryError as exc:
        print(f"Generated-story verification failed: {exc}")
        return 1

    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def asp_report() -> int:
    try:
        import asp
    except ImportError as exc:
        print(f"ASP mode requires the shared ASP helper and clingo: {exc}", file=sys.stderr)
        return 2

    show = "#show resolved/1.\n#show story_possible/2."
    model = asp.one_model(asp_program(show))
    pairs = sorted(asp.atoms(model, "story_possible"))
    print("ASP found these stage and star-problem combinations have a clue, repair, and proof:")
    for stage_key, incident_key in pairs:
        print(
            f"- {STAGE_REGISTRY[stage_key].stage_phrase}: "
            f"{incident_key.replace('_', ' ')}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nursery-rhyme storyworld about curiosity, a little stage, and a paper star."
    )
    parser.add_argument("--stage", choices=STAGE_REGISTRY)
    parser.add_argument("--name", help="Name of the young performer.")
    parser.add_argument("--helper", help="Name of the helpful friend.")
    parser.add_argument("--incident", choices=INCIDENTS)
    parser.add_argument("--opening", choices=OPENINGS)
    parser.add_argument("-n", type=int, default=1, help="Number of stories to generate.")
    parser.add_argument("--all", action="store_true", help="Generate every reasonable stage/problem combination.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true", help="Solve and print the ASP world possibilities.")
    parser.add_argument("--verify", action="store_true", help="Check ASP/Python parity and generated stories.")
    parser.add_argument("--show-asp", action="store_true", help="Print the grounded ASP program.")
    return parser


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)

    if trace and sample.world is not None:
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(
                f"{key}: {entity.label} "
                f"meters={entity.meters} memes={entity.memes}"
            )

    if qa:
        print()
        print("== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        try:
            print(asp_program("#show resolved/1.\n#show story_possible/2."))
        except ImportError as exc:
            print(f"ASP display requires the shared ASP helper and clingo: {exc}", file=sys.stderr)
            raise SystemExit(2)
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        raise SystemExit(asp_report())
    if args.n < 1:
        raise StoryError("The number of stories must be at least one.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        pairs = [
            (stage_key, incident_key)
            for stage_key in STAGE_REGISTRY
            for incident_key in INCIDENTS
            if is_reasonable_pair(stage_key, incident_key)
        ]
        for index, (stage_key, incident_key) in enumerate(pairs):
            params = StoryParams(
                stage=stage_key,
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                helper_name=HELPER_NAMES[index % len(HELPER_NAMES)],
                incident=incident_key,
                opening=OPENINGS[index % len(OPENINGS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index * 7919)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)

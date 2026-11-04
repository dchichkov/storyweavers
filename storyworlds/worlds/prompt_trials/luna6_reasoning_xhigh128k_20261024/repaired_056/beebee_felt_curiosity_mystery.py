#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_ROOT = os.path.abspath(__file__)
for _ in range(5):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


FEATURES = ("curiosity",)

PLACES = {
    "sunlit sewing room": {
        "display": "the sunlit sewing room",
        "description": "Sunlight warmed the shelves of felt and thread.",
        "resources": {
            "quilt",
            "draft",
            "felt_flower",
            "small_bell",
            "padded_band",
            "story_board",
            "felt_leaf",
            "felt_heart",
        },
    },
    "puppet nook": {
        "display": "the puppet nook",
        "description": "Bright costumes waited in baskets along the puppet nook wall.",
        "resources": {
            "felt_flower",
            "small_bell",
            "padded_band",
            "story_board",
            "felt_leaf",
            "felt_heart",
        },
    },
    "story corner": {
        "display": "the story corner",
        "description": "A low felt board stood ready for a new tale.",
        "resources": {"story_board", "felt_leaf", "felt_heart"},
    },
    "attic playroom": {
        "display": "the attic playroom",
        "description": "Warm light fell across the attic playroom's patchwork quilt.",
        "resources": {"quilt", "draft", "story_board", "felt_leaf", "felt_heart"},
    },
}

MYSTERIES = {
    "quilt_star": {
        "title": "The Star in the Quilt",
        "requirements": {"quilt", "draft"},
        "activity": "a bright quilt for a puppet show",
        "opening": (
            "The loose blue felt star that belonged on the quilt had vanished "
            "just before the puppet show."
        ),
        "item_label": "the blue felt star",
        "item_id": "blue_star",
        "hidden_location": "inside the quilt's folded edge",
        "final_location": "on the quilt",
        "clue": (
            "A blue thread peeked from the quilt's folded edge, while the ribbon "
            "by the open window fluttered toward it."
        ),
        "turn_question": (
            "The ribbon is blowing toward that fold. Could the star be tucked inside?"
        ),
        "turn_reply": "The blue thread points there. Let's lift the fold gently.",
        "deduction": (
            "the open window's breeze had lifted the quilt and tucked the loose "
            "star into its fold"
        ),
        "search_action": (
            "Beebee held the quilt steady while {companion} lifted the folded edge, "
            "and the blue star slid into view."
        ),
        "repair_action": (
            "Together they stitched a small loop onto the star and smoothed the quilt flat."
        ),
        "outcome": "The star stayed on the quilt, ready for the puppet show.",
        "ending": (
            "At showtime, the blue star gleamed above the little puppets while "
            "the window ribbon hung still."
        ),
        "lesson": (
            "A breeze can hide something without anyone taking it, so look for "
            "what moved."
        ),
        "answer_missing": (
            "The loose blue felt star was missing from the quilt just before "
            "the puppet show."
        ),
        "answer_resolution": (
            "Beebee and the companion found the star inside the quilt's fold, "
            "stitched on a small loop, and smoothed the quilt flat."
        ),
    },
    "hidden_bell": {
        "title": "The Bell Beneath the Flower",
        "requirements": {"felt_flower", "small_bell", "padded_band"},
        "activity": "a flower headband for the puppet parade",
        "opening": (
            "The tiny brass bell that belonged on the felt flower was missing "
            "from the headband."
        ),
        "item_label": "the tiny brass bell",
        "item_id": "brass_bell",
        "hidden_location": "inside the headband's padded felt lining",
        "final_location": "on the felt flower",
        "clue": (
            "A small round bump hid beneath the padded felt band, and a faint "
            "ting sounded when the headband moved."
        ),
        "turn_question": (
            "I heard a tiny ting beneath the band. Could the bell be inside?"
        ),
        "turn_reply": (
            "The flower's loop is loose, so let's open the soft fold instead "
            "of pulling at it."
        ),
        "deduction": (
            "the bell had slipped through the loose loop and nestled inside "
            "the headband's padded lining"
        ),
        "search_action": (
            "Beebee held the flower still while {companion} eased open the lining; "
            "the bell gave a bright little chime."
        ),
        "repair_action": (
            "They tied the bell back with a snug felt loop and checked that it "
            "rang freely."
        ),
        "outcome": (
            "The bell chimed from the flower without getting lost in the lining again."
        ),
        "ending": (
            "The parade began with a merry ting, and the flower bobbed safely "
            "above the felt costumes."
        ),
        "lesson": (
            "A tiny sound can tell you where to look, especially when you listen "
            "before tugging."
        ),
        "answer_missing": (
            "The tiny brass bell was missing from the felt flower on the headband."
        ),
        "answer_resolution": (
            "Beebee and the companion found the bell inside the padded lining, "
            "then tied it back to the flower with a snug felt loop."
        ),
    },
    "leaf_heart": {
        "title": "The Heart on the Hidden Leaf",
        "requirements": {"story_board", "felt_leaf", "felt_heart"},
        "activity": "a felt story board for the afternoon tale",
        "opening": (
            "The red felt heart had vanished from the story board just before "
            "story time."
        ),
        "item_label": "the red felt heart",
        "item_id": "red_heart",
        "hidden_location": "on the back of the green felt leaf",
        "final_location": "at the center of the story board",
        "clue": (
            "The green felt leaf lay with one point raised, and a red fuzzy edge "
            "peeked from its back."
        ),
        "turn_question": "There's red fuzz on the back of the leaf. Could it be the heart?",
        "turn_reply": "Then the heart traveled with the leaf. Turn it over gently.",
        "deduction": (
            "the red felt heart had clung to the back of the green felt leaf "
            "when the board was rearranged"
        ),
        "search_action": (
            "Beebee steadied the board while {companion} turned over the leaf, "
            "revealing the red heart beneath it."
        ),
        "repair_action": (
            "They freed the heart from the leaf and placed each felt shape in "
            "its own spot."
        ),
        "outcome": (
            "The story board was ready, with the heart shining in the middle "
            "of its felt garden."
        ),
        "ending": (
            "When story time began, the red heart sat beside the green leaf, "
            "bright against the quiet board."
        ),
        "lesson": (
            "Felt shapes can cling together, so check both sides before deciding "
            "something is gone."
        ),
        "answer_missing": (
            "The red felt heart was missing from the story board just before "
            "story time."
        ),
        "answer_resolution": (
            "Beebee and the companion found the heart clinging to the back of "
            "the green felt leaf and returned both shapes to their places."
        ),
    },
}

COMPANIONS = ("Mira", "Rowan", "Kit", "Tavi", "Nell", "Jules")
MOODS = ("patient", "bright-eyed", "thoughtful", "eager")

PARAMETER_REGISTRIES = {
    "places": PLACES,
    "mysteries": MYSTERIES,
    "companions": COMPANIONS,
    "moods": MOODS,
    "features": FEATURES,
}

OPENING_BEATS = (
    "Morning light made every color look ready for a story.",
    "The room was quiet except for a soft rustle of fabric.",
    "A small patch of sunlight rested on the worktable.",
    "For a moment, everyone was thinking about the fun that came next.",
)

REFLECTIONS = (
    "Beebee smiled; asking a question had led to a clue.",
    "The companion nodded, glad they had looked before blaming anyone.",
    "Beebee tucked the new discovery away for the next puzzle.",
    "Together they remembered how much one careful look could reveal.",
)


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    visible: bool = True
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    mystery: str
    companion: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    phase: str = "unstarted"

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


def _compatible(place: str, mystery: str) -> bool:
    if place not in PLACES or mystery not in MYSTERIES:
        return False
    return MYSTERIES[mystery]["requirements"].issubset(PLACES[place]["resources"])


def compatibility_pairs() -> set[tuple[str, str]]:
    return {
        (place, mystery)
        for place in PLACES
        for mystery in MYSTERIES
        if _compatible(place, mystery)
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle mystery storyworld about Beebee, felt, and curiosity."
    )
    parser.add_argument("--place", choices=tuple(PLACES))
    parser.add_argument("--mystery", choices=tuple(MYSTERIES))
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None)
    mystery = getattr(args, "mystery", None)

    if place is not None and place not in PLACES:
        raise StoryError(f"Unknown setting: {place!r}.")
    if mystery is not None and mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {mystery!r}.")

    if place is not None and mystery is not None:
        if not _compatible(place, mystery):
            title = MYSTERIES[mystery]["title"]
            raise StoryError(
                f"{PLACES[place]['display'].capitalize()} lacks the materials "
                f"needed for {title}."
            )
    elif place is not None:
        choices = [name for name in MYSTERIES if _compatible(place, name)]
        if not choices:
            raise StoryError(f"No mystery is possible in {PLACES[place]['display']}.")
        mystery = rng.choice(choices)
    elif mystery is not None:
        choices = [name for name in PLACES if _compatible(name, mystery)]
        if not choices:
            raise StoryError(f"No setting has the materials for {MYSTERIES[mystery]['title']}.")
        place = rng.choice(choices)
    else:
        place, mystery = rng.choice(sorted(compatibility_pairs()))

    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    mood = getattr(args, "mood", None) or rng.choice(MOODS)

    if companion not in COMPANIONS:
        raise StoryError(f"Unknown companion: {companion!r}.")
    if mood not in MOODS:
        raise StoryError(f"Unknown mood: {mood!r}.")

    return StoryParams(
        place=place,
        mystery=mystery,
        companion=companion,
        mood=mood,
        seed=None,
    )


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    identity = "|".join(
        (params.place, params.mystery, params.companion, params.mood)
    )
    digest = hashlib.blake2b(identity.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def _validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown setting: {params.place!r}.")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery!r}.")
    if not _compatible(params.place, params.mystery):
        title = MYSTERIES[params.mystery]["title"]
        raise StoryError(
            f"{PLACES[params.place]['display'].capitalize()} lacks the materials "
            f"needed for {title}."
        )
    if params.companion not in COMPANIONS:
        raise StoryError(f"Unknown companion: {params.companion!r}.")
    if params.mood not in MOODS:
        raise StoryError(f"Unknown mood: {params.mood!r}.")


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    rng = random.Random(_story_seed(params))
    place_meta = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    companion = params.companion

    world = World(place=place_meta["display"])
    beebee = Entity(
        id="Beebee",
        kind="character",
        type="felt_bee",
        label="little felt bee",
        location=place_meta["display"],
        meters={"energy": 1.0, "distance_to_clue": 3.0, "wing_quiver": 0.1},
        memes={"curiosity": 0.8, "confidence": 0.25, "worry": 0.2},
    )
    helper = Entity(
        id=companion,
        kind="character",
        type="child_helper",
        label="Beebee's companion",
        location=place_meta["display"],
        meters={"energy": 1.0, "distance_to_clue": 3.0},
        memes={"patience": 0.6, "worry": 0.25, "confidence": 0.3},
    )
    missing_item = Entity(
        id=mystery["item_id"],
        kind="prop",
        type="felt_clue_object",
        label=mystery["item_label"],
        location=mystery["hidden_location"],
        meters={"wear": 0.0},
        memes={"belongs_in_scene": 1.0, "safe": 1.0},
        visible=False,
    )
    setting = Entity(
        id="setting",
        kind="location",
        type="room",
        label=place_meta["display"],
        location=place_meta["display"],
        meters={"light": 0.8},
        memes={"welcoming": 1.0},
    )
    world.entities = {
        entity.id: entity for entity in (beebee, helper, missing_item, setting)
    }
    world.phase = "the object is missing"
    world.facts = {
        "setting": params.place,
        "mystery": params.mystery,
        "status": "missing",
        "item": mystery["item_label"],
        "hidden_location": mystery["hidden_location"],
        "cause": mystery["deduction"],
        "feature": "curiosity",
    }
    world.trace.append(f"noticed_missing:{mystery['item_label']}")

    world.say(place_meta["description"])
    world.say(rng.choice(OPENING_BEATS))
    world.say(
        f"Beebee, a {params.mood} little bee sewn from soft felt, was helping "
        f"{companion} prepare {mystery['activity']}."
    )
    world.say(mystery["opening"])
    world.say(
        "A small mystery had begun. Curiosity tugged at Beebee more strongly "
        "than worry."
    )

    world.para()
    world.say(f'"Maybe someone took it!" {companion} whispered.')
    world.say(
        '"Let us look for clues before we decide," Beebee replied. '
        "The little bee began with what was actually in front of them."
    )
    beebee.memes["worry"] = 0.1
    beebee.memes["curiosity"] = 0.95
    helper.memes["patience"] = 0.8
    world.trace.append("paused_before_blame:the_first_guess_was_not_evidence")
    world.say(f"They checked the room gently. {mystery['clue']}")

    world.para()
    world.say(f'"{mystery["turn_question"]}" {companion} said.')
    world.say(f'"{mystery["turn_reply"]}" Beebee answered.')
    world.facts["clue_observed"] = mystery["clue"]
    world.trace.append(f"clue_observed:{mystery['clue']}")
    beebee.location = "beside the clue"
    helper.location = "beside the clue"
    beebee.meters["distance_to_clue"] = 0.3
    beebee.meters["wing_quiver"] = 0.0
    beebee.memes["confidence"] = 0.7
    helper.memes["confidence"] = 0.65
    world.phase = "the clue points to a hiding place"
    world.say(f"Then the pieces fit: {mystery['deduction']}.")
    world.trace.append(f"deduced:{mystery['deduction']}")
    world.facts["deduction"] = mystery["deduction"]

    world.para()
    world.say(mystery["search_action"].format(companion=companion))
    missing_item.visible = True
    missing_item.location = mystery["final_location"]
    missing_item.memes["found"] = 1.0
    world.facts["status"] = "found"
    world.phase = "the missing object is found"
    world.trace.append(f"found:{mystery['item_label']}:{mystery['hidden_location']}")

    world.say(mystery["repair_action"])
    world.say(mystery["outcome"])
    world.say(rng.choice(REFLECTIONS))
    world.say(f"Beebee had learned something useful: {mystery['lesson']}")
    world.say(mystery["ending"])

    beebee.meters["energy"] = 0.8
    beebee.memes["confidence"] = 0.95
    beebee.memes["worry"] = 0.0
    beebee.memes["care"] = 0.8
    helper.memes["confidence"] = 0.9
    helper.memes["worry"] = 0.0
    world.facts["status"] = "resolved"
    world.facts["resolution"] = mystery["outcome"]
    world.facts["lesson"] = mystery["lesson"]
    world.phase = "the object is safe and the mystery is solved"
    world.trace.append(f"secured:{mystery['item_label']}:{mystery['final_location']}")
    world.trace.append("resolved:the clue changed what the friends believed")

    prompts = [
        (
            f"Tell a child-friendly mystery called '{mystery['title']}' in "
            f"{place_meta['display']}, where Beebee investigates a missing felt object."
        ),
        (
            f"Show how Beebee and {companion} use Curiosity and a real clue instead "
            "of blaming someone."
        ),
        (
            "Write a gentle ending that shows where the missing object is found "
            "and how the friends keep it safe."
        ),
    ]

    story_qa = [
        QAItem(
            question="What was missing at the beginning of the mystery?",
            answer=mystery["answer_missing"],
        ),
        QAItem(
            question="Which clue helped Beebee and the companion decide where to look?",
            answer=(
                f"They noticed that {mystery['clue'][0].lower()}"
                f"{mystery['clue'][1:]} That clue pointed them toward a hiding place."
            ),
        ),
        QAItem(
            question="What did Beebee discover had happened?",
            answer=f"They discovered that {mystery['deduction']}.",
        ),
        QAItem(
            question="How did Beebee and the companion solve the mystery?",
            answer=mystery["answer_resolution"],
        ),
        QAItem(
            question="How did Curiosity help Beebee?",
            answer=(
                "Curiosity encouraged Beebee to look for evidence before deciding "
                "that someone had taken the missing object."
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is felt?",
            answer=(
                "Felt is a soft cloth made from fibers pressed together, so it "
                "does not unravel like many woven fabrics."
            ),
        ),
        QAItem(
            question="What does curiosity mean?",
            answer=(
                "Curiosity is a wish to learn or find out more, often by asking "
                "questions and looking carefully."
            ),
        ),
        QAItem(
            question="Why did Beebee look for a clue before blaming anyone?",
            answer=(
                "A clue can show what really happened, while a quick guess may "
                "unfairly blame someone."
            ),
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
blocked(P, M) :- requires(M, R), setting(P), not has(P, R).
compatible(P, M) :- setting(P), mystery(M), not blocked(P, M).
compatible_story(P, M) :- compatible(P, M), feature(curiosity).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place, metadata in PLACES.items():
        place_term = place.replace(" ", "_")
        lines.append(asp.fact("setting", place_term))
        for resource in sorted(metadata["resources"]):
            lines.append(asp.fact("has", place_term, resource))
    for mystery, metadata in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery))
        for requirement in sorted(metadata["requirements"]):
            lines.append(asp.fact("requires", mystery, requirement))
    for feature in FEATURES:
        lines.append(asp.fact("feature", feature))
    return "\n".join(lines)


def asp_program(show: str = "#show compatible_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatibilities() -> set[tuple[str, str]]:
    import asp

    symbols = asp.one_model(asp_program("#show compatible/2."))
    return set(asp.atoms(symbols, "compatible"))


def _verify_generated_stories() -> tuple[bool, str]:
    checks = (
        StoryParams("sunlit sewing room", "quilt_star", "Mira", "patient", 17),
        StoryParams("puppet nook", "hidden_bell", "Rowan", "bright-eyed", 23),
        StoryParams("story corner", "leaf_heart", "Kit", "thoughtful", 31),
        StoryParams("attic playroom", "quilt_star", "Nell", "eager", 41),
    )
    for params in checks:
        sample = generate(params)
        if not all(word in sample.story for word in ("Beebee", "felt", "Curiosity")):
            return False, f"required story detail missing for {params.mystery}"
        if sample.story.count('"') < 4:
            return False, f"spoken back-and-forth missing for {params.mystery}"
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
            return False, f"questions or answers missing for {params.mystery}"
        if any("{" in answer or "}" in answer for item in sample.story_qa for answer in (item.answer,)):
            return False, f"unresolved text in story answers for {params.mystery}"
        if params.mystery in sample.story:
            return False, f"internal mystery key leaked into story for {params.mystery}"
        if sample.world is None or sample.world.facts.get("status") != "resolved":
            return False, f"world state did not resolve for {params.mystery}"
    return True, "generated stories include dialogue, grounded answers, and resolved world state"


def asp_verify() -> int:
    import asp

    python_pairs = {
        (place.replace(" ", "_"), mystery)
        for place, mystery in compatibility_pairs()
    }
    symbols = asp.one_model(
        asp_program(
            "#show compatible/2.\n"
            "#show compatible_story/2.\n"
            "#show feature/1."
        )
    )
    clingo_pairs = set(asp.atoms(symbols, "compatible"))
    clingo_story_pairs = set(asp.atoms(symbols, "compatible_story"))
    clingo_features = set(asp.atoms(symbols, "feature"))

    if (
        python_pairs != clingo_pairs
        or python_pairs != clingo_story_pairs
        or clingo_features != {(feature,) for feature in FEATURES}
    ):
        print("MISMATCH between Python reasoning and ASP rules.")
        print("Only in Python:", sorted(python_pairs - clingo_pairs))
        print("Only in ASP:", sorted(clingo_pairs - python_pairs))
        print("Story compatibility mismatch:", sorted(clingo_story_pairs ^ python_pairs))
        print("ASP features:", sorted(clingo_features))
        return 1

    stories_ok, message = _verify_generated_stories()
    if not stories_ok:
        print(f"STORY CHECK FAILED: {message}")
        return 1

    print(
        f"OK: ASP and Python agree on {len(python_pairs)} compatible setting/mystery pairs."
    )
    print(f"OK: {message}.")
    return 0


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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            details = [f"label={entity.label}", f"location={entity.location}"]
            if entity.carried_by:
                details.append(f"carried_by={entity.carried_by}")
            if entity.visible is not True:
                details.append("visible=False")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.kind}/{entity.type} {' '.join(details)}")
        for event in sample.world.trace:
            print(f"  event: {event}")
        print(f"  phase: {sample.world.phase}")

    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = (
    StoryParams("sunlit sewing room", "quilt_star", "Mira", "patient"),
    StoryParams("puppet nook", "hidden_bell", "Rowan", "bright-eyed"),
    StoryParams("story corner", "leaf_heart", "Kit", "thoughtful"),
    StoryParams("attic playroom", "leaf_heart", "Nell", "eager"),
)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        try:
            sys.exit(asp_verify())
        except ImportError as exc:
            print(f"ASP verification requires clingo: {exc}", file=sys.stderr)
            sys.exit(2)

    if args.asp:
        try:
            import asp

            symbols = asp.one_model(
                asp_program(
                    "#show compatible/2.\n"
                    "#show compatible_story/2."
                )
            )
            print("Compatible setting/mystery pairs:")
            for pair in sorted(asp.atoms(symbols, "compatible")):
                print(f"  {pair[0]}: {MYSTERIES[pair[1]]['title']}")
            print("Curiosity-enabled stories:")
            for pair in sorted(asp.atoms(symbols, "compatible_story")):
                print(f"  {pair[0]}: {MYSTERIES[pair[1]]['title']}")
        except ImportError as exc:
            print(f"ASP mode requires clingo: {exc}", file=sys.stderr)
            sys.exit(2)
        return

    if args.n < 1:
        print("error: -n must be a positive number.", file=sys.stderr)
        sys.exit(2)

    base_seed = (
        args.seed
        if args.seed is not None
        else random.SystemRandom().randrange(0, 2**32)
    )

    try:
        if args.all:
            samples = []
            for index, curated in enumerate(CURATED):
                params = StoryParams(
                    place=curated.place,
                    mystery=curated.mystery,
                    companion=curated.companion,
                    mood=curated.mood,
                    seed=base_seed + index,
                )
                samples.append(generate(params))
        else:
            samples = []
            for index in range(args.n):
                params = resolve_params(
                    args,
                    random.Random(base_seed + index * 7919),
                )
                params.seed = base_seed + index
                samples.append(generate(params))
    except StoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

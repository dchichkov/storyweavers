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


_here = os.path.abspath(os.path.dirname(__file__))
_root = _here
while not os.path.isfile(os.path.join(_root, "storyworlds", "results.py")):
    _parent = os.path.dirname(_root)
    if _parent == _root:
        raise ImportError("Could not find storyworlds/results.py")
    _root = _parent
sys.path.insert(0, _root)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


CHILD_NAMES = ("Isla", "Fiona", "Skye", "Eilidh", "Aileen", "Niamh")
SIBLING_NAMES = ("Rory", "Callum", "Finlay", "Ewan", "Hamish", "Fraser")
AUNT_NAMES = ("Mairi", "Morag", "Iona", "Ailsa", "Nessa")
SETTINGS = (
    "a snug cottage in the Scottish Highlands",
    "a whitewashed croft on the Isle of Skye",
    "a small stone house near Loch Lomond",
)

SOUND_CASES: dict[str, dict[str, str]] = {
    "window_latch": {
        "effect": "Rrrrr-rrr... tik-tik!",
        "child_line": "That parcel is purring! Could a kitten be inside?",
        "misread": "a kitten purring inside the parcel",
        "source_id": "loose_window_latch",
        "source_type": "window_latch",
        "source_label": "the loose window latch",
        "observation": (
            "A gust shook the loose window latch against its frame—"
            "Rrrrr-rrr... tik-tik!—while the parcel stayed perfectly still."
        ),
        "source_explanation": (
            "The loose window latch rattled against its frame in the wind; "
            "the parcel stayed still."
        ),
        "belief_release": (
            "That was the window latch, not a kitten in the parcel."
        ),
        "clue_tag": "latch_rattle",
    },
    "rain_spout": {
        "effect": "Pitter-patter... ka-thunk!",
        "child_line": "Someone is knocking from inside! What if they need help?",
        "misread": "someone knocking from inside the parcel",
        "source_id": "loose_rain_spout",
        "source_type": "rain_spout",
        "source_label": "a loose rain spout",
        "observation": (
            "Rain ran through a loose metal spout and made it tap the wall—"
            "pitter-patter... ka-thunk!—while the parcel did not move."
        ),
        "source_explanation": (
            "Rain made a loose metal spout tap against the wall; nobody was "
            "knocking inside the parcel."
        ),
        "belief_release": (
            "That knocking came from the rain spout, not from inside the parcel."
        ),
        "clue_tag": "rain_spout_tapping",
    },
    "rowan_branch": {
        "effect": "Skritch... skritch... tap!",
        "child_line": "Something is scratching inside the parcel!",
        "misread": "a small creature scratching inside the parcel",
        "source_id": "rowan_branch",
        "source_type": "branch",
        "source_label": "a bare rowan branch",
        "observation": (
            "A bare rowan branch brushed the cottage wall—"
            "skritch... skritch... tap!—with each gust, while the parcel stayed quiet."
        ),
        "source_explanation": (
            "A bare rowan branch brushed the stone wall in the gusts; "
            "the parcel was still."
        ),
        "belief_release": (
            "That scratching was the rowan branch outside, not a creature in the parcel."
        ),
        "clue_tag": "branch_scrape",
    },
}

FEATURES = ("misunderstanding", "sound_effects", "conflict")
STYLE = "bedtime_story"

PARAMETER_REGISTRIES = {
    "child_name": CHILD_NAMES,
    "sibling_name": SIBLING_NAMES,
    "aunt_name": AUNT_NAMES,
    "setting": SETTINGS,
    "sound_case": tuple(SOUND_CASES),
}


@dataclass
class StoryParams:
    child_name: str = "Isla"
    sibling_name: str = "Rory"
    aunt_name: str = "Mairi"
    setting: str = SETTINGS[0]
    sound_case: Optional[str] = None
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {
                "subject": "they",
                "object": "them",
                "possessive": "their",
            }[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class WorldState:
    phase: str = "evening"
    parcel_sealed: bool = True
    misunderstanding_active: bool = False
    conflict_active: bool = False
    clue_found: bool = False
    source_identified: bool = False
    gift_revealed: bool = False
    resolved: bool = False


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.state = WorldState()
        self.facts: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        if entity.id in self.entities:
            raise StoryError(f"Duplicate world entity: {entity.id}")
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def reasonableness_gate(params: StoryParams) -> bool:
    """Reject explicit choices that cannot describe this small story world."""
    if not isinstance(params, StoryParams):
        raise StoryError("Expected StoryParams for a Scottish parcel bedtime story.")
    for field_name in ("child_name", "sibling_name", "aunt_name", "setting"):
        value = getattr(params, field_name)
        choices = PARAMETER_REGISTRIES[field_name]
        if value not in choices:
            raise StoryError(
                f"Unknown {field_name.replace('_', ' ')} {value!r}; "
                f"choose one of: {', '.join(choices)}."
            )
    if params.child_name == params.sibling_name:
        raise StoryError("The child and sibling must have different names.")
    if params.aunt_name in (params.child_name, params.sibling_name):
        raise StoryError("The aunt must have a different name from both children.")
    if params.sound_case is not None:
        if params.sound_case not in SOUND_CASES:
            raise StoryError(
                f"Unknown sound case {params.sound_case!r}; "
                f"choose one of: {', '.join(SOUND_CASES)}."
            )
        if not _case_is_reasonable(SOUND_CASES[params.sound_case]):
            raise StoryError(
                f"Sound case {params.sound_case!r} has no clear clue or safe resolution."
            )
    if params.seed is not None and (
        not isinstance(params.seed, int) or isinstance(params.seed, bool)
    ):
        raise StoryError("The seed must be an integer.")
    return True


def _case_is_reasonable(case: dict[str, str]) -> bool:
    required = (
        "effect",
        "child_line",
        "misread",
        "source_id",
        "source_type",
        "source_label",
        "observation",
        "source_explanation",
        "belief_release",
        "clue_tag",
    )
    return all(isinstance(case.get(key), str) and case[key].strip() for key in required)


def _select_case(params: StoryParams) -> tuple[str, dict[str, str]]:
    if params.sound_case is not None:
        key = params.sound_case
    elif params.seed is not None:
        key = tuple(SOUND_CASES)[params.seed % len(SOUND_CASES)]
    else:
        stable = "|".join(
            (
                params.child_name,
                params.sibling_name,
                params.aunt_name,
                params.setting,
            )
        )
        digest = hashlib.sha256(stable.encode("utf-8")).digest()
        key = tuple(SOUND_CASES)[int.from_bytes(digest[:8], "big") % len(SOUND_CASES)]
    return key, SOUND_CASES[key]


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    case_key, case = _select_case(params)
    child_name = params.child_name
    sibling_name = params.sibling_name
    aunt_name = params.aunt_name
    world = World(params)

    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type="child",
            label="child in pajamas",
            location="bedroom",
            meters={"energy": 0.38, "hands_steady": 0.65},
            memes={"worry": 0.68, "curiosity": 0.72, "trust": 0.55},
        )
    )
    sibling = world.add(
        Entity(
            id=sibling_name,
            kind="character",
            type="sibling",
            label="child's sibling",
            location="bedroom",
            meters={"energy": 0.4, "hands_steady": 0.72},
            memes={"frustration": 0.48, "confidence": 0.62, "trust": 0.58},
        )
    )
    gran = world.add(
        Entity(
            id="Gran",
            kind="character",
            type="grandmother",
            label="their grandmother",
            location="kitchen",
            meters={"energy": 0.55, "steadiness": 0.9},
            memes={"calm": 0.9, "affection": 0.9},
        )
    )
    parcel = world.add(
        Entity(
            id="parcel",
            kind="object",
            type="parcel",
            label="wrapped bedtime parcel",
            owner=f"{child_name} and {sibling_name}",
            location="rug beside the window",
            meters={"sealed": 1.0, "dry": 1.0, "near_window": 1.0},
            memes={"mystery": 0.9},
        )
    )
    source = world.add(
        Entity(
            id=case["source_id"],
            kind="object",
            type=case["source_type"],
            label=case["source_label"],
            location="outside the bedroom window",
            meters={"active": 1.0, "audible_inside": 1.0, "observed": 0.0},
            memes={"startling": 0.4},
        )
    )
    weather = world.add(
        Entity(
            id="night_wind",
            kind="environment",
            type="weather",
            label="wind and rain around the cottage",
            location="outside",
            meters={"wind": 0.7, "rain": 0.5},
            memes={"restless": 0.3},
        )
    )
    lamb = world.add(
        Entity(
            id="wooden_lamb",
            kind="object",
            type="bedtime_gift",
            label="carved wooden lamb with a bell and music box",
            owner=f"Auntie {aunt_name}",
            location="inside parcel",
            meters={"inside_parcel": 1.0, "music_playing": 0.0},
            memes={"comfort": 0.0},
        )
    )
    window = world.add(
        Entity(
            id="bedroom_window",
            kind="object",
            type="window",
            label="bedroom window",
            location="bedroom",
            meters={"closed": 0.0, "secured": 0.0},
            memes={"rattling": 0.0},
        )
    )

    world.state.phase = "parcel_arrives_at_bedtime"
    world.state.misunderstanding_active = True
    world.state.conflict_active = True
    world.events.append("The children hear an unfamiliar sound near the wrapped parcel.")
    child.memes["worry"] = 0.82
    sibling.memes["frustration"] = 0.63

    world.say(
        f"At bedtime in {params.setting}, {child_name} and {sibling_name} "
        "were already in their pajamas."
    )
    world.say(
        f"A parcel from Auntie {aunt_name} rested on the rug beside the window, "
        f"with both children's names on its tag."
    )
    world.say(
        f"The wind sighed around the roof. A strange sound seemed to slip from "
        f"the parcel's side: {case['effect']}"
    )

    world.para()
    child_line = case["child_line"]
    world.say(f'{child_name} hugged the blanket. "{child_line}"')
    world.say(
        f'{sibling_name} kept their hands away from the wrapping. '
        '"Maybe the storm is making that sound. Please do not tear the paper yet."'
    )
    world.say(
        f'"But what if something needs our help?" {child_name} asked. '
        f'"Let us listen before we decide," {sibling_name} replied.'
    )

    world.para()
    world.state.phase = "careful_listening"
    world.events.append("The siblings keep the parcel still and wait for another gust.")
    world.say(
        f'{sibling_name} whispered, "Let us keep the parcel still and listen '
        "when the wind comes again.\""
    )
    world.say(case["observation"])
    source.meters["observed"] = 1.0
    child.memes["worry"] = 0.24
    sibling.memes["frustration"] = 0.18
    sibling.memes["confidence"] = 0.35
    child.memes["trust"] = 0.82
    sibling.memes["trust"] = 0.86
    world.state.clue_found = True
    world.state.source_identified = True
    world.state.misunderstanding_active = False
    world.state.conflict_active = False
    world.events.append("The repeated sound matches the outdoor source, not the still parcel.")
    world.say(f'{child_name} lowered their hands from the ribbon. "{case["belief_release"]}"')
    world.say(
        f'"I only guessed it was the storm," {sibling_name} said. '
        '"We found out by listening together. Let us ask Gran to help us open it."'
    )

    world.para()
    world.state.phase = "gran_checks_the_parcel"
    gran.location = "bedroom"
    world.events.append("Gran checks the parcel label and helps the children open it.")
    world.say(
        "They called Gran from the kitchen. She came in wearing a soft tartan shawl "
        "and read the label by the bedside lamp."
    )
    world.say(
        f'"Auntie {aunt_name} sent this to both of you," Gran said. '
        '"You were kind to worry. Let us untie it gently together."'
    )
    world.say(
        "They loosened the ribbon instead of tearing the paper. Inside lay a "
        "hand-carved wooden lamb with a tiny silver bell and a little wind-up music box."
    )
    world.say(
        "The bell gave a bright ting! as Gran lifted the lamb. A folded note read, "
        f'"For my two night owls: turn the key once and let the lamb sing you to sleep. '
        f'Love, Auntie {aunt_name}."'
    )
    parcel.meters["sealed"] = 0.0
    parcel.location = "bedroom floor, beside the open wrapping"
    parcel.memes["mystery"] = 0.0
    lamb.location = "beside the bedside lamp"
    lamb.meters["inside_parcel"] = 0.0
    lamb.meters["music_playing"] = 1.0
    lamb.memes["comfort"] = 0.92
    world.state.parcel_sealed = False
    world.state.gift_revealed = True

    world.para()
    world.state.phase = "settled_for_sleep"
    window.meters["closed"] = 1.0
    window.meters["secured"] = 1.0
    window.memes["rattling"] = 0.0
    source.meters["audible_inside"] = 0.0
    weather.memes["restless"] = 0.1
    child.memes["worry"] = 0.06
    sibling.memes["frustration"] = 0.03
    child.memes["trust"] = 0.96
    sibling.memes["trust"] = 0.96
    child.meters["energy"] = 0.2
    sibling.meters["energy"] = 0.2
    lamb.meters["music_playing"] = 0.0
    world.state.resolved = True
    world.events.append("The window is secured, the parcel is open, and the children settle together.")
    world.say(
        f'"I am sorry I was ready to pull the ribbon," {child_name} admitted. '
        f'"And I am sorry I guessed before we checked," {sibling_name} replied. '
        '"Listening together was better."'
    )
    world.say(
        "Gran secured the window, and the storm softened to a hush behind the glass. "
        "The wooden lamb rested beside the neatly looped ribbon on the bedside table."
    )
    world.say(
        "Its last music-box note drifted into the quiet Scottish night as the two "
        "children closed their eyes, no longer arguing about the sound."
    )

    world.facts = {
        "case_key": case_key,
        "initial_sound": case["effect"],
        "initial_belief": case["misread"],
        "source_label": case["source_label"],
        "source_explanation": case["source_explanation"],
        "observation": case["observation"],
        "gift_description": (
            "a hand-carved wooden lamb with a tiny silver bell and a little wind-up music box"
        ),
        "resolution": (
            "They kept the parcel still, listened for the sound again, and found its "
            "outdoor source before asking Gran to help them open the gift gently."
        ),
        "ending_image": (
            "The wooden lamb rested beside the neatly looped ribbon while its last "
            "music-box note faded into the quiet Scottish night."
        ),
        "child": child,
        "sibling": sibling,
        "gran": gran,
        "parcel": parcel,
        "source": source,
        "weather": weather,
        "lamb": lamb,
        "window": window,
    }
    return world


def generate_prompts(world: World) -> list[str]:
    child = world.params.child_name
    sibling = world.params.sibling_name
    return [
        "Write a gentle Scottish bedtime story about a mysterious parcel, a sound-based misunderstanding, and two children who learn to listen together.",
        f"Tell a cozy bedtime tale in which {child} and {sibling} disagree about a strange sound, investigate it carefully, and make peace.",
        "Use clear sound effects, warm dialogue, a helpful family member, and a quiet ending that shows what changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    child = world.params.child_name
    sibling = world.params.sibling_name
    aunt = world.params.aunt_name
    return [
        QAItem(
            question=f"What did {child} first think the strange sound meant?",
            answer=(
                f"At first, {child} thought it might be {facts['initial_belief']}. "
                f"{facts['source_explanation']}"
            ),
        ),
        QAItem(
            question=f"How did {child} and {sibling} discover where the sound came from?",
            answer=(
                f"They kept the parcel still and listened when the wind came again. "
                f"{facts['observation']} That helped them understand that the sound "
                "was not coming from inside the wrapping."
            ),
        ),
        QAItem(
            question=f"What did Auntie {aunt} send in the parcel?",
            answer=(
                f"Auntie {aunt} sent {facts['gift_description']}. The children opened "
                "it gently with Gran's help and listened to its bedtime tune."
            ),
        ),
        QAItem(
            question=f"How did {child} and {sibling} settle their disagreement?",
            answer=(
                f"{facts['resolution']} They both apologized for guessing too quickly, "
                "then settled beside the lamb as its music faded."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parcel?",
            answer=(
                "A parcel is a package wrapped or boxed so it can be carried or sent "
                "from one person to another."
            ),
        ),
        QAItem(
            question="Why can listening carefully help when something sounds strange?",
            answer=(
                "Listening carefully can help someone notice when a sound repeats "
                "along with another event, such as a gust of wind. That clue may show "
                "where the sound really comes from."
            ),
        ),
        QAItem(
            question="What is a bedtime story?",
            answer=(
                "A bedtime story is a tale shared near sleep, often with a gentle "
                "ending that helps listeners feel calm and safe."
            ),
        ),
        QAItem(
            question="What does Scottish mean in this story?",
            answer=(
                "Scottish means connected with Scotland. The cottage, names, tartan "
                "shawl, and quiet Highland night give the story its Scottish setting."
            ),
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- simulated world state ---"]
    lines.append(f"  setting={world.params.setting!r}")
    lines.append(f"  phase={world.state.phase}")
    lines.append(f"  parcel_sealed={world.state.parcel_sealed}")
    lines.append(f"  misunderstanding_active={world.state.misunderstanding_active}")
    lines.append(f"  conflict_active={world.state.conflict_active}")
    lines.append(f"  clue_found={world.state.clue_found}")
    lines.append(f"  source_identified={world.state.source_identified}")
    lines.append(f"  gift_revealed={world.state.gift_revealed}")
    lines.append(f"  resolved={world.state.resolved}")
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:20} ({entity.type:14}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append("  event trail:")
    lines.extend(f"    - {event}" for event in world.events)
    return "\n".join(lines)


ASP_RULES = r"""
% A registered sound case is reasonable when it has a sound, a mistaken
% interpretation, an observable clue, a safe choice, and a gentle ending.
well_formed_case(C) :-
    sound_case(C),
    sound_effect(C),
    mistaken_source(C),
    evidence(C),
    safe_choice(C),
    gentle_ending(C).

valid_case(C) :-
    well_formed_case(C),
    feature(misunderstanding),
    feature(sound_effects),
    feature(conflict),
    style(bedtime_story).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    rows = [
        asp.fact("style", STYLE),
        *(asp.fact("feature", feature) for feature in FEATURES),
    ]
    for key, case in SOUND_CASES.items():
        rows.extend(
            (
                asp.fact("sound_case", key),
                asp.fact("sound_effect", key),
                asp.fact("mistaken_source", key),
                asp.fact("evidence", key, case["clue_tag"]),
                asp.fact("safe_choice", key),
                asp.fact("gentle_ending", key),
            )
        )
    return "\n".join(rows)


def asp_program(show: str = "#show valid_case/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible_cases() -> set[str]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    return {str(args[0]) for args in asp.atoms(model, "valid_case")}


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp  # noqa: F401
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    python_cases = {
        key for key, case in SOUND_CASES.items() if _case_is_reasonable(case)
    }
    try:
        asp_cases = asp_compatible_cases()
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1

    if asp_cases != python_cases:
        print(
            "MISMATCH: ASP/Python case parity differs "
            f"(ASP={sorted(asp_cases)}, Python={sorted(python_cases)})."
        )
        return 1

    for index, key in enumerate(sorted(python_cases)):
        params = StoryParams(
            child_name="Isla",
            sibling_name="Rory",
            aunt_name="Mairi",
            setting=SETTINGS[index % len(SETTINGS)],
            sound_case=key,
            seed=100 + index,
        )
        try:
            sample = generate(params)
        except StoryError as exc:
            print(f"MISMATCH: Python rejected registered case {key}: {exc}")
            return 1
        world = sample.world
        if (
            world is None
            or not world.state.resolved
            or world.state.conflict_active
            or world.state.misunderstanding_active
            or not world.state.clue_found
            or not world.state.gift_revealed
            or world.state.parcel_sealed
            or len(sample.story.split()) < 100
            or sample.story.count('"') < 6
            or "parcel" not in sample.story.lower()
            or not sample.story_qa
        ):
            print(f"MISMATCH: generated story for {key} failed its story-state checks.")
            return 1

    invalid = StoryParams(
        child_name="Isla",
        sibling_name="Isla",
        aunt_name="Mairi",
        setting=SETTINGS[0],
        sound_case=next(iter(SOUND_CASES)),
    )
    try:
        reasonableness_gate(invalid)
    except StoryError:
        pass
    else:
        print("MISMATCH: Python accepted a story with the same child and sibling.")
        return 1

    print(
        f"OK: ASP/Python parity holds for {len(python_cases)} sound cases; "
        "generated stories resolve their misunderstandings and conflicts."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Scottish bedtime parcel story about listening, sound, and making peace."
    )
    parser.add_argument("--child-name")
    parser.add_argument("--sibling-name")
    parser.add_argument("--aunt-name")
    parser.add_argument("--setting")
    parser.add_argument("--sound-case")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    sibling_choices = tuple(name for name in SIBLING_NAMES if name != child_name)
    sibling_name = args.sibling_name or rng.choice(sibling_choices)
    aunt_name = args.aunt_name or rng.choice(AUNT_NAMES)
    params = StoryParams(
        child_name=child_name,
        sibling_name=sibling_name,
        aunt_name=aunt_name,
        setting=args.setting or rng.choice(SETTINGS),
        sound_case=args.sound_case,
        seed=args.seed,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    if not (
        world.state.resolved
        and world.state.clue_found
        and world.state.gift_revealed
        and not world.state.conflict_active
        and not world.state.misunderstanding_active
        and not world.state.parcel_sealed
    ):
        raise StoryError("The parcel story did not reach a safe, resolved bedtime ending.")
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(("", "== (2) Story questions =="))
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(("", "== (3) World-knowledge questions =="))
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _curated_samples() -> list[StoryParams]:
    return [
        StoryParams(
            "Isla",
            "Rory",
            "Mairi",
            SETTINGS[0],
            "window_latch",
            1,
        ),
        StoryParams(
            "Fiona",
            "Callum",
            "Morag",
            SETTINGS[1],
            "rain_spout",
            2,
        ),
        StoryParams(
            "Skye",
            "Finlay",
            "Ailsa",
            SETTINGS[2],
            "rowan_branch",
            3,
        ),
    ]


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.show_asp:
            print(asp_program())
            return
        if args.verify:
            raise SystemExit(asp_verify())
        if args.asp:
            try:
                compatible = sorted(asp_compatible_cases())
            except Exception as exc:
                print(f"ASP unavailable: {exc}", file=sys.stderr)
                raise SystemExit(1)
            print(
                f"{len(compatible)} compatible Scottish bedtime parcel patterns: "
                + ", ".join(compatible)
            )
            return
        if args.n < 1 and not args.all:
            raise StoryError("The number of stories must be at least one.")

        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        if args.all:
            # Validate any explicit choices even though --all uses its curated set.
            resolve_params(args, random.Random(base_seed))
            samples = [generate(params) for params in _curated_samples()]
        else:
            samples = []
            for index in range(args.n):
                seed = base_seed + index
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                samples.append(generate(params))

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return

        for index, sample in enumerate(samples):
            header = (
                f"### variant {index + 1}"
                if len(samples) > 1 and not args.all
                else ""
            )
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()

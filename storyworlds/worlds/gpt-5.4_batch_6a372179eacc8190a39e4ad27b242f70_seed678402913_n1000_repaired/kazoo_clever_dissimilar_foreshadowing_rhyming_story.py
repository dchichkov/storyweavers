#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kazoo_clever_dissimilar_foreshadowing_rhyming_story.py
==================================================================================

A standalone storyworld about a clever kazoo trick that helps a very dissimilar
pair of friends find each other again when sight is blocked. The prose aims for
a gentle rhyming-story feel, and the world model includes an explicit
foreshadowing beat that later pays off.

Run it
------
    python storyworlds/worlds/gpt-5.4/kazoo_clever_dissimilar_foreshadowing_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/kazoo_clever_dissimilar_foreshadowing_rhyming_story.py --place meadow --pair mouse_moose --obstacle fog
    python storyworlds/worlds/gpt-5.4/kazoo_clever_dissimilar_foreshadowing_rhyming_story.py --obstacle waterfall
    python storyworlds/worlds/gpt-5.4/kazoo_clever_dissimilar_foreshadowing_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/kazoo_clever_dissimilar_foreshadowing_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/kazoo_clever_dissimilar_foreshadowing_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when this script is run directly:
# this file lives under storyworlds/worlds/gpt-5.4/, so go up three levels.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "ewe"}
        male = {"boy", "father", "ram"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.id


@dataclass
class Pairing:
    id: str
    small_name: str
    small_type: str
    small_noun: str
    big_name: str
    big_type: str
    big_noun: str
    bond_word: str
    snack: str
    tags: set[str] = field(default_factory=set)

    @property
    def dissimilar_line(self) -> str:
        return (
            f"{self.small_name} the {self.small_noun} and {self.big_name} the {self.big_noun} "
            f"were a dissimilar pair"
        )


@dataclass
class Place:
    id: str
    label: str
    path_label: str
    picnic: str
    detail: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    opener: str
    hides_sight: bool = False
    sound_clear: bool = False
    cue: str = ""
    drift: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tune:
    id: str
    pattern: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PAIRINGS = {
    "mouse_moose": Pairing(
        id="mouse_moose",
        small_name="Pip",
        small_type="mouse",
        small_noun="mouse",
        big_name="Moss",
        big_type="moose",
        big_noun="moose",
        bond_word="side by side",
        snack="a berry pie",
        tags={"friends", "size"},
    ),
    "wren_bear": Pairing(
        id="wren_bear",
        small_name="Wren",
        small_type="wren",
        small_noun="wren",
        big_name="Bram",
        big_type="bear",
        big_noun="bear",
        bond_word="wing by paw",
        snack="a honey bun",
        tags={"friends", "size"},
    ),
    "vole_pony": Pairing(
        id="vole_pony",
        small_name="Dot",
        small_type="vole",
        small_noun="vole",
        big_name="Clover",
        big_type="pony",
        big_noun="pony",
        bond_word="step by clip-clop step",
        snack="an apple tart",
        tags={"friends", "size"},
    ),
}

PLACES = {
    "meadow": Place(
        id="meadow",
        label="the moonlit meadow",
        path_label="the clover path",
        picnic="the hilltop lantern picnic",
        detail="Fireflies bobbed above the grass, and little silver seeds floated past.",
        affords={"fog", "grass"},
        tags={"meadow"},
    ),
    "riverside": Place(
        id="riverside",
        label="the riverside lane",
        path_label="the pebble path",
        picnic="the willow-light picnic",
        detail="The river gave a sleepy gleam, and reeds leaned over the ribboned stream.",
        affords={"fog", "reeds"},
        tags={"river"},
    ),
    "grove": Place(
        id="grove",
        label="the lantern grove",
        path_label="the winding lantern path",
        picnic="the acorn-lamp picnic",
        detail="Round lanterns swung from branch to branch, and owls blinked softly as if at a dance.",
        affords={"fog", "hedge"},
        tags={"grove"},
    ),
}

OBSTACLES = {
    "fog": Obstacle(
        id="fog",
        label="fog",
        opener="a gray fog came curling low",
        hides_sight=True,
        sound_clear=True,
        cue="If the world turns woolly and white, let the kazoo keep you in sight.",
        drift="The mist wrapped round their knees, then their noses, then the tips of their toes.",
        tags={"fog", "weather"},
    ),
    "reeds": Obstacle(
        id="reeds",
        label="tall reeds",
        opener="a stand of tall reeds swayed and crossed",
        hides_sight=True,
        sound_clear=True,
        cue="If the reeds hide every bend, let the kazoo call your friend.",
        drift="The reeds whispered shh-shh-shh and made green walls where the path had been.",
        tags={"reeds", "plants"},
    ),
    "hedge": Obstacle(
        id="hedge",
        label="a twisty hedge",
        opener="a twisty hedge turned the path in loops",
        hides_sight=True,
        sound_clear=True,
        cue="If the hedge makes corners too sly, let the kazoo answer back nearby.",
        drift="Leafy turns folded one over another until the little lane felt like a green puzzle.",
        tags={"hedge", "plants"},
    ),
    "waterfall": Obstacle(
        id="waterfall",
        label="a thundering waterfall",
        opener="a thundering waterfall roared beside the track",
        hides_sight=False,
        sound_clear=False,
        cue="",
        drift="Its crashing splash swallowed every small sound.",
        tags={"waterfall", "water"},
    ),
    "windmill": Obstacle(
        id="windmill",
        label="a clattering windmill lane",
        opener="the old windmill clacked and rattled",
        hides_sight=False,
        sound_clear=False,
        cue="",
        drift="The wooden wings went clack-clack-clack and stole the shape of every note.",
        tags={"windmill", "noise"},
    ),
}

TUNES = {
    "high_low": Tune(
        id="high_low",
        pattern="toot-tee, toot-tee, low then high",
        rhyme='"{0}! Here am I! Follow my song and do not cry!"',
        tags={"kazoo"},
    ),
    "pause_pop": Tune(
        id="pause_pop",
        pattern="buzz-buzz, pause, then a bright bazoo",
        rhyme='"{0}! This way through! Hear my kazoo and come on through!"',
        tags={"kazoo"},
    ),
    "round_trip": Tune(
        id="round_trip",
        pattern="a round little hum that hopped, then flew",
        rhyme='"{0}! It is true! I saved this tune for guiding you!"',
        tags={"kazoo"},
    ),
}


def obstacle_reasonable(place_id: str, obstacle_id: str) -> bool:
    place = PLACES[place_id]
    obstacle = OBSTACLES[obstacle_id]
    return obstacle_id in place.affords and obstacle.hides_sight and obstacle.sound_clear


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for pair_id in PAIRINGS:
            for obstacle_id in OBSTACLES:
                if obstacle_reasonable(place_id, obstacle_id):
                    combos.append((place_id, pair_id, obstacle_id))
    return combos


@dataclass
class StoryParams:
    place: str
    pair: str
    obstacle: str
    tune: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="meadow",
        pair="mouse_moose",
        obstacle="fog",
        tune="high_low",
        seed=101,
    ),
    StoryParams(
        place="riverside",
        pair="wren_bear",
        obstacle="reeds",
        tune="pause_pop",
        seed=102,
    ),
    StoryParams(
        place="grove",
        pair="vole_pony",
        obstacle="hedge",
        tune="round_trip",
        seed=103,
    ),
]


def explain_rejection(place_id: str, obstacle_id: str) -> str:
    place = PLACES[place_id]
    obstacle = OBSTACLES[obstacle_id]
    if obstacle_id not in place.affords:
        return (
            f"(No story: {obstacle.label} does not fit {place.label}. "
            f"Pick an obstacle that belongs there.)"
        )
    if not obstacle.hides_sight:
        return (
            f"(No story: {obstacle.label} does not block sight, so there is no need "
            f"for a clever kazoo guide.)"
        )
    if not obstacle.sound_clear:
        return (
            f"(No story: {obstacle.label} swallows small sounds, so a kazoo would not "
            f"be a reasonable fix there.)"
        )
    return "(No story: this combination is not reasonable.)"


def foreshadow(world: World, small: Entity, big: Entity, obstacle: Obstacle) -> None:
    small.memes["alert"] += 1
    world.say(
        f'Before they set off, {small.name} tapped the shiny kazoo and sang, "{obstacle.cue}"'
    )
    world.say(
        f"{big.name} smiled at the little tune. It sounded playful then, but soon it would matter."
    )
    world.facts["foreshadowed"] = True


def setup(world: World, pairing: Pairing, place: Place) -> tuple[Entity, Entity]:
    small = world.add(
        Entity(
            id=pairing.small_name,
            kind="character",
            type=pairing.small_type,
            label=pairing.small_noun,
            role="small_friend",
            traits=["clever", "small"],
            tags=set(pairing.tags),
        )
    )
    big = world.add(
        Entity(
            id=pairing.big_name,
            kind="character",
            type=pairing.big_type,
            label=pairing.big_noun,
            role="big_friend",
            traits=["kind", "large"],
            tags=set(pairing.tags),
        )
    )
    kazoo = world.add(
        Entity(
            id="kazoo",
            kind="thing",
            type="instrument",
            label="kazoo",
            phrase="a bright brass kazoo",
            role="tool",
            tags={"kazoo", "music"},
        )
    )
    basket = world.add(
        Entity(
            id="basket",
            kind="thing",
            type="basket",
            label="basket",
            phrase=f"a basket holding {pairing.snack}",
            role="cargo",
            tags={"picnic"},
        )
    )
    world.facts["kazoo"] = kazoo
    world.facts["basket"] = basket

    small.memes["joy"] += 1
    big.memes["joy"] += 1
    small.memes["trust"] += 1
    big.memes["trust"] += 1

    world.say(
        f"{pairing.dissimilar_line}, yet they laughed on {pairing.bond_word} and made one merry air."
    )
    world.say(
        f"They were trotting through {place.label} toward {place.picnic}. {place.detail}"
    )
    world.say(
        f"{small.name} carried {kazoo.phrase}, and {big.name} carried {basket.phrase}."
    )
    world.facts["contains_dissimilar"] = True
    return small, big


def trouble_starts(world: World, small: Entity, big: Entity, obstacle: Obstacle, place: Place) -> None:
    world.para()
    world.say(
        f"But on {place.path_label}, {obstacle.opener}. {obstacle.drift}"
    )
    small.meters["can_see_friend"] = 0.0
    big.meters["can_see_friend"] = 0.0
    small.meters["separated"] += 1
    big.meters["separated"] += 1
    small.memes["worry"] += 1
    big.memes["worry"] += 1
    world.say(
        f"{small.name} could not see {big.name}'s face, and {big.name} could not see {small.name}'s place."
    )


def drift_apart(world: World, small: Entity, big: Entity) -> None:
    small.meters["distance"] += 1
    big.meters["distance"] += 1
    world.say(
        f'One friend stepped left and one stepped right. "Oh dear," said {big.name}, "the path was plain a moment ago in lantern light."'
    )


def clever_kazoo(world: World, small: Entity, big: Entity, tune: Tune) -> None:
    world.para()
    small.memes["clever"] += 1
    world.get("kazoo").meters["played"] += 1
    world.say(
        f"Then clever {small.name} remembered the warning song. {small.pronoun('subject').capitalize()} lifted the kazoo and played {tune.pattern} all along."
    )
    world.say(tune.rhyme.format(big.name))
    big.meters["heard_kazoo"] += 1
    big.memes["hope"] += 1
    world.facts["used_kazoo"] = True


def reunite(world: World, small: Entity, big: Entity, place: Place) -> None:
    small.meters["distance"] = 0.0
    big.meters["distance"] = 0.0
    small.meters["can_see_friend"] = 1.0
    big.meters["can_see_friend"] = 1.0
    small.meters["separated"] = 0.0
    big.meters["separated"] = 0.0
    small.memes["relief"] += 1
    big.memes["relief"] += 1
    small.memes["joy"] += 1
    big.memes["joy"] += 1
    world.say(
        f"Soon {big.name} followed the humming clue until the gray grew thin and the dear friend grew true."
    )
    world.say(
        f"They found each other nose to knee and cheered, " + '"We are together, and together we will be!"'
    )
    world.para()
    world.say(
        f"So on they went to {place.picnic}, one with a kazoo, one with a basket, both with hearts bright through and through."
    )
    world.say(
        "That night the lanterns glowed like stars on blue, and the brave little tune floated warmly through."
    )
    world.facts["reunited"] = True


def tell(pairing: Pairing, place: Place, obstacle: Obstacle, tune: Tune) -> World:
    world = World()
    small, big = setup(world, pairing, place)
    foreshadow(world, small, big, obstacle)
    trouble_starts(world, small, big, obstacle, place)
    drift_apart(world, small, big)
    clever_kazoo(world, small, big, tune)
    reunite(world, small, big, place)
    world.facts.update(
        pairing=pairing,
        place=place,
        obstacle=obstacle,
        tune=tune,
        small=small,
        big=big,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pairing = f["pairing"]
    obstacle = f["obstacle"]
    place = f["place"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the words "kazoo", "clever", and "dissimilar".',
        f"Tell a gentle foreshadowing story about a dissimilar pair of friends crossing {place.label} when {obstacle.label} hides the path, and a kazoo becomes the clever answer.",
        f"Write a child-facing rhyming tale where {pairing.small_name} and {pairing.big_name} are separated for a moment, then reunited by a small musical clue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    small = f["small"]
    big = f["big"]
    pairing = f["pairing"]
    place = f["place"]
    obstacle = f["obstacle"]
    tune = f["tune"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {small.name} the {pairing.small_noun} and {big.name} the {pairing.big_noun}. They are a dissimilar pair, but they care for each other and travel together.",
        ),
        (
            "What were they carrying?",
            f"{small.name} carried a kazoo, and {big.name} carried a basket for the picnic. Those two things matter because the kazoo becomes the tool that helps them meet again.",
        ),
        (
            f"What problem did {obstacle.label} cause?",
            f"{obstacle.label.capitalize()} blocked their sight, so they could not see each other on the path. That made them drift apart and feel worried.",
        ),
    ]
    if f.get("foreshadowed"):
        qa.append(
            (
                "How did the story use foreshadowing?",
                f"At the start, {small.name} sang a warning about using the kazoo if the path grew hard to see. Later, that early line came true when {small.name} used the kazoo to guide {big.name} back.",
            )
        )
    if f.get("used_kazoo"):
        qa.append(
            (
                f"Why was {small.name}'s idea clever?",
                f"It was clever because the kazoo could travel through {obstacle.label} even when sight was blocked. {small.name} remembered the earlier warning and turned a playful instrument into a safe guide.",
            )
        )
    if f.get("reunited"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with the two friends together again, walking on to {place.picnic}. The final lantern image shows that the fear has changed into warmth, music, and relief.",
            )
        )
    qa.append(
        (
            f"What tune did {small.name} play?",
            f"{small.name} played {tune.pattern}. The special pattern gave {big.name} a sound to follow through the hidden path.",
        )
    )
    return qa


KNOWLEDGE = {
    "kazoo": [
        (
            "What is a kazoo?",
            "A kazoo is a small musical instrument that buzzes when you hum into it. It can make a bright, silly sound with only a little breath.",
        )
    ],
    "fog": [
        (
            "What is fog?",
            "Fog is a cloud close to the ground. It can make it hard to see far away.",
        )
    ],
    "reeds": [
        (
            "What are reeds?",
            "Reeds are tall water plants with long stems. When many reeds grow close together, they can hide a path behind them.",
        )
    ],
    "hedge": [
        (
            "What is a hedge?",
            "A hedge is a line of bushes or shrubs. A twisty hedge can make a path feel like a green maze.",
        )
    ],
    "echo": [
        (
            "Why can sound help when you cannot see well?",
            "Sound can travel around corners or through mist even when your eyes cannot see clearly. A familiar sound can help someone know which way to go.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is a small clue that hints at something important later. It helps the ending feel surprising and also just right.",
        )
    ],
    "friends": [
        (
            "What does it mean if two friends are dissimilar?",
            "It means they are different in some ways, like size or shape or habits. They can still be wonderful friends even when they are not alike.",
        )
    ],
}
KNOWLEDGE_ORDER = ["kazoo", "fog", "reeds", "hedge", "echo", "foreshadowing", "friends"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"kazoo", "echo", "foreshadowing", "friends"}
    obstacle = world.facts["obstacle"]
    if obstacle.id in {"fog", "reeds", "hedge"}:
        tags.add(obstacle.id)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A reasonable story needs an obstacle that belongs in the place, hides sight,
% and still lets a kazoo note travel through.
valid(P, Pair, O) :- place(P), pair(Pair), obstacle(O),
                     affords(P, O), hides_sight(O), sound_clear(O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, obstacle_id))
    for pair_id in PAIRINGS:
        lines.append(asp.fact("pair", pair_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        if obstacle.hides_sight:
            lines.append(asp.fact("hides_sight", obstacle_id))
        if obstacle.sound_clear:
            lines.append(asp.fact("sound_clear", obstacle_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming storyworld where a clever kazoo helps a dissimilar pair find each other again."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pair", choices=PAIRINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tune", choices=TUNES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and not obstacle_reasonable(args.place, args.obstacle):
        raise StoryError(explain_rejection(args.place, args.obstacle))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.pair is None or combo[1] == args.pair)
        and (args.obstacle is None or combo[2] == args.obstacle)
    ]
    if not combos:
        if args.place and args.obstacle:
            raise StoryError(explain_rejection(args.place, args.obstacle))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, pair_id, obstacle_id = rng.choice(sorted(combos))
    tune_id = args.tune or rng.choice(sorted(TUNES))
    return StoryParams(
        place=place_id,
        pair=pair_id,
        obstacle=obstacle_id,
        tune=tune_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.pair not in PAIRINGS:
        raise StoryError(f"(Invalid pair: {params.pair})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Invalid obstacle: {params.obstacle})")
    if params.tune not in TUNES:
        raise StoryError(f"(Invalid tune: {params.tune})")
    if not obstacle_reasonable(params.place, params.obstacle):
        raise StoryError(explain_rejection(params.place, params.obstacle))

    world = tell(
        pairing=PAIRINGS[params.pair],
        place=PLACES[params.place],
        obstacle=OBSTACLES[params.obstacle],
        tune=TUNES[params.tune],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(5):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if "kazoo" not in sample.story.lower():
                raise StoryError("(Smoke test failed: story omitted 'kazoo'.)")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM SAMPLE FAILED at seed {seed}: {err}")
            break
    if rc == 0:
        print("OK: random sample generation succeeded.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, pair, obstacle) combos:\n")
        for place_id, pair_id, obstacle_id in combos:
            print(f"  {place_id:10} {pair_id:12} {obstacle_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.pair} at {p.place} with {p.obstacle}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

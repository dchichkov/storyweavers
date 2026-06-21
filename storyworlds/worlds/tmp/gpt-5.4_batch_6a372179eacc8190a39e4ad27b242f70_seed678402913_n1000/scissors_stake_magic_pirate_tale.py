#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scissors_stake_magic_pirate_tale.py
==============================================================

A standalone story world for a small magical pirate tale: two children pretend
to be pirates near a little harbor, a boat is tied to a wooden stake with a
glowing rope, and one child is tempted to use scissors to solve a problem too
quickly. In this world, cutting the magic mooring is a real hazard: the rope is
what keeps the tide from whisking the boat away.

The simulation keeps physical meters and emotional memes on typed entities,
drives prose from state changes, and includes an ASP twin for the domain gate
and outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/scissors_stake_magic_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/scissors_stake_magic_pirate_tale.py --boat skiff
    python storyworlds/worlds/gpt-5.4/scissors_stake_magic_pirate_tale.py --response moon_knot
    python storyworlds/worlds/gpt-5.4/scissors_stake_magic_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/scissors_stake_magic_pirate_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/scissors_stake_magic_pirate_tale.py --qa --json
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    floats: bool = False
    tied: bool = False
    safe_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Harbor:
    id: str
    place: str
    water: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BoatCfg:
    id: str
    label: str
    phrase: str
    cargo: str
    drift: str
    image: str
    pull_difficulty: int
    floats: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicAid:
    id: str
    label: str
    phrase: str
    glow: str
    use_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in ("instigator", "cautioner")]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_drift(world: World) -> list[str]:
    boat = world.get("boat")
    rope = world.get("rope")
    tide = world.get("tide")
    if rope.meters["cut"] < THRESHOLD or boat.meters["adrift"] >= THRESHOLD:
        return []
    sig = ("drift", boat.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat.meters["adrift"] += 1
    tide.meters["pull"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__adrift__"]


CAUSAL_RULES = [
    Rule(name="drift", tag="physical", apply=_r_drift),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(boat: BoatCfg) -> bool:
    return boat.floats


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def drift_severity(boat: BoatCfg, delay: int) -> int:
    return boat.pull_difficulty + delay


def is_recovered(response: Response, boat: BoatCfg, delay: int) -> bool:
    return response.power >= drift_severity(boat, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_drift(world: World) -> dict:
    sim = world.copy()
    do_cut(sim, narrate=False)
    return {
        "adrift": sim.get("boat").meters["adrift"] >= THRESHOLD,
        "pull": sim.get("tide").meters["pull"],
    }


def do_cut(world: World, narrate: bool = True) -> None:
    rope = world.get("rope")
    rope.meters["cut"] += 1
    rope.tied = False
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, harbor: Harbor, boat: BoatCfg) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"At dusk, {a.id} and {b.id} turned the little harbor into a pirate kingdom. "
        f"{harbor.detail}"
    )
    world.say(
        f'A moon-map shimmered in {a.id}\'s hand, and {boat.phrase} bobbed beside the dock. '
        f'"Captain {a.id} and Scout {b.id}!" {a.id} cried. "Tonight we find the hidden gold!"'
    )


def discovery(world: World, b: Entity, harbor: Harbor, boat: BoatCfg) -> None:
    world.say(
        f"But the silver moon-map slipped from the dock and landed in {boat.cargo}. "
        f"The little vessel was tied to a wooden stake where {harbor.water} lapped softly."
    )
    world.say(
        f'{b.id} leaned over the planks. "If only we could bring it in without falling," '
        f'{b.pronoun()} said.'
    )


def temptation(world: World, a: Entity) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} spotted a pair of scissors in the basket of play things and grinned. '
        f'"I know a fast way," {a.pronoun()} said.'
    )


def warning(world: World, b: Entity, a: Entity, parent: Entity, boat: BoatCfg) -> None:
    pred = predict_drift(world)
    b.memes["caution"] += 1
    world.facts["predicted_pull"] = pred["pull"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} knew the shining rope was not ordinary at all."
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "No, {a.id}. The magic rope is holding {boat.label} '
        f'to the stake. If you snip it with the scissors, the tide will steal the boat."{extra}'
    )
    world.say(
        f'"{parent.label_word.capitalize()} said enchanted knots must be untied, not cut," '
        f'{b.id} added.'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"We just need one quick snip," {a.id} said, and because {a.pronoun()} was '
            f'{b.id}\'s older sibling, {b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"We just need one quick snip," {a.id} said, and darted forward anyway.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity, aid: MagicAid, boat: BoatCfg) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'"We just need one quick snip," {a.id} said. But {b.id} stood firm, and at last '
        f'{a.id} looked at the glowing rope, thought of the wandering tide, and lowered the scissors.'
    )
    world.say(
        f'They carried the scissors back to the basket and called for {parent.label_word}. '
        f'Soon {parent.label_word} brought {aid.phrase}, and its light showed the knot plainly.'
    )
    world.say(
        f"Together they eased the map out of {boat.cargo} without cutting a thing."
    )


def cut_scene(world: World, boat: BoatCfg) -> None:
    do_cut(world)
    world.say(
        f"Snip! The silver rope parted at the stake. For one blink nothing happened. "
        f"Then {boat.drift}."
    )


def alarm(world: World, b: Entity, boat: BoatCfg, parent: Entity) -> None:
    world.say(f'"The boat!" {b.id} gasped. "{boat.label.capitalize()} is drifting away!"')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, aid: MagicAid, boat: BoatCfg) -> None:
    world.get("boat").meters["adrift"] = 0.0
    world.get("tide").meters["pull"] = 0.0
    body = response.text.format(boat=boat.label, aid=aid.label)
    world.say(
        f"{parent.label_word.capitalize()} came running with {aid.phrase}. "
        f"{parent.pronoun().capitalize()} {body}."
    )
    world.say(
        f"Soon {boat.label} bumped the dock again, and the bright rope was tied back to the stake in a neat safe knot."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them and hugged them close. '
        f'"I am glad you called me," {parent.pronoun()} said. "Scissors are for paper and cloth, '
        f'not for a magic mooring rope. A clever pirate solves the right problem the right way."'
    )


def safe_turn(world: World, parent: Entity, a: Entity, b: Entity, aid: MagicAid, boat: BoatCfg) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next evening, {parent.label_word} had a surprise: {aid.phrase}. "
        f"It {aid.glow}."
    )
    world.say(
        f'"Now," {parent.pronoun()} smiled, "{aid.use_line}"'
    )
    world.say(
        f"{a.id} held the shining light high while {b.id} read the moon-map. "
        f"Beside them, {boat.image}."
    )
    world.say('"Safe magic for brave pirates!" they cheered.')


def rescue_fail(world: World, parent: Entity, response: Response, aid: MagicAid, boat: BoatCfg) -> None:
    tide = world.get("tide")
    tide.meters["pull"] += 1
    body = response.fail.format(boat=boat.label, aid=aid.label)
    world.say(
        f"{parent.label_word.capitalize()} hurried down with {aid.phrase}, but {parent.pronoun()} {body}."
    )
    world.say(
        f"{boat.label.capitalize()} slipped past the last post and out into the dark glittering water."
    )


def loss(world: World, parent: Entity, a: Entity, b: Entity, boat: BoatCfg) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"There was no way to chase it in the dark. {parent.label_word.capitalize()} kept the children safely on the dock while they watched {boat.label} grow smaller and smaller."
    )
    world.say(
        f"The moon-map was gone with it, and the game felt suddenly quiet."
    )


def grim_lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} wrapped an arm around both children. '
        f'"You are safe, and that matters most," {parent.pronoun()} whispered. '
        f'"But remember this: cutting a magic rope with scissors can turn a little problem into a big one."'
    )
    world.say(
        "After that, whenever a knot looked tricky, they fetched a grown-up before touching it."
    )


def tell(
    harbor: Harbor,
    boat: BoatCfg,
    aid: MagicAid,
    response: Response,
    *,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            traits=["bold"],
            age=instigator_age,
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation},
        )
    )
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="stake", type="stake", label="wooden stake", tied=True))
    world.add(Entity(id="rope", type="rope", label="silver rope", tied=True, tags={"rope", "magic"}))
    world.add(Entity(id="tide", type="tide", label="tide"))
    boat_ent = world.add(Entity(id="boat", type="boat", label=boat.label, phrase=boat.phrase, floats=boat.floats, tied=True))
    world.add(Entity(id="scissors", type="tool", label="scissors"))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = 6.0
    b.memes["caution"] = initial_caution(trait)

    play_setup(world, a, b, harbor, boat)
    discovery(world, b, harbor, boat)

    world.para()
    temptation(world, a)
    warning(world, b, a, parent, boat)
    averted = would_avert(relation, a.age, b.age, trait)

    if averted:
        back_down(world, a, b, parent, aid, boat)
        world.para()
        safe_turn(world, parent, a, b, aid, boat)
        severity = 0
        recovered = True
    else:
        defy(world, a, b)
        world.para()
        cut_scene(world, boat)
        alarm(world, b, boat, parent)
        severity = drift_severity(boat, delay)
        boat_ent.meters["severity"] = float(severity)
        recovered = is_recovered(response, boat, delay)

        world.para()
        if recovered:
            rescue(world, parent, response, aid, boat)
            lesson(world, parent, a, b)
            world.para()
            safe_turn(world, parent, a, b, aid, boat)
        else:
            rescue_fail(world, parent, response, aid, boat)
            loss(world, parent, a, b, boat)
            grim_lesson(world, parent, a, b)

    outcome = "averted" if averted else ("recovered" if recovered else "lost")
    world.facts.update(
        harbor=harbor,
        boat_cfg=boat,
        aid=aid,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        adrift=world.get("boat").meters["adrift"] >= THRESHOLD or outcome == "lost",
        recovered=recovered,
        predicted_pull=world.facts.get("predicted_pull", 0),
    )
    return world


@dataclass
class StoryParams:
    harbor: str
    boat: str
    aid: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    seed: Optional[int] = None


HARBORS = {
    "moon_cove": Harbor(
        id="moon_cove",
        place="the moonlit cove",
        water="the black-blue water",
        detail="A crooked dock became their ship, a painted crate became their treasure chest, and the salt wind seemed full of old sea songs.",
        tags={"harbor", "magic", "pirate"},
    ),
    "star_pier": Harbor(
        id="star_pier",
        place="the starry pier",
        water="the silver water",
        detail="A weathered plank became their deck, a bucket became their drum, and the night made every ripple look enchanted.",
        tags={"harbor", "magic", "pirate"},
    ),
}

BOATS = {
    "skiff": BoatCfg(
        id="skiff",
        label="skiff",
        phrase="a little skiff with a crescent-moon sail",
        cargo="its tiny seat",
        drift="the skiff rocked once and began sliding away from the dock",
        image="the skiff gleamed like a small white fish under the moon",
        pull_difficulty=2,
        tags={"boat", "harbor"},
    ),
    "dinghy": BoatCfg(
        id="dinghy",
        label="dinghy",
        phrase="a little dinghy painted with gold stars",
        cargo="its bow",
        drift="the dinghy swung out, turned its nose, and drifted into the current",
        image="the dinghy floated steady as a sleepy duck beside the dock",
        pull_difficulty=2,
        tags={"boat", "harbor"},
    ),
    "treasure_raft": BoatCfg(
        id="treasure_raft",
        label="treasure raft",
        phrase="a tiny treasure raft with a red cloth flag",
        cargo="the middle of the raft",
        drift="the treasure raft twirled once and skimmed away from the stake",
        image="the little raft shone with dewdrops like a necklace of pearls",
        pull_difficulty=3,
        tags={"boat", "harbor"},
    ),
}

MAGIC_AIDS = {
    "shell_lantern": MagicAid(
        id="shell_lantern",
        label="shell lantern",
        phrase="a shell lantern",
        glow="spilled pearl-colored light over the planks",
        use_line="let's use magic light to see the knot before we touch it.",
        tags={"magic", "light"},
    ),
    "star_lamp": MagicAid(
        id="star_lamp",
        label="star lamp",
        phrase="a star lamp",
        glow="cast a soft blue ring over the dock",
        use_line="a pirate can be brave and still look carefully first.",
        tags={"magic", "light"},
    ),
    "whisper_shell": MagicAid(
        id="whisper_shell",
        label="whisper shell",
        phrase="a whisper shell",
        glow="glimmered and hummed with gentle sea-magic",
        use_line="the sea tells its secrets best to patient hands.",
        tags={"magic", "light"},
    ),
}

RESPONSES = {
    "moon_knot": Response(
        id="moon_knot",
        sense=3,
        power=4,
        text="lifted the {aid} high, caught the drifting {boat} with a hooked line, and retied the glowing rope in a moon-knot",
        fail="threw a hooked line toward the {boat}, but the tide had already pulled it too far to catch",
        qa_text="used a hooked line and the magic light to catch the boat and tie it back safely",
        tags={"rescue", "rope", "magic"},
    ),
    "calm_call": Response(
        id="calm_call",
        sense=3,
        power=3,
        text="spoke a calm harbor rhyme over the {aid}, and the drifting {boat} slowed long enough to be pulled back by hand",
        fail="sang the harbor rhyme, but the water had already tugged the {boat} beyond the dock",
        qa_text="used a calm harbor rhyme and the magic aid to slow the boat and pull it back",
        tags={"rescue", "magic"},
    ),
    "long_pole": Response(
        id="long_pole",
        sense=2,
        power=2,
        text="snagged the {boat} with the long dock pole and drew it back inch by inch",
        fail="reached with the long dock pole, but the {boat} had drifted beyond its tip",
        qa_text="used the long dock pole to hook the boat and pull it back",
        tags={"rescue", "dock"},
    ),
    "jump_in": Response(
        id="jump_in",
        sense=1,
        power=1,
        text="splashed into the cold water and dragged the {boat} back",
        fail="started to splash after the {boat}, but stopped because the dark water was too risky",
        qa_text="jumped in after the boat",
        tags={"water"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "steady", "curious", "clever", "sensible"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_responses():
        return combos
    for harbor_id in HARBORS:
        for boat_id, boat in BOATS.items():
            if hazard_at_risk(boat):
                combos.append((harbor_id, boat_id))
    return combos


KNOWLEDGE = {
    "scissors": [
        (
            "What are scissors for?",
            "Scissors are tools for cutting paper, cloth, and other safe things with a grown-up's help. They are not for cutting ropes that hold something important in place.",
        )
    ],
    "stake": [
        (
            "What is a stake by a dock?",
            "A dock stake is a strong wooden post driven into the ground. People tie ropes to it so a boat stays where it should.",
        )
    ],
    "rope": [
        (
            "Why do boats need ropes at a dock?",
            "A rope keeps a boat from drifting away with the water. If the rope is untied or cut, the boat can move off quickly.",
        )
    ],
    "tide": [
        (
            "What is the tide?",
            "The tide is the way sea water slowly moves higher, lower, and sideways along the shore. It can tug floating things away from a dock.",
        )
    ],
    "magic": [
        (
            "What is magic in a story like this?",
            "Magic in a story is a special make-believe power that can make light glow or a rhyme work. Even in a magical story, characters still need to be careful and wise.",
        )
    ],
    "light": [
        (
            "Why is a light useful when you look at a knot?",
            "A good light helps you see where the knot loops and where your hands should go. Seeing clearly makes a careful fix easier.",
        )
    ],
    "rescue": [
        (
            "What should you do if something drifts away near water?",
            "Call a grown-up right away and stay where it is safe. Running or jumping into dark water can make the problem bigger.",
        )
    ],
}
KNOWLEDGE_ORDER = ["scissors", "stake", "rope", "tide", "magic", "light", "rescue"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    boat = f["boat_cfg"]
    aid = f["aid"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a magical pirate tale for a 3-to-5-year-old that includes the words "scissors" and "stake" and ends safely with no drifting boat.',
            f"Tell a gentle harbor story where {a.id} wants to use scissors on a glowing rope tied to a stake, but {b.id} stops {a.pronoun('object')} and a grown-up uses {aid.phrase} instead.",
            "Write a story where children learn that quick cutting is not always a clever fix, especially when magic and water are involved.",
        ]
    if outcome == "lost":
        return [
            'Write a cautionary magical pirate tale that includes the words "scissors" and "stake" and ends with a drifting boat that cannot be brought back that night.',
            f"Tell a story where {a.id} cuts a magic mooring rope at the stake, the little {boat.label} drifts away, and the children learn to call a grown-up before touching harbor knots.",
            "Write a sad-but-safe pirate story where everyone stays safe but loses part of the game because someone chose a risky shortcut.",
        ]
    return [
        'Write a magical pirate tale for a 3-to-5-year-old that includes the words "scissors" and "stake" and ends with a grown-up fixing the problem wisely.',
        f"Tell a harbor story where {a.id} cuts a glowing rope tied to a stake, the {boat.label} drifts off, and a calm grown-up brings it back with magic and care.",
        f"Write a simple pirate adventure with moonlight, a drifting boat, and {aid.phrase} proving that patient magic is better than a quick snip.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    boat = f["boat_cfg"]
    aid = f["aid"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were pretending to be pirates at the harbor. It also includes their {parent.label_word}, who helps when the trouble starts.",
        ),
        (
            "What problem did the children have?",
            f"Their moon-map had fallen into the {boat.label}, which was tied to a wooden stake. They wanted it back, but they needed a safe way to reach it.",
        ),
        (
            f"Why did {b.id} say not to use the scissors?",
            f"{b.id} knew the glowing rope was what held the {boat.label} to the stake. If the rope was cut, the tide could pull the boat away.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed after {b.id} warned {a.id}?",
                f"{a.id} stopped trying to cut the rope and put the scissors away. Then their {parent.label_word} used {aid.phrase} so everyone could see the knot clearly and solve the problem without a dangerous shortcut.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with the boat still tied to the stake and the children using careful magic instead of cutting. The last image shows them playing pirates again with light and patience.",
            )
        )
    elif f["outcome"] == "recovered":
        qa.append(
            (
                f"What happened when {a.id} cut the rope?",
                f"The rope parted at the stake and the {boat.label} began to drift away. The danger came because the tide could move the floating boat as soon as the mooring was gone.",
            )
        )
        qa.append(
            (
                f"How did their {parent.label_word} fix the problem?",
                f"{parent.label_word.capitalize()} {response.qa_text}. The rescue worked because the grown-up used the right tool and stayed calm.",
            )
        )
        qa.append(
            (
                "What did the children learn?",
                "They learned that being quick is not the same as being wise. A careful pirate asks for help and unties a knot properly instead of cutting first.",
            )
        )
    else:
        qa.append(
            (
                f"Could their {parent.label_word} get the {boat.label} back right away?",
                f"No. By the time the grown-up tried to help, the tide had already pulled the boat too far from the dock. Everyone stayed safe, but the game and the moon-map were lost for the night.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly but safely, with the children still on the dock and the {boat.label} gone into the dark water. The ending proves why cutting the rope was a much bigger mistake than it first seemed.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"scissors", "stake", "rope", "tide", "magic"}
    if world.facts["outcome"] != "lost":
        tags.add("light")
    if world.facts["outcome"] in {"recovered", "lost"}:
        tags.add("rescue")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = []
        if e.floats:
            flags.append("floats")
        if e.tied:
            flags.append("tied")
        if e.safe_light:
            flags.append("safe_light")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        harbor="moon_cove",
        boat="skiff",
        aid="shell_lantern",
        response="moon_knot",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
    ),
    StoryParams(
        harbor="star_pier",
        boat="dinghy",
        aid="star_lamp",
        response="calm_call",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
    StoryParams(
        harbor="moon_cove",
        boat="treasure_raft",
        aid="whisper_shell",
        response="long_pole",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="friends",
    ),
    StoryParams(
        harbor="star_pier",
        boat="treasure_raft",
        aid="shell_lantern",
        response="long_pole",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="father",
        trait="clever",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
    ),
]


def explain_rejection(boat: BoatCfg) -> str:
    if not boat.floats:
        return f"(No story: {boat.label} would not drift from the stake, so cutting the rope makes no real harbor problem.)"
    return "(No story: this combination does not create a reasonable drifting-boat hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    recovered = is_recovered(RESPONSES[params.response], BOATS[params.boat], params.delay)
    return "recovered" if recovered else "lost"


ASP_RULES = r"""
hazard(B) :- boat(B), floats(B).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(H,B) :- harbor(H), boat(B), hazard(B).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(PD + D) :- chosen_boat(B), pull_difficulty(B, PD), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
recovered :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(recovered) :- not averted, recovered.
outcome(lost) :- not averted, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for harbor_id in HARBORS:
        lines.append(asp.fact("harbor", harbor_id))
    for boat_id, boat in BOATS.items():
        lines.append(asp.fact("boat", boat_id))
        if boat.floats:
            lines.append(asp.fact("floats", boat_id))
        lines.append(asp.fact("pull_difficulty", boat_id, boat.pull_difficulty))
    for aid_id in MAGIC_AIDS:
        lines.append(asp.fact("aid", aid_id))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_boat", params.boat),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(80):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            continue
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a magical pirate harbor, a rope tied to a stake, and a risky shortcut with scissors."
    )
    ap.add_argument("--harbor", choices=HARBORS)
    ap.add_argument("--boat", choices=BOATS)
    ap.add_argument("--aid", choices=MAGIC_AIDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much of a head start the drifting boat gets")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible-story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP and Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.boat and not BOATS[args.boat].floats:
        raise StoryError(explain_rejection(BOATS[args.boat]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.harbor is None or combo[0] == args.harbor)
        and (args.boat is None or combo[1] == args.boat)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    harbor_id, boat_id = rng.choice(sorted(combos))
    aid_id = args.aid or rng.choice(sorted(MAGIC_AIDS))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)

    return StoryParams(
        harbor=harbor_id,
        boat=boat_id,
        aid=aid_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.harbor not in HARBORS:
        raise StoryError(f"(Invalid harbor: {params.harbor})")
    if params.boat not in BOATS:
        raise StoryError(f"(Invalid boat: {params.boat})")
    if params.aid not in MAGIC_AIDS:
        raise StoryError(f"(Invalid aid: {params.aid})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Invalid response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        HARBORS[params.harbor],
        BOATS[params.boat],
        MAGIC_AIDS[params.aid],
        RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (harbor, boat) combos:\n")
        for harbor_id, boat_id in combos:
            print(f"  {harbor_id:10} {boat_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.boat} at {p.harbor} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

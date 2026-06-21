#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/eighth_nip_cabin_sound_effects_kindness_fable.py
============================================================================

A standalone story world for a small fable-shaped tale about a kind forest host,
a mysterious sound outside a cabin, and an unexpected eighth place at the table.

Seed cues rebuilt as world state
--------------------------------
- words: "eighth", "nip", "cabin"
- features: Sound Effects, Kindness
- style: Fable

World logic
-----------
A small animal host is inside a cabin on a cold evening, with seven places set
for supper. Outside, a hungry visitor makes a noise at the door, shutter, or
roof. The host can answer with enough kindness to truly warm and feed the
visitor, or only a weak gesture that leaves the visitor out on the porch.
Reasonableness is constrained:

- A visitor must be able to reach the chosen sound source.
- The chosen food must stretch to an eighth serving.
- Low-sense responses are known to the world but refused for normal stories.

The result is a short, state-driven fable: a clear beginning, a tense middle
built from the noise and the host's choice, and an ending image that proves what
changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/eighth_nip_cabin_sound_effects_kindness_fable.py
    python storyworlds/worlds/gpt-5.4/eighth_nip_cabin_sound_effects_kindness_fable.py --visitor sparrow --sound shutter
    python storyworlds/worlds/gpt-5.4/eighth_nip_cabin_sound_effects_kindness_fable.py --food pie
    python storyworlds/worlds/gpt-5.4/eighth_nip_cabin_sound_effects_kindness_fable.py --all
    python storyworlds/worlds/gpt-5.4/eighth_nip_cabin_sound_effects_kindness_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/eighth_nip_cabin_sound_effects_kindness_fable.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "doe", "mother", "aunt", "woman"}
        male = {"buck", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Season:
    id: str
    opener: str
    cold: int
    sky: str
    tags: set[str] = field(default_factory=set)


@dataclass
class VisitorKind:
    id: str
    label: str
    phrase: str
    type: str
    can_reach: set[str] = field(default_factory=set)
    sound_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    vessel: str
    portions: int
    warmth: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundSource:
    id: str
    place: str
    noises: list[str] = field(default_factory=list)
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    invite_inside: bool
    wrap: bool
    share: bool
    text: str
    porch_text: str
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_need_makes_noise(world: World) -> list[str]:
    out: list[str] = []
    visitor = world.get("visitor")
    if visitor.attrs.get("inside"):
        return out
    source = world.facts["sound_cfg"]
    if visitor.meters["cold"] >= THRESHOLD or visitor.meters["hunger"] >= THRESHOLD:
        sig = ("noise", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("cabin").meters["noise"] += 1
            host = world.get("host")
            host.memes["alarm"] += 1
            out.append("__noise__")
    return out


def _r_inside_warms(world: World) -> list[str]:
    out: list[str] = []
    visitor = world.get("visitor")
    if not visitor.attrs.get("inside"):
        return out
    sig = ("warm", visitor.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    visitor.meters["cold"] = 0.0
    visitor.memes["trust"] += 1
    visitor.memes["relief"] += 1
    out.append("__warm__")
    return out


def _r_food_fills(world: World) -> list[str]:
    out: list[str] = []
    visitor = world.get("visitor")
    if visitor.meters["fed"] < THRESHOLD:
        return out
    sig = ("fed", visitor.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    visitor.meters["hunger"] = 0.0
    visitor.memes["gratitude"] += 1
    out.append("__fed__")
    return out


CAUSAL_RULES = [
    Rule(name="need_makes_noise", tag="physical", apply=_r_need_makes_noise),
    Rule(name="inside_warms", tag="physical", apply=_r_inside_warms),
    Rule(name="food_fills", tag="physical", apply=_r_food_fills),
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


def reachable(visitor: VisitorKind, sound: SoundSource) -> bool:
    return sound.id in visitor.can_reach


def food_stretches(food: Food) -> bool:
    return food.portions >= 8


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def cold_severity(season: Season, delay: int) -> int:
    return season.cold + delay


def is_warmed(response: Response, season: Season, delay: int) -> bool:
    return response.power >= cold_severity(season, delay)


def predict_need(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    visitor = sim.get("visitor")
    return {
        "cold": visitor.meters["cold"],
        "hunger": visitor.meters["hunger"],
        "noise": sim.get("cabin").meters["noise"],
    }


def introduce(world: World, host: Entity, season: Season, food: Food) -> None:
    world.say(
        f"{season.opener}, {host.id} kept a little cabin at the edge of the pines. "
        f"The {season.sky} and the air had the nip of winter in it."
    )
    world.say(
        f"On the table stood seven {food.vessel} of {food.label}, neat as a row of candles. "
        f"There was room enough, if kindness asked for it, for an eighth."
    )


def host_trait_line(world: World, host: Entity) -> None:
    world.say(
        f"{host.id} was known among the trees for a soft voice and a ready paw. "
        f"{host.pronoun('subject').capitalize()} believed a warm room should not keep all its warmth to itself."
    )


def start_noise(world: World, visitor: Entity, sound: SoundSource, visitor_cfg: VisitorKind) -> None:
    visitor.meters["cold"] += 1
    visitor.meters["hunger"] += 1
    propagate(world, narrate=False)
    beats = " ".join(sound.noises)
    world.say(
        f"Then, from the {sound.place}, came a strange little chorus: {beats}."
    )
    world.say(visitor_cfg.sound_line)
    world.say(
        f"The sound ran around the cabin walls and made the lamplight seem small for one blink."
    )


def wonder(world: World, host: Entity, sound: SoundSource) -> None:
    host.memes["fear"] += 1
    pred = predict_need(world)
    world.facts["predicted_noise"] = pred["noise"]
    world.say(
        f'"Who taps so late?" {host.id} whispered. Yet the noise from the {sound.place} did not sound angry; '
        f"it sounded thin and tired."
    )


def choose_kindness(world: World, host: Entity, visitor_cfg: VisitorKind, sound: SoundSource) -> None:
    host.memes["kindness"] += 1
    world.say(
        f"So {host.id} lifted the latch instead of the broom. Behind the {sound.place}, {sound.reveal}: "
        f"{visitor_cfg.phrase}, shivering hard enough to make even the dark look chilly."
    )


def delay_beat(world: World, season: Season, delay: int, sound: SoundSource) -> None:
    if delay <= 0:
        return
    if delay == 1:
        world.say(
            f"For one worried moment, the cold evening waited outside the {sound.place}, and the frost bit a little deeper."
        )
    else:
        world.say(
            f"For two long moments, while the wind fussed at the {sound.place}, the night sharpened and the cold grew meaner."
        )
    world.facts["severity"] = cold_severity(season, delay)


def help_visitor(
    world: World,
    host: Entity,
    visitor: Entity,
    response: Response,
    food: Food,
    season: Season,
    delay: int,
) -> bool:
    warmed = is_warmed(response, season, delay)
    if response.wrap:
        visitor.meters["wrapped"] += 1
    if response.invite_inside and warmed:
        visitor.attrs["inside"] = True
    if response.share:
        visitor.meters["fed"] += 1
    propagate(world, narrate=False)
    if warmed:
        world.say(response.text.format(food=food.label, vessel=food.vessel))
        world.say(
            f"Soon the little guest stopped trembling. The cabin smelled of {food.warmth}, and fear had no chair left to sit in."
        )
    else:
        world.say(response.porch_text.format(food=food.label, vessel=food.vessel))
        world.say(
            f"The visitor nibbled thankfully, but the porch boards were still cold, and the night stayed bigger than the welcome."
        )
    return warmed


def table_turn(world: World, host: Entity, visitor_cfg: VisitorKind, food: Food, warmed: bool) -> None:
    if warmed:
        world.say(
            f"{host.id} set out an eighth {food.vessel[:-1] if food.vessel.endswith('s') else food.vessel} and filled it as carefully as the first seven."
        )
        world.say(
            f"By the time the lamp burned low, the cabin held not seven quiet places, but eight, and the smallest one was smiling."
        )
    else:
        world.say(
            f"{host.id} looked at the seven waiting {food.vessel} and wished one of them had been brave enough to cross the threshold too."
        )
        world.say(
            f"From the porch came one softer sound -- a grateful little {visitor_cfg.label}-sigh -- and then the forest grew still."
        )


def moral(world: World, warmed: bool) -> None:
    if warmed:
        world.say(
            "And that is why the pine folk say: when a door answers a frightened sound with kindness, the whole house grows larger."
        )
    else:
        world.say(
            "And that is why the pine folk say: kindness tossed from far away is better than none, but kindness that opens the door is warmer."
        )


SEASONS = {
    "frost": Season(
        id="frost",
        opener="On the eighth evening after the first frost",
        cold=2,
        sky="windows wore silver ferns",
        tags={"winter", "frost"},
    ),
    "snow": Season(
        id="snow",
        opener="On the eighth evening of the first snow",
        cold=3,
        sky="roof carried a white hush",
        tags={"winter", "snow"},
    ),
}

VISITORS = {
    "mouse": VisitorKind(
        id="mouse",
        label="mouse",
        phrase="a field mouse with whiskers bright with frost",
        type="animal",
        can_reach={"door", "shutter"},
        sound_line='"Scritch-scritch," went the tiny claws, and then a hopeful "tap-tap."',
        tags={"mouse", "small_animal"},
    ),
    "sparrow": VisitorKind(
        id="sparrow",
        label="sparrow",
        phrase="a brown sparrow with feathers puffed against the cold",
        type="animal",
        can_reach={"shutter", "roof"},
        sound_line='"Tap-tap! Rustle-rustle!" sounded the small wings at the wood.',
        tags={"bird", "small_animal"},
    ),
    "hedgehog": VisitorKind(
        id="hedgehog",
        label="hedgehog",
        phrase="a hedgehog no bigger than a pinecone basket, with a cold nose and tired feet",
        type="animal",
        can_reach={"door"},
        sound_line='"Tok-tok, snuff-snuff," came the careful little bumps below the latch.',
        tags={"hedgehog", "small_animal"},
    ),
}

FOODS = {
    "stew": Food(
        id="stew",
        label="acorn stew",
        phrase="a pot of acorn stew",
        vessel="bowls",
        portions=8,
        warmth="rosemary and warm acorns",
        ending_image="eight bowls steamed in a shining row",
        tags={"stew", "meal"},
    ),
    "buns": Food(
        id="buns",
        label="berry buns",
        phrase="a tray of berry buns",
        vessel="plates",
        portions=8,
        warmth="honey and berries",
        ending_image="eight plates held soft berry buns under the lamp",
        tags={"bread", "meal"},
    ),
    "porridge": Food(
        id="porridge",
        label="oat porridge",
        phrase="a kettle of oat porridge",
        vessel="cups",
        portions=8,
        warmth="cinnamon and oats",
        ending_image="eight cups sent up little white curls of steam",
        tags={"porridge", "meal"},
    ),
    "pie": Food(
        id="pie",
        label="turnip pie",
        phrase="one turnip pie",
        vessel="plates",
        portions=6,
        warmth="butter and turnip",
        ending_image="six slices sat under a cloth",
        tags={"pie", "meal"},
    ),
}

SOUNDS = {
    "door": SoundSource(
        id="door",
        place="door",
        noises=["Tok-tok.", "Scritch.", "Tok-tok."],
        reveal="the host found a shape huddled by the step",
        tags={"knock", "door"},
    ),
    "shutter": SoundSource(
        id="shutter",
        place="shutter",
        noises=["Tap-tap.", "Rattle-rattle."],
        reveal="the host pushed the shutter wide and looked down",
        tags={"tap", "shutter"},
    ),
    "roof": SoundSource(
        id="roof",
        place="roof",
        noises=["Thump.", "Slide.", "Rustle-rustle."],
        reveal="the host peered up beneath the eaves",
        tags={"roof", "rustle"},
    ),
}

RESPONSES = {
    "invite_share": Response(
        id="invite_share",
        sense=3,
        power=2,
        invite_inside=True,
        wrap=False,
        share=True,
        text="At once {host} opened the door wide, beckoned the visitor inside, and shared the hottest {food} in the cabin.",
        porch_text="",
        qa_text="opened the door and shared hot food",
        tags={"invite", "share"},
    ),
    "blanket_share": Response(
        id="blanket_share",
        sense=3,
        power=4,
        invite_inside=True,
        wrap=True,
        share=True,
        text="{host} wrapped the visitor in a woolen scrap, carried them in from the cold, and set before them a warm helping of {food}.",
        porch_text="",
        qa_text="wrapped the visitor, brought them inside, and shared warm food",
        tags={"invite", "blanket", "share"},
    ),
    "porch_plate": Response(
        id="porch_plate",
        sense=1,
        power=1,
        invite_inside=False,
        wrap=False,
        share=True,
        text="",
        porch_text="{host} set a plate of {food} outside and whispered that it might help.",
        qa_text="left food on the porch",
        tags={"porch", "share"},
    ),
}

HOST_NAMES = ["Pip", "Mira", "Hazel", "Bramble", "Nettle", "Fern"]
HOST_TYPES = ["doe", "buck"]


@dataclass
class StoryParams:
    season: str
    visitor: str
    food: str
    sound: str
    response: str
    host_name: str
    host_type: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        season="frost",
        visitor="mouse",
        food="porridge",
        sound="shutter",
        response="blanket_share",
        host_name="Mira",
        host_type="doe",
        delay=0,
    ),
    StoryParams(
        season="frost",
        visitor="hedgehog",
        food="stew",
        sound="door",
        response="invite_share",
        host_name="Bramble",
        host_type="buck",
        delay=0,
    ),
    StoryParams(
        season="snow",
        visitor="sparrow",
        food="buns",
        sound="roof",
        response="blanket_share",
        host_name="Hazel",
        host_type="doe",
        delay=0,
    ),
    StoryParams(
        season="snow",
        visitor="mouse",
        food="porridge",
        sound="door",
        response="invite_share",
        host_name="Pip",
        host_type="buck",
        delay=2,
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for season_id in SEASONS:
        for visitor_id, visitor in VISITORS.items():
            for food_id, food in FOODS.items():
                for sound_id, sound in SOUNDS.items():
                    if reachable(visitor, sound) and food_stretches(food):
                        combos.append((season_id, visitor_id, food_id, sound_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    if params.season not in SEASONS or params.response not in RESPONSES:
        raise StoryError("(Invalid parameters for outcome check.)")
    return "welcomed" if is_warmed(RESPONSES[params.response], SEASONS[params.season], params.delay) else "porch"


KNOWLEDGE = {
    "winter": [(
        "What does a nip of winter mean?",
        "A nip of winter means the air feels sharply cold, as if the cold gave you a tiny bite. It is a way of saying the weather has turned chilly."
    )],
    "mouse": [(
        "Why do mice scratch softly?",
        "Mice are very small, so their feet and claws make light scratching sounds instead of heavy stomps. That is why a mouse at a door often sounds like scritch-scritch."
    )],
    "bird": [(
        "Why might a sparrow tap at a shutter?",
        "A sparrow can land on a ledge or sill and peck or tap with its beak. Its light body makes quick little sounds on wood."
    )],
    "hedgehog": [(
        "What is a hedgehog?",
        "A hedgehog is a small animal with tiny legs and a coat of spines. It can curl up into a little ball when it feels unsafe."
    )],
    "door": [(
        "What sound does a small knock make on a door?",
        "A small knock can sound like tok-tok or tap-tap. Writers use sound words like that to help you hear the scene in your mind."
    )],
    "shutter": [(
        "What is a shutter?",
        "A shutter is a wooden cover over a window. It can tap or rattle when something touches it or when the wind shakes it."
    )],
    "roof": [(
        "Why do roofs make different sounds from doors?",
        "A roof is higher and wider, so things can slide, thump, or rustle across it. A door more often knocks or scratches."
    )],
    "meal": [(
        "Why is sharing food kind?",
        "Sharing food helps someone who is hungry feel safe and cared for. It also shows that you see their need and want to help."
    )],
    "blanket": [(
        "Why does a blanket help when someone is cold?",
        "A blanket holds warm air close to a body, so heat does not escape as quickly. That helps a cold creature warm up."
    )],
    "invite": [(
        "Why can inviting someone inside matter more than leaving food outside?",
        "Going inside gives both shelter and warmth, not only food. When the weather is harsh, a roof and a hearth can help as much as a meal."
    )],
}
KNOWLEDGE_ORDER = [
    "winter",
    "mouse",
    "bird",
    "hedgehog",
    "door",
    "shutter",
    "roof",
    "meal",
    "blanket",
    "invite",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    host = f["host"]
    visitor_cfg = f["visitor_cfg"]
    food = f["food_cfg"]
    season = f["season_cfg"]
    return [
        'Write a short fable for a 3-to-5-year-old that includes the words "eighth", "nip", and "cabin", and uses clear sound effects.',
        f"Tell a gentle animal fable where {host.id} hears a mysterious noise at a cabin on a cold night and answers it with kindness.",
        f"Write a story in which a hungry {visitor_cfg.label} outside a cabin becomes the unexpected eighth guest because someone shares {food.label} on a {season.id} night.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    host = f["host"]
    visitor_cfg = f["visitor_cfg"]
    food = f["food_cfg"]
    sound = f["sound_cfg"]
    outcome = f["outcome"]
    response = f["response_cfg"]
    season = f["season_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {host.id}, a kind forest host in a cabin, and a small {visitor_cfg.label} outside in the cold. The story follows the choice to answer a worrying sound with kindness."
        ),
        (
            "What strange sound did the host hear?",
            f"The sound came from the {sound.place}, and it was made of little noises like {' '.join(sound.noises)}. Those sound effects made the visitor seem mysterious before {host.id} knew who was there."
        ),
        (
            "Why did the sound happen?",
            f"The visitor was cold and hungry outside the cabin, so it tapped and scratched to ask for help. The noise was not a threat; it was a small creature trying to be noticed."
        ),
        (
            "Why did the story mention an eighth place?",
            f"There were seven places already waiting at the table, and kindness made room for one more. The eighth place shows that the cabin grew wider in spirit when someone needy arrived."
        ),
    ]
    if outcome == "welcomed":
        qa.append((
            f"How did {host.id} help the visitor?",
            f"{host.id} {response.qa_text}. That helped with both problems, because the visitor needed warmth as well as supper on that {season.id} night."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with eight places in the cabin instead of seven, and the smallest guest was smiling. The final image proves that kindness changed the house from a private supper into a shared shelter."
        ))
    else:
        qa.append((
            f"Was the host kind enough at first?",
            f"{host.id} was kind, but not kind enough to truly warm the visitor. Food on the porch helped a little, yet the visitor still had the cold night around it."
        ))
        qa.append((
            "What lesson did the ending teach?",
            "The ending taught that distant kindness is not as strong as open-door kindness. A gift helps, but shelter and welcome can help even more."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    f = world.facts
    tags |= set(f["season_cfg"].tags)
    tags |= set(f["visitor_cfg"].tags)
    tags |= set(f["sound_cfg"].tags)
    tags |= set(f["food_cfg"].tags)
    tags |= set(f["response_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def tell(
    season: Season,
    visitor_cfg: VisitorKind,
    food: Food,
    sound: SoundSource,
    response: Response,
    host_name: str = "Mira",
    host_type: str = "doe",
    delay: int = 0,
) -> World:
    world = World()
    host = world.add(Entity(
        id=host_name,
        kind="character",
        type=host_type,
        label="host",
        phrase=f"{host_name} of the pines",
        role="host",
        traits=["kind"],
    ))
    visitor = world.add(Entity(
        id="Guest",
        kind="character",
        type=visitor_cfg.type,
        label=visitor_cfg.label,
        phrase=visitor_cfg.phrase,
        role="visitor",
        attrs={"inside": False},
        tags=set(visitor_cfg.tags),
    ))
    cabin = world.add(Entity(
        id="cabin",
        kind="thing",
        type="cabin",
        label="cabin",
        phrase="a pine cabin",
        role="home",
    ))
    meal = world.add(Entity(
        id="meal",
        kind="thing",
        type="food",
        label=food.label,
        phrase=food.phrase,
        role="meal",
        attrs={"portions": food.portions},
        tags=set(food.tags),
    ))

    introduce(world, host, season, food)
    host_trait_line(world, host)

    world.para()
    start_noise(world, visitor, sound, visitor_cfg)
    wonder(world, host, sound)
    delay_beat(world, season, delay, sound)
    choose_kindness(world, host, visitor_cfg, sound)

    world.para()
    warmed = help_visitor(world, host, visitor, response, food, season, delay)
    table_turn(world, host, visitor_cfg, food, warmed)
    moral(world, warmed)

    world.facts.update(
        host=host,
        visitor=visitor,
        cabin=cabin,
        meal=meal,
        season_cfg=season,
        visitor_cfg=visitor_cfg,
        food_cfg=food,
        sound_cfg=sound,
        response_cfg=response,
        outcome="welcomed" if warmed else "porch",
        delay=delay,
        severity=cold_severity(season, delay),
        eighth_place=warmed,
    )
    return world


def explain_combo(visitor: VisitorKind, sound: SoundSource, food: Food) -> str:
    if not reachable(visitor, sound):
        return (
            f"(No story: a {visitor.label} does not plausibly make this noise at the {sound.place}. "
            f"Pick a sound source it can reach.)"
        )
    if not food_stretches(food):
        return (
            f"(No story: {food.label} only stretches to {food.portions} servings, so there is no honest eighth portion to share.)"
        )
    return "(No story: this combination does not fit the world.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try: {better}.)"
    )


ASP_RULES = r"""
reachable(V, S) :- visitor(V), sound(S), can_reach(V, S).
stretches(F) :- food(F), portions(F, P), P >= 8.
valid(Sea, V, F, S) :- season(Sea), reachable(V, S), stretches(F).

sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.

severity(C + D) :- chosen_season(Sea), cold(Sea, C), delay(D).
welcomed :- chosen_response(R), power(R, P), severity(V), P >= V.
outcome(welcomed) :- welcomed.
outcome(porch) :- not welcomed.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for season_id, season in SEASONS.items():
        lines.append(asp.fact("season", season_id))
        lines.append(asp.fact("cold", season_id, season.cold))
    for visitor_id, visitor in VISITORS.items():
        lines.append(asp.fact("visitor", visitor_id))
        for sound_id in sorted(visitor.can_reach):
            lines.append(asp.fact("can_reach", visitor_id, sound_id))
    for food_id, food in FOODS.items():
        lines.append(asp.fact("food", food_id))
        lines.append(asp.fact("portions", food_id, food.portions))
    for sound_id in SOUNDS:
        lines.append(asp.fact("sound", sound_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_season", params.season),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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
    for season_id in SEASONS:
        for response_id in RESPONSES:
            for delay in (0, 1, 2):
                cases.append(StoryParams(
                    season=season_id,
                    visitor="mouse",
                    food="porridge",
                    sound="door",
                    response=response_id,
                    host_name="Pip",
                    host_type="buck",
                    delay=delay,
                ))
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a kind cabin, a mysterious sound, and an unexpected eighth place."
    )
    ap.add_argument("--season", choices=SEASONS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--host-name")
    ap.add_argument("--host-type", choices=HOST_TYPES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the host hesitates before helping")
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
    if args.visitor and args.sound:
        visitor = VISITORS[args.visitor]
        sound = SOUNDS[args.sound]
        food = FOODS[args.food] if args.food else next(iter(FOODS.values()))
        if not reachable(visitor, sound):
            raise StoryError(explain_combo(visitor, sound, food))
    if args.food and not food_stretches(FOODS[args.food]):
        visitor = VISITORS[args.visitor] if args.visitor else next(iter(VISITORS.values()))
        sound = SOUNDS[args.sound] if args.sound else next(iter(SOUNDS.values()))
        raise StoryError(explain_combo(visitor, sound, FOODS[args.food]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.season is None or combo[0] == args.season)
        and (args.visitor is None or combo[1] == args.visitor)
        and (args.food is None or combo[2] == args.food)
        and (args.sound is None or combo[3] == args.sound)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    season_id, visitor_id, food_id, sound_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    host_name = args.host_name or rng.choice(HOST_NAMES)
    host_type = args.host_type or rng.choice(HOST_TYPES)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])

    return StoryParams(
        season=season_id,
        visitor=visitor_id,
        food=food_id,
        sound=sound_id,
        response=response_id,
        host_name=host_name,
        host_type=host_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        season = SEASONS[params.season]
        visitor_cfg = VISITORS[params.visitor]
        food = FOODS[params.food]
        sound = SOUNDS[params.sound]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if not reachable(visitor_cfg, sound) or not food_stretches(food):
        raise StoryError(explain_combo(visitor_cfg, sound, food))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        season=season,
        visitor_cfg=visitor_cfg,
        food=food,
        sound=sound,
        response=response,
        host_name=params.host_name,
        host_type=params.host_type,
        delay=params.delay,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (season, visitor, food, sound) combos:\n")
        for season_id, visitor_id, food_id, sound_id in combos:
            print(f"  {season_id:6} {visitor_id:9} {food_id:8} {sound_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = (
                f"### {p.host_name}: {p.visitor} at the {p.sound} "
                f"({p.season}, {p.food}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()

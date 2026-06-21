#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/magnum_bravery_curiosity_dialogue_bedtime_story.py
=============================================================================

A standalone story world about a small bedtime mystery: a child hears a soft
night sound, feels both frightened and curious, and discovers that bravery can
mean asking for help or looking carefully with safe light.

The word "magnum" appears in the world as the writing on the family dog's tag.

Run it
------
    python storyworlds/worlds/gpt-5.4/magnum_bravery_curiosity_dialogue_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/magnum_bravery_curiosity_dialogue_bedtime_story.py --spot window --source branch_tap --response call_parent
    python storyworlds/worlds/gpt-5.4/magnum_bravery_curiosity_dialogue_bedtime_story.py --source branch_tap --response star_lamp
    python storyworlds/worlds/gpt-5.4/magnum_bravery_curiosity_dialogue_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/magnum_bravery_curiosity_dialogue_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/magnum_bravery_curiosity_dialogue_bedtime_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
class Spot:
    id: str
    phrase: str
    from_bed: str
    approach: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    spot: str
    need: str
    sound_text: str
    worry_text: str
    reveal_text: str
    settle_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    capabilities: set[str]
    opening: str
    action: str
    brave_meaning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    spot: str
    source: str
    response: str
    hero: str
    gender: str
    parent: str
    comfort: str
    trait: str
    seed: Optional[int] = None


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


def _r_noise_stirs(world: World) -> list[str]:
    hero = world.get("hero")
    source = world.get("source")
    if source.meters["noisy"] < THRESHOLD:
        return []
    sig = ("noise_stirs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["curiosity"] += 1
    return []


def _r_light_softens(world: World) -> list[str]:
    room = world.get("room")
    hero = world.get("hero")
    if room.meters["lit"] < THRESHOLD:
        return []
    sig = ("light_softens",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if hero.memes["fear"] >= THRESHOLD:
        hero.memes["fear"] -= 1
    hero.memes["hope"] += 1
    return []


def _r_found_calm(world: World) -> list[str]:
    hero = world.get("hero")
    source = world.get("source")
    room = world.get("room")
    if source.meters["found"] < THRESHOLD:
        return []
    sig = ("found_calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["bravery"] += 1
    hero.memes["sleepy"] += 1
    room.meters["calm"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="noise_stirs", tag="emotion", apply=_r_noise_stirs),
    Rule(name="light_softens", tag="emotion", apply=_r_light_softens),
    Rule(name="found_calm", tag="emotion", apply=_r_found_calm),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SPOTS = {
    "window": Spot(
        id="window",
        phrase="the window beside the curtain",
        from_bed="near the window",
        approach="the moonlit window",
        glow="where a silver square of moonlight lay on the floor",
        tags={"window"},
    ),
    "under_bed": Spot(
        id="under_bed",
        phrase="the shadow under the bed",
        from_bed="under the bed",
        approach="the edge of the bed skirt",
        glow="where the rug disappeared into a dark little cave",
        tags={"under_bed"},
    ),
    "toy_corner": Spot(
        id="toy_corner",
        phrase="the toy corner by the shelf",
        from_bed="by the toy shelf",
        approach="the toy corner",
        glow="where blocks and books made small moonlit shapes",
        tags={"toys"},
    ),
    "doorway": Spot(
        id="doorway",
        phrase="the bedroom doorway",
        from_bed="at the doorway",
        approach="the open doorway",
        glow="where the hall made a pale line beyond the room",
        tags={"doorway"},
    ),
}

SOURCES = {
    "branch_tap": Source(
        id="branch_tap",
        label="a tapping branch",
        spot="window",
        need="adult",
        sound_text="tap... tap... tap",
        worry_text="as if tiny knuckles were asking to come in",
        reveal_text="a windy branch was brushing the glass with soft little taps",
        settle_text="The latch was checked, the curtain was tucked back, and the sound became only a sleepy rustle outside.",
        tags={"branch", "window"},
    ),
    "blanket_tail": Source(
        id="blanket_tail",
        label="a slipping blanket tail",
        spot="under_bed",
        need="peek",
        sound_text="shff... shff",
        worry_text="as if something small were creeping through the dark",
        reveal_text="the loose corner of the blanket had slid down and was rubbing the rug whenever Magnum's tail thumped nearby",
        settle_text="The blanket was tucked back up, and the dark under the bed looked ordinary again.",
        tags={"blanket", "under_bed"},
    ),
    "marble_roll": Source(
        id="marble_roll",
        label="a rolling marble",
        spot="toy_corner",
        need="peek",
        sound_text="tik... tik... tik",
        worry_text="as if a tiny foot were tiptoeing among the toys",
        reveal_text="a shiny marble had rolled from the toy basket and was knocking softly against a wooden block",
        settle_text="The marble went back into the basket, and the corner grew still.",
        tags={"marble", "toys"},
    ),
    "magnum_snore": Source(
        id="magnum_snore",
        label="Magnum's sleepy snore",
        spot="doorway",
        need="peek",
        sound_text="hrrmph... hrrmph",
        worry_text="as if a mysterious creature were puffing in the hall",
        reveal_text="Magnum had curled by the doorway and was making a round, rumbling snore in his dreams",
        settle_text="When he woke, he wagged once, turned in a circle, and settled with his chin on his paws.",
        tags={"dog", "snore"},
    ),
}

RESPONSES = {
    "call_parent": Response(
        id="call_parent",
        sense=4,
        capabilities={"peek", "adult"},
        opening="called softly for a grown-up instead of staying alone with the worry",
        action="Parent came in at once, sat at the side of the bed, and listened before helping check the sound",
        brave_meaning="Bravery, Parent said, can sound quiet. Sometimes it is a whisper that asks for help.",
        tags={"ask_help", "adult"},
    ),
    "star_lamp": Response(
        id="star_lamp",
        sense=3,
        capabilities={"peek"},
        opening="remembered the bedtime rule: light first, then look carefully",
        action="Hero clicked on the little star lamp and stayed on the rug while peeking with Magnum close by",
        brave_meaning="Bravery, Hero decided, can be gentle too. It can mean looking slowly instead of imagining the worst.",
        tags={"lamp", "light"},
    ),
    "hide_under_quilt": Response(
        id="hide_under_quilt",
        sense=1,
        capabilities=set(),
        opening="hid under the quilt and guessed at the sound",
        action="No one checked, so the room stayed full of wondering",
        brave_meaning="This is not a response the storyworld accepts.",
        tags={"hide"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Max", "Noah", "Finn", "Theo", "Eli"]
COMFORTS = ["soft rabbit", "small moon pillow", "striped bear", "little quilted fox"]
TRAITS = ["curious", "gentle", "thoughtful", "brave", "careful"]


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def source_matches_spot(source: Source, spot: Spot) -> bool:
    return source.spot == spot.id


def response_handles(source: Source, response: Response) -> bool:
    return source.need in response.capabilities


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for spot_id, spot in SPOTS.items():
        for source_id, source in SOURCES.items():
            if not source_matches_spot(source, spot):
                continue
            for response in sensible_responses():
                if response_handles(source, response):
                    combos.append((spot_id, source_id, response.id))
    return combos


def explain_spot_mismatch(source: Source, spot: Spot) -> str:
    return (
        f"(No story: {source.label} belongs at {SPOTS[source.spot].phrase}, not at "
        f"{spot.phrase}. Pick the matching spot so the bedtime mystery stays grounded.)"
    )


def explain_response(source: Source, response: Response) -> str:
    if response.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_responses()))
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Try: {better}.)"
        )
    return (
        f"(No story: {response.id} cannot honestly reveal {source.label}. "
        f"That sound needs a response that can handle '{source.need}'.)"
    )


def predict_calm(world: World, response_id: str) -> dict:
    sim = world.copy()
    room = sim.get("room")
    source = sim.get("source")
    response = RESPONSES[response_id]
    if "peek" in response.capabilities:
        room.meters["lit"] += 1
    if source.need in response.capabilities:
        source.meters["found"] += 1
    propagate(sim, narrate=False)
    return {
        "found": source.meters["found"] >= THRESHOLD,
        "calm": room.meters["calm"] >= THRESHOLD,
    }


def bedtime_setup(world: World, hero: Entity, parent: Entity, comfort: str, spot: Spot) -> None:
    world.say(
        f"It was bedtime, and {hero.id}'s room had gone soft and blue with moonlight. "
        f"{parent.label_word.capitalize()} had already tucked {hero.pronoun('object')} in with a {comfort}."
    )
    world.say(
        f"At the foot of the bed lay the family dog, Magnum. On his round tag, the word "
        f"magnum winked in the moonlight while he kept one sleepy eye on {hero.id}."
    )
    world.say(
        f"The room was quiet enough to hear the clock breathe and to see {spot.glow}."
    )


def hear_sound(world: World, hero: Entity, source: Source, spot: Spot) -> None:
    src = world.get("source")
    src.meters["noisy"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a sound came from {spot.phrase}: {source.sound_text}. It was only a small sound, "
        f"but in the dark it felt bigger, {source.worry_text}."
    )
    world.say(
        f"{hero.id} sat up a little. {hero.pronoun('possessive').capitalize()} heart gave a jump, "
        f"and so did {hero.pronoun('possessive')} curiosity."
    )


def whisper(world: World, hero: Entity, source: Source) -> None:
    world.say(
        f'"Magnum," {hero.id} whispered, "did you hear that?"'
    )
    if source.id == "magnum_snore":
        world.say(
            'Magnum answered with another soft "hrrmph," which did not solve the mystery at all.'
        )
    else:
        world.say(
            "Magnum lifted his head, thumped his tail once, and listened too."
        )


def choose_response(world: World, hero: Entity, parent: Entity, response: Response, source: Source) -> None:
    pred = predict_calm(world, response.id)
    world.facts["predicted_found"] = pred["found"]
    world.say(
        f"{hero.id} was still curious enough to want the true answer. So {hero.pronoun()} {response.opening}."
    )
    if response.id == "call_parent":
        hero.memes["trust"] += 1
        world.say(
            f'"{parent.label_word.capitalize()}?" {hero.id} called. "There is a sound, and I want to know what it is."'
        )
        world.say(
            f'{parent.label_word.capitalize()} came in right away. "{response.action}," '
            f'{parent.pronoun()} said. "We can be brave and careful at the same time."'
        )
    elif response.id == "star_lamp":
        world.say(
            f'"I want to know," {hero.id} whispered, "but I want to know safely."'
        )
        world.say(
            f"So {hero.pronoun()} did exactly that: {response.action}."
        )


def investigate(world: World, hero: Entity, parent: Entity, spot: Spot, source: Source, response: Response) -> None:
    room = world.get("room")
    src = world.get("source")
    room.meters["lit"] += 1
    if response.id == "call_parent":
        world.say(
            f"Together they looked toward {spot.approach}. Magnum padded after them so close that his warm side brushed {hero.id}'s ankle."
        )
    else:
        world.say(
            f"The little lamp painted warm stars across the room. With Magnum beside {hero.pronoun('object')}, {hero.id} leaned just enough to see {spot.from_bed}."
        )
    propagate(world, narrate=False)
    src.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the mystery opened like a small folded paper. It was only this: {source.reveal_text}."
    )


def settle(world: World, hero: Entity, parent: Entity, source: Source, response: Response) -> None:
    world.say(source.settle_text)
    if response.id == "call_parent":
        world.say(
            f'{parent.label_word.capitalize()} smiled and brushed {hero.id}\'s hair back. "{response.brave_meaning}"'
        )
    else:
        world.say(
            f'{response.brave_meaning}'
        )
    if source.id == "magnum_snore":
        world.say(
            f'{hero.id} laughed a tiny bedtime laugh. "It was you all along, Magnum."'
        )
    else:
        world.say(
            f'"It was not a scary thing after all," {hero.id} said, feeling the room grow ordinary and kind again.'
        )
    world.say(
        f"Soon Magnum curled in his place, {hero.id} sank into the pillow, and the room sounded like a room again instead of a riddle."
    )


def tell(
    *,
    spot: Spot,
    source: Source,
    response: Response,
    hero_name: str,
    hero_type: str,
    parent_type: str,
    comfort: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    magnum = world.add(Entity(id="magnum", kind="character", type="dog", label="Magnum", role="dog"))
    room = world.add(Entity(id="room", type="bedroom", label="the bedroom"))
    src = world.add(Entity(id="source", type="source", label=source.label))
    hero.attrs["name"] = hero_name
    hero.attrs["trait"] = trait
    hero.attrs["comfort"] = comfort
    parent.attrs["name"] = parent.label_word.capitalize()
    magnum.attrs["tag_name"] = "magnum"

    bedtime_setup(world, hero, parent, comfort, spot)
    world.para()
    hear_sound(world, hero, source, spot)
    whisper(world, hero, source)
    choose_response(world, hero, parent, response, source)
    world.para()
    investigate(world, hero, parent, spot, source, response)
    settle(world, hero, parent, source, response)

    world.facts.update(
        hero=hero,
        parent=parent,
        magnum=magnum,
        room=room,
        source_cfg=source,
        source=src,
        spot=spot,
        response=response,
        comfort=comfort,
        trait=trait,
        found=src.meters["found"] >= THRESHOLD,
        calm=room.meters["calm"] >= THRESHOLD,
        bravery=hero.memes["bravery"] >= THRESHOLD,
    )
    return world


def pair_name(entity: Entity) -> str:
    return entity.attrs.get("name", entity.label or entity.id)


KNOWLEDGE = {
    "ask_help": [
        (
            "Can asking for help be brave?",
            "Yes. Asking for help is brave because it means telling the truth about what you need instead of hiding with a worry."
        )
    ],
    "lamp": [
        (
            "Why does a night-lamp help at bedtime?",
            "A night-lamp adds gentle light, so your eyes can see what is really there. That makes it easier for your mind to stop turning little sounds into big fears."
        )
    ],
    "window": [
        (
            "Why do branches tap on windows at night?",
            "When wind moves a tree branch, it can brush the glass and make a soft tapping sound. In a quiet room, that sound can seem louder than it really is."
        )
    ],
    "under_bed": [
        (
            "Why can the space under a bed feel scary?",
            "It is dark and partly hidden, so your imagination fills in what you cannot see. A little light often shows that it is only an ordinary shadowy space."
        )
    ],
    "toys": [
        (
            "Why can toys make sounds by themselves?",
            "If a toy is loose or round, it can roll or bump another toy when the floor shakes a little. That can make tiny sounds in a quiet room."
        )
    ],
    "dog": [
        (
            "Do dogs snore when they sleep?",
            "Some dogs do. When they are deeply asleep, their breathing can make soft snuffling or rumbling sounds."
        )
    ],
    "snore": [
        (
            "What is a snore?",
            "A snore is a sound made while someone or some animal is asleep and breathing in a noisy way."
        )
    ],
    "blanket": [
        (
            "Why might a blanket make a sound on the floor?",
            "If a blanket corner slips down and rubs on the rug, it can make a soft dragging sound when it moves."
        )
    ],
    "marble": [
        (
            "Why does a marble make ticking sounds?",
            "A marble is hard and round, so when it rolls and taps wood or another toy, it makes a small clear clicking sound."
        )
    ],
}
KNOWLEDGE_ORDER = ["ask_help", "lamp", "window", "under_bed", "toys", "blanket", "marble", "dog", "snore"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    source = world.facts["source_cfg"]
    response = world.facts["response"]
    spot = world.facts["spot"]
    name = pair_name(hero)
    return [
        (
            f'Write a gentle bedtime story for a 3-to-5-year-old where a child named {name} '
            f'hears a small night sound at {spot.phrase}, feels both brave and curious, and includes dialogue and the word "magnum".'
        ),
        (
            f"Tell a bedtime mystery where {name} hears {source.sound_text} from {spot.phrase} "
            f"and solves it by {response.id.replace('_', ' ')}."
        ),
        (
            f"Write a calm story in which bravery means {response.brave_meaning.lower()} "
            f"and the ending shows the room becoming peaceful again."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    source = world.facts["source_cfg"]
    spot = world.facts["spot"]
    response = world.facts["response"]
    name = pair_name(hero)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, {pw}, and their dog Magnum. The story follows them through one small bedtime mystery."
        ),
        (
            "What happened at bedtime?",
            f"{name} heard a sound from {spot.phrase}. In the dark it felt bigger than it really was, so fear and curiosity both woke up at the same time."
        ),
        (
            f"Why did {name} not stay scared forever?",
            f"{name} wanted the true answer more than a pretend scary one, so {hero.pronoun('subject')} chose a careful response. That safe step turned the mystery into something that could be understood."
        ),
        (
            f"What was the sound really?",
            f"It was {source.reveal_text}. The answer was ordinary once someone looked closely."
        ),
    ]
    if response.id == "call_parent":
        qa.append(
            (
                f"How was {name} brave?",
                f"{name} was brave by calling for {pw} and telling the truth about the worry. In this story, bravery means asking for help and then looking carefully together."
            )
        )
    else:
        qa.append(
            (
                f"How was {name} brave?",
                f"{name} was brave by turning on safe light and checking slowly instead of guessing in the dark. Magnum stayed close, which helped the careful plan feel possible."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The sound was explained, the room felt calm again, and {name} could settle back into bed. The ending proves the change because the room stops feeling like a riddle and starts feeling ordinary and sleepy."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    source = world.facts["source_cfg"]
    response = world.facts["response"]
    tags = set(source.tags) | set(response.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Spot, Src, Resp) :- spot(Spot), source(Src), response(Resp),
                          source_at(Src, Spot), sensible(Resp),
                          needs(Src, Need), capable(Resp, Need).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("source_at", source_id, source.spot))
        lines.append(asp.fact("needs", source_id, source.need))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        for cap in sorted(response.capabilities):
            lines.append(asp.fact("capable", response_id, cap))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


CURATED = [
    StoryParams(
        spot="window",
        source="branch_tap",
        response="call_parent",
        hero="Lily",
        gender="girl",
        parent="mother",
        comfort="soft rabbit",
        trait="curious",
    ),
    StoryParams(
        spot="under_bed",
        source="blanket_tail",
        response="star_lamp",
        hero="Ben",
        gender="boy",
        parent="father",
        comfort="little quilted fox",
        trait="thoughtful",
    ),
    StoryParams(
        spot="toy_corner",
        source="marble_roll",
        response="call_parent",
        hero="Mia",
        gender="girl",
        parent="mother",
        comfort="small moon pillow",
        trait="careful",
    ),
    StoryParams(
        spot="doorway",
        source="magnum_snore",
        response="star_lamp",
        hero="Theo",
        gender="boy",
        parent="father",
        comfort="striped bear",
        trait="gentle",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a soft night sound, Magnum, and a brave bedtime answer."
    )
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.spot:
        source = SOURCES[args.source]
        spot = SPOTS[args.spot]
        if not source_matches_spot(source, spot):
            raise StoryError(explain_spot_mismatch(source, spot))
    if args.source and args.response:
        source = SOURCES[args.source]
        response = RESPONSES[args.response]
        if not response_handles(source, response) or response.sense < SENSE_MIN:
            raise StoryError(explain_response(source, response))

    combos = [
        combo for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.source is None or combo[1] == args.source)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spot_id, source_id, response_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    comfort = rng.choice(COMFORTS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        spot=spot_id,
        source=source_id,
        response=response_id,
        hero=hero,
        gender=gender,
        parent=parent,
        comfort=comfort,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    spot = SPOTS[params.spot]
    source = SOURCES[params.source]
    response = RESPONSES[params.response]

    if not source_matches_spot(source, spot):
        raise StoryError(explain_spot_mismatch(source, spot))
    if not response_handles(source, response) or response.sense < SENSE_MIN:
        raise StoryError(explain_response(source, response))

    world = tell(
        spot=spot,
        source=source,
        response=response,
        hero_name=params.hero,
        hero_type=params.gender,
        parent_type=params.parent,
        comfort=params.comfort,
        trait=params.trait,
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

    c_sense = set(asp_sensible())
    p_sense = {r.id for r in sensible_responses()}
    if c_sense == p_sense:
        print(f"OK: sensible responses match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "magnum" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story was empty or missed the seed word.)")
        print("OK: curated smoke test generated a bedtime story.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(0))
        sample = generate(params)
        if not sample.story:
            raise StoryError("(Smoke test failed: random generation returned an empty story.)")
        print("OK: default random generation succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show sensible/1.\n#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (spot, source, response) combos:\n")
        for spot, source, response in combos:
            print(f"  {spot:10} {source:12} {response}")
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
            header = f"### {p.hero}: {p.source} at {p.spot} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

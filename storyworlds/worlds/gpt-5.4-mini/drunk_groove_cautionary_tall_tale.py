#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/drunk_groove_cautionary_tall_tale.py
=====================================================================

A small, standalone story world in a tall-tale register about a lively groove,
a drink-too-much mistake, a near-spiral, and a calm stop before the music goes
truly sour. The world is deliberately tiny: one fiddler, one friend, one saloon,
one risky cup, and one dancing groove that can carry a crowd too far.

The tale is cautionary in the old yarn-spinning sense:
- music can be joyful and wild,
- but if a player is drunk, the groove can wobble into trouble,
- and the sensible choice is to stop, swap the cup for water, and keep the band
  together without harm.

The prose is state-driven: emotional and physical meters accumulate, decisions
change the world, and the ending image proves what changed.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    label: str
    detail: str
    crowd: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Groove:
    id: str
    label: str
    phrase: str
    danger: str
    joy: str
    tempo: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Drink:
    id: str
    label: str
    phrase: str
    strength: int
    harmless: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    fiddler = world.get("fiddler")
    if fiddler.meters["drunk"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fiddler.meters["wobble"] += 1
    fiddler.memes["unease"] += 1
    world.get("band").meters["risk"] += 1
    out.append("__wobble__")
    return out


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    if world.get("band").meters["risk"] < THRESHOLD:
        return out
    sig = ("spread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("crowd").memes["restless"] += 1
    world.get("friend").memes["worry"] += 1
    out.append("__restless__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("wobble", "physical", _r_wobble),
    Rule("spread", "social", _r_spread),
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
        for s in produced:
            world.say(s)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def hazard_at_risk(drink: Drink, groove: Groove) -> bool:
    return drink.strength >= 2 and groove.id == "wild"


def fire_severity(drink: Drink, delay: int) -> int:
    return drink.strength + delay


def is_contained(response: Response, drink: Drink, delay: int) -> bool:
    return response.power >= fire_severity(drink, delay)


def predict_trouble(world: World, drink_id: str) -> dict:
    sim = world.copy()
    _do_drink(sim, sim.get(drink_id), narrate=False)
    return {
        "wobble": sim.get("fiddler").meters["wobble"] >= THRESHOLD,
        "risk": sim.get("band").meters["risk"],
    }


def _do_drink(world: World, drink: Entity, narrate: bool = True) -> None:
    drink.meters["drunk"] += 1
    drink.meters["empty"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, fiddler: Entity, friend: Entity, setting: Setting, groove: Groove) -> None:
    fiddler.memes["pride"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In {setting.label}, where the lanterns leaned like sleepy moons, "
        f"{fiddler.id} was playing {groove.phrase}. {setting.detail}"
    )
    world.say(
        f"{friend.id} stomped and clapped while the crowd packed the room "
        f"thick as corn in a jar."
    )


def tempt(world: World, fiddler: Entity, drink: Drink, groove: Groove) -> None:
    fiddler.memes["longing"] += 1
    world.say(
        f"The tune hit a bold groove, and {fiddler.id} grinned at "
        f"{drink.phrase} by the fiddle case. \"Just one sip won't hurt the song,\" "
        f"{fiddler.pronoun()} said."
    )
    world.say("But the old barn smell of the place and the dancing feet made that sip look bigger than it was.")


def warn(world: World, friend: Entity, fiddler: Entity, drink: Drink, groove: Groove) -> None:
    pred = predict_trouble(world, "drink")
    friend.memes["worry"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f"{friend.id} touched {fiddler.pronoun('possessive')} sleeve. "
        f"\"Easy now,\" {friend.pronoun()} said. \"That {drink.label} can make a head swim, "
        f"and a drunk player can lose the groove.\""
    )


def defy(world: World, fiddler: Entity, drink: Drink) -> None:
    fiddler.meters["drunk"] += 1
    fiddler.memes["defiance"] += 1
    world.say(
        f"\"I can play straight as a fencepost,\" {fiddler.id} laughed, and took the drink anyway."
    )


def wobble(world: World, fiddler: Entity, groove: Groove) -> None:
    world.say(
        f"At once the groove turned lopsided. {fiddler.id}'s bow skidded like a wagon on ice, "
        f"and the tune began to stagger."
    )


def alarm(world: World, friend: Entity, fiddler: Entity) -> None:
    world.say(
        f"{friend.id} saw the wobble and cried, \"Stop the tune before the whole hall gets dizzy!\""
    )


def rescue(world: World, parent: Entity, response: Response, drink: Drink, groove: Groove) -> None:
    body = response.text.replace("{drink}", drink.label)
    world.say(
        f"{parent.label_word.capitalize()} came from the doorway in two long strides and {body}."
    )
    world.say(
        f"The song steadied, the room quit spinning, and the groove settled back into a safe, bright beat."
    )


def lesson(world: World, parent: Entity, fiddler: Entity, friend: Entity, drink: Drink) -> None:
    fiddler.memes["lesson"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} said, \"Music is a fine horse, but a drunk rider can fall off. "
        f"Keep the cup away from the bow.\""
    )
    world.say(
        f"{fiddler.id} nodded, shamefaced and sorry, and set the {drink.label} aside for water instead."
    )


def safe_finish(world: World, parent: Entity, fiddler: Entity, friend: Entity, groove: Groove) -> None:
    fiddler.meters["drunk"] = 0.0
    fiddler.meters["water"] += 1
    fiddler.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Before long, {fiddler.id} lifted a tin cup of water and played the same groove clean and true."
    )
    world.say(
        f"The crowd cheered as the tall-tale tune rolled on, bright as sunrise on river glass, "
        f"and nobody had to fear the wobbly drink again."
    )


def tell(setting: Setting, groove: Groove, drink: Drink, response: Response,
         fiddler_name: str = "Rufus", fiddler_gender: str = "boy",
         friend_name: str = "Mabel", friend_gender: str = "girl",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    fiddler = world.add(Entity(id=fiddler_name, kind="character", type=fiddler_gender, role="instigator"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="cautioner"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="band", label="the band"))
    world.add(Entity(id="crowd", label="the crowd"))
    world.add(Entity(id="drink", label=drink.label))
    world.facts["delay"] = delay
    world.facts["setting"] = setting
    world.facts["groove"] = groove
    world.facts["drink_cfg"] = drink

    setup(world, fiddler, friend, setting, groove)
    world.para()
    tempt(world, fiddler, drink, groove)
    warn(world, friend, fiddler, drink, groove)

    contained = is_contained(response, drink, delay)
    if hazard_at_risk(drink, groove):
        defy(world, fiddler, drink)
        world.para()
        wobble(world, fiddler, groove)
        alarm(world, friend, fiddler)
        if contained:
            world.para()
            rescue(world, parent, response, drink, groove)
            lesson(world, parent, fiddler, friend, drink)
            world.para()
            safe_finish(world, parent, fiddler, friend, groove)
            outcome = "contained"
        else:
            world.say("The tune ran wild enough to chase the moon behind a cloud, and the whole hall had to scatter.")
            outcome = "burned"
    else:
        world.say("Mabel took the cup away before it could spoil the music, and the groove stayed merry and level.")
        world.para()
        safe_finish(world, parent, fiddler, friend, groove)
        outcome = "averted"

    world.facts.update(
        fiddler=fiddler, friend=friend, parent=parent, outcome=outcome,
        contained=contained, lesson=True,
    )
    return world


SETTINGS = {
    "saloon": Setting("saloon", "the river saloon", "The floorboards creaked like old geese, and a lamp swung over the bandstand.", "crowd"),
    "barn": Setting("barn", "the hay barn", "The rafters hummed, and the dust danced where the boots hit.", "crowd"),
    "fair": Setting("fair", "the county fair tent", "The canvas flapped, and the midway lights blinked like fireflies.", "crowd"),
}

GROOVES = {
    "wild": Groove("wild", "a wild groove", "a wild groove", "drunk", "merry", "fast", tags={"groove"}),
    "river": Groove("river", "a river groove", "a river groove", "drunk", "shiny", "steady", tags={"groove"}),
    "square": Groove("square", "a square-dance groove", "a square-dance groove", "drunk", "spry", "quick", tags={"groove"}),
}

DRINKS = {
    "whiskey": Drink("whiskey", "whiskey", "a glass of whiskey", 3, "watered down", tags={"drink"}),
    "cider": Drink("cider", "hard cider", "a mug of hard cider", 2, "gentle", tags={"drink"}),
    "brandy": Drink("brandy", "brandy", "a little brandy", 2, "strong", tags={"drink"}),
}

RESPONSES = {
    "water": Response("water", 3, 4, "set the drink aside and poured a cool cup of water for {drink}", "couldn't steady the room at all", "set the drink aside and poured water for {drink}", tags={"water"}),
    "pause": Response("pause", 2, 3, "called for a pause, put the bow down, and waited for the head-sway to pass", "tried to pause, but the wobble had already grown too big", "called for a pause and put the bow down", tags={"pause"}),
    "stool": Response("stool", 2, 2, "sat the fiddler on a sturdy stool and let the room quiet down", "sat the fiddler down, but the room kept spinning", "sat the fiddler on a sturdy stool", tags={"stool"}),
}

GROOVE_ORDER = ["groove", "drink", "water", "pause", "stool"]

CURATED = [
    StoryParams := None
]

@dataclass
class StoryParams:
    setting: str
    groove: str
    drink: str
    response: str
    fiddler: str
    fiddler_gender: str
    friend: str
    friend_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    StoryParams("saloon", "wild", "whiskey", "water", "Rufus", "boy", "Mabel", "girl", "mother", 0),
    StoryParams("barn", "river", "brandy", "pause", "Clara", "girl", "Hank", "boy", "father", 0),
    StoryParams("fair", "square", "cider", "stool", "Jed", "boy", "Nina", "girl", "mother", 1),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for g in GROOVES:
            for d in DRINKS:
                if hazard_at_risk(DRINKS[d], GROOVES[g]) and sensible_responses():
                    combos.append((s, g, d))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary tall-tale story world about a drunk groove and a safer ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--groove", choices=GROOVES)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--fiddler")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.groove and args.drink:
        if not hazard_at_risk(DRINKS[args.drink], GROOVES[args.groove]):
            raise StoryError("No story: that drink would not upset that groove enough for a cautionary tale.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.groove is None or c[1] == args.groove)
              and (args.drink is None or c[2] == args.drink)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, groove, drink = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    fiddler = args.fiddler or rng.choice(["Rufus", "Clara", "Jed", "Pearl"])
    friend = args.friend or rng.choice(["Mabel", "Hank", "Nina", "Otis"])
    parent = args.parent or rng.choice(["mother", "father"])
    fgender = "girl" if fiddler in {"Clara", "Pearl"} else "boy"
    frgender = "girl" if friend in {"Mabel", "Nina"} else "boy"
    return StoryParams(setting, groove, drink, response, fiddler, fgender, friend, frgender, parent, delay=rng.randint(0, 1))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], GROOVES[params.groove], DRINKS[params.drink], RESPONSES[params.response],
                 params.fiddler, params.fiddler_gender, params.friend, params.friend_gender, params.parent, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary tall tale for a young child that includes the words "drunk" and "groove".',
        f"Tell a tall tale where {f['fiddler'].id} wants one sip from a drink and the groove begins to wobble, but a friend warns them in time.",
        f"Write a child-facing story about music, a drunk mistake, and a safer choice that keeps the groove going without harm.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    fiddler, friend, parent = f["fiddler"], f["friend"], f["parent"]
    drink, groove, setting = f["drink_cfg"], f["groove"], f["setting"]
    qa = [
        ("Who is the story about?", f"It is about {fiddler.id}, {friend.id}, and the music they made in {setting.label}."),
        ("Why did the friend worry?", f"{friend.id} worried because the {drink.label} could make {fiddler.id} drunk and throw the groove off. That kind of wobble can turn a lively tune into a risky one."),
    ]
    if f["outcome"] == "contained":
        qa.append(("How did the grown-up help?", f"{parent.label_word.capitalize()} stopped the danger with {RESPONSES[f['response']].qa_text.replace('{drink}', drink.label)}. After that, the groove steadied and the crowd could keep dancing safely."))
        qa.append(("How did the story end?", f"It ended with water instead of liquor, and the groove came back clean and true. The ending image proves the music was saved without anyone getting hurt."))
    elif f["outcome"] == "averted":
        qa.append(("What happened before trouble started?", f"{friend.id} took the drink away before it could spoil the song, so the groove never slipped into trouble. The band kept its feet under it and the hall stayed calm."))
    else:
        qa.append(("What happened when the warning was ignored?", f"The groove got wild enough that the hall had to scatter. The drunk choice turned a happy tune into a cautionary mess."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"groove", "drink"}
    if world.facts["outcome"] == "contained":
        tags |= {"water"}
    out: list[tuple[str, str]] = []
    if "groove" in tags:
        out.append(("What is a groove in music?", "A groove is the steady, moving beat that makes music easy to clap, dance, or tap along to."))
    if "drink" in tags:
        out.append(("Why can too much drink be dangerous?", "Too much drink can make a person dizzy, confused, or clumsy, so it can lead to bad choices or accidents."))
    if "water" in tags:
        out.append(("Why is water a good choice instead of whiskey?", "Water is safe and clear, and it helps a person settle down without making them drunk."))
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(D, G) :- drink(D), groove(G), strong(D, S), S >= 2, wild(G).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, G, D) :- setting(S), groove(G), drink(D), hazard(D, G).
outcome(contained) :- chosen_response(R), power(R, P), severity(V), P >= V.
outcome(burned) :- not outcome(contained), hazard(chosen_drink, chosen_groove).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid, g in GROOVES.items():
        lines.append(asp.fact("groove", gid))
        if gid == "wild":
            lines.append(asp.fact("wild", gid))
    for did, d in DRINKS.items():
        lines.append(asp.fact("drink", did))
        lines.append(asp.fact("strong", did, d.strength))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        _ = sample.to_json()
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def outcome_of(params: StoryParams) -> str:
    if not hazard_at_risk(DRINKS[params.drink], GROOVES[params.groove]):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], DRINKS[params.drink], params.delay) else "burned"


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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, g, d in asp_valid_combos():
            print(f"  {s:8} {g:8} {d}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.fiddler}: {p.groove} / {p.drink} ({outcome_of(p)})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/million_element_tolerate_fallen_tree_trail_cautionary.py
=========================================================================================

A small fairy-tale cautionary story world set on a fallen tree trail.

Premise:
- Two children or a child and a brave helper go down a trail where a fallen tree
  blocks the way.
- One character wants to rush ahead with a sharp little "element" from a knapsack
  or touch something risky.
- Another character is cautious and warns them to tolerate waiting, thinking,
  and asking for help.
- Bravery is tested: the brave choice is not to act quickly, but to act wisely.

This world is intentionally tiny and state-driven. It generates a complete story,
three Q&A sets, and supports a Python/ASP parity check.

Seed words woven into the domain:
- million
- element
- tolerate

Setting:
- fallen tree trail

Style:
- Fairy Tale
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
BRAVERY_BASE = 5.0


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
        female = {"girl", "mother", "mom", "queen", "woman"}
        male = {"boy", "father", "dad", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen", "king": "king"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    mood: str
    features: list[str]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class RiskyElement:
    id: str
    label: str
    phrase: str
    danger: str
    cause: str
    result: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class TrailObstacle:
    id: str
    label: str
    phrase: str
    blocked_by: str
    flinch: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Remedy:
    id: str
    sense: int
    power: int
    phrase: str
    fail_phrase: str
    result_phrase: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_alarm(world: World) -> list[str]:
    out = []
    if world.get("trail").meters["blocked"] >= THRESHOLD and ("alarm",) not in world.fired:
        world.fired.add(("alarm",))
        for kid in ("hero", "companion"):
            if kid in world.entities:
                world.get(kid).memes["worry"] += 1
        out.append("__alarm__")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    if world.get("trail").meters["safe"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        for kid in ("hero", "companion"):
            if kid in world.entities:
                world.get(kid).memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("alarm", _r_alarm), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def valid_element(element: RiskyElement, obstacle: TrailObstacle) -> bool:
    return element.id == "spark" and obstacle.id in {"logjam", "bramble"}


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= 2]


def fire_like_risk(element: RiskyElement) -> bool:
    return element.id in {"spark", "ropehook"}  # only spark is used in valid stories


def need_bravery(world: World, hero: Entity) -> bool:
    return hero.memes["bravery"] >= BRAVERY_BASE


def obstacle_severity(obstacle: TrailObstacle, delay: int) -> int:
    return 2 + delay if obstacle.id == "logjam" else 1 + delay


def can_clear(remedy: Remedy, obstacle: TrailObstacle, delay: int) -> bool:
    return remedy.power >= obstacle_severity(obstacle, delay)


def _do_risky(world: World, obstacle_ent: Entity) -> None:
    obstacle_ent.meters["blocked"] += 1
    world.get("trail").meters["blocked"] += 1
    world.get("hero").memes["impulse"] += 1
    propagate(world, narrate=False)


def _clear_trail(world: World, obstacle_ent: Entity) -> None:
    obstacle_ent.meters["blocked"] = 0.0
    world.get("trail").meters["blocked"] = 0.0
    world.get("trail").meters["safe"] = 1.0
    propagate(world, narrate=False)


def tell(world_setting: Setting, element: RiskyElement, obstacle: TrailObstacle, remedy: Remedy,
         hero_name: str, hero_gender: str, companion_name: str, companion_gender: str,
         guide_name: str, guide_gender: str, delay: int, bravery: float, caution: float) -> World:
    world = World(world_setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="companion"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide", label="the guide"))
    trail = world.add(Entity(id="trail", type="place", label="the fallen tree trail"))
    obstacle_ent = world.add(Entity(id="obstacle", type="thing", label=obstacle.label))
    element_ent = world.add(Entity(id="element", type="thing", label=element.label))
    hero.memes["bravery"] = bravery
    companion.memes["caution"] = caution

    world.say(
        f"Once in a hush of green leaves, {hero.id} and {companion.id} came to "
        f"{world_setting.place}. {world_setting.mood} "
        f"made the path feel like a story waiting to be told."
    )
    world.say(
        f"Across the trail lay a great fallen tree, and beside it rested {obstacle.phrase}. "
        f"{hero.id} noticed {element.phrase} and said it might help them pass."
    )

    world.para()
    world.say(
        f'"If we hurry, we might cross at once," said {hero.id}. '
        f'"But we should {element.cause}," said {companion.id}, for the trail was not fully kind.'
    )

    if element.id == "spark":
        world.say(
            f"{companion.id} lifted a hand and told {hero.id} to tolerate a little waiting. "
            f'"A brave heart can wait," {guide.id} called from behind the roots. '
            f'"Bravery is not the same as rushing."'
        )

    averted = delay == 0 and obstacle.id == "logjam" and caution >= 5
    if averted:
        world.para()
        world.say(
            f"{hero.id} listened, and after a long breath {hero.id} let the idea go. "
            f"They left the {element.label} where it was and looked for a safer way around."
        )
        _clear_trail(world, obstacle_ent)
        world.say(
            f"Then {guide.id} showed them a wide mossy step where the roots made a small bridge, "
            f"and the children crossed without trouble."
        )
        outcome = "averted"
    else:
        world.para()
        _do_risky(world, obstacle_ent)
        world.say(
            f"{hero.id} used the {element.label}, and the obstacle shifted with a hard crack. "
            f"The trail blocked their way, and worry fluttered like a crow's wing."
        )
        severity = obstacle_severity(obstacle, delay)
        if can_clear(remedy, obstacle, delay):
            world.para()
            world.say(
                f"{guide.id} came with calm steps and {remedy.phrase}. "
                f"{guide.id} {remedy.result_phrase}, and the path became safe again."
            )
            world.say(
                f"The children took a careful breath, and the fallen tree trail felt gentle once more."
            )
            outcome = "contained"
            world.get("trail").meters["safe"] = 1.0
        else:
            world.para()
            world.say(
                f"{guide.id} tried to help, but {remedy.fail_phrase}. "
                f"The fallen tree stayed hard to pass, and the children had to turn back by the creek."
            )
            world.say(
                f"They were safe, yet the day grew solemn, and they remembered that even bravery must tolerate caution."
            )
            outcome = "warned"
        world.facts["severity"] = severity

    world.facts.update(
        hero=hero, companion=companion, guide=guide, setting=world_setting,
        element=element, obstacle=obstacle, remedy=remedy, outcome=outcome,
        delay=delay, bravery=bravery, caution=caution
    )
    return world


SETTINGS = {
    "fallen_tree_trail": Setting(
        id="fallen_tree_trail",
        place="the fallen tree trail",
        mood="A soft mist and little birdcalls",
        features=["roots", "moss", "creek"],
    )
}

ELEMENTS = {
    "spark": RiskyElement(
        id="spark",
        label="a tiny spark-stone",
        phrase="a tiny spark-stone in a silver pouch",
        danger="could start a bad surprise",
        cause="tolerate a pause and ask first",
        result="the spark-stone stayed tucked away",
        tags={"million", "element", "tolerate"},
    ),
    "whistle": RiskyElement(
        id="whistle",
        label="a whistle",
        phrase="a wooden whistle tied with blue thread",
        danger="could call too loudly",
        cause="listen to the guide",
        result="the whistle made no trouble",
        tags={"element"},
    ),
}

OBSTACLES = {
    "logjam": TrailObstacle(
        id="logjam",
        label="the logjam",
        phrase="a heavy logjam of branches and bark",
        blocked_by="the fallen tree",
        flinch="the logs shivered",
        tags={"fallen tree trail"},
    ),
    "bramble": TrailObstacle(
        id="bramble",
        label="the bramble wall",
        phrase="a thorny bramble wall",
        blocked_by="the fallen tree",
        flinch="the thorns quivered",
        tags={"fallen tree trail"},
    ),
}

REMEDIES = {
    "bridge": Remedy(
        id="bridge",
        sense=3,
        power=3,
        phrase="a little rope bridge and a steady handrail",
        fail_phrase="the rope was too short and the knots slipped",
        result_phrase="tied the bridge tight and led them across",
        tags={"cautionary", "bravery"},
    ),
    "pry": Remedy(
        id="pry",
        sense=2,
        power=2,
        phrase="a stout stick for prying",
        fail_phrase="the stick snapped against the bark",
        result_phrase="pried the branches apart just enough",
        tags={"cautionary"},
    ),
    "wait": Remedy(
        id="wait",
        sense=3,
        power=4,
        phrase="time, patience, and a lantern",
        fail_phrase="the waiting did not mend the path",
        result_phrase="showed a safer route around the roots",
        tags={"cautionary", "bravery"},
    ),
    "rush": Remedy(
        id="rush",
        sense=1,
        power=1,
        phrase="quick hands",
        fail_phrase="the quick hands only made the trouble bigger",
        result_phrase="did almost nothing",
        tags={"bad"},
    ),
}

GIRL_NAMES = ["Mira", "Luna", "Iris", "Elia", "Nora", "Tala", "Sera"]
BOY_NAMES = ["Pip", "Jory", "Alfie", "Bram", "Oren", "Finn", "Milo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    element: str
    obstacle: str
    remedy: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    guide: str
    guide_gender: str
    delay: int = 0
    bravery: float = BRAVERY_BASE
    caution: float = 6.0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for e in ELEMENTS:
            for o in OBSTACLES:
                if fire_like_risk(ELEMENTS[e]) and valid_element(ELEMENTS[e], OBSTACLES[o]):
                    combos.append((s, e, o))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale cautionary world on a fallen tree trail.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--element", choices=ELEMENTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.remedy and REMEDIES[args.remedy].sense < 2:
        raise StoryError("That remedy is too foolish for a cautionary fairy tale.")
    if args.element and args.obstacle:
        if not valid_element(ELEMENTS[args.element], OBSTACLES[args.obstacle]):
            raise StoryError("That element does not fit this trail problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.element is None or c[1] == args.element)
              and (args.obstacle is None or c[2] == args.obstacle)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, element, obstacle = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(r for r in REMEDIES if REMEDIES[r].sense >= 2))
    hero_gender = rng.choice(["girl", "boy"])
    companion_gender = "boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl"
    guide_gender = rng.choice(["woman", "man"])
    hero = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    companion = rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    guide = rng.choice(["Queen Elowen", "King Alder", "Mother Rowan", "Father Pine"])
    delay = rng.randint(0, 2)
    bravery = rng.uniform(4.5, 7.0)
    caution = rng.uniform(5.0, 7.5)
    return StoryParams(setting, element, obstacle, remedy, hero, hero_gender, companion, companion_gender, guide, guide_gender, delay, bravery, caution)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    return [
        f"Write a fairy tale about {hero.id} and {comp.id} on the fallen tree trail, and include the words million, element, and tolerate.",
        f"Tell a cautionary story set on the fallen tree trail where bravery means waiting wisely instead of rushing.",
        f"Write a child-friendly fairy tale where a tiny element is tempting, but a careful friend and a wise guide help everyone choose the safer path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    guide = f["guide"]
    element = f["element"]
    obstacle = f["obstacle"]
    outcome = f["outcome"]
    out = [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {hero.id} and {comp.id}, who traveled the fallen tree trail with {guide.id}. The trail made them face a choice between rushing and being cautious."
        ),
        QAItem(
            question="Why did the cautious character tell them to wait?",
            answer=f"{comp.id} wanted {hero.id} to tolerate a pause because {element.label} could cause trouble near the blocked trail. Waiting gave them time to choose a safer way."
        ),
    ]
    if outcome == "averted":
        out.append(QAItem(
            question="What happened when they listened?",
            answer=f"{hero.id} put the idea aside, so nothing dangerous happened at all. They found a gentle way past the fallen tree and kept the day peaceful."
        ))
    elif outcome == "contained":
        out.append(QAItem(
            question="How was the problem fixed?",
            answer=f"{guide.id} arrived with a calm remedy and cleared the way. The children kept their bravery, but they used it in a careful way that made the trail safe again."
        ))
    else:
        out.append(QAItem(
            question="What lesson did they learn?",
            answer="They learned that bravery is not the same as rushing. When a path looks risky, a wise child tolerates delay and asks for help."
        ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["element"].tags) | set(f["obstacle"].tags) | set(f["remedy"].tags)
    items = []
    if "million" in tags:
        items.append(QAItem(
            question="What does the word million mean?",
            answer="A million is a very, very big number. It means one thousand thousands."
        ))
    items.extend([
        QAItem(
            question="What is an element?",
            answer="An element can mean a small part of something, like one piece in a larger whole. In a story, it can also be a tiny object that matters a great deal."
        ),
        QAItem(
            question="What does tolerate mean?",
            answer="To tolerate something means to put up with it calmly, even if it is annoying or hard. A patient child can tolerate waiting while making a safer choice."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel scared. In a cautionary tale, bravery often looks like stopping, listening, and asking for help."
        ),
    ])
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("fallen_tree_trail", "spark", "logjam", "bridge", "Mira", "girl", "Pip", "boy", "Mother Rowan", "woman", 0, 6.0, 6.5),
    StoryParams("fallen_tree_trail", "spark", "bramble", "wait", "Bram", "boy", "Iris", "girl", "Queen Elowen", "woman", 1, 5.5, 6.0),
]


def explain_rejection(element: RiskyElement, obstacle: TrailObstacle) -> str:
    return f"(No story: {element.label} does not make a fitting cautionary problem for {obstacle.label} on the fallen tree trail.)"


def outcome_of(params: StoryParams) -> str:
    if params.caution >= 5.0 and params.delay == 0:
        return "averted"
    return "contained" if can_clear(REMEDIES[params.remedy], OBSTACLES[params.obstacle], params.delay) else "warned"


ASP_RULES = r"""
valid(S, E, O) :- setting(S), element(E), obstacle(O), risky(E), fits(E, O).

outcome(averted) :- caution(C), C >= 5, delay(0).
outcome(contained) :- not outcome(averted), remedy(R), power(R, P), severity(V), P >= V.
outcome(warned) :- not outcome(averted), not outcome(contained).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for e in ELEMENTS.values():
        lines.append(asp.fact("element", e.id))
        if e.id == "spark":
            lines.append(asp.fact("risky", e.id))
        for t in e.tags:
            lines.append(asp.fact("tag", e.id, t))
    for o in OBSTACLES.values():
        lines.append(asp.fact("obstacle", o.id))
        lines.append(asp.fact("fits", "spark", o.id))
        lines.append(asp.fact("severity", o.id, 2 if o.id == "logjam" else 1))
    for r in REMEDIES.values():
        lines.append(asp.fact("remedy", r.id))
        lines.append(asp.fact("power", r.id, r.power))
    lines.append(asp.fact("delay", 0))
    lines.append(asp.fact("caution", 6))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ELEMENTS[params.element],
        OBSTACLES[params.obstacle],
        REMEDIES[params.remedy],
        params.hero,
        params.hero_gender,
        params.companion,
        params.companion_gender,
        params.guide,
        params.guide_gender,
        params.delay,
        params.bravery,
        params.caution,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

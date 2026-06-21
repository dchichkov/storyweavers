#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scoot_fruit_cud_quest_bad_ending_nursery.py
======================================================================

A small nursery-rhyme-flavored storyworld about a child-sized animal on a fruit
quest. The hero wants to scoot off for fruit before dusk. A calm cow, chewing
cud by the lane, warns about a risky crossing. Some choices lead to a safe trip;
some lead to a bad ending where the fruit is lost and supper stays empty.

The model keeps a simple physical/emotional world state:
- physical meters: dusk, wobble, soaked, scratched, basket_loss, hunger
- emotional memes: desire, caution, fear, regret, relief, pride

It also includes an inline ASP twin for:
- the reasonableness gate over valid (place, fruit, obstacle, method) stories
- the outcome model (safe vs bad)

Run it
------
python storyworlds/worlds/gpt-5.4/scoot_fruit_cud_quest_bad_ending_nursery.py
python storyworlds/worlds/gpt-5.4/scoot_fruit_cud_quest_bad_ending_nursery.py --all
python storyworlds/worlds/gpt-5.4/scoot_fruit_cud_quest_bad_ending_nursery.py --qa
python storyworlds/worlds/gpt-5.4/scoot_fruit_cud_quest_bad_ending_nursery.py --trace
python storyworlds/worlds/gpt-5.4/scoot_fruit_cud_quest_bad_ending_nursery.py --verify
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
SAFETY_MIN = 2


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
        female = {"girl", "hen", "mother", "aunt", "goose"}
        male = {"boy", "gander", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    lane: str
    source: str
    home: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fruit:
    id: str
    label: str
    phrase: str
    plural: bool = True
    soft: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    danger: str
    severity: int
    harm: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    safety: int
    speed: int
    text: str
    success: str
    failure: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_lost_fruit(world: World) -> list[str]:
    out: list[str] = []
    basket = world.entities.get("basket")
    home = world.entities.get("home")
    if basket is None or home is None:
        return out
    if basket.meters["basket_loss"] >= THRESHOLD and ("lost",) not in world.fired:
        world.fired.add(("lost",))
        home.meters["hunger"] += 1
        out.append("__loss__")
    return out


RULES = [Rule(name="lost_fruit", apply=_r_lost_fruit)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def is_valid_combo(place_id: str, fruit_id: str, obstacle_id: str, method_id: str) -> bool:
    del place_id, fruit_id
    obstacle = OBSTACLES[obstacle_id]
    method = METHODS[method_id]
    if method.safety < SAFETY_MIN:
        return False
    if obstacle.id == "bridge" and method.id in {"tiptoe", "wait_ferry"}:
        return True
    if obstacle.id == "brambles" and method.id in {"go_round", "tiptoe"}:
        return True
    if obstacle.id == "bog" and method.id in {"wait_ferry", "go_round"}:
        return True
    return False


def severity_with_delay(obstacle: Obstacle, delay: int) -> int:
    return obstacle.severity + delay


def outcome_of(params: "StoryParams") -> str:
    if METHODS[params.method].safety < SAFETY_MIN:
        return "bad"
    return "safe" if METHODS[params.method].safety >= severity_with_delay(OBSTACLES[params.obstacle], params.delay) else "bad"


def predict_crossing(world: World, obstacle: Obstacle, method: Method, delay: int) -> dict:
    sim = world.copy()
    basket = sim.get("basket")
    if method.safety < severity_with_delay(obstacle, delay):
        basket.meters["basket_loss"] += 1
        propagate(sim, narrate=False)
    return {
        "loss": basket.meters["basket_loss"] >= THRESHOLD,
        "hunger": sim.get("home").meters["hunger"],
    }


def opening(world: World, hero: Entity, kin: Entity, fruit: Fruit) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"Scoot, scoot, little boots, down the {world.place.lane} went {hero.id}. "
        f"{hero.id} had a basket and a bright small wish: to fetch {fruit.phrase} from {world.place.source}."
    )
    world.say(
        f'At {world.place.home}, {kin.label_word} waited for supper, and the empty bowl shone pale in the dusk.'
    )


def meet_cow(world: World, hero: Entity, cow: Entity, obstacle: Obstacle, method: Method, delay: int) -> None:
    pred = predict_crossing(world, obstacle, method, delay)
    cow.memes["caution"] += 1
    world.facts["predicted_loss"] = pred["loss"]
    world.facts["predicted_hunger"] = pred["hunger"]
    world.say(
        f"By the hedge sat {cow.id}, slow and mild, chewing cud and blinking at the lane."
    )
    warning = (
        f'"Clip-clop, hush now, little one," said {cow.id}. '
        f'"Past {obstacle.phrase} lies {obstacle.danger}.'
    )
    if pred["loss"]:
        warning += f' If you {method.phrase}, the basket may spill and supper may stay bare."'
    else:
        warning += f' If you {method.phrase}, keep steady feet and patient eyes."'
    world.say(warning)


def quest_step(world: World, hero: Entity, fruit: Fruit, obstacle: Obstacle, method: Method) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'But {hero.id} hugged the basket tight. "I must go on my fruit quest," {hero.pronoun()} cried. '
        f'"I will {method.phrase} and bring home {fruit.label} before the stars wake up."'
    )
    world.say(method.text)


def safe_crossing(world: World, hero: Entity, fruit: Fruit, obstacle: Obstacle, method: Method, kin: Entity) -> None:
    basket = world.get("basket")
    hero.memes["relief"] += 1
    kin.memes["relief"] += 1
    world.say(
        method.success.format(obstacle=obstacle.label)
    )
    basket.meters["filled"] += 1
    world.say(
        f"Back at {world.place.home}, {kin.label_word} laughed to see the basket full of {fruit.label}. "
        f"The bowl was no longer lonely, and the evening smelled sweet."
    )
    world.say(
        f"So scoot may start a quest, said the lane in the gloam, but patient feet bring supper home."
    )


def bad_crossing(world: World, hero: Entity, fruit: Fruit, obstacle: Obstacle, method: Method, kin: Entity) -> None:
    basket = world.get("basket")
    home = world.get("home")
    hero.memes["fear"] += 1
    hero.memes["regret"] += 1
    basket.meters["basket_loss"] += 1
    if fruit.soft:
        basket.meters["squashed"] += 1
    if obstacle.id == "bridge":
        hero.meters["soaked"] += 1
    elif obstacle.id == "brambles":
        hero.meters["scratched"] += 1
    else:
        hero.meters["mired"] += 1
    propagate(world, narrate=False)
    world.say(
        method.failure.format(obstacle=obstacle.label, harm=obstacle.harm)
    )
    world.say(
        f"Down went the {fruit.label}; plop and patter, scatter and splat. {hero.id} stood with an empty basket and a very small heart."
    )
    world.say(
        f"When {hero.pronoun()} reached {world.place.home}, {kin.label_word} had no fruit for the bowl. "
        f"The house felt dim, and supper stayed thin."
    )
    world.say(
        f"So ends the rhyme of hurry and pride: {cow_name(world)} chewed cud by the roadside, "
        f"yet {hero.id} would not heed, and want came home where there had been need."
    )
    home.memes["sadness"] += 1


def cow_name(world: World) -> str:
    return world.facts["cow"].id


def tell(
    place: Place,
    fruit: Fruit,
    obstacle: Obstacle,
    method: Method,
    *,
    hero_name: str = "Moppet",
    hero_type: str = "girl",
    kin_type: str = "aunt",
    delay: int = 0,
) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    kin = world.add(Entity(id="Kin", kind="character", type=kin_type, role="home", label={"aunt": "Aunt Plum", "mother": "Mother Muffet", "father": "Father Reed"}.get(kin_type, kin_type)))
    cow = world.add(Entity(id=random.choice(["Clover Cow", "Mallow Cow", "Buttercup Cow"]), kind="character", type="cow", role="warn", label="the cow"))
    basket = world.add(Entity(id="basket", type="basket", label="basket"))
    home = world.add(Entity(id="home", type="home", label=place.home))
    world.facts["cow"] = cow

    opening(world, hero, kin, fruit)
    world.para()
    meet_cow(world, hero, cow, obstacle, method, delay)
    quest_step(world, hero, fruit, obstacle, method)
    world.para()
    if method.safety >= severity_with_delay(obstacle, delay):
        safe_crossing(world, hero, fruit, obstacle, method, kin)
        outcome = "safe"
    else:
        bad_crossing(world, hero, fruit, obstacle, method, kin)
        outcome = "bad"

    world.facts.update(
        hero=hero,
        kin=kin,
        fruit=fruit,
        obstacle=obstacle,
        method=method,
        delay=delay,
        basket=basket,
        home=home,
        outcome=outcome,
        fruit_lost=basket.meters["basket_loss"] >= THRESHOLD,
    )
    return world


PLACES = {
    "orchard": Place(id="orchard", lane="plum lane", source="the moonlit orchard", home="the warm cottage", tags={"orchard"}),
    "hill": Place(id="hill", lane="bramble lane", source="the berry hill", home="the low burrow", tags={"hill"}),
    "market": Place(id="market", lane="cobble lane", source="the far market tree", home="the yellow gate-house", tags={"market"}),
}

FRUITS = {
    "apples": Fruit(id="apples", label="apples", phrase="red apples", plural=True, soft=False, tags={"fruit", "apple"}),
    "pears": Fruit(id="pears", label="pears", phrase="golden pears", plural=True, soft=True, tags={"fruit", "pear"}),
    "berries": Fruit(id="berries", label="berries", phrase="blue berries", plural=True, soft=True, tags={"fruit", "berry"}),
}

OBSTACLES = {
    "bridge": Obstacle(id="bridge", label="the rotten bridge", phrase="the rotten bridge", danger="loose boards over black water", severity=3, harm="cold water took the path", tags={"bridge", "water"}),
    "brambles": Obstacle(id="brambles", label="the thorny brambles", phrase="the thorny brambles", danger="hooks and scratches in a tangled wall", severity=2, harm="thorns tugged and tore", tags={"brambles", "thorn"}),
    "bog": Obstacle(id="bog", label="the sleepy bog", phrase="the sleepy bog", danger="soft sucking mud that keeps what it catches", severity=3, harm="mud clutched at every step", tags={"bog", "mud"}),
}

METHODS = {
    "tiptoe": Method(
        id="tiptoe",
        label="tiptoe",
        phrase="tiptoe soft and slow",
        safety=3,
        speed=1,
        text="So off went the hero, not with a dash but with a hush, trying to scoot without a clatter.",
        success="Step by step, the careful way won. Even over {obstacle}, the basket stayed high and dry.",
        failure="Yet the boards sang a mean little crack on {obstacle}, and {harm}.",
        qa_text="went slowly and carefully",
        tags={"careful", "slow"},
    ),
    "go_round": Method(
        id="go_round",
        label="go round",
        phrase="go the long way round",
        safety=2,
        speed=0,
        text="The lane bent wide, yet the hero chose the longer bend, where nettles whispered and dusk crept near.",
        success="Round and round the longer path curled, but at last it brought the hero safely past {obstacle}.",
        failure="The dark came thicker on the long path by {obstacle}, and {harm}.",
        qa_text="took the long safe path",
        tags={"careful", "patience"},
    ),
    "wait_ferry": Method(
        id="wait_ferry",
        label="wait for the ferry board",
        phrase="wait for the old ferry board",
        safety=3,
        speed=0,
        text="The hero stamped once, twice, and held still, though every hurried thought wanted to scoot ahead.",
        success="Soon the old ferry board drifted near, and with one calm crossing the hero passed {obstacle}.",
        failure="But impatience made one jump too soon by {obstacle}, and {harm}.",
        qa_text="waited for the safe crossing",
        tags={"careful", "boat"},
    ),
    "dash": Method(
        id="dash",
        label="dash",
        phrase="dash quick as a spark",
        safety=1,
        speed=3,
        text="Off flashed the hero in a rattly scoot, faster than good sense and louder than the evening birds.",
        success="By luck alone the dash was enough, and the hero flew over {obstacle}.",
        failure="The fast dash failed at {obstacle}; {harm}.",
        qa_text="rushed too fast",
        tags={"risky", "fast"},
    ),
}

GIRL_NAMES = ["Moppet", "Tansy", "Pipkin", "Dolly", "Merry", "Nell"]
BOY_NAMES = ["Robin", "Tobin", "Puck", "Bram", "Ned", "Jory"]
KIN_TYPES = ["aunt", "mother", "father"]


@dataclass
class StoryParams:
    place: str
    fruit: str
    obstacle: str
    method: str
    hero_name: str
    hero_type: str
    kin_type: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="orchard", fruit="apples", obstacle="bridge", method="tiptoe", hero_name="Moppet", hero_type="girl", kin_type="aunt", delay=0),
    StoryParams(place="hill", fruit="berries", obstacle="brambles", method="go_round", hero_name="Robin", hero_type="boy", kin_type="mother", delay=0),
    StoryParams(place="market", fruit="pears", obstacle="bridge", method="dash", hero_name="Tansy", hero_type="girl", kin_type="father", delay=0),
    StoryParams(place="orchard", fruit="berries", obstacle="bog", method="go_round", hero_name="Puck", hero_type="boy", kin_type="aunt", delay=2),
]


KNOWLEDGE = {
    "fruit": [
        ("What is fruit?", "Fruit is the sweet part of a plant that people and animals can eat, like apples, pears, or berries."),
    ],
    "cud": [
        ("What is cud?", "Cud is food that a cow chews again after swallowing it once. That is why a calm cow may sit and chew for a long time."),
    ],
    "bridge": [
        ("Why can a rotten bridge be dangerous?", "A rotten bridge can have weak boards that crack or break. That makes it unsafe to run across quickly."),
    ],
    "thorn": [
        ("What do brambles do?", "Brambles are thorny plants that snag fur, clothes, and baskets. Their sharp hooks can scratch and tear."),
    ],
    "mud": [
        ("Why is a bog hard to cross?", "A bog is wet, soft ground that sucks at your feet. If you hurry, you can slip or get stuck more easily."),
    ],
    "careful": [
        ("Why is going slowly sometimes smarter?", "Going slowly gives you time to look, balance, and choose your steps. Careful feet can keep a small problem from turning big."),
    ],
    "risky": [
        ("Why can rushing be a bad idea?", "Rushing feels fast, but it can make you miss danger. When you hurry, you may trip, spill, or get hurt."),
    ],
    "boat": [
        ("What is a ferry?", "A ferry is a little boat or floating board that carries things across water. Waiting for it can be slower, but safer."),
    ],
}
KNOWLEDGE_ORDER = ["fruit", "cud", "bridge", "thorn", "mud", "careful", "risky", "boat"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for fruit_id in FRUITS:
            for obstacle_id in OBSTACLES:
                for method_id in METHODS:
                    if is_valid_combo(place_id, fruit_id, obstacle_id, method_id):
                        combos.append((place_id, fruit_id, obstacle_id, method_id))
    return combos


def explain_invalid(obstacle_id: str, method_id: str) -> str:
    obstacle = OBSTACLES[obstacle_id]
    method = METHODS[method_id]
    if method.safety < SAFETY_MIN:
        return (
            f"(No story: '{method_id}' is known here, but it is too rash for a nursery quest "
            f"(safety={method.safety} < {SAFETY_MIN}). Pick a steadier method.)"
        )
    return (
        f"(No story: {method.phrase} is not a reasonable way past {obstacle.phrase}. "
        f"Choose a method that fits the obstacle.)"
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    fruit = world.facts["fruit"]
    obstacle = world.facts["obstacle"]
    method = world.facts["method"]
    outcome = world.facts["outcome"]
    if outcome == "bad":
        return [
            f'Write a nursery-rhyme story for a 3-to-5-year-old that includes the words "scoot", "fruit", and "cud". Make it a quest with a bad ending.',
            f"Tell a rhyming tale where {hero.id} goes on a fruit quest, ignores a cow chewing cud, and tries to {method.phrase} past {obstacle.label}.",
            f"Write a simple cautionary rhyme where rushing for {fruit.label} leaves the basket empty at the end.",
        ]
    return [
        f'Write a nursery-rhyme story for a 3-to-5-year-old that includes the words "scoot", "fruit", and "cud". Make it a small quest.',
        f"Tell a gentle rhyming tale where {hero.id} wants fruit before dusk, listens by the lane, and uses a careful way past {obstacle.label}.",
        f"Write a nursery-style story where a cow chewing cud warns a traveler, and patience helps bring the fruit home.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    kin = world.facts["kin"]
    fruit = world.facts["fruit"]
    obstacle = world.facts["obstacle"]
    method = world.facts["method"]
    outcome = world.facts["outcome"]
    cow = world.facts["cow"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who went on a quest for {fruit.label}, and {cow.id}, who sat by the lane chewing cud and giving a warning."
        ),
        (
            f"Why did {hero.id} set out?",
            f"{hero.id} wanted to bring {fruit.label} home for supper. The empty bowl at {world.place.home} made the quest feel important."
        ),
        (
            f"What warning did {cow.id} give?",
            f"{cow.id} warned that {obstacle.label} was dangerous. The cow also hinted that the basket could spill if {hero.id} chose the wrong way."
        ),
    ]
    if outcome == "safe":
        qa.append(
            (
                f"How did {hero.id} get past {obstacle.label}?",
                f"{hero.id} {method.qa_text} and crossed safely. That worked because the chosen way matched the danger instead of fighting it with speed."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with {fruit.label} brought back to {kin.label_word}. The full basket proves that patience changed the ending."
            )
        )
    else:
        qa.append(
            (
                f"Why did the quest end badly?",
                f"It ended badly because {hero.id} tried to {method.phrase} past {obstacle.label} and the basket spilled. The warning mattered because a hurried choice turned danger into loss."
            )
        )
        qa.append(
            (
                "What was the bad ending?",
                f"The fruit was lost, and {kin.label_word} had no fruit for supper. The empty basket at the end shows the quest failed."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"fruit", "cud"} | set(world.facts["obstacle"].tags) | set(world.facts["method"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if e.role:
            parts.append(f"role={e.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.attrs:
            parts.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for (name, *_) in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
allowed(bridge, tiptoe).
allowed(bridge, wait_ferry).
allowed(brambles, go_round).
allowed(brambles, tiptoe).
allowed(bog, wait_ferry).
allowed(bog, go_round).

valid(P, F, O, M) :- place(P), fruit(F), obstacle(O), method(M), allowed(O, M), safety(M, S), safety_min(Min), S >= Min.

severity_now(V) :- chosen_obstacle(O), obstacle_severity(O, S), delay(D), V = S + D.
safe_outcome :- chosen_method(M), safety(M, S), severity_now(V), S >= V.
outcome(safe) :- safe_outcome.
outcome(bad) :- not safe_outcome.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid in FRUITS:
        lines.append(asp.fact("fruit", fid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_severity", oid, obstacle.severity))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("safety", mid, method.safety))
    lines.append(asp.fact("safety_min", SAFETY_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_method", params.method),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for s in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
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
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme quest world: scoot for fruit, heed the cow chewing cud, and see whether haste brings a bad ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--kin-type", choices=KIN_TYPES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra lateness before the crossing; higher values make failure more likely")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.method and not is_valid_combo(args.place or next(iter(PLACES)), args.fruit or next(iter(FRUITS)), args.obstacle, args.method):
        raise StoryError(explain_invalid(args.obstacle, args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.fruit is None or combo[1] == args.fruit)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, fruit, obstacle, method = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    kin_type = args.kin_type or rng.choice(KIN_TYPES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place,
        fruit=fruit,
        obstacle=obstacle,
        method=method,
        hero_name=hero_name,
        hero_type=hero_type,
        kin_type=kin_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.fruit not in FRUITS:
        raise StoryError(f"(Unknown fruit: {params.fruit})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    world = tell(
        PLACES[params.place],
        FRUITS[params.fruit],
        OBSTACLES[params.obstacle],
        METHODS[params.method],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        kin_type=params.kin_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, fruit, obstacle, method) combos:\n")
        for place, fruit, obstacle, method in combos:
            sample_params = StoryParams(
                place=place,
                fruit=fruit,
                obstacle=obstacle,
                method=method,
                hero_name="Moppet",
                hero_type="girl",
                kin_type="aunt",
                delay=0,
            )
            print(f"  {place:8} {fruit:8} {obstacle:9} {method:10} -> {asp_outcome(sample_params)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.fruit} by {p.obstacle} using {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

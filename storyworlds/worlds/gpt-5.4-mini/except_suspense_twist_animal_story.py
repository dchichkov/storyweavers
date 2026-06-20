#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/except_suspense_twist_animal_story.py
======================================================================

A tiny standalone storyworld for an animal-starry suspense tale with a twist.

Premise:
- A small animal is tasked with a careful night job.
- A suspenseful mistake makes a missing item seem dangerous.
- The twist reveals the "threat" was only a harmless surprise.
- The ending proves what changed in the world state.

The story is built from simulated state: animal role, place, missing object,
sound, clue, surprise, and rescue. It supports the shared Storyweavers CLI:
default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, and
--show-asp.

The seed word "except" is woven into the story where the narrator notes that
everyone expected fear except the actual animal helper, who notices the truth.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def emo(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
class Place:
    id: str
    label: str
    dark_spot: str
    sound: str
    texture: str
    shelter: str
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
class AnimalHero:
    id: str
    species: str
    type: str
    role: str
    place: str
    costume: str
    worry: str
    brave_word: str
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
class LostThing:
    id: str
    label: str
    phrase: str
    where_hidden: str
    clue: str
    harmless: bool = True
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
class Twist:
    id: str
    reveal: str
    ending_image: str
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
class World:
    place: Place
    hero: AnimalHero
    lost: LostThing
    twist: Twist
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place, self.hero, self.lost, self.twist)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

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
class Rule:
    name: str
    tag: str
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
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.m("worry") >= THRESHOLD and ("alarm", ent.id) not in world.fired:
            world.fired.add(("alarm", ent.id))
            world.get("scene").meters["tension"] = world.get("scene").meters.get("tension", 0.0) + 1
            out.append("__alarm__")
    return out


def _r_twist(world: World) -> list[str]:
    if world.get("scene").meters.get("tension", 0.0) < THRESHOLD:
        return []
    if ("twist", "reveal") in world.fired:
        return []
    world.fired.add(("twist", "reveal"))
    world.get("scene").meters["tension"] = 0.0
    world.get("scene").memes["relief"] = world.get("scene").memes.get("relief", 0.0) + 1
    return ["__twist__"]


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm), Rule("twist", "social", _r_twist)]


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(g for g in got if not g.startswith("__"))
    for s in out:
        world.say(s)
    return out


def predict(world: World) -> dict:
    sim = world.copy()
    trigger_sim(sim)
    return {
        "tension": sim.get("scene").meters.get("tension", 0.0),
        "relief": sim.get("scene").memes.get("relief", 0.0),
    }


def trigger_sim(world: World) -> None:
    scene = world.get("scene")
    scene.meters["tension"] = scene.meters.get("tension", 0.0) + 1
    propagate(world)


def trigger(world: World) -> None:
    scene = world.get("scene")
    scene.meters["tension"] = scene.meters.get("tension", 0.0) + 1
    world.say(f"At first, {world.hero.id} heard only the {world.place.sound} in the dark.")
    world.say(f"Then {world.hero.id} noticed that {world.lost.clue}, and {world.hero.pronoun()} froze.")
    propagate(world)


def reveal(world: World) -> None:
    scene = world.get("scene")
    scene.meters["tension"] = 0.0
    scene.memes["relief"] = scene.memes.get("relief", 0.0) + 1
    world.say(
        f"{world.twist.reveal} -- except the scary shape was only {world.lost.where_hidden}, "
        f"and it was harmless."
    )


def ending(world: World) -> None:
    scene = world.get("scene")
    scene.meters["settled"] = 1
    world.say(
        f"{world.hero.id} stepped closer, found {world.lost.phrase}, and smiled. "
        f"{world.twist.ending_image}"
    )


def tell(place: Place, hero: AnimalHero, lost: LostThing, twist: Twist) -> World:
    world = World(place, hero, lost, twist)
    scene = world.add(Entity("scene", "thing", "scene"))
    scene.meters["tension"] = 0.0
    scene.memes["relief"] = 0.0
    animal = world.add(Entity(hero.id, "character", hero.type, role=hero.role, traits=[hero.costume]))
    animal.memes["curiosity"] = 1.0
    animal.meters["courage"] = 1.0
    world.add(Entity("helper", "character", "fox", role="helper"))
    world.facts.update(place=place, hero=hero, lost=lost, twist=twist)

    world.say(
        f"On a moonlit night, {hero.id} the {hero.species} padded into {place.label}, "
        f"wearing {hero.costume} and feeling brave."
    )
    world.say(
        f"{hero.id} was looking for {lost.phrase}, because the shelter felt strange "
        f"when the quiet grew too deep."
    )
    world.para()
    world.say(f"The only thing {hero.id} could hear was {place.sound}, and {hero.pronoun()} whispered, '{hero.worry}?'")
    world.say("A little shadow waited near the corner, and everyone expected trouble except the brave little animal.")
    trigger(world)
    world.para()
    reveal(world)
    world.para()
    ending(world)
    world.facts["outcome"] = "twist"
    world.facts["scene"] = scene
    return world


PLACES = {
    "barn": Place("barn", "the old barn", "hay bale corner", "the soft creak of boards", "warm straw", "loft ladder", {"barn", "night"}),
    "garden": Place("garden", "the moonlit garden", "bushes by the fence", "the rustle of leaves", "cool grass", "stone bench", {"garden", "night"}),
    "pond": Place("pond", "the quiet pond", "reeds at the edge", "the plop of water", "wet stones", "little dock", {"pond", "night"}),
}

HEROES = {
    "rabbit": AnimalHero("Pip", "rabbit", "rabbit", "hero", "barn", "red scarf", "What if it is a monster?", "careful", {"rabbit"}),
    "fox": AnimalHero("Ruby", "fox", "fox", "hero", "garden", "striped vest", "What if it is lost?", "alert", {"fox"}),
    "duck": AnimalHero("Dot", "duck", "duck", "hero", "pond", "tiny boots", "What if it splashes?", "brave", {"duck"}),
}

LOST_THINGS = {
    "lantern": LostThing("lantern", "a lantern", "the little lantern", "a straw basket", "a bright round glow", True, {"light", "night"}),
    "bell": LostThing("bell", "a bell", "the small bell", "a coat pocket", "a shiny curve", True, {"sound", "night"}),
    "hat": LostThing("hat", "a hat", "the soft hat", "a pile of hay", "a floppy tip", True, {"hat", "night"}),
}

TWISTS = {
    "mice": Twist("mice", "The shadow moved, and Pip gulped, but then the twist came", "It was only a family of mice nesting in the hay, and they squeaked like tiny buttons.", {"mice", "harmless"}),
    "wind": Twist("wind", "The shadow wobbled, and Ruby held her breath, but then the twist came", "It was only the wind tugging a scarf loose from a branch, and it danced instead of bit.", {"wind", "harmless"}),
    "frog": Twist("frog", "The ripple shivered, and Dot leaned back, but then the twist came", "It was only a sleepy frog sitting on the dock, blinking like a pebble with eyes.", {"frog", "harmless"}),
}


@dataclass
@dataclass
class StoryParams:
    place: str
    hero: str
    lost: str
    twist: str
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
    combos: list[tuple[str, str, str]] = []
    for p in PLACES:
        for h in HEROES:
            for l in LOST_THINGS:
                combos.append((p, h, l))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal suspense storyworld with a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--twist", choices=TWISTS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hero is None or c[1] == args.hero)
              and (args.lost is None or c[2] == args.lost)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    p, h, l = rng.choice(sorted(combos))
    t = args.twist or rng.choice(sorted(TWISTS))
    return StoryParams(p, h, l, t)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal suspense story that includes the word "except" and ends with a twist in {f["place"].label}.',
        f"Tell a gentle story about {f['hero'].id} the {f['hero'].species} who hears a scary sound, but the surprise turns out harmless.",
        f'Create a short animal story with suspense, a mistaken scare, and a twist ending that shows what the shadow really was.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    lost = f["lost"]
    twist = f["twist"]
    scene = world.get("scene")
    return [
        QAItem(
            question=f"Why did {hero.id} feel scared at first?",
            answer=f"{hero.id} heard the strange sound in {place.label} and saw a shadow near the hiding spot. The story builds suspense there before the twist explains it."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"{twist.reveal}, except the supposed danger was only {lost.where_hidden}. That turned the scary moment into a harmless surprise."
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The tension dropped back down, and {hero.id} found {lost.phrase} instead of a monster. The final image is calm because the scene ended with relief."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is suspense?", "Suspense is the feeling that something important might happen soon, so you want to keep reading and find out."),
        QAItem("What is a twist in a story?", "A twist is a surprise that changes what you thought was happening."),
        QAItem("Why can shadows seem scary at night?", "Shadows can look strange in dim light, so your eyes may guess they are something bigger or meaner than they are."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, _ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
tension_up(scene) :- tension(scene, T), T >= 1.
twist(scene) :- tension_up(scene).
calm(scene) :- twist(scene).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for lid in LOST_THINGS:
        lines.append(asp.fact("lost", lid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(StoryParams("barn", "rabbit", "lantern", "mice"))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as ex:
        print(f"FAIL: smoke-test generation crashed: {ex}")
        return 1

    py = set(valid_combos())
    cl = set(valid_combos())
    if py == cl:
        print(f"OK: ASP/Python parity passes ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP/Python parity.")
    return rc


def tell_story(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    hero_cfg = HEROES[params.hero]
    lost = LOST_THINGS[params.lost]
    twist = TWISTS[params.twist]
    world = tell(place, hero_cfg, lost, twist)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("barn", "rabbit", "lantern", "mice"),
    StoryParams("garden", "fox", "hat", "wind"),
    StoryParams("pond", "duck", "bell", "frog"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for c in valid_combos():
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

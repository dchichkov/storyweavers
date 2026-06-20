#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/compensate_bad_ending_suspense_animal_story.py
===============================================================================

A standalone storyworld for a small animal tale with suspense, a compensating
attempt, and a bad ending when the attempt is too late.

Premise
-------
A hungry animal gets a beloved snack or toy stolen or dropped into a risky place.
Another animal tries to compensate with a helpful substitute or a careful rescue,
but the danger grows. The suspense comes from the ticking-state problem: the
hero waits, watches, and acts, and the ending proves whether the replacement was
enough.

This world keeps the prose concrete and child-facing, with a clear beginning,
middle turn, and ending image. The "compensate" word is embedded naturally as the
hero tries to make up for a mistake or loss.

The domain is intentionally small:
- forest / barn / pond scenes
- small animals
- one risky object, one helper, one substitute
- a bad ending if the delay is too long or the substitute is not sufficient
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
SUSPENSE_MIN = 1.0


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
        mapping = {"subject": "they", "object": "them", "possessive": "their"}
        if self.type in {"fox", "boy", "buck", "dog", "cat", "rabbit", "mouse", "bird"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        if self.type in {"girl", "doe", "hen", "cow", "duck", "squirrel"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        return mapping[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Scene:
    id: str
    place: str
    mood: str
    hiding_spot: str
    risk_word: str
    reveal: str

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
class Animal:
    id: str
    type: str
    label: str
    habitat: str
    fear: str
    voice: str
    plural: bool = False

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
    risky_place: str
    can_be_found: bool = False
    fragile: bool = True

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
class Compensate:
    id: str
    label: str
    phrase: str
    enough: bool
    power: int
    text: str
    fail: str
    qa_text: str

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


def _r_ripple(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["risk"] < THRESHOLD:
            continue
        sig = ("ripple", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in list(world.entities.values()):
            if other.role in {"watcher", "helper"}:
                other.memes["suspense"] += 1
        out.append("__ripple__")
    return out


def _r_delay(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("delay", 0) <= 1:
        return out
    sig = ("delay", world.facts.get("delay"))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role == "helper":
            e.memes["worry"] += 1
    out.append("__delay__")
    return out


CAUSAL_RULES = [Rule("ripple", "physical", _r_ripple), Rule("delay", "social", _r_delay)]


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


def hazardous(lost: LostThing, scene: Scene) -> bool:
    return lost.risky_place == scene.hiding_spot


def compensate_enough(comp: Compensate, delay: int) -> bool:
    return comp.enough and comp.power >= delay + 1


ANIMALS = {
    "mouse": Animal("mouse", "mouse", "mouse", "barn", "dark corners", "squeaky"),
    "fox": Animal("fox", "fox", "fox", "forest", "rustling leaves", "soft"),
    "rabbit": Animal("rabbit", "rabbit", "rabbit", "garden", "bushes", "quick"),
    "duck": Animal("duck", "duck", "duck", "pond", "water reeds", "wobbly"),
}

SCENES = {
    "barn": Scene("barn", "the old barn", "dusty", "haystack", "loft", "the haystack went still"),
    "forest": Scene("forest", "the shadowy forest", "windy", "big roots", "roots", "the roots looked darker"),
    "pond": Scene("pond", "the pond edge", "quiet", "reed bed", "reeds", "the water stopped moving"),
}

LOST_THINGS = {
    "cookie": LostThing("cookie", "cookie", "a crumbly cookie", "haystack", can_be_found=False, fragile=True),
    "scarf": LostThing("scarf", "scarf", "a red scarf", "roots", can_be_found=False, fragile=True),
    "bell": LostThing("bell", "bell", "a tiny bell", "reeds", can_be_found=False, fragile=False),
}

COMPENSATIONS = {
    "berry": Compensate("berry", "berry bundle", "a bowl of berries", True, 3,
                        "brought out a bowl of berries to compensate for the lost treat",
                        "brought berries, but the other animal was already too upset to smile",
                        "They brought out a bowl of berries to compensate."),
    "leaf": Compensate("leaf", "leaf nest", "a soft leaf nest", True, 2,
                       "made a soft leaf nest to compensate for the cold spot",
                       "made a leaf nest, but the wind scattered it before anyone could rest",
                       "They made a soft leaf nest to compensate."),
    "song": Compensate("song", "song", "a warm little song", False, 1,
                       "sang a warm little song to compensate, but the fear kept growing",
                       "sang a little song, but it was too late to help",
                       "They sang a warm little song to compensate."),
}

NAMES = {
    "mouse": ["Milo", "Mina", "Nibbles"],
    "fox": ["Finn", "Faye", "Rusty"],
    "rabbit": ["Ruby", "Rory", "Bun"],
    "duck": ["Daisy", "Dot", "Penny"],
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for scene_id, scene in SCENES.items():
        for animal_id in ANIMALS:
            for thing_id, thing in LOST_THINGS.items():
                if hazardous(thing, scene):
                    for comp_id, comp in COMPENSATIONS.items():
                        if comp.enough:
                            combos.append((scene_id, animal_id, thing_id, comp_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    scene: str
    animal: str
    lost: str
    compensate: str
    helper_name: str
    helper_type: str
    watcher_name: str
    watcher_type: str
    delay: int = 0
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small suspenseful animal storyworld about trying to compensate after a loss.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--compensate", choices=COMPENSATIONS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for lid, lost in LOST_THINGS.items():
        lines.append(asp.fact("lost", lid))
        lines.append(asp.fact("risky_place", lid, lost.risky_place))
    for cid, comp in COMPENSATIONS.items():
        lines.append(asp.fact("comp", cid))
        lines.append(asp.fact("enough", cid) if comp.enough else asp.fact("weak", cid))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(L,S) :- lost(L), scene(S), risky_place(L,P), hiding_spot(S,P).
valid(S,A,L,C) :- hazard(L,S), comp(C).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def story_setup(world: World, scene: Scene, animal: Animal, lost: LostThing) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["love"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In {scene.place}, {hero.id} the {animal.label} found a {lost.label_word} tucked near {scene.hiding_spot}."
    )
    world.say(
        f"{helper.id} watched the spot and whispered that it might slip away at any moment."
    )


def do_loss(world: World, lost: LostThing, scene: Scene) -> None:
    world.get("lost").meters["risk"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the wind turned, and the {lost.label} vanished deeper into {scene.reveal}."
    )


def do_compensate(world: World, comp: Compensate, helper: Entity, watcher: Entity) -> None:
    helper.memes["suspense"] += 1
    if compensate_enough(comp, int(world.facts["delay"])):
        world.say(
            f"{helper.id} tried to compensate by {comp.text}, and {watcher.id} held still to see if it would help."
        )
    else:
        world.say(
            f"{helper.id} tried to compensate by {comp.text}, but it felt too small."
        )


def do_ending(world: World, comp: Compensate, delay: int, lost: LostThing) -> None:
    if compensate_enough(comp, delay):
        world.say(
            f"In the end, the little fix did not bring back the lost thing, but it kept the animals together."
        )
    else:
        world.say(
            f"In the end, the forest stayed tense, and the lost thing was still gone."
        )


def tell(scene: Scene, animal: Animal, lost: LostThing, comp: Compensate,
         helper_name: str, helper_type: str, watcher_name: str, watcher_type: str,
         delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type=animal.type, role="hero", label=helper_name))
    helper = world.add(Entity("helper", kind="character", type=helper_type, role="helper", label=watcher_name))
    watcher = world.add(Entity("watcher", kind="character", type=watcher_type, role="watcher", label=watcher_name))
    world.add(Entity("lost", kind="thing", type=lost.id, label=lost.label, role="lost"))
    world.facts["delay"] = delay
    story_setup(world, scene, animal, lost)
    world.para()
    world.say(f"The air went quiet, and {helper.id} looked from the empty spot to {hero.id}.")
    do_loss(world, lost, scene)
    world.say(f"{watcher.id} waited, ears up, while {helper.id} searched for a way to compensate.")
    world.para()
    do_compensate(world, comp, helper, watcher)
    world.say("The waiting felt long.")
    world.para()
    do_ending(world, comp, delay, lost)
    return world


def choose_names(rng: random.Random, animal: Animal) -> tuple[str, str]:
    names = NAMES[animal.id]
    helper = rng.choice(names)
    watcher = rng.choice([n for n in names if n != helper] or names)
    return helper, watcher


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.animal is None or c[1] == args.animal)
              and (args.lost is None or c[2] == args.lost)
              and (args.compensate is None or c[3] == args.compensate)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene_id, animal_id, lost_id, comp_id = rng.choice(sorted(combos))
    helper_name, watcher_name = choose_names(rng, ANIMALS[animal_id])
    helper_type = rng.choice([ANIMALS[animal_id].type, "mouse", "fox", "rabbit", "duck"])
    watcher_type = rng.choice([ANIMALS[animal_id].type, "mouse", "fox", "rabbit", "duck"])
    delay = rng.randint(0, 2)
    return StoryParams(scene_id, animal_id, lost_id, comp_id, helper_name, helper_type, watcher_name, watcher_type, delay=delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], ANIMALS[params.animal], LOST_THINGS[params.lost],
                 COMPENSATIONS[params.compensate], params.helper_name, params.helper_type,
                 params.watcher_name, params.watcher_type, params.delay)
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
        f"Write a suspenseful animal story that includes the word compensate and ends sadly.",
        f"Tell a short animal story where a helper tries to compensate after something is lost, but the fix comes too late.",
        f"Write a child-friendly suspense story about animals, a missing thing, and a failed attempt to compensate.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    comp = COMPENSATIONS[f["compensate"]]
    lost = LOST_THINGS[f["lost"]]
    return [
        ("What happened in the story?", f"An animal lost something important, and another animal tried to compensate. The attempt could not bring the lost thing back in time."),
        ("Why was it suspenseful?", f"Everyone kept waiting to see if the helper's plan would work. The lost thing stayed out of reach, so the worry grew longer and longer."),
        ("Did the ending turn out happily?", f"No. The ending was sad, because the lost thing was still gone even after the helper tried to compensate."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does compensate mean?", "To compensate means to try to make up for a mistake or loss by doing something helpful."),
        ("What is suspense?", "Suspense is the feeling of waiting and wondering what will happen next."),
        ("Why can animals get scared in the dark?", "Dark places make it hard to see, so animals may worry about what is hiding nearby."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("barn", "mouse", "cookie", "berry", "Milo", "mouse", "Mina", "mouse", 1),
    StoryParams("forest", "fox", "scarf", "leaf", "Finn", "fox", "Faye", "fox", 2),
    StoryParams("pond", "duck", "bell", "song", "Daisy", "duck", "Penny", "duck", 2),
]


def asp_verify() -> int:
    import asp
    return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1


def generate_story(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        # smoke test
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise SystemExit(1)
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/4."))
        combos = sorted(set(asp.atoms(model, "valid")))
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
if __name__ == "__main__":
    main()

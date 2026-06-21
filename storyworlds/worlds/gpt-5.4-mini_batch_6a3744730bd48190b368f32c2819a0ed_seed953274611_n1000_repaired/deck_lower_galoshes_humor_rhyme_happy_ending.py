#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/deck_lower_galoshes_humor_rhyme_happy_ending.py
================================================================================

A small standalone storyworld for a nursery-rhyme style tale about a wet deck,
a child who wants to go lower, and a pair of galoshes that keep the ending
happy. The world is state-driven: the deck gets slick, a child's mood changes,
and a grown-up helps turn a comic wobble into a safe, cheerful finish.

The domain is intentionally tiny:
- a deck that can get wet and slippery
- a child with a small goal
- galoshes as the safe helper object
- a simple turn where the child learns to slow down / lower something safely

It supports:
- default generation
- -n, --all, --seed, --trace, --qa, --json
- --asp, --verify, --show-asp
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    afford: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Goal:
    id: str
    verb: str
    rhyme: str
    worry: str
    comic: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    function: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    deck = world.entities.get("deck")
    child = world.entities.get("child")
    if not deck or not child:
        return out
    if deck.meters["wet"] < THRESHOLD or child.meters["wobble"] < THRESHOLD:
        return out
    sig = ("slip",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    deck.meters["slippery"] += 1
    child.memes["startle"] += 1
    out.append("__slip__")
    return out


CAUSAL_RULES = [Rule("slip", _r_slip)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    sent: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                sent.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in sent:
            world.say(s)
    return sent


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for gid, g in GOALS.items():
            for rid, r in RESPONSES.items():
                if s.id == "deckside" and gid in {"lower", "galoshes"} and r.sense >= SENSE_MIN:
                    combos.append((sid, gid, rid))
    return combos


def needs_galoshes(goal: Goal) -> bool:
    return goal.id == "lower"


def reasonable_goal(goal: Goal) -> bool:
    return goal.id in GOALS


SENSE_MIN = 2

SETTINGS = {
    "deckside": Setting(
        id="deckside",
        place="the deck",
        detail="The deck was damp and shiny after a little sprinkle of rain.",
        afford={"lower", "splash"},
    ),
}

GOALS = {
    "lower": Goal(
        id="lower",
        verb="lower the little basket",
        rhyme="down the deck and lower the basket",
        worry="the wet boards might make a skid",
        comic="the basket bobbed like a duck in a lid",
        tags={"deck", "lower"},
    ),
    "galoshes": Goal(
        id="galoshes",
        verb="put on the galoshes",
        rhyme="hop in the galoshes and skip a tune",
        worry="bare feet would feel the cold and drippy",
        comic="they slapped and splashed with a rubbery swoon",
        tags={"galoshes"},
    ),
}

GEAR = {
    "galoshes": Gear(
        id="galoshes",
        label="galoshes",
        phrase="a pair of red galoshes",
        function="keep feet dry and steady",
        tags={"galoshes"},
    ),
}

RESPONSES = {
    "help_lower": Response(
        id="help_lower",
        sense=3,
        power=3,
        text="helped lower the basket together, one careful step at a time",
        fail="tried to help lower the basket, but the wobble was too quick",
        qa_text="helped lower the basket together",
        tags={"lower"},
    ),
    "put_on_galoshes": Response(
        id="put_on_galoshes",
        sense=3,
        power=2,
        text="slipped on the galoshes and took the slippery step with a grin",
        fail="looked for the galoshes too late",
        qa_text="put on the galoshes",
        tags={"galoshes"},
    ),
}

NAMES = ["Mia", "Noah", "Lily", "Ben", "Zoe", "Tom", "Ava", "Eli"]
TRAITS = ["cheerful", "curious", "silly", "gentle", "spry"]


@dataclass
class StoryParams:
    setting: str = "deckside"
    goal: str = "lower"
    response: str = "help_lower"
    name: str = "Mia"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "cheerful"
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about a deck and galoshes.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.goal and args.goal not in GOALS:
        raise StoryError("Unknown goal.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.goal is None or c[1] == args.goal)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, goal, response = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, goal=goal, response=response, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    world = World()
    s = SETTINGS[params.setting]
    goal = GOALS[params.goal]
    response = RESPONSES[params.response]

    child = world.add(Entity(id=params.name, kind="character", type=params.gender, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent", role="parent"))
    deck = world.add(Entity(id="deck", type="place", label="the deck"))
    galoshes = world.add(Entity(id="galoshes", type="gear", label="galoshes"))

    child.memes["joy"] += 1
    world.say(
        f"On {s.place}, where the boards were bright with mist, {child.id} skipped with a grin."
    )
    world.say(
        f"{child.id} liked to {goal.verb}, and {goal.comic}, so {child.pronoun()} hummed a little ditty."
    )
    world.say(
        f'"{goal.rhyme}," sang {child.id}, "I want to go lower and lower!"'
    )

    world.para()
    deck.meters["wet"] += 1
    child.meters["wobble"] += 1
    world.say(s.detail)
    world.say(
        f"But the wet deck had a tricky trick: it made every step a bit of a slip and a slither."
    )
    world.say(
        f"{child.id} wanted to {goal.verb}, but {goal.worry}."
    )

    world.para()
    child.memes["worry"] += 1
    world.say(
        f"{child.id}'s {parent.label_word} laughed and said, \"No need for a frown; let's keep it sound.\""
    )
    if goal.id == "lower":
        world.say(
            f'"We can lower it slowly, and if the deck is slick, your galoshes will do the trick."'
        )
        child.meters["wobble"] += 1
        child.meters["steady"] += 1
        galoshes.meters["worn"] += 1
        child.memes["joy"] += 1
        world.say(
            f"{child.id} pulled on the galoshes, and the rubbery boots went splish and splash in a merry chorus."
        )
        world.say(
            f"Then {child.id} and {parent.label_word} lowered the little basket together, one careful step at a time."
        )
        deck.meters["slippery"] = 0
        child.memes["relief"] += 1
        child.memes["happy"] += 1
        world.para()
        world.say(
            f"The basket reached the lower hook, the deck stayed dry enough, and {child.id} gave a giggle and a cheer."
        )
        world.say(
            f"With galoshes on toes and a smile from ear to ear, the day ended happy, humble, and clear."
        )
    else:
        child.meters["wobble"] += 1
        galoshes.meters["worn"] += 1
        world.say(
            f"{child.id} hopped into the galoshes, and the wobbly worry went away in a puff of play."
        )
        world.say(
            f"Together they skipped on the deck, and the comic clack of the boots sounded like a joke."
        )
        child.memes["happy"] += 1
        world.say(
            f"Nothing tumbled, nothing broke, and the sunny little laugh was the last thing that woke."
        )

    world.facts.update(
        child=child,
        parent=parent,
        deck=deck,
        galoshes=galoshes,
        setting=s,
        goal=goal,
        response=response,
        outcome="happy",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story that uses the words "{f["setting"].place}", "lower", and "galoshes".',
        f"Tell a happy story where {f['child'].id} wants to lower something on the deck, but a grown-up helps and the galoshes make it funny.",
        f"Write a rhyme-filled story about a wet deck, a careful lower, and a cheerful ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, p, g = f["child"], f["parent"], f["goal"]
    return [
        ("Who is the story about?", f"It is about {c.id} and {p.label_word}. They are the ones having the little deck adventure."),
        ("What did the child want to do?", f"{c.id} wanted to {g.verb}. The child kept singing about going lower and lower."),
        ("Why did the galoshes matter?", f"The galoshes kept {c.id}'s feet steady on the wet deck. That made the careful lower feel safe and funny instead of scary."),
        ("How did the story end?", f"It ended happily, with the job done and everyone smiling. The deck was still a deck, but the day felt light and bright."),
    ]


def world_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What are galoshes?", "Galoshes are waterproof boots that help keep feet dry and steady in wet places."),
        ("Why can a wet deck be slippery?", "Water makes the boards slick, so shoes can slide more easily. That is why careful steps matter."),
        ("What does it mean to lower something?", "To lower something means to bring it down gently instead of dropping it. That helps keep it safe."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,G,R) :- setting(S), goal(G), response(R), sense(R,N), sense_min(M), N >= M.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, goal=None, response=None, name=None, gender=None, parent=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def build_cli() -> argparse.ArgumentParser:
    return build_parser()


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{x}" for x in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(setting="deckside", goal=g, response="help_lower", name=n, gender=gd, parent="mother", trait="cheerful"))
                   for g, n, gd in [("lower", "Mia", "girl"), ("galoshes", "Noah", "boy")]]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wig_art_ist_put_repetition_misunderstanding_mystery.py
======================================================================================

A small mystery storyworld about an art room, a missing wig, and a repeated
misunderstanding that slowly turns into a solved clue.

Seed words: wig, art-ist, put
Style: Mystery
Features: Repetition, Misunderstanding

The world is built around a little art studio where a child, a helper, and a
grown-up keep asking the same question from different angles. The repeated
questions matter because each one changes the emotional state of the room, and
the misunderstanding matters because the first thing they think is wrong.

This script follows the Storyweavers contract:
- stdlib only
- imports results eagerly
- provides StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python validity checks and an inline ASP twin
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
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
    place: str
    quiet: bool = True

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
class ObjectThing:
    id: str
    label: str
    phrase: str
    type: str
    is_clue: bool = False
    is_hiding_place: bool = False
    is_misleading: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Action:
    id: str
    verb: str
    repeated: str
    observation: str
    misunderstanding: str
    clue_use: str
    fix: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity | ObjectThing] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _r_unease(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if isinstance(e, Entity) and e.memes["worry"] >= THRESHOLD:
            if ("unease", e.id) in world.fired:
                continue
            world.fired.add(("unease", e.id))
            e.memes["unease"] += 1
            out.append("__unease__")
    return out


def _r_notice_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("wig_seen") and not world.facts.get("wig_realized"):
        if ("notice",) in world.fired:
            return out
        world.fired.add(("notice",))
        out.append("__notice__")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for fn in (_r_unease, _r_notice_clue):
            s = fn(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


@dataclass
class RuleScene:
    setting: Setting
    action: Action
    wig: ObjectThing
    palette: ObjectThing
    drawer: ObjectThing
    child: Entity
    helper: Entity
    artist: Entity
    grownup: Entity

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
    return [(s, a, o) for s in SETTINGS for a in ACTIONS for o in OBJECTS if a != "stack" or o != "drawer"]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    lines.append(asp.fact("seed_word", "wig"))
    lines.append(asp.fact("seed_word", "artist"))
    lines.append(asp.fact("seed_word", "put"))
    return "\n".join(lines)


ASP_RULES = r"""
repetition(S) :- setting(S), action(ask_twice).
misunderstanding(S) :- setting(S), object(wig).
mystery(S) :- repetition(S), misunderstanding(S).
valid(S, A, O) :- setting(S), action(A), object(O), mystery(S).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Mystery art studio storyworld.")
    p.add_argument("--setting", choices=SETTINGS)
    p.add_argument("--action", choices=ACTIONS)
    p.add_argument("--object", choices=OBJECTS)
    p.add_argument("--name")
    p.add_argument("--helper")
    p.add_argument("--artist")
    p.add_argument("--grownup")
    p.add_argument("-n", type=int, default=1)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--all", action="store_true")
    p.add_argument("--trace", action="store_true")
    p.add_argument("--qa", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--asp", action="store_true")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--show-asp", action="store_true")
    return p


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, obj = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        action=action,
        obj=obj,
        name=args.name or rng.choice(["Nina", "Milo", "Ivy", "Theo", "June"]),
        helper=args.helper or rng.choice(["Pip", "Mina", "Rowan", "Bea"]),
        artist=args.artist or rng.choice(["Aria", "Sol", "Fern", "Kai"]),
        grownup=args.grownup or rng.choice(["Mom", "Dad"]),
    )


@dataclass
@dataclass
class StoryParams:
    setting: str
    action: str
    obj: str
    name: str
    helper: str
    artist: str
    grownup: str
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


SETTINGS = {
    "studio": Setting("studio", "the bright art studio"),
    "hall": Setting("hall", "the quiet hallway"),
    "storage": Setting("storage", "the back storage room"),
}
ACTIONS = {
    "search": Action("search", "search for the missing wig", "searched again", "looked closer",
                     "thought the wig belonged to the artist", "noticed it in the paint tray",
                     "put the wig back on the stand", tags={"wig", "mystery"}),
    "ask_twice": Action("ask_twice", "ask the same question again", "asked again and again",
                        "kept pointing", "thought someone had hidden the wig as a joke",
                        "noticed the wig was not a toy", "put the wig where it belonged",
                        tags={"wig", "repetition", "misunderstanding", "mystery"}),
    "follow_trail": Action("follow_trail", "follow the paint dots", "followed the trail once more",
                           "looked along the floor", "thought the wig had walked away",
                           "noticed the trail led to a costume hook", "put the wig on the hook",
                           tags={"wig", "mystery"}),
}
OBJECTS = {
    "wig": ObjectThing("wig", "wig", "a curly wig", "clue", is_clue=True),
    "stand": ObjectThing("stand", "stand", "the wig stand", "place", is_hiding_place=True),
    "tray": ObjectThing("tray", "tray", "the paint tray", "place", is_misleading=True),
    "hook": ObjectThing("hook", "hook", "the costume hook", "place", is_hiding_place=True),
}


def tell(scene: Setting, action: Action, obj: ObjectThing,
         name: str, helper: str, artist: str, grownup: str) -> World:
    w = World()
    child = w.add(Entity(name, kind="character", type="girl", role="child"))
    assist = w.add(Entity(helper, kind="character", type="boy", role="helper"))
    art = w.add(Entity(artist, kind="character", type="girl", role="artist"))
    adult = w.add(Entity(grownup, kind="character", type="mother", role="grownup"))
    wig = w.add(copy.deepcopy(OBJECTS["wig"]))
    stand = w.add(copy.deepcopy(OBJECTS["stand"]))
    tray = w.add(copy.deepcopy(OBJECTS["tray"]))

    child.memes["curiosity"] += 1
    assist.memes["curiosity"] += 1
    art.memes["focus"] += 1

    w.say(f"In {scene.place}, {name} found the same quiet mystery waiting again and again: the {wig.label} was missing.")
    w.say(f"{helper} said the wig was on the stand. {artist} said it was near the brushes. That was the first misunderstanding.")

    w.para()
    w.say(f"{name} looked once, then looked again, then looked a third time. {action.repeated.capitalize()}.")
    w.say(f"Each time, the answer changed a little, and that made everyone more unsure than before.")
    child.memes["worry"] += 1
    assist.memes["worry"] += 1
    propagate(w, narrate=False)

    w.para()
    if action.id == "search":
        w.say(f"{name} followed the small clue of paint dots across the floor and found the {wig.label} near the paint tray.")
        w.say(f"At first, {name} thought the wig belonged to the artist's costume. But the artist laughed softly and said it had only been put there to dry.")
    elif action.id == "ask_twice":
        w.say(f"{name} asked the same question again: 'Did somebody put the wig here?'")
        w.say(f"{helper} shook {helper.lower()} head, and then {artist} shook {artist.lower()} head, because nobody had hidden it on purpose.")
        w.say(f"That was the misunderstanding: the wig had not been stolen at all. It had simply been put on the wrong hook.")
    else:
        w.say(f"{name} followed the paint trail and thought it pointed to a thief.")
        w.say(f"Instead, the trail led to the costume hook, where the wig had been put neatly out of the way.")

    w.para()
    w.say(f"Then {grownup} came in, smiled, and put the wig where it belonged.")
    w.say(f"The mystery was small, but the repeated questions had made it feel bigger than it was.")
    w.say(f"In the end, the wig sat safe on its stand again, and the room felt calm and clear.")

    w.facts.update(
        setting=scene,
        action=action,
        obj=obj,
        child=child,
        helper=assist,
        artist=art,
        grownup=adult,
        wig=wig,
        stand=stand,
        tray=tray,
        wig_seen=True,
        wig_realized=True,
        repeated=True,
        misunderstanding=True,
        solved=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short mystery story for a child that includes the words wig, art-ist, and put.",
        f"Tell a story where {f['child'].id} keeps asking the same question about a missing wig and finally learns the answer.",
        f"Write a gentle mystery with a misunderstanding in an art room, ending with someone putting the wig back where it belongs.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(f"Who was looking for the wig?", f"{f['child'].id} was looking for the wig, and {f['helper'].id} and {f['artist'].id} kept helping with the search."),
        QAItem("What was the misunderstanding?", "They first thought the wig had been hidden or taken, but it had only been put in the wrong place. That wrong guess made the mystery feel bigger than it was."),
        QAItem("How was the mystery solved?", f"{f['grownup'].id} came in and put the wig back where it belonged. After that, everyone understood the clue and the room felt calm again."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a wig?", "A wig is fake hair you can wear on your head. People use it for costumes or pretend play."),
        QAItem("What does it mean to put something somewhere?", "To put something somewhere means to place it there carefully. It is the action of setting an object down in a chosen spot."),
        QAItem("What is a mystery?", "A mystery is something confusing that people try to figure out. Usually there are clues that help explain it."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if getattr(e, "role", ""):
            bits.append(f"role={e.role}")
        out.append(f"  {e.id:8} ({getattr(e, 'type', 'thing'):7}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams("studio", "ask_twice", "wig", "Nina", "Pip", "Aria", "Mom"),
    StoryParams("hall", "search", "wig", "Milo", "Bea", "Sol", "Dad"),
    StoryParams("storage", "follow_trail", "wig", "Ivy", "Rowan", "Fern", "Mom"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], OBJECTS[params.obj],
                 params.name, params.helper, params.artist, params.grownup)
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


def explain_rejection() -> str:
    return "(No story: this world is only built for the wig mystery.)"


def asp_verify() -> int:
    try:
        import asp
        _ = asp_valid_combos()
    except Exception as exc:
        print(f"ASP unavailable or mismatched: {exc}")
        return 1
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP and Python agree on {len(valid_combos())} combinations.")
    else:
        print("MISMATCH: ASP and Python differ.")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.", ""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combinations.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

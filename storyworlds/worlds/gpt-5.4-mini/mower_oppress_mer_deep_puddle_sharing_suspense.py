#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mower_oppress_mer_deep_puddle_sharing_suspense.py
===================================================================================

A standalone story world for a small animal tale about sharing across a deep
puddle, with a suspenseful turn and a gentle ending.  It keeps the world model
tight: typed entities have physical meters and emotional memes, the plot is
driven by state changes, and the generated prose follows what happened rather
than swapping nouns into a fixed paragraph.

Seed words / prompt cues:
- mower
- oppress
- mer
- deep puddle
- Sharing
- Suspense
- Animal Story

The story world centers on two animal friends who want to move a little mower
across a deep puddle. A tense moment happens when the mower slips near the water,
and a shared plan with a rope, a stick, or a helping paw keeps the mower safe.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Theme:
    id: str
    setting: str
    play_frame: str
    goal: str
    ending_image: str
    role_solo: str = "an animal"
    role_plural: str = "animals"

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
class ActorCfg:
    id: str
    species: str
    label: str
    kind_word: str
    age: int
    bold: int

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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    risky: bool = True

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
class HelperCfg:
    id: str
    label: str
    tool: str
    guard: int

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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    puddle = world.entities.get("puddle")
    if not puddle:
        return out
    if puddle.meters["danger"] < THRESHOLD:
        return out
    sig = ("slip", "puddle")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role in {"instigator", "helper"}:
            e.memes["suspense"] += 1
    out.append("__slip__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    tool = world.entities.get("tool")
    if not helper or not tool:
        return out
    if helper.memes["share"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tool.meters["safe"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES = [Rule("slip", _r_slip), Rule("share", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            for item in rule.apply(world):
                if item.startswith("__"):
                    continue
                produced.append(item)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def danger_check(target: ObjectCfg) -> bool:
    return target.risky


def sensible_tools() -> list[HelperCfg]:
    return [h for h in HELPERS.values() if h.guard >= SENSE_MIN]


def choose_tool(target: ObjectCfg) -> Optional[HelperCfg]:
    for h in HELPERS.values():
        if h.guard >= SENSE_MIN and target.risky:
            return h
    return None


def simulate_risk(world: World) -> dict:
    sim = world.copy()
    sim.get("puddle").meters["danger"] = 1
    propagate(sim, narrate=False)
    return {
        "suspense": sim.get("hero").memes["suspense"],
        "safe": sim.get("tool").meters["safe"] >= THRESHOLD,
    }


def start(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright morning, {a.label_word} and {b.label_word} went to "
        f"{theme.setting}. {theme.play_frame}"
    )
    world.say(
        f"They found {theme.goal} and a wide, deep puddle waiting in the path."
    )


def want_mower(world: World, a: Entity, tool: Entity) -> None:
    a.memes["want"] += 1
    world.say(
        f"{a.label_word} wanted to roll the mower through the mud, because "
        f"the mower looked ready for a game."
    )
    world.say(
        f'"Look," {a.label_word} said, "the mower can go first."'
    )


def warn(world: World, b: Entity, a: Entity, tool: Entity, puddle: Entity) -> None:
    b.memes["care"] += 1
    world.say(
        f"{b.label_word} pointed at the deep puddle and spoke in a small, serious "
        f"voice. " 
        f'"If the mower slips there, we may not get it back right away."'
    )
    world.say(
        f"{b.label_word} did not want to oppress the fun; {b.pronoun()} only wanted "
        f"to keep the mower safe."
    )


def suspense(world: World, a: Entity, b: Entity, tool: Entity, puddle: Entity) -> None:
    puddle.meters["danger"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The mower rolled closer and closer to the puddle's edge. For a moment, "
        f"the whole path went quiet."
    )
    world.say(
        f"{a.label_word} held {a.pronoun('possessive')} breath while {b.label_word} "
        f"stretched out a helping paw."
    )


def share(world: World, a: Entity, b: Entity, tool: Entity, helper: HelperCfg) -> None:
    b.memes["share"] += 1
    world.say(
        f"Then {b.label_word} remembered the {helper.tool}. {b.label_word} shared it "
        f"with {a.label_word}, and together they hooked the mower safely."
    )
    world.say(
        f"They pulled at the same time, nice and slow, so the mower stayed dry."
    )


def ending(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(theme.ending_image)
    world.say(
        f"After that, {a.label_word} and {b.label_word} could laugh again, and "
        f"the mower became part of their shared game."
    )


def tell(theme: Theme, actor1: ActorCfg, actor2: ActorCfg, target: ObjectCfg,
         helper: HelperCfg) -> World:
    world = World()
    hero = world.add(Entity(id=actor1.id, kind="character", type=actor1.species, label=actor1.label, role="instigator"))
    friend = world.add(Entity(id=actor2.id, kind="character", type=actor2.species, label=actor2.label, role="helper"))
    tool = world.add(Entity(id="tool", type="thing", label=target.label))
    puddle = world.add(Entity(id="puddle", type="thing", label="deep puddle"))
    world.facts["theme"] = theme
    world.facts["actor1"] = hero
    world.facts["actor2"] = friend
    world.facts["target"] = target
    world.facts["helper"] = helper

    start(world, hero, friend, theme)
    world.para()
    want_mower(world, hero, tool)
    warn(world, friend, hero, tool, puddle)
    world.para()
    suspense(world, hero, friend, tool, puddle)
    share(world, hero, friend, tool, helper)
    world.para()
    ending(world, hero, friend, theme)
    world.facts["outcome"] = "shared"
    return world


THEMES = {
    "deep_puddle": Theme(
        "deep_puddle",
        "the edge of a deep puddle by the grass",
        "The two animal friends were playing beside the path, and the air felt still.",
        "a little mower",
        "The puddle shone like a mirror, and the mower was dry and safe again.",
        "a little animal",
        "two animals",
    )
}

ACTORS = {
    "rabbit": ActorCfg("Pip", "rabbit", "Pip", "young rabbit", 5, 6),
    "duck": ActorCfg("Dot", "duck", "Dot", "duck", 6, 5),
    "fox": ActorCfg("Fin", "fox", "Fin", "fox", 7, 4),
}

OBJECTS = {
    "mower": ObjectCfg("mower", "mower", "a little mower", True),
}

HELPERS = {
    "rope": HelperCfg("rope", "rope", "short rope", 3),
    "stick": HelperCfg("stick", "stick", "long stick", 2),
    "net": HelperCfg("net", "net", "small net", 4),
}



@dataclass
class StoryParams:
    theme: str
    actor1: str
    actor2: str
    target: str
    helper: str
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
    StoryParams("deep_puddle", "rabbit", "duck", "mower", "rope", seed=1),
    StoryParams("deep_puddle", "fox", "rabbit", "mower", "stick", seed=2),
    StoryParams("deep_puddle", "duck", "fox", "mower", "net", seed=3),
]



def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for t in THEMES:
        for a1 in ACTORS:
            for a2 in ACTORS:
                if a1 == a2:
                    continue
                for obj in OBJECTS:
                    for h in HELPERS:
                        combos.append((t, a1, a2, h))
    return combos


KNOWLEDGE = {
    "mower": [("What is a mower?",
               "A mower is a tool that cuts grass. People usually guide it along the ground.")],
    "puddle": [("What is a puddle?",
                "A puddle is a small pool of water on the ground after rain.")],
    "share": [("What does it mean to share?",
               "To share means to let someone else use something with you or help with it.")],
    "suspense": [("What is suspense?",
                  "Suspense is the tense feeling you get when you are waiting to see what happens next.")],
    "rope": [("What can a rope be used for?",
              "A rope can help pull, carry, or tie things together when grown-ups or careful kids use it safely.")],
    "stick": [("What can a stick help with?",
               "A stick can help reach or push something from a little farther away.")],
    "net": [("What is a net?",
             "A net is made of string or cord with holes in it, and it can help catch or hold things.")],
    "oppress": [("What does the word oppress mean?",
                 "To oppress means to treat someone unfairly or make things feel hard and heavy for them.")],
    "mer": [("What does mer mean in a fairy tale word?",
              "Mer can be a short, storybook-sounding word, often used in a made-up name or a sea-themed word.")],
}
KNOWLEDGE_ORDER = ["mower", "puddle", "share", "suspense", "rope", "stick", "net", "oppress", "mer"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story with the words "mower", "oppress", and "mer".',
        f"Tell a suspenseful sharing story where {f['actor1'].label_word} and {f['actor2'].label_word} keep a mower safe near a deep puddle.",
        f"Write a calm but tense story about two animal friends who share a tool and solve a puddle problem together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["actor1"]
    b = f["actor2"]
    theme = f["theme"]
    return [
        ("Who are the story about?",
         f"The story is about {a.label_word} and {b.label_word}, two animal friends who were playing by a deep puddle."),
        ("What were they trying to do?",
         f"They were trying to keep the mower safe and move it past the deep puddle without letting it slip in."),
        ("What made the moment feel tense?",
         f"The mower rolled close to the puddle's edge, so everyone had to watch carefully. That near-slip created the suspense in the story."),
        ("How did they solve the problem?",
         f"They shared the helper tool and pulled together. Working together kept the mower dry and let them finish safely."),
        ("How did the story end?",
         f"It ended with the puddle shining and the mower safe again. The animals could laugh and keep sharing their game."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    tags = {"mower", "puddle", "share", "suspense", "oppress", "mer"}
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
dangerous_puddle(P) :- puddle(P), deep(P).
sensible(H) :- helper(H), guard(H, G), G >= sense_min.
valid(T, A1, A2, H) :- theme(T), actor(A1), actor(A2), A1 != A2, helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
        lines.append(asp.fact("puddle", "puddle"))
        lines.append(asp.fact("deep", "puddle"))
    for aid in ACTORS:
        lines.append(asp.fact("actor", aid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("guard", hid, h.guard))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: clingo gate matches valid_combos().")
    else:
        print("MISMATCH: ASP and Python validity differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: sharing, suspense, and a deep puddle.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--actor1", choices=ACTORS)
    ap.add_argument("--actor2", choices=ACTORS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--target", choices=OBJECTS)
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
              if (args.theme is None or c[0] == args.theme)
              and (args.actor1 is None or c[1] == args.actor1)
              and (args.actor2 is None or c[2] == args.actor2)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, a1, a2, helper = rng.choice(sorted(combos))
    return StoryParams(theme, a1, a2, "mower", helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], ACTORS[params.actor1], ACTORS[params.actor2], OBJECTS[params.target], HELPERS[params.helper])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for row in asp_valid_combos():
            print(" ", row)
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
            params = resolve_params(args, random.Random(seed))
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

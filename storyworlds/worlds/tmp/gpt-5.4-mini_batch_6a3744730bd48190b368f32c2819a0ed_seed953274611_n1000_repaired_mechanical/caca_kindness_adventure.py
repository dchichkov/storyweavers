#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/caca_kindness_adventure.py
===========================================================

A small standalone storyworld for an adventure tale about kindness, discovery,
and a helpful little mistake called "caca".

Premise
-------
A child on a make-believe adventure wants to reach a tiny treasure place. Along
the way, someone has an accident or a yucky mishap, and the kind choice is to
stop, help, clean up, and keep going together. The ending should feel like a
small brave journey that became kinder because of what happened.

This world keeps the prose concrete and state-driven:
- entities have meters and memes,
- the plot moves through a few causal beats,
- kindness changes the social state,
- the ending image proves something changed.

It also includes a Python reasonableness gate and an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/caca_kindness_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/caca_kindness_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/caca_kindness_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/caca_kindness_adventure.py --verify
    python storyworlds/worlds/gpt-5.4-mini/caca_kindness_adventure.py --show-asp
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

NAMES = ["Mia", "Noah", "Lina", "Eli", "Zoe", "Ari", "Nora", "Theo"]
HELPER_NAMES = ["Pip", "Juno", "Bea", "Max", "Tia", "Rae"]
PLACES = {
    "trail": "a winding trail by the trees",
    "cave": "a sunny cave at the hill",
    "island": "a little island beach",
}
ARTIFACTS = {
    "map": "a crinkly map",
    "lantern": "a tiny lantern",
    "shell": "a shiny shell",
}
MISHAPS = {
    "caca": {
        "label": "caca",
        "mess": "yucky",
        "cause": "a squishy caca patch on the path",
        "clean": "wipe up the caca with leaves and water",
        "risk": "it could make the path slippery and stop the adventure",
        "kindness": "kindness means helping first instead of laughing",
    }
}
AID = {
    "kit": {
        "label": "cleaning kit",
        "tool": "a small cleaning kit",
        "use": "cleaned the mess carefully",
    },
    "water": {
        "label": "water bottle",
        "tool": "a bottle of water and a cloth",
        "use": "poured water and wiped the ground clean",
    },
    "leaves": {
        "label": "leaf bundle",
        "tool": "a bundle of big leaves",
        "use": "covered the mess so nobody stepped in it",
    },
}

ASP_RULES = r"""
risk(mishap, caca) :- mishap(caca).
kind_path(caca) :- kind(mishap).
valid(mishap, aid) :- risk(mishap, caca), aid(aid).
kind_story(caca, aid) :- valid(mishap, aid), kind(mishap).
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)

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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    mishap: str
    place: str
    artifact: str
    aid: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    guide: str
    guide_type: str
    seed: Optional[int] = None
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
        w.facts = dict(self.facts)
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


def _r_soften(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["mess"] >= THRESHOLD and ("soften", e.id) not in world.fired:
            world.fired.add(("soften", e.id))
            e.memes["embarrassment"] += 1
            out.append("__soften__")
    return out

def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            xs = rule.apply(world)
            if xs:
                changed = True
                out.extend(x for x in xs if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out

CAUSAL_RULES = [Rule("soften", _r_soften)]

def reasonableness_gate(mishap: str, aid: str) -> bool:
    return mishap in MISHAPS and aid in AID

def valid_combos() -> list[tuple[str, str, str]]:
    return [("trail", "caca", k) for k in AID]

def asp_facts() -> str:
    import asp
    lines = [asp.fact("mishap", "caca"), asp.fact("kind", "mishap")]
    for aid in AID:
        lines.append(asp.fact("aid", aid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))

def tell(params: StoryParams) -> World:
    if not reasonableness_gate(params.mishap, params.aid):
        raise StoryError("That adventure setup is not reasonable.")
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_type, role="friend"))
    guide = world.add(Entity(id=params.guide, kind="character", type=params.guide_type, role="guide"))
    mish = MISHAPS[params.mishap]
    aid = AID[params.aid]
    hero.memes["curiosity"] += 1
    friend.memes["joy"] += 1
    world.say(f"{hero.id} and {friend.id} set off on an adventure at {PLACES[params.place]}.")
    world.say(f"They carried {ARTIFACTS[params.artifact]} and followed it toward a small treasure place.")
    world.para()
    world.say(f"Then they found {mish['cause']}.")
    world.say(f"{friend.id} wrinkled {friend.pronoun('possessive')} nose, but {guide.id} stayed calm.")
    world.say(f'"{mish["kindness"]}," {guide.id} said. "We can help and keep going."')
    friend.meters["mess"] += 1
    hero.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(f"{hero.id} knelt down, and together they used {aid["tool"]} to help clean the path.")
    world.say(f"{guide.id} showed them how to move slowly, and soon {aid["use"]}.")
    world.say(f"The adventure started again, and the little treasure place was right ahead.")
    world.say(f"This time, {hero.id} picked up {ARTIFACTS[params.artifact]} with clean hands and smiled at {friend.id}.")
    world.facts.update(hero=hero, friend=friend, guide=guide, mishap=params.mishap, aid=params.aid, place=params.place, artifact=params.artifact)
    return world

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly adventure story that includes the word "{f["mishap"]}" and shows kindness.',
        f"Tell a small adventure where {f['hero'].id} helps after a yucky {f['mishap']} mess.",
        f"Write a story about a brave walk, a surprise mess, and a kind helper who keeps the adventure going.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, guide = f["hero"], f["friend"], f["guide"]
    return [
        QAItem(question=f"What happened on the path?", answer=f"They found caca on the path, and it made the adventure pause for a moment before anyone could keep going."),
        QAItem(question=f"What did {guide.id} teach them?", answer=f"{guide.id} taught them that kindness means helping first. That made the mess smaller and helped the adventure start again."),
        QAItem(question=f"How did the story end?", answer=f"It ended with clean hands, calmer faces, and the treasure place still waiting ahead. {hero.id} and {friend.id} kept walking together after helping."),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is kindness?", answer="Kindness is choosing to help, share, and care about someone else's problem. It can turn a hard moment into a better one."),
        QAItem(question="Why should a caca mess be cleaned up?", answer="A caca mess should be cleaned up because it is yucky and can spread germs or make the ground slippery. Cleaning it helps keep everyone safe."),
        QAItem(question="What should you do when you find a mess on a path?", answer="You should stop, stay calm, and ask for help or clean it carefully with a grown-up. That keeps the path safe for the next person."),
    ]

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        me = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if me:
            bits.append(f"memes={me}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about caca and kindness.")
    ap.add_argument("--mishap", choices=MISHAPS, default="caca")
    ap.add_argument("--place", choices=PLACES, default="trail")
    ap.add_argument("--artifact", choices=ARTIFACTS, default="map")
    ap.add_argument("--aid", choices=AID)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--guide")
    ap.add_argument("--hero-type", choices=["girl", "boy"], default="girl")
    ap.add_argument("--friend-type", choices=["girl", "boy"], default="boy")
    ap.add_argument("--guide-type", choices=["girl", "boy"], default="girl")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    aid = args.aid or rng.choice(sorted(AID))
    if not reasonableness_gate("caca", aid):
        raise StoryError("Invalid setup.")
    return StoryParams(
        mishap="caca",
        place=args.place or "trail",
        artifact=args.artifact or "map",
        aid=aid,
        hero=args.hero or rng.choice(NAMES),
        hero_type=args.hero_type,
        friend=args.friend or rng.choice([n for n in HELPER_NAMES if n != args.hero]),
        friend_type=args.friend_type,
        guide=args.guide or rng.choice(HELPER_NAMES),
        guide_type=args.guide_type,
    )

def generate(params: StoryParams) -> StorySample:
    if params.mishap not in MISHAPS:
        raise StoryError("Unknown mishap.")
    if params.aid not in AID:
        raise StoryError("Unknown aid.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )

CURATED = [
    StoryParams(mishap="caca", place="trail", artifact="map", aid="kit", hero="Mia", hero_type="girl", friend="Noah", friend_type="boy", guide="Pip", guide_type="girl"),
    StoryParams(mishap="caca", place="island", artifact="shell", aid="water", hero="Lina", hero_type="girl", friend="Ari", friend_type="boy", guide="Juno", guide_type="girl"),
    StoryParams(mishap="caca", place="cave", artifact="lantern", aid="leaves", hero="Theo", hero_type="boy", friend="Zoe", friend_type="girl", guide="Bea", guide_type="girl"),
]

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))

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

def asp_program_full(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo gate.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program_full("#show valid/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clutz_suspense_nursery_rhyme.py
===============================================================

A small standalone storyworld for a nursery-rhyme-like suspense tale about
a clutz in a moonlit nursery. The domain is built around a tiny, stateful
sequence: a bedtime game begins, a clumsy mishap creates a scary moment, a
calm helper uses a clever trick, and the ending proves the world is safe again.

The prose aims to keep a sing-song, child-facing feel while still being driven
by simulated meters and memes rather than a frozen paragraph with swapped nouns.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "cat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    room: str
    hero: str
    helper: str
    mischief: str
    danger: str
    safe_fix: str
    seed: Optional[int] = None


@dataclass
class Room:
    id: str
    label: str
    moonlit: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Mischief:
    id: str
    label: str
    action: str
    sound: str
    risk: str
    makes_noise: bool = True
    causes_shadow: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Danger:
    id: str
    label: str
    seems: str
    worsens: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    action: str
    glow: str
    calm: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.rooms: dict[str, Room] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_room(self, room: Room) -> Room:
        self.rooms[room.id] = room
        return room

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
        clone.rooms = copy.deepcopy(self.rooms)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["noisy"] < THRESHOLD:
            continue
        sig = ("noise", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.rooms["nursery"].meters["unease"] += 1
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["startle"] += 1
        out.append("__noise__")
    return out


def _r_shadow(world: World) -> list[str]:
    out: list[str] = []
    if world.rooms["nursery"].meters["unease"] < THRESHOLD:
        return out
    sig = ("shadow")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.rooms["nursery"].meters["shadow"] += 1
    out.append("__shadow__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.rooms["nursery"].meters["shadow"] < THRESHOLD:
        return out
    sig = ("calm")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.entities.values():
        if e.kind == "character":
            e.memes["worry"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("noise", _r_noise), Rule("shadow", _r_shadow), Rule("calm", _r_calm)]


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


def hazard_at_risk(mischief: Mischief, danger: Danger) -> bool:
    return mischief.causes_shadow and danger.worsens == "shadow"


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.id in {"nightlight", "lullaby", "lantern"}]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.id == "nightlight")


def world_tale(world: World, hero: Entity, helper: Entity, mischief: Mischief,
               danger: Danger, fix: Fix) -> None:
    nursery = world.rooms["nursery"]
    hero.memes["curious"] += 1
    helper.memes["watchful"] += 1
    world.say(
        f"Under the hush of the moon, {hero.id} and {helper.id} played in the {nursery.label}. "
        f"The room was soft and silver, and every shadow sat still as a mouse."
    )
    world.say(
        f'But {hero.id}, the clutz, gave {mischief.action}. {mischief.sound} went the little mishap, '
        f'and {mischief.risk} showed its teeth.'
    )
    world.para()
    world.say(
        f'"Oh dear," whispered {helper.id}. "That looks {danger.seems}, and the dark may grow."'
    )
    world.say(
        f'{hero.id} blinked and clutched {hero.pronoun("possessive")} sleeve. The nursery felt very quiet, '
        f'but not very safe.'
    )
    world.say(
        f'Then {helper.id} hummed {fix.action}; {fix.glow} and {fix.calm}.'
    )
    world.say(
        f"The shadow shrank. The room turned sweet and small again, and the moon looked friendly at the window."
    )
    world.say(
        f'By the end, {hero.id} was no longer a wobbling clutz in the gloom; {hero.id} was a sleepy little helper, '
        f'sitting still while the nursery sang itself to sleep.'
    )


ROOMS = {
    "nursery": Room(id="nursery", label="nursery"),
    "bedroom": Room(id="bedroom", label="bedroom"),
    "playroom": Room(id="playroom", label="playroom"),
}

MISCHIEF = {
    "toybox_tumble": Mischief(
        id="toybox_tumble", label="toybox tumble", action="reached too far for the rattle",
        sound="Clatter-clink!", risk="one toy rolled under the bed", causes_shadow=True,
        tags={"clutz", "suspense"},
    ),
    "curtain_tug": Mischief(
        id="curtain_tug", label="curtain tug", action="pulled the curtain string by mistake",
        sound="Swish!", risk="the curtain made a tall, spooky sway", causes_shadow=True,
        tags={"clutz", "suspense"},
    ),
    "nightlamp_bump": Mischief(
        id="nightlamp_bump", label="nightlamp bump", action="bumped the nightlamp with a knee",
        sound="Bonk!", risk="the lamp blinked out for a breath", causes_shadow=True,
        tags={"clutz", "suspense"},
    ),
}

DANGERS = {
    "shadow": Danger(id="shadow", label="shadow", seems="a little spooky", worsens="shadow", tags={"shadow"}),
    "hush": Danger(id="hush", label="hush", seems="very hushy", worsens="shadow", tags={"hush"}),
}

FIXES = {
    "nightlight": Fix(id="nightlight", label="nightlight", action="a gentle nightlight wink", glow="the nightlight glowed like a tiny moon", calm="its warm glow made the corners round and kind", tags={"light"}),
    "lullaby": Fix(id="lullaby", label="lullaby", action="a soft lullaby", glow="the tune floated over the quilt", calm="the tune tucked the worry in like a blanket", tags={"song"}),
    "lantern": Fix(id="lantern", label="lantern", action="a paper lantern blink", glow="the lantern shone amber and small", calm="its glow made the shadows behave", tags={"light"}),
}

NAMES = ["Milo", "Nina", "Pip", "Lila", "Toby", "Rose"]
HELPERS = ["Mama", "Papa", "Grandma", "Grandpa", "Nurse"]
VALID_MISCHIEF = ["toybox_tumble", "curtain_tug", "nightlamp_bump"]
VALID_FIXES = ["nightlight", "lullaby", "lantern"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for mis in MISCHIEF:
            for fix in FIXES:
                combos.append((room, mis, fix))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A clutzy suspense nursery-rhyme storyworld.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--mischief", choices=MISCHIEF)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
              if (args.room is None or c[0] == args.room)
              and (args.mischief is None or c[1] == args.mischief)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, mis, fix = rng.choice(sorted(combos))
    return StoryParams(
        room=room,
        hero=args.hero or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        mischief=mis,
        danger="shadow",
        safe_fix=fix,
    )


def tell(params: StoryParams) -> World:
    if params.room not in ROOMS or params.mischief not in MISCHIEF or params.safe_fix not in FIXES:
        raise StoryError("Invalid StoryParams.")
    world = World()
    world.add_room(copy.deepcopy(ROOMS[params.room]))
    hero = world.add(Entity(id=params.hero, kind="character", type="boy", role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type="mother", role="helper"))
    mis = MISCHIEF[params.mischief]
    danger = DANGERS[params.danger]
    fix = FIXES[params.safe_fix]

    hero.memes["sleepy"] += 1
    helper.memes["watchful"] += 1

    world.say(
        f"By the nursery light, {hero.id} was a clutz, a tripping little sprite, "
        f"with a moonbeam smile and a heart so bright."
    )
    world.say(
        f"{helper.id} hummed low while the night wore thin, and the toys all rested in the box within."
    )

    world.para()
    hero.meters["noisy"] += 1
    world_tale(world, hero, helper, mis, danger, fix)
    propagate(world, narrate=False)

    world.facts.update(
        hero=hero, helper=helper, mischief=mis, danger=danger, fix=fix,
        room=world.rooms[params.room],
        outcome="calm",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story that includes the word "{f["hero"].id}" and a small suspenseful mishap in a nursery.',
        f"Tell a gentle suspense story where {f['hero'].id}, the clutz, makes a tiny mistake, then {f['helper'].id} helps calm the room.",
        f"Write a moonlit bedtime rhyme with a little scare, a helpful grown-up, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    fix = f["fix"]
    room = f["room"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, the clutz, and {helper.id} in the {room.label}. "
                   f"The story follows a tiny bedtime mishap and the gentle help that follows.",
        ),
        QAItem(
            question="Why did the room feel spooky for a moment?",
            answer=f"{hero.id} made a small clumsy mistake, and that caused a bit of shadow and unease. "
                   f"The room did not become truly unsafe, but it felt hushy enough to worry about.",
        ),
        QAItem(
            question="How did the helper make things better?",
            answer=f"{helper.id} used {fix.label} to bring back a calm glow. That bright little fix made the shadows shrink and helped everyone settle down again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nightlight?",
            answer="A nightlight is a tiny lamp that gives a soft glow in the dark. It helps a room feel friendly at bedtime.",
        ),
        QAItem(
            question="What does a lullaby do?",
            answer="A lullaby is a soft song for sleepy children. It helps them relax and feel safe enough to rest.",
        ),
        QAItem(
            question="Why can a shadow feel scary to a little child?",
            answer="A shadow can look bigger or stranger when the room is very quiet. When children are sleepy, even a small dark shape can seem spooky for a moment.",
        ),
    ]


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    for room in world.rooms.values():
        meters = {k: v for k, v in room.meters.items() if v}
        if meters:
            lines.append(f"  room:{room.id} meters={meters}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
danger(noise) :- noisy(hero).
unease :- danger(noise).
shadow :- unease.
calm :- shadow.
valid(Room, Mis, Fix) :- room(Room), mischief(Mis), fix(Fix).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for mid in MISCHIEF:
        lines.append(asp.fact("mischief", mid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(room="nursery", hero="Milo", helper="Mama", mischief="toybox_tumble", danger="shadow", safe_fix="nightlight"),
    StoryParams(room="bedroom", hero="Nina", helper="Grandma", mischief="curtain_tug", danger="shadow", safe_fix="lullaby"),
    StoryParams(room="playroom", hero="Pip", helper="Papa", mischief="nightlamp_bump", danger="shadow", safe_fix="lantern"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

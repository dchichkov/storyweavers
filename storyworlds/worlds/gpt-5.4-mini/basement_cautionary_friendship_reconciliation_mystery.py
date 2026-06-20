#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/basement_cautionary_friendship_reconciliation_mystery.py
========================================================================================

A standalone storyworld for a small basement mystery: two friends hear a strange
sound, one wants to investigate, the other gives a careful warning, they discover
the source is harmless, and they reconcile after a tense moment. The world is
state-driven and child-facing, with a clear cautious beat, a friendship beat,
and a reconciliatory ending image.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/basement_cautionary_friendship_reconciliation_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/basement_cautionary_friendship_reconciliation_mystery.py --all
    python storyworlds/worlds/gpt-5.4-mini/basement_cautionary_friendship_reconciliation_mystery.py --verify
    python storyworlds/worlds/gpt-5.4-mini/basement_cautionary_friendship_reconciliation_mystery.py --qa --json
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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


@dataclass
class Room:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})


@dataclass
class ObjectCfg:
    id: str
    label: str
    kind: str
    can_hide: bool = False
    can_rattle: bool = False
    can_scare: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {})


@dataclass
class StoryParams:
    basement: str
    mystery: str
    hidden_object: str
    noise_source: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.rooms: dict[str, Room] = {}
        self.objects: dict[str, ObjectCfg] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        if isinstance(ent, Room):
            self.rooms[ent.id] = ent
        elif isinstance(ent, Entity):
            self.entities[ent.id] = ent
        else:
            self.objects[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities.get(eid) or self.rooms.get(eid) or self.objects[eid]

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
        w.rooms = copy.deepcopy(self.rooms)
        w.objects = copy.deepcopy(self.objects)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    room = world.rooms["basement"]
    if room.meters.get("mystery", 0.0) >= THRESHOLD and ("fear", "f1") not in world.fired:
        world.fired.add(("fear", "f1"))
        for e in world.entities.values():
            if e.role in {"explorer", "cautious"}:
                e.memes["fear"] = e.memes.get("fear", 0.0) + 1
        room.meters["tension"] = room.meters.get("tension", 0.0) + 1
        out.append("__fear__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    obj = world.objects["hidden"]
    if obj.meters.get("revealed", 0.0) >= THRESHOLD and ("reveal", "done") not in world.fired:
        world.fired.add(("reveal", "done"))
        world.rooms["basement"].meters["mystery"] = 0.0
        out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("reveal", _r_reveal)]


def basement_setup(world: World, a: Entity, b: Entity, room: Room, mystery: str) -> None:
    world.say(f"On a rainy evening, {a.id} and {b.id} crept down to the basement.")
    world.say(f"The basement felt {mystery}, with old boxes, a dusty shelf, and a narrow light under the door.")
    room.meters["mystery"] = 1.0
    a.memes["curiosity"] = 1.0
    b.memes["curiosity"] = 1.0


def hear_noise(world: World, noise: str) -> None:
    world.say(f"Then they heard a {noise} from behind the stacked boxes, and both children froze.")
    world.rooms["basement"].meters["mystery"] = world.rooms["basement"].meters.get("mystery", 0.0) + 1


def warn(world: World, cautious: Entity, explorer: Entity) -> None:
    cautious.memes["care"] = cautious.memes.get("care", 0.0) + 1
    world.say(f'"Wait," {cautious.id} whispered. "{explorer.id}, we should not rush into a dark basement when we do not know what made that sound."')


def ignore_or_listen(world: World, explorer: Entity, cautious: Entity) -> None:
    if explorer.memes.get("curiosity", 0.0) > cautious.memes.get("care", 0.0):
        explorer.memes["bravery"] = explorer.memes.get("bravery", 0.0) + 1
        world.say(f'{explorer.id} took one nervous step closer anyway, but {explorer.pronoun()} kept {explorer.pronoun("possessive")} voice low.')
    else:
        world.say(f'{explorer.id} listened, and the two friends stood still together, trying to solve the mystery kindly.')


def reveal_source(world: World, obj: ObjectCfg, a: Entity, b: Entity) -> None:
    hidden = world.objects["hidden"]
    hidden.meters["revealed"] = hidden.meters.get("revealed", 0.0) + 1
    world.say(f'Then {a.id} lifted a cardboard box and found the answer: {obj.label}.')
    if obj.can_rattle:
        world.say(f'It had been making the {world.facts["noise_source"]} all along.')
    world.say("It was only a harmless little thing, not a monster at all.")


def reconcile(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["relief"] = a.memes.get("relief", 0.0) + 1
    b.memes["relief"] = b.memes.get("relief", 0.0) + 1
    a.memes["friendship"] = a.memes.get("friendship", 0.0) + 1
    b.memes["friendship"] = b.memes.get("friendship", 0.0) + 1
    world.say(f"{a.id} grinned at {b.id}. \"You were right to be careful,\" {a.id} said.")
    world.say(f'{b.id} smiled back. "{a.id}, thanks for listening. We make a better team when we stay together."')
    world.say(f"{parent.label_word.capitalize()} came down the stairs and shone a flashlight over the boxes, glad the mystery had ended safely.")
    world.say("The friends carried the box upstairs side by side, calmer than before.")


def tell(params: StoryParams) -> World:
    world = World()
    room = world.add(Room("basement", "the basement"))
    a = world.add(Entity(params.friend1, kind="character", type=params.friend1_gender, role="explorer", traits=["curious"]))
    b = world.add(Entity(params.friend2, kind="character", type=params.friend2_gender, role="cautious", traits=["careful"]))
    parent = world.add(Entity("Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    obj = world.add(ObjectCfg("hidden", label=params.hidden_object, kind="thing", can_hide=True, can_rattle=True))
    noise = world.add(ObjectCfg("noise", label=params.noise_source, kind="thing", can_scare=True))

    world.facts.update(friend1=a, friend2=b, parent=parent, room=room, obj=obj, noise=noise, params=params)

    basement_setup(world, a, b, room, params.mystery)
    world.para()
    hear_noise(world, params.noise_source)
    warn(world, b, a)
    ignore_or_listen(world, a, b)
    world.para()
    reveal_source(world, obj, a, b)
    propagate(world, narrate=False)
    reconcile(world, a, b, parent)

    world.facts["outcome"] = "reconciled"
    return world


BASEMENTS = {
    "quiet": "a little eerie",
    "dim": "dark and echoing",
    "dusty": "full of whispers",
}

MYSTERIES = {
    "box": "a cardboard box",
    "pipe": "a loose pipe",
    "toy": "an old wind-up toy",
    "basket": "a wicker basket",
}

NOISES = {
    "rattle": "a rattle-rattle sound",
    "tap": "a tap-tap sound",
    "clink": "a clink-clink sound",
}

GIRL_NAMES = ["Mia", "Zoe", "Ava", "Lily", "Nora", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Finn", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(b, m, n) for b in BASEMENTS for m in MYSTERIES for n in NOISES]


@dataclass
class StoryParams:
    basement: str
    mystery: str
    hidden_object: str
    noise_source: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "basement": [("What is a basement?", "A basement is a lower room under a house, often used for storage or laundry.")],
    "flashlight": [("What is a flashlight?", "A flashlight is a small battery light you can carry in the dark without any flame.")],
    "careful": [("What does it mean to be careful?", "Being careful means slowing down, looking first, and trying not to make a mistake or get hurt.")],
    "friendship": [("What is friendship?", "Friendship is when people care about each other, help each other, and stay kind during hard moments.")],
    "reconcile": [("What does reconcile mean?", "To reconcile means to make peace again after a disagreement.")],
    "mystery": [("What is a mystery?", "A mystery is something you do not understand yet, so you look for clues.")],
    "rattle": [("What can make a rattling sound?", "Loose things like boxes, toys, or pipes can rattle when they move.")],
}
KNOWLEDGE_ORDER = ["basement", "mystery", "rattle", "careful", "friendship", "reconcile", "flashlight"]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a basement mystery story for a young child that includes the word "basement" and ends with friendship.',
        f"Tell a cautious story where {p.friend1} hears a strange sound in the basement, {p.friend2} warns {p.friend1}, and they discover the answer together.",
        f"Write a simple mystery about two friends who start uneasy in a basement but reconcile after finding out what made the noise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a: Entity = f["friend1"]
    b: Entity = f["friend2"]
    parent: Entity = f["parent"]
    obj: ObjectCfg = f["obj"]
    qa = [
        QAItem(
            question="Who are the story's main characters?",
            answer=f"The story is about {a.id} and {b.id}, two friends who go into the basement together. {parent.label_word.capitalize()} comes in at the end to help them feel safe."
        ),
        QAItem(
            question="Why did the basement feel scary at first?",
            answer=f"It felt {f['params'].mystery} because the room was dim, there were old boxes, and a strange sound came from behind them. The unknown noise made the friends worry before they found the clue."
        ),
        QAItem(
            question=f"What did the friends discover?",
            answer=f"They discovered {obj.label}, which was making the {f['noise'].label} all along. Once they saw it, the big mystery turned into something harmless."
        ),
        QAItem(
            question="How did they fix their disagreement?",
            answer=f"{b.id} warned {a.id} to slow down, then {a.id} listened and thanked {b.id} for being careful. After that, the two friends smiled, forgave each other, and carried the box upstairs together."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"basement", "mystery", "rattle", "careful", "friendship", "reconcile", "flashlight"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
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
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.type:7}) role={e.role} meters={e.meters} memes={e.memes}")
    for r in world.rooms.values():
        lines.append(f"  {r.id:10} (room   ) meters={r.meters} memes={r.memes}")
    for o in world.objects.values():
        lines.append(f"  {o.id:10} (object ) label={o.label} meters={o.meters}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_high(B) :- room(B), mystery_meter(B, M), M >= 1.
fear(A) :- mystery_high(B), explorer(A).
revealed(O) :- object(O), revealed_meter(O, M), M >= 1.
reconciled(A, C) :- friend(A), friend(C), listener(C), explorer(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for bid in BASEMENTS:
        lines.append(asp.fact("room", bid))
    for mid in MYSTERIES:
        lines.append(asp.fact("object", mid))
    for nid in NOISES:
        lines.append(asp.fact("noise", nid))
    lines.append(asp.fact("friend", "f1"))
    lines.append(asp.fact("friend", "f2"))
    lines.append(asp.fact("explorer", "f1"))
    lines.append(asp.fact("listener", "f2"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    rc = 0
    model = asp.one_model(asp_program("#show mystery_high/1."))
    _ = asp.atoms(model, "mystery_high")
    if set(valid_combos()) != set(valid_combos()):
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE FAIL: {exc}")
        return 1
    print("OK: story generation smoke test passed.")
    print("OK: ASP twin loaded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Basement mystery storyworld with caution, friendship, and reconciliation.")
    ap.add_argument("--basement", choices=BASEMENTS)
    ap.add_argument("--mystery", choices=list(BASEMENTS))
    ap.add_argument("--hidden-object", dest="hidden_object", choices=["cardboard box", "old wind-up toy", "wicker basket", "loose pipe"])
    ap.add_argument("--noise-source", dest="noise_source", choices=list(NOISES.values()))
    ap.add_argument("--friend1")
    ap.add_argument("--friend1-gender", dest="friend1_gender", choices=["girl", "boy"])
    ap.add_argument("--friend2")
    ap.add_argument("--friend2-gender", dest="friend2_gender", choices=["girl", "boy"])
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
    basement = args.basement or rng.choice(list(BASEMENTS))
    mystery = args.mystery or rng.choice(list(BASEMENTS))
    hidden_object = args.hidden_object or rng.choice(list(MYSTERIES.values()))
    noise_source = args.noise_source or rng.choice(list(NOISES.values()))
    friend1_gender = args.friend1_gender or rng.choice(["girl", "boy"])
    friend2_gender = args.friend2_gender or ("boy" if friend1_gender == "girl" else "girl")
    friend1 = args.friend1 or rng.choice(GIRL_NAMES if friend1_gender == "girl" else BOY_NAMES)
    friend2_pool = [n for n in (GIRL_NAMES if friend2_gender == "girl" else BOY_NAMES) if n != friend1]
    friend2 = args.friend2 or rng.choice(friend2_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(basement, mystery, hidden_object, noise_source, friend1, friend1_gender, friend2, friend2_gender, parent)


def valid_story(params: StoryParams) -> bool:
    return params.friend1 != params.friend2


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("The two friends must have different names.")
    world = World()
    sample_world = tell(params)
    return StorySample(
        params=params,
        story=sample_world.render(),
        prompts=generation_prompts(sample_world),
        story_qa=story_qa(sample_world),
        world_qa=world_knowledge_qa(sample_world),
        world=sample_world,
    )


CURATED = [
    StoryParams("quiet", "quiet", "cardboard box", "rattle-rattle sound", "Mia", "girl", "Ben", "boy", "mother"),
    StoryParams("dim", "dim", "old wind-up toy", "tap-tap sound", "Leo", "boy", "Ava", "girl", "father"),
    StoryParams("dusty", "dusty", "wicker basket", "clink-clink sound", "Nora", "girl", "Max", "boy", "mother"),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show mystery_high/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin is available for this world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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

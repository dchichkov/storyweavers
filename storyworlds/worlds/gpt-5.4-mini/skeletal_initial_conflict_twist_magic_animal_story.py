#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/skeletal_initial_conflict_twist_magic_animal_story.py
=====================================================================================

A standalone story world for a small animal tale with a skeletal-looking thing,
an initial conflict, a magic twist, and a gentle ending image.

This world keeps the contract shape used by the repository:
- stdlib-only script
- eager import of storyworlds/results.py
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --qa, --json, --trace, --asp, --verify, --show-asp
- Python reasonableness gate plus inline ASP twin
- state-driven story and QA derived from simulated world facts
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]



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
    animal_home: str

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
class Conflict:
    id: str
    want: str
    worry: str
    trigger: str
    solved_by: str

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
    action: str
    ending_image: str

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
class Magic:
    id: str
    name: str
    effect: str
    light: str
    safe: bool = True

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        return clone


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["fear"] >= THRESHOLD and ent.memes["trust"] >= THRESHOLD:
            sig = ("calm", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["fear"] = max(0.0, ent.memes["fear"] - 1.0)
            out.append("")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    nest = world.entities.get("nest")
    charm = world.entities.get("charm")
    if not nest or not charm:
        return out
    if nest.meters["skeletal"] < THRESHOLD or charm.meters["glow"] < THRESHOLD:
        return out
    sig = ("magic", nest.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    nest.meters["cozy"] += 1
    nest.meters["glow"] += 1
    for e in world.characters():
        e.memes["wonder"] += 1
        e.memes["fear"] = max(0.0, e.memes["fear"] - 1.0)
    out.append("")
    return out


CAUSAL_RULES = [_r_calm, _r_magic]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if s])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(conflict: Conflict, twist: Twist, magic: Magic, setting: Setting) -> bool:
    return conflict.id in {"argue", "worry"} and twist.id in {"glow", "reveal"} and magic.safe and setting.id in {"moon_den", "moss_garden", "riverbank"}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CONFLICTS:
            for t in TWISTS:
                for m in MAGICS:
                    if reasonableness_gate(CONFLICTS[c], TWISTS[t], MAGICS[m], SETTINGS[s]):
                        combos.append((s, c, t, m))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    conflict: str
    twist: str
    magic: str
    hero: str
    friend: str
    hero_gender: str
    friend_gender: str
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


def intro(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"At {setting.place}, {hero.id} and {friend.id} were playing near {setting.animal_home}. "
        f"The air felt {setting.mood}, and the little animals could hear soft rustles in the leaves."
    )


def state_conflict(world: World, hero: Entity, friend: Entity, conflict: Conflict) -> None:
    hero.memes["want"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"{hero.id} wanted to {conflict.want}, but {friend.id} worried about {conflict.worry}. "
        f"{friend.id} said, \"That might make a problem.\""
    )
    world.say(
        f"{hero.id} frowned. \"But I want to try,\" {hero.pronoun()} said, and the two friends went quiet for a moment."
    )


def use_magic(world: World, hero: Entity, friend: Entity, magic: Magic, twist: Twist) -> None:
    charm = world.get("charm")
    nest = world.get("nest")
    charm.meters["glow"] += 1
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"Then {hero.id} found {magic.name}, and the little light began to shine. "
        f"It was not a loud kind of magic; it was a gentle one, like a firefly blink."
    )
    world.say(
        f"The {twist.reveal} was surprising: {twist.action}. "
        f"The light touched the {nest.label}, and the {magic.effect} made the bones stop looking lonely."
    )
    nest.meters["skeletal"] += 1
    propagate(world, narrate=False)
    if nest.meters["cozy"] >= THRESHOLD:
        world.say(f"Slowly, the {nest.label} changed into {twist.ending_image}.")


def resolve(world: World, hero: Entity, friend: Entity, conflict: Conflict, twist: Twist) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    friend.memes["fear"] = 0.0
    world.say(
        f"{friend.id} blinked, then smiled. \"I see it now,\" {friend.id} said. "
        f"\"The magic was helping us all along.\""
    )
    world.say(
        f"{hero.id} laughed and nodded. The initial argument faded away, and the friends sat together by the warm, glowing nest."
    )
    world.say(
        f"By the end, the dark little place looked kind instead of spooky: {twist.ending_image}."
    )


SETTINGS = {
    "moon_den": Setting("moon_den", "Moon Den", "silver and quiet", "an old rabbit burrow"),
    "moss_garden": Setting("moss_garden", "Moss Garden", "soft and green", "a hollow stump"),
    "riverbank": Setting("riverbank", "River Bank", "cool and bright", "a tucked-in reed nest"),
}

CONFLICTS = {
    "argue": Conflict("argue", "pull on the old nest", "breaking the tiny bones of the nest", "initial", "listen"),
    "worry": Conflict("worry", "step closer to the strange shape", "scaring the little owl inside", "initial", "wait"),
}

TWISTS = {
    "glow": Twist("glow", "twist", "a hidden charm woke up under the feathers", "a cozy nest glowing like a small moon"),
    "reveal": Twist("reveal", "twist", "the skeletal branches were only an old frame for a new home", "a bright home wrapped in leaves and light"),
}

MAGICS = {
    "lantern_spell": Magic("lantern_spell", "a moon lantern spell", "cozy leaf-patterns appeared", "glow"),
    "firefly_song": Magic("firefly_song", "a firefly song", "warm dots of light danced in the air", "sparkle"),
}


GIRL_NAMES = ["Mina", "Luna", "Tia", "Nora", "Poppy", "Ivy"]
BOY_NAMES = ["Ollie", "Finn", "Milo", "Benji", "Arlo", "Theo"]


def tell(setting: Setting, conflict: Conflict, twist: Twist, magic: Magic,
         hero: str, friend: str, hero_gender: str, friend_gender: str) -> World:
    world = World(setting)
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    f = world.add(Entity(id=friend, kind="character", type=friend_gender, role="friend"))
    world.add(Entity(id="nest", type="thing", label="skeletal nest"))
    world.add(Entity(id="charm", type="thing", label="magic charm"))

    intro(world, h, f, setting)
    world.para()
    state_conflict(world, h, f, conflict)
    world.para()
    use_magic(world, h, f, magic, twist)
    world.para()
    resolve(world, h, f, conflict, twist)

    world.facts.update(
        hero=h, friend=f, setting=setting, conflict=conflict, twist=twist, magic=magic,
        outcome="twist", nested_glow=world.get("nest").meters["cozy"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly animal story that includes the words "skeletal" and "initial".',
        f"Tell a story about {f['hero'].id} and {f['friend'].id} where an initial disagreement turns into a magic twist.",
        f"Write a small animal tale with a spooky-looking place, a gentle magic moment, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    friend = f["friend"].id
    conflict = f["conflict"]
    twist = f["twist"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero} and {friend}, two little animals who started with an initial disagreement and then found a calmer way forward."
        ),
        QAItem(
            question=f"What did {hero} want at first?",
            answer=f"{hero} wanted to {conflict.want}. That choice made the problem feel bigger until the magic twist helped."
        ),
        QAItem(
            question="What changed the mood of the story?",
            answer=f"The magic charm did. It made the skeletal-looking place glow and turned the scary feeling into wonder."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {twist.ending_image}. The friends were no longer arguing; they were sitting together and enjoying the light."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word skeletal usually mean?",
            answer="It usually means something looks like bones or has a bone-like shape. In stories, it can make a place look spooky or very thin."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change in what is happening. It makes the story turn in a new direction."
        ),
        QAItem(
            question="Why do magic stories often feel exciting?",
            answer="Magic can change what the characters think is possible. That surprise makes the story feel exciting and a little mysterious."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
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
    lines.append(f"  fired rules: {sorted({n for n, _ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_combo(S, C, T, M) :- setting(S), conflict(C), twist(T), magic(M),
    setting_ok(S), conflict_ok(C), twist_ok(T), magic_ok(M).

setting_ok(moon_den).
setting_ok(moss_garden).
setting_ok(riverbank).

conflict_ok(argue).
conflict_ok(worry).

twist_ok(glow).
twist_ok(reveal).

magic_ok(lantern_spell).
magic_ok(firefly_song).

outcome(twist) :- safe_combo(_, _, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show safe_combo/4."))
    return sorted(set(asp.atoms(model, "safe_combo")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in ASP gate:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        rc = 1

    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke-tested normal generation.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams("moon_den", "argue", "glow", "lantern_spell", "Mina", "Ollie", "girl", "boy"),
    StoryParams("moss_garden", "worry", "reveal", "firefly_song", "Luna", "Finn", "girl", "boy"),
    StoryParams("riverbank", "argue", "reveal", "lantern_spell", "Theo", "Nora", "boy", "girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with skeletal, initial conflict, and a magic twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.conflict is None or c[1] == args.conflict)
              and (args.twist is None or c[2] == args.twist)
              and (args.magic is None or c[3] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, conflict, twist, magic = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != hero])
    return StoryParams(setting, conflict, twist, magic, hero, friend, hero_gender, friend_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CONFLICTS[params.conflict],
        TWISTS[params.twist],
        MAGICS[params.magic],
        params.hero,
        params.friend,
        params.hero_gender,
        params.friend_gender,
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
        print(asp_program("", "#show safe_combo/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} safe combos:")
        for item in combos:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero} and {p.friend}: {p.setting}, {p.conflict}, {p.twist}, {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small story world in a swimming pool fairy tale with a vision-based twist.

Premise:
A tiny princess named Mira visits a silver swimming pool that glitters like a
mirror. She wants to follow a shining fish-like light under the water, but the
pool's keeper warns her that the light is not what it seems. The turn comes when
Mira uses a looking-glass charm to see the hidden truth: the "fish" is a golden
key resting in a shell, meant to open the pool gate for everyone. The resolution
is gentle and fairy-tale bright: Mira shares the key, the gate opens, and the
pool becomes a place of joy rather than mystery.

The world model tracks:
- physical meters: splash, soaked, opened, hidden, visible
- emotional memes: wonder, worry, courage, kindness, surprise

The story is generated from stateful simulation rather than a frozen paragraph.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "mom", "woman"}
        male = {"boy", "prince", "king", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the swimming pool"
    affords: set[str] = field(default_factory=lambda: {"vision", "splash", "twist"})


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    type: str
    kind: str = "thing"


@dataclass
class StoryParams:
    setting: str
    twist: str
    name: str
    hero_type: str
    keeper_type: str
    seed: Optional[int] = None


SETTINGS = {
    "pool": Setting(place="the swimming pool"),
}

ARTIFACTS = {
    "looking_glass": Artifact(
        id="looking_glass",
        label="looking-glass charm",
        phrase="a little looking-glass charm on a ribbon",
        type="charm",
    ),
    "golden_key": Artifact(
        id="golden_key",
        label="golden key",
        phrase="a tiny golden key with a shell-shaped head",
        type="key",
    ),
    "shell": Artifact(
        id="shell",
        label="shell",
        phrase="a pearly shell",
        type="shell",
    ),
}

NAMES = ["Mira", "Lila", "Nora", "Elsa", "Iris", "Talia"]
HERO_TYPES = ["princess", "girl"]
KEEPER_TYPES = ["keeper", "queen"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for msg in apply_rules(world):
            if msg:
                changed = True
                out.append(msg)
    if narrate:
        for s in out:
            world.say(s)
    return out


def apply_rules(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    pool = world.get("pool")
    charm = world.entities.get("looking_glass")
    key = world.entities.get("golden_key")
    shell = world.entities.get("shell")

    if hero.meters.get("splash", 0) >= THRESHOLD and ("splash",) not in world.fired:
        world.fired.add(("splash",))
        hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
        out.append(f"Ripples rose around {hero.id} like silver lace.")

    if hero.memes.get("worry", 0) >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        out.append(f"The keeper's warning made the water feel very still.")

    if charm and hero.meters.get("visible", 0) >= THRESHOLD and ("see_twist",) not in world.fired:
        if key and shell and key.meters.get("hidden", 0) >= THRESHOLD:
            world.fired.add(("see_twist",))
            key.meters["hidden"] = 0
            key.meters["visible"] = 1
            shell.meters["open"] = 1
            hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
            out.append("The looking-glass charm showed that the shining fish was only a trick of light.")
            out.append("Under the shell, a golden key was waiting all along.")

    if key and key.meters.get("visible", 0) >= THRESHOLD and ("open_gate",) not in world.fired:
        world.fired.add(("open_gate",))
        pool.meters["opened"] = 1
        hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
        out.append("The gate unlocked with a sweet little click, as if the pool had been holding its breath.")
    return out


def predict_twist(world: World) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["visible"] = 1
    propagate(sim, narrate=False)
    return bool(sim.entities["golden_key"].meters.get("visible", 0))


def tell_world(hero_name: str, hero_type: str, keeper_type: str) -> World:
    world = World(SETTINGS["pool"])
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_type, label="the keeper"))
    pool = world.add(Entity(id="pool", kind="place", type="pool", label="the swimming pool"))

    charm = world.add(Entity(id="looking_glass", type="charm", label="looking-glass charm"))
    key = world.add(Entity(id="golden_key", type="key", label="golden key"))
    shell = world.add(Entity(id="shell", type="shell", label="shell"))

    key.meters["hidden"] = 1
    shell.meters["closed"] = 1
    pool.meters["opened"] = 0

    hero.memes["wonder"] = 1
    keeper.memes["worry"] = 1

    world.say(f"Once in {world.setting.place}, there lived a little {hero.type} named {hero_name}.")
    world.say(f"{hero_name} loved the water because it shone like a mirror in a fairy tale.")

    world.para()
    world.say(f"One bright morning, {hero_name} noticed a sparkle under the water and wanted to follow it.")
    world.say(f"But {keeper.label} warned, \"Little one, do not trust every shine you see.\"")
    hero.meters["splash"] = 1
    hero.memes["worry"] = 1
    hero.meters["visible"] = 0
    propagate(world)

    world.para()
    world.say(f"{hero_name} lifted the looking-glass charm and peered through it with careful vision.")
    if predict_twist(world):
        hero.meters["visible"] = 1
        propagate(world)
    else:
        raise StoryError("The twist did not resolve as expected.")

    world.para()
    world.say(f"{hero_name} smiled, because the mystery was kind, not cruel.")
    world.say(f"Together, {hero_name} and {keeper.label} opened the shell and used the golden key.")
    world.say(f"At last, {world.setting.place} stood open and bright, and everyone could come and play.")

    world.facts.update(
        hero=hero,
        keeper=keeper,
        pool=pool,
        charm=charm,
        key=key,
        shell=shell,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a short fairy tale set in a swimming pool with a magical vision twist.',
        f"Tell a gentle story about {hero.label} using a looking-glass charm to discover what the sparkle in the pool really is.",
        "Write a child-friendly tale where a hidden thing is revealed by careful vision and the ending opens into joy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    keeper = f["keeper"]
    key = f["key"]
    shell = f["shell"]
    return [
        QAItem(
            question=f"Who is the fairy-tale child in the swimming pool story?",
            answer=f"The story is about {hero.label}, a little {hero.type} who loves the water in {world.setting.place}.",
        ),
        QAItem(
            question="What did the keeper warn about?",
            answer=f"The keeper warned that the sparkle under the water should not be trusted right away, because it was hiding a deeper truth.",
        ),
        QAItem(
            question="What did the looking-glass charm reveal?",
            answer=f"It revealed that the shining fish-like sparkle was really the hidden golden key waiting inside a shell.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The pool gate opened, so {world.setting.place} became a bright place where everyone could play together.",
        ),
        QAItem(
            question="How did the hero solve the mystery?",
            answer=f"{hero.label} used careful vision with the looking-glass charm, then shared the truth with {keeper.label} and helped open the shell.",
        ),
        QAItem(
            question="Why was the twist important?",
            answer=f"The twist mattered because it turned a confusing shimmer into a useful gift: the golden key that opened the pool gate.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is vision?",
            answer="Vision is the sense that lets someone see shapes, colors, light, and movement with their eyes.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what the listener thought was happening.",
        ),
        QAItem(
            question="What is a swimming pool?",
            answer="A swimming pool is a basin of water where people can splash, swim, and play safely.",
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
visible_twist(H) :- hero(H), sees(H), hidden_key(k).
resolution :- visible_twist(_), opened_gate.

story_ok :- resolution.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("keeper", "keeper"),
        asp.fact("hidden_key", "k"),
        asp.fact("opened_gate"),
        asp.fact("sees", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(a.name == "story_ok" for a in model)
    if ok:
        print("OK: ASP gate supports the twist story.")
        return 0
    print("MISMATCH: ASP gate did not derive story_ok.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale swimming pool story world with a vision twist.")
    ap.add_argument("--setting", choices=SETTINGS.keys(), default="pool")
    ap.add_argument("--twist", choices=["vision"], default="vision")
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES, default="princess")
    ap.add_argument("--keeper-type", choices=KEEPER_TYPES, default="keeper")
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
    if args.twist != "vision":
        raise StoryError("This world only supports the vision twist.")
    return StoryParams(
        setting=args.setting,
        twist=args.twist,
        name=args.name or rng.choice(NAMES),
        hero_type=args.hero_type,
        keeper_type=args.keeper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params.name, params.hero_type, params.keeper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show visible_twist/1. #show resolution/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(
            setting="pool",
            twist="vision",
            name="Mira",
            hero_type="princess",
            keeper_type="keeper",
            seed=base_seed,
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

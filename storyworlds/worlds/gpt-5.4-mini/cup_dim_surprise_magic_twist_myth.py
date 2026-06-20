#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cup_dim_surprise_magic_twist_myth.py
====================================================================

A small, standalone story world inspired by a mythic seed: a dim cup in a shrine,
a surprise, a bit of magic, and a twist that changes what the characters believe
the cup is for.

The world model is intentionally simple:
- one child or young keeper
- one elder or guide
- one sacred cup that is dim or bright
- one surprising magical event
- one twist that reveals the cup's true use
- a final myth-like ending image proving the change

The prose is generated from world state, not from a frozen template swap.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Shrine:
    name: str
    place: str
    dark: str
    sacred: str
    hush: str


@dataclass
class Cup:
    id: str
    label: str
    dimness: int
    made_of: str
    meaning: str
    can_hold_light: bool = True
    can_reflect: bool = True


@dataclass
class Magic:
    id: str
    sign: str
    gift: str
    glow: int
    surprise: str
    twist: str


@dataclass
class World:
    shrine: Shrine
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.shrine)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SHRINES = {
    "stone_hall": Shrine("stone hall", "beside the old river", "the room was dim at dusk", "the cup was kept on a stone altar", "everyone had to speak softly"),
    "moon_temple": Shrine("moon temple", "under the silver hill", "moonlight slipped through high cracks", "the cup waited in a carved niche", "the air felt still and hushed"),
    "cave_shrine": Shrine("cave shrine", "deep in the cliff", "the cave was dim and cool", "the cup rested on a round shelf", "the walls held every whisper"),
}

CUPS = {
    "cup_dim": Cup("cup_dim", "the cup-dim cup", 1, "silver", "to hold the first light of dawn"),
    "sun_cup": Cup("sun_cup", "the sun cup", 2, "gold", "to keep a brave ember alive"),
    "river_cup": Cup("river_cup", "the river cup", 1, "bronze", "to gather moonlit water"),
}

MAGICS = {
    "surprise": Magic("surprise", "a lantern of light appeared", "a bright path in the dark", 2, "the shadows opened with a gasp", "the cup was not meant to be empty"),
    "magic": Magic("magic", "warm light rose from the cup", "a hidden glow under the rim", 3, "the cup answered the moon", "light can sleep before it wakes"),
    "twist": Magic("twist", "the cup rang like a little bell", "a promise of dawn", 2, "what looked dim was only waiting", "the cup was a vessel, not a treasure"),
}

GIVERS = ["Ari", "Mina", "Ivo", "Nia", "Levi", "Sera"]
GUIDES = ["elder", "priestess", "guardian", "grandmother", "keeper"]

TOPICS = {
    "cup-dim": [
        ("What does dim mean?",
         "Dim means not very bright. A dim thing gives only a little light, like a candle far away or a lamp turned low."),
        ("What is a cup?",
         "A cup is a small container people use to hold liquid. In a story, a cup can also be special or sacred."),
    ],
    "magic": [
        ("What is magic in a story?",
         "Magic in a story is something surprising and impossible in real life, like light appearing where no lamp was before."),
    ],
    "surprise": [
        ("Why can a surprise change a story?",
         "A surprise can change what the characters think is happening. It can turn worry into wonder or reveal a new truth."),
    ],
    "twist": [
        ("What is a twist in a story?",
         "A twist is a sudden turn that changes how you understand the story. It often reveals that something was not what it seemed."),
    ],
}
TOPIC_ORDER = ["cup-dim", "surprise", "magic", "twist"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic cup-dim surprise magic twist story world.")
    ap.add_argument("--shrine", choices=SHRINES)
    ap.add_argument("--cup", choices=CUPS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=GUIDES)
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


@dataclass
class StoryParams:
    shrine: str
    cup: str
    magic: str
    name: str
    guide: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, m) for s in SHRINES for c in CUPS for m in MAGICS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.shrine is None or c[0] == args.shrine)
              and (args.cup is None or c[1] == args.cup)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    shrine, cup, magic = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIVERS)
    guide = args.guide or rng.choice(GUIDES)
    return StoryParams(shrine, cup, magic, name, guide)


def _act_intro(world: World, hero: Entity, guide: Entity, cup: Cup) -> None:
    world.say(
        f"In the {world.shrine.name}, {hero.id} kept watch beside {guide.label_word}. "
        f"{world.shrine.hush.capitalize()}, and {cup.label} sat under the shadow of the altar."
    )
    hero.memes["wonder"] = 1
    cup_ent = world.get("cup")
    cup_ent.meters["dimness"] = float(cup.dimness)
    world.say(
        f"{hero.id} looked at {cup.label} and saw how dim it was, as if the day had not yet remembered it."
    )


def _act_surprise(world: World, hero: Entity, cup_ent: Entity, magic: Magic) -> None:
    hero.memes["startle"] = hero.memes.get("startle", 0) + 1
    cup_ent.meters["surprise"] = 1
    world.say(
        f"Then came a surprise: {magic.surprise}. {hero.id} stepped back, then leaned close again."
    )


def _act_magic(world: World, hero: Entity, cup_ent: Entity, magic: Magic) -> None:
    cup_ent.meters["glow"] += magic.glow
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"Magic answered the hush. {magic.gift.capitalize()} rose from {cup_ent.label}, and the dim cup began to glow."
    )


def _act_twist(world: World, hero: Entity, guide: Entity, cup_ent: Entity, cup: Cup, magic: Magic) -> None:
    cup_ent.meters["meaning"] = 1
    hero.memes["understanding"] = 1
    world.say(
        f"Then the twist arrived: {magic.twist.capitalize()}. {guide.id} smiled and said the cup had never been a prize to keep."
    )
    world.say(
        f"It was a vessel for dawn, meant to share light with the shrine and the river path beyond it."
    )
    world.say(
        f"{hero.id} set {cup.label} where the first light could find it, and the little glow grew calm and steady."
    )


def tell(shrine: Shrine, cup: Cup, magic: Magic, name: str = "Nia", guide_name: str = "elder") -> World:
    world = World(shrine)
    hero = world.add(Entity(id=name, kind="character", type="girl", role="keeper"))
    guide = world.add(Entity(id=guide_name, kind="character", type="priestess", role="guide", label=guide_name))
    cup_ent = world.add(Entity(id="cup", type="thing", label=cup.label))
    world.facts.update(hero=hero, guide=guide, cup=cup, magic=magic, shrine=shrine)

    _act_intro(world, hero, guide, cup)
    world.para()
    _act_surprise(world, hero, cup_ent, magic)
    _act_magic(world, hero, cup_ent, magic)
    world.para()
    _act_twist(world, hero, guide, cup_ent, cup, magic)

    world.facts["ended_bright"] = cup_ent.meters.get("glow", 0) >= THRESHOLD
    world.facts["understood"] = hero.memes.get("understanding", 0) >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cup = f["cup"]
    magic = f["magic"]
    shrine = f["shrine"]
    return [
        f'Write a myth-like story for a young child that includes the word "cup-dim" and a surprise in the {shrine.name}.',
        f"Tell a short myth where {f['hero'].id} finds {cup.label}, then magic and a twist reveal what the cup is really for.",
        f'Write a gentle magical tale with the words "surprise", "magic", and "twist" about a dim cup in a sacred place.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    cup = f["cup"]
    magic = f["magic"]
    qa = [
        QAItem(
            question="What did the child notice first?",
            answer=f"{hero.id} noticed that {cup.label} was dim and quiet in the shrine. That dimness made the later magic feel even more surprising."
        ),
        QAItem(
            question="What happened after the surprise?",
            answer=f"A surprise opened the moment, and then magic rose from the cup. The glow showed that the cup was changing from dim to bright."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {guide.id} said the cup was never just treasure. It was a vessel for dawn, so the light was meant to be shared."
        ),
    ]
    if world.facts.get("ended_bright"):
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} placing {cup.label} where first light could reach it. The cup stayed bright and calm, like a small star keeping watch."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"cup-dim", "surprise", "magic", "twist"}
    out: list[QAItem] = []
    for tag in TOPIC_ORDER:
        if tag in tags:
            for q, a in TOPICS[tag]:
                out.append(QAItem(q, a))
    return out


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
    lines.append("== (3) World knowledge ==")
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
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for s in SHRINES:
        lines.append(asp.fact("shrine", s))
    for c, cup in CUPS.items():
        lines.append(asp.fact("cup", c))
        lines.append(asp.fact("dimness", c, cup.dimness))
    for m, magic in MAGICS.items():
        lines.append(asp.fact("magic", m))
        lines.append(asp.fact("glow", m, magic.glow))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, M) :- shrine(S), cup(C), magic(M).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import os
    import subprocess
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combos.")
    # smoke test normal generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story.strip()
        print("OK: generate() smoke test produced a story.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


CURATED = [
    StoryParams("moon_temple", "cup_dim", "surprise", "Nia", "keeper"),
    StoryParams("stone_hall", "sun_cup", "magic", "Ari", "elder"),
    StoryParams("cave_shrine", "river_cup", "twist", "Mina", "guardian"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SHRINES[params.shrine], CUPS[params.cup], MAGICS[params.magic], params.name, params.guide)
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
    return "(No story: this world has no invalid combinations; choose a supported shrine, cup, and magic.)"


def resolve_one_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{s} {c} {m}" for s, c, m in asp_valid_combos()))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.cup} in {p.shrine} ({p.magic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

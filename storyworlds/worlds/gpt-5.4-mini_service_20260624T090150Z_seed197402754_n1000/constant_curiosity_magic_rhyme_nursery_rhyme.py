#!/usr/bin/env python3
"""
constant_curiosity_magic_rhyme_nursery_rhyme.py
================================================

A small nursery-rhyme story world about a curious child, a bit of magic,
and a rhyme that helps things stay constant and calm.

Seed story idea:
---
A curious child hears a tiny magic rhyme that makes a lantern glow.
The glow is lovely, but it wavers whenever the child gets too excited.
The child learns a constant little rhyme to keep the magic steady.
In the end, the child shares the rhyme and the lantern shines all night.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    name: str
    effect: str
    rhyme: str
    constant_line: str
    glow_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    care: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        other = World(self.setting)
        other.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


THRESHOLD = 1.0


SETTINGS = {
    "nursery": Setting(place="the nursery", indoors=True, affords={"rhyme", "magic"}),
    "playroom": Setting(place="the playroom", indoors=True, affords={"rhyme", "magic"}),
    "bedroom": Setting(place="the bedroom", indoors=True, affords={"rhyme", "magic"}),
}

CHARMS = {
    "lantern": Charm(
        id="lantern",
        name="little lantern",
        effect="glow",
        rhyme="Glow, glow, little light, sing with me and stay all night",
        constant_line="Keep your glow so steady and bright, constant as a candlelight",
        glow_kind="glimmer",
        tags={"magic", "light", "rhyme"},
    ),
    "music_box": Charm(
        id="music_box",
        name="tiny music box",
        effect="sing",
        rhyme="Tinkle, tinkle, tune so sweet, tap the floor with tiny feet",
        constant_line="Keep your tune so gentle and true, constant as the morning dew",
        glow_kind="note",
        tags={"magic", "music", "rhyme"},
    ),
}

PRIZES = {
    "bottle": Prize(
        id="bottle",
        label="bottle",
        phrase="a glass bottle of moon-beam bubbles",
        type="bottle",
        care="hold it carefully",
    ),
    "blanket": Prize(
        id="blanket",
        label="blanket",
        phrase="a soft blue blanket",
        type="blanket",
        care="keep it tucked and neat",
    ),
}

NAMES = ["Mia", "Nina", "Lulu", "Toby", "Ben", "Pip", "Ada", "Ivy"]
TRAITS = ["curious", "bright-eyed", "cheery", "gentle", "spry"]


@dataclass
class StoryParams:
    place: str
    charm: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="nursery", charm="lantern", prize="bottle", name="Mia", gender="girl", trait="curious"),
    StoryParams(place="playroom", charm="music_box", prize="blanket", name="Toby", gender="boy", trait="bright-eyed"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about curiosity, magic, rhyme, and constant steadiness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def prize_at_risk(charm: Charm, prize: Prize) -> bool:
    return charm.id == "lantern" and prize.id == "bottle" or charm.id == "music_box" and prize.id == "blanket"


def select_fix(charm: Charm, prize: Prize) -> bool:
    return prize_at_risk(charm, prize)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for ch in CHARMS:
            for pr in PRIZES:
                if select_fix(CHARMS[ch], PRIZES[pr]):
                    out.append((place, ch, pr))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.charm and args.prize:
        ch, pr = CHARMS[args.charm], PRIZES[args.prize]
        if not prize_at_risk(ch, pr) or not select_fix(ch, pr):
            raise StoryError("No story: that charm and prize do not make a believable nursery-rhyme problem and fix.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.charm is None or c[1] == args.charm)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches the chosen options.")
    place, charm, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, charm=charm, prize=prize, name=name, gender=gender, trait=trait)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    prize = world.add(Entity(
        id="prize",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
    ))
    charm = world.add(Entity(
        id="charm",
        type="thing",
        label=CHARMS[params.charm].name,
        phrase=CHARMS[params.charm].name,
        owner=hero.id,
    ))

    hero.memes["curiosity"] = 1.0
    hero.memes["delight"] = 1.0
    prize.worn_by = hero.id
    charm.worn_by = hero.id

    world.say(f"{hero.id} was a {params.trait} little {params.gender} who lived in {setting.place}.")
    world.say(f"{hero.id} loved a {CHARMS[params.charm].name} and a {PRIZES[params.prize].phrase}.")
    world.say(f"One day, {hero.id} found a {CHARMS[params.charm].name} with a tiny rhyme inside.")
    world.para()
    world.say(f"{hero.id} sang, “{CHARMS[params.charm].rhyme}.”")
    world.say(f"The {CHARMS[params.charm].name} began to {CHARMS[params.charm].effect}, and the room felt merry and bright.")
    world.say(f"But when {hero.id} got too wiggly, the magic wavered and the light grew thin.")
    hero.memes["worry"] = 1.0
    world.para()
    world.say(f"{hero.id} held still and tried again.")
    world.say(f"This time, {hero.id} sang, “{CHARMS[params.charm].constant_line}.”")
    hero.memes["calm"] = 1.0
    hero.memes["curiosity"] += 1.0
    world.say(f"The magic listened. It stayed constant, soft, and steady, like a tiny star that knew its way home.")
    world.say(f"{hero.id} smiled, and the {PRIZES[params.prize].label} stayed safe and snug.")
    world.say(f"At the end, {hero.id} shared the rhyme with the whole room, and the little light shone all night long.")

    world.facts.update(hero=hero, prize=prize, charm=charm, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    params = f["params"]
    return [
        f'Write a nursery-rhyme story about a curious child named {hero.id} and a magic {params.charm}.',
        f'Tell a gentle story where "{params.charm}" and the word "constant" help a child keep a magic glow steady.',
        f'Write a short bedtime story with curiosity, magic, and rhyme in which {hero.id} learns a steady little song.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    params = f["params"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {params.trait} little {hero.type} who loves curiosity, magic, and rhyme.",
        ),
        QAItem(
            question=f"What did {hero.id} sing to make the magic stay steady?",
            answer=f"{hero.id} sang the constant rhyme: “{CHARMS[params.charm].constant_line}.”",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the magic stayed constant, the room was calm, and the little {CHARMS[params.charm].name} shone all night.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    charm = f["charm"]
    out = [
        QAItem(question="What does curiosity mean?", answer="Curiosity means wanting to look, learn, and ask questions about new things."),
        QAItem(question="What is a rhyme?", answer="A rhyme is a little pattern of words that sound alike at the end, which makes them fun to say and sing."),
        QAItem(question="What does constant mean?", answer="Constant means steady and not changing much, like something that keeps the same way for a while."),
    ]
    if charm.id == "lantern":
        out.append(QAItem(question="What does a lantern do?", answer="A lantern gives off light so a room or path is easier to see in the dark."))
    if charm.id == "music_box":
        out.append(QAItem(question="What does a music box do?", answer="A music box makes a small tune when it is wound up or opened carefully."))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(C, P) :- charm(C), prize(P), compatible(C, P).
fix(C, P) :- risk(C, P).
valid(Place, C, P) :- setting(Place), charm(C), prize(P), fix(C, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for c in CHARMS:
        for p in PRIZES:
            if select_fix(CHARMS[c], PRIZES[p]):
                lines.append(asp.fact("compatible", c, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(f"{len(model)} shown atoms")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

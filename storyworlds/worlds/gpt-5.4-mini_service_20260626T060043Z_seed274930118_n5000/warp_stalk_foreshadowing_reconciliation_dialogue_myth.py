#!/usr/bin/env python3
"""
A mythic story world about weaving, omen, and reconciliation.

Seed image:
A young weaver in a village keeps finding that the loom's warp threads and the reed stalks
do not agree. An old river-spirit foretells a snag, the child argues with a proud elder,
and in the end they mend the cloth together.

The world is intentionally tiny and constraint-checked:
- physical state: warp threads can be taut, frayed, or aligned; stalks can bend or split
- emotional state: doubt, pride, fear, hope, and peace
- a foreshadowed problem must arise before the reconciliation can matter
- dialogue is part of the causality, not just decoration
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"taut": 0.0, "frayed": 0.0, "aligned": 0.0, "mended": 0.0}
        if not self.memes:
            self.memes = {"doubt": 0.0, "pride": 0.0, "fear": 0.0, "hope": 0.0, "peace": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    mood: str
    omen: str


@dataclass
class StoryParams:
    setting: str
    hero: str
    elder: str
    spirit: str
    seed: Optional[int] = None


SETTINGS = {
    "river": Setting(name="the riverbank", mood="silver and quiet", omen="the water kept looping around the stones"),
    "hill": Setting(name="the hill shrine", mood="windy and bright", omen="the grass bowed before the morning wind"),
    "temple": Setting(name="the old temple court", mood="still and shadowed", omen="the bells gave one soft note and then hushed"),
}

HEROES = [
    ("Nia", "girl", "young weaver"),
    ("Tala", "girl", "young weaver"),
    ("Ivo", "boy", "young weaver"),
    ("Soren", "boy", "young weaver"),
]

ELDERS = [
    ("Grandmother", "woman", "eldress"),
    ("Uncle", "man", "eldest keeper"),
    ("Aunt", "woman", "story-keeper"),
]

SPIRITS = [
    ("Mira", "woman", "river-spirit"),
    ("Ash", "man", "loom-spirit"),
    ("Aster", "thing", "wind-spirit"),
]

TRAITS = ["bold", "quiet", "curious", "stubborn", "gentle"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def foreshadow(world: World, hero: Entity, elder: Entity, spirit: Entity) -> None:
    hero.memes["doubt"] += 1
    world.say(
        f"At {world.setting.name}, {world.setting.omen}. "
        f"{spirit.label} watched the loom and said, "
        f"\"When the warp trembles, the cloth remembers.\""
    )
    world.say(
        f"{hero.id} listened, but {hero.pronoun('possessive')} hands stayed on the threads, "
        f"because {hero.pronoun()} wanted to finish the pattern before dusk."
    )
    elder.memes["pride"] += 1
    world.facts["foreshadowed"] = True


def dialogue(world: World, hero: Entity, elder: Entity, spirit: Entity) -> None:
    hero.memes["fear"] += 1
    elder.memes["pride"] += 1
    world.say(
        f'"Do not pull the warp so hard," said {elder.id}. '
        f'"The stalk reed will bite the thread."'
    )
    world.say(
        f'"But the pattern is almost whole," said {hero.id}. '
        f'"If I stop now, the cloth will never sing."'
    )
    world.say(
        f"{spirit.label} answered softly, "
        f"\"A song can pause and still remain a song.\""
    )
    world.facts["dialogue"] = True


def fray(world: World, hero: Entity, stalk: Entity, warp: Entity) -> None:
    if "fray" in world.fired:
        return
    world.fired.add("fray")
    warp.meters["taut"] += 1
    warp.meters["frayed"] += 1
    stalk.meters["split"] += 1
    hero.memes["doubt"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"Still, the {warp.label} grew too taut, and one {stalk.label} split with a dry little snap."
    )
    world.say(
        f"{hero.id} stared at the broken place and felt the whole design wobble."
    )
    world.facts["broken"] = True


def reconcile(world: World, hero: Entity, elder: Entity, spirit: Entity, warp: Entity, stalk: Entity) -> None:
    if "reconcile" in world.fired:
        return
    world.fired.add("reconcile")
    hero.memes["hope"] += 1
    elder.memes["peace"] += 1
    hero.memes["doubt"] = max(0.0, hero.memes["doubt"] - 1)
    elder.memes["pride"] = max(0.0, elder.memes["pride"] - 1)
    warp.meters["aligned"] += 1
    warp.meters["taut"] = max(0.0, warp.meters["taut"] - 1)
    stalk.meters["mended"] += 1
    world.say(
        f"{hero.id} lowered {hero.pronoun('possessive')} hands and said, "
        f"\"I thought strength meant pulling harder. I was wrong.\""
    )
    world.say(
        f"{elder.id} touched the warped edge and answered, "
        f"\"Then we will mend it together.\""
    )
    world.say(
        f"{spirit.label} smiled like rain on stone, and the three of them lifted the thread again, "
        f"this time easing it into place."
    )
    world.say(
        f"The broken stalk was set back, the warp came straight, and the cloth began to hold its shape."
    )
    hero.memes["peace"] += 1
    elder.memes["peace"] += 1
    world.facts["reconciled"] = True


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero_name, hero_type, hero_role = next(x for x in HEROES if x[0] == params.hero)
    elder_name, elder_type, elder_role = next(x for x in ELDERS if x[0] == params.elder)
    spirit_name, spirit_type, spirit_role = next(x for x in SPIRITS if x[0] == params.spirit)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_role))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, label=elder_role))
    spirit = world.add(Entity(id=spirit_name, kind="character" if spirit_type != "thing" else "thing", type=spirit_type, label=spirit_role))

    warp = world.add(Entity(id="warp", type="warp", label="warp thread", plural=True))
    stalk = world.add(Entity(id="stalk", type="stalk", label="reed stalk"))

    world.say(
        f"{hero.id} was a {TRAITS[(len(hero.id) + len(elder.id)) % len(TRAITS)]} {hero_role} at {world.setting.name}."
    )
    world.say(
        f"{hero.id} loved the loom, the warp thread, and the patient work of making one thing become another."
    )

    world.para()
    foreshadow(world, hero, elder, spirit)
    dialogue(world, hero, elder, spirit)

    world.para()
    fray(world, hero, stalk, warp)
    reconcile(world, hero, elder, spirit, warp, stalk)

    world.facts.update(
        hero=hero,
        elder=elder,
        spirit=spirit,
        warp=warp,
        stalk=stalk,
        setting=setting,
    )
    return world


def qa_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    return [
        f"Write a short myth about {hero.id} weaving at {world.setting.name}, where an omen comes true and the family mends the work together.",
        f"Tell a child-friendly legend that uses the words warp and stalk and includes a warning, an argument, and a peaceful ending.",
        f"Write a tiny myth in which {hero.id} listens to {elder.id} and learns that fixing can be gentler than forcing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    spirit: Entity = f["spirit"]
    warp: Entity = f["warp"]
    stalk: Entity = f["stalk"]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {hero.id}, a {hero.label} who learns to weave with care at {world.setting.name}.",
        ),
        QAItem(
            question=f"What warning did {spirit.id} give?",
            answer=f"{spirit.label.capitalize()} warned that when the warp trembles, the cloth remembers, which meant the threads needed gentler hands.",
        ),
        QAItem(
            question=f"What went wrong with the weaving?",
            answer=f"The warp was pulled too taut, a reed stalk split, and the cloth began to wobble instead of holding its shape.",
        ),
        QAItem(
            question=f"How did {hero.id} and {elder.id} fix it?",
            answer=f"{hero.id} admitted the mistake, {elder.id} agreed to help, and together they eased the warp back into place and mended the broken stalk.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the cloth holding its shape again, and with {hero.id} feeling peace instead of worry.",
        ),
    ]


KNOWLEDGE = {
    "warp": [(
        "What is a warp in weaving?",
        "The warp is the set of threads stretched on a loom. Weft threads are woven across them to make cloth.",
    )],
    "stalk": [(
        "What is a stalk?",
        "A stalk is a long, thin stem of a plant like grass, grain, or reeds.",
    )],
    "myth": [(
        "What is a myth?",
        "A myth is an old story that explains a world, a custom, or a mystery using gods, spirits, or heroes.",
    )],
    "river": [(
        "Why do people tell stories about rivers?",
        "People tell stories about rivers because rivers give water, carry boats, and can seem powerful and magical.",
    )],
}


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["myth"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["warp"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["stalk"])
    if world.setting.name == "the riverbank":
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["river"])
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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryOptions:
    setting: str
    hero: str
    elder: str
    spirit: str
    seed: Optional[int] = None


CURATED = [
    StoryOptions(setting="river", hero="Nia", elder="Grandmother", spirit="Mira"),
    StoryOptions(setting="hill", hero="Ivo", elder="Uncle", spirit="Aster"),
    StoryOptions(setting="temple", hero="Tala", elder="Aunt", spirit="Ash"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mythic story world about warp, stalk, omen, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--hero", choices=[n for n, _, _ in HEROES])
    ap.add_argument("--elder", choices=[n for n, _, _ in ELDERS])
    ap.add_argument("--spirit", choices=[n for n, _, _ in SPIRITS])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryOptions:
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    hero = args.hero or rng.choice([n for n, _, _ in HEROES])
    elder = args.elder or rng.choice([n for n, _, _ in ELDERS])
    spirit = args.spirit or rng.choice([n for n, _, _ in SPIRITS])
    return StoryOptions(setting=setting, hero=hero, elder=elder, spirit=spirit)


def generate(params: StoryOptions) -> StorySample:
    world = tell(StoryParams(setting=params.setting, hero=params.hero, elder=params.elder, spirit=params.spirit, seed=params.seed))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=qa_prompts(world),
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


ASP_RULES = r"""
setting(river; hill; temple).
hero(nia; tala; ivo; soren).
elder(grandmother; uncle; aunt).
spirit(mira; ash; aster).

foreshadowed(S) :- setting(S).
dialogue(S) :- setting(S).
broken(S) :- setting(S).
reconciled(S) :- setting(S).

valid_story(S,H,E,P) :- setting(S), hero(H), elder(E), spirit(P),
                         foreshadowed(S), dialogue(S), broken(S), reconciled(S).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h, _, _ in HEROES:
        lines.append(asp.fact("hero", h))
    for e, _, _ in ELDERS:
        lines.append(asp.fact("elder", e))
    for p, _, _ in SPIRITS:
        lines.append(asp.fact("spirit", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(s.setting, h, e, p) for s in SETTINGS for h, _, _ in HEROES for e, _, _ in ELDERS for p, _, _ in SPIRITS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible story combos:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryOptions(**p.__dict__)) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

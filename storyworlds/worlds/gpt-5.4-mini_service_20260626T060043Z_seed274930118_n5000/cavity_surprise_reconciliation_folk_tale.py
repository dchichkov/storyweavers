#!/usr/bin/env python3
"""
storyworlds/worlds/cavity_surprise_reconciliation_folk_tale.py
==============================================================

A small folk-tale storyworld about a sudden cavity, a surprising discovery,
and a gentle reconciliation.

Premise:
- A child or small folk-tale creature loves sweet treats.
- A hidden cavity causes an unexpected hurt.
- A helper reveals the cause with surprise.
- The story resolves with care, apology, and reconciliation.

The world is modeled as a little simulation with physical meters and emotional
memes, plus an inline ASP twin for the reasonableness gate.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "witch"}
        male = {"boy", "man", "father", "grandfather", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    features: set[str] = field(default_factory=set)


@dataclass
class Sweet:
    id: str
    label: str
    phrase: str
    sugar: str
    theme: str = "sweet"


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    remedy: str
    theme: str = "care"


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    sweet: str
    comfort: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy

        other = World(self.setting)
        other.entities = _copy.deepcopy(self.entities)
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


SETTINGS = {
    "woodland": Setting(place="the woodlands", features={"whispering trees", "old path"}),
    "village": Setting(place="the village lane", features={"baker", "well"}),
    "cottage": Setting(place="the cottage hearth", features={"warm stove", "shelf of jars"}),
}

SWEETS = {
    "honeycake": Sweet("honeycake", "honey cake", "a sticky honey cake", "sticky"),
    "berrytart": Sweet("berrytart", "berry tart", "a bright berry tart", "sugary"),
    "treaclebun": Sweet("treaclebun", "treacle bun", "a dark treacle bun", "sweet"),
}

COMFORTS = {
    "rinse": Comfort("rinse", "warm rinse", "a warm salt rinse", "soothes"),
    "cloth": Comfort("cloth", "soft cloth", "a soft cloth wrap", "covers"),
    "spark": Comfort("sparkling water", "sparkling water", "a sip of sparkling water", "cleans"),
}

HEROES = [
    ("Mina", "girl"),
    ("Owen", "boy"),
    ("Nell", "girl"),
    ("Bram", "boy"),
    ("Elsa", "girl"),
]

HELPERS = [
    ("grandmother", "grandmother"),
    ("carpenter", "man"),
    ("herbalist", "woman"),
    ("miller", "man"),
    ("midwife", "woman"),
]


def can_surprise(world: World, sweet: Sweet) -> bool:
    return sweet.id in {"honeycake", "berrytart", "treaclebun"}


def can_reconcile(world: World, sweet: Sweet, comfort: Comfort) -> bool:
    return sweet.theme == "sweet" and comfort.theme == "care"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for feat in sorted(s.features):
            lines.append(asp.fact("feature", pid, feat))
    for sid, s in SWEETS.items():
        lines.append(asp.fact("sweet", sid))
        lines.append(asp.fact("sweet_theme", sid, s.theme))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        lines.append(asp.fact("comfort_theme", cid, c.theme))
    return "\n".join(lines)


ASP_RULES = r"""
surprise(S) :- sweet(S), sweet_theme(S, sweet).
reconcile(S, C) :- sweet(S), comfort(C), sweet_theme(S, sweet), comfort_theme(C, care).
valid(P, S, C) :- place(P), surprise(S), reconcile(S, C).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for sweet in SWEETS.values():
            for comfort in COMFORTS.values():
                if can_surprise(World(SETTINGS[place]), sweet) and can_reconcile(World(SETTINGS[place]), sweet, comfort):
                    out.append((place, sweet.id, comfort.id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about a cavity, surprise, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sweet", choices=SWEETS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=sorted({t for _, t in HEROES}))
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=sorted({t for _, t in HELPERS}))
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


def explain_rejection(sweet: Sweet, comfort: Comfort) -> str:
    return f"(No story: {sweet.label} and {comfort.label} do not make a sensible surprise-and-reconciliation pair.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    sweet = SWEETS[args.sweet] if args.sweet else rng.choice(list(SWEETS.values()))
    comfort = COMFORTS[args.comfort] if args.comfort else rng.choice(list(COMFORTS.values()))
    place = args.place or rng.choice(list(SETTINGS))
    if not (can_surprise(World(SETTINGS[place]), sweet) and can_reconcile(World(SETTINGS[place]), sweet, comfort)):
        raise StoryError(explain_rejection(sweet, comfort))
    hero_name, hero_type = (args.name, args.hero_type) if args.name and args.hero_type else rng.choice(HEROES)
    if args.name and not args.hero_type:
        hero_type = rng.choice(["girl", "boy"])
    elif args.hero_type and not args.name:
        hero_name = rng.choice([n for n, t in HEROES if t == args.hero_type])
    helper = args.helper or rng.choice([h for h, _ in HELPERS])
    helper_type = args.helper_type or dict(HELPERS).get(helper, rng.choice([t for _, t in HELPERS]))
    return StoryParams(place=place, hero=hero_name, hero_type=hero_type, helper=helper, helper_type=helper_type,
                       sweet=sweet.id, comfort=comfort.id)


def _setup(world: World, p: StoryParams) -> tuple[Entity, Entity, Entity, Entity]:
    hero = world.add(Entity(id=p.hero, kind="character", type=p.hero_type, label=p.hero, role="hero",
                            meters={"pain": 0.0, "courage": 0.0, "sweetness": 0.0}, memes={"worry": 0.0, "joy": 0.0, "surprise": 0.0, "peace": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type=p.helper_type, label=p.helper, role="helper",
                              meters={"skill": 1.0}, memes={"care": 1.0, "surprise": 0.0, "peace": 0.0}))
    sweet = world.add(Entity(id=p.sweet, kind="thing", type="sweet", label=SWEETS[p.sweet].label, phrase=SWEETS[p.sweet].phrase,
                             role="treat", owner=hero.id, meters={"sugar": 1.0}, memes={"promise": 1.0}))
    comfort = world.add(Entity(id=p.comfort, kind="thing", type="comfort", label=COMFORTS[p.comfort].label, phrase=COMFORTS[p.comfort].phrase,
                               role="remedy", meters={"gentleness": 1.0}))
    return hero, helper, sweet, comfort


def _narrate_surprise(world: World, hero: Entity, helper: Entity, sweet: Entity) -> None:
    hero.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    world.say(f"In {world.setting.place}, {hero.id} bit into {sweet.phrase} and gave a little gasp.")
    world.say(f"The old helper looked closely and said, 'Ah, a tiny cavity has been hiding there all along.'")
    world.say(f"That was a surprise to {hero.id}, and even the birds on the hedge seemed to listen.")


def _narrate_turn(world: World, hero: Entity, helper: Entity, sweet: Entity) -> None:
    hero.meters["pain"] += 1
    hero.memes["worry"] += 1
    world.say(f"{hero.id}'s tooth ached like a pebble in a shoe, and {hero.pronoun('possessive')} heart grew small.")
    world.say(f"{helper.label.capitalize()} did not scold {hero.id}; instead, {helper.pronoun()} spoke softly about sweet crumbs and careful brushing.")


def _narrate_reconciliation(world: World, hero: Entity, helper: Entity, comfort: Entity) -> None:
    hero.memes["peace"] += 1
    helper.memes["peace"] += 1
    hero.memes["worry"] = 0.0
    hero.meters["pain"] = 0.0
    world.say(f"Together they chose {comfort.phrase}, and the ache began to fade.")
    world.say(f"{hero.id} apologized for sneaking too many sweets, and {helper.label} forgave {hero.pronoun('object')} with a warm smile.")
    world.say(f"By dusk, {hero.id} was calm again, and the little town felt kinder for the lesson it had learned.")


def tell(setting: Setting, p: StoryParams) -> World:
    world = World(setting)
    hero, helper, sweet, comfort = _setup(world, p)
    world.facts = {"hero": hero, "helper": helper, "sweet": sweet, "comfort": comfort, "place": setting, "params": p}
    world.say(f"Once in {setting.place}, {hero.id} loved sweet things and wandered where the stories grew like moss.")
    world.say(f"{helper.label.capitalize()} had a steady voice and a kind hand, like a lantern on a dark road.")
    world.para()
    _narrate_surprise(world, hero, helper, sweet)
    world.para()
    _narrate_turn(world, hero, helper, sweet)
    world.para()
    _narrate_reconciliation(world, hero, helper, comfort)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short folk tale about {p.hero}, a hidden cavity, and a gentle surprise in {p.place}.",
        f"Tell a child-friendly story where {p.hero} learns about a cavity after eating a sweet treat and then makes peace with the helper.",
        f"Write a simple folk tale with a surprise, a cavity, and reconciliation at {p.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, sweet = f["hero"], f["helper"], f["sweet"]
    return [
        QAItem(
            question=f"What happened when {hero.id} tasted the sweet treat?",
            answer=f"{hero.id} got a surprise because a hidden cavity hurt {hero.pronoun('possessive')} tooth, so {hero.id} gasped and listened closely.",
        ),
        QAItem(
            question=f"Who explained the cavity to {hero.id}?",
            answer=f"{helper.label.capitalize()} explained it kindly, without scolding, so the truth could be heard like a story around a fire.",
        ),
        QAItem(
            question=f"How did the story end after the sweet treat and the ache?",
            answer=f"{hero.id} apologized, {helper.label} forgave {hero.pronoun('object')}, and they reached reconciliation with a calmer heart.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cavity?",
            answer="A cavity is a tiny hole in a tooth that can make it hurt, especially after sweet food."
        ),
        QAItem(
            question="Why do people brush their teeth?",
            answer="People brush their teeth to wash away food bits and help keep holes and pain away."
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a mistake or a worry, so everyone can feel calm together."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id:10} ({e.type:9}) meters={meters} memes={memes}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="woodland", hero="Mina", hero_type="girl", helper="grandmother", helper_type="grandmother", sweet="honeycake", comfort="rinse"),
    StoryParams(place="village", hero="Owen", hero_type="boy", helper="miller", helper_type="man", sweet="berrytart", comfort="cloth"),
    StoryParams(place="cottage", hero="Nell", hero_type="girl", helper="herbalist", helper_type="woman", sweet="treaclebun", comfort="spark"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for sid in SWEETS:
        lines.append(asp.fact("sweet", sid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        hero=args.name or rng.choice([n for n, _ in HEROES]),
        hero_type=args.hero_type or rng.choice(["girl", "boy"]),
        helper=args.helper or rng.choice([n for n, _ in HELPERS]),
        helper_type=args.helper_type or rng.choice([t for _, t in HELPERS]),
        sweet=args.sweet or rng.choice(list(SWEETS)),
        comfort=args.comfort or rng.choice(list(COMFORTS)),
    )


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    p = resolve_params(args, rng)
    if not (can_surprise(World(SETTINGS[p.place]), SWEETS[p.sweet]) and can_reconcile(World(SETTINGS[p.place]), SWEETS[p.sweet], COMFORTS[p.comfort])):
        raise StoryError(explain_rejection(SWEETS[p.sweet], COMFORTS[p.comfort]))
    return p


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
            try:
                params = build_story_params(args, random.Random(seed))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.sweet} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

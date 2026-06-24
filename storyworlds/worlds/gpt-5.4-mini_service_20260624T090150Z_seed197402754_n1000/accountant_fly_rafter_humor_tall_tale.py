#!/usr/bin/env python3
"""
A tiny tall-tale storyworld about an accountant, a fly, and a rafter.

A careful accountant is trying to balance the books in a funny old room when a
bold fly starts buzzing around the rafters. The accountant chases, notices the
mischief, and finds a humorous fix that turns the whole bother into a laugh.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"accountant"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"fly"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little attic office"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relief:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "attic": Setting(place="the little attic office", indoors=True, affords={"fly"}),
    "loft": Setting(place="the high loft room", indoors=True, affords={"fly"}),
}

TROUBLES = {
    "fly": Trouble(
        id="fly",
        verb="swat the fly",
        gerund="swatting at the fly",
        rush="reach up and swat at the fly",
        mess="buzzed",
        soil="made the figures wobble",
        zone={"head", "hands"},
        keyword="fly",
        tags={"fly", "humor"},
    ),
}

RELIEFS = {
    "rafter": Relief(
        id="rafter",
        label="a rafter",
        prep="set a paper box on the desk and invite the fly to land there",
        tail="hung a shiny paper sign from the rafter that said, 'Fly, please buzz by appointment!'",
    ),
}

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    place: str
    trouble: str
    relief: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story model helpers
# ---------------------------------------------------------------------------

def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def predict_mess(world: World, actor: Entity, trouble: Trouble) -> dict:
    sim = world.copy()
    _do_trouble(sim, sim.get(actor.id), trouble, narrate=False)
    accountant = next(e for e in sim.characters() if e.type == "accountant")
    return {
        "messed_up": accountant.meters.get("confusion", 0.0) >= THRESHOLD,
        "funny": accountant.memes.get("humor", 0.0) >= THRESHOLD,
    }


def _do_trouble(world: World, actor: Entity, trouble: Trouble, narrate: bool = True) -> None:
    if trouble.id not in world.setting.affords:
        return
    world.zone = set(trouble.zone)
    _add_meter(actor, "confusion", 1.0)
    _add_meme(actor, "irritation", 1.0)
    if narrate:
        world.say(f"{actor.id} kept trying to {trouble.verb}, but the fly would not sit still.")


def _rafter_giggle(world: World, actor: Entity) -> None:
    _add_meme(actor, "humor", 1.0)
    world.say(
        f"Then {actor.id} looked up at the rafter and laughed, because the fly was perched "
        f"up high like a tiny king on a twig throne."
    )


def _humorous_fix(world: World, actor: Entity, trouble: Trouble, relief: Relief) -> None:
    _add_meme(actor, "relief", 1.0)
    _add_meme(actor, "humor", 1.0)
    world.say(
        f"{actor.id} stopped chasing and did something smarter: {relief.prep}."
    )
    world.say(
        f"At once the fly bobbed down, and by the time the sun leaned through the rafters, "
        f"{actor.pronoun('possessive')} ledger was steady again."
    )
    world.say(relief.tail)
    world.say(
        f"{actor.id} chuckled, the fly buzzed politely, and the whole office felt as merry "
        f"as a fiddle in a hatbox."
    )


def tell(setting: Setting, trouble: Trouble, relief: Relief, name: str) -> World:
    world = World(setting)
    accountant = world.add(Entity(
        id=name,
        kind="character",
        type="accountant",
        label="accountant",
        traits=["careful", "funny"],
    ))
    fly = world.add(Entity(
        id="Fly",
        kind="character",
        type="fly",
        label="fly",
        traits=["bold", "tiny"],
    ))
    world.add(Entity(
        id="rafter",
        type="rafter",
        label="rafter",
        phrase="a sturdy rafter above the desk",
    ))

    _add_meter(accountant, "order", 1.0)
    _add_meme(accountant, "pride", 1.0)

    world.say(
        f"{accountant.id} was a careful accountant in {setting.place}, with neat books and a pen "
        f"as straight as a fence post."
    )
    world.say(
        f"{accountant.id} liked every number to sit still, but a bold fly had other ideas."
    )
    world.para()
    world.say(
        f"One bright morning, the fly zipped under the rafter and made a great humming circle "
        f"over the desk."
    )
    _do_trouble(world, accountant, trouble)
    world.say(
        f"{accountant.id} tried to keep the columns lined up, yet the buzzing made the figures "
        f"feel wobbly and the room feel twice as small."
    )
    world.para()
    _rafter_giggle(world, accountant)
    _humorous_fix(world, accountant, trouble, relief)
    world.facts.update(
        accountant=accountant,
        fly=fly,
        rafter=world.get("rafter"),
        trouble=trouble,
        relief=relief,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["accountant"]
    t = f["trouble"]
    return [
        f"Write a short tall tale for young children about {a.id}, a {t.keyword}, and a rafter.",
        f"Tell a funny story where an accountant tries to {t.verb} but finds a kinder idea instead.",
        f"Write a gentle humorous tale in which a fly and a rafter help a busy accountant stop fussing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    acc = f["accountant"]
    trouble = f["trouble"]
    relief = f["relief"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {acc.id}, a careful accountant who works in the little office.",
        ),
        QAItem(
            question=f"What kept bothering {acc.id}?",
            answer=f"A bold fly kept buzzing around the room and making it hard to {trouble.verb}.",
        ),
        QAItem(
            question=f"How did {acc.id} solve the problem?",
            answer=f"{acc.id} stopped chasing the fly, laughed at the rafter, and used {relief.label} in a funny way so the fly would settle down.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the numbers were steady again and {acc.id} was laughing instead of worrying.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an accountant?",
            answer="An accountant is a person who helps keep track of money and numbers so things stay organized.",
        ),
        QAItem(
            question="What is a fly?",
            answer="A fly is a tiny buzzing insect that can zip around very quickly.",
        ),
        QAItem(
            question="What is a rafter?",
            answer="A rafter is a beam up high in a roof that helps hold the roof up.",
        ),
        QAItem(
            question="Why do people smile at funny surprises?",
            answer="People smile at funny surprises because humor can make a problem feel lighter and friendlier.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
accountant(acc1).
fly(fly1).
rafter(raf1).
humor(humor1).

buzzing(fly1).
up_high(raf1).
uses(acc1, humor1).

trouble(acc1, fly1) :- buzzing(fly1).
funny_turn(acc1) :- uses(acc1, humor1), up_high(raf1).
resolved(acc1) :- funny_turn(acc1), trouble(acc1, fly1).

#show trouble/2.
#show funny_turn/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("accountant", "acc1"),
        asp.fact("fly", "fly1"),
        asp.fact("rafter", "raf1"),
        asp.fact("humor", "humor1"),
        asp.fact("buzzing", "fly1"),
        asp.fact("up_high", "raf1"),
        asp.fact("uses", "acc1", "humor1"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show trouble/2. #show funny_turn/1. #show resolved/1."))
    atoms = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = {
        ("trouble", ("acc1", "fly1")),
        ("funny_turn", ("acc1",)),
        ("resolved", ("acc1",)),
    }
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", atoms ^ expected)
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="attic", trouble="fly", relief="rafter", name="Mabel"),
    StoryParams(place="loft", trouble="fly", relief="rafter", name="Nora"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for trouble in TROUBLES:
            if trouble in setting.affords:
                for relief in RELIEFS:
                    combos.append((place, trouble, relief))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: accountant, fly, and rafter.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--trouble", choices=TROUBLES.keys())
    ap.add_argument("--relief", choices=RELIEFS.keys())
    ap.add_argument("--name")
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
              if (args.place is None or c[0] == args.place)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.relief is None or c[2] == args.relief)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, trouble, relief = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Mabel", "Nora", "Lottie", "Etta", "Della"])
    return StoryParams(place=place, trouble=trouble, relief=relief, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TROUBLES[params.trouble], RELIEFS[params.relief], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show trouble/2. #show funny_turn/1. #show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show trouble/2. #show funny_turn/1. #show resolved/1."))
        for sym in model:
            print(sym)
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
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

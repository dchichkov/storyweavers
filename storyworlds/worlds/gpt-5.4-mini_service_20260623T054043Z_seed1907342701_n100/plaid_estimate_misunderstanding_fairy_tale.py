#!/usr/bin/env python3
"""
storyworlds/worlds/plaid_estimate_misunderstanding_fairy_tale.py
=================================================================

A standalone storyworld for a fairy-tale misunderstanding about a plaid item
and the word "estimate". The world keeps physical meters and emotional memes,
lets a small causal simulation drive the prose, and exposes a declarative ASP
twin for parity checks.

Seed idea:
- A child in a fairy-tale place wants a plaid thing for a feast.
- They misunderstand "estimate" and think it means a strange kind of spell or
  guessing game, while the grown-up means "measure and judge the amount".
- The turn comes from the mismatch, and the ending proves what changed: the
  right amount of cloth is chosen, the plaid item is finished, and the mood
  becomes bright.

The script is self-contained and uses only the stdlib plus the shared
storyworlds/results.py and storyworlds/asp.py helpers.
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
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "mother", "daughter"}
        male = {"boy", "king", "father", "son", "tailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Cloth:
    id: str
    label: str
    phrase: str
    use: str
    plaid: bool = False
    size: str = "small"
    tags: set[str] = field(default_factory=set)


@dataclass
class Help:
    id: str
    label: str
    phrase: str
    action: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str = ""
    cloth: str = ""
    helper: str = ""
    name: str = ""
    gender: str = ""
    adult: str = ""
    seed: Optional[int] = None


PLACES = {
    "castle_workroom": Place("castle_workroom", "the castle workroom", "warm and bright", {"measure", "stitch"}),
    "market_stall": Place("market_stall", "the market stall", "busy and colorful", {"measure", "buy"}),
    "rose_garden": Place("rose_garden", "the rose garden", "quiet and green", {"measure", "stitch"}),
}

CLOTH = {
    "plaid_cloak": Cloth("plaid_cloak", "plaid cloth", "a bolt of plaid cloth", "stitch a cloak", plaid=True, size="medium", tags={"plaid", "cloth"}),
    "plaid_bunting": Cloth("plaid_bunting", "plaid bunting", "a string of plaid bunting", "hang a banner", plaid=True, size="long", tags={"plaid", "cloth"}),
    "plain_ribbon": Cloth("plain_ribbon", "plain ribbon", "a long plain ribbon", "tie a garland", plaid=False, size="long", tags={"ribbon"}),
    "plaid_blanket": Cloth("plaid_blanket", "plaid blanket", "a folded plaid blanket", "cover a chair", plaid=True, size="wide", tags={"plaid", "blanket"}),
}

HELP = {
    "measuring_string": Help("measuring_string", "measuring string", "a measuring string", "measure carefully", tags={"measure"}),
    "chalk_marks": Help("chalk_marks", "chalk marks", "some chalk marks", "mark the length", tags={"measure"}),
    "golden_scissors": Help("golden_scissors", "golden scissors", "golden scissors", "trim the cloth", tags={"stitch"}),
}

GIRL_NAMES = ["Elsa", "Mira", "Clara", "Tilda", "Nina", "Rosie"]
BOY_NAMES = ["Robin", "Otto", "Felix", "Gareth", "Pip", "Bram"]
ADULTS = ["queen", "tailor", "gardener"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for cloth in CLOTH:
            for helper in HELP:
                if "measure" in PLACES[place].affords and "measure" in HELP[helper].tags:
                    if CLOTH[cloth].plaid:
                        out.append((place, cloth, helper))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about plaid and estimate.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cloth", choices=CLOTH)
    ap.add_argument("--helper", choices=HELP)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULTS)
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
              and (args.cloth is None or c[1] == args.cloth)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, cloth, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    adult = args.adult or rng.choice(ADULTS)
    return StoryParams(place=place, cloth=cloth, helper=helper, name=name, gender=gender, adult=adult)


def _measure_text(length: float) -> str:
    if length < 2:
        return "a little too short"
    if length > 4:
        return "long enough for a grand cloak"
    return "just right"


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.cloth not in CLOTH or params.helper not in HELP:
        raise StoryError("Unknown story parameters.")
    place = PLACES[params.place]
    cloth = CLOTH[params.cloth]
    helper = HELP[params.helper]
    if not cloth.plaid:
        raise StoryError("This story needs a plaid thing so the word can matter.")

    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name,
                            meters={"desire": 0.0, "curiosity": 0.0}, memes={"hope": 0.0, "confusion": 0.0}))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult, label=f"the {params.adult}",
                             meters={"care": 0.0}, memes={"concern": 0.0}))
    cloth_ent = world.add(Entity(id="cloth", type="thing", label=cloth.label, phrase=cloth.phrase,
                                 meters={"length": 3.0, "cut": 0.0, "finished": 0.0, "plaidness": 1.0 if cloth.plaid else 0.0},
                                 memes={"importance": 1.0}, attrs={"use": cloth.use}))
    tool = world.add(Entity(id="tool", type="thing", label=helper.label, phrase=helper.phrase,
                            meters={"accuracy": 1.0}, memes={"helpfulness": 1.0}, attrs={"action": helper.action}))

    world.facts.update(hero=hero, adult=adult, cloth=cloth_ent, tool=tool, place=place, cloth_cfg=cloth, helper_cfg=helper)

    hero.meters["desire"] += 1
    hero.memes["hope"] += 1
    world.say(f"In {place.label}, {hero.label} came to the {adult.label_word if hasattr(adult, 'label_word') else params.adult} with a wish for {cloth.phrase}.")
    world.say(f"The little room felt like a tale, and the plaid cloth shone softly beside the window.")

    world.para()
    hero.meters["curiosity"] += 1
    adult.meters["care"] += 1
    adult.memes["concern"] += 1
    world.say(f"{hero.label} heard the word “estimate” and frowned. {hero.pronoun().capitalize()} thought it meant a fancy guess-song, not a careful counting of cloth.")
    world.say(f'{hero.label} said, "Will the estimate make it grand?" and the {params.adult} smiled, because the child had misunderstood the word.')

    world.para()
    world.say(f'The {params.adult} lifted {helper.phrase} and said, "We estimate first. That means we measure and judge what is needed."')
    needed = 3.0
    cloth_ent.meters["needed"] = needed
    cloth_ent.meters["estimate"] = needed
    world.say(f"The string lay along the plaid cloth, and the answer was {_measure_text(needed)}.")

    if cloth_ent.meters["length"] < cloth_ent.meters["needed"]:
        cloth_ent.memes["worry"] = 1.0
        world.say(f"At first, the plaid cloth looked too short, and the child's heart sank a little.")
        cloth_ent.meters["length"] = cloth_ent.meters["needed"]
    else:
        world.say(f"The plaid cloth was already long enough, so the child only needed to trim it kindly.")

    cloth_ent.meters["cut"] = 1.0
    cloth_ent.meters["finished"] = 1.0
    hero.memes["confusion"] = 0.0
    hero.memes["joy"] = 1.0
    world.say(f"Together they made the plaid cloth into {cloth.use}, and the misunderstanding melted away like mist at sunrise.")
    world.say(f"By the end, {hero.label} wore the finished plaid treasure, and {cloth.phrase} had become a bright part of the day.")

    world.facts["finished"] = True
    world.facts["needed"] = needed
    world.facts["misunderstanding"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, adult, cloth = f["hero"], f["adult"], f["cloth_cfg"]
    return [
        f'Write a short fairy tale for a young child about {hero.label} and a plaid thing, using the word "estimate".',
        f"Tell a gentle story where {hero.label} misunderstands estimate, and the grown-up shows how to measure {cloth.phrase}.",
        f'Write a fairy tale with a mistaken word, a plaid cloth, and a happy ending where "estimate" means careful measuring.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, adult, cloth, place, tool = f["hero"], f["adult"], f["cloth"], f["place"], f["tool"]
    cloth_cfg = f["cloth_cfg"]
    helper_cfg = f["helper_cfg"]
    return [
        QAItem(
            question=f"Why did {hero.label} look puzzled when the {adult.label_word if hasattr(adult, 'label_word') else adult.type} said estimate?",
            answer=f"{hero.label} misunderstood the word. {hero.pronoun().capitalize()} thought estimate was a magical guessing game, but it meant to measure carefully.",
        ),
        QAItem(
            question=f"What did the {adult.type} use to help with the plaid cloth?",
            answer=f"The {adult.label} used {tool.label} to measure the plaid cloth. That helped them judge the right amount before any cutting was done.",
        ),
        QAItem(
            question=f"What happened to {cloth_cfg.phrase} by the end?",
            answer=f"It was turned into {cloth_cfg.use}. The plaid cloth was no longer just folded cloth; it became something useful and ready for the tale's happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does estimate mean?",
            answer="Estimate means to make a careful guess about how much of something is needed. In a sewing room, it can mean measuring and judging the cloth before cutting.",
        ),
        QAItem(
            question="What is plaid?",
            answer="Plaid is a cloth pattern made of crossing lines and checks. It often looks cozy and old-fashioned, like something from a fairy tale.",
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="castle_workroom", cloth="plaid_cloak", helper="measuring_string", name="Mira", gender="girl", adult="queen"),
    StoryParams(place="market_stall", cloth="plaid_bunting", helper="chalk_marks", name="Robin", gender="boy", adult="tailor"),
    StoryParams(place="rose_garden", cloth="plaid_blanket", helper="golden_scissors", name="Clara", gender="girl", adult="gardener"),
    StoryParams(place="castle_workroom", cloth="plaid_bunting", helper="measuring_string", name="Bram", gender="boy", adult="queen"),
]


ASP_RULES = r"""
place(P) :- place_fact(P).
plaid_cloth(C) :- cloth_fact(C), plaid_fact(C).
helper(H) :- helper_fact(H), measure_fact(H).
valid(P,C,H) :- place(P), plaid_cloth(C), helper(H).
misunderstanding :- estimates_word, not meaning_known.
meaning_known :- measure_meaning.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, cloth in CLOTH.items():
        lines.append(asp.fact("cloth_fact", cid))
        if cloth.plaid:
            lines.append(asp.fact("plaid_fact", cid))
    for hid, helpo in HELP.items():
        lines.append(asp.fact("helper_fact", hid))
        if "measure" in helpo.tags:
            lines.append(asp.fact("measure_fact", hid))
    lines.append(asp.fact("estimates_word"))
    lines.append(asp.fact("measure_meaning"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = cl == py
    smoke = None
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        smoke = sample.story and bool(sample.prompts)
    except Exception:
        smoke = False
    if ok and smoke:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos) and generation smoke-test passed.")
        return 0
    if not ok:
        print("MISMATCH between ASP and Python valid_combos().")
        print("only in ASP:", sorted(cl - py))
        print("only in Python:", sorted(py - cl))
    if not smoke:
        print("Generation smoke-test failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.cloth not in CLOTH or params.helper not in HELP:
        raise StoryError("Unknown story parameter.")
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
        print(asp_program("#show valid/3.\n#show misunderstanding/0.\n#show meaning_known/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

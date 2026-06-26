#!/usr/bin/env python3
"""
A folk-tale storyworld about two towns, a cleaved road, and a tender buss.

Premise:
- Two small towns share a market lane that has been cleaved by a storm-fallen oak.
- A brave child remembers, in flashback, how the old bridge was once mended.
- The child must choose between keeping a selfish shortcut and doing a kind, hard thing.

World dynamics:
- Physical meters track debris, distance, and repair.
- Emotional memes track bravery, worry, relief, and moral value.
- A buss is a gentle kiss used as a folk-tale sign of blessing, thanks, or apology.

The story is constrained to read like a complete folk tale: setup, trouble, brave
action, and a resolved ending image.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Town:
    name: str
    folk: str
    charm: str
    value: str
    brave_sign: str


@dataclass
class StoryParams:
    town_a: str
    town_b: str
    hero_name: str
    hero_kind: str
    helper_name: str
    helper_kind: str
    value: str
    seed: Optional[int] = None


class World:
    def __init__(self, town_a: Town, town_b: Town):
        self.town_a = town_a
        self.town_b = town_b
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.flashback: bool = False
        self.cleave_width: float = 0.0

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about towns, cleave, and buss.")
    ap.add_argument("--town-a", choices=sorted(TOWNS))
    ap.add_argument("--town-b", choices=sorted(TOWNS))
    ap.add_argument("--value", choices=sorted(MORAL_VALUES))
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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


TOWNS = {
    "brookhaven": Town("Brookhaven", "bakers", "bread warm from the ovens", "sharing", "a silver ribbon"),
    "hillend": Town("Hillend", "shepherds", "wind over the grass", "courage", "a bright lantern"),
    "mossmere": Town("Mossmere", "weavers", "threads on a drying line", "kindness", "a green knot"),
    "foxglove": Town("Foxglove", "gardeners", "apples in baskets", "truth", "a red scarf"),
}

MORAL_VALUES = {
    "sharing": "sharing",
    "kindness": "kindness",
    "courage": "courage",
    "truth": "truth",
}

GIRL_NAMES = ["Mira", "Elin", "Sera", "Nia", "Tove", "Anya"]
BOY_NAMES = ["Perrin", "Jory", "Rian", "Bram", "Ludo", "Niko"]
HELPER_NAMES = ["Old Wren", "Nan Pippa", "Moss Tom", "Uncle Rook", "Aunt Elspeth"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.town_a == params.town_b:
        raise StoryError("The tale needs two different towns.")
    if params.value not in MORAL_VALUES:
        raise StoryError("The story needs a clear moral value.")
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must be different people.")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for a in TOWNS:
        for b in TOWNS:
            if a == b:
                continue
            for v in MORAL_VALUES:
                combos.append((a, b, v))
    return combos


ASP_RULES = r"""
#show valid/3.

town(T) :- town_fact(T).
different(A,B) :- town(A), town(B), A != B.
valid(A,B,V) :- town(A), town(B), different(A,B), value(V).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for k in TOWNS:
        lines.append(asp.fact("town_fact", k))
    for k in MORAL_VALUES:
        lines.append(asp.fact("value", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print(" only in clingo:", sorted(a - p))
    if p - a:
        print(" only in python:", sorted(p - a))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.town_a is None or c[0] == args.town_a)
              and (args.town_b is None or c[1] == args.town_b)
              and (args.value is None or c[2] == args.value)]
    if not combos:
        raise StoryError("No valid town pair matches the given options.")
    town_a, town_b, value = rng.choice(sorted(combos))
    hero_kind = rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_kind == "girl" else BOY_NAMES)
    helper_kind = rng.choice(["woman", "man"])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    params = StoryParams(
        town_a=town_a, town_b=town_b, hero_name=hero_name,
        hero_kind=hero_kind, helper_name=helper_name, helper_kind=helper_kind,
        value=value,
    )
    reasonableness_gate(params)
    return params


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_kind, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_kind, label=params.helper_name))
    lane = world.add(Entity(id="lane", type="road", label="market lane", meters={"cleaved": 0.0, "repaired": 0.0}))
    oak = world.add(Entity(id="oak", type="thing", label="storm-fallen oak", meters={"weight": 1.0}))
    ribbon = world.add(Entity(id="ribbon", type="thing", label="bridge ribbon", owner=helper.id))

    hero.memes["bravery"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["moral_value"] = 0.0
    helper.memes["faith"] = 0.0

    world.say(
        f"Long ago, between {world.town_a.name} and {world.town_b.name}, there ran one market lane."
    )
    world.say(
        f"The folk of {world.town_a.name} loved {world.town_a.charm}, and the folk of {world.town_b.name} loved {world.town_b.charm}."
    )
    world.say(
        f"The lane carried their carts and gossip, and each week the people met there for honest trade and warm news."
    )

    world.para()
    world.say(
        f"But after a hard wind, a great oak came down and cleaved the lane in two."
    )
    lane.meters["cleaved"] = 1.0
    world.cleave_width = 1.0
    hero.memes["worry"] += 1.0
    helper.memes["faith"] += 1.0
    world.say(
        f"Now neither town could pass easily, and the children had to circle the long way through the hills."
    )

    world.para()
    world.flashback = True
    world.say(
        f"When {hero.label} saw the broken lane, {hero.pronoun('subject')} had a flashback."
    )
    world.say(
        f"{hero.label} remembered being small, when {helper.label} had tied a bright ribbon across the old plank and said that a kind hand can mend what a storm has bitten."
    )
    world.say(
        f"That memory filled {hero.pronoun('object')} with courage, and {hero.pronoun('possessive')} heart grew steadier."
    )
    hero.memes["bravery"] += 1.0
    hero.memes["moral_value"] += 1.0

    world.para()
    world.say(
        f"Yet the easier choice was to keep the lane blocked, for then {hero.label} could take the shortcut path alone and arrive first at the market."
    )
    hero.memes["worry"] += 1.0
    hero.memes["bravery"] += 1.0
    world.say(
        f"But {hero.label} knew the {params.value} way was to help the whole road, not only {hero.pronoun('object')}self."
    )

    world.say(
        f"So {hero.label} called for {helper.label}, and together they hauled the oak aside, pebble by pebble."
    )
    lane.meters["cleaved"] = 0.0
    lane.meters["repaired"] = 1.0
    world.say(
        f"Then {helper.label} tied the ribbon to a fresh post, and {hero.label} gave {helper.pronoun('object')} a thankful buss on the cheek."
    )
    helper.memes["joy"] = 1.0
    hero.memes["moral_value"] += 1.0
    hero.memes["worry"] = 0.0
    world.say(
        f"The buss was small, but it carried a blessing: the work was done for the good of both towns."
    )

    world.para()
    world.say(
        f"By dusk, carts from {world.town_a.name} and {world.town_b.name} crossed the lane again."
    )
    world.say(
        f"The folk traded bread, wool, apples, and stories, and {hero.label} stood by the ribboned bridge with a brave smile."
    )
    world.say(
        f"That night the two towns slept easier, because one child had chosen {params.value} over selfishness."
    )

    world.facts = {
        "hero": hero,
        "helper": helper,
        "lane": lane,
        "oak": oak,
        "ribbon": ribbon,
        "town_a": world.town_a,
        "town_b": world.town_b,
        "value": params.value,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child about two towns, a lane that was cleaved, and a brave choice.',
        f"Tell a simple story where {f['hero'].label} remembers a past kindness in a flashback and helps both towns.",
        f"Write a short story that includes a buss as a gentle sign of thanks after a hard job is finished.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"What happened to the lane between {f['town_a'].name} and {f['town_b'].name}?",
            answer="A storm-fallen oak came down and cleaved the lane in two.",
        ),
        QAItem(
            question=f"What did {hero.label} remember in the flashback?",
            answer=f"{hero.label} remembered that {helper.label} once tied a bright ribbon across the old plank and showed that kind hands can mend broken things.",
        ),
        QAItem(
            question=f"Why was {hero.label} brave at the end?",
            answer=f"{hero.label} was brave because {hero.pronoun('subject')} chose to help repair the lane for both towns instead of taking the selfish shortcut.",
        ),
        QAItem(
            question=f"What was the buss for?",
            answer=f"The buss was a gentle kiss of thanks after the lane was cleared and the work was done together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does brave mean?",
            answer="Brave means you do the right thing even when it feels hard or a little scary.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="What is a buss?",
            answer="A buss is an old word for a gentle kiss, often used to show thanks or love.",
        ),
        QAItem(
            question="What is moral value?",
            answer="A moral value is an idea about how to treat others well, like kindness, truth, sharing, or courage.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  flashback={world.flashback}")
    lines.append(f"  cleave_width={world.cleave_width}")
    return "\n".join(lines)


CURATED = [
    StoryParams("brookhaven", "hillend", "Mira", "girl", "Old Wren", "woman", "sharing"),
    StoryParams("mossmere", "foxglove", "Perrin", "boy", "Nan Pippa", "woman", "kindness"),
    StoryParams("hillend", "brookhaven", "Sera", "girl", "Uncle Rook", "man", "courage"),
]


def generate(params: StoryParams) -> StorySample:
    w = World(TOWNS[params.town_a], TOWNS[params.town_b])
    w = tell(w, params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible town/value combos:\n")
        for a, b, v in combos:
            print(f"  {a:10} {b:10} {v}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.town_a} to {p.town_b} ({p.value})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

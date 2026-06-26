#!/usr/bin/env python3
"""
storyworlds/worlds/dwell_weed_harrow_surprise_rhyme_sharing_adventure.py
========================================================================

A small story world for a gentle Adventure tale about children, garden work,
surprise, rhyme, and sharing.

Premise:
- A child and a helper work in a garden.
- The garden has a weed patch that must be cleared with a harrow.
- A surprise object changes the mood.
- A rhyme and a sharing choice turn the day from tricky to bright.

The world model tracks physical state in meters and emotional state in memes.
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
    tool_for: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
    place: str = "the garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    keyword: str
    surprise: str
    rhyme_words: tuple[str, str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    owner_kind: str = "any"


@dataclass
class World:
    setting: Setting
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
        import copy

        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=dict(self.facts),
        )


SETTINGS = {
    "garden": Setting(place="the garden", affords={"weed", "harrow"}),
    "yard": Setting(place="the yard", affords={"weed", "harrow"}),
    "plot": Setting(place="the little plot", affords={"weed", "harrow"}),
}

ACTIVITIES = {
    "weed": Activity(
        id="weed",
        verb="pull out the weeds",
        gerund="weeding the rows",
        mess="tired",
        soil="still tangled",
        keyword="weed",
        surprise="a bright butterfly under a leaf",
        rhyme_words=("weed", "seed"),
        tags={"weed"},
    ),
    "harrow": Activity(
        id="harrow",
        verb="pull the harrow across the soil",
        gerund="harrowing the soil",
        mess="bumpy",
        soil="full of bumps",
        keyword="harrow",
        surprise="a shiny button in the dirt",
        rhyme_words=("harrow", "sparrow"),
        tags={"harrow"},
    ),
}

TOOLS = {
    "harrow": Tool(
        id="harrow",
        label="a small harrow",
        phrase="a small harrow with wooden handles",
        helps={"harrow"},
    ),
    "basket": Tool(
        id="basket",
        label="a woven basket",
        phrase="a woven basket for gathering things",
        helps={"sharing"},
    ),
}

NAMES = ["Mina", "Ari", "Pip", "Nora", "Theo", "June", "Luca", "Ivy"]
PARTNERS = ["helper", "grandparent", "friend"]
TRAITS = ["curious", "cheerful", "careful", "spirited", "gentle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    partner: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(place, act) for place, s in SETTINGS.items() for act in s.affords]


def _do_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0.0) + 1.0
    hero.memes["effort"] = hero.memes.get("effort", 0.0) + 1.0
    if activity.id == "weed":
        world.facts["weed_patch"] = True
    if activity.id == "harrow":
        world.facts["soil_broken"] = True


def _maybe_surprise(world: World, hero: Entity, activity: Activity) -> None:
    if world.facts.get("surprise_seen"):
        return
    world.facts["surprise_seen"] = True
    world.say(f"Then, under a leaf, {hero.id} found {activity.surprise}.")


def _rhyme(world: World, hero: Entity, activity: Activity) -> None:
    a, b = activity.rhyme_words
    world.facts["rhyme_used"] = True
    world.say(
        f"{hero.id} laughed and said a tiny rhyme: "
        f"\"{a} and {b}, {a} and {b}, the garden can shine up ahead.\""
    )


def _sharing(world: World, hero: Entity, partner: Entity) -> None:
    basket = world.add(Entity(id="basket", type="basket", label="basket", phrase=TOOLS["basket"].phrase))
    world.facts["basket"] = basket
    hero.memes["sharing"] = hero.memes.get("sharing", 0.0) + 1.0
    partner.memes["sharing"] = partner.memes.get("sharing", 0.0) + 1.0
    world.say(
        f"Together they used {basket.phrase} to share the small finds, and "
        f"{partner.id} smiled at how easy the work felt when both hands helped."
    )


def tell(world: World, hero_name: str, partner_kind: str, trait: str, activity: Activity) -> World:
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name, meters={}, memes={}))
    partner = world.add(Entity(id="Partner", kind="character", type=partner_kind, label=f"the {partner_kind}", meters={}, memes={}))
    tool = world.add(Entity(id="Harrow", kind="thing", type="harrow", label="harrow", phrase=TOOLS["harrow"].phrase))

    hero.memes["curious"] = 1.0
    world.facts.update(hero=hero, partner=partner, activity=activity, tool=tool, trait=trait)

    world.say(
        f"{hero.id} was a {trait} child who loved to dwell in the garden when the sun was mild."
    )
    world.say(
        f"{hero.id} and {partner.id} came to the garden to {activity.verb}."
    )
    world.say(
        f"They brought {tool.phrase}, because the weeds and the hard soil needed patient hands."
    )

    world.para()
    _do_activity(world, hero, activity)
    world.say(f"At first, the work was slow, and {hero.id} felt the rows tug back like stubborn strings.")
    _maybe_surprise(world, hero, activity)
    _rhyme(world, hero, activity)

    world.para()
    if activity.id == "weed":
        world.say(
            f"After the rhyme, {hero.id} picked out the weeds more carefully, and the patch began to look neat."
        )
    else:
        world.say(
            f"After the rhyme, {hero.id} pulled the harrow in gentle lines, and the soil started to look smooth."
        )
    _sharing(world, hero, partner)
    world.say(
        f"By the end, the garden felt calmer, and {hero.id} could dwell there with a proud, bright smile."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a short Adventure story for a young child about {hero.id} in {world.setting.place} with the word "{act.keyword}".',
        f"Tell a gentle story where {hero.id} works on {act.gerund}, finds a surprise, and learns to share.",
        f'Write a simple story using the words "{act.keyword}", "Surprise", "Rhyme", and "Sharing".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    act = f["activity"]
    qa = [
        QAItem(
            question=f"What was {hero.id} doing in {world.setting.place}?",
            answer=f"{hero.id} was {act.gerund} with {partner.id}.",
        ),
        QAItem(
            question=f"What surprise did {hero.id} find?",
            answer=f"{hero.id} found {act.surprise}.",
        ),
        QAItem(
            question=f"What helped the work feel better?",
            answer="A little rhyme helped, and then they shared what they found.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The garden looked better, and {hero.id} felt proud and happy after sharing.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a weed?",
            answer="A weed is a plant growing where people do not want it, so gardeners often pull it out.",
        ),
        QAItem(
            question="What is a harrow?",
            answer="A harrow is a garden tool used to break up and smooth soil.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use or enjoy something with you.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern of words that sound alike at the end.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the chosen setting affords the activity.
valid(Place, Activity) :- affords(Place, Activity).

% A child can have an adventure when the activity exists in the setting.
adventure(Place, Activity) :- valid(Place, Activity).

#show valid/2.
#show adventure/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for act in ACTIVITIES.values():
        lines.append(asp.fact("activity", act.id))
        for tag in sorted(act.tags):
            lines.append(asp.fact("tag", act.id, tag))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    clingo_valid = sorted(set(asp.atoms(model, "valid")))
    py_valid = sorted(valid_combos())
    if clingo_valid == py_valid:
        print(f"OK: clingo gate matches valid_combos() ({len(py_valid)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", clingo_valid)
    print("  python:", py_valid)
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle Adventure story world about weeds, harrows, surprise, rhyme, and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--partner", choices=PARTNERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    partner = args.partner or rng.choice(PARTNERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, partner=partner, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    activity = ACTIVITIES[params.activity]
    tell(world, params.name, params.partner, params.trait, activity)
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


CURATED = [
    StoryParams(place="garden", activity="weed", name="Mina", partner="helper", trait="curious"),
    StoryParams(place="yard", activity="harrow", name="Theo", partner="friend", trait="cheerful"),
    StoryParams(place="plot", activity="weed", name="Ivy", partner="grandparent", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity) combos:\n")
        for place, activity in combos:
            print(f"  {place:12} {activity}")
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

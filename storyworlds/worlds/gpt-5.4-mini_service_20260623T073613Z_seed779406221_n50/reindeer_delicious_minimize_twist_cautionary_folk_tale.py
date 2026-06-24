#!/usr/bin/env python3
"""
storyworlds/worlds/reindeer_delicious_minimize_twist_cautionary_folk_tale.py
============================================================================

A standalone storyworld in a folk-tale style about a reindeer, a delicious
temptation, a careful twist, and a cautionary lesson.

Premise:
A small reindeer loves a delicious treat while helping at a winter market. The
treat is tempting, but too much of it makes the sleigh load heavy and hard to
pull. A wise helper suggests a way to minimize the load, and the story turns
when the reindeer chooses the lighter path.

This world models:
- physical meters: load, heavy, spill, cold, speed
- emotional memes: delight, worry, pride, relief
- causal progression with a warning, a twist, and a safe ending
- Python reasonableness gate plus inline ASP twin
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carries: Optional[str] = None
    pulled_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"reindeer", "stag"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    winter: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    delicious: str
    mess: str
    load: int
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TwistPlan:
    id: str
    label: str
    action: str
    minimize: str
    ending: str
    lightening: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
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


@dataclass
class StoryParams:
    place: str
    treat: str
    twist: str
    name: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "village_square": Place("village_square", "the village square", True, {"market"}),
    "forest_road": Place("forest_road", "the forest road", True, {"market"}),
    "barn_yard": Place("barn_yard", "the barn yard", True, {"market"}),
}

TREATS = {
    "honeycake": Treat(
        "honeycake",
        "honey cake",
        "a honey cake with berry glaze",
        "delicious and sweet",
        "crumbly and sticky",
        load=3,
        risk="too heavy",
        tags={"delicious", "cake"},
    ),
    "berry_pies": Treat(
        "berry_pies",
        "berry pies",
        "two berry pies",
        "delicious and warm",
        "juicy and messy",
        load=4,
        risk="too much to carry",
        plural=True,
        tags={"delicious", "berries"},
    ),
    "spiced_bread": Treat(
        "spiced_bread",
        "spiced bread",
        "a loaf of spiced bread",
        "delicious and warm",
        "soft and crumbly",
        load=2,
        risk="hard to hold",
        tags={"delicious", "bread"},
    ),
}

TWISTS = {
    "share": TwistPlan(
        "share",
        "share the treat with the village bell-ringer",
        "split the treat into smaller pieces",
        "The load grew lighter at once",
        lightening=2,
        tags={"twist", "minimize"},
    ),
    "swap": TwistPlan(
        "swap",
        "swap the big basket for a little tray",
        "move the food into the smaller tray",
        "The reindeer could pull more easily",
        lightening=3,
        tags={"twist", "minimize"},
    ),
    "save": TwistPlan(
        "save",
        "save one bite for later and carry less now",
        "leave the extra pieces at the warm oven",
        "The sleigh felt light as snow",
        lightening=4,
        tags={"twist", "minimize"},
    ),
}

NAMES = ["Runa", "Bram", "Mira", "Tovi", "Soren", "Alma"]
HELPERS = ["old mare", "bell-ringer", "market baker", "kind goat"]

ASP_RULES = r"""
place(P) :- place_name(P).
treat(T) :- treat_name(T).
twist(W) :- twist_name(W).

risky(T) :- load(T, L), L >= 3.
good_twist(W) :- twist_name(W), minimizes(W).

valid_story(P, T, W) :- place_name(P), treat_name(T), twist_name(W), risky(T), good_twist(W).

lightened(T, W, N) :- load(T, L), lighten(W, N), L > N.
safe_end(T, W) :- valid_story(_, T, W), lightened(T, W, N), N >= 2.
"""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale reindeer storyworld about a delicious temptation and a minimizing twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for t in TREATS:
            for w in TWISTS:
                out.append((p, t, w))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.treat is None or c[1] == args.treat)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, treat, twist = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, treat=treat, twist=twist, name=name, helper=helper)


def tell(place: Place, treat: Treat, twist: TwistPlan, name: str, helper: str) -> World:
    world = World(place)
    reindeer = world.add(Entity(id=name, kind="character", type="reindeer", label=name))
    assistant = world.add(Entity(id="Helper", kind="character", type="helper", label=helper, type="helper"))
    gift = world.add(Entity(id="Treat", kind="thing", type="treat", label=treat.label, phrase=treat.phrase))
    reindeer.meters.update({"load": 0.0, "speed": 0.0})
    reindeer.memes.update({"delight": 0.0, "worry": 0.0, "pride": 0.0, "relief": 0.0})

    world.say(f"{name} was a small reindeer who loved the winter road and the bright village square.")
    world.say(f"{name} also loved {treat.delicious} {treat.label}, and the smell made {reindeer.pronoun('possessive')} nose twitch.")

    world.para()
    world.say(f"One market morning, {name} helped carry {treat.phrase} toward {place.label}.")
    reindeer.meters["load"] += treat.load
    reindeer.memes["delight"] += 1

    if treat.load >= 3:
        world.say(f"That treat was {treat.risk}, and the sleigh began to creak.")
        reindeer.memes["worry"] += 1

    world.para()
    world.say(f"{helper.capitalize()} saw the trouble and whispered a cautionary warning: 'A heavy load can slow a good reindeer.'")
    world.say(f"{name} wanted to keep every bite, but {helper} suggested a way to minimize the load.")
    reindeer.memes["pride"] += 1

    if twist.id == "share":
        world.say(f"The twist was simple: {name} shared the treat with {helper}.")
        reindeer.meters["load"] -= twist.lightening
        reindeer.memes["worry"] = 0
    elif twist.id == "swap":
        world.say(f"The twist was clever: {name} swapped the big basket for a little tray.")
        reindeer.meters["load"] -= twist.lightening
        reindeer.memes["worry"] = 0
    else:
        world.say(f"The twist was gentle: {name} saved one bite for later and carried less now.")
        reindeer.meters["load"] -= twist.lightening
        reindeer.memes["worry"] = 0

    if reindeer.meters["load"] < 1:
        reindeer.meters["load"] = 0

    world.para()
    world.say(f"With the load minimized, {name} tugged the sleigh again.")
    reindeer.meters["speed"] = 1.0 if reindeer.meters["load"] <= 1 else 0.5

    world.say(f"{twist.ending}, and the bells rang like happy little stars.")
    reindeer.memes["relief"] += 1

    world.facts.update(reindeer=reindeer, assistant=assistant, gift=gift, place=place, treat=treat, twist=twist)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story for a young child about a reindeer named {f["reindeer"].id} who loves a delicious treat but learns to minimize the load.',
        f"Tell a cautionary winter story where {f['reindeer'].id} carries {f['treat'].phrase} and then makes a wise twist to keep going.",
        f'Write a short story with the words "reindeer", "delicious", and "minimize" that ends with a lighter sleigh and a happy bell.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    r = f["reindeer"]
    t = f["treat"]
    tw = f["twist"]
    helper = f["assistant"].label
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {r.id}, a small reindeer who loves {t.label} and learns a careful lesson."
        ),
        QAItem(
            question=f"Why did {helper} give a warning?",
            answer=f"{helper.capitalize()} saw that {t.phrase} was heavy enough to slow the sleigh. That is why {helper} told {r.id} to minimize the load."
        ),
        QAItem(
            question=f"What twist helped {r.id}?",
            answer=f"{tw.label.capitalize()} helped by making the load lighter. After that, the sleigh could move safely again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to minimize something?",
            answer="To minimize something means to make it as small or as light as you can."
        ),
        QAItem(
            question="Why can a heavy load be a problem for a sleigh?",
            answer="A heavy load can make a sleigh slow and hard to pull, especially on a cold winter road."
        ),
        QAItem(
            question="Why are delicious treats tempting?",
            answer="Delicious treats smell and taste so good that it can be hard to stop at just one bite."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    for section, items in (("story", sample.story_qa), ("world", sample.world_qa)):
        lines.append(f"== {section} qa ==")
        for item in items:
            lines.append(f"Q: {item.question}")
            lines.append(f"A: {item.answer}")
        lines.append("")
    return "\n".join(lines).rstrip()


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TREATS[params.treat], TWISTS[params.twist], params.name, params.helper)
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


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_name", p))
    for t, obj in TREATS.items():
        lines.append(asp.fact("treat_name", t))
        lines.append(asp.fact("load", t, obj.load))
    for w in TWISTS:
        lines.append(asp.fact("twist_name", w))
        lines.append(asp.fact("minimizes", w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3.\n#show safe_end/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = set(valid_combos())
    if len(atoms) != len(py):
        print("MISMATCH between ASP and Python gates.")
        return 1
    print(f"OK: ASP and Python gates agree on {len(py)} combos.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(p, t, w, NAMES[i % len(NAMES)], HELPERS[i % len(HELPERS)]))
                   for i, (p, t, w) in enumerate(valid_combos()[:5])]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()

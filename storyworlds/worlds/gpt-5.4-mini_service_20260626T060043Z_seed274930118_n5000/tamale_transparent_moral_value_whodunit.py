#!/usr/bin/env python3
"""
Standalone storyworld: a tiny whodunit about a missing tamale, a transparent
clue, and the moral value of telling the truth.

Seed premise:
A child discovers a tamale has vanished before dinner. A transparent container,
a few careful observations, and honest choices reveal what really happened.
The story should feel like a gentle whodunit: clues, suspicion, turn, reveal.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    kind: str = "character"
    name: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class ObjectThing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    visible: bool = True
    transparent: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the little kitchen"
    time: str = "evening"


@dataclass
class StoryParams:
    setting: str
    hero: str
    suspect: str
    missing_item: str
    clue: str
    culprit: str
    moral_value: str = "truth"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.facts: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


MISSING_ITEMS = {
    "tamale": {
        "label": "tamale",
        "phrase": "a warm tamale wrapped in corn husks",
        "color": "golden",
        "shape": "small and tucked into a plate",
    },
}

SETTINGS = {
    "kitchen": Setting(place="the little kitchen", time="evening"),
    "pantry": Setting(place="the quiet pantry", time="afternoon"),
    "dining_room": Setting(place="the dining room", time="dinnertime"),
}

NAMES = ["Mina", "Theo", "Pia", "Jun", "Iris", "Noah", "Lena", "Owen"]
SUSPECTS = ["parent", "sibling", "neighbor", "grandparent"]

ASP_RULES = r"""
missing(X) :- item(X), taken(X).
clue_visible(C) :- clue(C), transparent(C).
culprit(C) :- suspicion(C), lied_about_food(C).
truthful(X) :- said_where(X), not lied_about_food(X).
moral_value(truth) :- truthful(_).
reveal(C) :- culprit(C), clue_visible(_).
#show missing/1.
#show clue_visible/1.
#show moral_value/1.
#show reveal/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.place:
            lines.append(asp.fact("place", sid, s.place))
    for iid in MISSING_ITEMS:
        lines.append(asp.fact("item", iid))
    lines.append(asp.fact("clue", "transparent_container"))
    lines.append(asp.fact("transparent", "transparent_container"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show clue_visible/1.\n#show moral_value/1.\n"))
    atoms = set((sym.name, tuple(a.name if a.type != 1 else a.string for a in sym.arguments)) for sym in model)
    expected = {("clue_visible", ("transparent_container",)), ("moral_value", ("truth",))}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH in ASP parity check.")
    print("expected:", expected)
    print("got:", atoms)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about a missing tamale.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--missing-item", choices=MISSING_ITEMS)
    ap.add_argument("--clue", choices=["transparent_container"])
    ap.add_argument("--culprit", choices=["parent", "sibling", "neighbor", "grandparent"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(NAMES)
    suspect = args.suspect or rng.choice(SUSPECTS)
    missing_item = args.missing_item or "tamale"
    clue = args.clue or "transparent_container"
    culprit = args.culprit or rng.choice(SUSPECTS)
    if culprit == hero:
        raise StoryError("The hero cannot be the culprit in this gentle whodunit.")
    return StoryParams(setting, hero, suspect, missing_item, clue, culprit, "truth")


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Character(id="hero", name=params.hero, role="child", traits=["curious", "careful"]))
    suspect = world.add(Character(id="suspect", name=params.suspect, role="suspect", traits=["nervous"]))
    culprit = world.add(Character(id="culprit", name=params.culprit, role="culprit", traits=["guilty"]))
    tamale = world.add(ObjectThing(
        id="tamale",
        label="tamale",
        phrase="a warm tamale wrapped in corn husks",
        owner="family",
        location=params.setting,
        visible=False,
        transparent=False,
    ))
    clue = world.add(ObjectThing(
        id="transparent_container",
        label="transparent container",
        phrase="a clear container that could be seen through",
        location=params.setting,
        visible=True,
        transparent=True,
    ))

    world.facts.update(hero=hero, suspect=suspect, culprit=culprit, tamale=tamale, clue=clue, params=params)

    world.say(f"{hero.name} was in {setting.place}, where dinner was supposed to be simple and warm.")
    world.say(f"On the table sat {tamale.phrase}, or at least it should have been there, because now it was gone.")
    world.para()
    world.say(f"{hero.name} looked at {suspect.name} and then at the empty plate.")
    world.say(f"On a shelf nearby, there was {clue.phrase}, and because it was transparent, {hero.name} could see exactly what was inside.")

    world.para()
    world.say(f"{hero.name} noticed a tiny smear of masa inside the clear container.")
    world.say(f"That clue did not prove everything, but it pointed toward someone who had touched the tamale and tried to hide the evidence.")
    world.say(f"At last, {culprit.name} lowered {culprit.pronoun('possessive')} eyes and told the truth: {culprit.name} had taken the tamale without asking.")

    world.para()
    world.say(f"{culprit.name} apologized and brought the tamale back.")
    world.say(f"{hero.name} did not shout; {hero.name} said that honesty mattered more than pretending nothing had happened.")
    world.say(f"Soon the family shared the tamale, and the clear container sat by the plate like a quiet witness that had helped solve the mystery.")

    world.facts["resolved"] = True
    world.facts["moral_value"] = "truth"

    prompts = [
        'Write a short child-friendly whodunit about a missing tamale and a transparent clue.',
        f"Tell a mystery story set in {setting.place} where {params.hero} solves what happened to a tamale.",
        "Write a gentle detective story that ends by showing the value of truth.",
    ]

    story_qa = [
        QAItem(
            question=f"What was missing from the table in {setting.place}?",
            answer="A warm tamale was missing from the table.",
        ),
        QAItem(
            question=f"What clue did {params.hero} notice that was transparent?",
            answer="The clue was a transparent container, so {0} could see inside it.".format(params.hero),
        ),
        QAItem(
            question=f"Who had taken the tamale?",
            answer=f"{params.culprit.name if hasattr(culprit, 'name') else params.culprit} had taken the tamale without asking.",
        ),
        QAItem(
            question=f"What moral value did the story show?",
            answer="The story showed that truth matters, because telling the truth helped solve the mystery and make things right.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does transparent mean?",
            answer="Transparent means you can see through it.",
        ),
        QAItem(
            question="What is a tamale?",
            answer="A tamale is a food made from masa, often wrapped in a corn husk and steamed.",
        ),
        QAItem(
            question="Why is telling the truth important?",
            answer="Telling the truth helps people solve problems, repair trust, and understand what really happened.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        attrs = []
        if isinstance(e, ObjectThing):
            attrs.append(f"transparent={e.transparent}")
            attrs.append(f"visible={e.visible}")
            if e.location:
                attrs.append(f"location={e.location}")
        else:
            attrs.append(f"role={e.role}")
        lines.append(f"  {e.id}: {type(e).__name__} " + " ".join(attrs))
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


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
    StoryParams("kitchen", "Mina", "parent", "tamale", "transparent_container", "sibling"),
    StoryParams("dining_room", "Theo", "sibling", "tamale", "transparent_container", "grandparent"),
    StoryParams("pantry", "Pia", "neighbor", "tamale", "transparent_container", "parent"),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show clue_visible/1.\n#show moral_value/1.\n"))
    return sorted(set((sym.name, tuple(a.string if a.type == 1 else a.name for a in sym.arguments)) for sym in model))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show clue_visible/1.\n#show moral_value/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show clue_visible/1.\n#show moral_value/1.\n"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.hero} / {p.setting} / tamale mystery"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

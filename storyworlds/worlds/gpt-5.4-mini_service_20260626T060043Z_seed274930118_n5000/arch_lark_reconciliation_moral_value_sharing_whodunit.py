#!/usr/bin/env python3
"""
A small whodunit-style storyworld about an arch, a lark, sharing, moral value,
and reconciliation.

Premise:
- In a quiet old garden with a stone arch, something goes missing before a small
  gathering.
- A lark, a shared basket, and a careful observer turn the story into a gentle
  mystery.
- The hidden cause is not villainy but misunderstanding, and the ending proves
  that the truth restores trust.

The world is intentionally compact and constraint-checked: only a few plausible
mystery variants are allowed, and each one has a clear reveal and a reconciled
ending.
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
    carried_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    missing: str
    culprit: str
    motive: str
    reveal_method: str
    resolution: str
    tags: set[str] = field(default_factory=set)


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "garden": Setting("the old garden", True, {"song", "berry", "note"}),
    "courtyard": Setting("the courtyard", True, {"song", "bell", "note"}),
    "greenhouse": Setting("the greenhouse", False, {"leaf", "note"}),
}

MYSTERIES = {
    "shared_basket": Mystery(
        id="shared_basket",
        clue="a basket with two handles but only one ribbon",
        missing="the berry tart",
        culprit="lark",
        motive="the lark wanted a bright crumb and then hid because it was startled",
        reveal_method="follow the crumbs under the arch",
        resolution="share the tart pieces fairly and forgive the sneaky peck",
        tags={"arch", "lark", "sharing", "reconciliation", "moral_value"},
    ),
    "borrowed_note": Mystery(
        id="borrowed_note",
        clue="a note that smelled like fennel and rain",
        missing="the apology note",
        culprit="lark",
        motive="the lark used the note to line its nest, not knowing it mattered",
        reveal_method="listen for the note fluttering in the arch",
        resolution="rewrite the note together and make peace",
        tags={"arch", "lark", "reconciliation", "moral_value"},
    ),
    "crumb_trail": Mystery(
        id="crumb_trail",
        clue="a trail of crumbs leading beneath the stone arch",
        missing="the shared seed cake",
        culprit="lark",
        motive="the lark was trying to carry a tiny bite to its chicks",
        reveal_method="watch the lark hop to the nest",
        resolution="split the cake and keep a plate for the birds",
        tags={"arch", "lark", "sharing", "reconciliation", "moral_value"},
    ),
}

CHARACTER_NAMES = ["Mina", "Iris", "Nico", "Pia", "Theo", "June"]
CHARACTER_TYPES = ["girl", "boy"]
OBSERVERS = ["the gardener", "the aunt", "the older brother", "the neighbor"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    observer: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.outdoors:
            lines.append(asp.fact("outdoors", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S, M) :- setting(S), mystery(M), tag(M, arch), tag(M, lark).
#show compatible/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid, m in MYSTERIES.items():
            if {"arch", "lark"}.issubset(m.tags):
                combos.append((sid, mid))
    return combos


def asp_verify() -> int:
    a = set(asp_compatible())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style arch and lark storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--observer", choices=OBSERVERS)
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
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHARACTER_NAMES)
    gender = args.gender or rng.choice(CHARACTER_TYPES)
    observer = args.observer or rng.choice(OBSERVERS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, observer=observer)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.name, params.gender, params.observer)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.hidden:
            parts.append("hidden=True")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(parts)}")
    return "\n".join(lines)


def tell(setting: Setting, mystery: Mystery, name: str, gender: str, observer: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    clue = world.add(Entity(id="clue", label="clue", phrase=mystery.clue))
    missing = world.add(Entity(id="missing", label=mystery.missing, phrase=mystery.missing, hidden=True))
    lark = world.add(Entity(id="lark", kind="character", type="bird", label="lark"))
    basket = world.add(Entity(id="basket", label="shared basket", phrase="the shared basket", plural=False))
    basket.meters["shared"] = 1.0

    world.facts.update(hero=hero, clue=clue, missing=missing, lark=lark, basket=basket,
                       mystery=mystery, setting=setting, observer=observer)

    world.say(f"{name} was the sort of child who noticed every small thing at {setting.place}.")
    world.say(f"That morning, a clue had been left behind: {mystery.clue}.")
    world.say(f"People in the garden whispered that something important was missing, and the {observer} looked worried.")

    world.para()
    if mystery.id == "shared_basket":
        world.say(f"The missing thing was {mystery.missing}, which had been meant to be shared.")
        world.say(f"{name} remembered the basket near the stone arch and the sweet smell of crumbs.")
        world.say(f"Then a little lark fluttered up to the arch and gave the whole puzzle a nervous, guilty look.")
    elif mystery.id == "borrowed_note":
        world.say(f"The missing thing was {mystery.missing}, and it mattered because it held a kind apology.")
        world.say(f"{name} saw the note clipped near the arch, then saw it was gone a moment later.")
        world.say(f"A lark hopped through the ivy as if it knew more than it meant to admit.")
    else:
        world.say(f"The missing thing was {mystery.missing}, taken from the shared plate before anyone could begin.")
        world.say(f"{name} followed a neat trail of crumbs under the arch, where a lark was pecking at the last sweet bits.")

    world.para()
    world.say(f"{name} did not accuse at once. Instead, {name} watched closely, the way a careful detective would.")
    world.say(f"The clue pointed toward the arch, and the arch pointed toward the lark.")
    world.say(f"When {name} looked again, the truth was gentler than a theft: the lark had taken the thing for a reason.")

    world.para()
    world.say(f"{mystery.motive.capitalize()}.")
    world.say(f"{name} understood that the wrong was real, but it was not meant cruelly.")
    world.say(f"So {name} spoke softly, and the {observer} listened too.")
    world.say(f"They decided to solve the trouble by naming the truth, sharing what remained, and making room for forgiveness.")
    world.say(f"At last, everyone agreed to {mystery.resolution}, and the uneasy feeling in the garden melted away.")
    world.say(f"Under the old arch, the lark stayed nearby, no longer chased, and the missing thing was no longer a secret.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a young child with an old arch and a lark, where a clue leads to a gentle reveal.',
        f"Tell a mystery story in {f['setting'].place} about {f['hero'].id}, a lark, and a missing shared item, ending in reconciliation.",
        f"Write a child-friendly detective story that shows the moral value of sharing and ends with forgiveness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    observer = f["observer"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who noticed the clue in {setting.place}?",
            answer=f"{hero.id} noticed the clue and paid attention instead of jumping to a quick accusation.",
        ),
        QAItem(
            question=f"What was the missing thing in the story?",
            answer=f"The missing thing was {mystery.missing}. It had been part of something meant to be shared.",
        ),
        QAItem(
            question=f"Why did the story feel like a whodunit?",
            answer=f"It felt like a whodunit because there was a missing thing, a clue, careful watching, and a reveal near the arch.",
        ),
        QAItem(
            question=f"How did {hero.id} and the {observer} solve the trouble?",
            answer=f"They spoke gently, found the reason the lark had taken it, and chose reconciliation instead of anger.",
        ),
        QAItem(
            question=f"What moral value did the story show?",
            answer="The story showed sharing and forgiveness. It taught that finding the truth can help people make peace.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an arch?",
            answer="An arch is a curved structure that can make a doorway or frame a path in a garden or building.",
        ),
        QAItem(
            question="What is a lark?",
            answer="A lark is a small bird that can hop, sing, and flutter quickly through grass and trees.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person use, enjoy, or receive something instead of keeping it all.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after a disagreement or mistake, so people can trust each other again.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good idea about how to treat others, such as being kind, honest, fair, or sharing.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_verify_wrapper() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify_wrapper())
    if args.asp:
        combos = asp_compatible()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for sid in SETTINGS:
            for mid in MYSTERIES:
                params = StoryParams(setting=sid, mystery=mid, name="Mina", gender="girl", observer="the gardener")
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

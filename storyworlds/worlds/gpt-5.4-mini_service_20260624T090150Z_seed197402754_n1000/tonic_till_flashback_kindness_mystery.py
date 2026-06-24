#!/usr/bin/env python3
"""
A tiny mystery storyworld about tonic, a till, a small kindness, and a clue
that only makes sense after a flashback.

Premise:
- A child notices a strange thing at a market stall.
- A bottle of tonic is missing, and the till drawer is open.
- The child follows small clues, remembers an earlier moment in a flashback,
  and discovers the "mystery" was actually a kind act.

The world is intentionally small and constraint-checked:
- There is exactly one clue chain.
- The "solution" depends on a remembered earlier event.
- The ending image proves the change in state: the tonic is returned, the till is
  closed, and the worried feeling turns into gratitude.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    openable: bool = False
    opened: bool = False
    filled: bool = False
    empty: bool = False
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "they" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little market"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ItemSpec:
    label: str
    phrase: str
    kind: str
    clue_word: str
    risky: bool = False


@dataclass
class StoryParams:
    place: str
    item: str
    helper: str
    hero_name: str
    hero_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        other.facts = dict(self.facts)
        return other


SETTINGS = {
    "market": Setting(place="the little market", indoors=True, affords={"browse", "carry"}),
    "stall": Setting(place="the herb stall", indoors=False, affords={"browse", "carry"}),
    "kitchen": Setting(place="the warm kitchen", indoors=True, affords={"mix", "carry"}),
}

ITEMS = {
    "tonic": ItemSpec(
        label="tonic",
        phrase="a small bottle of tonic",
        kind="tonic",
        clue_word="tonic",
        risky=True,
    ),
    "ledger": ItemSpec(
        label="till",
        phrase="the brass till",
        kind="till",
        clue_word="till",
        risky=False,
    ),
    "lantern": ItemSpec(
        label="lantern",
        phrase="a little lantern",
        kind="lantern",
        clue_word="light",
        risky=False,
    ),
}

PEOPLE = {
    "girl": ["Mina", "Tia", "Lena", "Nora", "Ivy"],
    "boy": ["Eli", "Milo", "Noah", "Theo", "Finn"],
}

HELPERS = ["kind aunt", "quiet clerk", "old gardener", "gentle baker"]


ASP_RULES = r"""
setting(market). setting(stall). setting(kitchen).
affords(market,browse). affords(market,carry).
affords(stall,browse). affords(stall,carry).
affords(kitchen,mix). affords(kitchen,carry).

item(tonic). item(ledger). item(lantern).
risky(tonic).
clue_word(tonic,tonic).
clue_word(ledger,till).
clue_word(lantern,light).

valid_place_item(P,I) :- affords(P,carry), item(I).
mystery_pair(P,I) :- valid_place_item(P,I), risky(I).
#show valid_place_item/2.
#show mystery_pair/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        if setting.indoors:
            lines.append(asp.fact("indoors", name))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", name, act))
    for name, spec in ITEMS.items():
        lines.append(asp.fact("item", name))
        if spec.risky:
            lines.append(asp.fact("risky", name))
        lines.append(asp.fact("clue_word", name, spec.clue_word))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_place_item/2.\n#show mystery_pair/2."))
    valid = set(asp.atoms(model, "valid_place_item"))
    mystery = set(asp.atoms(model, "mystery_pair"))
    py_valid = {(p, i) for p in SETTINGS for i in ITEMS if "carry" in SETTINGS[p].affords}
    py_mystery = {(p, i) for p in SETTINGS for i in ITEMS if ITEMS[i].risky and "carry" in SETTINGS[p].affords}
    if valid != py_valid or mystery != py_mystery:
        print("MISMATCH between ASP and Python.")
        print("only in asp valid:", sorted(valid - py_valid))
        print("only in py valid:", sorted(py_valid - valid))
        print("only in asp mystery:", sorted(mystery - py_mystery))
        print("only in py mystery:", sorted(py_mystery - mystery))
        return 1
    print(f"OK: ASP parity verified ({len(py_valid)} valid, {len(py_mystery)} mystery).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with tonic, till, flashback, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, i) for p in SETTINGS for i in ITEMS if "carry" in SETTINGS[p].affords]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.item and args.place and (args.place, args.item) not in combos:
        raise StoryError("That place cannot host that item in this storyworld.")
    if args.gender and args.gender not in PEOPLE:
        raise StoryError("Unknown gender choice.")
    place, item = rng.choice(sorted(combos))
    if args.place:
        place = args.place
    if args.item:
        item = args.item
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(PEOPLE[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, item=item, helper=helper, hero_name=name, hero_gender=gender)


def _hero_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    return "he", "him", "his"


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    item = ITEMS[params.item]
    subj, obj, poss = _hero_pronouns(params.hero_gender)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label=params.helper))
    tonic = world.add(Entity(id="tonic", type="tonic", label="tonic", phrase="a small bottle of tonic", owner=helper.id))
    till = world.add(Entity(id="till", type="till", label="till", phrase="the brass till", openable=True, opened=True))
    lantern = world.add(Entity(id="lantern", type="lantern", label="lantern", phrase="a little lantern"))

    world.facts.update(hero=hero, helper=helper, tonic=tonic, till=till, lantern=lantern, item=item, subj=subj, obj=obj, poss=poss)

    world.say(f"{hero.id} came to {world.setting.place} because a small mystery had been bothering {obj}.")
    world.say(f"On the counter, {item.phrase} seemed to be the clue, and the brass till sat open beside it.")
    world.say(f"{hero.id} loved little puzzles, so {subj} looked carefully instead of guessing too fast.")

    world.para()
    world.say(f"Then {hero.id} noticed a faint shine near the floor.")
    world.say(f"{subj.capitalize()} remembered a flashback: earlier, {helper.label if helper.label else params.helper} had set the tonic down while helping an old customer, and a kind smile had distracted everyone.")
    world.say(f"In that flashback, the helper had said, \"I will keep it safe till the right person comes back.\"")

    world.para()
    world.say(f"That was the part the mystery needed.")
    world.say(f"The tonic had not been stolen at all; it had been moved for kindness.")
    world.say(f"{hero.id} found it tucked behind the lantern, right where the helper could reach it again.")
    world.say(f"{subj.capitalize()} closed the till, brought back the tonic, and thanked {helper.label} for being so kind.")

    world.para()
    world.say(f"By the end, the little market felt calm again.")
    world.say(f"The tonic stood on the counter, the till was shut, and the strange feeling turned into a warm, solved smile.")

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    return [
        f"Write a short mystery story for a young child about {hero.id} and a {item.label}.",
        f"Tell a gentle story with a flashback and a kindness clue that explains the missing {item.label}.",
        f"Write a simple mystery where the words tonic and till appear and the ending feels solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    subj, obj, poss = f["subj"], f["obj"], f["poss"]
    return [
        QAItem(
            question=f"What mystery was {hero.id} trying to solve at {world.setting.place}?",
            answer=f"{hero.id} was trying to solve why the {item.label} looked strange beside the till. The answer turned out to be kind, not scary.",
        ),
        QAItem(
            question=f"What did the flashback show about {helper.label if helper.label else 'the helper'} and the tonic?",
            answer=f"The flashback showed that the helper had set the tonic down carefully while helping an old customer, then promised to keep it safe till the right person came back.",
        ),
        QAItem(
            question=f"Why did the story end happily for {hero.id}?",
            answer=f"It ended happily because {hero.id} found the tonic, closed the till, and understood that the mystery was really an act of kindness.",
        ),
        QAItem(
            question=f"How did {hero.id} act when the clues appeared?",
            answer=f"{subj.capitalize()} looked carefully instead of guessing too fast, which helped {obj} notice the flashback clue and solve the mystery.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tonic?",
            answer="Tonic is a small drink or mixture people may keep in a bottle. In stories, it can be a clue or a special thing to protect.",
        ),
        QAItem(
            question="What is a till?",
            answer="A till is a cash drawer or box where a shopkeeper keeps money at a stall or in a shop.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a story moment that goes back to something that happened earlier, so the reader can understand a clue.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means doing something gentle and helpful for someone else, like keeping their tonic safe until they come back.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = [f"type={e.type}"]
        if e.openable:
            bits.append(f"opened={e.opened}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id}: " + " ".join(bits))
    return "\n".join(lines)


CURATED = [
    StoryParams(place="market", item="tonic", helper="kind aunt", hero_name="Mina", hero_gender="girl"),
    StoryParams(place="stall", item="tonic", helper="quiet clerk", hero_name="Eli", hero_gender="boy"),
    StoryParams(place="kitchen", item="tonic", helper="old gardener", hero_name="Nora", hero_gender="girl"),
]


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_place_item/2.\n#show mystery_pair/2."))
    return sorted(set(asp.atoms(model, "valid_place_item")))


def asp_valid_mysteries() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show mystery_pair/2."))
    return sorted(set(asp.atoms(model, "mystery_pair")))


def build_story_params_from_combo(combo: tuple[str, str], rng: random.Random) -> StoryParams:
    place, item = combo
    gender = rng.choice(["girl", "boy"])
    return StoryParams(place=place, item=item, helper=rng.choice(HELPERS), hero_name=rng.choice(PEOPLE[gender]), hero_gender=gender)


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
        print(asp_program("#show valid_place_item/2.\n#show mystery_pair/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        valid = asp_valid_combos()
        myst = asp_valid_mysteries()
        print(f"{len(valid)} valid place-item combos; {len(myst)} mystery pairs")
        for p, i in valid:
            print(f"{p} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i - 1
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
            header = f"### {p.hero_name}: {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/negotiate_precise_sirloin_reconciliation_rhyme_flashback_detective.py
========================================================================================

A small detective-story world about a precise missing sirloin, a tense
negotiation, a flashback clue, and a reconciliation ending in rhyme.

The premise:
- A careful detective investigates why a prized sirloin is missing.
- The main tension is between a chef and a guest who disagree about what
  happened and how to make it right.
- A flashback reveals the sirloin was moved, not stolen.
- The ending reconciles the characters after they negotiate a fair fix.

The story remains state-driven: meters track physical placement and evidence,
memes track suspicion, stress, trust, and relief.
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
    caretakers: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "chefwoman"}
        male = {"man", "boy", "father", "chefman", "detective"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the corner diner"
    time: str = "late evening"


@dataclass
class Clue:
    kind: str
    precise_phrase: str
    solution: str
    rhyme: str
    flashback_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    detective: str
    chef: str
    guest: str
    seed: Optional[int] = None


SETTINGS = {
    "diner": Setting(place="the corner diner", time="late evening"),
    "bistro": Setting(place="the tiny bistro", time="rainy dusk"),
    "kitchen": Setting(place="the back kitchen", time="busy afternoon"),
}

CLUES = {
    "sirloin": Clue(
        kind="sirloin",
        precise_phrase="a precise sirloin",
        solution="the sirloin was moved to rest on the warming tray",
        rhyme="The steak did not take; it only had to wait.",
        flashback_line="Earlier, the cook had slid the sirloin aside to make room for a pie.",
        tags={"sirloin", "food", "missing", "move", "rhyme", "flashback"},
    ),
}

DETECTIVE_NAMES = ["Mira", "Noel", "Ivy", "June", "Evan", "Cole"]
CHEF_NAMES = ["Chef Lina", "Chef Otto", "Chef Sam", "Chef Ruth"]
GUEST_NAMES = ["Mr. Pike", "Ms. Vale", "Aunt Nia", "Mr. Reed"]


class World:
    def __init__(self, setting: Setting, clue: Clue) -> None:
        self.setting = setting
        self.clue = clue
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone = World(self.setting, self.clue)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    clue = CLUES[params.clue]
    world = World(setting, clue)

    detective = world.add(Entity(
        id=params.detective,
        kind="character",
        type="detective",
        label="the detective",
    ))
    chef = world.add(Entity(
        id=params.chef,
        kind="character",
        type="chefman" if params.chef.startswith("Chef") and "Ruth" not in params.chef and "Lina" not in params.chef else "chefwoman",
        label=params.chef,
    ))
    guest = world.add(Entity(
        id=params.guest,
        kind="character",
        type="man" if params.guest.startswith("Mr.") else "woman",
        label=params.guest,
    ))
    steak = world.add(Entity(
        id="sirloin",
        kind="thing",
        type="sirloin",
        label="sirloin",
        phrase="a precise sirloin steak",
        owner=chef.id,
        caretakers=[chef.id],
    ))
    tray = world.add(Entity(
        id="tray",
        kind="thing",
        type="tray",
        label="warming tray",
        phrase="a warming tray",
        owner=chef.id,
    ))
    world.facts.update(detective=detective, chef=chef, guest=guest, steak=steak, tray=tray)
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    det: Entity = f["detective"]
    chef: Entity = f["chef"]
    guest: Entity = f["guest"]
    steak: Entity = f["steak"]
    world.say(f"{det.id} was a careful detective who noticed every crumb and every pause in a room.")
    world.say(
        f"At {world.setting.place}, {chef.label} had prepared {steak.phrase}, "
        f"and {guest.label} had promised to wait until dinner was ready."
    )
    _add_meme(det, "duty", 1)
    _add_meme(chef, "pride", 1)
    _add_meme(guest, "hunger", 1)


def ask_about_missing(world: World) -> None:
    f = world.facts
    det: Entity = f["detective"]
    chef: Entity = f["chef"]
    steak: Entity = f["steak"]
    _add_meme(det, "curiosity", 1)
    _add_meme(chef, "stress", 1)
    world.say(
        f"Then {det.id} leaned in and asked why {steak.label} was not on the plate yet."
    )
    world.say(
        f"{chef.label} frowned, because {steak.label} had been set down with very precise care."
    )


def tense_denial(world: World) -> None:
    f = world.facts
    chef: Entity = f["chef"]
    guest: Entity = f["guest"]
    detective: Entity = f["detective"]
    _add_meme(chef, "suspicion", 1)
    _add_meme(guest, "worry", 1)
    _add_meme(detective, "suspicion", 1)
    world.say(
        f"{guest.label} said someone must have taken it, but {chef.label} shook "
        f"{chef.pronoun('possessive')} head and looked hurt."
    )
    world.say(
        f"{detective.id} kept the peace and said the best answer would be a precise one."
    )


def flashback(world: World) -> None:
    f = world.facts
    chef: Entity = f["chef"]
    detective: Entity = f["detective"]
    steak: Entity = f["steak"]
    if "flashback" in world.fired:
        return
    world.fired.add("flashback")
    _add_meme(detective, "insight", 1)
    steak.meters["hidden"] = 1
    world.para()
    world.say(
        f"In a flashback, {chef.label} remembered the earlier rush: {CLUES['sirloin'].flashback_line}"
    )
    world.say(
        f"That meant the sirloin had not vanished at all; it had only changed places."
    )


def negotiate_fix(world: World) -> None:
    f = world.facts
    detective: Entity = f["detective"]
    chef: Entity = f["chef"]
    guest: Entity = f["guest"]
    steak: Entity = f["steak"]
    tray: Entity = f["tray"]
    steak.meters["hidden"] = 0
    steak.meters["served"] = 1
    tray.meters["warm"] = 1
    _add_meme(chef, "relief", 1)
    _add_meme(guest, "relief", 1)
    _add_meme(detective, "confidence", 1)
    world.say(
        f"{detective.id} suggested they negotiate instead of blame. {chef.label} would bring "
        f"the sirloin from the warming tray, and {guest.label} would wait one more minute."
    )
    world.say(
        f"It was a precise bargain: no shouting, no shame, only a fair return to the table."
    )


def reconciliation(world: World) -> None:
    f = world.facts
    chef: Entity = f["chef"]
    guest: Entity = f["guest"]
    detective: Entity = f["detective"]
    steak: Entity = f["steak"]
    _add_meme(chef, "trust", 1)
    _add_meme(guest, "trust", 1)
    _add_meme(detective, "satisfaction", 1)
    world.say(
        f"Then came reconciliation. {chef.label} placed {steak.label} on the plate, and "
        f"{guest.label} apologized for jumping to conclusions."
    )
    world.say(
        f"{detective.id} smiled, because the case had been solved by calm words instead of a loud storm."
    )


def rhyme_ending(world: World) -> None:
    f = world.facts
    detective: Entity = f["detective"]
    chef: Entity = f["chef"]
    guest: Entity = f["guest"]
    steak: Entity = f["steak"]
    _add_meme(detective, "joy", 1)
    _add_meme(chef, "joy", 1)
    _add_meme(guest, "joy", 1)
    steak.meters["served"] = 1
    world.say(
        f"As they ate, {detective.id} recited a little rhyme: "
        f"\"{world.clue.rhyme}\""
    )
    world.say(
        f"The three of them laughed together, and the precise sirloin finally rested where it belonged."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    narrate_setup(world)
    world.para()
    ask_about_missing(world)
    tense_denial(world)
    flashback(world)
    world.para()
    negotiate_fix(world)
    reconciliation(world)
    rhyme_ending(world)
    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(place, clue) for place in SETTINGS for clue in CLUES]


@dataclass
class ASPModel:
    pass


ASP_RULES = r"""
setting(diner).
setting(bistro).
setting(kitchen).

clue(sirloin).

valid(P, C) :- setting(P), clue(C).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: negotiate a precise sirloin reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--detective", choices=DETECTIVE_NAMES)
    ap.add_argument("--chef", choices=CHEF_NAMES)
    ap.add_argument("--guest", choices=GUEST_NAMES)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue = rng.choice(combos)
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    chef = args.chef or rng.choice(CHEF_NAMES)
    guest = args.guest or rng.choice(GUEST_NAMES)
    if detective == chef or detective == guest or chef == guest:
        raise StoryError("Please choose different names for detective, chef, and guest.")
    return StoryParams(place=place, clue=clue, detective=detective, chef=chef, guest=guest)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short detective story about {f['detective'].id} and a precise missing sirloin.",
        f"Tell a child-friendly mystery where {f['chef'].label} and {f['guest'].label} negotiate after a misunderstanding.",
        f"Write a story with a flashback, a rhyme, and a reconciliation ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det: Entity = f["detective"]
    chef: Entity = f["chef"]
    guest: Entity = f["guest"]
    steak: Entity = f["steak"]
    return [
        QAItem(
            question=f"Who solved the mystery about the missing {steak.label}?",
            answer=f"{det.id} solved it by asking careful questions and noticing the flashback clue.",
        ),
        QAItem(
            question=f"Why did {chef.label} stop worrying about the {steak.label}?",
            answer="Because the flashback showed that the sirloin had been moved to the warming tray, not stolen.",
        ),
        QAItem(
            question=f"What changed when {chef.label} and {guest.label} reconciled?",
            answer="They stopped blaming each other, negotiated a fair wait, and ended the night smiling together.",
        ),
        QAItem(
            question=f"What did the detective mean by a precise bargain?",
            answer="It meant they agreed on one clear plan: bring the sirloin back from the warming tray and let dinner continue calmly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues, asks questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a reconciliation?",
            answer="Reconciliation is when people stop arguing and make peace again.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little pattern of words that sound alike at the end.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something from earlier.",
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="diner", clue="sirloin", detective="Mira", chef="Chef Lina", guest="Mr. Pike"),
    StoryParams(place="bistro", clue="sirloin", detective="Noel", chef="Chef Otto", guest="Ms. Vale"),
    StoryParams(place="kitchen", clue="sirloin", detective="Ivy", chef="Chef Ruth", guest="Aunt Nia"),
]


def generate(params: StoryParams) -> StorySample:
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue) combos:\n")
        for place, clue in combos:
            print(f"  {place:10} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

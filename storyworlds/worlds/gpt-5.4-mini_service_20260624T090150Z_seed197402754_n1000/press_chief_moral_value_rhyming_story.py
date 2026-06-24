#!/usr/bin/env python3
"""
A small rhyming storyworld about a press and a chief, where a moral value is
learned through a concrete simulated change in the world.

The story premise:
- A press helps make posters, pages, or signs.
- A chief wants the work to be fair, neat, and honest.
- A small problem appears: the press is used in a rushed or selfish way.
- The chief teaches a moral value: share fairly, tell the truth, or use care.
- The ending proves the change in state and feeling.

This file is self-contained and follows the Storyweavers storyworld contract.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"chief", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Location:
    id: str
    phrase: str
    place_type: str = "hall"
    orderly: bool = True


@dataclass
class PressKind:
    id: str
    label: str
    verb: str
    output: str
    sound: str
    mess: str
    is_small: bool = True
    rhyme_end: str = ""


@dataclass
class Moral:
    id: str
    label: str
    lesson: str
    fix_phrase: str
    closing_image: str
    rhyme_word: str


@dataclass
class World:
    location: Location
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    mood: str = "calm"
    disorder: float = 0.0
    truth: float = 1.0

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
        w = World(self.location)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.mood = self.mood
        w.disorder = self.disorder
        w.truth = self.truth
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
LOCATIONS = {
    "print_shop": Location(id="print_shop", phrase="the print shop", place_type="shop", orderly=True),
    "town_hall": Location(id="town_hall", phrase="the town hall", place_type="hall", orderly=True),
    "news_room": Location(id="news_room", phrase="the news room", place_type="room", orderly=True),
}

PRESSES = {
    "ink_press": PressKind(
        id="ink_press",
        label="ink press",
        verb="press",
        output="fresh flyers",
        sound="clackety-clack",
        mess="inky",
        rhyme_end="best",
    ),
    "card_press": PressKind(
        id="card_press",
        label="card press",
        verb="press",
        output="bright cards",
        sound="tap-tap-tap",
        mess="smudged",
        rhyme_end="neat",
    ),
    "stamp_press": PressKind(
        id="stamp_press",
        label="stamp press",
        verb="stamp",
        output="marked signs",
        sound="thump-thump",
        mess="crooked",
        rhyme_end="clean",
    ),
}

MORALS = {
    "fair_share": Moral(
        id="fair_share",
        label="fair share",
        lesson="share the work and let each helper have a turn",
        fix_phrase="divide the pages and take turns with care",
        closing_image="the pages came out even and bright, side by side in the light",
        rhyme_word="care",
    ),
    "truth": Moral(
        id="truth",
        label="truth",
        lesson="tell the truth right away, even when it feels hard",
        fix_phrase="admit the mistake and set the record straight",
        closing_image="the words came out honest and clear, with no need for fear",
        rhyme_word="true",
    ),
    "care": Moral(
        id="care",
        label="care",
        lesson="slow down and handle the work with care",
        fix_phrase="wipe the press and use it with care",
        closing_image="the ink stayed neat and the paper shone sweet",
        rhyme_word="near",
    ),
}

CHIEF_NAMES = ["Chief Nora", "Chief Ben", "Chief Mira", "Chief Leo"]
HELPER_NAMES = ["Ari", "Tess", "Milo", "June", "Owen", "Zia"]
TRAITS = ["kind", "bold", "busy", "keen", "calm"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    location: str
    press: str
    moral: str
    chief_name: str
    helper_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid if a press, a chief, and a moral value can form a conflict
% and a fair fix that actually changes the world state.
valid(L, P, M) :- location(L), press(P), moral(M),
                  presses_at(L, P), has_chief(L), teaches(M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if loc.orderly:
            lines.append(asp.fact("orderly", lid))
    for pid, p in PRESSES.items():
        lines.append(asp.fact("press", pid))
        lines.append(asp.fact("press_sound", pid, p.sound))
        lines.append(asp.fact("press_mess", pid, p.mess))
    for mid, m in MORALS.items():
        lines.append(asp.fact("moral", mid))
        lines.append(asp.fact("teaches", mid))
    for lid in LOCATIONS:
        for pid in PRESSES:
            lines.append(asp.fact("presses_at", lid, pid))
            lines.append(asp.fact("has_chief", lid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    py = set((loc, press, moral) for loc in LOCATIONS for press in PRESSES for moral in MORALS)
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches python gate ({len(cl)} combos).")
        return 0
    print("MISMATCH between ASP and python gate.")
    print("only in ASP:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def _ripple_disorder(world: World) -> list[str]:
    out = []
    press = world.facts["press_obj"]
    if press.meters.get("used", 0) >= 1 and world.disorder >= 1.0:
        sig = ("mess", press.id)
        if sig not in world.fired:
            world.fired.add(sig)
            press.meters["mess"] = press.meters.get("mess", 0) + 1
            out.append(f"The {press.label} got smudged in the rush.")
    return out

def _ripple_mood(world: World) -> list[str]:
    out = []
    chief = world.facts["chief_obj"]
    if world.disorder >= 1.0 and chief.memes.get("worry", 0) < 1.0:
        sig = ("worry", chief.id)
        if sig not in world.fired:
            world.fired.add(sig)
            chief.memes["worry"] = 1.0
            chief.memes["resolve"] = 1.0
            out.append(f"{chief.id} frowned, then chose a better way.")
    return out

RULES = [_ripple_disorder, _ripple_mood]

def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            s = rule(world)
            if s:
                produced.extend(s)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"

def tell(location: Location, press: PressKind, moral: Moral, chief_name: str, helper_name: str, trait: str) -> World:
    world = World(location)
    chief = world.add(Entity(id=chief_name, kind="character", type="chief", label=chief_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="child", label=helper_name))
    press_ent = world.add(Entity(id="press", type="press", label=press.label, phrase=press.label))
    world.facts.update(location=location, press=press, moral=moral, chief_obj=chief, helper_obj=helper, press_obj=press_ent)

    world.say(f"At {location.phrase}, {chief_name} kept a steady pace, with a smile that shone in the sun.")
    world.say(f"{helper_name} was {trait} and quick, and loved the {press.label} sound: {press.sound} and fun.")
    world.say(f"Together they worked on bright new signs, to make the town's pages run.")

    world.para()
    world.say(f"But {helper_name} rushed the job too fast, and tried to use the {press.label} alone.")
    helper.meters["used_press"] = 1
    world.disorder = 1.0
    world.truth = 0.5
    propagate(world, narrate=True)

    world.para()
    world.say(f"{chief_name} said, \"A good deed grows when we share, and the fair way helps us all.\"")
    world.say(f"\"{moral.fix_phrase}, and then the work will stand up tall.\"")
    helper.memes["remorse"] = 1.0
    helper.memes["learned"] = 1.0
    world.disorder = 0.0
    world.truth = 1.0
    press_ent.meters["used"] = 1
    press_ent.meters["clean"] = 1
    world.say(f"They took turns with the {press.label}, slow and bright, and the papers came out small and neat.")
    world.say(f"{moral.closing_image}, and the whole room felt sweet.")

    world.facts["final_moral"] = moral
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for children about a {f["press"].label} and a chief.',
        f"Tell a gentle tale where {f['chief_obj'].id} teaches a moral value after a mistake with the press.",
        f"Write a simple story with a clear problem, a fair fix, and a happy rhyme at the end.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    chief = f["chief_obj"]
    helper = f["helper_obj"]
    press = f["press"]
    moral = f["moral"]
    return [
        QAItem(
            question=f"Who kept the work fair at {world.location.phrase}?",
            answer=f"{chief.id} kept the work fair and helped {helper.id} slow down.",
        ),
        QAItem(
            question=f"What went wrong when {helper.id} used the {press.label} too fast?",
            answer=f"The work got rushed and messy, so the press became smudged and the town did not get neat pages at first.",
        ),
        QAItem(
            question=f"What moral value did {chief.id} teach in the story?",
            answer=f"{chief.id} taught {moral.label}: {moral.lesson}.",
        ),
        QAItem(
            question=f"How did the story end after the lesson?",
            answer=f"They took turns with the {press.label}, and the pages came out neat, bright, and ready to share.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a press?", answer="A press is a machine or tool that helps make things by pushing, stamping, or printing them onto paper or another surface."),
        QAItem(question="What does a chief do?", answer="A chief is a leader who helps guide a group and make fair choices."),
        QAItem(question="What does it mean to share?", answer="To share means to let other people use something or take a turn with you."),
        QAItem(question="What is a moral value?", answer="A moral value is a good way of acting, like being fair, honest, kind, or careful."),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"disorder={world.disorder} truth={world.truth}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: a press, a chief, and a moral value.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--press", choices=PRESSES)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--chief-name", choices=CHIEF_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(l, p, m) for l in LOCATIONS for p in PRESSES for m in MORALS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.location:
        combos = [c for c in combos if c[0] == args.location]
    if args.press:
        combos = [c for c in combos if c[1] == args.press]
    if args.moral:
        combos = [c for c in combos if c[2] == args.moral]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    loc, press, moral = rng.choice(sorted(combos))
    return StoryParams(
        location=loc,
        press=press,
        moral=moral,
        chief_name=args.chief_name or rng.choice(CHIEF_NAMES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(LOCATIONS[params.location], PRESSES[params.press], MORALS[params.moral],
                 params.chief_name, params.helper_name, params.trait)
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
    StoryParams(location="print_shop", press="ink_press", moral="fair_share", chief_name="Chief Nora", helper_name="Ari", trait="kind"),
    StoryParams(location="town_hall", press="card_press", moral="truth", chief_name="Chief Ben", helper_name="Tess", trait="busy"),
    StoryParams(location="news_room", press="stamp_press", moral="care", chief_name="Chief Mira", helper_name="Milo", trait="keen"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid triples:")
        for v in vals:
            print(" ", v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.chief_name}: {p.press} at {p.location} (moral: {p.moral})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

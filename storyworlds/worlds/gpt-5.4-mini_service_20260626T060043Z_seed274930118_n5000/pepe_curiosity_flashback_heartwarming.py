#!/usr/bin/env python3
"""
A small heartwarming storyworld about Pepe's curiosity and a gentle flashback.

Premise:
- Pepe is a little child/bunny? Keep it concrete and warm.
- A curious question leads Pepe to a memory about a kindness from the past.
- The remembered clue helps Pepe make a caring choice now.

World model:
- Physical meters track carried items, found objects, and small environmental state.
- Emotional memes track curiosity, worry, warmth, and relief.
- A flashback is a stateful recall event, not just a decorative line.

The script intentionally keeps the domain small and constraint-driven:
- Curiosity can uncover a tucked-away keepsake or clue.
- Flashback can reveal who helped whom and why the current choice matters.
- The ending proves a changed state: a repaired object, a shared treat, or a
  reunited keepsake that makes someone feel better.

Includes an ASP twin for the reasonableness gate and a verification mode.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Core tuning
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities / world state
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    placed_in: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"lost": 0.0, "fixed": 0.0, "shared": 0.0, "warm": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "love": 0.0, "flashback": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    cozy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class LostThing:
    id: str
    label: str
    phrase: str
    where: str
    can_be_found: bool = True
    sentimental: bool = True


@dataclass
class Reminder:
    id: str
    label: str
    phrase: str
    helps_with: str
    warm_clue: str


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = []
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": Place("the kitchen", indoors=True, cozy=True, affords={"search", "share"}),
    "garden": Place("the garden", indoors=False, cozy=True, affords={"search", "share"}),
    "porch": Place("the porch", indoors=False, cozy=True, affords={"search", "share"}),
}

LOST_THINGS = {
    "button": LostThing("button", "button", "a small red button", "basket"),
    "bell": LostThing("bell", "bell", "a tiny brass bell", "windowsill"),
    "scarf": LostThing("scarf", "scarf", "a soft blue scarf", "chair"),
}

REMINDERS = {
    "cookie": Reminder("cookie", "cookie", "a warm cookie", "sharing", "crumbs"),
    "blanket": Reminder("blanket", "blanket", "a quilted blanket", "comfort", "soft hands"),
    "drawing": Reminder("drawing", "drawing", "a crayon drawing", "memory", "a smiling note"),
}

NAMES = ["Pepe", "Milo", "Nina", "Luna", "Ollie", "Tess", "Benny", "Iris"]
KINDS = ["boy", "girl"]

# The required seed words.
FEATURE_WORDS = ["pepe", "curiosity", "flashback"]


@dataclass
class StoryParams:
    place: str
    lost_thing: str
    reminder: str
    name: str = "Pepe"
    kind: str = "boy"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers for narration / reasoning
# ---------------------------------------------------------------------------

def place_detail(place: Place) -> str:
    if place.indoors:
        return f"The {place.name.removeprefix('the ')} felt cozy and still."
    return f"The {place.name.removeprefix('the ')} felt soft with wind and quiet light."


def reasonableness(place: Place, lost: LostThing, reminder: Reminder) -> bool:
    # Curiosity can lead to searching anywhere. The story is valid when the lost
    # thing can plausibly be found in the chosen place and the reminder helps.
    return lost.can_be_found and reminder.helps_with in {"sharing", "comfort", "memory"}


def predict(world: World, hero: Entity, lost: LostThing, reminder: Reminder) -> dict:
    sim = world.copy()
    _search_for_lost(sim, sim.get(hero.id), lost, narrate=False)
    _remember(sim, sim.get(hero.id), reminder, narrate=False)
    return {
        "found": bool(sim.facts.get("found")),
        "warmth": hero.memes["love"] + sim.get(hero.id).meters["warm"] + 1.0,
    }


def _search_for_lost(world: World, hero: Entity, lost: LostThing, narrate: bool = True) -> None:
    if world.facts.get("found"):
        return
    if world.place.name.endswith(lost.where) or lost.where in {"basket", "chair", "windowsill"}:
        hero.memes["curiosity"] += 1
        hero.meters["lost"] += 1
        world.facts["found"] = True
        world.facts["found_thing"] = lost.id
        if narrate:
            world.say(
                f"{hero.id} followed {hero.pronoun('possessive')} curious thought and looked near the {lost.where}."
            )
            world.say(f"At last, {hero.id} found {lost.phrase} tucked safely away.")


def _remember(world: World, hero: Entity, reminder: Reminder, narrate: bool = True) -> None:
    hero.memes["flashback"] += 1
    world.facts["flashback"] = reminder.id
    if narrate:
        world.say(
            f"That little sight brought a gentle flashback: {hero.id} remembered {reminder.phrase} and the kind moment it carried."
        )


def _warm_choice(world: World, hero: Entity, reminder: Reminder, lost: LostThing, narrate: bool = True) -> None:
    hero.memes["love"] += 1
    hero.memes["relief"] += 1
    hero.meters["warm"] += 1
    world.facts["shared"] = True
    if narrate:
        world.say(
            f"{hero.id} chose to share {reminder.phrase} with a smile, because the memory made {hero.pronoun('object')} feel brave and gentle."
        )
        world.say(
            f"Then {hero.id} set {lost.phrase} back where it belonged, and the room felt warm again."
        )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(place: Place, lost: LostThing, reminder: Reminder, name: str = "Pepe", kind: str = "boy") -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=kind))
    keeper = world.add(Entity(id="Caretaker", kind="character", type="mother", label="Mom"))
    thing = world.add(Entity(id=lost.id, type=lost.label, label=lost.label, phrase=lost.phrase, caretaker=keeper.id))
    warm = world.add(Entity(id=reminder.id, type=reminder.label, label=reminder.label, phrase=reminder.phrase, owner=hero.id))

    # Act 1: gentle setup.
    world.say(f"{hero.id} was a little {kind} with a very curious heart.")
    world.say(f"{hero.id} loved wondering about tiny things, and {place_detail(place)}")
    world.say(f"One day, {hero.id} noticed that {thing.phrase} was missing.")
    hero.memes["worry"] += 1

    # Act 2: curiosity opens the search and the flashback.
    world.say(f"{hero.id}'s curiosity grew bigger than the worry, so {hero.pronoun('subject')} began to look around.")
    _search_for_lost(world, hero, lost, narrate=True)
    _remember(world, hero, reminder, narrate=True)

    # If the memory teaches kindness, resolve through sharing and restoring.
    world.say(f"The remembered feeling nudged {hero.id} toward a kind choice.")
    _warm_choice(world, hero, warm, thing, narrate=True)

    # Act 3: ending image with visible change.
    world.say(
        f"In the end, {hero.id} felt lighter, the missing thing was safe again, and the little room seemed to glow with the warmth of being cared for."
    )

    world.facts.update(
        hero=hero,
        keeper=keeper,
        lost=thing,
        reminder=warm,
        place=place,
        found=bool(world.facts.get("found")),
        shared=bool(world.facts.get("shared")),
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    lost: Entity = f["lost"]
    return [
        f'Write a heartwarming story for a young child about {hero.id}, curiosity, and a missing {lost.label}.',
        f"Tell a gentle tale where {hero.id} notices something lost, has a flashback, and makes a kind choice.",
        f'Write a short story that uses the words "{hero.id}", "curious", and "flashback" and ends warmly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    keeper: Entity = f["keeper"]
    lost: Entity = f["lost"]
    reminder: Entity = f["reminder"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type} with a curious heart.",
        ),
        QAItem(
            question=f"What was missing at the start?",
            answer=f"{lost.phrase} was missing at the start, so {hero.id} went looking for it.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered {reminder.phrase}, which brought back a gentle feeling and helped make the choice feel warm.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} sharing kindly, putting {lost.phrase} back, and feeling lighter and happy.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "pepe": [
        ("Who is Pepe in this storyworld?", "Pepe is the name of the little main character in this storyworld."),
    ],
    "curiosity": [
        ("What is curiosity?", "Curiosity is the feeling that makes someone want to learn, look, and ask questions."),
    ],
    "flashback": [
        ("What is a flashback?", "A flashback is when a story briefly shows something from the past that a character remembers."),
    ],
    "sharing": [
        ("Why is sharing kind?", "Sharing is kind because it lets someone else enjoy something too, and it can make both people feel cared for."),
    ],
    "comfort": [
        ("What does comfort mean?", "Comfort means a feeling that helps someone feel safe, calm, and cared for."),
    ],
    "memory": [
        ("Why can memories help people?", "Memories can help people because they remind them of what mattered before and what to do now."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["pepe"])
    out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["curiosity"])
    out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["flashback"])
    f = world.facts
    reminder: Entity = f["reminder"]
    if reminder.label in {"cookie", "blanket", "drawing"}:
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[REMINDER_TOPIC(reminder.label)])
    return out


def REMINDER_TOPIC(label: str) -> str:
    if label == "cookie":
        return "sharing"
    if label == "blanket":
        return "comfort"
    return "memory"


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_valid(P) :- place(P).
lost_ok(L) :- lost(L).
reminder_ok(R) :- reminder(R).

valid_story(P, L, R) :- place_valid(P), lost_ok(L), reminder_ok(R), can_be_found(L), helps(R, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for lid, l in LOST_THINGS.items():
        lines.append(asp.fact("lost", lid))
        if l.can_be_found:
            lines.append(asp.fact("can_be_found", lid))
    for rid, r in REMINDERS.items():
        lines.append(asp.fact("reminder", rid))
        lines.append(asp.fact("helps", rid, r.helps_with))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_stories() -> list[tuple]:
    out = []
    for p in PLACES:
        for l in LOST_THINGS:
            for r in REMINDERS:
                if reasonableness(PLACES[p], LOST_THINGS[l], REMINDERS[r]):
                    out.append((p, l, r))
    return sorted(out)


def asp_verify() -> int:
    import asp
    py = set(python_valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python reasonableness ({len(py)} stories).")
        return 0
    print("MISMATCH between Python and clingo:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about Pepe's curiosity and a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--lost-thing", choices=LOST_THINGS)
    ap.add_argument("--reminder", choices=REMINDERS)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
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
    place = args.place or rng.choice(list(PLACES))
    lost = args.lost_thing or rng.choice(list(LOST_THINGS))
    reminder = args.reminder or rng.choice(list(REMINDERS))
    if not reasonableness(PLACES[place], LOST_THINGS[lost], REMINDERS[reminder]):
        raise StoryError("This combination does not make a believable heartwarming story.")
    kind = args.kind or rng.choice(KINDS)
    name = args.name or ("Pepe" if rng.random() < 0.7 else rng.choice(NAMES))
    return StoryParams(place=place, lost_thing=lost, reminder=reminder, name=name, kind=kind)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], LOST_THINGS[params.lost_thing], REMINDERS[params.reminder], params.name, params.kind)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", lost_thing="button", reminder="cookie", name="Pepe", kind="boy"),
    StoryParams(place="garden", lost_thing="bell", reminder="blanket", name="Pepe", kind="boy"),
    StoryParams(place="porch", lost_thing="scarf", reminder="drawing", name="Pepe", kind="boy"),
]


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
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible story combinations:\n")
        for p, l, r in triples:
            print(f"  {p:8} {l:10} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.lost_thing} / {p.reminder} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Storyworld: long, inept attic ladder with sound effects and rhyming-story style.

A small classical simulation:
- a child wants to climb into the attic
- the ladder is long and inept, so it creaks, wobbles, and worries the grown-up
- a safer plan resolves the tension
- the ending image proves what changed

The story is authored from simulated state, not from a frozen paragraph.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the attic ladder"
    affords: set[str] = field(default_factory=lambda: {"climb"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str  # attic | below


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    help_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "attic_ladder": Setting(place="the attic ladder", affords={"climb"}),
}

ACTIVITIES = {
    "climb": Activity(
        id="climb",
        verb="climb up the attic ladder",
        gerund="climbing up the attic ladder",
        rush="run for the ladder",
        sound="creak, creak, clatter",
        risk="bump and tumble",
        tags={"ladder", "sound_effects", "attic", "rhyming"},
    ),
}

PRIZES = {
    "kite": Prize(
        label="kite",
        phrase="a bright paper kite",
        type="kite",
        location="attic",
    ),
    "book": Prize(
        label="book",
        phrase="a tiny rhyme book",
        type="book",
        location="attic",
    ),
    "drum": Prize(
        label="drum",
        phrase="a little toy drum",
        type="drum",
        location="attic",
    ),
}

GEAR = {
    "flashlight": Gear(
        id="flashlight",
        label="a flashlight",
        prep="carry a flashlight and go slowly",
        help_text="the light helps the child see each step",
        tags={"sound_effects", "attic"},
    ),
    "steady_hand": Gear(
        id="steady_hand",
        label="a steady hand",
        prep="hold the ladder steady",
        help_text="steady hands keep the ladder from wobbling",
        tags={"ladder"},
    ),
}

NAMES = ["Mia", "Noah", "Luna", "Eli", "Piper", "Theo"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["brave", "cheery", "curious", "spry"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return activity.id == "climb" and prize.location == "attic"


def select_gear(activity: Activity, prize: Prize) -> Optional[list[Gear]]:
    if not prize_at_risk(activity, prize):
        return None
    return [GEAR["flashlight"], GEAR["steady_hand"]]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def intro(world: World, hero: Entity, parent: Entity, prize: Entity, act: Activity) -> None:
    world.say(
        f"{hero.id} was a little {hero.pronoun('possessive')} child who loved bright little tunes and tidy rhymes."
    )
    world.say(
        f"One day {hero.id} heard a soft attic whisper about {prize.phrase}, hidden high and snug."
    )
    world.say(
        f"The ladder was long and inept, a creaky old stair-thing that went {act.sound} with every step."
    )


def predict_mess(world: World, hero: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["eagerness"] = 1
    return True


def warn(world: World, parent: Entity, hero: Entity, act: Activity, prize: Entity) -> None:
    world.say(
        f"{parent.pronoun('subject').capitalize()} said, “That ladder goes {act.sound}, and it may make you yelp and leap. "
        f"Let's not rush and risk a bump and tumble.”"
    )


def desire(world: World, hero: Entity, act: Activity) -> None:
    hero.memes["eagerness"] = 1
    world.say(
        f"{hero.id} still wanted to {act.verb}, tip-tap, zip-zap, with toes so quick and a grin so wide."
    )


def compromise(world: World, parent: Entity, hero: Entity, act: Activity) -> Gear:
    g1 = GEAR["flashlight"]
    g2 = GEAR["steady_hand"]
    world.add(Entity(id=g1.id, type="gear", label=g1.label, protective=True, owner=hero.id))
    world.add(Entity(id=g2.id, type="gear", label=g2.label, protective=True, owner=parent.id))
    world.say(
        f"Then {parent.id} chose {g1.label} and {g2.label}: {g1.prep}, and {g2.prep}."
    )
    world.say(
        f"{g1.help_text.capitalize()}; {g2.help_text}, so the climb could be calm and not grim."
    )
    return g1


def resolve(world: World, hero: Entity, parent: Entity, prize: Entity, act: Activity) -> None:
    hero.memes["joy"] = 1
    hero.memes["confidence"] = 1
    world.say(
        f"At last {hero.id} went {act.gerund}, one careful step, then another, with {parent.id} beside."
    )
    world.say(
        f"Up in the attic, {hero.id} found {prize.phrase}, and down below the ladder said {act.sound} no more."
    )
    world.say(
        f"The long, inept ladder still looked old, but now it had a gentle job and a safer ride."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------

def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))

    intro(world, hero, parent, prize, activity)
    world.para()
    warn(world, parent, hero, activity, prize)
    desire(world, hero, activity)
    world.para()
    compromise(world, parent, hero, activity)
    resolve(world, hero, parent, prize, activity)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, resolved=True)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    act = f["activity"]
    return [
        'Write a short rhyming story for a young child about an attic ladder with sound effects.',
        f"Tell a gentle rhyming story where {hero.id} wants to {act.verb} to reach {prize.phrase}.",
        "Make the ladder creak and clatter, but end with a safe, happy plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do on the attic ladder?",
            answer=f"{hero.id} wanted to {act.verb} to get {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the long, inept ladder?",
            answer=f"{parent.id} worried because the ladder went {act.sound} and could make {hero.id} wobble or tumble.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended safely, with {hero.id} going slowly, finding {prize.phrase}, and the ladder getting a calmer job.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What sound does a creaky old ladder often make?",
            answer="A creaky ladder can go creak, creak, or clatter when someone steps on it.",
        ),
        QAItem(
            question="Why is a flashlight helpful in a dark attic?",
            answer="A flashlight helps people see where they are stepping so they can move more carefully.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
attic(place).
affords(attic_ladder, climb).
activity(climb).
prize(kite).
prize(book).
prize(drum).

at_risk(A,P) :- activity(A), prize(P), A = climb, P = kite.
at_risk(A,P) :- activity(A), prize(P), A = climb, P = book.
at_risk(A,P) :- activity(A), prize(P), A = climb, P = drum.

gear_ok(A,P) :- at_risk(A,P), activity(A), prize(P).
valid(place, A, P) :- attic(place), gear_ok(A,P).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("attic", "attic_ladder"),
        asp.fact("affords", "attic_ladder", "climb"),
    ]
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos():")
    print("python only:", sorted(py - asp_set))
    print("asp only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming attic-ladder storyworld with sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not prize_at_risk(act, prize):
            raise StoryError("That prize is not at risk on the attic ladder story.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        "girl" if params.gender == "girl" else "boy",
        params.parent,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="attic_ladder", activity="climb", prize="kite", name="Mia", gender="girl", parent="mother", trait="curious"),
            StoryParams(place="attic_ladder", activity="climb", prize="book", name="Noah", gender="boy", parent="father", trait="cheery"),
            StoryParams(place="attic_ladder", activity="climb", prize="drum", name="Luna", gender="girl", parent="mother", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

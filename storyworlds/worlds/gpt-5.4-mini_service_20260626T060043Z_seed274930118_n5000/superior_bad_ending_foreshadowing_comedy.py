#!/usr/bin/env python3
"""
storyworlds/worlds/superior_bad_ending_foreshadowing_comedy.py
==============================================================

A small comedy storyworld built from the seed word "superior" with two narrative
instruments: foreshadowing and a bad ending.

Premise:
- A child is proud of a "superior" thing that is obviously a little too fancy
  for the situation.

Story shape:
- Setup: the child loves the superior thing.
- Foreshadowing: a wobble, a sticky patch, a noisy clue, or another comic omen
  hints that the thing is not as superior as it looks.
- Turn: the child tries anyway.
- Ending: the thing fails in a funny, harmless way, leaving everyone laughing.

The world model uses meters for physical state and memes for emotional state.
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    clue: str
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affordances={"stack", "carry"}),
    "hall": Setting(place="the hall", affordances={"stack", "carry"}),
    "yard": Setting(place="the yard", affordances={"stack", "carry"}),
}

ACTIVITIES = {
    "stack": Activity(
        id="stack",
        verb="stack the cups",
        gerund="stacking cups",
        rush="run to the table",
        mess="wobbly",
        zone={"head", "hands"},
        clue="one cup kept leaning like it had a secret",
        keyword="superior",
    ),
    "carry": Activity(
        id="carry",
        verb="carry the cake",
        gerund="carrying the cake",
        rush="rush across the room",
        mess="smeared",
        zone={"hands", "torso"},
        clue="the frosting was already sliding like a tiny white hill",
        keyword="superior",
    ),
}

PRIZES = {
    "hat": Prize(
        label="hat",
        phrase="a superior paper party hat",
        type="hat",
        region="head",
    ),
    "trophy": Prize(
        label="trophy",
        phrase="a shiny superior prize trophy",
        type="trophy",
        region="hands",
    ),
    "cake": Prize(
        label="cake",
        phrase="a superior birthday cake",
        type="cake",
        region="hands",
        plural=False,
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Pia", "Zoe"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Max", "Ben", "Ira"]
TRAITS = ["proud", "busy", "silly", "careful", "brave", "curious"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or prize.label == "cake"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affordances:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy storyworld with foreshadowing and a bad ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not prize_at_risk(act, prize):
            raise StoryError("That prize is not really at risk in this comedy setup.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
        and (args.gender is None or args.gender in PRIZES[c[2]].genders)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", meters={}, memes={}))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural,
        meters={"clean": 1.0}, memes={}
    ))

    # Setup
    world.say(f"{hero.id} was a little {trait} {hero.type} who thought the word superior sounded like a crown.")
    world.say(f"{hero.id} loved {activity.gerund}, and {hero.pronoun('possessive')} {prize.label} was extra fancy because it was {prize.phrase}.")
    world.say(f"At {setting.place}, the day felt ready for a laugh.")

    # Foreshadowing
    world.para()
    world.say(f"But there was a clue. {activity.clue.capitalize()}.")
    world.say(f"{hero.id} noticed it and still said the {prize.label} looked superior enough to handle anything.")
    hero.memes["confidence"] = 1.0
    hero.memes["foreshadow_worry"] = 0.5
    prize.meters["wobble"] = 1.0 if activity.id == "stack" else 0.0

    # Turn
    world.para()
    world.say(f"Then {hero.id} tried to {activity.verb} anyway.")
    if activity.id == "stack":
        world.say(f"{hero.pronoun('possessive').capitalize()} hands went up high, and the top cup swayed like it wanted to dance.")
        hero.meters["careless_move"] = 1.0
    else:
        world.say(f"{hero.id} rushed forward, and the cake began to slide before anyone could say 'careful.'")
        hero.meters["mess"] = 1.0

    # Bad ending
    world.para()
    if activity.id == "stack":
        prize.meters["clean"] = 0.0
        prize.meters["broken"] = 1.0
        hero.memes["surprised"] = 1.0
        parent.memes["amused"] = 1.0
        world.say(f"With one tiny wobble and one very un-superior sneeze from the room, the whole stack toppled over.")
        world.say(f"The cups bounced, the hat flew sideways, and {hero.id} stared at the pile with big round eyes.")
        world.say(f"Then {parent.label} laughed so hard they had to sit down, and {hero.id} laughed too, because the disaster was too silly to stay serious.")
        world.say(f"In the end, the superior party hat was lopsided, the cups were everywhere, and the room looked like a clown had organized it.")
    else:
        prize.meters["clean"] = 0.0
        prize.meters["smeared"] = 1.0
        hero.memes["surprised"] = 1.0
        parent.memes["amused"] = 1.0
        world.say(f"The cake slid right out of {hero.id}'s hands and landed with a soft, goofy flop.")
        world.say(f"Frosting smeared in a white streak, and the superior cake became a very un-superior mess.")
        world.say(f"{hero.id} made a shocked face for one second, then giggled at the frosting on {hero.pronoun('possessive')} nose.")
        world.say(f"{parent.label} snorted with laughter, and the room ended in crumbs, giggles, and a cake that looked like it had lost an argument.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    return [
        f'Write a short comedy story for a child where {hero.id} tries to {act.verb} and the superior {prize.label} causes trouble.',
        f'Create a funny story with foreshadowing, a proud child, and a bad ending involving {prize.phrase}.',
        f"Tell a simple story where {hero.id} ignores a clue and ends up with a silly mess at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"What did {hero.id} think the word superior sounded like?",
            answer=f"{hero.id} thought it sounded like a crown, because {hero.pronoun('subject')} was a little {trait} {hero.type} who liked fancy things.",
        ),
        QAItem(
            question=f"What clue hinted that things might go wrong before {hero.id} tried to {act.verb}?",
            answer=f"The clue was: {act.clue}. That was the foreshadowing that the superior plan would not stay neat.",
        ),
        QAItem(
            question=f"What happened at the end to {hero.pronoun('possessive')} {prize.label}?",
            answer=f"It ended badly and in a funny way: the {prize.label} got messy, toppled, or smeared, so it was no longer superior-looking at all.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a clue early in the story that hints something important or funny may happen later.",
        ),
        QAItem(
            question="What is a bad ending in a comedy story?",
            answer="A bad ending in a comedy story means the plan fails, but it fails in a silly or harmless way that can still be funny.",
        ),
        QAItem(
            question="What does superior mean?",
            answer="Superior means better, fancier, or higher in quality than something else.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="kitchen", activity="stack", prize="hat", name="Mina", gender="girl", parent="mother", trait="proud"),
    StoryParams(place="hall", activity="carry", prize="cake", name="Theo", gender="boy", parent="father", trait="silly"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), region(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
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
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

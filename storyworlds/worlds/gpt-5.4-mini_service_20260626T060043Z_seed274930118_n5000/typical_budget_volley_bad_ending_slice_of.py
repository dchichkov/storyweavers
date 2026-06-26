#!/usr/bin/env python3
"""
storyworlds/worlds/typical_budget_volley_bad_ending_slice_of.py
==============================================================

A small slice-of-life story world about an ordinary day, a tight budget, and a
volleyball game that does not quite end well.

Premise:
- A child wants to play volleyball with friends.
- Their family can only afford a budget ball and a budget net.
- The cheap gear is good enough to start the game, but not sturdy enough to last.
- A small mistake or weak seam causes the game to end in disappointment.

The world is intentionally narrow: only a few combinations are plausible, and
the story engine uses the simulated world state to produce the prose, Q&A, and
ASP parity checks.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Venue:
    place: str = "the neighborhood court"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
    plural: bool = False


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


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


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("pressure", 0.0) < THRESHOLD:
            continue
        ball = next((e for e in world.entities.values() if e.type == "ball" and e.owner == actor.id), None)
        if not ball:
            continue
        if ball.meters.get("fragile", 0.0) < THRESHOLD:
            continue
        sig = ("break", ball.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ball.meters["broken"] = 1.0
        out.append(f"The {ball.label} popped with a small, sad snap.")
    return out


def _r_lost_game(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        ball = next((e for e in world.entities.values() if e.type == "ball" and e.owner == actor.id), None)
        if not ball or ball.meters.get("broken", 0.0) < THRESHOLD:
            continue
        sig = ("lost", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["disappointment"] = actor.memes.get("disappointment", 0.0) + 1.0
        out.append("The game stopped right there.")
    return out


CAUSAL_RULES = [
    ("break", _r_break),
    ("lost", _r_lost_game),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.venue.affords:
        return
    actor.meters["pressure"] = actor.meters.get("pressure", 0.0) + 1.0
    actor.meters["energy"] = actor.meters.get("energy", 0.0) + 1.0
    world.say(f"{actor.id} tried to {activity.verb}.")
    world.say(f"The little game had an easy rhythm at first.")
    propagate(world, narrate=narrate)


def setup_story(world: World, hero: Entity, parent: Entity, prize: Entity, ball: Entity, gear: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} was a {next((t for t in hero.meters.keys()), '')}".strip())
    world.say(f"{hero.id} was a {hero.type} who liked ordinary afternoons and small games after school.")
    hero.memes["want"] = 1.0
    world.say(f"{hero.pronoun().capitalize()} wanted to {activity.verb} at {world.venue.place}.")
    world.say(f"But the family was on a budget, so they had a {gear.label} instead of the fancy kind.")
    world.say(f"{hero.id}'s {parent.type} had bought {hero.pronoun('object')} {prize.phrase}.")
    ball.worn_by = hero.id
    gear.worn_by = hero.id
    world.say(f"{hero.id} carried {ball.obj()} and {gear.obj()} out to the court.")


def turn_story(world: World, hero: Entity, parent: Entity, ball: Entity, gear: Entity, activity: Activity) -> None:
    world.para()
    world.say(f"The neighbors were already tossing the ball over the net, and {hero.id} ran to join them.")
    world.say(f"{hero.pronoun().capitalize()} loved the quick back-and-forth of {activity.keyword}.")
    world.say(f"{hero.id} reached high for one more hit, and the cheap seam on the {ball.label} stretched hard.")
    ball.meters["fragile"] = 1.0
    _do_activity(world, hero, activity, narrate=True)
    if ball.meters.get("broken", 0.0) < THRESHOLD:
        ball.meters["broken"] = 1.0
        world.say(f"Then the {ball.label} gave way anyway, because budget gear can only go so far.")
        propagate(world, narrate=True)
    world.say(f"The friends stood still for a second, watching the sagging net and the flat ball.")


def ending_story(world: World, hero: Entity, parent: Entity, ball: Entity, prize: Entity) -> None:
    world.para()
    hero.memes["joy"] = max(0.0, hero.memes.get("joy", 0.0) - 1.0)
    hero.memes["disappointment"] = hero.memes.get("disappointment", 0.0) + 1.0
    world.say(f"{hero.id} picked up the flat {ball.label} and looked down at the scratched court.")
    world.say(f"{hero.pronoun().capitalize()} did not get a new ball that day.")
    world.say(f"{hero.pronoun().capitalize()} and {hero.pronoun('possessive')} {parent.type} walked home quietly in the warm evening light, with the game ending in a small, disappointing silence.")


def tell(venue: Venue, activity: Activity, prize_cfg: Prize, gear_def: Gear,
         hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "typical") -> World:
    world = World(venue)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, plural=prize_cfg.plural
    ))
    ball = world.add(Entity(
        id="ball", type="ball", label="volleyball", phrase="a budget volleyball",
        owner=hero.id, caretaker=parent.id
    ))
    gear = world.add(Entity(
        id="gear", type="gear", label=gear_def.label, phrase=gear_def.phrase,
        owner=hero.id, caretaker=parent.id, plural=gear_def.plural
    ))

    world.facts.update(hero=hero, parent=parent, prize=prize, ball=ball, gear=gear, activity=activity, venue=venue, trait=trait)
    setup_story(world, hero, parent, prize, ball, gear, activity)
    turn_story(world, hero, parent, ball, gear, activity)
    ending_story(world, hero, parent, ball, prize)
    return world


SETTINGS = {
    "courtyard": Venue(place="the neighborhood court", indoor=False, affords={"volley"}),
    "park": Venue(place="the park court", indoor=False, affords={"volley"}),
    "schoolyard": Venue(place="the schoolyard", indoor=False, affords={"volley"}),
}

ACTIVITIES = {
    "volley": Activity(
        id="volley",
        verb="play volleyball",
        gerund="playing volleyball",
        rush="run for the ball",
        risk="the ball would crack",
        mess="broken",
        zone={"hands", "arms"},
        keyword="volley",
        tags={"volley", "budget", "typical"},
    ),
}

PRIZES = {
    "ball": Prize(id="ball", label="ball", phrase="a budget volleyball", region="hands", plural=False),
}

GEAR = [
    Gear(
        id="cheap_net",
        label="a budget net",
        phrase="a budget net with thin rope",
        prep="set up the budget net",
        tail="had already made do with the budget net",
        guards={"broken"},
        covers={"arms"},
    ),
]

GIRL_NAMES = ["Mina", "Lena", "Nia", "Tara", "Sana", "Rosa"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Jasper", "Milo", "Theo"]
TRAITS = ["typical", "quiet", "cheerful", "careful", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "volley", "ball") for place in SETTINGS]


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a budget volleyball game with a bad ending.")
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
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("This prize does not fit that gender in this little world.")
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "volley"
    prize = args.prize or "ball"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    if (place, activity, prize) not in valid_combos():
        raise StoryError("No valid combination matches the requested options.")
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], GEAR[0], params.name, params.gender, params.parent, params.trait)
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
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    return [
        f'Write a short slice-of-life story for a young child that includes the word "{act.keyword}" and the word "budget".',
        f"Tell a story where {hero.id} wants to {act.verb} but the family has only a budget setup.",
        f"Write a gentle everyday story about a typical afternoon, a volley game, and an ending that is a little sad.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, ball, act = f["hero"], f["parent"], f["prize"], f["ball"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at the court?",
            answer=f"{hero.id} wanted to {act.verb}. It was a typical afternoon, and the game felt fun at first.",
        ),
        QAItem(
            question=f"Why was the game a budget game?",
            answer=f"It was a budget game because the family used a budget volleyball and a budget net instead of fancy gear.",
        ),
        QAItem(
            question=f"What happened to the volleyball during the game?",
            answer=f"The volleyball got too strained, popped, and turned flat. That is why the game ended badly.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt disappointed. {hero.pronoun().capitalize()} walked home with the flat ball and no chance to keep playing.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is volleyball?",
            answer="Volleyball is a game where players hit a ball over a net and try to keep it in play.",
        ),
        QAItem(
            question="What does budget mean?",
            answer="Budget means there is not much money to spend, so people choose cheaper things.",
        ),
        QAItem(
            question="What does a ball do when it pops?",
            answer="When a ball pops, air escapes and it becomes flat, so it cannot bounce or be played with well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
valid(Place, volley, ball) :- place(Place), affords(Place, volley), prize(ball).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, venue in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for a in sorted(venue.affords):
            lines.append(asp.fact("affords", place, a))
    lines.append(asp.fact("prize", "ball"))
    lines.append(asp.fact("activity", "volley"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


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
    StoryParams(place="courtyard", activity="volley", prize="ball", name="Mina", gender="girl", parent="mother", trait="typical"),
    StoryParams(place="park", activity="volley", prize="ball", name="Owen", gender="boy", parent="father", trait="careful"),
    StoryParams(place="schoolyard", activity="volley", prize="ball", name="Lena", gender="girl", parent="mother", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

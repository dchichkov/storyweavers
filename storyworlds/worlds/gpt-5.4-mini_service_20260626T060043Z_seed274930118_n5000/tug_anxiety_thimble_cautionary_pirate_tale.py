#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tug_anxiety_thimble_cautionary_pirate_tale.py
==============================================================================================================

A small cautionary pirate-tale storyworld built from the seed words:
tug, anxiety, thimble.

Premise:
- A young pirate wants to tug at ship gear or cargo on a docked voyage.
- A cautious captain can foresee the trouble and the anxiety that follows.
- A sensible replacement action uses a small protective thimble or other gear.

The world is intentionally tiny and constraint-checked: only combinations that
actually create risk and have a plausible fix are generated.
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["strain", "scrape", "mess", "risk"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "anxiety", "worry", "relief", "care"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    risk_word: str
    zone: set[str]
    weather: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.weather = self.weather
        c.paragraphs = [[]]
        return c


def _r_mess(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["strain"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["mess"] += 1
            out.append(f"{actor.id}'s {item.label} got scuffed by the tugging.")
    return out


def _r_anxiety(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("anxiety", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["anxiety"] += 1
        out.append(f"{actor.id} felt a little knot of anxiety in {actor.peaceful_name if hasattr(actor, 'peaceful_name') else 'their chest'}.")
    return out


CAUSAL_RULES = [_r_mess, _r_anxiety]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def tell(place: Place, activity: Activity, prize_cfg: Prize,
         name: str = "Mira", gender: str = "girl",
         parent_type: str = "captain", trait: str = "careful") -> World:
    world = World(place)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=name, kind="character", type=gender,
        meters={"strain": 0.0, "mess": 0.0, "risk": 0.0},
        memes={"joy": 0.0, "anxiety": 0.0, "worry": 0.0, "relief": 0.0, "care": 0.0},
    ))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, label="the captain"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    hero.memes["care"] += 1

    world.say(f"{hero.id} was a little {trait} pirate who noticed every rope and every wave.")
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund} on the deck and hearing the rigging sing.")
    world.say(f"One day, {hero.id}'s {parent.label} gave {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} kept {prize.it()} close, because {prize.label} felt lucky in {hero.pronoun('possessive')} hand.")

    world.para()
    world.say(f"Near the harbor, {hero.id} and {hero.pronoun('possessive')} {parent.label} stood by {place.name}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} chest fluttered with a little anxiety.")
    hero.memes["worry"] += 1
    hero.meters["risk"] += 1
    propagate(world, narrate=True)

    world.say(f'"If you {activity.rush}, you might lose the {prize.label}," {parent.label} warned.')
    world.say(f"{hero.id} still reached for the line, and the deck creaked with the tug.")
    hero.meters["strain"] += 1
    propagate(world, narrate=True)

    world.para()
    gear_def = select_gear(activity, prize)
    if gear_def:
        gear = world.add(Entity(
            id=gear_def.id, type="gear", label=gear_def.label, protective=True,
            covers=set(gear_def.covers), plural=gear_def.plural, owner=hero.id, caretaker=parent.id
        ))
        gear.worn_by = hero.id
        world.say(f'{parent.label} held up a small smile. "First, let us {gear_def.prep}," {parent.label} said.')
        world.say(f"{hero.id} nodded and used {gear_def.label} before trying again.")
        hero.memes["worry"] = 0.0
        hero.memes["anxiety"] = 0.0
        hero.memes["relief"] += 1
        world.say(f"After that, {hero.id} could {activity.verb} without hurting the {prize.label}.")
        world.say(f"{hero.id} laughed softly, and the {prize.label} stayed safe in the salty air.")
        world.say(f"They {gear_def.tail}, and the ship felt calm again.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear_def, place=place)
    return world


PLACES = {
    "dock": Place("the dock", affords={"tug"}),
    "deck": Place("the deck", affords={"tug"}),
    "harbor": Place("the harbor wall", affords={"tug"}),
    "cove": Place("the cove", affords={"tug"}),
}

ACTIVITIES = {
    "tug": Activity(
        id="tug",
        verb="tug on the rope",
        gerund="tugging on ropes",
        rush="tug the rope harder",
        mess="strain",
        risk_word="tug",
        zone={"hands", "torso"},
        weather="windy",
        keyword="tug",
        tags={"rope", "wind", "ship"},
    ),
}

PRIZES = {
    "thimble": Prize(
        label="thimble",
        phrase="a tiny brass thimble",
        type="thimble",
        region="hands",
    ),
    "map": Prize(
        label="map",
        phrase="a folded treasure map",
        type="map",
        region="torso",
    ),
    "compass": Prize(
        label="compass",
        phrase="a shiny compass",
        type="compass",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="glove",
        label="a sailor's glove",
        covers={"hands"},
        guards={"strain"},
        prep="put on a sailor's glove first",
        tail="walked back to the line with the glove on",
    ),
    Gear(
        id="thimble_guard",
        label="a little leather thimble-guard",
        covers={"hands"},
        guards={"strain"},
        prep="slip on a little leather thimble-guard first",
        tail="came back ready and careful",
    ),
]

NAMES = ["Mira", "Ned", "Lia", "Finn", "Pip", "Tess"]
TRAITS = ["careful", "bright-eyed", "steady", "small", "brave"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in PLACES.values():
        for act_id in place.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place.name, act_id, prize_id))
    return out


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short cautionary pirate tale for a young child that includes the word "{act.keyword}".',
        f"Tell a story where {hero.id} wants to {act.verb}, but {parent.label} worries about {hero.pronoun('possessive')} {prize.label}.",
        f"Write a gentle pirate story about a little {hero.type} learning not to be reckless with a {prize.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {act.verb}, even though that felt a little risky.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {hero.pronoun('possessive')} {prize.label}?",
            answer=f"{parent.label} worried because tugging could strain the deck gear and make the {prize.label} unsafe or lost.",
        ),
        QAItem(
            question=f"What feeling did {hero.id} have when the captain warned {hero.pronoun('object')}?",
            answer=f"{hero.id} felt anxiety first, because {hero.pronoun('possessive')} chest tightened when the danger was explained.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did {gear.label} help in the end?",
            answer=f"It helped {hero.id} stay careful so {hero.id} could {act.verb} without hurting the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel after using the {gear.label}?",
            answer=f"{hero.id} felt relief and laughed softly, because the plan kept the {prize.label} safe.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a thimble for?",
            answer="A thimble is a tiny cap worn on a finger to help protect it while sewing.",
        ),
        QAItem(
            question="What does anxiety mean?",
            answer="Anxiety is a worried feeling that makes your body feel tense, jumpy, or uneasy.",
        ),
        QAItem(
            question="What does tugging mean?",
            answer="Tugging means pulling something firmly or suddenly with your hands.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not really threaten a {prize.label} in this tiny world.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: this world does not make {PRIZES[prize_id].label} depend on {gender}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P),
                   mess_of(A,M), guards(G,M),
                   covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary pirate tale about tugging, anxiety, and a thimble.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == PLACES[args.place].name)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_name, activity, prize_id = rng.choice(sorted(combos))
    place = next(p for p in PLACES.values() if p.name == place_name)
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=next(k for k, v in PLACES.items() if v.name == place.name),
                       activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
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
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="dock", activity="tug", prize="thimble", name="Mira", gender="girl", parent="captain", trait="careful"),
            StoryParams(place="deck", activity="tug", prize="map", name="Ned", gender="boy", parent="captain", trait="steady"),
            StoryParams(place="harbor", activity="tug", prize="compass", name="Lia", gender="girl", parent="captain", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
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

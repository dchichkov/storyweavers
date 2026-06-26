#!/usr/bin/env python3
"""
storyworlds/worlds/assembly_onsie_curiosity_bad_ending_rhyme_myth.py
=====================================================================

A small myth-flavored story world about a curious child, an assembly line,
and a snapped-together onsie that turns out to be a bad idea until a safer
path is chosen.

Seed tale premise:
- A child is drawn to a grand assembly.
- A special onsie is being prepared.
- Curiosity makes the child reach too soon.
- The first ending goes wrong, then rhyme and ritual help repair the moment.
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
    protective: bool = False
    region: str = ""
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wear": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "hope": 0.0, "joy": 0.0, "regret": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)
    mood: str = "hushed"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    mythline: str


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
    rhyme: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w


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
    "workshop": Place(name="the assembly hall", indoor=True, affords={"assembly"}, mood="bright"),
    "nursery": Place(name="the nursery workshop", indoor=True, affords={"assembly"}, mood="hushed"),
}

ACTIVITIES = {
    "assembly": Activity(
        id="assembly",
        verb="help with the assembly",
        gerund="helping with the assembly",
        rush="run to the table of pieces",
        mess="tangled",
        soil="tangled and torn",
        zone={"torso"},
        keyword="assembly",
        mythline="The little hands of the hall loved to make one thing from many.",
    )
}

PRIZES = {
    "onsie": Prize(
        label="onsie",
        phrase="a bright little onsie",
        type="onsie",
        region="torso",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a protective apron",
        covers={"torso"},
        guards={"tangled"},
        prep="put on a protective apron first",
        tail="put on the apron and returned to the workbench",
        rhyme="apron and patron",
    ),
    Gear(
        id="ties",
        label="soft ribbon ties",
        covers={"torso"},
        guards={"tangled"},
        prep="tie the pieces with soft ribbon ties first",
        tail="used the ribbon ties and went back to the hall",
        plural=True,
        rhyme="ties and skies",
    ),
]

GIRL_NAMES = ["Mira", "Ivy", "Nora", "Luna", "Aria"]
BOY_NAMES = ["Eli", "Tao", "Finn", "Milo", "Sage"]
TRAITS = ["curious", "earnest", "bold", "gentle", "restless"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world of assembly, onsie, curiosity, and rhyme.")
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
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError("No story: this assembly does not truly endanger the onsie in a fixable way.")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("No story: that onsie is not a fitting choice for the chosen child here.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.memes["curiosity"] += 1
    actor.meters[activity.mess] += 1
    if narrate:
        world.say(f"{actor.pronoun().capitalize()} reached for the pieces, and the room seemed to listen.")


def propagate(world: World, narrate: bool = True) -> None:
    for actor in world.characters():
        if actor.meters["tangled"] >= THRESHOLD:
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("damage", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["damage"] += 1
                item.meters["tangled"] += 1
                if narrate:
                    world.say(f"That touch left {actor.pronoun('possessive')} {item.label} tangled and sad.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["damage"] >= THRESHOLD}


def tell(place: Place, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=hero_traits if False else []))
    hero.traits = hero_traits
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = world.add(Entity(id="onsie", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    prize.worn_by = hero.id

    world.say(f"In the old assembly hall, {hero.id} was a {hero_traits[0]} little {hero.type} who loved to watch many parts become one.")
    world.say(f"{hero.id} treasured {hero.pronoun('possessive')} {prize.label}, and the bright cloth felt like a tiny banner of home.")
    world.para()
    world.say(f"The hall was {place.mood}, and {activity.mythline}")
    world.say(f"One day {hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label} lifted a careful hand.")
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(f'"You will get your {prize.label} {activity.soil}," {parent.label} said. "The old song warns us first."')
    world.say(f"{hero.id} still ran toward the table and tried to {activity.rush}.")
    _do_activity(world, hero, activity, narrate=False)
    propagate(world)
    world.para()
    world.say(f"{hero.id} frowned at the tangled moment, because the first ending was a bad one.")
    gear = select_gear(activity, prize)
    if gear:
        gear_ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
        gear_ent.worn_by = hero.id
        if predict_mess(world, hero, activity, prize.id)["soiled"]:
            gear_ent.worn_by = None
            del world.entities[gear.id]
            gear = None
    if gear:
        world.say(f"Then the {parent.label} spoke in rhyme: '{gear.rhyme}, and no more tugging skies.'")
        world.say(f'"{gear.prep}," {parent.label} said, "and we can mend the work without losing the wonder."')
        hero.memes["joy"] += 1
        hero.memes["hope"] += 1
        hero.memes["regret"] += 1
        world.say(f"{hero.id}'s face brightened, and {hero.id} went with {parent.label} to {gear.tail}.")
        world.say(f"At the end, {hero.id} was {activity.gerund}, {prize.label} safe and bright, while the hall kept its quiet gold glow.")
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short myth-like story for a child named {hero.id} about assembly and a special onsie, using the word "{act.keyword}".',
        f"Tell a gentle myth where a curious {hero.type} wants to {act.verb} but a parent worries about {prize.label}.",
        f'Write a simple story with rhyme, a bad ending that gets repaired, and the word "{prize.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act, gear = f["hero"], f["parent"], f["prize"], f["activity"], f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at the assembly hall?",
            answer=f"{hero.id} wanted to {act.verb} in the assembly hall, because the making of things filled {hero.pronoun('possessive')} heart with curiosity.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the onsie?",
            answer=f"{parent.label} worried because {hero.id} would get {prize.label} {act.soil} if the child rushed into the assembly too soon.",
        ),
        QAItem(
            question=f"What made the first ending go badly?",
            answer=f"The first ending went badly because {hero.id} touched the pieces before the safe choice was made, and the onsie became tangled.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How was the problem fixed with rhyme?",
            answer=f"{parent.label} used a rhyme about {gear.label} and guided {hero.id} to use it first, so the assembly could continue without ruining the onsie.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happier and braver at the end, because the bad ending was changed into a safe one and the onsie stayed bright.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is curiosity?", answer="Curiosity is the feeling that makes someone want to know more, look closer, and ask what will happen next."),
        QAItem(question="What is an assembly?", answer="An assembly is when separate parts are brought together to make one thing, like pieces becoming a toy or a tool."),
        QAItem(question="What is a rhyme?", answer="A rhyme is when words sound alike at the end, which can make a story or song feel memorable."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} worn_by={e.worn_by} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, r))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "No story: the assembly would not truly threaten the onsie in a way that needs a rescue."
    return "No story: the available gear does not make a believable fix for this assembly and onsie."


def valid_gender(prize_id: str, gender: str) -> bool:
    return gender in PRIZES[prize_id].genders


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait, "curious"],
        params.parent,
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


CURATED = [
    StoryParams(place="workshop", activity="assembly", prize="onsie", name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="nursery", activity="assembly", prize="onsie", name="Eli", gender="boy", parent="father", trait="earnest"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, act, prize in triples:
            print(f"  {place:10} {act:10} {prize:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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

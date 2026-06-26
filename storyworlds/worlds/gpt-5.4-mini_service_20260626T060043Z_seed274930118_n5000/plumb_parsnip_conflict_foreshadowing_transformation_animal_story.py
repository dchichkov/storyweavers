#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/plumb_parsnip_conflict_foreshadowing_transformation_animal_story.py
===============================================================================================================

A small animal-story world built from the seed words plumb and parsnip, with
Conflict, Foreshadowing, and Transformation as the main narrative instruments.

The premise is a gentle garden tale: an animal wants to keep working on a neat
line in the soil while another animal worries about the parsnips. A small
warning hints at trouble, the conflict grows, and a practical change in method
turns the problem into a cooperative ending.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "hare", "fox", "badger", "mouse", "squirrel"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


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
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"rabbit", "hare", "fox", "badger", "mouse", "squirrel"})


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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "garden": Setting(place="the garden", affords={"dig", "harvest"}),
    "patch": Setting(place="the parsnip patch", affords={"dig", "harvest"}),
    "burrow": Setting(place="the burrow", indoors=True, affords={"measure"}),
}

ACTIVITIES = {
    "dig": Activity(
        id="dig",
        verb="dig a straight row",
        gerund="digging a straight row",
        rush="dash toward the soft earth",
        mess="muddy",
        soil="muddy and crooked",
        zone={"feet", "hands"},
        keyword="plumb",
        tags={"plumb", "mud"},
    ),
    "harvest": Activity(
        id="harvest",
        verb="pull up parsnips",
        gerund="pulling up parsnips",
        rush="rush to the patch",
        mess="dirty",
        soil="dirty and bent",
        zone={"hands"},
        keyword="parsnip",
        tags={"parsnip", "food"},
    ),
    "measure": Activity(
        id="measure",
        verb="check the plumb line",
        gerund="checking the plumb line",
        rush="lean over the line",
        mess="spilled",
        soil="spilled and messy",
        zone={"torso", "hands"},
        keyword="plumb",
        tags={"plumb"},
    ),
}

PRIZES = {
    "parsnips": Prize(
        label="parsnips",
        phrase="a basket of bright parsnips",
        type="parsnips",
        region="hands",
        plural=True,
        genders={"rabbit", "hare", "mouse", "squirrel"},
    ),
    "line": Prize(
        label="plumb line",
        phrase="a careful plumb line with a small weight",
        type="line",
        region="torso",
        genders={"rabbit", "hare", "fox", "badger"},
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a garden apron",
        covers={"torso", "hands"},
        guards={"dirty", "spilled"},
        prep="put on a garden apron",
        tail="put on the garden apron and worked more carefully",
    ),
    Gear(
        id="boots",
        label="rubber boots",
        covers={"feet"},
        guards={"muddy"},
        prep="put on rubber boots",
        tail="put on the rubber boots and stepped around the wet ground",
        plural=True,
    ),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    species: str
    friend: str
    seed: Optional[int] = None


SPECIES_NAMES = {
    "rabbit": ["Pip", "Mina", "Bun", "Tilly"],
    "hare": ["Hop", "Luna", "Tess"],
    "fox": ["Finn", "Ruby", "Poppy"],
    "badger": ["Bram", "Nell", "Moss"],
    "mouse": ["Nip", "Dot", "Peep"],
    "squirrel": ["Sage", "Quill", "Merry"],
}

TRAITS = ["careful", "curious", "grumpy", "gentle", "quick"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not reasonably threaten {prize.label}.)"


def explain_species(prize_id: str, species: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical item for a {species} here; try {ok}.)"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            for mess in ("muddy", "dirty", "spilled"):
                if actor.meters.get(mess, 0.0) < THRESHOLD:
                    continue
                for item in world.worn_items(actor):
                    if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                        continue
                    sig = ("soak", item.id, mess)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters[mess] = item.meters.get(mess, 0.0) + 1
                    item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                    produced.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess}.")
                    changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, species: str, friend_species: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=species))
    friend = world.add(Entity(id="Friend", kind="character", type=friend_species, label=f"the {friend_species}"))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=friend.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    gear_def = None

    world.say(f"{hero.id} was a {random.choice(TRAITS)} {species} who loved the neat lines in the {setting.place}.")
    world.say(f"{hero.id} also loved {activity.gerund}, especially when the soil smelled fresh.")
    world.say(f"One morning, {friend.label} brought out {prize.phrase}, and {hero.id} held it close.")

    world.para()
    world.say(f"At the {setting.place}, {hero.id} wanted to {activity.verb}.")
    world.say(f"{friend.label} watched the ground and frowned, because the work looked close to {prize.label}.")
    world.say(f"Just then, {friend.label} noticed a small dip in the dirt and said, 'That might slip if you go too fast.'")
    world.say(f"The warning felt tiny, but it was a foreshadowing of trouble.")

    world.say(f"{hero.id} still tried to {activity.rush}, and the worry grew into a conflict.")
    pred = predict_mess(world, hero, activity, "Prize")
    if pred["soiled"]:
        world.say(f"{friend.label} held up a hand and said, 'Wait. {prize.label} could get {activity.soil}.'")

    world.para()
    world.say(f"{hero.id} pouted for a moment, then looked at the line and the basket.")
    gear_def = select_gear(activity, prize)
    if gear_def:
        gear = world.add(Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            owner=hero.id,
            caretaker=friend.id,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
        ))
        gear.worn_by = hero.id
        if predict_mess(world, hero, activity, "Prize")["soiled"]:
            gear.worn_by = None
            del world.entities[gear.id]
            gear_def = None
    if gear_def:
        world.say(f"Then {friend.label} smiled and said, 'Let's {gear_def.prep} first.'")
        world.say(f"{hero.id} nodded. That small change was a transformation: the same job, but a safer way to do it.")
        world.say(f"Soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, and the two friends worked side by side.")
        world.say(f"At the end, the row was straighter than before, and the parsnips looked brighter in the morning light.")
    else:
        world.say(f"Then {hero.id} slowed down, took a breath, and made the line by hand.")
        world.say(f"The conflict softened into careful teamwork, and the parsnips stayed safe.")

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=True,
        resolved=True,
    )
    return world


KNOWLEDGE = {
    "plumb": [("What does a plumb line do?", "A plumb line helps people check if something hangs straight up and down.")],
    "parsnip": [("What is a parsnip?", "A parsnip is a pale root vegetable that grows under the soil.")],
    "mud": [("What is mud?", "Mud is wet dirt that can stick to paws, shoes, and clothes.")],
    "garden": [("What is a garden?", "A garden is a place where plants grow and people or animals care for them.")],
    "line": [("What does it mean for a line to be straight?", "A straight line does not bend or wobble.")],
    "apron": [("What is an apron for?", "An apron helps keep clothes cleaner while you work with messy things.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, act, prize = f["hero"], f["friend"], f["activity"], f["prize"]
    return [
        f'Write a short animal story for a young child that includes the word "{act.keyword}" and the word "{prize.label}".',
        f"Tell a gentle story about {hero.id}, a {hero.type}, and {friend.label}, where a warning about the {prize.label} leads to a kinder plan.",
        f"Write an animal story with a clear conflict, a small foreshadowing clue, and a transformation that helps the friends finish their work.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, act = f["hero"], f["friend"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a {hero.type} who cares about the {world.setting.place}, and {friend.label}, who worries about the {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, even though that could trouble the {prize.label}.",
        ),
        QAItem(
            question=f"What warning hinted that trouble might happen?",
            answer=f"The warning was the small dip in the dirt. It foreshadowed that the work might go wrong if {hero.id} rushed ahead.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did the friends change the plan?",
            answer=f"They used {gear.label} first, so {hero.id} could keep working without ruining the {prize.label}. That was the story's transformation.",
        ))
    qa.append(QAItem(
        question=f"How did the story end?",
        answer=f"It ended with {hero.id} and {friend.label} working side by side, and the {prize.label} staying safe and clean.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", activity="dig", prize="parsnips", name="Pip", species="rabbit", friend="badger"),
    StoryParams(place="patch", activity="harvest", prize="parsnips", name="Mina", species="hare", friend="mouse"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Species) :- valid(Place,A,P), wears(Species,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(description="Animal story world with plumb, parsnip, conflict, foreshadowing, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--species", choices=list(SPECIES_NAMES))
    ap.add_argument("--friend", choices=list(SPECIES_NAMES))
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
    if args.species and args.prize and args.species not in PRIZES[args.prize].genders:
        raise StoryError(explain_species(args.prize, args.species))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    species = args.species or rng.choice(sorted(prize.genders))
    friend = args.friend or rng.choice([s for s in SPECIES_NAMES if s != species])
    name = args.name or rng.choice(SPECIES_NAMES[species])
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, species=species, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.species, params.friend)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with species):\n")
        for place, act, prize in triples:
            species = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:10} {act:10} {prize:10}  [{', '.join(species)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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

#!/usr/bin/env python3
"""
A small slice-of-life cautionary storyworld about a curious child, a delicate
probe, and a grown-up who notices a problem before it becomes a trillion little
troubles.

The seed tale behind this world is simple: a child wants to use a probe
carelessly around a fragile everyday thing, a parent worries, and they find a
safer way to satisfy the curiosity without causing a mess.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "damage": 0.0, "workload": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "comfort": 0.0, "regret": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
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


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mess"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != actor.id:
                continue
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["mess"] += 1
            item.meters["damage"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got dirty.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["damage"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


CAUSAL_RULES = [_r_soil, _r_workload]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def valid_combo(setting: Setting, activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone and activity.mess in {"mess"} and bool(GEAR_BY_ACTIVITY.get(activity.id))


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["damage"] >= THRESHOLD)}


def activity_note(activity: Activity) -> str:
    return {
        "probe": "the little probe made the whole idea feel important",
    }.get(activity.id, "it turned the day into a small experiment")


def setting_note(setting: Setting) -> str:
    return f"{setting.place.capitalize()} felt calm and ordinary, with one small thing waiting on the table."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["mess"] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    world.say(f"{hero.id} was a little {trait} {hero.type} who liked noticing how things worked.")
    world.say(f"{hero.id} loved {activity.gerund} because {activity_note(activity)}.")
    world.say(f"One afternoon, {hero.id}'s {parent_type} had bought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} liked {prize.it()} and carried it carefully.")

    world.para()
    world.say(setting_note(setting))
    world.say(f"{hero.id} wanted to {activity.verb} near {prize.label}, but {parent.label} frowned a little.")
    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.facts["predicted_soil"] = activity.soil
        world.say(f'"If you do that, your {prize.label} will get {activity.soil}," {parent.label} said.')
        world.say(f'"That could turn into a trillion tiny problems," {parent.label} added.')
    hero.memes["worry"] += 0.5
    hero.memes["regret"] += 0.5
    world.say(f"{hero.id} reached toward the thing anyway, then stopped to listen.")

    gear = select_gear(activity, prize)
    world.para()
    if gear:
        world.say(f"{parent.label.capitalize()} picked up {gear.label} and smiled.")
        world.say(f'"How about we {gear.prep} and then {activity.verb} together?" {parent.label} asked.')
        hero.memes["comfort"] += 1
        hero.memes["worry"] = 0.0
        world.say(f"{hero.id}'s face warmed up, and {hero.id} nodded.")
        world.say(f"They {gear.tail}. Soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, and the little afternoon felt safe again.")
        world.facts["resolved"] = True
        world.facts["gear"] = gear
    else:
        world.say(f"{parent.label.capitalize()} gave a firmer no, because there was no safe way to make it work.")
        world.say(f"{hero.id} put the probe down and chose a quieter game instead.")
        world.say(f"Later, the {prize.label} still looked bright on the shelf, and the room stayed peaceful.")
        world.facts["resolved"] = False
        world.facts["gear"] = None

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting)
    return world


def build_world_state(world: World) -> None:
    pass


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"probe"}),
    "table": Setting(place="the dining table", affords={"probe"}),
    "porch": Setting(place="the porch", affords={"probe"}),
}

ACTIVITIES = {
    "probe": Activity(
        id="probe",
        verb="probe it",
        gerund="probing things",
        rush="poke at everything in sight",
        mess="mess",
        soil="muddied and sticky",
        zone={"torso", "hands"},
        keyword="probe",
        tags={"probe", "cautionary"},
    ),
}

PRIZES = {
    "jar": Prize(
        label="jar",
        phrase="a glass cookie jar",
        type="jar",
        region="hands",
        plural=False,
    ),
    "plant": Prize(
        label="plant",
        phrase="a small houseplant in a red pot",
        type="plant",
        region="hands",
    ),
    "lamp": Prize(
        label="lamp",
        phrase="a little lamp with a cord",
        type="lamp",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="tray",
        label="a plastic tray",
        covers={"hands", "torso"},
        guards={"mess"},
        prep="place the jar on a plastic tray first",
        tail="carried the tray to the table",
    ),
    Gear(
        id="gloves",
        label="rubber gloves",
        covers={"hands"},
        guards={"mess"},
        prep="put on rubber gloves first",
        tail="put on the gloves and tried again gently",
        plural=True,
    ),
]
GEAR_BY_ACTIVITY = {"probe": GEAR[0]}

NAMES = ["Milo", "Nina", "June", "Sami", "Ivy", "Toby"]
TRAITS = ["careful", "curious", "bouncy", "quiet", "bright"]


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
    hero = f["hero"]
    prize = f["prize"]
    act = f["activity"]
    return [
        'Write a short slice-of-life cautionary story for a small child about a probe and a safe choice.',
        f"Tell a gentle everyday story where {hero.id} wants to {act.verb} near {prize.label}, but a parent worries about a messy accident.",
        'Write a story that includes the word "trillion" as part of a grown-up warning, then ends with a safer plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    gear = f.get("gear")
    out = [
        QAItem(
            question=f"What did {hero.id} want to do near the {prize.label}?",
            answer=f"{hero.id} wanted to {act.verb}. {hero.id} was curious, but the grown-up worried it could make a mess.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried because the probe could make the {prize.label} {act.soil}, and that would be hard to clean up.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the end of the story?",
            answer=f"At the end, {hero.id} chose the safer way, and the room stayed calm and tidy.",
        ),
    ]
    if f.get("resolved") and gear:
        out.append(
            QAItem(
                question=f"How did {gear.label} help {hero.id}?",
                answer=f"{gear.label} gave {hero.id} a safer way to try the idea without making the {prize.label} dirty.",
            )
        )
    return out


KNOWLEDGE = {
    "probe": [(
        "What is a probe?",
        "A probe is a tool or object used to poke, check, or explore something carefully.",
    )],
    "trillion": [(
        "How big is a trillion?",
        "A trillion is an extremely big number. It is far more than a million or a billion.",
    )],
    "cautionary": [(
        "What does cautionary mean?",
        "Cautionary means it gives a warning or teaches you to be careful.",
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("resolved"):
        tags.add("cautionary")
    out: list[QAItem] = []
    for tag in ["probe", "trillion", "cautionary"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), guards(G, M), mess_of(A, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {(p, a, pr) for p, s in SETTINGS.items() for a in s.affords for pr in PRIZES if select_gear(ACTIVITIES[a], PRIZES[pr])}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if clingo_set - python_set:
        print("only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small cautionary slice-of-life storyworld about a probe and a safer choice.")
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
    combos = [(p, a, pr) for p in SETTINGS for a in SETTINGS[p].affords for pr in PRIZES if select_gear(ACTIVITIES[a], PRIZES[pr])]
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if args.gender:
        combos = [c for c in combos if args.gender in PRIZES[c[2]].genders]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="kitchen", activity="probe", prize="jar", name="Milo", gender="boy", parent="mother", trait="curious"),
    StoryParams(place="table", activity="probe", prize="plant", name="Nina", gender="girl", parent="father", trait="careful"),
    StoryParams(place="porch", activity="probe", prize="lamp", name="June", gender="girl", parent="mother", trait="bright"),
]


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
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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

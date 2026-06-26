#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/spa_quarry_edge_suspense_fable.py
==============================================================================================================

A small storyworld in a quarry-edge spa: a child, a little danger, and a safe
compromise. The tone leans toward fable, with a suspenseful turn and a calm
ending image.

Seed image:
---
At the edge of a quarry, a small stone spa breathed steam into the cool air.
A child wanted to enjoy the warm water, but the ground near the drop was loose.
A parent worried that one careless step could send a robe into the pool and a
paw or shoe toward the edge.
The answer was not to forbid the joy, but to find a safer stone bench a little
farther back from the brink.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "dirty": 0.0, "crack": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "desire": 0.0, "worry": 0.0, "fear": 0.0, "relief": 0.0, "love": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fox", "rabbit", "badger", "otter", "goat"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the quarry edge"
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
    weather: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.edge_risk: float = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.edge_risk = self.edge_risk
        return clone


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def _r_soak(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if item.region in world.zone and ("soak", item.id) not in world.fired:
                world.fired.add(("soak", item.id))
                item.meters["wet"] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet.")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["desire"] >= THRESHOLD and world.edge_risk >= THRESHOLD:
            sig = ("worry", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["worry"] += 1
            out.append("__worry__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_soak, _r_worry):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__worry__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "soiled": bool(prize.meters["wet"] >= THRESHOLD),
        "risk": sim.edge_risk,
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("The setting cannot host that spa scene.")
    world.zone = set(activity.zone)
    world.edge_risk += 1
    actor.meters["wet"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "quarry_edge": Setting(place="the quarry edge", affords={"spa"}),
}

ACTIVITIES = {
    "spa": Activity(
        id="spa",
        verb="enjoy the spa",
        gerund="soaking in the spa",
        rush="hurry toward the warm pool",
        mess="wet",
        soil="soaked",
        zone={"torso", "feet"},
        weather="cool",
        keyword="spa",
        tags={"spa", "water", "steam"},
    ),
}

PRIZES = {
    "robe": Prize(
        label="robe",
        phrase="a soft bath robe",
        type="robe",
        region="torso",
    ),
    "towel": Prize(
        label="towel",
        phrase="a thick towel",
        type="towel",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="stonebench",
        label="a flat stone bench",
        covers={"torso"},
        guards={"wet"},
        prep="move to the flat stone bench first",
        tail="moved to the flat stone bench",
    ),
    Gear(
        id="drywrap",
        label="a dry wrap",
        covers={"torso"},
        guards={"wet"},
        prep="put on a dry wrap first",
        tail="put on the dry wrap",
    ),
]

GIRL_NAMES = ["Mina", "Iris", "Luna", "Sage", "Nina"]
BOY_NAMES = ["Toby", "Owen", "Finn", "Arlo", "Jasper"]
TRAITS = ["quiet", "bold", "curious", "gentle", "steady"]


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


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={"wet": 0.0, "dirty": 0.0, "crack": 0.0},
                            memes={"joy": 0.0, "desire": 0.0, "worry": 0.0, "fear": 0.0, "relief": 0.0, "love": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    hero.traits = ["little"] + (hero_traits or ["steady"])

    world.say(f"At the quarry edge, {hero_name} was a little {hero.traits[1]} {hero_type} who loved quiet places.")
    world.say(f"{hero_name} loved {activity.gerund}, and the steam from the spa looked like a soft cloud.")
    world.say(f"That morning, {hero_name}'s {parent_type} brought {hero.pronoun('object')} {prize_cfg.phrase}.")
    prize.worn_by = hero.id
    world.say(f"{hero_name} wore {hero.pronoun('possessive')} {prize.label} as if the day had been made for it.")

    world.para()
    world.say(f"One cool day, {hero_name} and {hero.pronoun('possessive')} {parent_type} went to {setting.place}.")
    world.say(f"{hero_name} wanted to {activity.verb}, but the stones near the drop looked loose and sharp.")
    world.edge_risk = 1.0
    hero.memes["desire"] += 1
    hero.memes["fear"] += 0.5
    world.say(f"{parent_type.capitalize()} looked at the edge and grew still. One wrong step could make the robe slip and the child stumble.")
    world.say(f'"If you {activity.rush}, your {prize.label} may get {activity.soil}," {hero.pronoun("possessive")} {parent_type} said.')

    world.para()
    hero.memes["worry"] += 1
    hero.memes["fear"] += 1
    world.say(f"{hero_name} paused, feeling the suspense in the quiet air.")
    world.say(f"Then {hero_name} saw a flat stone bench a little farther from the brink.")
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        raise StoryError("No safe compromise fits this spa story.")
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, protective=True, covers=set(gear_def.covers)))
    gear.worn_by = hero.id
    world.say(f'"How about we {gear_def.prep} and then {activity.verb}?" said {hero.pronoun("possessive")} {parent_type}.')
    world.say(f"{hero_name} nodded. The fear eased at once, because the safer stone was the wiser stone.")
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0.0

    world.para()
    _do_activity(world, hero, activity, narrate=False)
    world.say(f"So they {gear_def.tail}, and {hero_name} settled down to {activity.gerund}.")
    world.say(f"The robe stayed dry, the steam warmed the air, and the quarry edge felt less like a threat and more like a calm old watcher.")
    world.say(f"In the end, {hero_name} was happy, {parent_type} was relieved, and the little spa still breathed mist beside the stones.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting,
                       gear=gear_def, resolved=True, conflict=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        'Write a short fable-like story for a young child about a spa at the quarry edge, with a little suspense and a safe choice.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.type} worries about the {prize.label} near the quarry edge.",
        f'Write a simple suspenseful story that includes the word "{act.keyword}" and ends with a calm, safe spa scene.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who wanted to {act.verb} at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.type} worry about the {prize.label}?",
            answer=f"{parent.type.capitalize()} worried because the stones near the quarry edge were loose, and the {prize.label} could get {act.soil} if the child rushed too close.",
        ),
        QAItem(
            question=f"What safer place did they choose instead of the brink?",
            answer=f"They chose the flat stone bench, which let {hero.id} enjoy the spa without danger.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {hero.pronoun('possessive')} {prize.label}?",
            answer=f"{hero.id} ended the day happy, and {hero.pronoun('possessive')} {prize.label} stayed dry and safe.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help?",
                answer=f"{gear.label.capitalize()} helped by giving them a safer place away from the edge, so the spa could still happen without the {prize.label} getting ruined.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spa?",
            answer="A spa is a place where warm water, steam, or baths help someone relax and feel clean.",
        ),
        QAItem(
            question="Why can a quarry edge be dangerous?",
            answer="A quarry edge can be dangerous because the ground near the drop may be loose and a slip could hurt someone.",
        ),
        QAItem(
            question="What does steam look like?",
            answer="Steam looks like a soft white mist that rises from hot water.",
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for (n, *_) in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="quarry_edge", activity="spa", prize="robe", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="quarry_edge", activity="spa", prize="towel", name="Toby", gender="boy", parent="father", trait="steady"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A quarry-edge spa storyworld with suspense and a fable-like ending.")
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
            raise StoryError("That activity and prize do not make a safe spa story.")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("That prize does not fit the requested gender in this world.")
    combos = [("quarry_edge", "spa", p) for p in PRIZES if (args.prize is None or args.prize == p)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    _, activity, prize_id = rng.choice(combos)
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place="quarry_edge", activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", "quarry_edge"), asp.fact("affords", "quarry_edge", "spa"), asp.fact("activity", "spa"), asp.fact("mess_of", "spa", "wet")]
    lines.append(asp.fact("splashes", "spa", "torso"))
    lines.append(asp.fact("splashes", "spa", "feet"))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
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
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {("quarry_edge", "spa", prize) for prize in PRIZES if select_gear(ACTIVITIES["spa"], PRIZES[prize])}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:12} {act:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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

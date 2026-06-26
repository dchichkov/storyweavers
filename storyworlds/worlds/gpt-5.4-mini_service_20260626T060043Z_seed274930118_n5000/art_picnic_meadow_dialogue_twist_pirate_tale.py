#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/art_picnic_meadow_dialogue_twist_pirate_tale.py
================================================================================================

A tiny story world about a pirate picnic in a meadow, where a child makes art,
talks with a crewmate, and a twist changes the plan.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the picnic meadow"
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("painted", "sandy", "wet"):
            if actor.meters.get(mess, 0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got messy.")
    return out


def _r_spark(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    map_item = world.get("map")
    if hero.memes.get("curiosity", 0) >= THRESHOLD and hero.memes.get("shared", 0) >= THRESHOLD:
        sig = ("spark",)
        if sig not in world.fired:
            world.fired.add(sig)
            map_item.meters["revealed"] = 1
            out.append("A little clue showed through the paint.")
    return out


CAUSAL_RULES = [
    ("soil", _r_soil),
    ("spark", _r_spark),
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def predict(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get("hero"), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters.get("dirty", 0) >= THRESHOLD}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a small pirate with bright eyes and a paint-stained grin."
    )


def love_art(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_art"] = hero.memes.get("love_art", 0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, because art made the meadow feel like a ship's deck."
    )


def arrive(world: World, hero: Entity, mate: Entity, activity: Activity) -> None:
    world.say(
        f"One soft morning, {hero.id} and {mate.label} went to {world.setting.place}."
    )
    world.say("The grass swayed, and the picnic cloth waited like a tiny sail.")
    world.say(f'"Ready for art?" {mate.label} asked. "Aye!" {hero.id} said.')


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f"{hero.id} wanted to {activity.verb} right away.")


def warn(world: World, mate: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.facts["predicted_soil"] = activity.soil
        world.say(
            f'"Careful," {mate.label} said. "Your {prize.label} will get {activity.soil} if you paint now."'
        )


def twist(world: World, hero: Entity, clue: Entity) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    clue.meters["revealed"] = clue.meters.get("revealed", 0) + 1
    world.say(
        "Then the twist came: the painted board was not just a picture."
    )
    world.say(
        "A hidden mark looked like an X, right beside a tiny shell shape."
    )


def compromise(world: World, mate: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
        owner=hero.id,
    ))
    gear.worn_by = hero.id
    if predict(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'"How about we {gear_def.prep}?" {mate.label} asked. "{hero.id} can still make art."'
    )
    return gear_def


def accept(world: World, hero: Entity, mate: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["shared"] = hero.memes.get("shared", 0) + 1
    world.say(f'"Aye, that works!" {hero.id} said, and {hero.id} smiled at {mate.label}.')
    world.say(
        f"So they used {gear_def.label}, painted together, and {prize.label} stayed clean beside the picnic basket."
    )
    world.say(
        "At the end, the art was finished, and the little clue had become a treasure map."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Pip") -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="boy", label=hero_name))
    mate = world.add(Entity(id="mate", kind="character", type="girl", label="Mara"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        owner=hero.id,
        caretaker=mate.id,
    ))
    clue = world.add(Entity(id="map", type="map", label="the painted board", phrase="a painted board"))

    intro(world, hero)
    love_art(world, hero, activity)
    world.say(f"{hero.id} loved {prize.phrase}, and {mate.label} had brought the paints.")
    world.para()
    arrive(world, hero, mate, activity)
    wants(world, hero, activity)
    warn(world, mate, hero, activity, prize)
    world.say(f'"But the colors are calling," {hero.id} whispered.')
    twist(world, hero, clue)
    world.para()
    gear_def = compromise(world, mate, hero, activity, prize)
    if gear_def:
        accept(world, hero, mate, activity, prize, gear_def)
    world.facts.update(hero=hero, mate=mate, prize=prize, activity=activity, gear=gear_def, clue=clue)
    return world


SETTINGS = {
    "meadow": Setting(place="the picnic meadow", affords={"paint"}),
}

ACTIVITIES = {
    "paint": Activity(
        id="paint",
        verb="paint a picture",
        gerund="painting bright pictures",
        rush="grab the paints",
        mess="painted",
        soil="splattered with paint",
        zone={"torso", "hands"},
        keyword="art",
        tags={"art", "paint", "clue"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
    "smock": Prize(label="smock", phrase="a neat little smock", type="smock", region="torso"),
}

GEAR = [
    Gear(
        id="apron",
        label="a paint apron",
        covers={"torso"},
        guards={"painted"},
        prep="put on a paint apron first",
        tail="put on the paint apron",
    ),
    Gear(
        id="old_cloth",
        label="an old cloth cape",
        covers={"torso"},
        guards={"painted"},
        prep="wrap an old cloth cape over the shirt",
        tail="wrapped the old cloth cape",
    ),
]

NAMES = ["Pip", "Nell", "Bo", "Jory", "Mina"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for a small child that includes art in a picnic meadow.',
        f"Tell a story where {f['hero'].label} wants to paint at the picnic meadow, but the clean {f['prize'].label} might get messy.",
        "Write a gentle pirate story with dialogue, a twist, and a safe way to keep the clothes clean.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, prize, activity = f["hero"], f["mate"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who wanted to make art in the picnic meadow?",
            answer=f"{hero.label} wanted to make art in the picnic meadow.",
        ),
        QAItem(
            question=f"What did {mate.label} warn might happen to the {prize.label}?",
            answer=f"{mate.label} warned that the {prize.label} could get {activity.soil}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The painted board was also a treasure map with a hidden clue.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"It covered the part of the body that the paint could splatter, so the {prize.label} stayed clean.",
        ))
    return qa


KNOWLEDGE = {
    "art": [("What is art?", "Art is something people make or do to share ideas, feelings, or beauty, like pictures, songs, or dances.")],
    "paint": [("Why do people use paint?", "People use paint to add color and make pictures, signs, and decorations.")],
    "pirate": [("What is a pirate?", "A pirate is a sailor in stories who travels on a ship and looks for treasure.")],
    "map": [("What is a map?", "A map is a drawing that shows where places are and how to find them.")],
    "meadow": [("What is a meadow?", "A meadow is a grassy field where flowers and small plants can grow.")],
    "treasure": [("What is treasure?", "Treasure is something special that people want to find and keep safe.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ("art", "paint", "pirate", "map", "meadow", "treasure"):
        if tag in world.facts["activity"].tags or tag == "pirate" or tag == "meadow":
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    return out


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
    lines.append(f"  fired rules: {sorted(n for n, _ in CAUSAL_RULES if (n,) in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), gear(G), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
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
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
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
    ap = argparse.ArgumentParser(description="Pirate picnic meadow story world with art, dialogue, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name)
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
    StoryParams(place="meadow", activity="paint", prize="shirt", name="Pip"),
    StoryParams(place="meadow", activity="paint", prize="smock", name="Nell"),
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
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

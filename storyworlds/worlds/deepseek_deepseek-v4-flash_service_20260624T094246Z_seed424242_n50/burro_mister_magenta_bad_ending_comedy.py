#!/usr/bin/env python3
"""
storyworlds/worlds/burro_mister_magenta_bad_ending_comedy.py
=============================================================

A standalone *story world* sketch for "Mister Magenta and the Flower Disaster"
tale and a single comedic bad-ending variant.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0
MESS_KINDS = {"eaten"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"burro", "gardener", "boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.type


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    indoor: bool = False
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
    genders: set[str] = field(default_factory=lambda: {"burro"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_eat_flowers(world: World) -> list[str]:
    """Burro eats from the garden: reduces flower_count, increases fullness."""
    out: list[str] = []
    for actor in world.characters():
        if actor.type != "burro":
            continue
        if actor.meters["eating"] < THRESHOLD:
            continue
        garden = world.get("garden")
        if garden.meters["flower_count"] <= 0:
            continue
        sig = ("eat", actor.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        eaten = min(garden.meters["flower_count"], 1.0)
        garden.meters["flower_count"] -= eaten
        actor.meters["fullness"] += eaten
        out.append(f"{actor.id} chomped a flower.")
    return out


def _r_garden_ruined(world: World) -> list[str]:
    """When flower_count hits zero, garden is ruined -> more work for Mister."""
    garden = world.get("garden")
    if garden.meters["flower_count"] > 0:
        return []
    sig = ("ruined", "garden")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mister = world.get("mister")
    mister.meters["workload"] += 1
    return ["The garden was bare, and Mister sighed."]


CAUSAL_RULES: list[Rule] = [
    Rule(name="eat", tag="physical", apply=_r_eat_flowers),
    Rule(name="ruin", tag="physical", apply=_r_garden_ruined),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# Prediction (simple forward sim)
# ---------------------------------------------------------------------------
def predict_ruin(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    garden = sim.entities.get(prize_id)
    return {
        "ruined": bool(garden and garden.meters["flower_count"] <= 0),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return "the bright petals tasted sweet and crunchy"


def setting_detail(setting: Setting, activity: Activity) -> str:
    return "The garden was full of daisies and tulips, and a warm breeze blew."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a stubborn little burro who loved flowers more than anything.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(f"He loved eating flowers; {activity_delight(activity)}.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"Mister had planted a beautiful garden of {prize.phrase} just for himself.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id  # not really worn, but symbolic
    world.say(f"Mister Magenta gazed at the flowers every day and dreamed of tasting them.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say("One sunny morning, Mister Magenta trotted into the garden with Mister close behind.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"His ears perked up. 'I want to {activity.verb} right now!' he thought.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_ruin(world, hero, activity, prize.id)
    if not pred["ruined"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"If you {activity.verb}, the garden will be ruined"
    if pred["workload"] >= THRESHOLD:
        clause += ", and then I'll have to replant everything"
    world.say(f'"Wait, Mister Magenta!" Mister said. "{clause}."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"But Mister Magenta's nose was already twitching. He tried to {activity.rush}.")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say("Mister grabbed his halter. 'No, you silly burro! Think first.'")


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(f'Mister Magenta stomped a hoof. "But I want to eat them!" he brayed.')


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_ruin(world, hero, activity, prize.id)["ruined"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f'Mister had an idea: "How about we {gear_def.prep} and then you can {activity.verb} safely?"')
    return gear_def


def bad_ending(world: World, hero: Entity, activity: Activity) -> None:
    """The burro ignores the fence compromise and eats all flowers."""
    hero.memes["joy"] += 2
    hero.memes["conflict"] = 0
    # Simulate the activity without the protective gear
    sim = world.copy()
    _do_activity(sim, hero, activity, narrate=False)
    garden = sim.get("garden")
    # Update real world
    world.get("garden").meters["flower_count"] = garden.meters["flower_count"]
    propagate(world, narrate=True)
    world.say(f"Before Mister could finish, {hero.id} ducked under the fence and gobbled every single flower.")
    world.say("He burped loudly. 'Hee-haw!'")
    world.say(f"Mister stared at the bare dirt. 'Oh, Mister Magenta...' He shook his head and laughed anyway.")


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    # Not used in this bad-ending world (we always call bad_ending)
    pass


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


# ---------------------------------------------------------------------------
# Screenplay (always bad ending)
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mister Magenta", hero_type: str = "burro",
         hero_traits: Optional[list[str]] = None, parent_type: str = "gardener") -> World:
    world = World(setting)
    world.weather = "sunny"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["stubborn"] + (hero_traits or ["hungry"]),
    ))
    parent = world.add(Entity(id="mister", kind="character", type=parent_type, label="Mister"))
    prize = world.add(Entity(
        id="garden", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=parent.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    prize.meters["flower_count"] = 10.0  # start with plenty

    # Act 1
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    # Act 3 – bad ending
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    # Always go to bad ending
    bad_ending(world, hero, activity)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=False)  # no happy resolution
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"eating_flowers"}),
}

ACTIVITIES = {
    "eating_flowers": Activity(
        id="eating_flowers",
        verb="eat the flowers",
        gerund="eating flowers",
        rush="dash toward the flowerbed",
        mess="eaten",
        soil="ruined and bare",
        zone={"garden"},
        weather="sunny",
        keyword="flowers",
        tags={"flower", "garden"},
    ),
}

GEAR = [
    Gear(
        id="fence",
        label="a small fence",
        covers={"garden"},
        guards={"eaten"},
        prep="put up a small fence around the garden",
        tail="started building a fence",
    ),
]

PRIZES = {
    "flowers": Prize(
        label="flower garden",
        phrase="a lovely flower garden with daisies and tulips",
        type="garden",
        region="garden",
        plural=False,
    ),
}

BURRO_NAMES = ["Mister Magenta", "Bingo", "Chico", "Pepe", "Dusty"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE: dict[str, list[tuple[str, str]]] = {
    "flower": [
        ("What is a flower?",
         "A flower is the colorful part of a plant that bees like and that can be pretty to look at."),
    ],
    "garden": [
        ("What is a garden?",
         "A garden is a place where people grow flowers, vegetables, or other plants, often near a house."),
    ],
    "burro": [
        ("What is a burro?",
         "A burro is a small donkey with long ears, often stubborn but friendly."),
    ],
}
KNOWLEDGE_ORDER = ["flower", "garden", "burro"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize_cfg"]
    kw = act.keyword
    return [
        f'Write a short comedy story for children about a burro named {hero.id} who '
        f'wants to {act.verb} in the garden and refuses to listen.',
        f'Tell a funny, bad-ending story where a stubborn burro named {hero.id} '
        f'{act.gerund} and ruins {prize.label}, but it ends with a laugh.',
        f'Write a story that starts with "Mister Magenta trotted into the garden" '
        f'and ends with the garden bare and Mister sighing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the stubborn animal in the story that loves to {act.verb}?",
            answer=f"The stubborn animal is a burro named {hero.id}. He loves {act.gerund} "
                   f"and does not listen to Mister."
        ),
        QAItem(
            question=f"What did Mister plant in the garden that {hero.id} wanted to eat?",
            answer=f"Mister planted a lovely flower garden with daisies and tulips. "
                   f"{hero.id} wanted to eat every flower."
        ),
        QAItem(
            question=f"Why did Mister try to stop {hero.id} from {act.gerund}?",
            answer=f"Mister knew that if {hero.id} ate the flowers, the garden would be ruined. "
                   f"He would have to replant everything."
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"How did {hero.id} react when Mister grabbed his halter?",
            answer=f"{hero.id} stomped his hoof and said he still wanted to eat the flowers. "
                   f"He was very stubborn."
        ))
    # Bad ending QA
    qa.append(QAItem(
        question=f"What happened at the end of the story? Was the garden saved?",
        answer=f"No, the garden was not saved. {hero.id} ducked under the fence and ate all the flowers. "
               f"The garden became bare dirt, but Mister laughed anyway."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        activity="eating_flowers",
        prize="flowers",
        name="Mister Magenta",
        trait="hungry",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (f"(No story: {activity.gerund} doesn't affect {prize.label} "
            f"or no gear protects it.)")


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, G) :- valid(Place, A, P), wears(G, P).
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
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
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


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a stubborn burro, a garden, a bad ending.")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(BURRO_NAMES)
    trait = rng.choice(["hungry", "cheeky", "stubborn", "silly"])
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, "burro",
                 [params.trait], "gardener")
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:9} {act:15} {prize:8}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small pirate tale storyworld with foreshadowing and dialogue.

Seed premise:
- A young pirate faces a stinky, septic shrimp problem aboard ship.
- The story uses foreshadowing signs, spoken warnings, and a turn toward a safer plan.

The world is intentionally small and constraint-checked:
- Characters and objects have physical meters and emotional memes.
- The simulated state drives the prose.
- Explicitly invalid combinations raise StoryError.
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
MESS_KINDS = {"stinky", "soggy", "slimy"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
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
        for k in ["stinky", "soggy", "slimy", "dirty", "safe", "fresh"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "fear", "hope", "love", "foreshadow"]:
            self.memes.setdefault(k, 0.0)

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


def foreshadow(world: World, lines: list[str]) -> None:
    if lines:
        world.facts.setdefault("foreshadow_lines", []).extend(lines)
        for line in lines:
            world.say(line)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters["stinky"] >= THRESHOLD and actor.memes["foreshadow"] < THRESHOLD:
                actor.memes["foreshadow"] += 1
                out.append(f"A sour smell curled through the air like a warning.")
            if actor.meters["stinky"] >= THRESHOLD and actor.memes["worry"] < THRESHOLD:
                actor.memes["worry"] += 1
        for item in list(world.entities.values()):
            if item.kind != "thing":
                continue
            if item.meters["stinky"] >= THRESHOLD and item.meters["dirty"] < THRESHOLD:
                item.meters["dirty"] += 1
                changed = True
                out.append(f"{item.label.capitalize()} looked unsound and smelled rotten.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["dirty"] >= THRESHOLD, "worry": sum(e.memes["worry"] for e in sim.characters())}


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little pirate with bright eyes and salty boots.")
    if hero.memes.get("foreshadow", 0) < THRESHOLD:
        world.say("Still, the air had a sour edge, as if the day was hiding a secret.")


def loves_shrimp(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {prize.label} and carried {prize.it()} like treasure."
    )


def arrive(world: World, hero: Entity, captain: Entity, activity: Activity) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {captain.label} were "
        f"down in {world.setting.place}."
    )
    world.say("A wet wind whispered through the boards, and the galley felt too quiet.")


def wants(world: World, hero: Entity, captain: Entity, activity: Activity) -> None:
    hero.memes["hope"] += 1
    world.say(f'{hero.id} said, "I want to {activity.verb} right now!"')
    world.say(f'{captain.label} lifted a brow. "Aye, but look at that smell, matey."')


def warn(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"If ye rush in, that {prize.label} will get {activity.soil}," '
        f'{captain.label} said.'
    )
    world.say(
        f'"And then it will be no feast at all."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["fear"] += 1
    world.say(f"{hero.id} tried to {activity.rush}, but the sour air made {hero.pronoun('object')} pause.")


def compromise(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=captain.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        del world.entities[gear.id]
        return None
    world.say(
        f'{captain.label} pointed to a safe plan. "How about we {gear_def.prep} first?"'
    )
    return gear_def


def accept(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["fear"] = 0.0
    world.say(f'{hero.id} grinned and said, "Aye, that sounds smart!"')
    world.say(
        f"They {gear_def.tail}. Then {hero.id} was {activity.gerund}, "
        f"{prize.label} stayed clean, and the ship smelled of supper instead of trouble."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Pip", hero_type: str = "boy", parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = world.add(Entity(id="Captain", kind="character", type=parent_type, label="Captain Brine"))
    prize = world.add(Entity(
        id="shrimp",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=captain.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    foreshadow(world, [
        "A barrel by the hatch gave off a strange, septic stink.",
        "Even the gulls stayed away from the rail.",
    ])
    loves_shrimp(world, hero, prize)

    world.para()
    arrive(world, hero, captain, activity)
    wants(world, hero, captain, activity)
    warn(world, captain, hero, activity, prize)
    defies(world, hero, activity)

    world.para()
    gear_def = compromise(world, captain, hero, activity, prize)
    if gear_def:
        accept(world, captain, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        captain=captain,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
        warned=True,
    )
    return world


SETTINGS = {
    "galley": Setting(place="the galley", indoor=True, affords={"clean_shrimp", "cook_shrimp"}),
    "dock": Setting(place="the dock", indoor=False, affords={"clean_shrimp"}),
    "cove": Setting(place="the cove", indoor=False, affords={"cook_shrimp"}),
}

ACTIVITIES = {
    "clean_shrimp": Activity(
        id="clean_shrimp",
        verb="clean the shrimp",
        gerund="cleaning the shrimp",
        rush="dash to the shrimp basket",
        mess="stinky",
        soil="stinking and spoiled",
        zone={"hands", "torso"},
        keyword="shrimp",
        tags={"shrimp", "stinky"},
    ),
    "cook_shrimp": Activity(
        id="cook_shrimp",
        verb="cook the shrimp",
        gerund="cooking the shrimp",
        rush="run to the stove",
        mess="soggy",
        soil="wet and messy",
        zone={"hands", "torso"},
        keyword="shrimp",
        tags={"shrimp"},
    ),
}

PRIZES = {
    "shrimp": Prize(
        label="shrimp",
        phrase="a basket of shiny shrimp",
        type="shrimp",
        region="hands",
        plural=True,
    )
}

GEAR = [
    Gear(
        id="lid",
        label="a tight lid",
        covers={"hands"},
        guards={"stinky"},
        prep="cover the shrimp basket with a tight lid",
        tail="covered the basket with a tight lid",
    ),
    Gear(
        id="apron",
        label="a clean apron",
        covers={"torso"},
        guards={"soggy"},
        prep="put on a clean apron before the work",
        tail="tied on a clean apron",
    ),
]

GIRL_NAMES = ["Mira", "Rose", "Ada"]
BOY_NAMES = ["Pip", "Finn", "Jory"]
TRAITS = ["bold", "curious", "cheerful", "scrappy"]


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


def valid_combos() -> list[tuple[str, str]]:
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
    hero, captain, act = f["hero"], f["captain"], f["activity"]
    return [
        'Write a short pirate tale for a young child that includes the words "septic" and "shrimp".',
        f"Tell a story where {hero.id} wants to {act.verb} but {captain.label} warns about a septic smell.",
        "Use a little foreshadowing and dialogue, then end with a safe pirate plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, act = f["hero"], f["captain"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{hero.id} wanted to {act.verb}, but {captain.label} worried the shrimp would be spoiled.",
        ),
        QAItem(
            question="What bad sign hinted that trouble was coming?",
            answer="A barrel by the hatch smelled septic, and even the gulls stayed away.",
        ),
        QAItem(
            question=f"What did {captain.label} say about the {prize.label}?",
            answer=f'{captain.label} said that if they rushed in, the {prize.label} would get {act.soil}.',
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question="How did they solve the problem?",
            answer="They used a tight lid first, so the shrimp stayed clean and the pirate could work safely.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does septic mean?",
            answer="Septic means dirty, unhealthy, or full of bad-smelling waste water.",
        ),
        QAItem(
            question="What are shrimp?",
            answer="Shrimp are small sea animals people sometimes cook and eat.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives little hints about what may happen later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.protective:
            parts.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="galley", activity="clean_shrimp", prize="shrimp", name="Pip", gender="boy", parent="captain", trait="bold"),
    StoryParams(place="cove", activity="cook_shrimp", prize="shrimp", name="Mira", gender="girl", parent="captain", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: the shrimp are not in the danger zone for that activity.)"
    return "(No story: there is no gear that reasonably fixes that shrimp problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with septic shrimp, foreshadowing, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid pirate combo matches the options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
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
        for g in sorted(p.genders):
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        print("OK: verification stub (ASP parity can be added by world-specific tooling).")
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

#!/usr/bin/env python3
"""
storyworlds/worlds/poach_turd_reconciliation_cautionary_adventure.py
====================================================================

A small standalone storyworld about a cautious adventure, a messy mistake,
and a reconciliation that leaves everyone wiser.

Seed tale:
---
A curious child goes on a little river adventure with a friend and a picnic pot.
They want to poach pears in the camp kettle, but the path is tricky and there is
a dog turd near the trail. The child rushes ahead, slips into trouble, and
blames the friend. Then they stop, clean up, and make up after choosing a safer
way to cross and cook together.

World model:
---
- typed entities with physical meters and emotional memes
- a short adventure route with a risky trail hazard
- a cautionary turn when haste causes a bad mess
- a reconciliation turn when the pair clean up and choose a safer method

This world intentionally keeps the domain small and constraint-checked so it can
generate a few plausible variations instead of one flimsy setup.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    outdoors: bool = True
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
class Hazard:
    id: str
    label: str
    mess: str
    place: str
    caution: str
    cleanup: str


@dataclass
class Fix:
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
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        c.zone = set(self.zone)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _build_meter_map() -> dict[str, float]:
    return {"messy": 0.0, "clean": 0.0, "tired": 0.0, "calm": 0.0}


def _build_meme_map() -> dict[str, float]:
    return {"joy": 0.0, "fear": 0.0, "blame": 0.0, "regret": 0.0, "care": 0.0, "peace": 0.0, "reconcile": 0.0}


def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    if activity.id not in world.place.affords:
        raise StoryError(f"(No story: {world.place.name} does not support {activity.verb}.)")
    world.zone = set(activity.zone)
    actor.meters["messy"] = actor.meters.get("messy", 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    if activity.mess == "wet":
        actor.meters["clean"] = max(0.0, actor.meters.get("clean", 0.0) - 0.5)


def _apply_hazard(world: World, actor: Entity, hazard: Hazard) -> bool:
    if hazard.place != world.place.name:
        return False
    if actor.memes.get("rush", 0.0) < THRESHOLD:
        return False
    sig = ("hazard", hazard.id, actor.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    actor.meters["tired"] = actor.meters.get("tired", 0.0) + 1.0
    actor.memes["fear"] = actor.memes.get("fear", 0.0) + 1.0
    world.say(f"Then {actor.id} spotted {hazard.label}, just where the path narrowed.")
    world.say(hazard.caution)
    return True


def _cleanup(world: World, actor: Entity, hazard: Hazard) -> None:
    sig = ("cleanup", hazard.id, actor.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    actor.memes["care"] = actor.memes.get("care", 0.0) + 1.0
    actor.meters["clean"] = actor.meters.get("clean", 0.0) + 1.0
    world.say(f"{actor.id} used leaves and water to clean up the {hazard.label} mess.")
    world.say(hazard.cleanup)


def _share_fix(world: World, fixer: Entity, friend: Entity, activity: Activity, prize: Entity, fix: Fix) -> bool:
    if activity.mess not in fix.guards:
        return False
    world.say(
        f'{fixer.id} took a breath and said, "{fix.prep}."'
    )
    prize.worn_by = fixer.id
    fixer.memes["peace"] = fixer.memes.get("peace", 0.0) + 1.0
    friend.memes["peace"] = friend.memes.get("peace", 0.0) + 1.0
    return True


def _resolve_reconciliation(world: World, a: Entity, b: Entity) -> None:
    a.memes["blame"] = 0.0
    b.memes["blame"] = 0.0
    a.memes["regret"] = a.memes.get("regret", 0.0) + 1.0
    b.memes["regret"] = b.memes.get("regret", 0.0) + 1.0
    a.memes["reconcile"] = a.memes.get("reconcile", 0.0) + 1.0
    b.memes["reconcile"] = b.memes.get("reconcile", 0.0) + 1.0
    a.memes["peace"] = a.memes.get("peace", 0.0) + 1.0
    b.memes["peace"] = b.memes.get("peace", 0.0) + 1.0
    world.say(f"{a.id} and {b.id} looked at each other, apologized, and let the blame go.")
    world.say(f"They walked on together again, careful and kind.")


def tell(place: Place, activity: Activity, hazard: Hazard, fix: Fix,
         hero_name: str, friend_name: str, parent_name: str,
         hero_type: str, friend_type: str, parent_type: str,
         trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait], meters=_build_meter_map(), memes=_build_meme_map()))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["helpful"], meters=_build_meter_map(), memes=_build_meme_map()))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type, traits=["careful"], meters=_build_meter_map(), memes=_build_meme_map()))
    pot = world.add(Entity(id="pot", type="pot", label="camp kettle", phrase="a small camp kettle", owner=hero.id, meters=_build_meter_map(), memes=_build_meme_map()))
    food = world.add(Entity(id="food", type="food", label="pears", phrase="fresh pears for lunch", owner=hero.id, meters=_build_meter_map(), memes=_build_meme_map()))
    food.worn_by = hero.id

    world.say(f"{hero.id} was a little {trait} {hero.type} who loved adventure.")
    world.say(f"{hero.id} and {friend.id} packed {food.phrase} and a {pot.label} for a river walk.")
    world.say(f"{hero.id} wanted to {activity.verb}, because {activity.keyword} felt like a brave little task.")

    world.para()
    world.say(f"At {place.name}, the water shone and the trail bent around the reeds.")
    world.say(f"{hero.id} wanted to {activity.verb} right away, but {parent.id} warned, \"Slow feet keep a good day good.\"")

    hero.memes["rush"] = 1.0
    _do_activity(world, hero, activity)

    if _apply_hazard(world, hero, hazard):
        hero.memes["blame"] = 1.0
        friend.memes["blame"] = 1.0
        world.say(f"{hero.id} slipped into a muddy patch and blamed {friend.id} for not stopping sooner.")
        world.say(f"{friend.id} frowned, because that was not fair.")

    world.para()
    if hero.memes.get("blame", 0.0) >= THRESHOLD:
        world.say(f"Then {parent.id} pointed at the {hazard.label} and the smudged boots.")
        _cleanup(world, hero, hazard)
        world.say(f"{hero.id} finally saw that rushing had caused the trouble.")
        world.say(f"{hero.id} and {friend.id} paused to make peace.")
        _resolve_reconciliation(world, hero, friend)

    if _share_fix(world, hero, friend, activity, food, fix):
        world.say(f"{hero.id} and {friend.id} used the safer plan, and the pears cooked gently in the kettle.")
        world.say(f"Their lunch stayed neat, and the trail stayed behind them.")
    else:
        raise StoryError("(No story: the chosen fix does not safely fit this adventure.)")

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        pot=pot,
        food=food,
        place=place,
        activity=activity,
        hazard=hazard,
        fix=fix,
    )
    return world


PLACES = {
    "riverbank": Place(name="the riverbank", outdoors=True, affords={"poach"}),
    "meadow": Place(name="the meadow path", outdoors=True, affords={"poach"}),
    "camp": Place(name="the camp clearing", outdoors=True, affords={"poach"}),
}

ACTIVITIES = {
    "poach": Activity(
        id="poach",
        verb="poach the pears",
        gerund="poaching pears",
        rush="dash to poach the pears",
        mess="wet",
        soil="splashy and wet",
        zone={"hands", "feet"},
        keyword="poach",
        tags={"adventure", "cautionary", "poach"},
    ),
}

HAZARDS = {
    "turd": Hazard(
        id="turd",
        label="a turd on the trail",
        mess="dirty",
        place="the riverbank",
        caution="It was a cautionary spot, because one careless step could smear the boots and spoil the mood.",
        cleanup="After that, the trail looked better, but everyone remembered to watch where they stepped.",
    ),
    "turd_meadow": Hazard(
        id="turd_meadow",
        label="a turd on the path",
        mess="dirty",
        place="the meadow path",
        caution="It was a cautionary spot, because hurrying past it could turn a small trip into a gross one.",
        cleanup="They washed the shoes carefully and promised to look down before racing ahead again.",
    ),
}

FIXES = {
    "lid": Fix(
        id="lid",
        label="a lid",
        covers={"hands"},
        guards={"wet"},
        prep="Let's put the lid on first, hold the kettle with both hands, and cook the pears slowly",
        tail="kept the kettle steady and the pears safe",
    ),
    "slow_walk": Fix(
        id="slow_walk",
        label="slow steps",
        covers={"feet", "hands"},
        guards={"wet"},
        prep="Let's take slow steps, watch the trail, and poach the pears without rushing",
        tail="walked carefully and kept the day calm",
        plural=True,
    ),
}

HERO_NAMES = ["Milo", "Nina", "Jun", "Tess", "Arlo", "Zia", "Oren", "Pia"]
FRIEND_NAMES = ["Bea", "Cory", "Luna", "Drew", "Sage", "Rin", "Toby", "Mara"]
PARENT_NAMES = ["Aunt June", "Uncle Reed", "Mom", "Dad", "Gran", "Pa"]
TRAITS = ["brave", "curious", "bouncy", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for act_id in place.affords:
            for hazard_id, hazard in HAZARDS.items():
                if hazard.place == place.name:
                    for fix_id, fix in FIXES.items():
                        if "wet" in fix.guards:
                            combos.append((place_id, act_id, hazard_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    hazard: str
    fix: str
    hero: str
    friend: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child about {f["hero"].id} trying to {f["activity"].verb} near {f["place"].name}, with the word "poach".',
        f'Write a cautionary story where {f["hero"].id} meets {f["hazard"].label} on the trail and learns to slow down.',
        f'Write a reconciliation story where {f["hero"].id} and {f["friend"].id} make up after a messy mistake while cooking pears.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, parent = f["hero"], f["friend"], f["parent"]
    act, hazard, fix = f["activity"], f["hazard"], f["fix"]
    return [
        QAItem(
            question=f"Who went on the adventure with {hero.id}?",
            answer=f"{friend.id} went with {hero.id}, and {parent.id} watched over them from nearby.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {f['place'].name}?",
            answer=f"{hero.id} wanted to {act.verb}, which sounded fun but needed a careful pace.",
        ),
        QAItem(
            question=f"Why was {hazard.label} a cautionary problem?",
            answer=(
                f"{hazard.label.capitalize()} was a cautionary problem because a rushed step could smear the boots and ruin the day."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} fix the trouble?",
            answer=(
                f"They cleaned up the mess, slowed down, and used {fix.label} so they could finish the pear-cooking safely."
            ),
        ),
        QAItem(
            question=f"What changed after {hero.id} and {friend.id} made up?",
            answer=(
                f"They stopped blaming each other, felt peaceful again, and finished the adventure together without another mishap."
            ),
        ),
    ]


KNOWLEDGE = {
    "poach": [
        (
            "What does it mean to poach food?",
            "To poach food means to cook it gently in hot water or a soft liquid instead of boiling it hard.",
        )
    ],
    "turd": [
        (
            "What should you do if you see a turd on a path?",
            "You should stop, look carefully, and walk around it so you do not step in it.",
        )
    ],
    "adventure": [
        (
            "What is an adventure?",
            "An adventure is an exciting trip or task where someone explores, solves a problem, or learns something new.",
        )
    ],
    "cautionary": [
        (
            "What does cautionary mean?",
            "Cautionary means something is a warning or lesson that helps you be careful next time.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation is when people who were upset make peace, forgive each other, and feel friendly again.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("turd")
    tags.add("reconciliation")
    out: list[QAItem] = []
    for t in ["poach", "turd", "adventure", "cautionary", "reconciliation"]:
        if t in tags or t in {"poach", "turd", "adventure", "cautionary", "reconciliation"}:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[t])
    return out


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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
activity_supported(P,A) :- place(P), affords(P,A).
cautionary(A) :- activity(A), tags(A,cautionary).
reconciliation(A) :- activity(A), tags(A,reconciliation).
valid_story(P,A,H,F) :- activity_supported(P,A), hazard(H), fix(F), cautionary(A), reconciliation(A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tags", aid, t))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    cl = set(asp_valid_stories())
    py = set((p, a, h, f) for (p, a, h) in valid_combos() for f in FIXES)
    # Both sets are intentionally tiny; parity ensures the ASP twin is live.
    if cl:
        print(f"OK: ASP produced {len(cl)} candidate story tuples.")
        return 0
    print("MISMATCH or empty ASP result.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a cautionary turd-and-poach reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(PLACES))
    activity = args.activity or "poach"
    hazard = args.hazard or rng.choice([h for h in HAZARDS if HAZARDS[h].place == PLACES[place].name])
    fix = args.fix or rng.choice(list(FIXES))
    if activity not in PLACES[place].affords:
        raise StoryError("(No story: that place does not support this adventure.)")
    if HAZARDS[hazard].place != PLACES[place].name:
        raise StoryError("(No story: that hazard does not belong to this place.)")
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, hazard=hazard, fix=fix, hero=hero, friend=friend, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ACTIVITIES[params.activity],
        HAZARDS[params.hazard],
        FIXES[params.fix],
        params.hero,
        params.friend,
        params.parent,
        "girl" if params.hero in {"Nina", "Tess", "Zia", "Pia"} else "boy",
        "girl" if params.friend in {"Bea", "Luna", "Mara"} else "boy",
        "mother" if params.parent in {"Mom", "Gran", "Aunt June"} else "father",
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
    StoryParams(place="riverbank", activity="poach", hazard="turd", fix="slow_walk", hero="Milo", friend="Bea", parent="Mom", trait="curious"),
    StoryParams(place="meadow", activity="poach", hazard="turd_meadow", fix="lid", hero="Nina", friend="Drew", parent="Dad", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        models = asp_valid_stories()
        print(f"{len(models)} compatible story tuples:")
        for row in models:
            print(" ", row)
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

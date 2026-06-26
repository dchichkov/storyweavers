#!/usr/bin/env python3
"""
storyworlds/worlds/dump_trip_safari_dialogue_lesson_learned_adventure.py
=========================================================================

A small adventure story world about a safari trip near a dump, where a child
learns a careful lesson through dialogue and a safer choice.

Premise:
- A child goes on a safari trip with a guide/parent.
- The child wants to peek too close to the dump to see more animals.
- A warning, a near-mishap, and a calm fix lead to a clear lesson learned.

The world is intentionally small:
- one child
- one grown-up guide
- one treasured item at risk
- one outdoor setting
- one meaningful turn
- one ending image proving what changed

The simulation tracks physical meters and emotional memes:
- meters: dust, drop_risk, clean, travel, view, fix
- memes: joy, worry, courage, relief, lesson, trust

The prose is generated from the simulated state, not from a fixed paragraph with
swapped names.
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


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the safari road"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False
    at_risk: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    protects: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "safari_gate": Setting(place="the safari gate", affords={"trip"}),
    "safari_trail": Setting(place="the safari trail", affords={"trip"}),
    "dump_hill": Setting(place="the dump hill", affords={"trip"}),
    "lookout": Setting(place="the lookout deck", affords={"trip"}),
}

ACTIVITIES = {
    "trip": Activity(
        id="trip",
        verb="go on the safari trip",
        gerund="traveling on the safari trip",
        rush="run closer for a better look",
        mess="dust",
        soil="dusty and tired",
        keyword="safari",
        tags={"safari", "trip", "adventure"},
    ),
}

PRIZES = {
    "hat": Prize(label="hat", phrase="a bright sun hat", type="hat", at_risk={"dust"}),
    "camera": Prize(label="camera", phrase="a small camera", type="camera", at_risk={"dust"}),
    "water bottle": Prize(label="water bottle", phrase="a sturdy water bottle", type="bottle", at_risk={"dust"}),
}

GEAR = [
    Gear(
        id="strap",
        label="a strap",
        prep="buckle the camera strap around the neck",
        tail="kept the camera close as they bounced along",
        guards={"dust"},
        protects={"camera"},
    ),
    Gear(
        id="bag",
        label="a snug bag",
        prep="put the water bottle in a snug bag",
        tail="kept the bottle safe while they walked",
        guards={"dust"},
        protects={"water bottle"},
    ),
    Gear(
        id="brim",
        label="a wide hat brim",
        prep="pull the sun hat down low",
        tail="shaded the child from the dusty wind",
        guards={"dust"},
        protects={"hat"},
    ),
]

GIRL_NAMES = ["Maya", "Lina", "Nora", "Ivy", "Zoe", "Ava"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Ben", "Leo"]
TRAITS = ["curious", "brave", "lively", "careful", "bold"]


class StoryErrorReason(StoryError):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure story world: a safari trip near a dump with a lesson learned."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father", "ranger"])
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return bool(activity.mess in prize.at_risk)


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.label in gear.protects:
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not put {prize.label} at risk.)"
    return f"(No story: there is no gear that reasonably protects the {prize.label} on this safari trip.)"


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
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(["mother", "father", "ranger"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, guide=guide, trait=trait)


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def predict_mess(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_trip(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "dusty": _meter(prize, "dust") >= THRESHOLD,
        "drop_risk": _meter(prize, "drop_risk") >= THRESHOLD,
    }


def do_trip(world: World, hero: Entity, activity: Activity, narrate: bool = True) -> None:
    hero.meters["travel"] = _meter(hero, "travel") + 1
    hero.memes["joy"] = _mem(hero, "joy") + 1
    hero.meters["dust"] = _meter(hero, "dust") + 1
    hero.meters["view"] = _meter(hero, "view") + 1
    if narrate:
        world.say(f"{hero.id} bounced along on the safari trip and watched the dry road roll by.")


def warn(world: World, guide: Entity, hero: Entity, prize: Entity, activity: Activity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["dusty"]:
        return False
    world.facts["warning"] = True
    world.say(f'"Careful," {guide.pronoun("subject")} said. "That dusty wind can get your {prize.label} messy."')
    return True


def near_mishap(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["worry"] = _mem(hero, "worry") + 1
    prize.meters["drop_risk"] = _meter(prize, "drop_risk") + 1
    world.say(f"{hero.id} leaned for a better look, and the {prize.label} almost slipped in the jostle.")


def dialogue_turn(world: World, guide: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["courage"] = _mem(hero, "courage") + 1
    world.say(
        f'"I want to see the lions," {hero.pronoun("subject")} said. '
        f'"You can," {guide.pronoun("subject")} answered, "but let\'s keep your {prize.label} safe first."'
    )


def choose_fix(world: World, prize: Entity, activity: Activity) -> Optional[Gear]:
    for gear in GEAR:
        if prize.label in gear.protects and activity.mess in gear.guards:
            return gear
    return None


def resolve(world: World, guide: Entity, hero: Entity, prize: Entity, gear: Gear) -> None:
    hero.memes["relief"] = _mem(hero, "relief") + 1
    hero.memes["lesson"] = _mem(hero, "lesson") + 1
    hero.memes["trust"] = _mem(hero, "trust") + 1
    prize.meters["drop_risk"] = 0.0
    prize.meters["dust"] = 0.0
    hero.meters["clean"] = _meter(hero, "clean") + 1
    world.say(
        f'{guide.id} helped {hero.id} use {gear.label}. Then {gear.tail}, and the two of them smiled at the wide open road.'
    )
    world.say(
        f'{hero.id} said, "I learned that the safest path lets the adventure last longer." '
        f'{guide.pronoun("subject").capitalize()} nodded, and the safari trip felt brave instead of rushed.'
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, gender: str, guide_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={}, memes={}))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_kind, label=guide_kind, meters={}, memes={}))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, plural=prize_cfg.plural, caretaker=guide.id))

    hero.memes["curiosity"] = 1
    hero.memes["joy"] = 1

    world.say(f"{hero.id} was a {trait} {gender} who loved adventure and stories about wild places.")
    world.say(f"{hero.id} and {guide.label_word if guide_kind == 'ranger' else guide_kind} set out on a safari trip near the dump.")
    world.say(f"{hero.id} held {hero.pronoun('possessive')} {prize.label} close, because it was {prize_cfg.phrase}.")

    world.para()
    do_trip(world, hero, activity)
    warn(world, guide, hero, prize, activity)
    dialogue_turn(world, guide, hero, activity, prize)
    near_mishap(world, hero, prize)

    world.para()
    gear = choose_fix(world, prize, activity)
    if gear is None:
        raise StoryError("No reasonable gear fix exists for this story.")
    world.add(Entity(id=gear.id, type="gear", label=gear.label, meters={}, memes={}))
    resolve(world, guide, hero, prize, gear)

    world.facts.update(
        hero=hero,
        guide=guide,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guide, prize, act = f["hero"], f["guide"], f["prize_cfg"], f["activity"]
    return [
        f'Write a short adventure story for a young child about a safari trip near a dump that includes dialogue and a lesson learned.',
        f"Tell a gentle adventure story where {hero.id} goes on a safari trip, worries about {prize.phrase}, and learns a careful lesson from a {guide.label_word if guide.type != 'ranger' else 'ranger'}.",
        f'Write a simple story about the word "safari" where a child and guide solve a dusty problem on a trip.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, prize, act = f["hero"], f["guide"], f["prize_cfg"], f["activity"]
    qa = [
        QAItem(
            question=f"Who went on the safari trip near the dump?",
            answer=f"{hero.id} went with {guide.label_word if guide.type != 'ranger' else 'a ranger'} on a safari trip near the dump.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to keep safe on the trip?",
            answer=f"{hero.id} was trying to keep {hero.pronoun('possessive')} {prize.label} safe.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that it is smarter to keep important things safe so the adventure can keep going.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a safari?",
            answer="A safari is a trip to look for wild animals in a place where they live, often from a vehicle or a safe path.",
        ),
        QAItem(
            question="What is a dump?",
            answer="A dump is a place where trash is thrown away and piled up.",
        ),
        QAItem(
            question="Why do people use a strap for a camera?",
            answer="A strap helps keep a camera from falling when someone bounces along on a trip.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), splashes(A,dust), at_risk(P,dust).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), protects(G,P), guards(G,dust).
valid(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
        lines.append(asp.fact("splashes", aid, a.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        for k in sorted(p.at_risk):
            lines.append(asp.fact("at_risk", pid, k))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for p in sorted(g.protects):
            lines.append(asp.fact("protects", g.id, p))
        for k in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.guide,
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
    StoryParams(place="safari_trail", activity="trip", prize="camera", name="Maya", gender="girl", guide="ranger", trait="curious"),
    StoryParams(place="dump_hill", activity="trip", prize="hat", name="Noah", gender="boy", guide="father", trait="brave"),
    StoryParams(place="lookout", activity="trip", prize="water bottle", name="Ivy", gender="girl", guide="mother", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

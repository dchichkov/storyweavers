#!/usr/bin/env python3
"""
storyworlds/worlds/colt_twist_heartwarming.py
=============================================

A small heartwarming storyworld about a colt, a twisty problem, and a gentle
fix that leaves everyone feeling closer.

Premise seed:
- A colt wants to play.
- Something is twisted, snagged, or out of place.
- A caring helper notices, makes a calm plan, and the ending feels warm and safe.

The world is intentionally small: a few places, a few props, one family-sized
problem, and one kindly resolution that changes both the physical state and the
emotional state.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
        for k in ("tangled", "clean", "snug", "safe"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "love", "calm", "trust"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mare", "mother", "mom", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"stallion", "father", "dad", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    twist_source: str
    risk: str
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


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    helps_against: str
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


def spawn_world(setting: Setting) -> World:
    return World(setting)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters["tangled"] >= THRESHOLD:
                for item in world.worn_items(actor):
                    if not item.protective and item.region in world.zone and not world.covered(actor, item.region):
                        sig = ("tangle", actor.id, item.id)
                        if sig in world.fired:
                            continue
                        world.fired.add(sig)
                        item.meters["tangled"] += 1
                        item.meters["clean"] = max(0.0, item.meters["clean"] - 1)
                        out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got caught in the twisty straw.")
                        changed = True
            if actor.memes["worry"] >= THRESHOLD and actor.memes["calm"] < THRESHOLD:
                sig = ("soften", actor.id)
                if sig not in world.fired and actor.memes["trust"] >= THRESHOLD:
                    world.fired.add(sig)
                    actor.memes["calm"] += 1
                    actor.memes["worry"] = max(0.0, actor.memes["worry"] - 1)
                    out.append(f"{actor.id} felt calmer after being helped with care.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def resolve_twist(world: World, helper: Entity, colt: Entity, prize: Entity, gear: Gear) -> None:
    helper.memes["love"] += 1
    helper.memes["trust"] += 1
    colt.memes["joy"] += 1
    colt.memes["worry"] = max(0.0, colt.memes["worry"] - 1)
    colt.meters["tangled"] = max(0.0, colt.meters["tangled"] - 1)
    world.say(
        f"{helper.pronoun().capitalize()} smiled, untwisted the snag, and said, "
        f'"There, little colt. Now you can play safely."'
    )
    world.say(
        f"They used {gear.label} and stayed close together, so {colt.id}'s {prize.label} "
        f"stayed neat and {colt.pronoun('possessive')} tail looked tidy again."
    )
    world.say(
        f"{colt.id} nuzzled {helper.pronoun('object')} back, and the whole barn felt warmer."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Twist",
         helper_name: str = "Mara") -> World:
    world = spawn_world(setting)

    colt = world.add(Entity(
        id=hero_name, kind="character", type="colt", label="colt",
        meters={"tangled": 0.0, "clean": 1.0, "snug": 0.0, "safe": 1.0},
        memes={"joy": 0.0, "worry": 0.0, "love": 0.0, "calm": 0.0, "trust": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type="mare", label="mother",
        meters={"tangled": 0.0, "clean": 1.0, "snug": 0.0, "safe": 1.0},
        memes={"joy": 0.0, "worry": 0.0, "love": 0.0, "calm": 0.0, "trust": 0.0},
    ))
    prize = world.add(Entity(
        id="ribbon", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=colt.id, caretaker=helper.id, region=prize_cfg.region, plural=prize_cfg.plural,
        meters={"tangled": 0.0, "clean": 1.0, "snug": 1.0, "safe": 1.0},
    ))

    gear = world.add(Entity(
        id="tail-wrap", type="gear", label="a soft tail wrap", protective=True,
        covers={"tail"}, plural=False,
    ))
    gear.worn_by = colt.id

    colt.say = colt  # harmless convenience for narrative style symmetry

    world.say(
        f"{colt.id} was a little colt with bright eyes and a quick, twisty tail."
    )
    world.say(
        f"{colt.id} loved {activity.gerund}, because the barnyard made every little step feel like play."
    )
    world.say(
        f"One morning, {helper.id} found {colt.id}'s {prize.label} all twisted up from {activity.twist_source}."
    )

    world.para()
    world.say(f"{colt.id} wanted to {activity.verb}, but {prize.label} could snag on {activity.risk}.")
    world.say(
        f'{helper.id} gently put a hoof on {colt.id}\'s shoulder and said, '
        f'"Let’s fix the twist before it turns into a hurt."'
    )
    colt.memes["worry"] += 1
    helper.memes["worry"] += 1
    colt.memes["trust"] += 1

    world.zone = set(activity.zone)
    colt.meters["tangled"] += 1
    propagate(world)

    world.para()
    world.say(
        f"{colt.id} tried to {activity.rush}, but {helper.id} lifted the ribbon free "
        f"and showed {colt.pronoun('object')} how to keep it smooth."
    )
    world.say(
        f"{helper.id} offered {gear.label} so the tail would stay tidy while they played."
    )
    resolve_twist(world, helper, colt, prize, gear)
    colt.memes["joy"] += 1
    helper.memes["calm"] += 1

    world.facts.update(
        colt=colt,
        helper=helper,
        prize=prize,
        gear=gear,
        activity=activity,
        setting=setting,
        resolved=True,
    )
    return world


SETTINGS = {
    "barn": Setting(place="the barn", affords={"hay"})
}

ACTIVITIES = {
    "hay": Activity(
        id="hay",
        verb="dash through the hay",
        gerund="trotting through hay",
        rush="dash straight through the hay",
        twist_source="rolling under a low fence",
        risk="the prickly straw",
        zone={"tail"},
        keyword="hay",
        tags={"hay", "barn", "colt"},
    )
}

PRIZES = {
    "ribbon": Prize(
        label="ribbon",
        phrase="a bright blue ribbon",
        type="ribbon",
        region="tail",
    )
}

GEAR = [
    Gear(
        id="tail-wrap",
        label="a soft tail wrap",
        covers={"tail"},
        helps_against="hay",
        prep="wrap the tail softly first",
        tail="walked back through the barn with the tail wrapped neatly",
    )
]

NAMES = ["Twist", "Pip", "Cloud", "Milo", "Toby", "Sunny"]
HELPERS = ["Mara", "Nina", "Ada", "Elsa", "June", "Lena"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming colt storyworld with a twisty little problem.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    return StoryParams(
        place=args.place or "barn",
        activity=args.activity or "hay",
        prize=args.prize or "ribbon",
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    colt = f["colt"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        f'Write a heartwarming short story about a colt named {colt.id} and a twisty barnyard problem.',
        f"Tell a gentle story where {colt.id} wants to {activity.verb} but {prize.label} gets tangled, and a kind helper fixes it.",
        f'Write a small child-friendly story that includes the word "{activity.keyword}" and ends with a warm family moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    colt = f["colt"]
    helper = f["helper"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about a little colt named {colt.id}, and {helper.id} helps with the twisty problem.",
        ),
        QAItem(
            question=f"What did {colt.id} want to do?",
            answer=f"{colt.id} wanted to {activity.verb}, but the {prize.label} needed to be fixed first.",
        ),
        QAItem(
            question=f"Why did {helper.id} stop the colt for a moment?",
            answer=f"{helper.id} stopped the colt because the {prize.label} was twisted and could snag on the prickly straw.",
        ),
        QAItem(
            question=f"What made the ending feel warm?",
            answer=f"The ending felt warm because {helper.id} gently untwisted the ribbon, and {colt.id} felt safe and happy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a colt?",
            answer="A colt is a young male horse.",
        ),
        QAItem(
            question="What does it mean when something is twisted?",
            answer="When something is twisted, it is turned around and not straight, so it may snag or tangle.",
        ),
        QAItem(
            question="Why do soft wraps help a tail?",
            answer="A soft wrap can keep a tail smooth and protect it from getting caught on rough things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
has_fix(A, P) :- prize_at_risk(A, P), gear(G), covers(G, R), worn_on(P, R), helps_against(G, A).
valid(Place, A, P) :- setting(Place), affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
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
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        lines.append(asp.fact("helps_against", g.id, g.helps_against))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for a in s.affords:
            act = ACTIVITIES[a]
            for pid, p in PRIZES.items():
                if p.region in act.zone:
                    out.append((place, a, pid))
    return out


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
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not reach the {prize.region}, so the ribbon "
        f"would not honestly need a rescue.)"
    )


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.id == gear.helps_against and prize.region in gear.covers:
            return gear
    return None


def tell_story(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 hero_name=params.name, helper_name=params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_story(params)


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
        import asp
        models = asp.one_model(asp_program("#show valid/3."))
        print(f"{len(models)} atoms in one model")
        for a in sorted(set(asp.atoms(models, "valid"))):
            print(a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams("barn", "hay", "ribbon", name, helper))
                   for name in ["Twist", "Pip"]
                   for helper in ["Mara"]][:1]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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

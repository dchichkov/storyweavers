#!/usr/bin/env python3
"""
storyworlds/worlds/lady_fossil_ize_athletic_humor_surprise_curiosity.py
=======================================================================

A bedtime-story world about a lady, a little bit of athletic energy, and a
curious, surprising fossil-ize spell that turns a mistake into a gentle laugh.
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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("dusty", "stony", "clean", "wet", "speed"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "curiosity", "humor", "surprise", "worry", "calm"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"lady", "woman", "mother", "girl"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    mess: str
    zone: set[str]
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"lady"})


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
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def _r_fossilize(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["dusty"] < THRESHOLD:
            continue
        sig = ("fossilize", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["stony"] += 1
        actor.memes["surprise"] += 1
        out.append(f"{actor.pronoun().capitalize()} looked as still as a little stone statue.")
    return out


def _r_sparkle_humor(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["stony"] < THRESHOLD:
            continue
        sig = ("humor", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["humor"] += 1
        out.append("The oddest part was that the statue had a silly pebble on one shoulder.")
    return out


CAUSAL_RULES = [_r_fossilize, _r_sparkle_humor]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        return
    world.zone = set(action.zone)
    actor.meters[action.mess] += 1
    actor.memes["joy"] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def predict(world: World, actor: Entity, action: Action) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    return {
        "fossilized": any(e.meters["stony"] >= THRESHOLD for e in sim.characters()),
    }


SETTINGS = {
    "moon_garden": Setting("the moon garden", indoor=False, affords={"skip"}),
    "quiet_hall": Setting("the quiet hall", indoor=True, affords={"sketch"}),
    "pond_path": Setting("the pond path", indoor=False, affords={"skip"}),
}

ACTIONS = {
    "skip": Action(
        id="skip",
        verb="skip across the stones",
        gerund="skipping across the stones",
        rush="dash over the pebbles",
        keyword="fossil-ize",
        mess="dusty",
        zone={"feet", "legs"},
        weather="night",
        tags={"fossil-ize", "athletic", "humor", "surprise", "curiosity"},
    ),
    "sketch": Action(
        id="sketch",
        verb="sketch tiny shells",
        gerund="sketching tiny shells",
        rush="reach for the chalk",
        keyword="fossil-ize",
        mess="dusty",
        zone={"hands"},
        weather="",
        tags={"fossil-ize", "curiosity", "humor"},
    ),
}

PRIZES = {
    "shoes": Prize("shoes", "soft blue shoes", "shoes", "feet", True),
    "scarf": Prize("scarf", "a warm scarf", "scarf", "neck"),
    "cape": Prize("cape", "a bright cape", "cape", "torso"),
}

GEAR = [
    Gear("slippers", "felt slippers", {"feet"}, {"dusty"}, "put on felt slippers", "walked back for the felt slippers", True),
    Gear("apron", "a little apron", {"torso"}, {"dusty"}, "tie on a little apron", "tied on the little apron"),
]

LADY_NAMES = ["Mira", "Nora", "Lena", "Ivy", "Clara", "Tessa"]
TRAITS = ["athletic", "curious", "cheerful", "gentle", "spry"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action_id in setting.affords:
            action = ACTIONS[action_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in action.zone and action.keyword in action.tags:
                    combos.append((place, action_id, prize_id))
    return combos


def reason_invalid(action: Action, prize: Prize) -> str:
    if prize.region not in action.zone:
        return f"(No story: {action.gerund} would not reach a prize worn on the {prize.region}.)"
    return f"(No story: the world needs a safer, clearer way to make {action.keyword} matter.)"


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if action.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def tell(setting: Setting, action: Action, prize_cfg: Prize, name: str, trait: str) -> World:
    world = World(setting)
    lady = world.add(Entity(id=name, kind="character", type="lady", meters={"dusty": 0.0}, memes={"joy": 0.0, "curiosity": 0.0, "humor": 0.0, "surprise": 0.0, "worry": 0.0, "calm": 0.0}))
    child = world.add(Entity(id="Child", kind="character", type="girl"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=lady.id, region=prize_cfg.region, plural=prize_cfg.plural))
    world.facts.update(lady=lady, child=child, prize=prize, action=action, setting=setting)

    world.say(f"{lady.id} was a {trait} lady who loved athletic games and quiet bedtime walks.")
    world.say(f"She carried {prize.phrase} because it made the evening feel soft and special.")
    world.para()
    world.say(f"One night, {lady.id} and the child wandered to {setting.place}.")
    world.say(f"{lady.id} wanted to {action.verb}, and the stones answered with a tiny whisper of surprise.")
    pred = predict(world, lady, action)
    if pred["fossilized"]:
        world.say(f"\"Careful,\" the child said, because {prize.label} might collect a dusty spell.")
    _do_action(world, lady, action, narrate=True)
    world.para()
    lady.memes["worry"] += 1
    world.say(f"Then {lady.id} stood very still, just long enough to look like a funny old fossil.")
    world.say(f"The child giggled, not because it was bad, but because the whole thing was so strange.")
    gear = select_gear(action, prize)
    if gear:
        gear_ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
        gear_ent.worn_by = lady.id
        world.say(f"After that, the child helped {lady.id} {gear.prep}.")
        lady.meters["dusty"] = 0.0
        lady.meters["stony"] = 0.0
        lady.memes["worry"] = 0.0
        lady.memes["calm"] += 1
        lady.memes["humor"] += 1
        world.say(f"At once, the dusty spell loosened, and {gear.tail}.")
        world.say(f"{lady.id} laughed softly, {action.gerund} again, while {prize.label} stayed clean.")
    world.facts["gear"] = gear
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lady = f["lady"]
    action = f["action"]
    prize = f["prize"]
    return [
        f'Write a bedtime story about {lady.id}, a lady who loves athletic play and a little "{action.keyword}" surprise.',
        f"Tell a gentle story where {lady.id} almost turns into a fossil while {action.verb}, but the child helps her laugh.",
        f"Write a child-friendly story that includes curiosity, humor, and surprise near {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lady = f["lady"]
    child = f["child"]
    prize = f["prize"]
    action = f["action"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who wanted to {action.verb} at {world.setting.place}?",
            answer=f"{lady.id}, the lady, wanted to {action.verb} there because she was athletic and full of evening energy.",
        ),
        QAItem(
            question=f"What made the moment feel surprising and a little funny?",
            answer=f"{lady.id} stood so still after the dusty spell that she looked like a tiny fossil statue, and that gave the child a big surprise and a giggle.",
        ),
        QAItem(
            question=f"Why did the child help {lady.id} after the dusty spell began?",
            answer=f"The child wanted {lady.id} to stay comfortable and happy, and the help made the curious, funny moment turn into bedtime calm.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did {gear.label} help the story end well?",
                answer=f"{gear.label} helped keep the dusty spell from sticking, so {lady.id} could keep moving and {prize.label} could stay nice and clean.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fossil?",
            answer="A fossil is a very old shape or mark left behind by a plant or animal, often preserved in stone.",
        ),
        QAItem(
            question="What does athletic mean?",
            answer="Athletic means strong and active, especially in games, running, jumping, or other body movements.",
        ),
        QAItem(
            question="Why can curiosity be useful?",
            answer="Curiosity helps someone notice details, ask questions, and learn what is happening around them.",
        ),
        QAItem(
            question="Why do bedtime stories often feel cozy?",
            answer="Bedtime stories often feel cozy because they use gentle language, safe endings, and soft pictures in the mind.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
compatible(A,P,G) :- prize_at_risk(A,P), gear(G), guards(G,dusty), covers(G,R), worn_on(P,R), splashes(A,R).
valid_story(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), compatible(A,P,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" python-only:", sorted(py - asp_set))
    print(" asp-only:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: lady, fossil-ize, athletic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=LADY_NAMES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(LADY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PRIZES[params.prize], params.name, params.trait)
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
    StoryParams(place="moon_garden", action="skip", prize="shoes", name="Mira", trait="athletic"),
    StoryParams(place="pond_path", action="skip", prize="cape", name="Nora", trait="curious"),
    StoryParams(place="quiet_hall", action="sketch", prize="scarf", name="Lena", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            sample = generate(params)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

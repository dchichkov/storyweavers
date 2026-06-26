#!/usr/bin/env python3
"""
A standalone storyworld for a heartwarming romp with twine, gentle foreshadowing,
kindness, and sound effects.

The domain is small and classical:
- a child wants to romp outside,
- a ball of twine or kite string becomes a problem,
- a kind helper notices a clue early,
- they use a careful fix, and
- the ending proves what changed.

This file follows the Storyweavers storyworld contract:
- StoryParams and registries are local to this script.
- Shared results containers are imported eagerly.
- ASP helpers are imported lazily in ASP helpers.
- The world model drives the prose and QA.
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tangle": 0.0, "fray": 0.0, "joy": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "kindness": 0.0, "foreshadow": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
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
    place: str
    outdoor: bool
    affords: set[str] = field(default_factory=set)
    mood: str = ""


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    starter: str
    finish: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "hands"
    plural: bool = False


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    verb: str
    tail: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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


def _r_tangle(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("tangle", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.owner != actor.id or item.type != "bundle":
                continue
            sig = ("tangle", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["fray"] = item.meters.get("fray", 0.0) + 1
            out.append(f"{item.label.capitalize()} gave a faint {item.phrase}.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("foreshadow", 0.0) < THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"{actor.pronoun().capitalize()} noticed the little clue and grew careful.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("kindness", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1
        out.append(f"Kindness made the whole moment feel softer.")
    return out


CAUSAL_RULES = [_r_tangle, _r_worry, _r_kindness]


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


def predict_fix(world: World, hero: Entity, activity: Activity, prize_id: str, fix: Optional[Fix]) -> dict:
    sim = copy_world(world)
    if fix is not None:
        sim.get(hero.id).memes["kindness"] += 1
    sim.get(hero.id).meters["tangle"] += 1
    sim.zone = set(activity.tags)
    simulate_activity(sim, hero.id, activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"tangled": prize.meters.get("fray", 0.0) >= THRESHOLD}


def copy_world(world: World) -> World:
    import copy
    clone = World(world.setting)
    clone.entities = copy.deepcopy(world.entities)
    clone.paragraphs = [[]]
    clone.facts = dict(world.facts)
    clone.fired = set(world.fired)
    clone.zone = set(world.zone)
    return clone


def simulate_activity(world: World, hero_id: str, activity: Activity, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    hero.meters["tangle"] = hero.meters.get("tangle", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.zone = set(activity.tags)
    if narrate:
        world.say(activity.sound)
        world.say(activity.starter)
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, fix_cfg: Fix,
         hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "bright"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    bundle = world.add(Entity(id="bundle", type="bundle", label="the twine bundle", phrase="looked a little loose", owner=hero.id))

    intro = f"{hero.id} was a little {hero.type} who loved a brisk romp in {setting.place}."
    world.say(intro)
    world.say(f"{hero.pronoun().capitalize()} liked the {activity.keyword} and the cheerful {activity.sound}.")
    world.say(f"{hero.id}'s {parent.label_word if hasattr(parent, 'label_word') else 'parent'} gave {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} held {prize.it()} close, and the twine bundle sat nearby with a tiny kink in one strand.")

    world.para()
    world.say(f"One day, {activity.sound}—{activity.starter}")
    world.say(f"{hero.id} wanted to {activity.verb}, and the path looked ready for a romp.")
    hero.memes["foreshadow"] += 1
    bundle.meters["fray"] += 0.5
    propagate(world)

    world.say(f"But {bundle.label} gave a soft sign of trouble before the fun could start.")
    world.say(f"{parent.id} noticed it first and smiled, because {fix_cfg.label} could help.")
    world.para()

    if fix_cfg is not None:
        hero.memes["kindness"] += 1
        world.say(f"{parent.id} used {fix_cfg.phrase} to {fix_cfg.verb}.")
        world.say(f"{hero.id} listened, and the kindness made the choice easy.")
        world.say(f"Together they {fix_cfg.tail}.")
    simulate_activity(world, hero.id, activity)
    if fix_cfg is not None:
        prize.meters["fray"] = 0.0
    world.say(f"At the end, {hero.id} was still {activity.gerund}, and {prize.label} stayed neat and safe.")
    world.say(f"{parent.id} laughed softly, and the little twine bundle did not spoil the day at all.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, fix=fix_cfg, bundle=bundle)
    return world


SETTINGS = {
    "garden": Setting(place="the garden", outdoor=True, affords={"romp"}, mood="bright"),
    "yard": Setting(place="the yard", outdoor=True, affords={"romp"}, mood="windy"),
    "meadow": Setting(place="the meadow", outdoor=True, affords={"romp"}, mood="soft"),
}

ACTIVITIES = {
    "romp": Activity(
        id="romp",
        verb="romp under the trees",
        gerund="romping under the trees",
        rush="run laughing down the path",
        sound="tap-tap, swish, and giggle-giggle",
        starter="The grass whispered, and the leaves went flutter-flutter.",
        finish="The whole path felt like a game.",
        risk="a loose twine snag could tug at the prize",
        keyword="romp",
        tags={"romp", "twine", "sound", "foreshadow"},
    )
}

PRIZES = {
    "kite": Prize(label="kite", phrase="a bright paper kite", type="kite", region="hands"),
    "scarf": Prize(label="scarf", phrase="a soft blue scarf", type="scarf", region="neck"),
    "basket": Prize(label="basket", phrase="a little picnic basket", type="basket", region="hands"),
}

FIXES = {
    "rewind": Fix(
        id="rewind",
        label="a tidy rewind",
        phrase="gentle hands and a little patience",
        verb="rewind the twine",
        tail="wrapped the twine into a neat, safe coil",
        guards={"twine"},
    ),
    "clip": Fix(
        id="clip",
        label="a small clip",
        phrase="a small bright clip",
        verb="pin the twine end safely",
        tail="fastened the loose end so it could not snag",
        guards={"twine"},
    ),
}

NAMES = ["Mina", "Theo", "Luna", "Noah", "Ivy", "Piper"]
TRAITS = ["brave", "curious", "cheerful", "gentle", "spirited"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    fix: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming romp storyworld with twine and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--fix", choices=FIXES)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act in ACTIVITIES:
            for prize in PRIZES:
                for fix in FIXES:
                    combos.append((place, act, prize, fix))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, act, prize, fix = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=act, prize=prize, fix=fix, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, activity, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a heartwarming story for a young child about "{activity.keyword}" and a loose twine clue.',
        f"Tell a gentle tale where {hero.id} wants to {activity.verb} but must protect {prize.phrase}.",
        f"Write a story with foreshadowing, kindness, and sound effects ending in a safe happy romp.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity, fix = f["hero"], f["parent"], f["prize"], f["activity"], f["fix"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"What clue hinted that trouble might happen before the romp?",
            answer=f"The twine bundle had a tiny kink, so it looked a little loose before the play began.",
        ),
        QAItem(
            question=f"How did {parent.id} help keep {prize.label} safe?",
            answer=f"They used {fix.phrase} to {fix.verb}, which kept the prize from being snagged.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} still {activity.gerund} while {prize.label} stayed neat and safe.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is twine used for?",
        answer="Twine is a thin string used for tying, wrapping, or holding things together.",
    ),
    QAItem(
        question="What does foreshadowing mean in a story?",
        answer="Foreshadowing is when a story gives a small clue that something important may happen later.",
    ),
    QAItem(
        question="What is kindness?",
        answer="Kindness is when someone helps, comforts, or speaks gently to another person.",
    ),
    QAItem(
        question="Why do sound effects make stories fun?",
        answer="Sound effects can help readers imagine the noises in a scene, like rustling leaves or cheerful footsteps.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if "twine" in tags:
        return WORLD_KNOWLEDGE
    return WORLD_KNOWLEDGE


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
activity(romp).
setting(garden).
setting(yard).
setting(meadow).
prize(kite).
prize(scarf).
prize(basket).
fix(rewind).
fix(clip).

valid_story(P,A,R,F) :- setting(P), activity(A), prize(R), fix(F).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], FIXES[params.fix], params.name, params.gender, params.parent)
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
    StoryParams(place="garden", activity="romp", prize="kite", fix="rewind", name="Mina", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="yard", activity="romp", prize="scarf", fix="clip", name="Theo", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="meadow", activity="romp", prize="basket", fix="rewind", name="Ivy", gender="girl", parent="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for combo in combos:
            print(" ", combo)
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

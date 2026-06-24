#!/usr/bin/env python3
"""
A small heartwarming story world about a child who wants to charge ahead,
then learns a gallant way to handle a conflict with kindness.

Seed tale:
---
A little child named Nia loved to charge into the playroom and be first at
everything. One afternoon, Nia found a shiny cardboard castle with a tiny paper
dragon. Nia wanted to grab the dragon right away, but her friend Ollie was
already holding it.

Nia felt a hot conflict in her chest. Ollie did not tease or shove back.
Instead, Ollie smiled, set the dragon on the table, and said, "You can have a
turn after me. We can both make the castle better if we work together."

Nia paused, took a breath, and tried a gallant choice. She held the door open
for a smaller child, waited her turn, and helped build the castle walls. Soon
the whole table was full of laughter, and the dragon stood on top of the castle
as a sign that sharing had made the game more fun.

World idea:
---
The domain simulates a small "turn-taking and helping" scene. A child may charge
toward a prized object or a line, creating conflict; a gallant helper may offer a
kind compromise that turns the moral value of patience into a happy ending.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the playroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    charge_meme: str
    conflict_meme: str
    moral_value: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gift:
    id: str
    label: str
    prep: str
    tail: str
    value: str = "gallant"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.turns: int = 0

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        c.turns = self.turns
        return c


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.chars():
        if actor.memes.get("charge", 0.0) < THRESHOLD:
            continue
        for other in world.chars():
            if other.id == actor.id:
                continue
            if other.held_by == actor.id:
                continue
            sig = ("conflict", actor.id, other.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
            out.append(
                f"{actor.id} felt a sharp conflict when {other.id} had the {world.facts['prize'].label}."
            )
    return out


CAUSAL_RULES = [
    _r_conflict,
]


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


def predict_conflict(world: World, actor: Entity) -> bool:
    sim = world.copy()
    sim.get(actor.id).memes["charge"] = 1.0
    propagate(sim, narrate=False)
    return any(e.memes.get("conflict", 0.0) >= THRESHOLD for e in sim.chars())


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved to charge into games and be first."
    )


def set_scene(world: World, prize: Entity) -> None:
    world.say(
        f"One afternoon, {world.setting.place} held a tiny tug of a game around {prize.phrase}."
    )


def desire(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["charge"] = hero.memes.get("charge", 0.0) + 1
    world.say(
        f"{hero.id} wanted to grab the {prize.label} right away, because being first felt exciting."
    )


def warn_or_notice(world: World, hero: Entity, prize: Entity, helper: Entity) -> None:
    if predict_conflict(world, hero):
        world.facts["conflict_foreseen"] = True
        world.say(
            f"But {hero.id} noticed a conflict in the room, and {helper.id} noticed it too."
        )


def gallant_turn(world: World, helper: Entity, hero: Entity, prize: Entity, gift: Gift) -> Optional[Gift]:
    if helper.memes.get("gallant", 0.0) < THRESHOLD:
        return None
    world.say(
        f"Then {helper.id} made a gallant choice: {gift.prep}."
    )
    return gift


def accept(world: World, hero: Entity, helper: Entity, prize: Entity, gift: Gift) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["conflict"] = 0.0
    hero.memes["moral_value"] = hero.memes.get("moral_value", 0.0) + 1
    world.say(
        f"{hero.id} slowed down, took a breath, and decided to be gallant too."
    )
    world.say(
        f"{hero.id} waited for a turn, helped with the game, and {gift.tail}. "
        f"In the end, the {prize.label} stayed at the center of a happy shared story."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Nia",
         hero_type: str = "girl", helper_name: str = "Ollie", helper_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    gift = Gift(id="open-door", label="open door", prep="held the door open for a smaller child", tail="the smaller child smiled and went first")

    helper.memes["gallant"] = 1.0
    world.facts.update(hero=hero, helper=helper, prize=prize, activity=activity, gift=gift)

    introduce(world, hero)
    world.para()
    set_scene(world, prize)
    desire(world, hero, prize)
    warn_or_notice(world, hero, prize, helper)
    propagate(world, narrate=True)
    world.para()
    if gallant_turn(world, helper, hero, prize, gift):
        accept(world, hero, helper, prize, gift)
    else:
        world.say(f"At last, {hero.id} chose a kind turn instead of a rush.")
    return world


SETTINGS = {
    "playroom": Setting(place="the playroom", affords={"castle"}),
    "hall": Setting(place="the school hall", affords={"line"}),
    "yard": Setting(place="the sunny yard", affords={"game"}),
}

ACTIVITIES = {
    "castle": Activity(
        id="castle",
        verb="build a castle",
        gerund="building a castle",
        rush="charge to the castle table",
        charge_meme="charge",
        conflict_meme="conflict",
        moral_value="patience",
        keyword="castle",
        tags={"castle", "sharing"},
    ),
    "line": Activity(
        id="line",
        verb="go first in line",
        gerund="standing in line",
        rush="charge to the front of the line",
        charge_meme="charge",
        conflict_meme="conflict",
        moral_value="turn-taking",
        keyword="line",
        tags={"line", "sharing"},
    ),
    "game": Activity(
        id="game",
        verb="join the game",
        gerund="joining the game",
        rush="charge into the game",
        charge_meme="charge",
        conflict_meme="conflict",
        moral_value="kindness",
        keyword="game",
        tags={"game", "sharing"},
    ),
}

PRIZES = {
    "dragon": Prize(label="dragon", phrase="a tiny paper dragon", type="dragon"),
    "baton": Prize(label="baton", phrase="a bright wooden baton", type="baton"),
    "ball": Prize(label="ball", phrase="a red play ball", type="ball"),
}

GALLANT_GIFTS = {
    "door": Gift(id="door", label="open door", prep="held the door open for a smaller child", tail="the smaller child went first"),
    "share": Gift(id="share", label="shared turn", prep="offered to share the next turn", tail="they both got a turn"),
}

GIRL_NAMES = ["Nia", "Mina", "Luna", "Ivy", "Rose", "Ari", "Maya"]
BOY_NAMES = ["Ollie", "Theo", "Finn", "Noah", "Ben", "Eli", "Max"]
TRAITS = ["curious", "gentle", "spirited", "brave", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                out.append((place, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world about charge, gallant, and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender,
                       helper=helper, helper_gender=helper_gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, prize, activity = f["hero"], f["helper"], f["prize"], f["activity"]
    return [
        f'Write a heartwarming story with the word "charge" where {hero.id} wants to {activity.verb} but learns a kinder way.',
        f'Write a simple story where {helper.id} acts gallant and helps {hero.id} through a conflict about {prize.label}.',
        f'Write a child-friendly story about patience, sharing, and the moral value of being gallant in {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, activity = f["hero"], f["helper"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label} at first?",
            answer=f"{hero.id} wanted to {activity.verb} right away and charge ahead."
        ),
        QAItem(
            question=f"Who was gallant in the story?",
            answer=f"{helper.id} was gallant because {helper.id} made a kind choice instead of making the conflict bigger."
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{hero.id} slowed down, chose patience, and the conflict turned into a happy shared turn."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be gallant?",
            answer="Being gallant means acting brave and kind, especially by helping others or choosing a generous way to solve a problem."
        ),
        QAItem(
            question="What is conflict?",
            answer="A conflict is a disagreement or a tense feeling when people want different things."
        ),
        QAItem(
            question="Why is patience a good moral value?",
            answer="Patience is a good moral value because waiting calmly helps people share, listen, and treat others fairly."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A conflict exists when the hero's charge collides with another character's hold.
conflict(H, O) :- charge(H), holds(O, P), hero(H), other(O), H != O, prize(P).

% Gallant behavior resolves the conflict when the helper offers a shared turn.
resolved(H) :- conflict(H, _), gallant(_, H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("moral", aid, a.moral_value))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for gid in GALLANT_GIFTS:
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show setting/1."))
    if model is None:
        print("ASP returned no model.")
        return 1
    print("OK: ASP twin loaded and solved.")
    return 0


CURATED = [
    StoryParams(place="playroom", activity="castle", prize="dragon", name="Nia", gender="girl", helper="Ollie", helper_gender="boy", trait="curious"),
    StoryParams(place="hall", activity="line", prize="baton", name="Mia", gender="girl", helper="Theo", helper_gender="boy", trait="thoughtful"),
    StoryParams(place="yard", activity="game", prize="ball", name="Finn", gender="boy", helper="Rose", helper_gender="girl", trait="brave"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 hero_name=params.name, hero_type=params.gender,
                 helper_name=params.helper, helper_type=params.helper_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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

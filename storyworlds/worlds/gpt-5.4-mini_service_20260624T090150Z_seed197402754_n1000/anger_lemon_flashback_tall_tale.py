#!/usr/bin/env python3
"""
Tall-tale storyworld: a giant lemon, a hot temper, and a flashback that explains
how a sour moment gets turned into a sweet one.

The world is intentionally small and classical:
- one child character
- one older helper
- one prized lemon thing
- one emotional pressure (anger)
- one flashback that reveals the cause
- one practical resolution that changes the ending image

The prose is state-driven. The flashback is not a gimmick; it is a causal beat
that changes what the listener understands about the anger.
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
# Core entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the orchard"
    season: str = "summer"


@dataclass
class Prize:
    label: str
    phrase: str
    type: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_type: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orchard": Setting(place="the orchard", season="summer"),
    "kitchen": Setting(place="the kitchen", season="summer"),
    "porch": Setting(place="the porch", season="summer"),
}

PRIZES = {
    "lemon": Prize(
        label="lemon",
        phrase="a bright lemon with a shine like a brass bell",
        type="lemon",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ruby", "Ivy"]
BOY_NAMES = ["Theo", "Ben", "Owen", "Finn", "Jack"]


# ---------------------------------------------------------------------------
# World behavior
# ---------------------------------------------------------------------------
ANGER_THRESHOLD = 1.0
SOUR_THRESHOLD = 1.0
MEMORY_THRESHOLD = 1.0


def tall_tale_opening(hero: Entity, helper: Entity, prize: Entity, setting: Setting) -> str:
    return (
        f"Out in {setting.place}, where the sun could wink at a cricket and the wind "
        f"could rattle a fence, {hero.id} kept {prize.phrase} on the table like it was a treasure from the moon."
    )


def flashback_line(hero: Entity, prize: Entity) -> str:
    return (
        f"Flashback: yesterday, {hero.id} had promised to save {prize.label} for a pie, "
        f"but a squirrel slipped by and tasted the first slice."
    )


def predict_anger(world: World, hero: Entity, prize: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["anger"] = 1.0
    sim.get(prize.id).meters["sour"] = 1.0
    return True


def apply_fury(world: World, hero: Entity, prize: Entity) -> None:
    if hero.memes.get("anger", 0.0) >= ANGER_THRESHOLD and prize.meters.get("sour", 0.0) >= SOUR_THRESHOLD:
        sig = ("storm", hero.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        hero.meters["stomp"] = hero.meters.get("stomp", 0.0) + 1.0
        hero.memes["bluster"] = hero.memes.get("bluster", 0.0) + 1.0


def gentle_fix(world: World, hero: Entity, helper: Entity, prize: Entity) -> bool:
    if prize.meters.get("sour", 0.0) < SOUR_THRESHOLD:
        return False
    sig = ("fix", prize.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    prize.meters["sour"] = 0.0
    prize.meters["sweet"] = 1.0
    hero.memes["anger"] = 0.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    helper.memes["approval"] = helper.memes.get("approval", 0.0) + 1.0
    world.say(
        f"{helper.id} smiled and showed {hero.id} how to turn the lemon into golden lemonade with honey and mint."
    )
    return True


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"stomp": 0.0},
        memes={"curiosity": 1.0, "anger": 0.0, "pride": 0.0},
    ))
    helper = world.add(Entity(
        id="Grandma",
        kind="character",
        type=params.helper_type,
        meters={},
        memes={"calm": 1.0, "approval": 0.0},
    ))
    prize = world.add(Entity(
        id="Lemon",
        type="lemon",
        label="lemon",
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=helper.id,
        meters={"sour": 1.0, "sweet": 0.0},
        memes={"value": 1.0},
    ))

    world.say(tall_tale_opening(hero, helper, prize, setting))
    world.say(
        f"{hero.id} loved that lemon so much that {hero.pronoun('possessive')} eyes shone like two chipper lanterns."
    )
    world.para()

    world.say(
        f"Then {hero.id} took one sniff, made a face, and got as hot as a skillet in July."
    )
    hero.memes["anger"] = 1.0
    apply_fury(world, hero, prize)
    world.say(
        f"{hero.id} stamped once, and the whole porch seemed to hear it."
    )
    world.say(flashback_line(hero, prize))
    world.say(
        f"That little memory explained the sour feeling: the lemon had been saved, then nearly lost, and now the anger came rushing back."
    )
    world.para()

    if gentle_fix(world, hero, helper, prize):
        world.say(
            f"{hero.id} squeezed the lemon with care, stirred the pitcher, and watched the sourness vanish like fog at sunrise."
        )
        world.say(
            f"By supper time, the lemonade was bright and sweet, and {hero.id} laughed so hard that even the chairs seemed to grin."
        )

    world.facts.update(hero=hero, helper=helper, prize=prize, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a tall tale for a young child about {hero.id}, a lemon, and a flashback that explains a burst of anger.',
        f"Tell a vivid story where {hero.id} remembers why a lemon made {hero.pronoun('object')} mad, then turns it into something good.",
        "Write a short, child-friendly tall tale with a flashback, a sour lemon, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize: Entity = f["prize"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What was {hero.id} holding in {setting.place}?",
            answer=f"{hero.id} was holding a bright lemon that looked almost like a tiny sun.",
        ),
        QAItem(
            question=f"Why did {hero.id} get angry?",
            answer=(
                f"{hero.id} got angry because the lemon felt sour, and the flashback showed that {prize.label} had almost been lost before."
            ),
        ),
        QAItem(
            question=f"Who helped {hero.id} calm down?",
            answer=f"{helper.id} helped {hero.id} calm down and turn the lemon into lemonade.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The sour lemon became sweet lemonade, and the anger settled down into pride and laughter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lemon?",
            answer="A lemon is a yellow fruit with a sharp sour taste.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that goes back to something that happened earlier.",
        ),
        QAItem(
            question="Why can sour food make a face scrunch up?",
            answer="Sour food can make a face scrunch up because the taste is strong and sharp on the tongue.",
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
prize(P) :- prize_name(P).

flashback_needed(H) :- anger(H), sour(lemon), promise_broken(lemon).
calm_end(H) :- anger(H), sour(lemon), then_made_lemonade(lemon).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = [
        asp.fact("hero_name", "hero"),
        asp.fact("prize_name", "lemon"),
        asp.fact("anger", "hero"),
        asp.fact("sour", "lemon"),
        asp.fact("promise_broken", "lemon"),
        asp.fact("then_made_lemonade", "lemon"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program("#show flashback_needed/1.\n#show calm_end/1."))
    atoms = set((a.name, tuple(str(x) for x in a.arguments)) for a in model)
    expected = {("flashback_needed", ("hero",)), ("calm_end", ("hero",))}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH: ASP parity check failed.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld with anger, lemon, and a flashback.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"], default=None)
    ap.add_argument("--prize", choices=PRIZES.keys())
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    prize = args.prize or "lemon"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["grandmother", "grandfather"])
    hero_type = "girl" if gender == "girl" else "boy"
    return StoryParams(place=place, hero_name=name, hero_type=hero_type, helper_type=helper, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show flashback_needed/1.\n#show calm_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show flashback_needed/1.\n#show calm_end/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = [
            StoryParams(place="orchard", hero_name="Mina", hero_type="girl", helper_type="grandmother", prize="lemon"),
            StoryParams(place="porch", hero_name="Theo", hero_type="boy", helper_type="grandfather", prize="lemon"),
            StoryParams(place="kitchen", hero_name="Ruby", hero_type="girl", helper_type="grandmother", prize="lemon"),
        ]
        samples = [generate(p) for p in params]
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

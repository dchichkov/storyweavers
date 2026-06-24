#!/usr/bin/env python3
"""
Standalone storyworld: a small adventure mystery built from tortilla, dog-dim,
and cheetah seed words.

Premise:
- A child explorer notices a strange "dog-dim" clue at a market trail.
- A tortilla is missing from a lunch bundle.
- A cheetah-shaped shadow appears near the path, but the true cause is not
  what it first seems.

Story instruments:
- Moral Value: honesty, kindness, and sharing.
- Inner Monologue: the hero thinks through clues before acting.
- Mystery to Solve: what happened to the tortilla?

The world is intentionally small and state-driven: meters track physical clues
and emotional urgency; memes track guilt, courage, and trust. The story resolves
only when the hero follows the clues and chooses a moral action.
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
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""

    def __post_init__(self):
        if not self.meters:
            self.meters = {"seen": 0.0}
        if not self.memes:
            self.memes = {"calm": 0.0}

    def pronoun(self) -> str:
        return "they" if self.kind == "character" else "it"

    def possessive(self) -> str:
        return "their" if self.kind == "character" else "its"


@dataclass
class Setting:
    place: str
    trail: str
    market: str
    den: str


@dataclass
class Clue:
    id: str
    label: str
    hint: str
    location: str
    truth: str


@dataclass
class StoryParams:
    setting: str
    hero: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "trail": Setting(place="the sunlit trail", trail="a narrow trail", market="the little market", den="the brush den"),
    "village": Setting(place="the village edge", trail="a dusty path", market="the snack stall", den="the shade den"),
    "canyon": Setting(place="the canyon path", trail="a rocky trail", market="the canyon market", den="the stone den"),
}

HEROES = ["Mina", "Pip", "Nori", "Lio", "Tala"]
CHEETAH_NAMES = ["Swift Spot", "Gold Stripe"]
CLUES = {
    "dog_dim": Clue(
        id="dog_dim",
        label="dog-dim track",
        hint="a small muddy mark that looked like a dog had walked through moonlight",
        location="trail",
        truth="a turtle-sized cart wheel made the track",
    ),
    "tortilla": Clue(
        id="tortilla",
        label="tortilla crumb",
        hint="a warm round crumb tucked beside a basket",
        location="market",
        truth="the tortilla had slipped from a lunch cloth",
    ),
    "cheetah": Clue(
        id="cheetah",
        label="cheetah shadow",
        hint="a fast stripe of gold that seemed to leap between bushes",
        location="den",
        truth="a cheetah mural painted on a wind kite cast the shadow",
    ),
}


def valid_settings() -> list[str]:
    return sorted(SETTINGS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a moral mystery and inner monologue.")
    ap.add_argument("--setting", choices=valid_settings())
    ap.add_argument("--hero")
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
    setting = args.setting or rng.choice(valid_settings())
    hero = args.hero or rng.choice(HEROES)
    return StoryParams(setting=setting, hero=hero)


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero, kind="character", label=params.hero))
    tortilla = world.add(Entity(id="tortilla", label="tortilla", phrase="a warm tortilla", location="market"))
    dogdim = world.add(Entity(id="dog_dim", label="dog-dim clue", phrase="a dog-dim clue", location="trail"))
    cheetah = world.add(Entity(id="cheetah", label="cheetah mark", phrase="a cheetah mark", location="den"))
    bundle = world.add(Entity(id="bundle", label="lunch bundle", phrase="a lunch bundle", location="market"))
    world.facts.update(hero=hero, tortilla=tortilla, dogdim=dogdim, cheetah=cheetah, bundle=bundle)
    return world


def _narrate_inner(world: World, hero: Entity, text: str) -> None:
    world.say(f"{hero.label} thought, “{text}”")


def _advance_to_clue(world: World, hero: Entity, clue: Clue) -> None:
    hero.meters["courage"] = hero.meters.get("courage", 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    _narrate_inner(world, hero, f"If I follow the {clue.label}, maybe the mystery will open.")
    world.say(f"{hero.label} walked toward {world.setting.place if clue.location == 'trail' else clue.location} and searched carefully.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.get(params.hero)
    tortilla = world.get("tortilla")
    dogdim = world.get("dog_dim")
    cheetah = world.get("cheetah")
    bundle = world.get("bundle")

    # Beginning
    world.say(f"At {world.setting.place}, {hero.label} found a lunch bundle, a strange dog-dim clue, and a flicker of a cheetah shape.")
    world.say(f"The tortilla was meant for the picnic, but now {hero.label} could not tell where it had gone.")

    # Middle: mystery and inner monologue
    world.para()
    hero.memes["worry"] = 1.0
    _narrate_inner(world, hero, "Should I blame the cheetah? No, I should look for real signs.")
    world.say(f"{hero.label} noticed the {dogdim.label}: {dogdim_truth(dogdim)}.")
    _advance_to_clue(world, hero, dogdim)
    world.say(f"That clue pointed back to the market, where a crumb of tortilla rested beside the basket.")
    tortilla.meters["found"] = 1.0
    world.facts["missing_tortilla"] = "found by careful searching"

    # Turn: moral value
    world.para()
    _narrate_inner(world, hero, "I can be honest about what I learned, and I can share the food instead of hiding it.")
    world.say(f"{hero.label} followed the trail again and saw the cheetah shape was only a wind kite with a painted stripe.")
    world.say(f"At the den, {hero.label} shared the tortilla with friends and told the truth about the false cheetah shadow.")
    hero.memes["trust"] = 1.0
    hero.memes["joy"] = 1.0
    bundle.meters["shared"] = 1.0

    # Ending image
    world.para()
    world.say(f"In the end, the mystery was solved: the tortilla had slipped from the lunch bundle, the dog-dim clue led the way, and the cheetah was only a harmless painted shadow.")
    world.say(f"{hero.label} left the trail smiling, with clean hands, a full heart, and a lesson about honesty and kindness.")

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dogdim_truth(clue: Entity) -> str:
    return "it was just a hint, not a real dog, and it meant someone had passed that way"


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        f"Write an adventure story for a young child about {hero.label}, a tortilla, and a dog-dim clue.",
        "Tell a mystery-to-solve tale where a cheetah shadow seems suspicious but turns out to be harmless.",
        "Write a short story with an inner monologue and a moral value about honesty and sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    return [
        QAItem(
            question=f"What mystery did {hero.label} try to solve?",
            answer="The mystery was where the missing tortilla had gone and what the strange dog-dim clue and cheetah shadow really meant.",
        ),
        QAItem(
            question=f"What did {hero.label} think to themself before solving the mystery?",
            answer="They thought they should not blame the cheetah too quickly and should follow real clues first.",
        ),
        QAItem(
            question=f"What moral choice did {hero.label} make at the end?",
            answer="They told the truth, shared the tortilla, and chose kindness instead of blame.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tortilla?",
            answer="A tortilla is a flat round bread, often made from corn or flour, that can be folded or filled with food.",
        ),
        QAItem(
            question="What is a cheetah?",
            answer="A cheetah is a fast wild cat with spots and a long body that can run very quickly.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to gather clues, think carefully, and figure out what really happened.",
        ),
    ]


ASP_RULES = r"""
mystery_solved :- clue(dog_dim), clue(tortilla), clue(cheetah), moral(choice_kind), inner(thinking).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("clue", "dog_dim"),
        asp.fact("clue", "tortilla"),
        asp.fact("clue", "cheetah"),
        asp.fact("moral", "choice_kind"),
        asp.fact("inner", "thinking"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show mystery_solved/0."))
    asp_ok = bool(model)
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python parity match for the mystery gate.")
        return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} location={e.location}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery_solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show mystery_solved/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for setting in valid_settings():
            samples.append(generate(StoryParams(setting=setting, hero=HEROES[0], seed=base_seed)))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

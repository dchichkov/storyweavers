#!/usr/bin/env python3
"""
storyworlds/worlds/shark_inner_monologue_cautionary_foreshadowing_nursery_rhyme.py
==================================================================================

A standalone storyworld for a tiny nursery-rhyme-like sea tale with a shark,
inner monologue, cautionary beats, and foreshadowing.

Seed tale sketch:
---
A little fish wanted to glide near a shark while the moon made the water glow.
The fish heard its own thoughts, noticed a shadow and a hush in the tide, and
remembered a gentle warning from an older crab. The fish chose a safer cove,
the shark passed by hungry but not angry, and the sea became calm again.

World model:
- A small reef world with a fish, a shark, and a helper.
- Physical meters track distance, hunger, and safety.
- Emotional memes track worry, courage, and relief.
- Foreshadowing is modeled as a shadow in the water and a quiet drift in the
  current before the shark arrives.
- Inner monologue is modeled as thoughts that can push the fish toward caution
  or curiosity.
- A cautionary turn happens when the helper warns the fish away from danger.
- The resolution proves what changed: the fish ends in a safe cove, with relief
  and a calmer sea.

This script follows the storyworld contract:
- stdlib only for the base story engine
- imports shared results eagerly
- imports asp lazily inside ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP_RULES twin
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
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

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    name: str
    water: str
    shelter: str
    safe_spot: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Shark:
    id: str
    label: str
    phrase: str
    size: str
    hunger: str
    drift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fish:
    id: str
    label: str
    phrase: str
    finny: str
    brave: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    warning: str
    safe_choice: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    fish: str
    shark: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "reef": Setting(
        name="the reef",
        water="blue water",
        shelter="a coral arch",
        safe_spot="a small cove",
        mood="gentle",
        affords={"swim"},
    ),
    "harbor": Setting(
        name="the harbor",
        water="silver water",
        shelter="a dock shadow",
        safe_spot="a quiet nook",
        mood="busy",
        affords={"swim"},
    ),
    "moonbay": Setting(
        name="Moon Bay",
        water="moonlit water",
        shelter="a shell cave",
        safe_spot="a hush of sea grass",
        mood="soft",
        affords={"swim"},
    ),
}

FISHES = {
    "poppy": Fish("poppy", "Poppy", "a little fish", "finny", "brave", {"fish", "small"}),
    "milo": Fish("milo", "Milo", "a tiny fish", "finny", "curious", {"fish", "small"}),
    "luna": Fish("luna", "Luna", "a bright fish", "finny", "gentle", {"fish", "small"}),
}

SHARKS = {
    "gray": Shark("gray", "Grayfin", "a shark", "big", "hungry", "slow drift", {"shark", "sea"}),
    "stripe": Shark("stripe", "Stripejaw", "a shark", "big", "hungry", "long drift", {"shark", "sea"}),
    "white": Shark("white", "Whitefin", "a shark", "big", "hungry", "wide drift", {"shark", "sea"}),
}

HELPERS = {
    "crab": Helper("crab", "Crabby", "an older crab", "The water feels wrong near that shadow.", "swim to the cove", {"crab", "warning"}),
    "turtle": Helper("turtle", "Tilda", "a wise turtle", "Look for the dark tail in the tide.", "hide by the shell cave", {"turtle", "warning"}),
    "starfish": Helper("starfish", "Sally", "a steady starfish", "A hush can mean a shark is near.", "drift to the coral arch", {"starfish", "warning"}),
}

GIRL_NAMES = ["Poppy", "Luna", "Mia", "Ava"]
BOY_NAMES = ["Milo", "Finn", "Noah", "Theo"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, f, sh, h) for s in SETTINGS for f in FISHES for sh in SHARKS for h in HELPERS]


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.fish not in FISHES or params.shark not in SHARKS or params.helper not in HELPERS:
        raise StoryError("Unknown entity choice.")


def outcome_is_safe(params: StoryParams) -> bool:
    return True


def tell(setting: Setting, fish_cfg: Fish, shark_cfg: Shark, helper_cfg: Helper) -> World:
    world = World(setting)
    fish = world.add(Entity(id=fish_cfg.id, kind="character", type="fish", label=fish_cfg.label, phrase=fish_cfg.phrase))
    shark = world.add(Entity(id=shark_cfg.id, kind="character", type="shark", label=shark_cfg.label, phrase=shark_cfg.phrase))
    helper = world.add(Entity(id=helper_cfg.id, kind="character", type="helper", label=helper_cfg.label, phrase=helper_cfg.phrase))

    for ent in (fish, shark, helper):
        ent.meters["distance"] = 0.0
        ent.meters["hunger"] = 0.0
        ent.meters["safety"] = 0.0
        ent.memes["worry"] = 0.0
        ent.memes["courage"] = 0.0
        ent.memes["relief"] = 0.0
        ent.memes["warning"] = 0.0
        ent.memes["curiosity"] = 0.0
        ent.memes["calm"] = 0.0

    world.facts["setting"] = setting
    world.facts["fish"] = fish
    world.facts["shark"] = shark
    world.facts["helper"] = helper

    fish.meters["distance"] = 3.0
    shark.meters["distance"] = 4.0
    shark.meters["hunger"] = 2.0
    fish.memes["curiosity"] = 1.0
    fish.memes["worry"] = 0.0
    helper.memes["warning"] = 1.0

    world.say(f"In {setting.name}, the {setting.mood} sea glowed like a rhyme.")
    world.say(f"{fish.label} was {fish_cfg.phrase}, and {fish.pronoun().capitalize()} liked to drift and play.")
    world.say(f"Far off, {shark.label} was {shark_cfg.phrase}, moving with {shark_cfg.drift} through the {setting.water}.")
    world.say(f"Near the water's edge stood {helper.label}, {helper_cfg.phrase}, as steady as a pebble in the tide.")

    world.para()
    world.say(f"{setting.water} shimmered, and a thin shadow stretched under the waves.")
    world.say(f"{fish.label}'s own thoughts whispered, 'I am small, and the sea is wide.'")
    world.say(f"Then another thought bobbed up: 'That shadow has teeth-shaped edges.'")

    fish.memes["worry"] += 1.0
    fish.memes["courage"] += 1.0
    world.para()
    world.say(f"{helper.label} called softly, '{helper_cfg.warning}'")
    world.say(f"{fish.label} listened and felt a little shake in {fish.pronoun('possessive')} fins.")
    world.say(f"'{helper_cfg.safe_choice.capitalize()},' {fish.label} thought, and that thought felt wise and light.")

    world.para()
    fish.meters["distance"] = 1.0
    helper.memes["relief"] += 1.0
    fish.memes["relief"] += 1.0
    fish.meters["safety"] = 1.0
    shark.meters["distance"] = 5.0
    world.say(f"{fish.label} drifted to {setting.safe_spot}, tucked beside {setting.shelter}, and kept out of the shadow.")
    world.say(f"{shark.label} passed by on {shark_cfg.drift}, hungry but not meeting a dinner it could reach.")
    world.say(f"The sea grew calm again, and {fish.label} sang a tiny line of thanks to the tide.")

    world.facts.update(
        fish=fish,
        shark=shark,
        helper=helper,
        safe_spot=setting.safe_spot,
        shadow="shadow",
        warning=helper_cfg.warning,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    fish = f["fish"]
    helper = f["helper"]
    setting = f["setting"]
    return [
        f'Write a short nursery-rhyme-like story about {fish.label} in {setting.name}, with a shark in the water, and a kind warning from {helper.label}.',
        f"Tell a gentle sea story where a small fish listens to its own thoughts, notices a shadow, and chooses a safe place instead of swimming toward the shark.",
        f'Write a cautionary tale for a young child that rhymes a little, includes a shark, and ends with the fish safe by the cove.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fish = f["fish"]
    helper = f["helper"]
    setting = f["setting"]
    shark = f["shark"]
    return [
        QAItem(
            question=f"Who is the story about in {setting.name}?",
            answer=f"It is about {fish.label}, a little fish who wanted to play near the water while {shark.label} drifted by.",
        ),
        QAItem(
            question=f"What did {fish.label} think when the shadow appeared?",
            answer=f"{fish.label} thought the shadow had teeth-shaped edges, so the little fish became careful instead of curious alone.",
        ),
        QAItem(
            question=f"What did {helper.label} warn {fish.label} about?",
            answer=f"{helper.label} warned that the water felt wrong near the shadow and told {fish.label} to choose the safe spot.",
        ),
        QAItem(
            question=f"Where did {fish.label} end up?",
            answer=f"{fish.label} ended up in {f['safe_spot']}, tucked by {setting.shelter}, safely away from {shark.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a shark?", answer="A shark is a big sea animal with sharp teeth that swims in the ocean."),
        QAItem(question="Why is a shadow in the water a warning?", answer="A shadow can mean something big is nearby, so it is wise to be careful."),
        QAItem(question="What should you do when a helper gives a safety warning?", answer="You should listen, move away from danger, and choose the safe place."),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    setting: str
    fish: str
    shark: str
    helper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="reef", fish="poppy", shark="gray", helper="crab"),
    StoryParams(setting="moonbay", fish="luna", shark="stripe", helper="turtle"),
    StoryParams(setting="harbor", fish="milo", shark="white", helper="starfish"),
]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
fish(F) :- fish_fact(F).
shark(SH) :- shark_fact(SH).
helper(H) :- helper_fact(H).
valid(S,F,SH,H) :- setting(S), fish(F), shark(SH), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for f in FISHES:
        lines.append(asp.fact("fish_fact", f))
    for sh in SHARKS:
        lines.append(asp.fact("shark_fact", sh))
    for h in HELPERS:
        lines.append(asp.fact("helper_fact", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos().")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme sea story with a shark, a warning, and a safe ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--fish", choices=FISHES)
    ap.add_argument("--shark", choices=SHARKS)
    ap.add_argument("--helper", choices=HELPERS)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.fish is None or c[1] == args.fish)
              and (args.shark is None or c[2] == args.shark)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, fish, shark, helper = rng.choice(sorted(combos))
    return StoryParams(setting=setting, fish=fish, shark=shark, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.fish not in FISHES or params.shark not in SHARKS or params.helper not in HELPERS:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], FISHES[params.fish], SHARKS[params.shark], HELPERS[params.helper])
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

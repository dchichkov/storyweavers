#!/usr/bin/env python3
"""
storyworlds/worlds/agate_chameleon_transformation_pirate_tale.py
=================================================================

A standalone story world for a small Pirate Tale domain:
a shipmate, an agate charm, a chameleon, and a transformation that helps the crew
escape a pinch and reach the treasure.

Story seed premise:
---
On a little pirate ship, a child pirate named Mara kept a polished agate in her
pocket because it glowed like sea glass. A tiny chameleon named Skit lived on the
rail and could change color to match sails, ropes, and palm leaves.

One windy evening, the crew needed to sneak past a lookout and reach a hidden
cove. Mara wanted to rush ahead, but the lookout's lantern would catch them.
Then Skit touched the agate, the stone warmed bright, and a transformation
began: Skit's colors shifted into a bold, shimmering pattern that blended with
the moonlit waves. The lookout looked the wrong way, and the crew slipped by.

Causal model:
---
    agate + chameleon + moonlight -> transformation spark
    transformation -> chameleon color shifts to match the best cover
    correct cover -> lookout fails to spot the crew
    safe passage -> crew reaches the cove and the treasure

Style note:
---
Keep the prose child-facing, concrete, and swashbuckling, like a short pirate tale.
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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "brightness": 0.0,
                "hidden": 0.0,
                "safe": 0.0,
                "change": 0.0,
            }
        if not self.memes:
            self.memes = {
                "wonder": 0.0,
                "worry": 0.0,
                "pride": 0.0,
                "fear": 0.0,
                "joy": 0.0,
                "conflict": 0.0,
                "transformed": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit cove"
    sea: str = "calm"
    affords: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    spark: str
    glow: str


@dataclass
class Creature:
    id: str
    label: str
    base_color: str
    transformed_color: str
    cover: str
    trigger: str


@dataclass
class StoryParams:
    place: str
    charm: str
    creature: str
    name: str
    gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    charm = world.facts.get("charm_entity")
    creature = world.facts.get("creature_entity")
    if not charm or not creature:
        return out
    c = world.get(charm.id)
    m = world.get(creature.id)
    if c.meters["brightness"] < THRESHOLD or m.memes["wonder"] < THRESHOLD:
        return out
    sig = ("transform", c.id, m.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    m.memes["transformed"] += 1
    m.meters["change"] += 1
    out.append("__transformation__")
    return out


def _r_hide(world: World) -> list[str]:
    out: list[str] = []
    creature = world.facts.get("creature_entity")
    if not creature:
        return out
    m = world.get(creature.id)
    if m.meters["change"] < THRESHOLD:
        return out
    sig = ("hide", m.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    m.meters["hidden"] += 1
    m.meters["safe"] += 1
    out.append("__hidden__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_transformation, _r_hide):
            items = rule(world)
            if items:
                changed = True
                produced.extend(x for x in items if x.startswith("__") is False)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def choose_cover(chameleon: Creature, setting: Setting) -> str:
    return chameleon.cover if setting.place else "the moonlit waves"


def setup_story(world: World, hero: Entity, captain: Entity, charm: Entity, creature: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} pirate with bright eyes and a brave grin."
    )
    world.say(
        f"{hero.pronoun().capitalize()} kept {hero.pronoun('possessive')} {charm.label} close because it shone like sea glass."
    )
    world.say(
        f"On the rail, a tiny {creature.type} named {creature.label} could change color faster than a flip of a sail."
    )
    world.para()
    world.say(
        f"One windy evening at {world.setting.place}, {hero.id} and {hero.pronoun('possessive')} {captain.label} needed to slip past a lookout."
    )
    world.say(
        f"But the lantern light was sharp, and the crew would be seen if they crossed the deck too soon."
    )


def tension(world: World, hero: Entity, captain: Entity, charm: Entity, creature: Entity) -> None:
    hero.memes["worry"] += 1
    creature.memes["wonder"] += 1
    world.say(
        f"{hero.id} held {hero.pronoun('possessive')} breath and rubbed the warm {charm.label} with a thumb."
    )
    world.say(
        f"Then {creature.label} climbed closer and touched the agate with a tiny toe."
    )
    charm.meters["brightness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The stone answered with a bright spark, and a strange feeling tugged at the air."
    )


def turn(world: World, creature: Entity) -> None:
    if creature.memes["transformed"] >= THRESHOLD:
        world.say(
            f"{creature.label} changed in a blink."
        )
        world.say(
            f"First came stripes, then speckles, then a shimmer the color of the moon on water."
        )
        world.say(
            f"The little chameleon became a moving patch of wave and shadow, perfect for hiding in plain sight."
        )


def resolution(world: World, hero: Entity, captain: Entity, creature: Entity) -> None:
    if creature.meters["hidden"] >= THRESHOLD:
        hero.memes["joy"] += 1
        captain.memes["pride"] += 1
        hero.memes["fear"] = 0.0
        world.para()
        world.say(
            f"The lookout peered into the dark and saw only a flicker of ripples, not the crew."
        )
        world.say(
            f"So {hero.id} and {hero.pronoun('possessive')} {captain.label} slipped past the lantern and reached the cove."
        )
        world.say(
            f"There, the crew found the hidden chest, and {creature.label} still shone in its moon-silver colors like a tiny triumph."
        )


def tell(setting: Setting, charm_cfg: Charm, creature_cfg: Creature,
         hero_name: str = "Mara", hero_type: str = "girl",
         captain_type: str = "captain", trait: str = "bold") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type, label="captain"))
    charm = world.add(Entity(id="Agate", type="charm", label=charm_cfg.label, phrase=charm_cfg.phrase))
    creature = world.add(Entity(id="Skit", type="chameleon", label=creature_cfg.id))
    world.facts["charm_entity"] = charm
    world.facts["creature_entity"] = creature

    setup_story(world, hero, captain, charm, creature)
    tension(world, hero, captain, charm, creature)
    world.para()
    turn(world, creature)
    resolution(world, hero, captain, creature)

    world.facts.update(
        hero=hero,
        captain=captain,
        charm=charm,
        creature=creature,
        setting=setting,
        trait=trait,
        resolved=creature.meters["hidden"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "cove": Setting(place="the moonlit cove", sea="calm", affords={"transformation"}),
    "deck": Setting(place="the pirate deck", sea="windy", affords={"transformation"}),
    "island": Setting(place="the tiny island shore", sea="gentle", affords={"transformation"}),
}

CHARMS = {
    "agate": Charm(
        id="agate",
        label="agate",
        phrase="a polished agate charm",
        spark="spark",
        glow="sea-glow",
    ),
}

CREATURES = {
    "chameleon": Creature(
        id="chameleon",
        label="Skit",
        base_color="green",
        transformed_color="moon-silver",
        cover="the moonlit waves",
        trigger="touch the agate",
    ),
}

GIRL_NAMES = ["Mara", "Nina", "Tess", "Ruby", "Lila"]
BOY_NAMES = ["Jory", "Pip", "Finn", "Bram", "Nico"]
TRAITS = ["bold", "curious", "spirited", "cheerful", "quick"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for charm_id in CHARMS:
            for creature_id in CREATURES:
                out.append((place, charm_id, creature_id))
    return out


def explain_rejection() -> str:
    return "(No story: this pirate tale needs an agate, a chameleon, and a transformation.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a pirate tale with an agate, a chameleon, and a transformation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--captain", choices=["captain"])
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
              and (args.charm is None or c[1] == args.charm)
              and (args.creature is None or c[2] == args.creature)]
    if not combos:
        raise StoryError(explain_rejection())
    place, charm, creature = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain = args.captain or "captain"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, charm=charm, creature=creature, name=name,
                       gender=gender, captain=captain, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short pirate story for a young child that includes the words "agate" and "chameleon".',
        f"Tell a swashbuckling story where {hero.id} uses an agate and a chameleon to solve a lookout problem.",
        f"Write a simple pirate tale about a magical transformation that helps a crew hide on a moonlit sea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    creature = f["creature"]
    charm = f["charm"]
    captain = f["captain"]
    return [
        QAItem(
            question=f"What did {hero.id} keep close in the pirate tale?",
            answer=f"{hero.id} kept {hero.pronoun('possessive')} {charm.label} close because it shone like sea glass.",
        ),
        QAItem(
            question=f"What happened when {creature.label} touched the agate?",
            answer=f"The agate sparked, and {creature.label} began a transformation that changed its colors into a moon-silver pattern.",
        ),
        QAItem(
            question=f"Why did the crew get past the lookout?",
            answer=f"The transformed chameleon blended with the moonlit waves, so the lookout did not spot {hero.id} and {hero.pronoun('possessive')} {captain.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an agate?",
            answer="An agate is a kind of stone with pretty bands or colors that people may polish and keep as a charm.",
        ),
        QAItem(
            question="What can a chameleon do?",
            answer="A chameleon can change its color to help it blend in with its surroundings.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a big change, when something becomes different from what it was before.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
charm(agate).
creature(chameleon).
setting(cove).
setting(deck).
setting(island).

valid_story(P, C, M) :- setting(P), charm(C), creature(M).

needs_transformation(C, M) :- charm(C), creature(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
    for m in CREATURES:
        lines.append(asp.fact("creature", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="cove", charm="agate", creature="chameleon", name="Mara", gender="girl", captain="captain", trait="bold"),
    StoryParams(place="deck", charm="agate", creature="chameleon", name="Nico", gender="boy", captain="captain", trait="curious"),
    StoryParams(place="island", charm="agate", creature="chameleon", name="Ruby", gender="girl", captain="captain", trait="spirited"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHARMS[params.charm], CREATURES[params.creature],
                 params.name, params.gender, params.captain, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for p, c, m in stories:
            print(f"  {p:8} {c:8} {m:12}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.place} ({p.charm} + {p.creature})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

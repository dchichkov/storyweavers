#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a careful child, a slippery promise, and a
twisty little rescue.

Seed premise:
- A young helper finds a magical stickle flower that grants luck.
- The helper is told the flower is liable to wobble loose if handled badly.
- Suspense grows when the flower disappears before the spring fair.
- Twist: the "lost" flower was used to guide a trapped lantern-fawn home.
- Happy ending: the helper learns the flower was never stolen, only shared.
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
# World model
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "witch", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the mossy glen"
    castle: str = "the little white castle"
    affords: set[str] = field(default_factory=lambda: {"forage", "follow", "sing"})


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    magic: str
    risk: str
    keep: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    need: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "glen": Setting(place="the mossy glen", castle="the little white castle", affords={"forage", "follow", "sing"}),
    "wood": Setting(place="the bluebell wood", castle="the lantern tower", affords={"forage", "follow"}),
    "meadow": Setting(place="the moonlit meadow", castle="the hilltop cottage", affords={"follow", "sing"}),
}

ARTIFACTS = {
    "stickle": Artifact(
        id="stickle",
        label="stickle flower",
        phrase="a bright stickle flower",
        magic="luck",
        risk="wobble loose",
        keep="nestle safely in a cloak pin",
        tags={"stickle", "magic", "flower"},
    ),
    "crown": Artifact(
        id="crown",
        label="silver crown",
        phrase="a silver crown with tiny bells",
        magic="dignity",
        risk="tilt off",
        keep="tie with a ribbon",
        tags={"crown", "silver"},
    ),
    "lantern": Artifact(
        id="lantern",
        label="glass lantern",
        phrase="a small glass lantern",
        magic="light",
        risk="crack",
        keep="wrap in wool",
        tags={"lantern", "light"},
    ),
}

CREATURES = {
    "faun": Creature(
        id="faun",
        label="lantern-fawn",
        phrase="a shy lantern-fawn with a glow like honey",
        need="a path home",
        tags={"faun", "lantern", "forest"},
    ),
    "bird": Creature(
        id="bird",
        label="silver bird",
        phrase="a silver bird with a scraped wing",
        need="a soft nest",
        tags={"bird", "wing"},
    ),
}

HERO_NAMES = ["Elin", "Mara", "Ivy", "Ros", "Tilda", "Nia"]
HELPER_NAMES = ["Pip", "Oren", "Luma", "Bram", "Sora", "Finn"]
TRAITS = ["kind", "brave", "curious", "gentle", "lively"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    artifact: str
    creature: str
    hero: str
    hero_kind: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def hero_title(kind: str) -> str:
    return {"girl": "girl", "boy": "boy"}.get(kind, kind)


def setup(world: World, hero: Entity, helper: Entity, artifact: Entity, creature: Entity) -> None:
    world.say(
        f"Once upon a time, in {world.setting.place}, there lived a little {hero_title(hero.type)} named {hero.id}."
    )
    world.say(
        f"{hero.id} was {world.facts['trait']} and loved the old stories about {artifact.label}s that could bring good luck."
    )
    world.say(
        f"One dawn, {hero.id} found {artifact.phrase} by the path, and {helper.id} said it was "
        f"liable to slip away if no one handled it carefully."
    )
    world.say(
        f"{hero.id} listened and tucked the flower into {hero.pronoun('possessive')} basket, hoping to keep it safe for the fair."
    )
    world.facts["artifact_safe"] = True


def suspense(world: World, hero: Entity, artifact: Entity) -> None:
    world.para()
    world.say(
        f"But when {hero.id} woke before the fair, the basket was empty."
    )
    world.say(
        f"The room felt quiet and cold, and {hero.id}'s heart beat fast, because the stickle flower was gone."
    )
    world.say(
        f'"If {artifact.label} is missing, the lanterns may dim," whispered {world.facts["helper"].id}, and the day grew full of suspense.'
    )
    world.facts["missing"] = True
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0


def search(world: World, hero: Entity, helper: Entity, creature: Entity) -> None:
    world.say(
        f"{hero.id} and {helper.id} followed a trail of soft gold dust through {world.setting.place}."
    )
    world.say(
        f"They passed ferns, stones, and little round mushrooms, calling for the stickle flower with careful voices."
    )
    world.say(
        f"At last they heard a tiny whimper under a briar arch, and there was {creature.phrase} trembling in the shade."
    )


def twist(world: World, hero: Entity, helper: Entity, artifact: Entity, creature: Entity) -> None:
    world.para()
    world.say(
        f"Then came the twist: the flower was not stolen at all."
    )
    world.say(
        f"{creature.id} had carried the stickle flower to the briars so its glow could guide the lost little creature home."
    )
    world.say(
        f"The flower had been hiding beside {creature.id}, bright as a small sunrise, because the forest path was dark and windy."
    )
    world.facts["found_with_creature"] = True
    world.facts["helped_creature"] = True


def happy_ending(world: World, hero: Entity, helper: Entity, artifact: Entity, creature: Entity) -> None:
    world.para()
    world.say(
        f"{hero.id} smiled and lifted the stickle flower gently, and {creature.id} blinked with relief."
    )
    world.say(
        f'“You were only helping,” {hero.id} said, and {helper.id} nodded. “That was a very kind thing to do.”'
    )
    world.say(
        f'Together they carried {creature.id} back to {world.setting.castle}, where warm cakes and lantern light waited.'
    )
    world.say(
        f"By evening, the stickle flower sat safely on the windowsill, the lanterns shone, and everyone laughed under the stars."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 2.0
    hero.memes["worry"] = 0.0
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Build story
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_kind))
    helper = world.add(Entity(id=params.helper, kind="character", type="helper"))
    artifact = world.add(Entity(id=params.artifact, type="artifact", label=ARTIFACTS[params.artifact].label, phrase=ARTIFACTS[params.artifact].phrase))
    creature = world.add(Entity(id=params.creature, type="creature", label=CREATURES[params.creature].label, phrase=CREATURES[params.creature].phrase))

    world.facts.update(
        hero=hero,
        helper=helper,
        artifact=artifact,
        creature=creature,
        trait=params.trait,
        place=params.place,
        artifact_name=params.artifact,
        creature_name=params.creature,
    )

    setup(world, hero, helper, artifact, creature)
    suspense(world, hero, artifact)
    search(world, hero, helper, creature)
    twist(world, hero, helper, artifact, creature)
    happy_ending(world, hero, helper, artifact, creature)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale that includes the word "{f["artifact_name"]}" and a gentle suspenseful mystery.',
        f"Tell a child-friendly story where {f['hero'].id} worries that the {ARTIFACTS[f['artifact_name']].label} is lost, but the ending is happy.",
        f"Write a fairy tale with a twist in which a small magical object is found beside a creature in need.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    artifact: Entity = f["artifact"]
    creature: Entity = f["creature"]
    return [
        QAItem(
            question=f"Who found the stickle flower at the start of the story?",
            answer=f"{hero.id} found the stickle flower by the path in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did the helper say the flower was liable to slip away?",
            answer=f"{helper.id} warned that the stickle flower was liable to slip away because it was a small magic flower and needed careful handling.",
        ),
        QAItem(
            question=f"What made the story suspenseful?",
            answer=f"The story became suspenseful when the basket was empty and {hero.id} thought the stickle flower had disappeared before the fair.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the stickle flower was not stolen; {creature.id} had taken it only to guide the lost creature home.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {creature.id} safely home, the stickle flower back on the windowsill, and the lanterns shining at {world.setting.castle}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a made-up story that often has magic, brave helpers, and a lesson or a happy ending.",
        ),
        QAItem(
            question="What does it mean if someone is liable to do something?",
            answer="If something is liable to happen, it is likely or ready to happen unless someone is careful.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that makes you wonder what will happen next.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you thought was happening.",
        ),
        QAItem(
            question="Why do happy endings feel nice?",
            answer="Happy endings feel nice because the trouble gets solved and the characters end up safe or content.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld with stickle, liable, suspense, twist, and a happy ending.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--artifact", choices=sorted(ARTIFACTS))
    ap.add_argument("--creature", choices=sorted(CREATURES))
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(sorted(SETTINGS))
    artifact = args.artifact or "stickle"
    creature = args.creature or "faun"
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.name or rng.choice(HERO_NAMES if gender == "girl" else HELPER_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES + HERO_NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)

    if artifact not in ARTIFACTS:
        raise StoryError("Unknown artifact.")
    if creature not in CREATURES:
        raise StoryError("Unknown creature.")
    return StoryParams(place=place, artifact=artifact, creature=creature, hero=hero, hero_kind=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
artifact(stickle).
artifact(crown).
artifact(lantern).

creature(faun).
creature(bird).

place(glen).
place(wood).
place(meadow).

likely_story(P,A,C) :- place(P), artifact(A), creature(C), A = stickle, C = faun.
valid_story(P,A,C) :- likely_story(P,A,C).
#show valid_story/3.
"""

def asp_facts() -> str:
    import asp
    out = []
    for p in SETTINGS:
        out.append(asp.fact("place", p))
    for a in ARTIFACTS:
        out.append(asp.fact("artifact", a))
    for c in CREATURES:
        out.append(asp.fact("creature", c))
    return "\n".join(out)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, a, c) for p in SETTINGS for a in ARTIFACTS for c in CREATURES if a == "stickle" and c == "faun"}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid story combo).")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="glen", artifact="stickle", creature="faun", hero="Elin", hero_kind="girl", helper="Pip", trait="kind"),
    StoryParams(place="wood", artifact="stickle", creature="faun", hero="Mara", hero_kind="girl", helper="Luma", trait="curious"),
    StoryParams(place="meadow", artifact="stickle", creature="faun", hero="Ivy", hero_kind="girl", helper="Bram", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        if len(samples) > 1 and not args.all:
            print(f"### variant {idx + 1}")
        elif args.all:
            p = sample.params
            print(f"### {p.hero} in {p.place}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

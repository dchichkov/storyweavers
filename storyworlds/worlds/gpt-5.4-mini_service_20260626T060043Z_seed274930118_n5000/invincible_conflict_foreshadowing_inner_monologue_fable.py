#!/usr/bin/env python3
"""
storyworlds/worlds/invincible_conflict_foreshadowing_inner_monologue_fable.py
==============================================================================

A tiny fable-style story world about pride, warning signs, inner monologue,
and a late-arriving kinder choice.

Premise:
- A small creature sets out feeling invincible.
- Foreshadowing appears in the sky, the wind, and other tiny signs.
- Another creature warns of trouble.
- The proud one thinks through the problem in private, then must choose
  between boasting and accepting help.

The simulated world tracks both physical meters and emotional memes so the
ending image comes from state changes rather than a frozen template.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["worry", "pride", "courage", "calm", "hope", "strain", "wet", "fear", "helpfulness"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

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
    place: str = "the meadow"
    affords: set[str] = field(default_factory=set)
    sky: str = "clear"


@dataclass
class CharacterSpec:
    type: str
    label: str
    phrase: str
    trait: str


@dataclass
class ObstacleSpec:
    id: str
    label: str
    phrase: str
    risk: str
    foreshadow: str
    mess: str


@dataclass
class AidSpec:
    id: str
    label: str
    phrase: str
    action: str
    effect: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    weather: str = ""
    threat: str = ""
    rescue: str = ""

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.weather = self.weather
        w.threat = self.threat
        w.rescue = self.rescue
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"walk", "deliver"}),
    "brook": Setting(place="the brook path", affords={"cross", "deliver"}),
    "orchard": Setting(place="the orchard", affords={"walk", "deliver"}),
}

HEROES = {
    "beetle": CharacterSpec(type="beetle", label="little beetle", phrase="a shiny beetle with a black shell", trait="proud"),
    "mouse": CharacterSpec(type="mouse", label="little mouse", phrase="a small mouse with quick paws", trait="nervous"),
    "rabbit": CharacterSpec(type="rabbit", label="little rabbit", phrase="a fast rabbit with long ears", trait="lively"),
}

RIVALS = {
    "sparrow": CharacterSpec(type="bird", label="sparrow", phrase="a sparrow with a sharp beak", trait="watchful"),
    "snail": CharacterSpec(type="snail", label="snail", phrase="a snail with a bright shell", trait="patient"),
    "frog": CharacterSpec(type="frog", label="frog", phrase="a frog with green feet", trait="plainspoken"),
}

OBSTACLES = {
    "storm": ObstacleSpec(
        id="storm",
        label="storm cloud",
        phrase="a storm cloud",
        risk="wet and slippery",
        foreshadow="the cloud had been growing gray since morning",
        mess="wet",
    ),
    "wind": ObstacleSpec(
        id="wind",
        label="wind gust",
        phrase="a strong wind",
        risk="hard to balance",
        foreshadow="the grass kept bowing low before the trouble came",
        mess="strain",
    ),
}

AIDS = {
    "leaf": AidSpec(
        id="leaf",
        label="broad leaf",
        phrase="a broad green leaf",
        action="use as a tiny roof",
        effect="stayed dry under the leaf",
    ),
    "tunnel": AidSpec(
        id="tunnel",
        label="root tunnel",
        phrase="a root tunnel",
        action="take the safe way through the roots",
        effect="kept out of the wind",
    ),
    "berry": AidSpec(
        id="berry",
        label="berry basket",
        phrase="a berry basket",
        action="carry the berries together",
        effect="made the load feel lighter",
    ),
}

GENTLE_NAMES = ["Bram", "Milo", "Pip", "Nia", "Tia", "Oren", "Luna", "Mina"]
TRAITS = ["proud", "cheerful", "stubborn", "careful", "curious"]

CURATED = [
    ("meadow", "beetle", "sparrow", "storm", "leaf"),
    ("brook", "mouse", "frog", "wind", "tunnel"),
    ("orchard", "rabbit", "snail", "storm", "berry"),
]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero: str
    witness: str
    obstacle: str
    aid: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _capitalize_first(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero_spec = HEROES[params.hero]
    witness_spec = RIVALS[params.witness]
    obstacle = OBSTACLES[params.obstacle]
    aid = AIDS[params.aid]

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=hero_spec.type,
        label=hero_spec.label,
        phrase=hero_spec.phrase,
        traits=[params.trait, hero_spec.trait],
    ))
    witness = world.add(Entity(
        id="Witness",
        kind="character",
        type=witness_spec.type,
        label=witness_spec.label,
        phrase=witness_spec.phrase,
        traits=[witness_spec.trait],
    ))
    world.add(Entity(
        id="Obstacle",
        kind="thing",
        type=obstacle.id,
        label=obstacle.label,
        phrase=obstacle.phrase,
    ))
    world.add(Entity(
        id="Aid",
        kind="thing",
        type=aid.id,
        label=aid.label,
        phrase=aid.phrase,
    ))

    world.weather = "darkening"
    world.threat = obstacle.id
    world.rescue = aid.id

    # opening state
    hero.memes["pride"] += 1
    hero.memes["courage"] += 1
    witness.memes["helpfulness"] += 1

    world.say(f"{hero.id} was {_article(hero_spec.type)} {hero_spec.phrase} who loved to boast that {hero.pronoun('subject')} was invincible.")
    world.say(f"{hero.id} walked through {world.setting.place} with {hero.pronoun('possessive')} chin high, while {witness.id} kept pace beside {hero.pronoun('object')}.")

    # foreshadowing
    world.para()
    world.say(f"That morning, {obstacle.foreshadow}.")
    world.say(f"The air felt odd, and even the leaves seemed to listen for what would happen next.")

    # conflict setup
    world.para()
    world.say(f"{hero.id} wanted to { 'cross' if params.place != 'orchard' else 'deliver' } the path anyway.")
    world.say(f"{witness.id} said, \"You may be brave, but the sky is warning us.\"")
    hero.memes["worry"] += 0.5
    hero.memes["pride"] += 0.5
    witness.memes["worry"] += 1

    # inner monologue
    world.say(f"Inside, {hero.id} thought, \"My shell is strong. The wind cannot touch me. I am invincible.\"")
    world.say(f"Still, {hero.id} noticed the cloud, and {hero.pronoun('possessive')} thoughts wavered a little.")

    # physical risk increases
    hero.meters["strain"] += 1
    if obstacle.id == "storm":
        hero.meters["wet"] += 0.5
    else:
        hero.meters["strain"] += 0.5

    # tension
    world.para()
    world.say(f"Then the trouble arrived at once: {obstacle.phrase} rolled in over {world.setting.place}.")
    world.say(f"The path turned {obstacle.risk}, and {hero.id} could no longer pretend nothing had changed.")

    # helper offer
    world.say(f"{witness.id} pointed to {aid.phrase} and said, \"Try this. It will {aid.effect}.\"")
    hero.memes["fear"] += 0.5
    hero.memes["hope"] += 0.5

    # resolution
    world.para()
    hero.memes["pride"] -= 0.5
    hero.memes["calm"] += 1
    world.say(f"{hero.id} listened, and the proud feeling softened.")
    world.say(f"{hero.id} chose to {aid.action}, and together they went on.")
    hero.meters["strain"] = max(0.0, hero.meters["strain"] - 0.5)
    if obstacle.id == "storm":
        hero.meters["wet"] = max(0.0, hero.meters["wet"] - 0.5)
    world.say(f"In the end, {hero.id} was not admired for being invincible, but for being wise enough to accept help.")

    world.para()
    world.say(f"The fable ended with {hero.id} moving safely forward, {witness.id} beside {hero.pronoun('object')}, and the storm left behind in the sky.")

    world.facts.update(
        hero=hero,
        witness=witness,
        obstacle=obstacle,
        aid=aid,
        place=params.place,
        story_params=params,
    )
    return world


# ---------------------------------------------------------------------------
# Reasoning and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    witness: Entity = f["witness"]
    obstacle: ObstacleSpec = f["obstacle"]
    aid: AidSpec = f["aid"]
    return [
        f'Write a short fable for a child about {hero.id}, who thinks {hero.pronoun("subject")} is invincible, but a warning sign changes the plan.',
        f'Tell a gentle story where {witness.id} warns {hero.id} about {obstacle.label} and they choose {aid.label} instead of boasting.',
        f'Write a simple fable that includes inner thoughts, a small conflict, and a safer choice under a darkening sky.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    witness: Entity = f["witness"]
    obstacle: ObstacleSpec = f["obstacle"]
    aid: AidSpec = f["aid"]
    return [
        QAItem(
            question=f"What did {hero.id} keep telling {hero.pronoun('object')}self at the start of the story?",
            answer=f"{hero.id} kept telling {hero.pronoun('object')}self that {hero.pronoun('subject')} was invincible, even though the sky was giving warning signs.",
        ),
        QAItem(
            question=f"What did {witness.id} warn {hero.id} about?",
            answer=f"{witness.id} warned {hero.id} that {obstacle.phrase} was coming and the path could turn {obstacle.risk}.",
        ),
        QAItem(
            question=f"What did {hero.id} choose to do instead of just boasting?",
            answer=f"{hero.id} chose to {aid.action}, which helped {hero.id} stay safe and keep going.",
        ),
        QAItem(
            question=f"How did the ending change the way {hero.id} was seen?",
            answer=f"At the end, {hero.id} was not important because of being invincible, but because {hero.id} listened and accepted help.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does invincible mean?",
            answer="Invincible means so strong or safe that you think nothing can beat you or hurt you.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue early in the story that hints that something important may happen later.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thoughts that the reader can hear, even if nobody else can.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson at the end.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the hero has a witness, an obstacle, and a possible aid.
has_story(H, W, O, A) :- hero(H), witness(W), obstacle(O), aid(A), compatible(H, W, O, A).

% Compatibility is a small declarative mirror of the Python gate.
compatible(H, W, O, A) :- brave(H), warns(W, O), helps(A, O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid, h in HEROES.items():
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("brave", hid))
    for wid, w in RIVALS.items():
        lines.append(asp.fact("witness", wid))
        lines.append(asp.fact("warns", wid, "storm"))
        lines.append(asp.fact("warns", wid, "wind"))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("helps", aid, "storm"))
        lines.append(asp.fact("helps", aid, "wind"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero in HEROES:
            for witness in RIVALS:
                for obstacle in OBSTACLES:
                    for aid in AIDS:
                        combos.append((place, hero, witness, obstacle, aid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show has_story/4."))
    return sorted(set(asp.atoms(model, "has_story")))


def asp_verify() -> int:
    py = len(valid_combos())
    cl = len(asp_valid_combos())
    if cl != py:
        print(f"MISMATCH: python={py}, clingo={cl}")
        return 1
    print(f"OK: clingo and python agree on {py} possible story shapes.")
    return 0


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable storyworld about invincible pride, foreshadowing, and a kinder choice.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--hero", choices=HEROES.keys())
    ap.add_argument("--witness", choices=RIVALS.keys())
    ap.add_argument("--obstacle", choices=OBSTACLES.keys())
    ap.add_argument("--aid", choices=AIDS.keys())
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    witness = args.witness or rng.choice(list(RIVALS))
    obstacle = args.obstacle or rng.choice(list(OBSTACLES))
    aid = args.aid or rng.choice(list(AIDS))
    if obstacle == "storm" and aid not in {"leaf", "berry"}:
        raise StoryError("(No story: the storm needs a sheltering or sharing aid to resolve well.)")
    if obstacle == "wind" and aid not in {"tunnel", "berry"}:
        raise StoryError("(No story: the wind needs a sheltered or steady path to resolve well.)")
    name = args.name or rng.choice(GENTLE_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, hero=hero, witness=witness, obstacle=obstacle, aid=aid, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show has_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story shapes:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, (place, hero, witness, obstacle, aid) in enumerate(CURATED):
            params = StoryParams(
                place=place,
                hero=hero,
                witness=witness,
                obstacle=obstacle,
                aid=aid,
                name=GENTLE_NAMES[i % len(GENTLE_NAMES)],
                trait=TRAITS[i % len(TRAITS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i - 1
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


def _on_trace(world: World) -> str:
    return dump_trace(world)


if __name__ == "__main__":
    main()

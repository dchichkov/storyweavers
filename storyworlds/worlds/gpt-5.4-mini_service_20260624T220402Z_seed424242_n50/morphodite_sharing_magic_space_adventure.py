#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


def _dd() -> defaultdict[str, float]:
    return defaultdict(float)


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    shared_with: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=_dd)
    memes: dict[str, float] = field(default_factory=_dd)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "morphodite":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"robot", "drone", "rover", "orb", "tool"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"captain", "pilot", "guide"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    label: str
    image: str
    edge: str
    dark: bool = True
    tags: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    compatible_places: set[str]
    share_way: str
    effect: str
    tags: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    artifact: str
    friend_kind: str
    hero_name: str
    friend_name: str
    guide_name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trail_lit: bool = False
        self.facts: dict[str, object] = {}

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.trail_lit = self.trail_lit
        clone.facts = copy.deepcopy(self.facts)
        return clone


def bump(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def feel(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def pair_ok(setting: Setting, artifact: Artifact) -> bool:
    return setting.id in artifact.compatible_places


def explain_rejection(setting: Setting, artifact: Artifact) -> str:
    return (
        f"(No story: {artifact.phrase} does not fit {setting.label}. "
        f"This space adventure only works when the magic object can truly help "
        f"in that place and can be shared there.)"
    )


SETTINGS: dict[str, Setting] = {
    "comet_tunnel": Setting(
        id="comet_tunnel",
        label="the comet tunnel",
        image="silver dust drifted along black stone walls",
        edge="the tunnel mouth",
        dark=True,
        tags={"space", "comet", "tunnel"},
        affords={"star_lantern", "moon_map"},
    ),
    "starship_hall": Setting(
        id="starship_hall",
        label="the starship hall",
        image="tiny panels blinked softly along the wall",
        edge="the far hatch",
        dark=True,
        tags={"space", "starship"},
        affords={"star_lantern", "moon_map", "comet_compass"},
    ),
    "asteroid_bridge": Setting(
        id="asteroid_bridge",
        label="the asteroid bridge",
        image="floating rocks hung in a line like stepping stones",
        edge="the first stone",
        dark=True,
        tags={"space", "asteroid", "bridge"},
        affords={"spark_orb", "comet_compass"},
    ),
    "nebula_dock": Setting(
        id="nebula_dock",
        label="the nebula dock",
        image="purple clouds curled under the dock like soft cotton",
        edge="the dock rail",
        dark=True,
        tags={"space", "nebula", "dock"},
        affords={"spark_orb", "star_lantern"},
    ),
}

ARTIFACTS: dict[str, Artifact] = {
    "star_lantern": Artifact(
        id="star_lantern",
        label="star lantern",
        phrase="a magic star lantern",
        compatible_places={"comet_tunnel", "starship_hall", "nebula_dock"},
        share_way="hold it together",
        effect="silver dots bloomed on the dark path",
        tags={"magic", "sharing", "star_lantern"},
    ),
    "moon_map": Artifact(
        id="moon_map",
        label="moon map",
        phrase="a magic moon map",
        compatible_places={"comet_tunnel", "starship_hall"},
        share_way="spread it open between them",
        effect="a blue line drew itself home",
        tags={"magic", "sharing", "moon_map"},
    ),
    "spark_orb": Artifact(
        id="spark_orb",
        label="spark orb",
        phrase="a magic spark orb",
        compatible_places={"asteroid_bridge", "nebula_dock"},
        share_way="cup it in both hands",
        effect="a tiny bridge of light flickered on",
        tags={"magic", "sharing", "spark_orb"},
    ),
    "comet_compass": Artifact(
        id="comet_compass",
        label="comet compass",
        phrase="a magic comet compass",
        compatible_places={"asteroid_bridge", "starship_hall"},
        share_way="take turns pointing it",
        effect="its needle spun and pointed to the safe way",
        tags={"magic", "sharing", "comet_compass"},
    ),
}

FRIEND_KINDS = {
    "robot": ("robot", "a small robot"),
    "drone": ("drone", "a little drone"),
    "rover": ("rover", "a tiny rover"),
}

HERO_NAMES = [
    "Miro", "Lumi", "Nova", "Tala", "Orin", "Pia", "Zuni", "Rae",
]
FRIEND_NAMES = [
    "Pip", "Bix", "Zee", "Toto", "Moss", "Nib", "Flick", "Rill",
]
GUIDE_NAMES = [
    "Captain Sol", "Pilot Jun", "Navigator Ray", "Captain Mira",
]
TRAITS = ["curious", "gentle", "brave", "shy", "cheerful", "careful"]


def predict_darkness(world: World, artifact: Artifact) -> bool:
    sim = world.copy()
    sim.get(artifact.id).shared_with = None
    return not sim.trail_lit


def _r_share_brightens(world: World) -> list[str]:
    out: list[str] = []
    art = world.get(world.facts["artifact_id"])
    hero = world.get(world.facts["hero_id"])
    friend = world.get(world.facts["friend_id"])
    if art.shared_with and not world.trail_lit:
        sig = ("share_brightens", art.id, art.shared_with)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        art.meters["glow"] += 1
        hero.memes["generosity"] += 1
        hero.memes["joy"] += 1
        friend.memes["relief"] += 1
        friend.memes["joy"] += 1
        world.trail_lit = True
        out.append(f"The {art.label} glowed brighter when {hero.id} and {friend.id} shared it.")
    return out


def _r_shared_relief(world: World) -> list[str]:
    out: list[str] = []
    if not world.trail_lit:
        return out
    guide = world.get(world.facts["guide_id"])
    sig = ("shared_relief", guide.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guide.memes["pride"] += 1
    guide.memes["relief"] += 1
    out.append(f"{guide.id} smiled because the safe way was now easy to see.")
    return out


CAUSAL_RULES = [_r_share_brightens, _r_shared_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def introduce(world: World, hero: Entity, friend: Entity, guide: Entity, artifact: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"{hero.id} was a little morphodite who could change shape when space needed a clever helper."
    )
    world.say(
        f"{hero.id} was {trait} and loved bright, magical things that glittered like tiny stars."
    )
    world.say(
        f"{friend.id} was {friend.phrase} who liked to follow shining paths, and {guide.id} was steering them through the dark."
    )
    world.say(
        f"At the edge of {world.setting.label}, {hero.id} found {artifact.phrase} and held it close."
    )


def arrive(world: World, hero: Entity, friend: Entity, guide: Entity, artifact: Entity) -> None:
    world.say(
        f"They moved deeper into {world.setting.label}, where {world.setting.image}."
    )
    world.say(
        f"{hero.id} wanted to keep the {artifact.label} all to itself because it shone so warmly."
    )
    world.say(
        f"But the path by {world.setting.edge} was dark, and {friend.id} had to slow down to see the next step."
    )


def warn(world: World, guide: Entity, hero: Entity, friend: Entity, artifact: Entity) -> bool:
    if not predict_darkness(world, artifact):
        return False
    world.facts["predicted_dark"] = True
    world.say(
        f'"If we keep the {artifact.label} to ourselves, we may miss the safe way," {guide.id} said softly.'
    )
    world.say(
        f"{friend.id} gave a tiny wobble and looked at the black path with worried lights."
    )
    return True


def hesitate(world: World, hero: Entity, artifact: Entity) -> None:
    feel(hero, "stubborn", 1)
    feel(hero, "worry", 0.5)
    world.say(
        f"{hero.id} clutched the {artifact.label} tighter, because it felt special in {hero.pronoun('possessive')} hands."
    )


def turn(world: World, hero: Entity, friend: Entity, artifact: Artifact) -> None:
    feel(hero, "kindness", 1)
    feel(hero, "generosity", 1)
    bump(hero, "morph", 1)
    world.say(
        f"Then {hero.id} saw how small {friend.id} looked beside the dark trail."
    )
    world.say(
        f"So the morphodite stretched into a second gentle shape and said it would {artifact.share_way}."
    )
    shared = world.get(artifact.id)
    shared.shared_with = friend.id
    shared.carried_by = hero.id
    bump(shared, "glow", 1)
    propagate(world, narrate=True)


def resolve(world: World, hero: Entity, friend: Entity, guide: Entity, artifact: Artifact) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    guide.memes["joy"] += 1
    world.say(
        f"With the {artifact.label} shared, {artifact.effect}."
    )
    world.say(
        f"{friend.id} smiled, {guide.id} relaxed, and {hero.id} felt proud instead of stingy."
    )
    if artifact.id == "moon_map":
        ending = f"The blue line on the map pointed straight home through the starry hall."
    elif artifact.id == "star_lantern":
        ending = f"Little silver dots blinked along the tunnel, and every step felt safe."
    elif artifact.id == "spark_orb":
        ending = f"A tiny bridge of light held steady over the floating rocks."
    elif artifact.id == "comet_compass":
        ending = f"The compass needle spun once and then pointed exactly where they should go."
    else:
        ending = f"Their path turned bright and friendly."
    world.say(ending)
    world.say(
        f"At the end, {hero.id} and {friend.id} went on together, while the magic glowed brighter because it had been shared."
    )


def tell(
    setting: Setting,
    artifact: Artifact,
    hero_name: str,
    friend_kind: str,
    friend_name: str,
    guide_name: str,
    trait: str,
) -> World:
    world = World(setting)

    friend_type, friend_phrase = FRIEND_KINDS[friend_kind]
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="morphodite",
        label=hero_name,
        phrase=f"a little morphodite named {hero_name}",
        traits=["little", trait, "spacey"],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_type,
        label=friend_name,
        phrase=friend_phrase,
        traits=["little", "patient"],
    ))
    guide = world.add(Entity(
        id=guide_name,
        kind="character",
        type="pilot",
        label=guide_name,
        phrase=guide_name,
        traits=["calm", "steady"],
    ))
    art = world.add(Entity(
        id=artifact.id,
        kind="thing",
        type="tool",
        label=artifact.label,
        phrase=artifact.phrase,
        traits=["magic", "sharing"],
        owner=hero.id,
    ))

    world.facts.update(
        hero_id=hero.id,
        friend_id=friend.id,
        guide_id=guide.id,
        artifact_id=art.id,
        setting_id=setting.id,
        artifact_label=artifact.label,
        setting_label=setting.label,
    )

    introduce(world, hero, friend, guide, art)
    world.para()
    arrive(world, hero, friend, guide, art)
    warn(world, guide, hero, friend, art)
    hesitate(world, hero, art)
    world.para()
    turn(world, hero, friend, artifact)
    world.para()
    resolve(world, hero, friend, guide, artifact)
    world.facts.update(shared=True, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting_label = f["setting_label"]
    artifact_label = f["artifact_label"]
    hero_id = f["hero_id"]
    friend_id = f["friend_id"]
    guide_id = f["guide_id"]
    return [
        (
            f'Write a short space adventure for a 3-to-5-year-old about a morphodite named {hero_id} '
            f'who learns to share a {artifact_label} at {setting_label}.'
        ),
        (
            f"Tell a gentle story where {hero_id} wants to keep a magic {artifact_label} but {friend_id} "
            f"needs it too, and {guide_id} helps them choose the shared way."
        ),
        (
            f'Write a child-friendly story with stars, sharing, and magic that ends with {hero_id} and '
            f'{friend_id} traveling safely together.'
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero_id = f["hero_id"]
    friend_id = f["friend_id"]
    guide_id = f["guide_id"]
    artifact_label = f["artifact_label"]
    setting_label = f["setting_label"]
    trait = next((t for t in world.get(hero_id).traits if t not in {"little", "spacey"}), "curious")
    artifact = world.get(f["artifact_id"])

    qa: list[QAItem] = [
        QAItem(
            question=f"Who was the story about in {setting_label}?",
            answer=(
                f"It was about {hero_id}, a little morphodite, and {friend_id}, who traveled with {guide_id} through {setting_label}."
            ),
        ),
        QAItem(
            question=f"Why did {guide_id} worry before {artifact_label} was shared?",
            answer=(
                f"{guide_id} worried because the path at {setting_label} was dark, and the {artifact_label} was needed to help both friends see the safe way."
            ),
        ),
        QAItem(
            question=f"How did {hero_id} help when {friend_id} could not see the path well?",
            answer=(
                f"{hero_id} decided to share the {artifact_label}, stretched into a clever new shape, and held it with {friend_id} so the magic could work better."
            ),
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=(
                f"The {artifact_label} glowed brighter, the path became safe, and {hero_id} and {friend_id} went on together instead of being stuck in the dark."
            ),
        ),
    ]
    if artifact.id == "moon_map":
        qa.append(QAItem(
            question=f"What did the moon map do after {hero_id} shared it?",
            answer="It drew a blue line that pointed the friends straight home.",
        ))
    elif artifact.id == "star_lantern":
        qa.append(QAItem(
            question=f"What did the star lantern show after it was shared?",
            answer="It filled the dark path with little silver dots of light.",
        ))
    elif artifact.id == "spark_orb":
        qa.append(QAItem(
            question=f"What did the spark orb make when it was shared?",
            answer="It flickered on a tiny bridge of light over the floating rocks.",
        ))
    elif artifact.id == "comet_compass":
        qa.append(QAItem(
            question=f"What did the comet compass do after both friends used it?",
            answer="Its needle spun and pointed to the safe way home.",
        ))
    return qa


KNOWLEDGE = {
    "morphodite": [
        (
            "What is a morphodite?",
            "A morphodite is a made-up space creature that can change shape in clever ways.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else use, hold, or enjoy something too.",
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is a special kind of impossible-sounding power that can make surprising things happen.",
        )
    ],
    "space": [
        (
            "What is space?",
            "Space is the big area beyond Earth where stars, planets, and moons are found.",
        )
    ],
    "comet": [
        (
            "What is a comet?",
            "A comet is a small icy space rock that can fly near the Sun and leave a bright tail behind it.",
        )
    ],
    "tunnel": [
        (
            "What is a tunnel?",
            "A tunnel is a long passage you can travel through, often inside rock, a hill, or a mountain.",
        )
    ],
    "starship": [
        (
            "What is a starship?",
            "A starship is a ship in stories that travels through space between stars.",
        )
    ],
    "bridge": [
        (
            "What is a bridge for?",
            "A bridge helps people cross over a gap, like water, rocks, or a deep drop.",
        )
    ],
    "star_lantern": [
        (
            "What does a star lantern do?",
            "A star lantern gives off bright light, so a dark space path is easier to see.",
        )
    ],
    "moon_map": [
        (
            "What does a moon map do?",
            "A moon map helps travelers see where to go, like a guide to a safe path.",
        )
    ],
    "spark_orb": [
        (
            "What is a spark orb for?",
            "A spark orb is a story object that can glow and light a way through a dark place.",
        )
    ],
    "comet_compass": [
        (
            "What does a compass do?",
            "A compass helps you know which way to go by pointing to the right direction.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "morphodite",
    "sharing",
    "magic",
    "space",
    "comet",
    "tunnel",
    "starship",
    "bridge",
    "star_lantern",
    "moon_map",
    "spark_orb",
    "comet_compass",
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.setting.tags)
    artifact = world.get(world.facts["artifact_id"])
    tags.update(artifact.tags)
    tags.add("morphodite")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    lines = ["--- world model state ---", f"  setting: {world.setting.label}", f"  trail_lit: {world.trail_lit}"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = [f"type={e.type}"]
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.shared_with:
            bits.append(f"shared_with={e.shared_with}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({sig[0] for sig in world.fired})}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, setting in SETTINGS.items():
        for artifact_id, artifact in ARTIFACTS.items():
            if pair_ok(setting, artifact):
                combos.append((place_id, artifact_id))
    return sorted(combos)


CURATED = [
    StoryParams(
        place="comet_tunnel",
        artifact="star_lantern",
        friend_kind="robot",
        hero_name="Miro",
        friend_name="Pip",
        guide_name="Captain Sol",
        trait="curious",
    ),
    StoryParams(
        place="starship_hall",
        artifact="moon_map",
        friend_kind="drone",
        hero_name="Lumi",
        friend_name="Zee",
        guide_name="Pilot Jun",
        trait="gentle",
    ),
    StoryParams(
        place="asteroid_bridge",
        artifact="comet_compass",
        friend_kind="rover",
        hero_name="Nova",
        friend_name="Bix",
        guide_name="Navigator Ray",
        trait="brave",
    ),
    StoryParams(
        place="nebula_dock",
        artifact="spark_orb",
        friend_kind="robot",
        hero_name="Tala",
        friend_name="Flick",
        guide_name="Captain Mira",
        trait="cheerful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a morphodite learns to share a magic space object."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--artifact", choices=sorted(ARTIFACTS))
    ap.add_argument("--friend-kind", choices=sorted(FRIEND_KINDS))
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--guide-name")
    ap.add_argument("--trait", choices=sorted(set(TRAITS)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--trace", action="store_true", help="dump the world model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.artifact:
        setting = SETTINGS[args.place]
        artifact = ARTIFACTS[args.artifact]
        if not pair_ok(setting, artifact):
            raise StoryError(explain_rejection(setting, artifact))

    combos = [
        (place_id, artifact_id)
        for place_id, artifact_id in valid_combos()
        if (args.place is None or args.place == place_id)
        and (args.artifact is None or args.artifact == artifact_id)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, artifact_id = rng.choice(combos)
    friend_kind = args.friend_kind or rng.choice(sorted(FRIEND_KINDS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    guide_name = args.guide_name or rng.choice(GUIDE_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        artifact=artifact_id,
        friend_kind=friend_kind,
        hero_name=hero_name,
        friend_name=friend_name,
        guide_name=guide_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ARTIFACTS[params.artifact],
        params.hero_name,
        params.friend_kind,
        params.friend_name,
        params.guide_name,
        params.trait,
    )
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        if setting.dark:
            lines.append(asp.fact("dark", place_id))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, a))
    for artifact_id, artifact in ARTIFACTS.items():
        lines.append(asp.fact("artifact", artifact_id))
        lines.append(asp.fact("magic", artifact_id))
        lines.append(asp.fact("shareable", artifact_id))
        for place_id in sorted(artifact.compatible_places):
            lines.append(asp.fact("compatible", place_id, artifact_id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, A) :- place(P), artifact(A), compatible(P, A), magic(A), shareable(A).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    else:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")

    exercised = 0
    try:
        for place_id, artifact_id in sorted(py):
            params = StoryParams(
                place=place_id,
                artifact=artifact_id,
                friend_kind="robot",
                hero_name="Miro",
                friend_name="Pip",
                guide_name="Captain Sol",
                trait="curious",
            )
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError(f"generated empty story for {place_id}/{artifact_id}")
            if not sample.story_qa:
                raise StoryError(f"missing story QA for {place_id}/{artifact_id}")
            exercised += 1
        print(f"OK: generated and checked {exercised} story variants.")
    except Exception as exc:
        ok = False
        print(f"VERIFY STORY FAILURE: {exc}")
    return 0 if ok else 1


def asp_valid_stories() -> list[tuple[str, str]]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, artifact) combos:\n")
        for place_id, artifact_id in combos:
            print(f"  {place_id:15} {artifact_id:15}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        limit = max(args.n * 50, 50)
        while len(samples) < args.n and i < limit:
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
            header = f"### {p.hero_name}: {p.artifact} at {p.place} (friend_kind: {p.friend_kind})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

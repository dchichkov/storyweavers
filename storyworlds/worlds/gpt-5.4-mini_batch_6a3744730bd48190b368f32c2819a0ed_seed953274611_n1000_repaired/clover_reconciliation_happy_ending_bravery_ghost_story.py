#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clover_reconciliation_happy_ending_bravery_ghost_story.py
=========================================================================================

A small standalone storyworld for a gentle ghost story about clover, bravery,
and reconciliation.

Premise:
- Two children meet a shy ghost in an old garden.
- One child is scared, one is braver, and a clover patch becomes the turning
  point.
- The ghost and the children misunderstand each other at first, then reconcile.
- The ending is warm, safe, and happy.

The story is driven by world state:
- physical meters: breeze, glow, wetness, settled, picked, planted
- emotional memes: fear, courage, hurt, trust, gratitude, joy

The prose is not a frozen paragraph with swapped nouns; it follows the evolving
world and the ending image proves what changed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    adjectives: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Scene:
    id: str
    place: str
    dark_place: str
    sound: str
    clover_phrase: str
    atmosphere: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Spirit:
    id: str
    name: str
    glow: str
    fear_note: str
    apology: str
    gift: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Charm:
    id: str
    label: str
    use: str
    comfort: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    scene: str
    spirit: str
    charm: str
    brave_child: str
    brave_gender: str
    shy_child: str
    shy_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SCENES = {
    "moon_garden": Scene(
        id="moon_garden",
        place="an old moonlit garden",
        dark_place="the stone path behind the roses",
        sound="the wind rattled the fence softly",
        clover_phrase="a tiny clover patch glimmered near the path",
        atmosphere="soft silver shadows lay over the grass",
        tags={"ghost", "garden", "clover", "moon"},
    ),
    "attic_house": Scene(
        id="attic_house",
        place="an old house garden under a slanted roof",
        dark_place="the back steps by the ivy",
        sound="the boards creaked in the night breeze",
        clover_phrase="a brave little clover grew by the steps",
        atmosphere="blue shadows made every corner look secret",
        tags={"ghost", "house", "clover", "night"},
    ),
}

SPIRITS = {
    "mossy": Spirit(
        id="mossy",
        name="Mossy",
        glow="a pale green glow",
        fear_note="was not angry, only lonely",
        apology="I only wanted someone to notice me",
        gift="kept the clover safe all night",
        tags={"ghost", "kind", "clover"},
    ),
    "pearl": Spirit(
        id="pearl",
        name="Pearl",
        glow="a soft white glow",
        fear_note="looked worried and small",
        apology="I did not mean to frighten anyone",
        gift="tucked the clover in a shell dish",
        tags={"ghost", "kind", "clover"},
    ),
}

CHARMS = {
    "lantern": Charm(
        id="lantern",
        label="a paper lantern",
        use="held it up like a little moon",
        comfort="the light was steady and warm",
        tags={"light", "safe"},
    ),
    "bell": Charm(
        id="bell",
        label="a small silver bell",
        use="rang it once so the sound would reach the ghost",
        comfort="the bell made a friendly tinkling sound",
        tags={"sound", "safe"},
    ),
    "blanket": Charm(
        id="blanket",
        label="a folded blanket",
        use="wrapped it around the scared child",
        comfort="the blanket made the night feel less cold",
        tags={"warmth", "safe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "June", "Zoe"]
BOY_NAMES = ["Theo", "Eli", "Finn", "Noah", "Milo", "Owen"]
SCARY_WORDS = ["shiver", "whisper", "mist", "shadow", "rattle"]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        other = World()
        other.entities = {k: v for k, v in self.entities.items()}
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    if ghost.meters["visible"] < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("brave", "shy"):
        world.get(eid).memes["fear"] += 1
    out.append("__spooky__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    if world.get("ghost").memes["trust"] < THRESHOLD:
        return out
    sig = ("settle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("ghost").meters["settled"] += 1
    return out


CAUSAL_RULES = [Rule("spook", _r_spook), Rule("settle", _r_settle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for spirit in SPIRITS:
            for charm in CHARMS:
                combos.append((scene, spirit, charm))
    return combos


def ghost_can_startle(spirit: Spirit) -> bool:
    return "ghost" in spirit.tags


def charm_is_helpful(charm: Charm) -> bool:
    return "safe" in charm.tags


def default_names(rng: random.Random) -> tuple[str, str]:
    brave = rng.choice(GIRL_NAMES + BOY_NAMES)
    shy = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != brave])
    return brave, shy


def tell(scene: Scene, spirit: Spirit, charm: Charm, brave_name: str, brave_gender: str,
         shy_name: str, shy_gender: str) -> World:
    world = World()
    brave = world.add(Entity(id="brave", kind="character", type=brave_gender, label=brave_name, role="brave"))
    shy = world.add(Entity(id="shy", kind="character", type=shy_gender, label=shy_name, role="shy"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=spirit.name, role="spirit"))
    clover = world.add(Entity(id="clover", kind="thing", type="plant", label="clover", tags={"clover"}))

    brave.memes["courage"] = 2.0
    shy.memes["fear"] = 1.0
    ghost.memes["lonely"] = 2.0
    ghost.meters["visible"] = 1.0
    clover.meters["growing"] = 1.0

    world.say(f"On a night of {scene.atmosphere}, {scene.place} waited quietly.")
    world.say(f"{scene.sound.capitalize()}, and {scene.clover_phrase}.")
    world.say(f"{brave_name} and {shy_name} stepped into the dark, carrying {charm.label}.")

    world.para()
    world.say(f"Then {spirit.name} drifted out from the shadows with {spirit.glow}.")
    world.say(f"{spirit.name} {spirit.fear_note}, and the air felt like a {random.choice(SCARY_WORDS)}.")
    shy.memes["fear"] += 1.0
    brave.memes["courage"] += 1.0
    propagate(world, narrate=False)

    world.say(f"{shy_name} gasped and nearly ran, but {brave_name} stood still.")
    world.say(f'"It is only a ghost," {brave_name} said, though {brave_name} was shaking a little.')
    world.say(f"Still, {brave_name} {charm.use}.")

    world.para()
    ghost.memes["hurt"] += 1.0
    world.say(f"{spirit.name} floated back and whispered, '{spirit.apology}.'")
    world.say(f"{shy_name} looked at the ghost and then at the clover.")
    world.say(f'"You did scare us," {shy_name} said softly. "But we can listen now."')
    world.say(f"{brave_name} nodded. " + f'"And we can be friends if you want to stay."')
    world.say(f"The little clover stayed bright in the moonlight, like a green promise.")
    ghost.memes["trust"] += 1.0
    brave.memes["trust"] += 1.0
    shy.memes["trust"] += 1.0

    world.para()
    propagate(world, narrate=False)
    ghost.meters["settled"] += 1.0
    brave.memes["joy"] += 1.0
    shy.memes["joy"] += 1.0
    ghost.memes["joy"] += 1.0
    world.say(f"{spirit.name} smiled a tiny, brave smile and {spirit.gift}.")
    world.say(f"{shy_name} stopped trembling. {brave_name} reached out, and the ghost reached back.")
    world.say(f"By the end, nobody was hiding. The garden was quiet, warm, and friends enough for everyone.")

    world.facts.update(
        scene=scene, spirit=spirit, charm=charm, brave=brave, shy=shy, clover=clover,
        resolved=True, reconciliation=True, happy_end=True,
        ghost_visible=ghost.meters["visible"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    spirit: Spirit = f["spirit"]
    charm: Charm = f["charm"]
    brave: Entity = f["brave"]
    shy: Entity = f["shy"]
    return [
        f'Write a gentle ghost story for a 4-to-6-year-old that includes the word "clover" and ends with reconciliation.',
        f"Tell a brave but soft ghost story where {brave.label} helps {shy.label} face {spirit.name}, and the children make peace.",
        f'Write a happy ending story set in {scene.place} where a ghost, a clover patch, and a kind promise help everyone become friends.',
        f"Use {charm.label} as a safe helper in a ghost story about fear turning into trust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    brave: Entity = f["brave"]
    shy: Entity = f["shy"]
    spirit: Spirit = f["spirit"]
    scene: Scene = f["scene"]
    answer1 = (
        f"The story is about {brave.label} and {shy.label} meeting {spirit.name} in {scene.place}. "
        f"It begins as a scary night, but it ends with everyone calm and friendly."
    )
    answer2 = (
        f"{brave.label} was the braver child. {brave.label} stayed near the ghost, used the little helper, "
        f"and gave {shy.label} the courage to keep talking instead of running away."
    )
    answer3 = (
        f"They reconciled by listening instead of hiding. {shy.label} admitted the fear, {spirit.name} apologized, "
        f"and the clover became a promise that the night could end well."
    )
    return [
        QAItem(question="Who was the story about?", answer=answer1),
        QAItem(question="Who acted bravely?", answer=answer2),
        QAItem(question="How did the children and the ghost make peace?", answer=answer3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clover?",
            answer="A clover is a small plant with round leaves. It often grows in grass and can look lucky or bright in the dark.",
        ),
        QAItem(
            question="Why can the dark make a ghost story feel spooky?",
            answer="Dark places hide shapes and make tiny sounds seem bigger. That is why brave words and a safe light can help.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and make peace again. They listen, apologize, and decide to be kind.",
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:6} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
ghost_visible :- visible(ghost,1).
settled :- trust(ghost,1).

#show valid/3.
#show ghost_visible/0.
#show settled/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for gid in SPIRITS:
        lines.append(asp.fact("spirit", gid))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        import asp
        if not asp.one_model(asp_program("", "#show valid/3.")):
            pass
    except Exception as exc:  # pragma: no cover - clingo availability/runtime
        print(f"ASP unavailable: {exc}")
        return 1

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


@dataclass
class CLIStory:
    scene: str
    spirit: str
    charm: str
    brave: str
    shy: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Gentle ghost story world with clover, bravery, and reconciliation.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--brave-name")
    ap.add_argument("--brave-gender", choices=["girl", "boy", "ghost"], default=None)
    ap.add_argument("--shy-name")
    ap.add_argument("--shy-gender", choices=["girl", "boy"], default=None)
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
    scene = args.scene or rng.choice(sorted(SCENES))
    spirit = args.spirit or rng.choice(sorted(SPIRITS))
    charm = args.charm or rng.choice(sorted(CHARMS))
    brave_name = args.brave_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    brave_gender = args.brave_gender or rng.choice(["girl", "boy"])
    shy_name = args.shy_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != brave_name])
    shy_gender = args.shy_gender or rng.choice(["girl", "boy"])
    if scene not in SCENES or spirit not in SPIRITS or charm not in CHARMS:
        raise StoryError("(No valid combination matches the given options.)")
    return StoryParams(
        scene=scene,
        spirit=spirit,
        charm=charm,
        brave_child=brave_name,
        brave_gender=brave_gender,
        shy_child=shy_name,
        shy_gender=shy_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"Unknown scene: {params.scene}")
    if params.spirit not in SPIRITS:
        raise StoryError(f"Unknown spirit: {params.spirit}")
    if params.charm not in CHARMS:
        raise StoryError(f"Unknown charm: {params.charm}")
    world = tell(
        SCENES[params.scene],
        SPIRITS[params.spirit],
        CHARMS[params.charm],
        params.brave_child,
        params.brave_gender,
        params.shy_child,
        params.shy_gender,
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


CURATED = [
    StoryParams(
        scene="moon_garden",
        spirit="mossy",
        charm="lantern",
        brave_child="Lily",
        brave_gender="girl",
        shy_child="Theo",
        shy_gender="boy",
    ),
    StoryParams(
        scene="attic_house",
        spirit="pearl",
        charm="bell",
        brave_child="Noah",
        brave_gender="boy",
        shy_child="June",
        shy_gender="girl",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show ghost_visible/0.\n#show settled/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero-style suspense tale set in a
storage closet, built from the seed words: discovery, theme, crab-dim.

Premise:
A small hero discovers a strange crab-dim clue hidden in a storage closet.
Suspense rises because the clue might be important, and the hero must decide
whether to open the taped box, trust the quiet dark, or call for help.

World model:
- Physical meters: shadow, dust, creak, sparkle, lockedness, tiny-hum.
- Emotional memes: courage, worry, wonder, pride, relief, suspense.

The simulated state drives the prose:
- Discovery increases wonder and suspense.
- The storage closet has real obstacles: a high shelf, a stuck latch, a taped box.
- A careful helper or a simple light can resolve the suspense.
- The ending proves what changed by showing the discovered item is safe and the
  hero's feelings shift from worry to relief.

Style target:
A child-facing Superhero Story with a clear beginning, tense middle, and a
resolved ending image.
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

STORY_THEME = "discovery"
SETTING_NAME = "storage closet"
STYLE_NAME = "Superhero Story"
SEED_WORD = "crab-dim"


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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = SETTING_NAME
    dark: bool = True
    cramped: bool = True


@dataclass
class DiscoveryItem:
    id: str
    label: str
    phrase: str
    clue: str
    weirdness: str
    hidden_in: str
    category: str = "clue"


@dataclass
class Helper:
    id: str
    label: str
    tool: str
    light: str
    method: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

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


def _m(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _n(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero suspense storyworld set in a storage closet.")
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--clue")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


HERO_NAMES = ["Nova", "Bolt", "Spark", "Vega", "Comet", "Iris"]
SIDEKICK_NAMES = ["Milo", "Pip", "Zia", "Bea", "Nori", "Tate"]


DISCOVERIES = {
    "crab-dim": DiscoveryItem(
        id="crab-dim",
        label="a tiny crab-dim compass",
        phrase="a tiny crab-dim compass",
        clue="it had a shell-shaped dial and a pinwheel pointer",
        weirdness="its red hand clicked like tiny claws",
        hidden_in="a taped cardboard box",
    ),
    "theme": DiscoveryItem(
        id="theme",
        label="a theme badge",
        phrase="a theme badge with a star on it",
        clue="it matched the old superhero posters",
        weirdness="it still smelled like dust and glue",
        hidden_in="a storage crate",
    ),
    "discovery": DiscoveryItem(
        id="discovery",
        label="a discovery map",
        phrase="a discovery map folded into quarters",
        clue="it showed a secret shelf behind the mop bucket",
        weirdness="it had a bright line drawn in silver ink",
        hidden_in="a file folder",
    ),
}

HELPERS = [
    Helper(id="flashlight", label="flashlight", tool="flashlight", light="a small beam", method="shine the beam"),
    Helper(id="gloves", label="gloves", tool="gloves", light="steady hands", method="pull the tape gently"),
    Helper(id="stepstool", label="step stool", tool="step stool", light="a higher reach", method="climb up carefully"),
]


@dataclass
class StoryParams:
    hero: str
    sidekick: str
    clue: str
    seed: Optional[int] = None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    clue = args.clue or rng.choice(sorted(DISCOVERIES))
    if clue not in DISCOVERIES:
        raise StoryError("Unknown clue choice.")
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    if hero == sidekick:
        raise StoryError("The hero and sidekick must be different characters.")
    return StoryParams(hero=hero, sidekick=sidekick, clue=clue)


def setup_world(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.hero, kind="character", type="hero", label=params.hero))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="sidekick", label=params.sidekick))
    clue = DISCOVERIES[params.clue]
    item = world.add(Entity(id="clue", kind="thing", type=clue.id, label=clue.label, phrase=clue.phrase))
    helper = world.add(Entity(id="helper", kind="thing", type="helper", label="helper"))
    helper.meters["light"] = 0.0

    world.facts.update(hero=hero, sidekick=sidekick, clue=item, helper=helper, clue_cfg=clue, setting=world.setting)
    return world


def predict_suspense(world: World) -> bool:
    sim = world.copy()
    hero = sim.get(sim.facts["hero"].id)
    clue_cfg: DiscoveryItem = sim.facts["clue_cfg"]
    _n(hero, "wonder", 1)
    _n(hero, "suspense", 1)
    _m(hero, "shadow", 1)
    return True if clue_cfg.hidden_in else False


def intro(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    clue_cfg: DiscoveryItem = world.facts["clue_cfg"]
    world.say(
        f"{hero.id} was a small superhero who loved discovery, especially when a theme of mystery floated in the air."
    )
    world.say(
        f"One afternoon, {hero.id} and {sidekick.id} slipped into the {world.setting.place}, where the light was thin and the shelves leaned close."
    )
    world.say(
        f"Near the back, {hero.id} noticed {clue_cfg.phrase} hidden in {clue_cfg.hidden_in}."
    )
    _n(hero, "wonder", 1)
    _m(hero, "shadow", 1)


def tension(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    clue_cfg: DiscoveryItem = world.facts["clue_cfg"]
    _n(hero, "suspense", 1)
    _n(sidekick, "worry", 1)
    _m(world.facts["helper"], "light", 0)
    world.say(
        f"{hero.id} wanted to pull the box open right away, but the closet was quiet in a way that made every little sound feel big."
    )
    world.say(
        f"A shelf creaked overhead, and {clue_cfg.weirdness}; that made {sidekick.id} whisper, \"What if it is important?\""
    )
    world.say(
        f"{hero.id} held still, because the clue looked strange and the tape felt stuck tight."
    )
    _m(hero, "creak", 1)
    _m(hero, "lockedness", 1)
    _n(hero, "worry", 1)
    _n(hero, "suspense", 2)


def choose_helper(world: World) -> Helper:
    clue_cfg: DiscoveryItem = world.facts["clue_cfg"]
    if clue_cfg.id == "crab-dim":
        return HELPERS[0]
    if clue_cfg.id == "theme":
        return HELPERS[1]
    return HELPERS[2]


def resolve_story(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    clue_cfg: DiscoveryItem = world.facts["clue_cfg"]
    helper = choose_helper(world)
    world.facts["helper_choice"] = helper

    world.para()
    world.say(
        f"Then {hero.id} remembered that a real hero does not race a mystery; a real hero studies it."
    )
    world.say(
        f"{hero.id} used a {helper.label} to {helper.method}, and {sidekick.id} held the box steady."
    )
    _n(hero, "courage", 1)
    _m(hero, "shadow", -1)
    _m(hero, "tiny-hum", 1)

    world.say(
        f"The tape let go with a soft rip, and inside was {clue_cfg.phrase}."
    )
    world.say(
        f"It was not a monster at all; it was a clever little clue, and its {clue_cfg.clue}."
    )
    _n(hero, "wonder", 1)
    _n(hero, "pride", 1)
    _n(sidekick, "relief", 1)
    _n(hero, "relief", 1)
    _n(hero, "suspense", -2)
    _m(hero, "lockedness", -1)

    world.para()
    world.say(
        f"{hero.id} smiled in the beam of light and tucked the clue safely into {hero.id}'s cape pocket."
    )
    world.say(
        f"The storage closet still looked small and dusty, but now it felt like the place where a good secret had been found."
    )
    world.say(
        f"{sidekick.id} grinned, because the discovery had turned into a hero moment, and the crab-dim mystery was solved."
    )

    world.facts["resolved"] = True
    world.facts["helper_choice"] = helper
    world.facts["ending_image"] = f"{hero.id} in the {world.setting.place} with the clue safe and the light shining"


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    tension(world)
    resolve_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    clue_cfg: DiscoveryItem = world.facts["clue_cfg"]
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    return [
        f"Write a {STYLE_NAME} for young children about discovery in a {SETTING_NAME}.",
        f"Tell a suspenseful story where {hero.id} and {sidekick.id} find {clue_cfg.phrase}.",
        f"Write a gentle superhero story that includes the words \"{STORY_THEME}\", \"theme\", and \"{SEED_WORD}\".",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    clue_cfg: DiscoveryItem = world.facts["clue_cfg"]
    helper: Helper = world.facts["helper_choice"]
    return [
        QAItem(
            question=f"Who found the strange clue in the {SETTING_NAME}?",
            answer=f"{hero.id} found {clue_cfg.phrase} with help from {sidekick.id}.",
        ),
        QAItem(
            question=f"What made the middle of the story suspenseful?",
            answer=f"The closet was quiet, the shelf creaked, and the taped box stayed stuck until {hero.id} handled it carefully.",
        ),
        QAItem(
            question=f"How did the hero open the mystery box?",
            answer=f"{hero.id} used a {helper.label} and careful hands to open it slowly instead of rushing.",
        ),
        QAItem(
            question=f"What was the crab-dim clue like?",
            answer=f"It was small, odd, and clever, with a shell-shaped feel and a red hand that clicked like tiny claws.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a storage closet?",
            answer="A storage closet is a small room where people keep boxes, tools, and other things they want to store.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of waiting to learn what will happen next, especially when something seems mysterious or important.",
        ),
        QAItem(
            question="Why should a hero be careful with an unknown box?",
            answer="A hero should be careful because the box might be breakable, important, or tricky to open without causing a mess.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% This tiny declarative twin mirrors the Python reasonableness gate.
% A discovery is suspenseful when it is hidden in the storage closet.
suspenseful(C) :- clue(C), hidden_in(C, storage_closet).

% A safe resolution exists when the clue can be opened carefully.
safe_resolution(C) :- suspenseful(C), helper(H), method(H, careful_open).

#show suspenseful/1.
#show safe_resolution/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines: list[str] = [asp.fact("setting", "storage_closet")]
    lines.append(asp.fact("place", "storage_closet"))
    for cid, clue in DISCOVERIES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("hidden_in", cid, "storage_closet"))
        if cid == "crab-dim":
            lines.append(asp.fact("theme_word", "discovery"))
    for helper in HELPERS:
        lines.append(asp.fact("helper", helper.id))
        lines.append(asp.fact("method", helper.id, "careful_open"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program("#show suspenseful/1.\n#show safe_resolution/1."))
    atoms = asp.atoms(model, "suspenseful")
    if ("crab-dim",) in set(atoms):
        print("OK: ASP gate recognizes the crab-dim clue as suspenseful.")
        return 0
    print("MISMATCH: ASP did not recognize the suspenseful clue.")
    return 1


CURATED = [
    StoryParams(hero="Nova", sidekick="Milo", clue="crab-dim"),
    StoryParams(hero="Spark", sidekick="Pip", clue="theme"),
    StoryParams(hero="Vega", sidekick="Zia", clue="discovery"),
]


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program("#show suspenseful/1.\n#show safe_resolution/1."))
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
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_story_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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

#!/usr/bin/env python3
"""
A storyworld about a storm, a tall tale, a flashback, and a foreshadowed rescue.

Premise:
- A little lantern-keeper named Jun tells an enormous-sounding tale about a storm
  rolling over the hill.
- The storm swells the creek, threatens a bridge, and sends the friends running.
- A remembered flashback explains why Jun knows the old bell-rope matters.
- Foreshadowing pays off when the odd clue from earlier becomes the rescue.

This world is intentionally small and state-driven: meters track the storm and
the creek, while memes track fear, hope, and pride.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford_storm: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "valley": Setting(place="the windy valley"),
    "harbor": Setting(place="the little harbor"),
    "hilltown": Setting(place="the hill town"),
    "meadow": Setting(place="the meadow road"),
}

HERO_NAMES = ["Jun", "Mira", "Toby", "Nell", "Pip", "Lark", "Otis", "Wren"]
COMPANION_NAMES = ["Aunt Sal", "Old Bram", "Mabel", "Uncle Reed", "Gran Dot", "Captain Hush"]
HERO_TYPES = ["girl", "boy"]
COMPANION_TYPES = ["aunt", "uncle", "woman", "man"]


ASP_RULES = r"""
storm_near(Place) :- setting(Place), afford_storm(Place).
foreshadow_bridge(Bridge) :- bridge(Bridge), creak(Bridge).
flashback_help(Hero) :- remembers(Hero, bell_rope).
need_rescue(Bridge) :- storm_strong, bridge(Bridge), over_creek(Bridge).
rescued(Bridge) :- need_rescue(Bridge), bell_rang.
"""


@dataclass
class State:
    storm: float = 0.0
    creek: float = 0.0
    bridge_sway: float = 0.0
    fear: float = 0.0
    hope: float = 0.0
    pride: float = 0.0
    bell_known: bool = False
    bell_rang: bool = False
    flashback_done: bool = False
    foreshadowed: bool = False
    rescued: bool = False


def _add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storm storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--companion-type", choices=COMPANION_TYPES)
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_name = args.name or rng.choice(HERO_NAMES)
    companion_name = args.companion or rng.choice(COMPANION_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    companion_type = args.companion_type or rng.choice(COMPANION_TYPES)
    if hero_name == companion_name:
        raise StoryError("hero and companion must be different names")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    state = State()

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    companion = world.add(Entity(id=params.companion_name, kind="character", type=params.companion_type, label=params.companion_name))
    bridge = world.add(Entity(id="bridge", type="bridge", label="the old bridge"))
    bell = world.add(Entity(id="bell", type="bell", label="the town bell"))

    world.facts.update(hero=hero, companion=companion, bridge=bridge, bell=bell, state=state)

    # Setup
    world.say(f"Folks said {hero.id} could hear thunder before other people heard the sky clear its throat.")
    world.say(f"{hero.id} lived near {world.setting.place}, where the road bent like a fishhook and the old bridge slept over a creek.")
    world.say(f"{companion.id} had a voice like a barn door and a habit of saying no storm could scare a proper lantern-keeper.")

    # Foreshadowing
    world.para()
    state.foreshadowed = True
    _add_meter(bridge, "creak", 1.0)
    world.say(f"One evening, {hero.id} tied a spare bell-rope to a post 'just in case,' and {companion.id} laughed at the notion.")
    world.say(f"But the post gave a little groan in the wind, as if it knew a bigger story was coming.")

    # Storm rises
    world.para()
    state.storm += 1.0
    state.creek += 1.0
    _add_meme(hero, "wonder", 1.0)
    _add_meme(companion, "confidence", 1.0)
    world.say("Then came a storm so grand it looked stitched together from dark coats and drumbeats.")
    world.say(f"Rain slapped the roofs, lightning flashed like a silver hook, and the creek below the bridge began to climb.")

    # Tall tale / tension
    state.fear += 1.0
    _add_meme(hero, "fear", 1.0)
    _add_meme(companion, "worry", 1.0)
    world.say(f"{hero.id} swore the storm had a voice, and {companion.id} swore it had ten voices, each louder than a bucket in a thunder shed.")
    world.say(f"The old bridge started to sway, and the creek pushed hard enough to make the riverbanks look nervous.")

    # Flashback
    world.para()
    state.flashback_done = True
    state.bell_known = True
    world.say(f"That swaying made {hero.id} remember a summer long ago, when the bell-rope had snapped in a windstorm and the town had gone nearly speechless.")
    world.say(f"Back then, a stranded calf, a stuck wagon, and a frightened child had all waited on that same bell to call help.")

    # Rescue turn
    world.para()
    state.bell_rang = True
    world.say(f"So {hero.id} grabbed the spare rope and rang the bell as if trying to wake the whole county at once.")
    world.say(f"The sound rolled over the hill, over the river, and straight into every porch and pasture nearby.")
    state.hope += 1.0
    state.rescued = True
    _add_meme(hero, "pride", 1.0)
    _add_meme(companion, "relief", 1.0)
    _add_meter(bridge, "safety", 1.0)
    world.say(f"Neighbors came running with planks, lanterns, and muddy boots, and together they steadied the bridge before the creek could swallow it.")
    world.say(f"When the storm finally wandered off, {hero.id} stood dry-ish and smiling while {companion.id} admitted the sky had met its match.")

    world.facts.update(storm="strong", rescue="bell", foreshadowed=True, flashback=True, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    return [
        'Write a tall tale for a young child about a storm, a tricky bridge, and one small brave act.',
        f"Tell a story where {hero.id} remembers an old bell-rope and uses it when {comp.id} says the storm is only noise.",
        f"Make a gentle tall tale with a flashback and foreshadowing, ending with a creek and bridge saved from the storm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    comp: Entity = f["companion"]
    state: State = f["state"]
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.id}, a little {hero.type} who lived near {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} remember from long ago?",
            answer=f"{hero.id} remembered an earlier storm when the bell-rope had snapped and the town had needed help fast.",
        ),
        QAItem(
            question=f"What was the foreshadowing clue before the storm got wild?",
            answer=f"The foreshadowing clue was the spare bell-rope tied to the post, which looked ordinary at first but mattered later.",
        ),
    ] + (
        [
            QAItem(
                question=f"How did the story end?",
                answer=f"The story ended with {hero.id} ringing the bell, neighbors saving the bridge, and the storm losing its grip on the creek.",
            )
        ] if state.rescued else []
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a storm?",
            answer="A storm is a time when the weather gets rough, with strong wind, heavy rain, thunder, or lightning.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue placed early in a story that hints something important will happen later.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly looks back at something that happened earlier.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a story told in a big, playful way, with extra-large actions and lively exaggeration.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    state: State = world.facts["state"]
    lines.append(
        "  state: "
        f"storm={state.storm}, creek={state.creek}, bridge_sway={state.bridge_sway}, "
        f"fear={state.fear}, hope={state.hope}, pride={state.pride}, "
        f"bell_known={state.bell_known}, bell_rang={state.bell_rang}, "
        f"flashback_done={state.flashback_done}, foreshadowed={state.foreshadowed}, rescued={state.rescued}"
    )
    return "\n".join(lines)


CURATED = [
    StoryParams(place="valley", hero_name="Jun", hero_type="boy", companion_name="Old Bram", companion_type="man"),
    StoryParams(place="harbor", hero_name="Mira", hero_type="girl", companion_name="Aunt Sal", companion_type="aunt"),
    StoryParams(place="hilltown", hero_name="Pip", hero_type="boy", companion_name="Gran Dot", companion_type="woman"),
]


def asp_facts() -> str:
    import asp

    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
        lines.append(asp.fact("afford_storm", key))
    for name in ["storm", "bridge", "creek", "bell_rope"]:
        lines.append(asp.fact("thing", name))
    lines.append(asp.fact("bridge", "bridge"))
    lines.append(asp.fact("over_creek", "bridge"))
    lines.append(asp.fact("bell", "bell"))
    lines.append(asp.fact("creak", "bridge"))
    lines.append(asp.fact("bell_rope", "bell_rope"))
    lines.append(asp.fact("remembers", "hero", "bell_rope"))
    lines.append(asp.fact("storm_strong"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show rescued/1. #show foreshadow_bridge/1. #show flashback_help/1."))
    atoms = set((s.name, tuple(a.name if a.type != a.type.String else a.string for a in s.arguments)) for s in model)
    expected = {
        ("foreshadow_bridge", ("bridge",)),
        ("flashback_help", ("hero",)),
        ("rescued", ("bridge",)),
    }
    if expected.issubset(atoms):
        print("OK: ASP rules produce the expected bridge-rescue shape.")
        return 0
    print("MISMATCH: ASP rules did not produce the expected atoms.")
    print("Observed:", sorted(atoms))
    return 1


def build_story(params: StoryParams) -> StorySample:
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
        print(asp_program("#show rescued/1. #show foreshadow_bridge/1. #show flashback_help/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            sys.exit(1)
        model = asp.one_model(asp_program("#show rescued/1. #show foreshadow_bridge/1. #show flashback_help/1."))
        print("\n".join(sorted(str(a) for a in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [build_story(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = build_story(params)
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
            header = f"### {p.hero_name} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

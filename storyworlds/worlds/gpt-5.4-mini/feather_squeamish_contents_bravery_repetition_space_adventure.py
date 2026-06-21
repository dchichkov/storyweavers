#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/feather_squeamish_contents_bravery_repetition_space_adventure.py
=================================================================================================

A standalone story world for a tiny Space Adventure tale built from the seed words
"feather", "squeamish", and "contents", with the narrative instruments of
Bravery and Repetition.

Premise:
- Two young space explorers are unpacking a supply crate on a moon outpost.
- One explorer is squeamish about a strange feather inside the crate contents.
- The other uses repeated brave steps and a calm helper tool to solve the problem.
- The ending shows that the crate is opened, the fear passes, and the explorers
  learn they can keep checking mysterious contents with courage.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes,
- state-driven prose,
- reasonableness gate with Python and inline ASP twin,
- three Q&A sets grounded in the simulated world,
- standard CLI flags: -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp.
"""

from __future__ import annotations

import argparse
import copy
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
BRAVERY_BASE = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    scene: str
    dark_space: str
    feels: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Creature:
    id: str
    label: str
    harmless: bool = True
    flutters: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Reaction:
    id: str
    sense: int
    courage: int
    text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["repetition"] < THRESHOLD:
            continue
        sig = ("repetition", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["calm"] += 1
        out.append("__repeat__")
    return out


CAUSAL_RULES = [Rule("repetition", "social", _r_repetition)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def reasonable(creature: Creature) -> bool:
    return creature.harmless and creature.flutters


def sensible_reactions() -> list[Reaction]:
    return [r for r in REACTIONS.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, c in CREATURES.items():
            if not reasonable(c):
                continue
            for rid in REACTIONS:
                if REACTIONS[rid].sense >= 2:
                    combos.append((sid, cid, rid))
    return combos


def bravery_check(squeamish: int, brave: int) -> bool:
    return brave > squeamish + 1


def outcome_of(params: "StoryParams") -> str:
    if bravery_check(params.squeamish_level, params.bravery_level):
        return "brave"
    return "hesitant"


def _do_open(world: World, creature: Creature, narrate: bool = True) -> None:
    creature.tags.add("seen")
    creature.harmless = creature.harmless
    propagate(world, narrate=narrate)


def repeat_opening(world: World, hero: Entity, crate: Entity, creature: Creature) -> None:
    world.say(
        f"{hero.id} and {crate.label_word} stood by the supply crate in the moon base, "
        f"where the air smelled metallic and the {crate.label_word} was packed with "
        f"mysterious contents."
    )


def describe_scene(world: World, setting: Setting, hero: Entity, companion: Entity) -> None:
    hero.memes["curiosity"] += 1
    companion.memes["curiosity"] += 1
    world.say(
        f"On a bright orbiting morning, {hero.id} and {companion.id} floated through "
        f"{setting.place}. {setting.scene}"
    )
    world.say(
        f"They peered at {setting.dark_space}, where the {setting.feels} made the shadows "
        f"look like they were drifting."
    )


def notice_feather(world: World, hero: Entity, companion: Entity, creature: Creature) -> None:
    world.say(
        f"Then {companion.id} spotted a {creature.label} tucked inside the crate, "
        f"and {companion.pronoun().capitalize()} felt squeamish right away."
    )
    companion.memes["squeamish"] += 1
    world.say(f'"A feather?" {companion.id} whispered. "Why is there a feather in there?"')


def brace_with_breaths(world: World, hero: Entity, companion: Entity) -> None:
    companion.memes["repetition"] += 1
    companion.memes["bravery"] += 1
    world.say(
        f"{hero.id} took one deep breath, then another, and said, "
        f'"One step at a time. One step at a time."'
    )
    world.say(
        f"{companion.id} copied the words, and the repeated whisper made the room feel "
        f"steadier."
    )


def open_contents(world: World, hero: Entity, crate: Entity, creature: Creature) -> None:
    _do_open(world, creature)
    crate.meters["opened"] += 1
    world.say(
        f"{hero.id} lifted the latch, and the crate opened with a soft click. Inside, "
        f"the contents were not scary at all -- just a folded survey kit, a snack pack, "
        f"and the feather from a test bird brought back for study."
    )


def calm_ending(world: World, hero: Entity, companion: Entity, setting: Setting) -> None:
    hero.memes["bravery"] += 1
    companion.memes["calm"] += 1
    world.say(
        f"{companion.id} leaned closer and saw that the feather was light as moon dust. "
        f"Nothing jumped, nothing bit, and nothing moved."
    )
    world.say(
        f"After that, they checked the rest of the contents together, one careful look "
        f"at a time, and the little base felt friendly again."
    )
    world.say(
        f"They floated away from {setting.dark_space} with the crate open, the feather "
        f"safe, and their courage bigger than before."
    )


def tell(setting: Setting, creature: Creature, reaction: Reaction,
         hero_name: str = "Nova", companion_name: str = "Pip",
         hero_gender: str = "girl", companion_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="companion"))
    crate = world.add(Entity(id="crate", type="thing", label="the crate"))
    hero.memes["bravery"] = BRAVERY_BASE
    companion.memes["squeamish"] = 4.0
    companion.memes["bravery"] = 3.0
    world.facts.update(setting=setting, creature=creature, reaction=reaction)

    describe_scene(world, setting, hero, companion)
    world.para()
    repeat_opening(world, hero, crate, creature)
    notice_feather(world, hero, companion, creature)
    world.para()
    brace_with_breaths(world, hero, companion)
    open_contents(world, hero, crate, creature)
    world.para()
    calm_ending(world, hero, companion, setting)

    world.facts.update(
        hero=hero,
        companion=companion,
        crate=crate,
        opened=crate.meters["opened"] >= THRESHOLD,
        brave=bravery_check(companion.memes["squeamish"], companion.memes["bravery"]),
        repeated=companion.memes["repetition"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moonbase": Setting(
        "moonbase",
        "the moon base",
        "The round windows showed a sky full of stars, and a tiny rover waited by the airlock.",
        "the cargo corner",
        "thin",
    ),
    "starship": Setting(
        "starship",
        "the starship corridor",
        "Blue panels hummed softly, and the floor lights blinked like little comets.",
        "the supply locker",
        "quiet",
    ),
    "orbital_lab": Setting(
        "orbital_lab",
        "the orbital lab",
        "Glass tubes glowed with gentle light, and the computers made small sleepy beeps.",
        "the sample shelf",
        "still",
    ),
}

CREATURES = {
    "feather": Creature("feather", "feather", harmless=True, flutters=True, tags={"feather"}),
    "plume": Creature("plume", "feather plume", harmless=True, flutters=True, tags={"feather"}),
    "down": Creature("down", "soft feather", harmless=True, flutters=True, tags={"feather"}),
}

REACTIONS = {
    "breath": Reaction("breath", 3, 3, "take three brave breaths", tags={"bravery"}),
    "count": Reaction("count", 2, 2, "count to five and try again", tags={"repetition"}),
    "ask": Reaction("ask", 2, 2, "ask for help and then try again", tags={"bravery", "repetition"}),
}

HERO_NAMES = ["Nova", "Mira", "Zia", "Luna", "Rae", "Ivy"]
COMPANION_NAMES = ["Pip", "Toby", "Finn", "Jax", "Bo", "Remy"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    creature: str
    reaction: str
    hero_name: str
    hero_gender: str
    companion_name: str
    companion_gender: str
    squeamish_level: int = 4
    bravery_level: int = 6
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with feather, squeamish, contents, bravery, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--reaction", choices=REACTIONS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANION_NAMES)
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
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
    if args.creature and not reasonable(CREATURES[args.creature]):
        raise StoryError("That creature is not a reasonable feather for this story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.creature is None or c[1] == args.creature)
              and (args.reaction is None or c[2] == args.reaction)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, creature, reaction = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero or rng.choice(HERO_NAMES)
    companion_name = args.companion or rng.choice([n for n in COMPANION_NAMES if n != hero_name])
    return StoryParams(
        setting, creature, reaction, hero_name, hero_gender, companion_name, companion_gender,
        squeamish_level=rng.randint(3, 6), bravery_level=rng.randint(5, 8)
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the words "feather", "squeamish", and "contents".',
        f"Tell a gentle moon-base story where {f['companion'].id} feels squeamish about a feather in a crate, but {f['hero'].id} uses bravery and repetition to keep going.",
        f"Write a small spaceship adventure about opening mysterious contents carefully, with a brave repeated phrase and a safe ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    setting = f["setting"]
    creature = f["creature"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {comp.id}, two little space explorers on {setting.place}. They are trying to open mysterious contents together."),
        ("Why did {0} feel squeamish?".format(comp.id),
         f"{comp.id} felt squeamish when {comp.id} saw the feather inside the crate. The strange little feather made the contents seem mysterious at first."),
        ("What helped them stay brave?",
         f"{hero.id} took repeated deep breaths and said the same brave words again and again. That repetition made the scary moment feel smaller."),
        ("What was inside the crate?",
         f"Inside the crate were harmless contents like a survey kit, a snack pack, and a feather for study. Once they opened it, nothing dangerous was hiding there."),
    ]
    if f.get("opened"):
        qa.append((
            "How did the story end?",
            f"It ended with the crate open and the explorers calm. The feather was safe, and they could keep checking the contents one careful look at a time."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a feather?",
         "A feather is a light part of a bird. It can float and drift through the air."),
        ("What does squeamish mean?",
         "Squeamish means feeling a little nervous or queasy about something odd, gross, or surprising."),
        ("What are contents?",
         "Contents are the things that are inside a box, bag, or container."),
        ("What is bravery?",
         "Bravery means doing something even though you feel scared or unsure."),
        ("What is repetition?",
         "Repetition means saying or doing something again and again."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moonbase", "feather", "breath", "Nova", "girl", "Pip", "boy"),
    StoryParams("starship", "plume", "count", "Mira", "girl", "Toby", "boy"),
    StoryParams("orbital_lab", "down", "ask", "Zia", "girl", "Jax", "boy"),
]


def explain_rejection(creature: Creature) -> str:
    return "(No story: this feather choice would not create a gentle enough space-adventure scene.)"


ASP_RULES = r"""
reasonable(C) :- creature(C), harmless(C), flutters(C).
brave(R) :- reaction(R), sense(R, S), S >= 2.
valid(S, C, R) :- setting(S), reasonable(C), brave(R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        if c.harmless:
            lines.append(asp.fact("harmless", cid))
        if c.flutters:
            lines.append(asp.fact("flutters", cid))
    for rid, r in REACTIONS.items():
        lines.append(asp.fact("reaction", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        import asp
    except Exception as err:
        print(f"ERROR: could not import asp helper: {err}")
        return 1
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    # Smoke test normal generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"ERROR: smoke test failed: {err}")
        return 1
    print("OK: generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CREATURES[params.creature],
        REACTIONS[params.reaction],
        params.hero_name,
        params.companion_name,
        params.hero_gender,
        params.companion_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
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
            header = f"### {p.hero_name} and {p.companion_name}: {p.setting}, {p.creature}, {p.reaction}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

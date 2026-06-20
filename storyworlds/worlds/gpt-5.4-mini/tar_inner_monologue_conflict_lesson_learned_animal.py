#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tar_inner_monologue_conflict_lesson_learned_animal.py
=====================================================================================

A small storyworld about an animal, a sticky tar patch, a conflict beat, an inner
monologue beat, and a lesson learned ending.

The world is intentionally tiny:
- a curious animal notices tar near a path or nest
- an internal thought pulls it toward the tar
- another animal warns or objects
- the animal gets stuck or nearly gets stuck
- a helper rescues or redirects
- the ending proves the lesson learned

The script follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports --n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
- produces state-driven prose and grounded QA
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"stuck": 0.0, "messed": 0.0, "helped": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "conflict": 0.0, "relief": 0.0,
                          "lesson": 0.0, "joy": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "mouse", "fox"}:
            base = {"subject": "it", "object": "it", "possessive": "its"}
            return base[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        return self.label or self.id



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
    detail: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class AnimalType:
    id: str
    name: str
    sound: str
    habitat: str
    size: str
    paw: str
    curious_line: str
    plural: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class TarPatch:
    id: str
    phrase: str
    near: str
    sticky: str
    danger: str
    traps: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    animal: str
    helper: str
    tar: str
    response: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


SETTINGS = {
    "riverbank": Setting("riverbank", "the riverbank", "The water shone nearby, and reeds nodded in the breeze."),
    "forest": Setting("forest", "the forest trail", "Tall trees made a cool tunnel of shade."),
    "farm": Setting("farm", "the barnyard path", "Hay bales sat nearby, and the animals knew every corner."),
}

ANIMALS = {
    "raccoon": AnimalType("raccoon", "raccoon", "chitter", "the forest", "small", "paws",
                          "This looks interesting.", "raccoons"),
    "fox": AnimalType("fox", "fox", "yip", "the woods", "small", "paws",
                      "Maybe I can learn something.", "foxes"),
    "bear": AnimalType("bear", "bear", "gruff hum", "the woods", "big", "paws",
                       "I should know what this is.", "bears"),
    "rabbit": AnimalType("rabbit", "rabbit", "thump", "the meadow", "small", "paws",
                         "I wonder what that is.", "rabbits"),
}

HELPERS = {
    "bird": "a bluebird",
    "deer": "a deer",
    "beaver": "a beaver",
    "squirrel": "a squirrel",
}

TAR_PATCHES = {
    "road_tar": TarPatch("road_tar", "a black tar patch", "beside the path", "sticky and shiny", "it could trap paws and fur"),
    "tree_tar": TarPatch("tree_tar", "tar on a fallen log", "near the log", "dark and gooey", "it could glue fur to the wood"),
    "nest_tar": TarPatch("nest_tar", "a tar spill near a nest", "by the nest", "thick and slick", "it could ruin feathers and feet"),
}

RESPONSES = {
    "pull_free": Response("pull_free", 4, 4,
                          "pulled the {tar} free with careful paws and rolled the sticky mess into leaves",
                          "tried to pull the {tar} free, but the tar held on too tightly",
                          "pulled the {tar} free with careful paws"),
    "sand_cover": Response("sand_cover", 3, 3,
                           "covered the {tar} with sand and bark until it stopped sticking",
                           "threw sand on the {tar}, but the tar was still too grabby",
                           "covered the {tar} so it would not stick anymore"),
    "call_help": Response("call_help", 5, 5,
                          "called for help, and together they used sticks and cloth to move the {tar} away",
                          "called for help, but the tar had already trapped the paw too hard",
                          "called for help and moved the {tar} away"),
}

CURIOUS_LINES = [
    "Maybe it was treasure.",
    "Maybe it was mud from a strange storm.",
    "Maybe it held a secret smell.",
    "Maybe it was something no one wanted, but everyone should understand.",
]

NAMES = ["Milo", "Pip", "Nia", "Tavi", "Luna", "Kiko", "Remy", "Hazel", "Ollie", "Mara"]


def reasonableness_ok(animal: AnimalType, tar: TarPatch, response: Response) -> bool:
    return tar.traps and response.sense >= 3 and animal.id in ANIMALS and tar.id in TAR_PATCHES


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ANIMALS:
            for t in TAR_PATCHES:
                if TAR_PATCHES[t].traps:
                    combos.append((s, a, t))
    return combos


ASP_RULES = r"""
traps(tar_patch).
valid(S,A,T) :- setting(S), animal(A), tar(T), traps(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for tid in TAR_PATCHES:
        lines.append(asp.fact("tar", tid))
        lines.append(asp.fact("traps", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about tar, conflict, and lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--tar", choices=TAR_PATCHES)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.response and RESPONSES[args.response].sense < 3:
        raise StoryError("The chosen response is too weak for this tar story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.animal is None or c[1] == args.animal)
              and (args.tar is None or c[2] == args.tar)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, animal, tar = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(setting, animal, helper, tar, response)


def _speak_inner(world: World, hero: Entity, tar: TarPatch) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} slowed down when {hero.title} saw {tar.phrase}. "
        f'Inside, {hero.pronoun()} thought, "{CURIOUS_LINES[0]}"'
    )
    world.say(
        f'But another thought answered back: "{tar.danger}. Better not touch it."'
    )


def _conflict(world: World, hero: Entity, helper: Entity, tar: TarPatch) -> None:
    hero.memes["conflict"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"{helper.id} spoke up right away. \"Don't step closer,\" {helper.pronoun()} said. "
        f"\"{tar.danger.capitalize()}.\""
    )
    world.say(
        f"{hero.id} wanted to ignore the warning, but {hero.pronoun()} felt the sticky pull of the shiny black patch."
    )


def _fall_or_stick(world: World, hero: Entity, tar: TarPatch) -> None:
    hero.meters["stuck"] += 1
    hero.meters["messed"] += 1
    world.say(
        f"{hero.id} reached out anyway, and one paw sank into {tar.phrase}. "
        f"The tar grabbed fast, clingy as glue."
    )


def _helper_action(world: World, helper: Entity, response: Response, tar: TarPatch) -> None:
    body = response.text.replace("{tar}", tar.phrase)
    helper.meters["helped"] += 1
    world.say(f"{helper.id} came closer and {body}.")
    world.say(
        f"The sticky patch lost its grip, and {helper.id} kept {helper.pronoun('possessive')} own feet on dry ground."
    )


def _lesson(world: World, hero: Entity, helper: Entity, tar: TarPatch) -> None:
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    hero.memes["joy"] += 1
    world.say("For a moment, both animals were quiet.")
    world.say(
        f"Then {hero.id} nodded. \"I thought it might be fun,\" {hero.pronoun()} said, "
        f"\"but tar only looks shiny. It can trap paws and fur.\""
    )
    world.say(
        f"{helper.id} nudged {hero.id} gently. \"Now you know,\" {helper.pronoun()} said, "
        f"\"and next time you can stop before the sticky part.\""
    )
    world.say(
        f"So {hero.id} kept away from {tar.phrase}, and the path looked safe again."
    )


def tell(setting: Setting, animal: AnimalType, helper_name: str, tar: TarPatch, response: Response) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=animal.id, label="the animal"))
    hero.id = random.choice(NAMES)
    helper = world.add(Entity(id=helper_name, kind="character", type="helper", label=HELPERS[helper_name]))
    helper.type = "bird" if helper_name == "bird" else "deer"
    tar_ent = world.add(Entity(id="tar", kind="thing", type="tar", label=tar.phrase))
    world.facts["tar"] = tar
    world.facts["response"] = response
    world.facts["animal"] = animal
    world.facts["helper"] = helper
    world.facts["hero"] = hero

    world.say(
        f"On a quiet day, {hero.id} wandered along {setting.place}. {setting.detail} "
        f"{hero.id} was a {animal.name} who liked to listen, look, and learn."
    )
    world.say(
        f"{hero.id} heard {animal.sound}s in {animal.habitat} and spotted {tar.phrase} near the trail."
    )
    _speak_inner(world, hero, tar)
    world.para()
    _conflict(world, hero, helper, tar)
    _fall_or_stick(world, hero, tar)
    world.para()
    _helper_action(world, helper, response, tar)
    _lesson(world, hero, helper, tar)
    world.facts["stuck"] = hero.meters["stuck"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    tar = f["tar"]
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the word "tar" and a clear lesson learned.',
        f"Tell a story where {hero.id} notices {tar.phrase}, has an inner thought about it, gets into a conflict, and learns to be careful.",
        f"Write a gentle animal story about sticky tar, a warning from a friend, and a lesson learned ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    tar = f["tar"]
    ans1 = (
        f"{hero.id} was the animal at the center of the story, and {helper.id} helped when the tar became a problem. "
        f"The scene started with curiosity and ended with a lesson learned."
    )
    ans2 = (
        f"{hero.id} wanted to touch {tar.phrase}, but {helper.id} warned {hero.id} that it could trap paws and fur. "
        f"That warning created the conflict before the rescue."
    )
    ans3 = (
        f"{hero.id} learned that tar is sticky and can trap animals if they step on it. "
        f"After that, {hero.id} stayed away from the tar and chose the safer path."
    )
    return [
        QAItem("Who is the story about?", ans1),
        QAItem("Why was there a conflict?", ans2),
        QAItem("What lesson did the animal learn?", ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is tar?", "Tar is thick, black, sticky stuff. It can glue things together and make a mess."),
        QAItem("Why should animals stay away from tar?", "Tar can trap paws, fur, or feathers, and that can hurt or slow an animal down."),
        QAItem("What should you do when something looks sticky and unsafe?", "Stop, look from far away, and call for help instead of touching it."),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ANIMALS[params.animal], params.helper, TAR_PATCHES[params.tar], RESPONSES[params.response])
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
    StoryParams("forest", "raccoon", "bird", "road_tar", "pull_free"),
    StoryParams("riverbank", "fox", "deer", "tree_tar", "sand_cover"),
    StoryParams("farm", "rabbit", "squirrel", "nest_tar", "call_help"),
]


def asp_verify() -> int:
    rc = 0
    p = set(valid_combos())
    c = set(asp_valid_combos())
    if p == c:
        print(f"OK: gate matches valid_combos() ({len(p)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if p - c:
            print("  only in python:", sorted(p - c))
        if c - p:
            print("  only in clingo:", sorted(c - p))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, animal=None, helper=None, tar=None, response=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos[:50]:
            print(" ", *c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, s in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Standalone storyworld: a tiny detective story about an insistently guarded tofu,
with humor, a mystery to solve, and a surprise ending.

The world model tracks:
- physical meters: hidden, moved, smelled, cracked, tasted, found
- emotional memes: curiosity, insistence, confusion, relief, amusement, surprise

A short seed tale for this world:
---
Mina loved helping in the kitchen, especially when her dad made tofu stir-fry.
One afternoon, a block of tofu vanished from the counter. Mina insisted she had
seen it a moment ago. Her dad became a tiny detective and looked under towels,
behind jars, and inside the fridge. At last they found the tofu hiding in the
dog's toy basket, and the surprise was that the dog had not stolen it at all:
the cat had pushed it there while chasing a spoon. Everyone laughed, and dinner
still turned out fine.

The script generates variations by swapping names, roles, locations, clues,
hiding places, and the surprising culprit -- while keeping the story grounded in
the simulated state changes.
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
# World data
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    movable: bool = True
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affordances: set[str] = field(default_factory=set)


@dataclass
class Scene:
    id: str
    clue: str
    search_spots: list[str]
    mess: str
    surprise: str
    culprit: str
    culprit_reason: str
    ending_image: str


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

    def entities_by_type(self, kind: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == kind]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting("the kitchen", True, {"search", "cook", "hide"}),
    "pantry": Setting("the pantry", True, {"search", "hide"}),
    "market": Setting("the little market", True, {"search", "hide"}),
}

SCENES = {
    "missing_tofu": Scene(
        id="missing_tofu",
        clue="a tofu block missing from the counter",
        search_spots=["under a towel", behind_jars := "behind the jars", "inside the fridge", "near the sink"],
        mess="crumbled",
        surprise="the cat had pushed the tofu into the toy basket",
        culprit="cat",
        culprit_reason="a spoon clink had startled it during a chase",
        ending_image="the tofu sat safely on a plate while everyone laughed",
    ),
    "mystery_smell": Scene(
        id="mystery_smell",
        clue="a funny smell drifting from the counter",
        search_spots=["beside the cutting board", "under the cookbook", "near the window", "in the cupboard"],
        mess="smelled",
        surprise="the scent came from toasted sesame oil, not spoiled tofu",
        culprit="dad",
        culprit_reason="he had secretly started dinner early",
        ending_image="the kitchen smelled warm and happy instead of strange",
    ),
    "tofu_riddle": Scene(
        id="tofu_riddle",
        clue="a wrapped tofu package with a torn corner",
        search_spots=["in the fridge drawer", "under a shopping bag", "behind the milk", "on the high shelf"],
        mess="moved",
        surprise="the tofu had been moved into a lunchbox by mistake",
        culprit="big sister",
        culprit_reason="she thought it was her leftover cake box in the rush",
        ending_image="the lunchbox and tofu sat side by side, both found",
    ),
}

NAMES = {
    "girl": ["Mina", "Luna", "Nora", "Pippa", "Tess", "Ivy"],
    "boy": ["Owen", "Theo", "Finn", "Milo", "Ben", "Ari"],
}
TRAITS = ["curious", "brave", "clever", "playful", "patient", "quick-eyed"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A tofu mystery is valid when there is a clue, a search path, and a surprise reveal.
valid_story(S) :- scene(S), clue(S,_), search_spot(S,_), surprise(S,_).

% The surprise is reasonable only if the culprit is not the first guessed suspect.
has_twist(S) :- surprise(S,_), culprit(S,C), suspect(S,X), X != C.

% Humor is supported by a harmless clue and an unthreatening culprit.
funny(S) :- scene(S), harmless(S), culprit(S,_).

% Solve requires at least one reveal after searching.
solved(S) :- valid_story(S), search_spot(S,_), surprise(S,_).
#show valid_story/1.
#show has_twist/1.
#show funny/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, sc in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("clue", sid, sc.clue))
        lines.append(asp.fact("surprise", sid, sc.surprise))
        lines.append(asp.fact("culprit", sid, sc.culprit))
        lines.append(asp.fact("harmless", sid))
        for spot in sc.search_spots:
            lines.append(asp.fact("search_spot", sid, spot))
        for suspect in {"cat", "dog", "dad", "big sister", "neighbor"}:
            lines.append(asp.fact("suspect", sid, suspect))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_models() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1.\n#show has_twist/1.\n#show funny/1.\n#show solved/1."))
    return sorted({(s.name, tuple(a.number if a.type.name == "Number" else a.string if a.type.name == "String" else a.name for a in s.arguments)) for s in model})


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1.\n#show has_twist/1.\n#show funny/1.\n#show solved/1."))
    shown = {s.name for s in model}
    expected = {"valid_story", "has_twist", "funny", "solved"}
    if shown == expected:
        print("OK: ASP rules produce the expected story predicates.")
        return 0
    print(f"Mismatch: {sorted(shown)} != {sorted(expected)}")
    return 1


# ---------------------------------------------------------------------------
# Storyworld core model
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    scene: str
    hero_name: str
    hero_gender: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style tofu mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["father", "mother", "dad", "mom", "grandparent", "sibling"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    scene = args.scene or rng.choice(list(SCENES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(["father", "mother"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, scene=scene, hero_name=name, hero_gender=gender, helper_type=helper, trait=trait)


def _speak(world: World, line: str) -> None:
    world.say(line)


def generate_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    scene = SCENES[params.scene]
    world = World(setting)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name, owner=None))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_type))
    tofu = world.add(Entity(id="tofu", kind="thing", type="tofu", label="tofu", phrase="a small white block of tofu", owner="helper", location="counter"))
    cat = world.add(Entity(id="cat", kind="character", type="cat", label="the cat"))
    dog = world.add(Entity(id="dog", kind="character", type="dog", label="the dog"))

    hero.memes["curiosity"] = 1
    hero.memes["insistence"] = 1
    helper.memes["amusement"] = 0.5

    # Act 1: setup
    _speak(world, f"{params.hero_name} was a {params.trait} little {params.hero_gender} who loved detective games.")
    _speak(world, f"One afternoon, {params.hero_name} and {helper.label} were getting ready to cook with tofu.")
    _speak(world, f"Then something strange happened: {scene.clue}.")
    tofu.meters["hidden"] = 1
    tofu.location = "missing"

    world.para()

    # Act 2: search and insist
    _speak(world, f'"The tofu was right here," {params.hero_name} said, and {hero.pronoun("subject")} insisted on looking again.')
    hero.memes["insistence"] += 1
    hero.memes["curiosity"] += 1

    searched = []
    for spot in scene.search_spots[:3]:
        searched.append(spot)
        _speak(world, f"{params.hero_name} checked {spot}, but found nothing useful.")
    helper.memes["confusion"] = 1
    _speak(world, f"{helper.label} frowned and became a tiny detective too.")

    world.para()

    # Act 3: reveal and surprise
    tofu.meters["found"] = 1
    tofu.location = "toy basket" if scene.id == "missing_tofu" else ("lunchbox" if scene.id == "tofu_riddle" else "plate")
    if scene.id == "missing_tofu":
        cat.memes["guilty"] = 0
        dog.memes["confused"] = 1
        world.facts["suspect"] = "dog"
        world.facts["culprit"] = "cat"
        world.facts["surprise"] = scene.surprise
        _speak(world, "At last they peeked in the dog's toy basket and gasped.")
        _speak(world, f"The surprise was that {scene.surprise}.")
        _speak(world, f'The cat blinked innocently, as if to say, "{scene.culprit_reason}."')
        helper.memes["relief"] = 1
        helper.memes["amusement"] = 1
        hero.memes["surprise"] = 1
        _speak(world, f"{params.hero_name} laughed so hard {hero.pronoun('possessive')} shoulders shook.")
        _speak(world, scene.ending_image.capitalize() + ".")
    elif scene.id == "mystery_smell":
        world.facts["suspect"] = "neighbor"
        world.facts["culprit"] = "dad"
        world.facts["surprise"] = scene.surprise
        _speak(world, f"They followed the smell and learned that {scene.surprise}.")
        _speak(world, f"{helper.label} chuckled, because {scene.culprit_reason}.")
        helper.memes["relief"] = 1
        hero.memes["surprise"] = 1
        _speak(world, scene.ending_image.capitalize() + ".")
    else:
        world.facts["suspect"] = "dog"
        world.facts["culprit"] = "big sister"
        world.facts["surprise"] = scene.surprise
        _speak(world, f"After one more careful look, they discovered that {scene.surprise}.")
        _speak(world, f"{helper.label} laughed at the mix-up, because {scene.culprit_reason}.")
        hero.memes["surprise"] = 1
        helper.memes["relief"] = 1
        _speak(world, scene.ending_image.capitalize() + ".")

    world.facts.update(hero=hero, helper=helper, tofu=tofu, scene=scene, searched=searched)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    scene = f["scene"]
    return [
        f'Write a short detective story for a child where {hero.label} insists on solving a tofu mystery.',
        f'Write a funny mystery story that includes the word "tofu" and ends with a surprise reveal.',
        f"Tell a gentle detective story set in {world.setting.place} where someone searches for {scene.clue}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    scene = f["scene"]
    tofu = f["tofu"]
    qa = [
        QAItem(
            question=f"Why did {hero.label} keep insisting on looking again?",
            answer=f"{hero.label} was sure the tofu had been there a moment ago, so {hero.pronoun('subject')} kept looking like a little detective.",
        ),
        QAItem(
            question=f"Where did they first search for the missing tofu?",
            answer=f"They checked {scene.search_spots[0]} first, then kept searching when they still could not find it.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that {scene.surprise}. That made the mystery funny instead of scary.",
        ),
        QAItem(
            question=f"How did {helper.label} feel when the tofu was finally found?",
            answer=f"{helper.label} felt relieved and amused, because the missing tofu case was solved at last.",
        ),
    ]
    if tofu.location:
        qa.append(QAItem(
            question="Where was the tofu at the end?",
            answer=f"At the end, the tofu was in the {tofu.location}.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tofu?",
            answer="Tofu is a soft food made from soybeans. It can be cooked in many ways and soaks up flavor well.",
        ),
        QAItem(
            question="What does it mean to insist?",
            answer="To insist means to keep saying something is true or important because you really believe it.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something strange or hidden that people try to figure out by looking for clues.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(setting, scene, "tofu") for setting in SETTINGS for scene in SCENES]


def resolve_scene_error(args: argparse.Namespace) -> Optional[str]:
    if args.scene == "missing_tofu" and args.setting == "market":
        return None
    return None


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1.\n#show has_twist/1.\n#show funny/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1.\n#show has_twist/1.\n#show funny/1.\n#show solved/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("kitchen", "missing_tofu", "Mina", "girl", "father", "curious"),
            StoryParams("pantry", "mystery_smell", "Owen", "boy", "mother", "clever"),
            StoryParams("kitchen", "tofu_riddle", "Luna", "girl", "father", "patient"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

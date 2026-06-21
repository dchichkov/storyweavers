#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tile_curiosity_repetition_ghost_story.py
=======================================================================

A standalone storyworld for a small ghost-story domain built from the seed
words and style cues: tile, curiosity, repetition, and a child-friendly spooky
tone.

Premise:
- A child hears a strange tapping from a tiled room after dark.
- Curiosity pulls them closer, but repetition makes the pattern feel purposeful.
- A helpful adult or older sibling discovers a small, non-scary cause behind the
  "ghostly" sound and changes the room so it feels safe again.

The story is simulated from world state: the repeated sound, the child's mood,
the investigation, the reveal, and the ending image all come from the model.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from collections import defaultdict
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Room:
    id: str
    label: str
    tiles: str
    lights: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
    room: str
    sound: str
    source: str
    reveal: str
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


@dataclass
class StoryRecipe:
    id: str
    room: str
    tiles: str
    lights: str
    source: str
    sound: str
    reveal: str
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
    def __init__(self, recipe: StoryRecipe) -> None:
        self.recipe = recipe
        self.entities: dict[str, Entity] = {}
        self.room = Room("room", recipe.room, recipe.tiles, recipe.lights)
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
        clone = World(self.recipe)
        clone.entities = copy.deepcopy(self.entities)
        clone.room = copy.deepcopy(self.room)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["listening"] < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.room.meters["tension"] += 1
    child.memes["curiosity"] += 1
    out.append("__repeat__")
    return out


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if world.room.meters["tension"] < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["unease"] += 1
    world.room.meters["quiet"] += 1
    out.append("__spook__")
    return out


CAUSAL_RULES = [_r_repeat, _r_spook]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            res = rule(world)
            if res:
                changed = True
                produced.extend(x for x in res if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _hear(world: World, child: Entity) -> None:
    child.meters["listening"] += 1
    child.memes["curiosity"] += 1
    world.room.meters["heard"] += 1
    world.say(
        f"At the edge of the dark hall, {child.id} heard a tiny tap-tap-tap from "
        f"the tiled room. Then it came again: tap-tap-tap, as if someone was "
        f"knocking from inside the walls."
    )


def _closer(world: World, child: Entity, helper: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} frowned and listened harder. Tap-tap-tap. Tap-tap-tap. "
        f"Each little pattern made {child.pronoun('possessive')} curiosity grow, "
        f"so {child.id} crept closer while {helper.id} watched the doorway."
    )


def _warn(world: World, helper: Entity, child: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f'"{child.id}," {helper.id} said softly, "it might only sound haunted, '
        f'but let us look together."'
    )
    world.say(
        f"{helper.id} held up a lamp and the blue tiles shone like moonlight."
    )


def _discover(world: World, helper: Entity, child: Entity, recipe: StoryRecipe) -> None:
    child.meters["investigating"] += 1
    world.room.meters["looked"] += 1
    world.say(
        f'They listened one more time. Tap-tap-tap. Then {helper.id} knelt down and '
        f'found the {recipe.source} making the sound against the tile: '
        f'{recipe.reveal}.'
    )
    world.say(
        f'It was not a ghost at all, just the {recipe.source} and the hollow tile '
        f'answering one another in the dark.'
    )


def _fix(world: World, helper: Entity, child: Entity, recipe: StoryRecipe) -> None:
    child.memes["unease"] = 0.0
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.room.meters["tension"] = 0.0
    world.say(
        f"{helper.id} moved the {recipe.source} away from the wall and slid a "
        f"small mat over the cold tile. The room became quiet at once."
    )
    world.say(
        f"{child.id} smiled as the tapping stopped. The same tiles that had seemed "
        f"spooky now looked plain and safe in the lamp glow."
    )


def _ending(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"After that, {child.id} was still curious, but {child.pronoun()} knew "
        f"the brave thing was to look closely, listen twice, and call for help."
    )
    world.say(
        f"That night, the tiled room was only a tiled room, and the last sound was "
        f"{child.id} and {helper.id} walking away together in quiet, happy steps."
    )


RECIPE_REGISTRY = {
    "bathroom": StoryRecipe(
        "bathroom",
        "a small bathroom",
        "white tiles",
        "a night-light",
        "a loose bath toy",
        "tap-tap-tap",
        "the bath toy had rolled under the sink and bumped the tile each time the pipes shifted",
        {"tile", "ghost", "curiosity", "repetition"},
    ),
    "laundry": StoryRecipe(
        "laundry",
        "a laundry room",
        "blue tiles",
        "a single bulb",
        "a metal spoon",
        "tap-tap-tap",
        "the spoon in the pocket of a coat kept tapping the machine whenever it spun",
        {"tile", "ghost", "curiosity", "repetition"},
    ),
    "kitchen": StoryRecipe(
        "kitchen",
        "a quiet kitchen",
        "square tiles",
        "a lamp by the sink",
        "a sliding bowl",
        "tap-tap-tap",
        "the bowl kept sliding a little and knocking the baseboard and tile together",
        {"tile", "ghost", "curiosity", "repetition"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Finn", "Noah"]
HELPER_NAMES = ["Mom", "Dad", "Aunt June", "Big Sam", "Grandma", "Mr. Lee"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(rid, "tile", "ghost_story") for rid in RECIPE_REGISTRY]


def reasonableness_check(recipe: StoryRecipe) -> None:
    if "tile" not in recipe.tags:
        raise StoryError("This ghost story needs tile so the tapping can feel cold and echoing.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story style tale with curiosity, repetition, and a tiled room."
    )
    ap.add_argument("--room", choices=RECIPE_REGISTRY)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--helper-role", choices=["mother", "father", "aunt", "uncle", "grandma", "grandpa", "older sibling"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for rid, recipe in RECIPE_REGISTRY.items():
        lines.append(asp.fact("roomtype", rid))
        lines.append(asp.fact("has_tile", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R) :- roomtype(R), has_tile(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == {("bathroom",), ("laundry",), ("kitchen",)}
    if not ok:
        print("MISMATCH: ASP and Python valid-combos disagree.")
        return 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: generate() produced empty story.")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(list(RECIPE_REGISTRY))
    recipe = RECIPE_REGISTRY[room]
    reasonableness_check(recipe)
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    child_name = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    helper_role = args.helper_role or rng.choice(["mother", "father", "older sibling", "grandma"])
    return StoryParams(child_name, child_gender, helper_name, helper_gender, helper_role, room, recipe.sound, recipe.source, recipe.reveal)


def tell(params: StoryParams) -> World:
    recipe = RECIPE_REGISTRY[params.room]
    world = World(recipe)
    child = world.add(Entity("child", kind="character", type=params.child_gender, role="curious"))
    helper = world.add(Entity("helper", kind="character", type=params.helper_gender, role=params.helper_role))
    world.say(
        f"One evening, {params.child_name} wandered into {recipe.room} because the house had gone very still."
    )
    world.say(
        f"The walls were lined with {recipe.tiles}, and the light from {recipe.lights} made the room look silver."
    )
    _hear(world, child)
    world.para()
    _closer(world, child, helper)
    _warn(world, helper, child)
    propagate(world, narrate=False)
    world.para()
    _discover(world, helper, child, recipe)
    _fix(world, helper, child, recipe)
    world.para()
    _ending(world, child, helper)
    world.facts.update(child=child, helper=helper, recipe=recipe)
    return world


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    h = world.facts["helper"]
    r = world.facts["recipe"]
    return [
        QAItem("What did the child hear?", f"{c.id} heard a repeated tap-tap-tap from the tiled room, and it sounded ghostly in the dark. The repetition made the sound seem like a message."),
        QAItem("What was the spooky sound really?", f"It was really {r.reveal}. The sound was only the ordinary {r.source} bumping and answering the tile."),
        QAItem("How did the story end?", f"The helper moved the noisy thing away and covered the tile with a mat, so the tapping stopped. After that, the room felt quiet and safe."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("Why do tiles make a room feel spooky?", "Tiles can feel spooky because they are hard, cool, and shiny, so sounds echo and the room seems empty."),
        QAItem("What is repetition in a story?", "Repetition means something happens again and again. In a ghost story, repeated sounds can make the scene feel eerie."),
        QAItem("Why is curiosity important here?", "Curiosity makes the child want to learn what is making the sound. That careful looking leads to the real answer instead of a scary guess."),
    ]


def generation_prompts(world: World) -> list[str]:
    r = world.facts["recipe"]
    return [
        f'Write a child-friendly ghost story that uses the word "tile" and the repeated sound "{r.sound}".',
        f"Tell a spooky-but-safe story about a curious child in {r.room} who keeps hearing the same tap again and again.",
        "Write a story where curiosity solves a ghostly mystery and repetition makes the sound feel haunted before the truth is found.",
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
    parts.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} role={e.role}")
    lines.append(f"  room: meters={dict(world.room.meters)} memes={dict(world.room.memes)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams("Mia", "girl", "Mom", "girl", "mother", "bathroom", "tap-tap-tap", "a loose bath toy", "the bath toy had rolled under the sink and bumped the tile each time the pipes shifted"),
    StoryParams("Leo", "boy", "Dad", "boy", "father", "laundry", "tap-tap-tap", "a metal spoon", "the spoon in the pocket of a coat kept tapping the machine whenever it spun"),
    StoryParams("Nora", "girl", "Grandma", "girl", "grandma", "kitchen", "tap-tap-tap", "a sliding bowl", "the bowl kept sliding a little and knocking the baseboard and tile together"),
]


def resolve_story_recipe(args: argparse.Namespace, rng: random.Random) -> StoryRecipe:
    room = args.room or rng.choice(list(RECIPE_REGISTRY))
    return RECIPE_REGISTRY[room]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid rooms:", ", ".join(r[0] for r in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

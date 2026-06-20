#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/belch_rush_mystery_to_solve_surprise_animal.py
===============================================================================

A standalone storyworld about animal friends, a little mystery to solve, and a
surprise ending. The seed words are **belch** and **rush**; the domain keeps a
child-facing animal-story feel, with a small simulated state that drives the
prose.

The core premise:
- An animal makes a loud belch and rushes into a scene.
- Something small and puzzling is missing or out of place.
- The friends investigate clues rather than simply swapping nouns in a fixed
  paragraph.
- A surprise reveals what really happened and leaves the world changed.

This file follows the shared Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate plus an inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "hidden": 0.0, "found": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"curious": 0.0, "worry": 0.0, "joy": 0.0, "surprise": 0.0}

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
class Setting:
    id: str
    place: str
    hiding_spots: list[str]
    clue_spots: list[str]

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
class Animal:
    id: str
    sound: str
    move: str
    snack: str
    surprise: str
    hiding: str
    clue: str
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    if world.get("snack").meters["hidden"] >= THRESHOLD and ("mess", "snack") not in world.fired:
        world.fired.add(("mess", "snack"))
        world.get("snack").meters["mess"] += 1
        world.get("snack").memes["worry"] += 1
        out.append("__mess__")
    return out


def _r_found(world: World) -> list[str]:
    out: list[str] = []
    if world.get("snack").meters["hidden"] < THRESHOLD:
        return out
    if world.get("snack").meters["found"] >= THRESHOLD:
        return out
    if ("found", "snack") in world.fired:
        return out
    world.fired.add(("found", "snack"))
    world.get("snack").meters["found"] += 1
    world.get("searcher").memes["curious"] += 1
    out.append("__found__")
    return out


def _r_joy(world: World) -> list[str]:
    out: list[str] = []
    if world.get("snack").meters["found"] >= THRESHOLD and ("joy", "snack") not in world.fired:
        world.fired.add(("joy", "snack"))
        world.get("snack").meters["tidy"] += 1
        world.get("searcher").memes["joy"] += 1
        world.get("companion").memes["joy"] += 1
        out.append("__joy__")
    return out


CAUSAL_RULES = [Rule("mess", "physical", _r_mess), Rule("found", "physical", _r_found), Rule("joy", "social", _r_joy)]


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


def predict_search(world: World) -> dict:
    sim = world.copy()
    sim.get("snack").meters["hidden"] += 1
    propagate(sim, narrate=False)
    return {"found": sim.get("snack").meters["found"] >= THRESHOLD, "mess": sim.get("snack").meters["mess"]}


def valid_combo(setting: Setting, animal: Animal) -> bool:
    return bool(setting.hiding_spots and setting.clue_spots and animal.hiding in setting.hiding_spots and animal.clue in setting.clue_spots)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, animal in ANIMALS.items():
            if valid_combo(setting, animal):
                combos.append((sid, aid))
    return combos


def reasonableness_ok(setting: Setting, animal: Animal, surprise: str) -> bool:
    return valid_combo(setting, animal) and surprise in {"hat", "balloon", "shell", "blanket"}


def _do_hide(world: World) -> None:
    world.get("snack").meters["hidden"] += 1
    propagate(world, narrate=False)


def tell(setting: Setting, animal: Animal, surprise: str, hero_name: str, companion_name: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", role="searcher"))
    companion = world.add(Entity(id=companion_name, kind="character", type="boy", role="companion"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    snack = world.add(Entity(id="snack", label=animal.snack))
    animal_ent = world.add(Entity(id="animal", label=animal.id, kind="character", type="thing", role="animal"))
    world.facts["animal"] = animal
    world.facts["setting"] = setting
    world.facts["surprise"] = surprise

    hero.memes["curious"] = 1.0
    companion.memes["curious"] = 1.0

    world.say(
        f"On a bright morning at {setting.place}, {hero.id} and {companion.id} were playing with {animal.id}."
    )
    world.say(
        f"Then {animal.id} gave a huge {animal.sound} and rushed across the room so fast that everyone blinked."
    )
    world.say(
        f"A moment later, the little {animal.snack} was missing, and {hero.id} wondered where it could have gone."
    )

    world.para()
    world.say(f'"Did you hear that?" {companion.id} asked. "This feels like a tiny mystery to solve."')
    pred = predict_search(world)
    world.facts["predicted"] = pred
    world.say(
        f'{hero.id} looked around the {setting.place} and listened for clues, because {animal.id} had hidden something nearby.'
    )
    _do_hide(world)
    world.say(
        f"Under the {animal.clue}, they spotted a tiny trail, and {companion.id} rushed to follow it."
    )

    world.para()
    if world.get("snack").meters["found"] >= THRESHOLD:
        world.say(
            f"At last, {hero.id} found the {animal.snack} tucked inside the {animal.hiding}, just where the clue led."
        )
        world.say(
            f"Everyone laughed when the surprise turned out to be a {surprise} tied to the snack like a silly little crown."
        )
        world.say(
            f"{animal.id} bobbed its head, gave another soft {animal.sound}, and then settled down for a calm snack time."
        )
    else:
        world.say(
            f"The clue trail faded for a moment, so {parent.label_word} gently helped them search again."
        )
        world.say(
            f"After a careful look, the missing treat was found, and the surprise still waited at the end."
        )

    world.facts.update(
        hero=hero,
        companion=companion,
        parent=parent,
        snack=snack,
        animal_ent=animal_ent,
        found=world.get("snack").meters["found"] >= THRESHOLD,
        hidden=world.get("snack").meters["hidden"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", ["cupboard", "table", "rug"], ["plate", "chair", "basket"]),
    "garden": Setting("garden", "the garden", ["bush", "bench", "watering can"], ["flowerpot", "stone", "bucket"]),
    "playroom": Setting("playroom", "the playroom", ["toy chest", "cushion", "sofa"], ["blocks", "lamp", "tunnel"]),
}

ANIMALS = {
    "dog": Animal("dog", "woof", "rush", "bone", "red bow", "under the table", "behind the plate", {"animal", "pet"}),
    "cat": Animal("cat", "meow", "dash", "fish biscuit", "tiny bell", "inside the toy chest", "under the cushion", {"animal", "pet"}),
    "duck": Animal("duck", "quack", "waddle-rush", "corn crumb", "shiny ribbon", "beside the bench", "near the flowerpot", {"animal", "wild"}),
    "bunny": Animal("bunny", "sniff", "hurry", "carrot slice", "paper crown", "under the sofa", "behind the lamp", {"animal", "wild"}),
}

SURPRISES = ["hat", "balloon", "shell", "blanket"]

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella", "Ruby"]
BOY_NAMES = ["Noah", "Theo", "Max", "Leo", "Finn", "Owen", "Ben"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    animal: str
    surprise: str
    hero: str
    companion: str
    parent: str
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
    ap = argparse.ArgumentParser(description="Animal mystery storyworld with a surprise ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero")
    ap.add_argument("--companion")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.animal is None or c[1] == args.animal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, animal = rng.choice(sorted(combos))
    surprise = args.surprise or rng.choice(SURPRISES)
    if not reasonableness_ok(SETTINGS[setting], ANIMALS[animal], surprise):
        raise StoryError("The chosen surprise does not fit this animal mystery.")
    hero = args.hero or rng.choice(GIRL_NAMES)
    companion = args.companion or rng.choice(BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, animal, surprise, hero, companion, parent)


def generation_prompts(world: World) -> list[str]:
    a = world.facts["animal"]
    s = world.facts["setting"]
    return [
        f'Write an animal story for a young child that includes the words "belch" and "rush" and takes place at {s.place}.',
        f"Tell a tiny mystery story where {a.id} makes a loud belch, rushes away, and the children solve what disappeared.",
        f"Write a gentle animal surprise story where a missing snack turns into a happy reveal.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    a = world.facts["animal"]
    hero = world.facts["hero"]
    comp = world.facts["companion"]
    parent = world.facts["parent"]
    snack = world.facts["snack"]
    s = world.facts["setting"]
    qa = [
        ("What kind of story is this?",
         f"It is an animal mystery story set at {s.place}. The children listen to clues, and the animal's noisy rush starts the puzzle."),
        (f"What happened after {a.id} made a loud belch?",
         f"{a.id} rushed away so quickly that everyone had to look around and solve a little mystery. That is how the missing treat became important."),
        ("What were the children trying to find?",
         f"They were trying to find the missing {snack.label}. The clue trail helped them notice where it had gone."),
        ("What was the surprise at the end?",
         f"The surprise was a {world.facts['surprise']} tied to the snack like a playful crown. It turned the mystery into a happy ending."),
    ]
    if world.get("snack").meters["found"] >= THRESHOLD:
        qa.append((f"How did {hero.id} and {comp.id} solve the mystery?",
                   f"They followed the clue, looked in the hiding spot, and found the missing snack. {parent.label_word.capitalize()} helped them stay calm while they searched."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    a = world.facts["animal"]
    return [
        ("What does belch mean?",
         "A belch is a loud burp. It can sound funny, especially in a silly animal story."),
        ("What does rush mean?",
         "To rush means to move very quickly. An animal that rushes darts off in a hurry."),
        (f"What kind of sound does a {a.id} make?",
         f"A {a.id} makes a {a.sound} sound. Animals often have different sounds in stories."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)} role={e.role}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hidden(snack) :- chosen_setting(S), chosen_animal(A), setting(S), animal(A).
found(snack) :- hidden(snack), search_started.
surprise_end(S) :- chosen_surprise(S), found(snack).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1."))
    _ = asp.atoms(model, "setting")
    # Smoke-test ordinary generation too.
    sample = generate(resolve_params(argparse.Namespace(setting=None, animal=None, surprise=None, parent=None, hero=None, companion=None), random.Random(7)))
    if not sample.story:
        print("Generation failed.")
        return 1
    print("OK: ASP loaded and generation smoke test passed.")
    return 0


def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1.\n#show animal/1.\n#show surprise/1."))
    return sorted(set(asp.atoms(model, "setting")))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ANIMALS[params.animal], params.surprise, params.hero, params.companion, params.parent)
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


CURATED = [
    StoryParams("kitchen", "dog", "hat", "Mia", "Noah", "mother"),
    StoryParams("garden", "duck", "balloon", "Lily", "Theo", "father"),
    StoryParams("playroom", "cat", "shell", "Zoe", "Finn", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1.\n#show animal/1.\n#show surprise/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{sid}" for (sid,) in asp_list()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

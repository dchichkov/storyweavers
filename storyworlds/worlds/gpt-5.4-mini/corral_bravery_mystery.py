#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/corral_bravery_mystery.py
=========================================================

A small storyworld about a child, a corral, and a brave mystery.

Premise
-------
A child hears a strange sound near a corral at dusk. They are nervous, but they
choose bravery, investigate carefully, and discover a harmless cause. A grown-up
helps, the mystery is solved, and the child ends feeling proud and brave.

This world keeps the tone close to a mystery: shadows, clues, searching, and a
final reveal. The emotional turn is bravery: fear rises, the child acts anyway,
and the ending proves that bravery changed what happened.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/corral_bravery_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/corral_bravery_mystery.py --all
    python storyworlds/worlds/gpt-5.4-mini/corral_bravery_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/corral_bravery_mystery.py --trace
    python storyworlds/worlds/gpt-5.4-mini/corral_bravery_mystery.py --json
    python storyworlds/worlds/gpt-5.4-mini/corral_bravery_mystery.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_THRESHOLD = 2.0


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str
    mood: str
    sound: str

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
class Mystery:
    id: str
    clue: str
    reveal: str
    source: str
    danger: bool = False
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
class Help:
    id: str
    action: str
    result: str
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue_source")
    if not clue:
        return out
    for ent in world.characters():
        if ent.memes["fear"] < THRESHOLD:
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["hesitation"] += 1
        out.append("__fear__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["bravery"] < BRAVERY_THRESHOLD:
            continue
        sig = ("brave", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["step_forward"] += 1
        out.append("__brave__")
    return out


CAUSAL_RULES = [
    Rule("fear", "social", _r_fear),
    Rule("bravery", "social", _r_bravery),
]


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


def _investigate(world: World, child: Entity, mystery: Mystery, narrate: bool = True) -> None:
    child.memes["bravery"] += 1
    child.meters["near_corral"] += 1
    propagate(world, narrate=narrate)


def predict_reveal(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    _investigate(sim, sim.get("child"), mystery, narrate=False)
    return {
        "brave": sim.get("child").meters["step_forward"] >= THRESHOLD,
        "fear": sim.get("child").meters["hesitation"],
    }


def intro(world: World, child: Entity) -> None:
    world.say(
        f"At dusk, {child.id} stood by the {world.setting.place} and listened to "
        f"the quiet {world.setting.mood} air."
    )


def mystery_sound(world: World, mystery: Mystery, child: Entity) -> None:
    world.say(
        f"Then a small sound came from the {mystery.source}. It was only a "
        f"{mystery.clue}, but it made the whole place feel secret."
    )
    child.memes["fear"] += 1


def brave_choice(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"{child.id} swallowed hard. {child.pronoun().capitalize()} was afraid, "
        f"but {child.pronoun()} still said, \"I'll look.\""
    )
    world.say(
        f"{child.id} took a deep breath and walked toward the dark fence while "
        f"{parent.label_word} watched from behind."
    )


def search(world: World, child: Entity, mystery: Mystery) -> None:
    child.meters["searching"] += 1
    world.say(
        f"{child.id} looked low, then high, and followed the clue to the edge of "
        f"the {world.setting.place}."
    )
    world.say(
        f"There, near the {mystery.source}, {child.id} found the reason for the "
        f"mystery."
    )


def reveal(world: World, mystery: Mystery, child: Entity, parent: Entity) -> None:
    world.say(
        f"It was just {mystery.reveal}. {mystery.source.capitalize()} had made the "
        f"sound, and the whole secret was harmless after all."
    )
    child.memes["fear"] = 0.0
    child.memes["pride"] += 1
    parent.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled and said, "
        f"\"That was brave of you. You checked carefully instead of running away.\""
    )


def ending(world: World, child: Entity, help_obj: Help) -> None:
    world.say(
        f"{child.id} grinned and stood a little taller. The {world.setting.place} "
        f"was quiet again, but now it felt like a place {child.pronoun()} knew."
    )
    world.say(
        f"With {help_obj.result}, {child.id} walked home proud, carrying the "
        f"bravery of the night like a bright little lantern."
    )


def tell(setting: Setting, mystery: Mystery, help_obj: Help,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                              role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type,
                              role="parent", label="the parent"))
    world.add(Entity(id="corral", type="place", label="the corral"))

    child.memes["bravery"] = 0.0
    child.memes["fear"] = 0.0

    intro(world, child)
    world.para()
    mystery_sound(world, mystery, child)
    brave_choice(world, child, parent)

    pred = predict_reveal(world, mystery)
    world.facts["predicted_fear"] = pred["fear"]

    world.para()
    search(world, child, mystery)
    _investigate(world, child, mystery, narrate=False)
    reveal(world, mystery, child, parent)

    world.para()
    ending(world, child, help_obj)

    world.facts.update(
        child=child,
        parent=parent,
        setting=setting,
        mystery=mystery,
        help=help_obj,
        brave=child.memes["bravery"] >= BRAVERY_THRESHOLD,
        solved=True,
    )
    return world


SETTINGS = {
    "corral": Setting("corral", "mystery", "a soft rustle"),
    "barn": Setting("barn", "quiet", "a little scrape"),
    "orchard": Setting("orchard", "sleepy", "a tiny tap"),
}

MYSTERIES = {
    "wind": Mystery("wind", "soft tapping", "the wind moving a loose ribbon",
                    "fence", danger=False, tags={"wind", "mystery"}),
    "cat": Mystery("cat", "tiny rustling", "a sleepy cat curled in the hay",
                   "gate", danger=False, tags={"cat", "mystery"}),
    "goat": Mystery("goat", "small nibbling noises", "a hungry little goat",
                    "feed bucket", danger=False, tags={"goat", "mystery"}),
}

HELPS = {
    "lantern": Help("lantern", "lit a lantern", "a warm lantern glow",
                    tags={"lantern"}),
    "handhold": Help("handhold", "held the parent's hand", "a steady hand",
                     tags={"hand", "comfort"}),
    "whistle": Help("whistle", "blew a small whistle", "a clear calling sound",
                    tags={"whistle"}),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lena", "Ruby", "Ada"]
BOY_NAMES = ["Eli", "Theo", "Milo", "Ben", "Owen", "Leo"]
TRAITS = ["careful", "curious", "quiet", "thoughtful"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    help: str
    name: str
    gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for hid in HELPS:
                combos.append((sid, mid, hid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about bravery at a corral.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--help-item", dest="help_item", choices=HELPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
              and (args.mystery is None or c[1] == args.mystery)
              and (args.help_item is None or c[2] == args.help_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, help_item = rng.choice(sorted(combos))
    m = MYSTERIES[mystery]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, mystery, help_item, name, gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    return [
        f"Write a gentle mystery story for a young child that takes place at a {f['setting'].place} and includes the word 'corral'.",
        f"Tell a story where {child.id} hears a clue near the corral, feels nervous, and shows bravery by investigating.",
        f"Write a child-facing mystery with a calm ending where the strange sound is explained and the child feels proud.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    mystery = f["mystery"]
    help_obj = f["help"]
    qa = [
        ("What kind of story is this?",
         f"It is a mystery story about {child.id} being brave at the corral. The mystery starts with a strange sound and ends with a calm answer."),
        ("Why was {0} nervous?".format(child.id),
         f"{child.id} was nervous because a small sound came from the corral and made the place feel secret. The unknown sound made {child.pronoun()} worry for a moment."),
        ("How did {0} show bravery?".format(child.id),
         f"{child.id} showed bravery by taking a deep breath and going to look. {child.pronoun().capitalize()} did not run away, and that choice helped solve the mystery."),
        ("What was the sound really?".format(child.id),
         f"It was really {mystery.reveal}. The sound was harmless, so the story ends with relief instead of danger."),
        ("How did the parent respond?",
         f"{parent.label_word.capitalize()} praised {child.id} for being brave and careful. The parent was glad {child.id} checked the clue instead of guessing."),
    ]
    if f.get("brave"):
        qa.append((
            "What changed by the end?",
            f"{child.id} started out frightened, but bravery grew and fear went away. By the end, {child.id} felt proud and the corral felt safe again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["help"].tags) | {"corral"}
    qa: list[tuple[str, str]] = []
    if "corral" in tags:
        qa.append(("What is a corral?",
                    "A corral is a fenced space where animals can stay safely together. People use it to keep animals from wandering away."))
    if "goat" in tags:
        qa.append(("What does a goat like to eat?",
                    "Goats like to nibble hay, leaves, and other plants. They are curious animals and often make little munching sounds."))
    if "lantern" in tags:
        qa.append(("What is a lantern?",
                    "A lantern is a light that helps you see in the dark. Some lanterns use batteries or a flame, but this kind is a safe light for a story."))
    if "wind" in tags:
        qa.append(("What does wind do?",
                    "Wind moves air around and can make fences, ribbons, and leaves rustle. It can sound mysterious when it is very quiet."))
    return qa


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], HELPS[params.help],
                 params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
brave(child) :- step_forward(child).
frightened(child) :- fear(child), not brave(child).
solved(mystery) :- brave(child), reveal(clue).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for hid in HELPS:
        lines.append(asp.fact("help", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set((a, b, c) for (a, b, c) in asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid_combos")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, help_item=None, gender=None, parent=None, name=None), random.Random(777)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams("corral", "goat", "lantern", "Mina", "girl", "mother"),
    StoryParams("barn", "wind", "handhold", "Eli", "boy", "father"),
    StoryParams("orchard", "cat", "whistle", "Nora", "girl", "mother"),
]


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
        print(f"{len(valid_combos())} compatible combos:")
        for c in valid_combos():
            print(" ", c)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting} / {p.mystery}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

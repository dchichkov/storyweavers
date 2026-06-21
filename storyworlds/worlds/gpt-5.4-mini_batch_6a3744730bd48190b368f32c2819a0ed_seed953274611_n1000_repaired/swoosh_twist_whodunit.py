#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/swoosh_twist_whodunit.py
========================================================

A small whodunit-style storyworld: a child notices a missing pie, follows clues
through a windy kitchen with a swoosh of a curtain, and a twist reveals the
"thief" was a helpful pet carrying the evidence to the real culprit.

The world is intentionally compact:
- one scene, one mystery, one twist
- typed entities with meters and memes
- a Python reasonableness gate plus an inline ASP twin
- deterministic prose driven by simulated state
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if case == "possessive":
            return "its"
        return "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Scene:
    room: str
    clue_places: list[str]
    sound_words: list[str]
    twist_item: str
    missing_item: str
    culprit_hint: str
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


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    reveal: str
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
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    adult_name: str
    adult_gender: str
    missing_item: str
    clue: str
    twist: str
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


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_tension(world: World) -> list[str]:
    out = []
    pie = world.entities.get("pie")
    if pie and pie.meters["missing"] >= THRESHOLD:
        for kid in [e for e in world.entities.values() if e.role in {"child", "helper"}]:
            kid.memes["worry"] += 1
        if ("tension",) not in world.fired:
            world.fired.add(("tension",))
            out.append("__tension__")
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    basket = world.entities.get("basket")
    cat = world.entities.get("cat")
    if basket and cat and basket.meters["found"] >= THRESHOLD and cat.memes["guilt"] >= THRESHOLD:
        if ("twist",) not in world.fired:
            world.fired.add(("twist",))
            out.append("__twist__")
    return out


RULES = [Rule("tension", _r_tension), Rule("twist", _r_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_missing(world: World) -> bool:
    sim = world.copy()
    sim.get("pie").meters["missing"] = 1
    propagate(sim, narrate=False)
    return sim.get("child").memes["worry"] >= THRESHOLD


SCENES = {
    "kitchen": Scene(
        room="the kitchen",
        clue_places=["the counter", "the rug", "the window"],
        sound_words=["swoosh", "tap", "rustle"],
        twist_item="basket",
        missing_item="pie",
        culprit_hint="the cat",
    ),
    "bakery": Scene(
        room="the bakery",
        clue_places=["the shelf", "the door", "the floor"],
        sound_words=["swoosh", "clink", "whisper"],
        twist_item="basket",
        missing_item="bun",
        culprit_hint="the dog",
    ),
}

CLUES = {
    "footprint": Clue(id="footprint", label="a tiny muddy footprint", kind="clue", reveal="near the rug", tags={"mystery"}),
    "crumbs": Clue(id="crumbs", label="a trail of crumbs", kind="clue", reveal="leading to the basket", tags={"mystery"}),
    "ribbon": Clue(id="ribbon", label="a blue ribbon", kind="clue", reveal="caught on the basket handle", tags={"mystery"}),
}

TWISTS = {
    "cat": "the cat had carried the missing pie crust into the basket to hide it from the ants",
    "dog": "the dog had dragged the bun into the basket because it smelled like breakfast",
}

NAMES_GIRL = ["Mia", "Lina", "Nora", "Ava", "Zoe"]
NAMES_BOY = ["Ben", "Theo", "Leo", "Max", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for clue in CLUES:
            for twist in TWISTS:
                if scene == "kitchen" and twist == "cat":
                    combos.append((scene, clue, twist))
                if scene == "bakery" and twist == "dog":
                    combos.append((scene, clue, twist))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style mystery with a swoosh and a twist.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--adult")
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
              if (args.scene is None or c[0] == args.scene)
              and (args.clue is None or c[1] == args.clue)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid mystery matches the given options.)")
    scene, clue, twist = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if child_gender == "girl" else "girl"
    adult_gender = rng.choice(["mother", "father"])
    child_name = args.name or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper_name = args.helper or rng.choice(NAMES_BOY if helper_gender == "boy" else NAMES_GIRL)
    adult_name = args.adult or rng.choice(["Mom", "Dad"])
    return StoryParams(
        scene=scene,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        adult_name=adult_name,
        adult_gender=adult_gender,
        missing_item=SCENES[scene].missing_item,
        clue=clue,
        twist=twist,
    )


def tell(params: StoryParams) -> World:
    scene = SCENES[params.scene]
    world = World(scene)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, role="child", label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, role="helper", label=params.helper_name))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult_gender, role="adult", label=params.adult_name))
    pie = world.add(Entity(id="pie", type="thing", label=params.missing_item))
    basket = world.add(Entity(id="basket", type="thing", label="a basket"))
    clue = world.add(Entity(id="clue", type="thing", label=CLUES[params.clue].label))
    cat = world.add(Entity(id="cat", type="animal", label="the cat"))
    cat.memes["guilt"] = 0.0

    world.say(
        f"One quiet afternoon in {scene.room}, {child.label} and {helper.label} were ready for a little mystery."
    )
    world.say(
        f"Then came a swoosh from the window curtain, and {child.label} turned. The pie on the counter was gone."
    )

    world.para()
    pie.meters["missing"] = 1
    child.memes["surprise"] += 1
    helper.memes["focus"] += 1
    world.say(
        f'"The pie!" {child.label} said. "{helper.label}, we have to find out who took it."'
    )
    world.say(
        f"{helper.label} pointed at {clue.label} {CLUES[params.clue].reveal}."
    )

    if predict_missing(world):
        world.say(
            f"{child.label} narrowed {child.pronoun('possessive')} eyes. This was a real whodunit now."
        )

    world.para()
    if params.clue == "crumbs":
        basket.meters["found"] = 1
        world.say(
            f"They followed the crumbs across {scene.clue_places[0]} and around {scene.clue_places[1]}."
        )
    elif params.clue == "footprint":
        basket.meters["found"] = 1
        world.say(
            f"They studied the footprint, then spotted the same muddy mark beside the basket."
        )
    else:
        basket.meters["found"] = 1
        world.say(
            f"The ribbon dangled from the basket handle, like a tiny flag saying look here."
        )

    cat.memes["guilt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last they peeked inside the basket."
    )
    world.say(
        f"And there was the twist: {TWISTS[params.twist]}."
    )

    world.para()
    pie.meters["missing"] = 0
    pie.meters["found"] = 1
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    adult.memes["calm"] += 1
    world.say(
        f"{adult.label} laughed softly, not angry at all. The mystery had a funny answer."
    )
    world.say(
        f"{child.label} set the pie back on the counter, and the whole room felt neat again, with the swoosh of the curtain settling down."
    )

    world.facts.update(
        child=child,
        helper=helper,
        adult=adult,
        pie=pie,
        basket=basket,
        clue=clue,
        cat=cat,
        scene=scene,
        params=params,
        twist_text=TWISTS[params.twist],
        outcome="solved",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.clue not in CLUES or params.twist not in TWISTS:
        raise StoryError("(Invalid story parameters.)")
    if (params.scene, params.clue, params.twist) not in valid_combos():
        raise StoryError("(No valid mystery matches the given options.)")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short whodunit for a child that includes the word swoosh and a twist.",
        f"Tell a gentle mystery about {f['params'].child_name} and {f['params'].helper_name} finding a missing {f['pie'].label}.",
        f"Write a story where a clue leads to a basket and the answer is surprising but kind.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Who was the story about?", f"It was about {f['child'].label} and {f['helper'].label}, who tried to solve a small mystery together."),
        ("What was missing?", f"The missing thing was {f['pie'].label}. The children noticed it was gone from the counter at the start."),
        ("What was the twist?", f"The twist was that {f['twist_text']}. That made the mystery surprising, but harmless in the end."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clue?", "A clue is a small sign that helps you figure out what happened in a mystery."),
        ("What does swoosh mean?", "Swoosh is the soft sound of something moving quickly through the air."),
        ("What is a twist in a story?", "A twist is a surprising turn that changes what you thought was going on."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id:6} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


CURATED = [
    StoryParams(scene="kitchen", child_name="Mia", child_gender="girl", helper_name="Ben", helper_gender="boy", adult_name="Mom", adult_gender="mother", missing_item="pie", clue="crumbs", twist="cat"),
    StoryParams(scene="bakery", child_name="Leo", child_gender="boy", helper_name="Nora", helper_gender="girl", adult_name="Dad", adult_gender="father", missing_item="bun", clue="ribbon", twist="dog"),
]


def explain_invalid(scene: str, clue: str, twist: str) -> str:
    return f"(No story: the combination {scene}/{clue}/{twist} does not fit this mystery.)"


ASP_RULES = r"""
valid(S,C,T) :- scene(S), clue(C), twist(T), compatible(S,T).
missing(P) :- scene(kitchen), pie(P).
missing(P) :- scene(bakery), bun(P).
twist(cat) :- compatible(kitchen,cat).
twist(dog) :- compatible(bakery,dog).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    lines.append(asp.fact("compatible", "kitchen", "cat"))
    lines.append(asp.fact("compatible", "bakery", "dog"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combo sets differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generated a story.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with a swoosh and a twist.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
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
              if (args.scene is None or c[0] == args.scene)
              and (args.clue is None or c[1] == args.clue)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid mystery matches the given options.)")
    scene, clue, twist = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if child_gender == "girl" else "girl"
    adult_gender = rng.choice(["mother", "father"])
    return StoryParams(
        scene=scene,
        child_name=rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY),
        child_gender=child_gender,
        helper_name=rng.choice(NAMES_BOY if helper_gender == "boy" else NAMES_GIRL),
        helper_gender=helper_gender,
        adult_name=rng.choice(["Mom", "Dad"]),
        adult_gender=adult_gender,
        missing_item=SCENES[scene].missing_item,
        clue=clue,
        twist=twist,
    )


def generate(params: StoryParams) -> StorySample:
    if (params.scene, params.clue, params.twist) not in valid_combos():
        raise StoryError(explain_invalid(params.scene, params.clue, params.twist))
    world = tell(params)
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
        print(f"{len(asp_valid_combos())} compatible mystery combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            if sample.story not in seen:
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a whodunit story that includes swoosh and ends with a twist.",
        f"Tell a mystery about {f['child'].label} and {f['helper'].label} finding a missing {f['pie'].label}.",
        "Make the answer surprising but kind, with a clue trail and a gentle ending.",
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clue?", "A clue is a small sign that helps solve a mystery."),
        ("What does swoosh mean?", "Swoosh is the soft sound of something moving quickly through the air."),
        ("What is a twist?", "A twist is a surprising turn in a story that changes the answer."),
    ]


if __name__ == "__main__":
    main()

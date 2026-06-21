#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bahbah_cautionary_kindness_humor_whodunit.py
=============================================================================

A standalone story world for a tiny whodunit: a child, a missing treat, a few
suspicious clues, a kind correction, and a gentle lesson about not accusing too
fast. The world stays small and physical, with meters for things that can get
moved, spilled, or messy, and memes for what the characters feel as the mystery
unfolds.

Seed premise
------------
A child finds a small mess and thinks the new goat named Bahbah must have done
it. The story should feel like a kid-friendly whodunit, with cautionary tension,
kindness toward the likely suspect, and a funny reveal that shows who really did
it.

Contract notes
--------------
- stdlib only
- imports storyworlds/results.py eagerly
- lazy imports storyworlds/asp.py inside ASP helpers
- includes StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

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
class Suspect:
    id: str
    label: str
    clue: str
    can_do_it: bool = True
    humorous: bool = False
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
class Clue:
    id: str
    label: str
    meter: str
    amount: float
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


@dataclass
class Resolution:
    id: str
    sense: int
    text: str
    lesson: str
    qa_text: str
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
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    if world.get("jar").meters["spilled"] < THRESHOLD:
        return out
    sig = ("spill_seen",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("floor").meters["sticky"] += 1
    world.get("child").memes["worry"] += 1
    out.append("__spill__")
    return out


def _r_accuse(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["suspicion"] < THRESHOLD:
        return out
    sig = ("accuse",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("goat").memes["sad"] += 1
    out.append("__accuse__")
    return out


CAUSAL_RULES = [
    _r_spill,
    _r_accuse,
]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def reasonableness_ok(params: "StoryParams") -> bool:
    return params.suspect in SUSPECTS and params.resolution in RESOLUTIONS


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for scene in SCENES:
        for suspect in SUSPECTS:
            for resolution in RESOLUTIONS:
                if SCENES[scene].mystery and RESOLUTIONS[resolution].sense >= SENSE_MIN:
                    out.append((scene, suspect, resolution))
    return out


def explain_rejection(_: str = "", __: str = "", ___: str = "") -> str:
    return "(No story: this combination does not make a fair little mystery.)"


@dataclass
class Scene:
    id: str
    place: str
    mystery: str
    mess: str
    ending: str
    clue: str
    has_goat: bool = True

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
    scene: str
    suspect: str
    resolution: str
    child: str
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


SCENES = {
    "kitchen": Scene(
        "kitchen", "the kitchen", "a missing snack", "crumbs and a little spill",
        "the snack was found in the pantry", "crumbs"),
    "laundry": Scene(
        "laundry", "the laundry room", "a missing sock", "a trail of fluff",
        "the sock was in the basket", "fluff"),
    "yard": Scene(
        "yard", "the backyard", "a missing rake", "muddy hoofprints",
        "the rake was behind the shed", "hoofprints"),
}

SUSPECTS = {
    "bahbah": Suspect("bahbah", "Bahbah the goat", "bahbah", can_do_it=False, humorous=True, tags={"goat", "bahbah"}),
    "cat": Suspect("cat", "the cat", "meow", can_do_it=True, humorous=True, tags={"cat"}),
    "wind": Suspect("wind", "the wind", "whoosh", can_do_it=False, humorous=True, tags={"wind"}),
}

RESOLUTIONS = {
    "kind_peek": Resolution(
        "kind_peek", 3,
        "the child knelt down, followed the clue, and looked under the crate instead of blaming anyone",
        "It is kinder to look for clues than to point paws or fingers too fast.",
        "looked under the crate and found the answer without blaming Bahbah",
        tags={"kindness", "caution"}),
    "apology": Resolution(
        "apology", 2,
        "the child apologized to Bahbah and helped wipe the floor",
        "A small mistake can be fixed with kindness and a clean cloth.",
        "apologized to Bahbah and helped clean up",
        tags={"kindness", "humor"}),
    "laugh_and_learn": Resolution(
        "laugh_and_learn", 2,
        "everyone laughed when the culprit turned out to be the sneaky cat",
        "Even a funny mystery should end with a careful look, not a fast guess.",
        "laughed and learned to check the clues first",
        tags={"humor", "caution"}),
}


GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Tom", "Leo", "Max", "Finn"]


def choose_child(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return name, gender


def tell(scene: Scene, suspect: Suspect, resolution: Resolution, child_name: str, child_gender: str, parent_name: str) -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=child_gender, label=child_name, role="detective", traits=["curious"]))
    parent = world.add(Entity("parent", kind="character", type="mother", label=parent_name, role="parent"))
    goat = world.add(Entity("goat", kind="character", type="thing", label="Bahbah", role="suspect"))
    jar = world.add(Entity("jar", type="thing", label="snack jar"))
    floor = world.add(Entity("floor", type="thing", label="floor"))
    jar.meters["spilled"] = 1.0
    child.memes["suspicion"] = 1.0 if suspect.id == "bahbah" else 0.0
    child.memes["curiosity"] = 1.0

    world.say(
        f"At {scene.place}, {child.label} found {scene.mystery}. "
        f"There were {scene.mess} all around, and one clue looked very odd."
    )
    world.say(
        f'{child.label} stared at the clue and whispered, "Bahbah?" '
        f'The little goat only went, "bahbah," as if it had nothing to hide.'
    )
    world.para()
    world.say(
        f"{child.label} almost pointed a finger at Bahbah, but {parent.label_word} said, "
        f'"First we look. A mystery is solved by clues, not by hasty guesses."'
    )
    world.say(
        f"Then {child.label} noticed that {scene.clue} led away from Bahbah and toward the pantry."
    )

    if suspect.id == "bahbah":
        world.say("Bahbah had been licking a salt shaker and looking very innocent.")
    elif suspect.id == "cat":
        world.say("The cat darted past with a crumb on its nose and a proud little tail.")
    else:
        world.say("A puff of wind had blown the paper napkin right off the table.")

    world.para()
    if resolution.id == "kind_peek":
        world.say(
            f"{child.label} knelt down, followed the clue, and found the answer hidden where nobody had looked."
        )
        world.say(
            f"{parent.label_word.capitalize()} smiled, and Bahbah got a gentle pat instead of a blame."
        )
    elif resolution.id == "apology":
        world.say(
            f"{child.label} blushed, apologized to Bahbah, and helped wipe up the mess with a soft cloth."
        )
        world.say("Bahbah chewed a leaf, very forgiven and very pleased.")
    else:
        world.say(
            f"{child.label} and {parent.label_word} followed the trail, then laughed when the sneaky cat was caught."
        )
        world.say("Bahbah just blinked, because Bahbah had never been the culprit at all.")

    world.say(
        f"In the end, the {scene.ending}, and {child.label} learned to be careful, kind, and a little bit funny about mysteries."
    )

    world.facts.update(
        scene=scene,
        suspect=suspect,
        resolution=resolution,
        child=child,
        parent=parent,
        goat=goat,
        jar=jar,
        floor=floor,
        culprit=suspect.id,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene, suspect, resolution = f["scene"], f["suspect"], f["resolution"]
    return [
        f'Write a kid-friendly whodunit set in {scene.place} that includes the word "bahbah".',
        f"Tell a short mystery where {f['child'].label} thinks {suspect.label} did it, but the clues lead to a kinder answer.",
        f"Write a funny cautionary story in whodunit style where the child does not blame Bahbah too quickly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, scene, suspect, resolution = f["child"], f["parent"], f["scene"], f["suspect"], f["resolution"]
    items = [
        QAItem(
            question="What kind of story is this?",
            answer="It is a small whodunit mystery with a funny clue, a careful ending, and a kind lesson about not blaming too fast."
        ),
        QAItem(
            question=f"Why did {child.label} think Bahbah might be involved?",
            answer=f"{child.label} saw the mess and the strange clue, so Bahbah looked suspicious at first. But the story shows that first guesses can be wrong."
        ),
        QAItem(
            question="How did the mystery get solved?",
            answer=f"{child.label} followed the clue instead of blaming anyone right away. That careful look led to the real answer and kept Bahbah safe from an unfair accusation."
        ),
    ]
    if suspect.id == "bahbah":
        items.append(
            QAItem(
                question="Was Bahbah really the culprit?",
                answer="No. Bahbah only sounded funny and looked suspicious for a moment, but the clue pointed somewhere else."
            )
        )
    if resolution.id == "kind_peek":
        items.append(
            QAItem(
                question="What did the child do that was kind?",
                answer=f"{child.label} looked for the answer without being mean, and that kindness helped everyone stay calm."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you solve a mystery."
        ),
        QAItem(
            question="Why should you not accuse someone too quickly?",
            answer="Because the first guess can be wrong, and an unfair accusation can hurt feelings. It is better to look carefully and be kind."
        ),
        QAItem(
            question="What does a goat say?",
            answer="A goat often makes a bleating sound like bahbah."
        ),
    ]
    if world.facts["suspect"].id == "cat":
        out.append(QAItem(
            question="What is a cat like in a mystery?",
            answer="A cat can be sneaky and make a funny suspect, especially if it has crumbs on its nose."
        ))
    return out


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


ASP_RULES = r"""
valid(S, Su, R) :- scene(S), suspect(Su), resolution(R), sense(R, N), sense_min(M), N >= M.
culprit(bahbah) :- suspect(bahbah).
kind_end(R) :- resolution(R), sense(R, N), N >= sense_min(M), M = 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for rid, res in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, res.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH between python and ASP valid combos.")
        print(" only python:", sorted(py - cl))
        print(" only asp:", sorted(cl - py))
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            scene=None, suspect=None, resolution=None, child=None, parent=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny cautionary kindness whodunit about Bahbah.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--child")
    ap.add_argument("--parent")
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
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("unknown suspect")
    if args.resolution and RESOLUTIONS[args.resolution].sense < SENSE_MIN:
        raise StoryError("resolution too weak")
    scene = args.scene or rng.choice(list(SCENES))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    resolution = args.resolution or rng.choice([k for k, v in RESOLUTIONS.items() if v.sense >= SENSE_MIN])
    child = args.child or rng.choice(GIRL_NAMES + BOY_NAMES)
    parent = args.parent or rng.choice(["Mom", "Dad"])
    return StoryParams(scene, suspect, resolution, child, parent)


CURATED = [
    StoryParams("kitchen", "bahbah", "kind_peek", "Mia", "Mom"),
    StoryParams("laundry", "cat", "laugh_and_learn", "Ben", "Dad"),
    StoryParams("yard", "wind", "apology", "Nora", "Mom"),
]


def generate(params: StoryParams) -> StorySample:
    scene = SCENES[params.scene]
    suspect = SUSPECTS[params.suspect]
    resolution = RESOLUTIONS[params.resolution]
    world = tell(scene, suspect, resolution, params.child, "girl" if params.child in GIRL_NAMES else "boy", params.parent)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for scene, suspect, resolution in asp_valid_combos():
            print(f"  {scene:8} {suspect:8} {resolution}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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

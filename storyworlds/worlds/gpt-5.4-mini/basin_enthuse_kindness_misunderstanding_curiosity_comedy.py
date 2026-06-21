#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/basin_enthuse_kindness_misunderstanding_curiosity_comedy.py
===========================================================================================

A small standalone storyworld for a comedy about curiosity, kindness, and a
misunderstanding around a basin. A child thinks a basin is for something grand,
enthuses about it, and a kind adult gently clears up the mix-up. The world model
tracks physical and emotional state so the story changes because the characters
do things, not because the wording is swapped.
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
class Setting:
    id: str
    place: str
    basin_use: str
    curiosity_hook: str

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
class Item:
    id: str
    label: str
    phrase: str
    purpose: str
    safe: bool = True
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
class Misunderstanding:
    id: str
    idea: str
    wrong_use: str
    comic_image: str
    correction: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    basin = world.entities.get("basin")
    if not kid or not basin:
        return out
    if kid.meters["splashed"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    basin.meters["wet"] += 1
    kid.memes["embarrassment"] += 1
    out.append("__spill__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    adult = world.entities.get("adult")
    if not kid or not adult:
        return out
    if kid.memes["embarrassment"] < THRESHOLD or adult.memes["kindness"] < THRESHOLD:
        return out
    sig = ("laugh",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["relief"] += 1
    adult.memes["warmth"] += 1
    out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("laugh", "social", _r_laugh)]


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


def playful_setup(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {adult.id} were in {setting.place}. "
        f"{child.id} kept peeking at {setting.curiosity_hook}."
    )


def enthuse(world: World, child: Entity, item: Item, misunderstanding: Misunderstanding) -> None:
    child.memes["enthusiasm"] += 1
    world.say(
        f'{child.id} pointed at the {item.label} and all but bounced in place. '
        f'"A basin!" {child.id} enthused. "That is a splendid {item.purpose}!"'
    )
    world.say(
        f'{child.id} imagined {misunderstanding.comic_image}. The idea sounded '
        f'grand and a little silly.'
    )


def warn_gently(world: World, adult: Entity, child: Entity, item: Item, misunderstanding: Misunderstanding) -> None:
    adult.memes["kindness"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f'{adult.id} smiled. "{child.id}, that basin is for {item.purpose}, '
        f'not for {misunderstanding.wrong_use}."'
    )
    world.say(
        f'"Oh!" {child.id} said, blinking. "I was curious, and I got the basin '
        f'mixed up."'
    )


def small_try(world: World, child: Entity, item: Item) -> None:
    child.meters["splashed"] += 1
    child.memes["mischief"] += 1
    world.say(
        f"Still curious, {child.id} gave the basin one tiny tap, and a little "
        f"splash leapt up like a shocked fish."
    )
    propagate(world, narrate=False)


def kind_fix(world: World, adult: Entity, child: Entity, item: Item, misunderstanding: Misunderstanding) -> None:
    adult.meters["helped"] += 1
    child.memes["relief"] += 1
    world.say(
        f"Then {adult.id} fetched a towel and set the {item.label} back in place. "
        f'{adult.id} laughed softly. "{misunderstanding.correction}"'
    )
    world.say(
        f"{child.id} grinned, because the mix-up had become a joke instead of a fuss."
    )


def ending_image(world: World, child: Entity, adult: Entity, item: Item, setting: Setting) -> None:
    world.say(
        f"At the end, the basin sat neatly where it belonged, the towel was dry, "
        f"and {child.id} was still enthused -- only now about helping {adult.id} "
        f"tidy up."
    )


def tell(setting: Setting, item: Item, misunderstanding: Misunderstanding,
         child_name: str = "Milo", child_gender: str = "boy",
         adult_name: str = "Mom", adult_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="curious_child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="kind_adult"))
    basin = world.add(Entity(id="basin", type="thing", label=item.label))
    world.add(Entity(id="towel", type="thing", label="towel"))
    world.facts.update(setting=setting, item=item, misunderstanding=misunderstanding)

    playful_setup(world, child, adult, setting)
    world.para()
    enthuse(world, child, item, misunderstanding)
    warn_gently(world, adult, child, item, misunderstanding)
    small_try(world, child, item)
    world.para()
    kind_fix(world, adult, child, item, misunderstanding)
    ending_image(world, child, adult, item, setting)
    world.facts.update(child=child, adult=adult, basin=basin,
                       confused=child.memes["enthusiasm"] >= THRESHOLD,
                       spill=basin.meters["wet"] >= THRESHOLD,
                       kind_help=adult.meters["helped"] >= THRESHOLD)
    return world


SETTINGS = {
    "bathroom": Setting("bathroom", "the bathroom", "washing hands", "the shiny taps"),
    "garden": Setting("garden", "the garden shed", "watering seeds", "the row of clay pots"),
    "kitchen": Setting("kitchen", "the kitchen", "catching drips from apples", "the fruit bowl"),
}

ITEMS = {
    "basin": Item("basin", "basin", "a blue basin", "hold water", safe=True, tags={"basin"}),
    "washbowl": Item("washbowl", "wash bowl", "a little wash bowl", "hold soap and water", safe=True, tags={"basin"}),
    "mixbowl": Item("mixbowl", "mixing bowl", "a mixing bowl", "catch batter", safe=True, tags={"basin"}),
}

MISUNDERSTANDINGS = {
    "fish": Misunderstanding(
        "fish", "it is a fish pool", "fishing",
        "a tiny imaginary fish wearing a hat",
        "Basins are for washing, not fishing, but your imagination gets full marks.",
        tags={"basin", "comedy", "curiosity"},
    ),
    "crown": Misunderstanding(
        "crown", "it is a crown dish", "wearing as a hat",
        "a kingly basin balanced on a kitten's head",
        "Basins are for holding water, not becoming hats, but nice try.",
        tags={"basin", "comedy", "curiosity"},
    ),
    "boat": Misunderstanding(
        "boat", "it is a boat", "sailing in",
        "a spoon-paddled basin sailing across the floor",
        "Basins are for washing, not sailing, though that was an excellent performance.",
        tags={"basin", "comedy", "curiosity"},
    ),
}



@dataclass
class StoryParams:
    setting: str
    item: str
    misunderstanding: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
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

CURATED = [
    StoryParams("bathroom", "basin", "fish", "Milo", "boy", "Mom", "mother"),
    StoryParams("garden", "washbowl", "crown", "Lena", "girl", "Dad", "father"),
    StoryParams("kitchen", "mixbowl", "boat", "Toby", "boy", "Mom", "mother"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, i, m) for s in SETTINGS for i in ITEMS for m in MISUNDERSTANDINGS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a basin and a misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--name")
    ap.add_argument("--adult")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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
              and (args.item is None or c[1] == args.item)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, mis = rng.choice(combos)
    gender = args.gender or rng.choice(["boy", "girl"])
    child_name = args.name or rng.choice(["Milo", "Lena", "Toby", "Nina", "Iris", "Sam"])
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    adult_name = args.adult or ("Mom" if adult_gender == "mother" else "Dad")
    return StoryParams(setting, item, mis, child_name, gender, adult_name, adult_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "basin" and "enthuse".',
        f"Tell a comedy story where {f['child'].id} gets a basin idea wrong, and {f['adult'].id} kindly clears up the misunderstanding.",
        f"Write a playful story about curiosity and kindness where a child enthuses about a basin and then learns what it is really for.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, item, mis = f["child"], f["adult"], f["item"], f["misunderstanding"]
    return [
        (f"What did {child.id} think the basin was for?",
         f"{child.id} thought the basin was for {mis.wrong_use}. That was the funny mix-up in the story."),
        (f"How did {adult.id} respond?",
         f"{adult.id} responded kindly and explained that the basin was for {item.purpose}. The kind answer turned the mistake into a laugh."),
        ("How did the story end?",
         f"It ended with the basin put back in place and everyone smiling. The child stayed curious, but now the curiosity came with a better idea."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a basin?",
         "A basin is a bowl-like container that can hold water. People often use one for washing or cleaning."),
        ("What does it mean to enthuse?",
         "To enthuse means to speak with a lot of excitement and energy. A person who enthuses sounds cheerful and eager."),
        ("Why are misunderstandings funny in stories?",
         "Misunderstandings are funny because one character guesses wrong while another knows the truth. The mistake can lead to a silly moment before things get cleared up."),
        ("Why is kindness important when someone is confused?",
         "Kindness helps the confused person feel safe enough to learn. A gentle explanation can fix the problem without hurt feelings."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
kindness(better) :- kind_help.
misunderstanding(cleared) :- spill, kindness(better).
curiosity(active) :- confused.
outcome(comedy) :- misunderstanding(cleared), curiosity(active).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("topic", "basin"),
        asp.fact("feature", "kindness"),
        asp.fact("feature", "misunderstanding"),
        asp.fact("feature", "curiosity"),
    ]
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    rc = 0
    model = asp.one_model(asp_program("", "#show outcome/1."))
    atoms = set(asp.atoms(model, "outcome"))
    ok = ("comedy",) in atoms
    if ok:
        print("OK: ASP twin produces the comedy outcome.")
    else:
        print("MISMATCH: ASP twin did not produce the expected outcome.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, item=None, misunderstanding=None, name=None, adult=None, gender=None, adult_gender=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def asp_list() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    return [str(a) for a in asp.atoms(model, "outcome")]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], MISUNDERSTANDINGS[params.misunderstanding],
                 params.child_name, params.child_gender, params.adult_name, params.adult_gender)
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
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(asp_list()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

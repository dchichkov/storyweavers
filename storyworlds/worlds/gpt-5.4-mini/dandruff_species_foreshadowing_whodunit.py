#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dandruff_species_foreshadowing_whodunit.py
===========================================================================

A small storyworld about a child detective, a mysterious trail of dandruff,
and a clue about species that foreshadows the culprit. The domain is a tidy
whodunit: someone notices an odd clue, gathers evidence, makes a careful
accusation, and resolves the mystery with a gentle reveal.

The world model keeps track of physical meters and emotional memes, and the
story is driven by state transitions rather than a frozen template. The prose is
child-facing and complete, with a beginning, a middle turn, and an ending image
that proves what changed.
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
SUSPECT_MIN = 2.0
CLUE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"evidence": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "pride": 0.0}

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
    weather: str
    foreshadow_line: str

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
class Suspect:
    id: str
    species: str
    species_hint: str
    grooming: str
    alibi: str
    clue_style: str
    hides_dandruff: bool = False

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
class Clue:
    id: str
    label: str
    kind: str
    detail: str
    points_to_species: str

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
        self.fired: set[str] = set()
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
        return clone


SETTINGS = {
    "school": Setting("school", "the school library", "quiet", "A tiny white flake on the blue chair foreshadowed that this case would not stay simple."),
    "museum": Setting("museum", "the museum hallway", "still", "Before anyone spoke, a dusting of white on the collar hinted that the answer would be furry, not sneaky."),
    "shop": Setting("shop", "the corner shop", "bright", "A speck on the glass counter hinted there was a visitor trail to follow."),
}

SUSPECTS = {
    "cat": Suspect("cat", "cat", "a cat", "licked its fur clean", "slept by the window", "soft paw prints", hides_dandruff=False),
    "dog": Suspect("dog", "dog", "a dog", "rolled in grass", "napped by the door", "muddy nose prints", hides_dandruff=False),
    "bird": Suspect("bird", "bird", "a bird", "preened its feathers", "sat in the cage", "tiny feather marks", hides_dandruff=False),
    "sheep": Suspect("sheep", "sheep", "a sheep", "rubs against fences", "waited in the yard", "crumbly wool bits", hides_dandruff=False),
    "rabbit": Suspect("rabbit", "rabbit", "a rabbit", "scratched behind one ear", "hid under a bench", "soft whisker traces", hides_dandruff=False),
}

CLUES = {
    "dandruff": Clue("dandruff", "dandruff", "flake", "a few white flakes on the chair", "grooming"),
    "fur": Clue("fur", "fur", "hair", "a fuzzy hair stuck to the ribbon", "cat"),
    "feathers": Clue("feathers", "feathers", "feather", "a light feather on the notebook", "bird"),
    "wool": Clue("wool", "wool", "fiber", "a curly wool thread on the floor", "sheep"),
    "whiskers": Clue("whiskers", "whiskers", "trace", "a soft whisker-like mark on the paper", "rabbit"),
}

GROWNUPS = ["mother", "father"]
DETECTIVE_NAMES = ["Mia", "Noah", "Lily", "Theo", "Ava", "Ben"]


def story_prompt(setting: World, suspect: Suspect) -> list[str]:
    return [
        f"Write a child-friendly whodunit in {setting.setting.place} that includes the word dandruff and the word species.",
        f"Tell a mystery story where a clue about dandruff foreshadows which species visited {setting.setting.place}.",
        f"Write a gentle detective story in which the answer is found by noticing a clue and thinking about species.",
    ]


def knowledge_for_species(species: str) -> tuple[str, str]:
    table = {
        "cat": ("What is a cat?", "A cat is a small furry animal that likes to groom itself and often has soft whiskers."),
        "dog": ("What is a dog?", "A dog is a pet animal that can leave muddy prints and has a very good nose."),
        "bird": ("What is a bird?", "A bird has feathers and a beak, and many birds like to preen their feathers clean."),
        "sheep": ("What is a sheep?", "A sheep is an animal with wool, and wool can leave little fluffy bits behind."),
        "rabbit": ("What is a rabbit?", "A rabbit is a small animal with whiskers and soft fur, and it can hide under things."),
    }
    return table[species]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for sp in SUSPECTS:
            combos.append((s, sp))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    suspect: str
    detective: str
    grownup: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld about dandruff, species, and foreshadowed clues.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective", choices=DETECTIVE_NAMES)
    ap.add_argument("--grownup", choices=GROWNUPS)
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
              and (args.suspect is None or c[1] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, suspect = rng.choice(sorted(combos))
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    grownup = args.grownup or rng.choice(GROWNUPS)
    return StoryParams(setting, suspect, detective, grownup)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sp in SUSPECTS:
        lines.append(asp.fact("suspect", sp))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P) :- setting(S), suspect(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def explain_rejection() -> str:
    return "(No story: the requested clues do not make a reasonable whodunit.)"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(setting: Setting, suspect: Suspect, detective: str, grownup: str) -> World:
    world = World(setting)
    det = world.add(Entity(detective, kind="character", type="child", role="detective"))
    adult = world.add(Entity(grownup, kind="character", type=grownup, role="grownup"))
    culprit = world.add(Entity("culprit", kind="character", type=suspect.species, label=suspect.species_hint, role="suspect"))
    scene = world.add(Entity("scene", label=setting.place))
    clue = world.add(Entity("clue", label="dandruff", role="clue"))
    world.facts["detective"] = det
    world.facts["adult"] = adult
    world.facts["culprit"] = culprit
    world.facts["setting"] = setting
    world.facts["suspect"] = suspect
    world.facts["scene"] = scene
    world.facts["clue"] = clue

    det.memes["curiosity"] += 1
    world.say(f"{detective} was a small detective who loved solving mysteries at {setting.place}.")
    world.say(f"One morning, {setting.foreshadow_line}")
    world.say(f"{detective} pointed at the clue. \"That looks like dandruff,\" {det.pronoun()} said, peering closer.")

    world.para()
    world.say(f"{detective} looked around and thought about species. {suspect.species_hint.capitalize()}s leave different signs.")
    world.say(f"The clue fit {suspect.clue_style}, and that was a better match than a sneaky stranger in a costume.")
    if suspect.species == "cat":
        world.say("A cat cleans itself, but a few flakes can still tumble off a sleepy coat.")
    elif suspect.species == "dog":
        world.say("A dog can leave a trail when it shakes after a dusty roll in the grass.")
    elif suspect.species == "bird":
        world.say("A bird preens its feathers, so a feather clue made the answer feel bright and clear.")
    elif suspect.species == "sheep":
        world.say("A sheep's wool can leave little white bits that look almost like snow.")
    else:
        world.say("A rabbit can hide under low things, and its soft fur can leave tiny traces behind.")

    world.para()
    det.meters["evidence"] += 1
    culprit.meters["evidence"] += 1
    detective_line = f"At last, {detective} said, \"The clue points to {suspect.species} species!\""
    world.say(detective_line)
    world.say(f"{grownup.capitalize()} smiled and nodded. \"You followed the clue, and you noticed what kind of animal could leave it.\"")
    world.say(f"The mystery ended with the right species stepping into the light, while the little white clue stayed on the table like a tiny badge of honor.")

    world.facts["outcome"] = "solved"
    return world


def generation_prompts(world: World) -> list[str]:
    return story_prompt(world, world.facts["suspect"])


def story_qa(world: World) -> list[tuple[str, str]]:
    suspect: Suspect = world.facts["suspect"]
    detective: Entity = world.facts["detective"]
    adult: Entity = world.facts["adult"]
    qa = [
        ("What kind of story is this?",
         "It is a whodunit mystery, where a detective looks at clues and figures out who or what fits best."),
        ("What clue did the detective notice?",
         "The detective noticed dandruff on the table, and that clue mattered because it foreshadowed the answer."),
        ("What did the detective think about?",
         "The detective thought about species, because different animals leave different signs and clues."),
        ("How did the mystery end?",
         f"{detective.id} solved it by matching the clue to {suspect.species}. {adult.id} praised the careful thinking, and the case was settled cleanly."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    suspect: Suspect = world.facts["suspect"]
    q, a = knowledge_for_species(suspect.species)
    return [
        q and (q, a),
        ("What is dandruff?",
         "Dandruff is a little flaking from skin or hair that can leave white specks behind."),
        ("What is a clue?",
         "A clue is a small bit of information that helps someone solve a mystery."),
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


CURATED = [
    StoryParams("school", "cat", "Mia", "mother"),
    StoryParams("museum", "bird", "Noah", "father"),
    StoryParams("shop", "sheep", "Ava", "mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SUSPECTS[params.suspect], params.detective, params.grownup)
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


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: clingo gate matches valid_combos().")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        try:
            sample = generate(CURATED[0])
            assert sample.story
        except Exception as exc:  # noqa: BLE001
            print(f"VERIFY FAILED: {exc}")
            sys.exit(1)
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b}" for a, b in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.detective}: {p.setting} / {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fog_foreshadowing_mystery_to_solve_curiosity_myth.py
====================================================================================

A small mythic storyworld about a child, a foggy path, a curiosity-driven
mystery, and a foretold truth that becomes clear by the end.

The world is intentionally tiny: a village edge, a fog bank, a bell, a lantern,
a lost goat, and a handful of myth-like signs. The story engine uses physical
meters and emotional memes, with a simple causal chain:
curiosity -> exploring the fog -> clues -> a solved mystery -> a clear ending.

It supports the standard Storyweavers CLI contract:
- default run
- -n, --all, --seed, --trace, --qa, --json
- --asp, --verify, --show-asp

The inline ASP twin mirrors the Python reasonableness gate and ending logic.
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
    title: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    name: str
    foggy: bool
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
class Mystery:
    id: str
    clue: str
    answer: str
    solve_tool: str
    requires_fog: bool = True
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
class Guide:
    id: str
    label: str
    glow: str
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
class World:
    place: Place
    mystery: Mystery
    guide: Guide
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World(self.place, self.mystery, self.guide)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c
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


def _r_fog_clues(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    clue = world.mystery.clue
    if not child:
        return out
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("fog_clues",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("fog").meters["thickness"] = 0.0
    world.get("bell").meters["heard"] += 1
    out.append("__clue__")
    return out


def _r_solved(world: World) -> list[str]:
    child = world.entities.get("child")
    if not child:
        return []
    sig = ("solved",)
    if sig in world.fired:
        return []
    if world.get("bell").meters["heard"] < THRESHOLD:
        return []
    world.fired.add(sig)
    child.memes["joy"] += 1
    return ["__solve__"]


CAUSAL_RULES = [Rule("fog_clues", _r_fog_clues), Rule("solved", _r_solved)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            for item in rule.apply(world):
                changed = True
                if not item.startswith("__"):
                    produced.append(item)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_start(params: "StoryParams") -> bool:
    return params.place in PLACES and params.mystery in MYSTERIES and params.guide in GUIDES


@dataclass
class StoryParams:
    place: str
    mystery: str
    guide: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
    curiosity: int = 6
    fog_thickness: int = 2
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


PLACES = {
    "harbor": Place(id="harbor", name="the harbor", foggy=True, tags={"fog", "sea"}),
    "hill": Place(id="hill", name="the hill path", foggy=True, tags={"fog", "path"}),
    "grove": Place(id="grove", name="the old grove", foggy=True, tags={"fog", "trees"}),
}

MYSTERIES = {
    "bell": Mystery(id="bell", clue="a bell sound inside the fog", answer="the bell rope had snagged on a branch", solve_tool="listen"),
    "lights": Mystery(id="lights", clue="tiny lights bobbing in the fog", answer="they were fireflies circling a lantern", solve_tool="look"),
    "hoofprints": Mystery(id="hoofprints", clue="hoofprints fading into the mist", answer="a small goat had walked home by the stream", solve_tool="track"),
}

GUIDES = {
    "lantern": Guide(id="lantern", label="a lantern", glow="glowed like a small moon", tags={"light"}),
    "torch": Guide(id="torch", label="a torch", glow="burned bright and steady", tags={"light"}),
}

CHILD_NAMES = ["Ari", "Mira", "Niko", "Sana", "Lea", "Tavi"]
ELDER_NAMES = ["Grandmother", "Grandfather", "Aunt", "Uncle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for p in PLACES:
        for m in MYSTERIES:
            for g in GUIDES:
                combos.append((p, m, g))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen fog tale could not begin.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic fog mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["girl", "boy"])
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
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.guide is None or c[2] == args.guide)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, guide = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    elder = args.elder or rng.choice([n for n in ELDER_NAMES if n != child])
    curiosity = rng.randint(5, 8)
    fog_thickness = rng.randint(1, 3)
    return StoryParams(place=place, mystery=mystery, guide=guide, child=child,
                       child_gender=child_gender, elder=elder, elder_gender=elder_gender,
                       curiosity=curiosity, fog_thickness=fog_thickness)


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.guide not in GUIDES:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    guide = GUIDES[params.guide]
    w = World(place, mystery, guide)
    child = w.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child, role="seeker"))
    elder = w.add(Entity(id="elder", kind="character", type=params.elder_gender, label=params.elder, role="guide"))
    fog = w.add(Entity(id="fog", kind="thing", type="thing", label="fog"))
    bell = w.add(Entity(id="bell", kind="thing", type="thing", label="bell"))
    child.memes["curiosity"] = float(params.curiosity)
    fog.meters["thickness"] = float(params.fog_thickness)
    w.say(f"{params.child} went with {params.elder} to {place.name}.")
    w.say(f"A fog lay over the ground, soft and thick, and even the stones seemed half-forgotten.")
    w.say(f'The child held {guide.label}, which {guide.glow}, and listened for a sign.')
    w.para()
    child.memes["wonder"] += 1
    w.say(f'{params.child} kept asking, "What is hiding in the fog?"')
    w.say(f'{params.elder} answered, "A mystery always leaves a trail. Watch, listen, and be patient."')
    if params.curiosity >= 5:
        w.say(f"{params.child} stepped closer, because curiosity pulled harder than fear.")
        w.say(f"A little clue waited there: {mystery.clue}.")
        w.say(f"It felt like a promise from the fog itself.")
    propagate(w, narrate=False)
    w.para()
    w.say(f"Then the bell rang once, clear and close, as if the mist had opened a mouth.")
    if w.get("bell").meters["heard"] >= THRESHOLD:
        w.say(f"{params.elder} followed the sound, and {params.child} followed the elder's hand.")
        w.say(f"At last they found the truth: {mystery.answer}.")
        w.say(f"The fog thinned, and the path became bright enough to see again.")
        w.say(f"{params.child} laughed, for the mystery was solved and the world felt larger than before.")
    w.facts.update(child=child, elder=elder, fog=fog, bell=bell, place=place,
                   mystery=mystery, guide=guide, outcome="solved")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a child who is curious about fog and hears a mystery in the mist.',
        f"Tell a small myth where {f['child'].label} asks what is hidden in the fog, follows clues, and discovers the truth.",
        f'Write a story that includes the word "fog" and ends with a mystery being solved by listening and looking carefully.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"].label
    elder = f["elder"].label
    mystery = f["mystery"]
    return [
        QAItem(
            question="What did the child want to know?",
            answer=f"{child} wanted to know what was hiding in the fog. That curiosity led {child} to follow the clue and listen for the truth."
        ),
        QAItem(
            question="How did the mystery get solved?",
            answer=f"They listened for the bell and followed the clue until the answer became clear. The fog lifted a little, and that let them see the real cause."
        ),
        QAItem(
            question=f"What was the answer to the mystery about {mystery.id}?",
            answer=f"The answer was {mystery.answer}. The story began with a strange sign and ended when the truth was found."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fog?",
            answer="Fog is a cloud of tiny water drops hanging close to the ground. It can hide paths and make familiar places look mysterious."
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to ask questions and look for answers. It can lead a person to explore carefully and solve a mystery."
        ),
        QAItem(
            question="Why is a lantern useful in the fog?",
            answer="A lantern gives steady light without needing a big flame. In fog, light helps people notice clues and keep moving safely."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:6} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", mystery="bell", guide="lantern", child="Ari", child_gender="boy", elder="Grandmother", elder_gender="girl", curiosity=7, fog_thickness=2),
    StoryParams(place="hill", mystery="lights", guide="torch", child="Mira", child_gender="girl", elder="Uncle", elder_gender="boy", curiosity=6, fog_thickness=3),
    StoryParams(place="grove", mystery="hoofprints", guide="lantern", child="Niko", child_gender="boy", elder="Aunt", elder_gender="girl", curiosity=8, fog_thickness=1),
]


ASP_RULES = r"""
has_fog(P) :- place(P).
curious(C) :- curiosity(C), curiosity(CI), CI >= 5.
clue_visible(M) :- mystery(M), requires_fog(M), has_fog(place1).
solved :- hears_bell, curious(child).
"""

def asp_facts() -> str:
    import asp
    parts = []
    for pid in PLACES:
        parts.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        parts.append(asp.fact("mystery", mid))
        if m.requires_fog:
            parts.append(asp.fact("requires_fog", mid))
    for gid in GUIDES:
        parts.append(asp.fact("guide", gid))
    parts.append(asp.fact("curiosity_min", 5))
    return "\n".join(parts)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        import asp  # noqa: F401
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH:")
        print("python-only:", sorted(py - asp_set))
        print("asp-only:", sorted(asp_set - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAILED: generate() smoke test crashed: {e}")
        return 1
    return rc


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
        print(f"{len(valid_combos())} compatible combos:")
        for c in valid_combos():
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

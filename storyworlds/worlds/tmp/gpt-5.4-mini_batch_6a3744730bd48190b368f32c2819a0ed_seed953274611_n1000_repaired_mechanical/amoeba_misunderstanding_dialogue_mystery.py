#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/amoeba_misunderstanding_dialogue_mystery.py
============================================================================

A tiny storyworld about a child detective, a small misunderstood amoeba, and a
mystery that ends with a gentle correction. The core shape is:

- a clue appears in a little lab or pond bowl,
- someone jumps to the wrong conclusion,
- a dialogue reveals the real cause,
- the final image proves the misunderstanding changed into understanding.

The world is intentionally small and child-facing. It models typed entities with
physical meters and emotional memes, uses a simple forward-chaining engine, and
includes an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

from storyworlds.results import QAItem, StoryError, StorySample  # eager import


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False
    living: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    setting: str
    suspect: str
    clue: str
    reveal: str
    name: str
    gender: str
    adult: str
    seed: Optional[int] = None
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


@dataclass
class Setting:
    id: str
    scene: str
    place_line: str
    clue_line: str
    has_water: bool = False
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


@dataclass
class Suspect:
    id: str
    label: str
    phrase: str
    movement: str
    size: str
    living: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Clue:
    id: str
    label: str
    phrase: str
    mystery_line: str
    truth_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Reveal:
    id: str
    label: str
    explanation: str
    action_line: str
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
        return clone
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


def _r_worry(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.memes["suspicion"] >= THRESHOLD and ("worry", ent.id) not in world.fired:
            world.fired.add(("worry", ent.id))
            ent.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_bubble(world: World) -> list[str]:
    out = []
    amoeba = world.entities.get("amoeba")
    if not amoeba:
        return out
    if amoeba.meters["glimmer"] >= THRESHOLD and ("bubble", "amoeba") not in world.fired:
        world.fired.add(("bubble", "amoeba"))
        world.get("jar").meters["bubbles"] += 1
        out.append("Tiny bubbles shimmered in the jar.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("bubble", _r_bubble)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            for s in rule.apply(world):
                changed = True
                if not s.startswith("__"):
                    produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("detective").memes["suspicion"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": sim.get("detective").memes["worry"],
        "bubbles": sim.get("jar").meters["bubbles"],
    }


def _intro(world: World, kid: Entity, setting: Setting, clue: Clue) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"On a quiet afternoon, {kid.id} found {setting.scene}. "
        f"{setting.place_line}"
    )
    world.say(
        f'{kid.id} pointed at the odd clue and whispered, "{clue.mystery_line}"'
    )


def _suspect(world: World, kid: Entity, suspect: Suspect, clue: Clue) -> None:
    kid.memes["suspicion"] += 1
    world.say(
        f'"That must be the culprit," {kid.id} said. "It looks like {suspect.phrase}."'
    )
    world.say(
        f'But the little {suspect.label} only {suspect.movement}. {clue.truth_line}'
    )


def _dialogue(world: World, kid: Entity, adult: Entity, suspect: Suspect, clue: Clue) -> None:
    pred = predict(world)
    adult.memes["calm"] += 1
    if pred["worry"] >= THRESHOLD:
        world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"{kid.id}," said {adult.id}, "what makes you think the {suspect.label} did it?"'
    )
    world.say(
        f'"Because it was right there," {kid.id} answered. "{clue.phrase} was all strange!"'
    )
    world.say(
        f'"Look closer," {adult.id} said. "Sometimes a mystery is only a misunderstanding."'
    )


def _reveal(world: World, kid: Entity, adult: Entity, suspect: Suspect, reveal: Reveal) -> None:
    amoeba = world.get("amoeba")
    amoeba.meters["glimmer"] += 1
    propagate(world, narrate=True)
    world.say(
        f'{adult.id} held up the glass jar and smiled. "{reveal.explanation}"'
    )
    world.say(
        f'Then {adult.id} showed {kid.id} {reveal.action_line}.'
    )
    kid.memes["understanding"] += 1
    kid.memes["relief"] += 1
    world.say(
        f'{kid.id} blinked, then grinned. "Oh! The {suspect.label} was not sneaky at all," '
        f'{kid.id} said. "It was just {reveal.label}."'
    )


def _ending(world: World, kid: Entity, suspect: Suspect, clue: Clue) -> None:
    world.say(
        f"At the end, the jar sat still in the sunlight, and the {suspect.label} "
        f"drifted gently through it like a tiny clear star."
    )
    world.say(
        f"{kid.id} wrote the answer on a paper card: {clue.truth_line} The mystery was solved."
    )


SETTINGS = {
    "pond_lab": Setting(
        id="pond_lab",
        scene="a small pond water tray on the table",
        place_line="A magnifying glass rested beside a glass jar, and sunlight fell across the desk.",
        clue_line="something swirled in the water",
        has_water=True,
    ),
    "window_sill": Setting(
        id="window_sill",
        scene="a glass jar by the window",
        place_line="A notebook, a spoon, and a bright lamp made the sill look like a tiny detective office.",
        clue_line="a trail of water spots",
        has_water=True,
    ),
}

SUSPECTS = {
    "amoeba": Suspect(
        id="amoeba",
        label="amoeba",
        phrase="a sneaky speck",
        movement="floated and stretched",
        size="tiny",
        living=True,
        tags={"amoeba", "living", "water"},
    ),
    "blob": Suspect(
        id="blob",
        label="blob",
        phrase="a jelly blob",
        movement="wobbled and turned",
        size="tiny",
        living=False,
        tags={"water"},
    ),
}

CLUES = {
    "swirl": Clue(
        id="swirl",
        label="swirl",
        phrase="the swirl in the water",
        mystery_line="Who made that swirl?",
        truth_line="the swirl came from the amoeba drifting around in the jar",
        tags={"swirl", "water", "mystery"},
    ),
    "spots": Clue(
        id="spots",
        label="spots",
        phrase="the water spots on the glass",
        mystery_line="Why are there little spots all over the glass?",
        truth_line="the spots were just drops from the water tray",
        tags={"spots", "water", "mystery"},
    ),
}

REVEALS = {
    "light": Reveal(
        id="light",
        label="a patch of sunlight",
        explanation="The amoeba was only moving toward the light, not sneaking around.",
        action_line="how the amoeba drifted toward the sunny side of the jar",
        tags={"light", "answer"},
    ),
    "food": Reveal(
        id="food",
        label="a tiny bit of food dust",
        explanation="The amoeba was reaching for food, not making trouble.",
        action_line="how the food dust sat at one edge of the jar",
        tags={"food", "answer"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for su in SUSPECTS:
                if su == "amoeba" and CLUES[c].id == "swirl":
                    combos.append((s, su, c))
    return combos


def explain_rejection(setting: Setting, suspect: Suspect, clue: Clue) -> str:
    return (
        f"(No story: this setup does not create a proper mystery. "
        f"Try the amoeba with the swirl clue, where a misunderstanding can be corrected.)"
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS.get(params.setting)
    suspect = SUSPECTS.get(params.suspect)
    clue = CLUES.get(params.clue)
    reveal = REVEALS.get(params.reveal)
    if not setting or not suspect or not clue or not reveal:
        raise StoryError("(Invalid parameters.)")
    world = World(setting)
    detective = world.add(Entity(id=params.name, kind="character", type=params.gender, role="detective"))
    adult = world.add(Entity(id=params.adult, kind="character", type="adult", role="helper", type="mother" if params.adult.lower() in {"mom", "mother"} else "father"))
    jar = world.add(Entity(id="jar", type="thing", label="jar"))
    amoeba = world.add(Entity(id="amoeba", type="living", label="amoeba", living=True))
    amoeba.meters["glimmer"] = 0.0
    world.facts.update(setting=setting, suspect=suspect, clue=clue, reveal=reveal, detective=detective, adult=adult, jar=jar, amoeba=amoeba)
    _intro(world, detective, setting, clue)
    world.para()
    _suspect(world, detective, suspect, clue)
    world.para()
    _dialogue(world, detective, adult, suspect, clue)
    world.para()
    _reveal(world, detective, adult, suspect, reveal)
    world.para()
    _ending(world, detective, suspect, clue)
    world.facts["outcome"] = "solved"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the word "amoeba" and a misunderstanding, then resolves with dialogue.',
        f"Tell a short detective story where {f['detective'].id} thinks the amoeba is suspicious, but an adult explains the real answer.",
        f"Write a mystery with a small clue in a jar, a wrong guess, and a calm conversation that solves the puzzle.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    adult = f["adult"]
    suspect = f["suspect"]
    clue = f["clue"]
    reveal = f["reveal"]
    return [
        ("What kind of story is this?",
         f"It is a little mystery about {detective.id}, a clue in water, and an amoeba that was misunderstood. The story begins with a puzzling clue and ends when the real cause is explained."),
        (f"Why did {detective.id} think the amoeba was the culprit?",
         f"{detective.id} saw the strange swirl and guessed wrong because it looked secret and suspicious. The clue was confusing, so the first idea was a misunderstanding."),
        ("How did the characters solve the mystery?",
         f"They talked it through. {adult.id} explained that the amoeba was only {reveal.label.lower()}, and then the odd clue made sense."),
        ("How did the story end?",
         f"It ended with the amoeba drifting calmly in the jar and the mystery written down as solved. The wrong guess changed into a clear answer."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an amoeba?",
         "An amoeba is a tiny living thing that lives in water. It can drift and change shape as it moves."),
        ("What does a detective do?",
         "A detective looks for clues and asks questions to solve a mystery. Detectives try not to guess too fast."),
        ("What is a misunderstanding?",
         "A misunderstanding happens when someone thinks the wrong thing at first. Talking carefully can help fix it."),
        ("What helps solve a mystery?",
         "Clues, careful looking, and clear dialogue help solve a mystery. When people explain what they saw, the answer becomes easier to find."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
selected_story(S,U,C,R) :- setting(S), suspect(U), clue(C), reveal(R), valid(S,U,C).
valid(S, amoeba, swirl) :- setting(S), clue(swirl).
misunderstanding(U) :- suspect(U), U = amoeba.
dialogue_turn :- setting(_), suspect(amoeba), clue(swirl), reveal(_).
solved :- misunderstanding(amoeba), dialogue_turn.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for u in SUSPECTS:
        lines.append(asp.fact("suspect", u))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for r in REVEALS:
        lines.append(asp.fact("reveal", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("  only python:", sorted(py - cl))
        print("  only ASP:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, suspect=None, clue=None, reveal=None, name=None, gender=None, adult=None), random.Random(7)))
        assert sample.story
        print("OK: smoke test story generation works.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny amoeba mystery world with dialogue and misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl", "mother", "father"])
    ap.add_argument("--adult")
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
    if args.suspect and args.suspect != "amoeba":
        raise StoryError("(No story: this world is built around an amoeba misunderstanding.)")
    if args.clue and args.clue != "swirl":
        raise StoryError("(No story: the clue must be a swirl so the misunderstanding can be resolved.)")
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combos.)")
    setting, suspect, clue = rng.choice(combos)
    reveal = args.reveal or rng.choice(sorted(REVEALS))
    name = args.name or rng.choice(["Mina", "Noah", "Lia", "Ezra"])
    gender = args.gender or rng.choice(["boy", "girl"])
    adult = args.adult or rng.choice(["Mom", "Dad"])
    return StoryParams(setting=setting, suspect=suspect, clue=clue, reveal=reveal, name=name, gender=gender, adult=adult)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(setting="pond_lab", suspect="amoeba", clue="swirl", reveal="light", name="Mina", gender="girl", adult="Mom"),
    StoryParams(setting="window_sill", suspect="amoeba", clue="swirl", reveal="food", name="Noah", gender="boy", adult="Dad"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

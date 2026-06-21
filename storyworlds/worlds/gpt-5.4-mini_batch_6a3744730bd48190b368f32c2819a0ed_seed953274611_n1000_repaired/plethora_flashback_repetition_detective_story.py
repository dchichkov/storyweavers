#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/plethora_flashback_repetition_detective_story.py
=================================================================================

A tiny detective story world built from the seed words:
- plethora
- flashback
- repetition

The domain is child-friendly and classical: a small mystery, a careful search,
a flashback that reveals an earlier overlooked detail, repeated suspecting of
the wrong thing, and a tidy resolution proving what changed.

The world model tracks typed entities with physical meters and emotional memes,
and the prose is driven by simulated state rather than a frozen template.
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
SENSE_MIN = 2


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Mystery:
    id: str
    setting: str
    missing: str
    hiding_place: str
    clue: str
    red_herring: str
    repetition_line: str
    flashback_line: str
    solution_line: str
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
class Suspect:
    id: str
    label: str
    innocence: str
    alibi: str
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
class Helper:
    id: str
    label: str
    phrase: str
    tool: str
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


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    key = ("relief", "missing")
    if key in world.fired:
        return out
    if world.get("trinket").meters["found"] >= THRESHOLD:
        world.fired.add(key)
        world.get("hero").memes["relief"] += 1
        world.get("owner").memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                out.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def glance_flashback(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"As {hero.id} stared at the empty shelf, {hero.pronoun()} had a flashback: "
        f"{mystery.flashback_line}"
    )


def repeat_suspecting(world: World, hero: Entity, suspect: Entity, mystery: Mystery) -> None:
    hero.memes["certainty"] += 1
    world.say(
        f"{hero.id} checked {suspect.label} again, and then checked {suspect.label} again. "
        f"{mystery.repetition_line}"
    )
    world.say(
        f'"Maybe it was {suspect.label} after all," {hero.id} muttered, '
        f'but the clue still did not fit.'
    )


def reveal(world: World, hero: Entity, helper: Entity, suspect: Entity, mystery: Mystery) -> None:
    trinket = world.get("trinket")
    trinket.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.label} listened, looked at the clue, and opened the little box behind the sofa. "
        f"There was the missing {mystery.missing} at last."
    )
    world.say(
        f"{mystery.solution_line} {suspect.reveal}"
    )
    world.say(
        f'{hero.id} grinned. "{mystery.missing.capitalize()} found!" {hero.pronoun()} said.'
    )


def ending(world: World, hero: Entity, owner: Entity, mystery: Mystery) -> None:
    trinket = world.get("trinket")
    owner.memes["joy"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{owner.label_word.capitalize()} laughed and hugged {hero.id}. "
        f"The missing {mystery.missing} was back where it belonged, and the room felt calm again."
    )
    world.say(
        f"This time, the shelf was neat, the clue made sense, and the detective had a true answer."
    )


def tell(mystery: Mystery, suspect: Suspect, helper: Helper) -> World:
    world = World()
    hero = world.add(Entity(id="Nia", kind="character", type="girl", role="detective", traits=["curious"]))
    owner = world.add(Entity(id="Grandpa", kind="character", type="man", role="owner", label="Grandpa"))
    room = world.add(Entity(id="room", type="room", label=mystery.setting))
    trinket = world.add(Entity(id="trinket", type="thing", label=mystery.missing))
    box = world.add(Entity(id="box", type="thing", label="little box"))
    world.add(Entity(id="suspect", kind="character", type="boy", role="suspect", label=suspect.label))
    world.add(Entity(id="helper", kind="character", type="girl", role="helper", label=helper.label))

    hero.memes["worry"] += 1
    owner.memes["worry"] += 1
    world.facts["mystery"] = mystery
    world.facts["suspect"] = suspect
    world.facts["helper"] = helper
    world.facts["hero"] = hero
    world.facts["owner"] = owner

    world.say(
        f"In {mystery.setting}, something was missing: the {mystery.missing}. "
        f"There was a plethora of clues on the table, but none of them solved the case yet."
    )
    world.say(
        f"{hero.id} took the case seriously. {hero.id} looked at the clue, the shelf, and the empty chair."
    )

    world.para()
    repeat_suspecting(world, hero, world.get("suspect"), mystery)
    glance_flashback(world, hero, mystery)
    world.say(
        f"{mystery.clue} sat there like a tiny promise."
    )

    world.para()
    reveal(world, hero, world.get("helper"), world.get("suspect"), mystery)
    ending(world, hero, owner, mystery)

    world.facts["outcome"] = "solved"
    world.facts["trinket_found"] = True
    return world


MYSTERIES = {
    "library": Mystery(
        id="library",
        setting="the quiet library corner",
        missing="silver bookmark",
        hiding_place="behind the sofa",
        clue="A crumb trail and a bent page",
        red_herring="the cat",
        repetition_line="Each time, the cat only blinked and yawned.",
        flashback_line="she remembered Grandpa reading by the sofa and setting something small on the cushion.",
        solution_line="The clue pointed to a place people often forget to look.",
        tags={"library", "flashback", "repetition", "plethora"},
    ),
    "kitchen": Mystery(
        id="kitchen",
        setting="the sunny kitchen",
        missing="blue spoon",
        hiding_place="inside the bread box",
        clue="A sticky ring on the counter",
        red_herring="the dog",
        repetition_line="Each time, the dog wagged his tail and looked innocent.",
        flashback_line="she remembered making soup and placing the spoon near the bread box.",
        solution_line="The answer was simple once the flashback came back.",
        tags={"kitchen", "flashback", "repetition", "plethora"},
    ),
    "classroom": Mystery(
        id="classroom",
        setting="the little classroom",
        missing="red marker",
        hiding_place="under a stack of paper",
        clue="One red dot on a scrap of paper",
        red_herring="the janitor's cart",
        repetition_line="Again and again, the cart squeaked by with nothing suspicious at all.",
        flashback_line="she remembered drawing a sign and resting the marker on the papers.",
        solution_line="The clue and the memory matched perfectly.",
        tags={"classroom", "flashback", "repetition", "plethora"},
    ),
}

SUSPECTS = {
    "cat": Suspect(id="cat", label="the cat", innocence="innocent", alibi="was sleeping all morning", reveal="The cat never touched the shelf.", tags={"cat"}),
    "dog": Suspect(id="dog", label="the dog", innocence="innocent", alibi="was outside in the yard", reveal="The dog only watched from the doorway.", tags={"dog"}),
    "cart": Suspect(id="cart", label="the cart", innocence="innocent", alibi="was parked by the sink", reveal="The cart just rattled by; it did not hide the missing thing.", tags={"cart"}),
}

HELPERS = {
    "friend": Helper(id="friend", label="Mina", phrase="a careful friend", tool="listening ears", tags={"friend"}),
    "teacher": Helper(id="teacher", label="Ms. Bell", phrase="a patient teacher", tool="a quiet key ring", tags={"teacher"}),
    "grandpa": Helper(id="grandpa", label="Grandpa", phrase="a wise grown-up", tool="a flashlight", tags={"grandpa"}),
}


@dataclass
class StoryParams:
    mystery: str
    suspect: str
    helper: str
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


CURATED = [
    StoryParams(mystery="library", suspect="cat", helper="grandpa"),
    StoryParams(mystery="kitchen", suspect="dog", helper="friend"),
    StoryParams(mystery="classroom", suspect="cart", helper="teacher"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for m in MYSTERIES:
        for s in SUSPECTS:
            for h in HELPERS:
                combos.append((m, s, h))
    return combos


def generation_prompts(world: World) -> list[str]:
    m = world.facts["mystery"]
    return [
        f'Write a child-friendly detective story that includes the word "plethora" and uses a flashback and repetition.',
        f"Tell a mystery story where Nia searches for the missing {m.missing}, suspects the wrong thing more than once, then remembers an earlier moment and solves it.",
        f"Write a short detective tale with a clue, a flashback, and repeated checking before the answer is found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    s: Suspect = world.facts["suspect"]
    h: Helper = world.facts["helper"]
    return [
        QAItem(
            question="What was missing in the story?",
            answer=f"The missing thing was the {m.missing}. Nia searched for it carefully until the clue led her to it.",
        ),
        QAItem(
            question="Why was there repetition in the story?",
            answer=f"Nia checked {s.label} again and again because she was not sure yet. The repeated checking showed her thinking hard before the answer became clear.",
        ),
        QAItem(
            question="How did the flashback help?",
            answer=f"The flashback reminded Nia of an earlier moment when the missing {m.missing} had been set down. That memory pointed her toward the right hiding place.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{h.label} helped open the little box, and the missing {m.missing} was found at last. After that, the room felt calm and the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier. It helps explain a clue or a decision in the present.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means a story repeats a word, action, or idea more than once. Writers use it to make something feel important or to show a character thinking hard.",
        ),
        QAItem(
            question="What does plethora mean?",
            answer="Plethora means a lot of something. If there is a plethora of clues, there are many clues to look at.",
        ),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell_story(params: StoryParams) -> World:
    mystery = MYSTERIES[params.mystery]
    suspect = SUSPECTS[params.suspect]
    helper = HELPERS[params.helper]
    return tell(mystery, suspect, helper)


def tell(mystery: Mystery, suspect: Suspect, helper: Helper) -> World:
    world = World()
    hero = world.add(Entity(id="Nia", kind="character", type="girl", role="detective"))
    owner = world.add(Entity(id="Grandpa", kind="character", type="man", role="owner", label="Grandpa"))
    suspect_ent = world.add(Entity(id="suspect", kind="character", type="boy", role="suspect", label=suspect.label))
    helper_ent = world.add(Entity(id="helper", kind="character", type="girl", role="helper", label=helper.label))
    world.add(Entity(id="trinket", type="thing", label=mystery.missing))
    world.add(Entity(id="box", type="thing", label="little box"))

    hero.memes["worry"] += 1
    owner.memes["worry"] += 1
    world.facts.update(mystery=mystery, suspect=suspect, helper=helper, hero=hero, owner=owner)

    world.say(
        f"In {mystery.setting}, something was missing: the {mystery.missing}. "
        f"There was a plethora of clues on the table, but none of them solved the case yet."
    )
    world.say(
        f"{hero.id} began like a true detective, peering at the clue and the empty shelf."
    )
    world.para()
    repeat_suspecting(world, hero, suspect_ent, mystery)
    glance_flashback(world, hero, mystery)
    world.para()
    reveal(world, hero, helper_ent, suspect_ent, mystery)
    ending(world, hero, owner, mystery)
    world.facts["outcome"] = "solved"
    return world


def repeat_suspecting(world: World, hero: Entity, suspect: Entity, mystery: Mystery) -> None:
    hero.memes["certainty"] += 1
    world.say(
        f"{hero.id} checked {suspect.label} again, and then checked {suspect.label} again. "
        f"{mystery.repetition_line}"
    )


def glance_flashback(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"Then a flashback arrived in {hero.id}'s mind: {mystery.flashback_line}"
    )


def reveal(world: World, hero: Entity, helper: Entity, suspect: Entity, mystery: Mystery) -> None:
    world.get("trinket").meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label} listened, looked again, and opened the little box behind the sofa. "
        f"There was the missing {mystery.missing} at last."
    )
    world.say(
        f"{mystery.solution_line} {suspect.reveal}"
    )
    world.say(f'"{mystery.missing.capitalize()} found!" {hero.id} said with a big smile.')


def ending(world: World, hero: Entity, owner: Entity, mystery: Mystery) -> None:
    hero.memes["joy"] += 1
    owner.memes["joy"] += 1
    world.say(
        f"{owner.label_word.capitalize()} laughed and hugged {hero.id}. "
        f"The {mystery.missing} was back where it belonged, and the detective's notes finally made sense."
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("(Invalid mystery choice.)")
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("(Invalid suspect choice.)")
    if args.helper and args.helper not in HELPERS:
        raise StoryError("(Invalid helper choice.)")
    choices = [c for c in valid_combos()
               if (args.mystery is None or c[0] == args.mystery)
               and (args.suspect is None or c[1] == args.suspect)
               and (args.helper is None or c[2] == args.helper)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    mystery, suspect, helper = rng.choice(sorted(choices))
    return StoryParams(mystery=mystery, suspect=suspect, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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


ASP_RULES = r"""
missing_found :- found(trinket).
solved :- missing_found.
plethora_clue :- clue_count(N), N >= 3.
flashback_used :- uses(flashback).
repetition_used :- uses(repetition).
valid_story(M, S, H) :- mystery(M), suspect(S), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_count", 3))
        lines.append(asp.fact("uses", "flashback"))
        lines.append(asp.fact("uses", "repetition"))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and python valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world with flashback and repetition.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--helper", choices=HELPERS)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible mystery stories:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.mystery} / {p.suspect} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

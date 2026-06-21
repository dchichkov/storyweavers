#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bravery_temporary_lesson_learned_sound_effects_flashback.py
==========================================================================================

A tiny whodunit-style storyworld about a child detective, a temporary disguise,
and a surprising lesson learned. The model keeps the world small and concrete:
typed entities carry physical meters and emotional memes, a simple causal engine
drives the turn, and the ending proves what changed.

Premise
-------
A child finds a clue, suspects the wrong culprit, then bravely follows the
sound effects and a flashback to uncover what really happened. The solution is
temporary, the lesson is lasting.

This world includes the seed words:
- bravery
- temporary

And the requested narrative instruments:
- Lesson Learned
- Sound Effects
- Flashback
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
REQUIRED_WORDS = ("bravery", "temporary")


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
class Clue:
    id: str
    label: str
    sound: str
    location: str
    evidence: str
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
    alibi: str
    sound: str
    temp_change: str
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
class Reveal:
    id: str
    label: str
    method: str
    proof: str
    lesson: str
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
    clue: str
    suspect: str
    reveal: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
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
        w.facts = copy.deepcopy(self.facts)
        return w


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


def _r_nervous(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["trouble"] >= THRESHOLD and ("nervous", "hero") not in world.fired:
        world.fired.add(("nervous", "hero"))
        hero.memes["fear"] += 1
        out.append("__narrate__")
    return out


def _r_relieved(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    if helper.memes["helped"] >= THRESHOLD and ("relieved", "helper") not in world.fired:
        world.fired.add(("relieved", "helper"))
        helper.memes["pride"] += 1
        out.append("__narrate__")
    return out


CAUSAL_RULES = [Rule("nervous", _r_nervous), Rule("relieved", _r_relieved)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def flashback(world: World, hero: Entity, clue: Clue, suspect: Suspect) -> None:
    hero.memes["memory"] += 1
    world.say(
        f"Then came a flashback. {hero.id} remembered {suspect.alibi} and the tiny "
        f"{suspect.sound} sound from earlier: {clue.sound}."
    )
    world.say(
        f"The memory clicked into place like a puzzle piece. The clue had not been a "
        f"crime at all; it had been a {clue.label} left near {clue.location}."
    )


def sound_effects(world: World, clue: Clue, suspect: Suspect) -> None:
    world.say(
        f"Outside the door, there went {clue.sound}... {suspect.sound}... {clue.sound}!"
    )
    world.say(
        f"Each sound pointed somewhere new, and the little detective followed the trail."
    )


def suspect_scene(world: World, hero: Entity, helper: Entity, suspect: Suspect, clue: Clue) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} took a brave breath of bravery and decided to ask hard questions. "
        f"{helper.id} stayed close, because the hallway felt too quiet."
    )
    world.say(
        f'"{clue.label} is missing," {hero.id} said, eyeing {suspect.label}. '
        f'"That looks suspicious."'
    )
    world.say(
        f"{suspect.label_word if hasattr(suspect, 'label_word') else suspect.label} looked odd, "
        f"but only for a temporary moment."
    )


def reveal_truth(world: World, hero: Entity, helper: Entity, suspect: Suspect, reveal: Reveal, clue: Clue) -> None:
    helper.memes["helped"] += 1
    world.say(
        f"{helper.id} lifted the {suspect.label} and showed the {reveal.method}. "
        f"Sure enough, {reveal.proof}."
    )
    world.say(
        f"{clue.label} was not stolen. It had simply been used for a temporary disguise "
        f"during the game."
    )
    world.say(
        f"That was the whole mystery: a small trick, a big worry, and a simple explanation."
    )


def lesson(world: World, hero: Entity, helper: Entity, reveal: Reveal, clue: Clue) -> None:
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"Lesson learned: if something looks strange, look again before jumping to a guess."
    )
    world.say(
        f"{hero.id} smiled, proud of {hero.pronoun('possessive')} bravery, and promised to "
        f"save big conclusions for after all the clues had spoken."
    )
    world.say(
        f"In the end, {clue.label} was back where it belonged, and the mystery was solved."
    )


def tell(clue: Clue, suspect: Suspect, reveal: Reveal,
         hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str,
         parent_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="detective"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    clue_ent = world.add(Entity(id="clue", type="thing", label=clue.label))
    suspect_ent = world.add(Entity(id="suspect", type="thing", label=suspect.label))

    hero.id = hero_name
    helper.id = helper_name

    hero.memes["bravery"] = 1.0
    helper.memes["worry"] = 1.0
    clue_ent.meters["missing"] = 1.0
    suspect_ent.attrs["sound"] = suspect.sound
    world.facts["clue"] = clue
    world.facts["suspect"] = suspect
    world.facts["reveal"] = reveal
    world.facts["parent"] = parent
    world.facts["hero"] = hero
    world.facts["helper"] = helper

    world.say(
        f"At the end of a quiet afternoon, {hero_name} noticed that the {clue.label} was gone. "
        f"{helper_name} gasped, and {parent.label_word} frowned at the suspicious silence."
    )
    world.say(
        f"It was a whodunit kind of day, the kind where every little noise could matter."
    )

    world.para()
    suspect_scene(world, hero, helper, suspect, clue)
    sound_effects(world, clue, suspect)

    world.para()
    flashback(world, hero, clue, suspect)
    reveal_truth(world, hero, helper, suspect, reveal, clue)
    lesson(world, hero, helper, reveal, clue)

    clue_ent.meters["missing"] = 0.0
    clue_ent.meters["found"] = 1.0
    hero.memes["peace"] += 1
    helper.memes["peace"] += 1
    parent.memes["approval"] += 1

    world.facts.update(
        story="whodunit",
        solved=True,
        clue_found=True,
        temporary=True,
        bravery=hero.memes["bravery"],
    )
    return world


CLUES = {
    "cookie": Clue(
        id="cookie",
        label="cookie",
        sound="crunch",
        location="the cookie jar",
        evidence="there was a trail of crumbs",
        tags={"food", "crumbs", "sound"},
    ),
    "lantern": Clue(
        id="lantern",
        label="lantern",
        sound="clink",
        location="the porch",
        evidence="the lantern had been moved",
        tags={"light", "metal", "sound"},
    ),
    "shoe": Clue(
        id="shoe",
        label="shoe",
        sound="tap-tap",
        location="the hallway",
        evidence="there were tiny shoe marks",
        tags={"footsteps", "hallway", "sound"},
    ),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the cat",
        alibi="the cat had been asleep on the rug",
        sound="mrrp",
        temp_change="a temporary disguise",
        tags={"pet", "sound"},
    ),
    "brother": Suspect(
        id="brother",
        label="the brother",
        alibi="the brother had been building a tower in the next room",
        sound="thump",
        temp_change="a temporary costume",
        tags={"family", "sound"},
    ),
    "wind": Suspect(
        id="wind",
        label="the open window",
        alibi="the window had blown a paper napkin across the room",
        sound="whoosh",
        temp_change="a temporary breeze",
        tags={"weather", "sound"},
    ),
}

REVEALS = {
    "mask": Reveal(
        id="mask",
        label="mask",
        method="a little party mask",
        proof="the missing clue was tucked behind it",
        lesson="look again before accusing",
        tags={"mask", "temporary"},
    ),
    "box": Reveal(
        id="box",
        label="box",
        method="an upside-down cardboard box",
        proof="the clue was sitting underneath the box",
        lesson="listen carefully to the room",
        tags={"box", "temporary"},
    ),
    "scarf": Reveal(
        id="scarf",
        label="scarf",
        method="a scarf tied too loosely",
        proof="the clue had snagged on the scarf for a moment",
        lesson="not every odd thing is a theft",
        tags={"scarf", "temporary"},
    ),
}

GIRL_NAMES = ["Mia", "Nina", "Tara", "Lina", "Ruby", "Sofia", "Pia"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Leo", "Arlo", "Finn", "Eli"]
PARENT_TYPES = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for c in CLUES:
        for s in SUSPECTS:
            for r in REVEALS:
                combos.append((c, s, r))
    return combos


def explain_rejection(_: object = None) -> str:
    return "(No story: this world is always reasonable, so there is no rejected combo.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny whodunit with bravery, temporary, sound effects, flashback, and a lesson learned."
    )
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
              if (args.clue is None or c[0] == args.clue)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.reveal is None or c[2] == args.reveal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    clue, suspect, reveal = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    hero = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_gender = "boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl"
    helper = rng.choice(BOY_NAMES if helper_gender == "boy" else GIRL_NAMES)
    if helper == hero:
        helper = rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != hero])
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(
        clue=clue,
        suspect=suspect,
        reveal=reveal,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if params.reveal not in REVEALS:
        raise StoryError("Unknown reveal.")
    world = tell(
        CLUES[params.clue],
        SUSPECTS[params.suspect],
        REVEALS[params.reveal],
        params.hero, params.hero_gender,
        params.helper, params.helper_gender,
        params.parent,
    )
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue"]
    suspect: Suspect = f["suspect"]
    return [
        f'Write a whodunit for a young child that includes the word "bravery" and the clue "{clue.label}".',
        f"Tell a mystery story where the sound effects {clue.sound} and {suspect.sound} lead to a flashback and a lesson learned.",
        f'Write a short mystery with the word "temporary" in it, where the wrong suspect looks guilty at first but is cleared by the end.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue: Clue = f["clue"]
    suspect: Suspect = f["suspect"]
    reveal: Reveal = f["reveal"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    parent: Entity = f["parent"]
    return [
        ("What kind of story is this?",
         "It is a whodunit mystery, so it starts with a small puzzle and ends when the truth comes out."),
        (f"What did {hero.id} show?",
         f"{hero.id} showed bravery and kept asking questions instead of giving up."),
        (f"Why did {hero.id} think {suspect.label} was suspicious?",
         f"{suspect.label} made a strange sound and the clue seemed to be missing. That made the scene look suspicious for a little while."),
        ("What changed the detective's mind?",
         f"A flashback did. {hero.id} remembered the earlier sound effects and realized the clue was only hidden for a temporary moment."),
        ("How was the mystery solved?",
         f"{helper.id} used {reveal.method} and the clue was found right away. Then everyone saw it had not been stolen at all."),
        ("What lesson was learned?",
         f"The lesson learned was to look again before guessing. The story ended with the clue back where it belonged and the wrong worry gone."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = f["clue"]
    suspect: Suspect = f["suspect"]
    reveal: Reveal = f["reveal"]
    items: list[QAItem] = []
    if "sound" in clue.tags:
        items.append(QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help you hear the story in your head, like crunch, clink, or whoosh. They make the scene feel lively and clear.",
        ))
    if "temporary" in reveal.tags or "temporary" in suspect.tags:
        items.append(QAItem(
            question="What does temporary mean?",
            answer="Temporary means it does not last forever. It is only for a short time before things change back.",
        ))
    items.append(QAItem(
        question="What is a flashback?",
        answer="A flashback is when the story jumps back to something that happened earlier. It helps the reader understand a clue or a memory.",
    ))
    return items


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(C,S,R) :- clue(C), suspect(S), reveal(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for r in REVEALS:
        lines.append(asp.fact("reveal", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import contextlib
    import io
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP parity failed.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(clue=None, suspect=None, reveal=None, parent=None), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as exc:
        print(f"MISMATCH: smoke test failed: {exc}")
        rc = 1
    if rc == 0:
        print("OK: ASP parity and story smoke test passed.")
    return rc


CURATED = [
    StoryParams(clue="cookie", suspect="cat", reveal="mask", hero="Mia", hero_gender="girl", helper="Owen", helper_gender="boy", parent="mother"),
    StoryParams(clue="lantern", suspect="wind", reveal="box", hero="Theo", hero_gender="boy", helper="Nina", helper_gender="girl", parent="father"),
    StoryParams(clue="shoe", suspect="brother", reveal="scarf", hero="Ruby", hero_gender="girl", helper="Ben", helper_gender="boy", parent="mother"),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = f["clue"]
    suspect: Suspect = f["suspect"]
    reveal: Reveal = f["reveal"]
    items: list[QAItem] = []
    if "sound" in clue.tags:
        items.append(QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help you hear the story in your head, like crunch, clink, or whoosh. They make the scene feel lively and clear.",
        ))
    items.append(QAItem(
        question="What does temporary mean?",
        answer="Temporary means it does not last forever. It is only for a short time before things change back.",
    ))
    items.append(QAItem(
        question="What is a flashback?",
        answer="A flashback is when the story jumps back to something that happened earlier. It helps the reader understand a clue or a memory.",
    ))
    return items


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
        print(f"{len(asp_valid_combos())} valid combos")
        for c in asp_valid_combos():
            print(c)
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(rng_base + i))
            params.seed = rng_base + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.clue} / {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

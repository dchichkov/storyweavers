#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/kennel_use_flashback_suspense_sound_effects_whodunit.py
=======================================================================================

A small, self-contained storyworld in a whodunit style.

Premise:
- A child visits a kennel.
- A favorite puppy has vanished from its pen.
- The child follows sound clues, a flashback, and a careful reveal.
- The story ends with the mystery solved and the kennel made calm again.

The world is intentionally tiny, concrete, and state-driven:
- entities have physical meters and emotional memes
- clues accumulate into deductions
- the ending proves what changed

Run:
    python storyworlds/worlds/gpt-5.4-mini/kennel_use_flashback_suspense_sound_effects_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/kennel_use_flashback_suspense_sound_effects_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/kennel_use_flashback_suspense_sound_effects_whodunit.py --verify
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
    traits: list[str] = field(default_factory=list)
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
class Setting:
    id: str
    place: str
    kennel_name: str
    smell: str
    hush: str
    soundline: str
    hidden_spot: str
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
    role: str
    clue: str
    alibi: str
    motive: str
    suspicious: int = 0
    innocent: bool = False
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
class ClueSource:
    id: str
    label: str
    sound: str
    flashback: str
    reveals: str
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
    setting: Setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    pup = world.get("puppy")
    if pup.meters["found"] >= THRESHOLD and not world.facts.get("revealed"):
        world.facts["revealed"] = True
        out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("reveal", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict(world: World) -> dict:
    sim = world.copy()
    simulate_search(sim, narrate=False)
    return {"found": sim.get("puppy").meters["found"] >= THRESHOLD}


def simulate_search(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    helper = world.get("helper")
    kennel = world.get("kennel")
    pup = world.get("puppy")
    mirror = world.get("mirror")
    gate = world.get("gate")
    helper.memes["worry"] += 1
    child.memes["curiosity"] += 1
    world.say(f"At {world.setting.place}, the air smelled of clean straw and wet paws.")
    world.say(f"The little {world.setting.kennel_name} was quiet, too quiet, and that made {child.id} look up at once.")
    world.say(f'"{child.id}," said {helper.id}, "we need to use our eyes and ears."')
    world.para()
    world.say("Clink. Scratch. Tap-tap-tap.")
    world.say(f"A sound came from near {world.setting.hidden_spot}, but it stopped the moment anyone turned.")
    world.say(f"{child.id} frowned. " f'"That sounded like {pup.label}."')
    world.say(f"Then {mirror.label} caught a tiny reflection: a blue ribbon on a collar, and a scuff by the gate.")
    child.memes["suspense"] += 1
    helper.memes["suspense"] += 1
    world.para()
    world.say(
        f"{helper.id} paused, and for a second {child.id} remembered {helper.attrs.get('flashback', '')}."
    )
    world.say(
        f"Back then, someone had said the same lesson: listen first, and don't rush past a clue."
    )
    world.say(f"{child.id} bent down. Behind the feed bin, {pup.label} gave one tiny whimper: yip.")
    pup.meters["found"] += 1
    pup.memes["relief"] += 1
    gate.meters["open"] = 0
    kennel.memes["calm"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(f"Clatter! {child.id} slid the feed bin aside and found {pup.label} curled up behind it.")
        world.say(
            f"It had not run away at all. It had only hidden from the banging gate, and the blue ribbon had snagged on the latch."
        )
        world.say(f"{helper.id} knelt and untangled the ribbon. The kennel went still, soft, and safe again.")


def setup_world(setting: Setting, child_name: str, helper_name: str, suspect: Suspect, clue: ClueSource) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl" if child_name in GIRL_NAMES else "boy", role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type="woman", role="helper"))
    kennel = world.add(Entity(id="kennel", type="place", label=setting.kennel_name))
    pup = world.add(Entity(id="puppy", type="dog", label="the puppy"))
    gate = world.add(Entity(id="gate", type="thing", label="the latch"))
    mirror = world.add(Entity(id="mirror", type="thing", label="the shiny window"))
    child.memes["curiosity"] = 1
    helper.attrs["flashback"] = clue.flashback
    world.facts.update(suspect=suspect, clue=clue, child=child, helper=helper, pup=pup, kennel=kennel, gate=gate, mirror=mirror)
    return world


def tell(setting: Setting, child_name: str, helper_name: str, suspect: Suspect, clue: ClueSource) -> World:
    world = setup_world(setting, child_name, helper_name, suspect, clue)
    child = world.get(child_name)
    helper = world.get(helper_name)
    pup = world.get("puppy")
    world.say(f"{child.id} went with {helper.id} to the {world.setting.kennel_name}.")
    world.say(f"{child.id} loved the place, but today the {world.setting.kennel_name} felt strange because one dog pen was empty.")
    world.say(f'"Where is {pup.label}?" {child.id} asked.')
    world.para()
    world.say(f"{helper.id} pointed to the floor. " f'"We will find out. First, we use our ears."')
    world.say(f"The room held its breath.")
    world.para()
    world.say(f"{clue.sound}")
    world.say(f"{clue.reveals}")
    world.para()
    simulate_search(world)
    world.para()
    world.say(f"{child.id} smiled when {pup.label} licked {child.pronoun('possessive')} hand.")
    world.say(f"That was the answer: no thief, no runaway, just a hidden puppy and one loose ribbon.")
    world.say(f"The kennel was calm again, and the mystery was solved.")
    world.facts["outcome"] = "solved"
    return world


SETTINGS = {
    "morning": Setting(
        id="morning",
        place="the animal shelter",
        kennel_name="kennel",
        smell="clean straw",
        hush="soft and still",
        soundline="clink scratch tap",
        hidden_spot="the feed bin",
    ),
    "afternoon": Setting(
        id="afternoon",
        place="the town kennel",
        kennel_name="kennel",
        smell="soap and hay",
        hush="bright but hushed",
        soundline="yip yip clatter",
        hidden_spot="behind the laundry cart",
    ),
}

SUSPECTS = {
    "raccoon": Suspect(
        id="raccoon",
        label="a raccoon",
        role="wild visitor",
        clue="muddy paw prints by the fence",
        alibi="the paw prints ended at the drain",
        motive="no snack was missing",
        suspicious=1,
        innocent=True,
        tags={"animal", "mystery"},
    ),
    "boy": Suspect(
        id="boy",
        label="a boy with a ball",
        role="visitor",
        clue="a bouncing ball near the gate",
        alibi="the boy was already at the front desk",
        motive="he was only asking for a lost sticker",
        suspicious=1,
        innocent=True,
        tags={"child", "mystery"},
    ),
    "wind": Suspect(
        id="wind",
        label="the wind",
        role="weather",
        clue="a door left ajar",
        alibi="the door clicked shut again",
        motive="it rattled the gate, but did not take anyone away",
        suspicious=0,
        innocent=True,
        tags={"weather", "mystery"},
    ),
}

CLUES = {
    "ribbon": ClueSource(
        id="ribbon",
        label="the blue ribbon",
        sound="Clink. Scratch. Tap-tap-tap.",
        flashback="a rainy day when the helper had tied a blue ribbon on the collar",
        reveals="The little sound was not a cry for help. It was a ribbon snagging on a latch.",
        tags={"sound", "flashback"},
    ),
    "bell": ClueSource(
        id="bell",
        label="the brass bell",
        sound="Ding. Ding. Ding.",
        flashback="the day the helper said bells are easier to find than whispers",
        reveals="The bright dinging came from a collar bell brushing against the metal pen.",
        tags={"sound", "flashback"},
    ),
}

GIRL_NAMES = ["Mina", "Tess", "Ruby", "Nora", "Lily"]
BOY_NAMES = ["Owen", "Eli", "Max", "Theo", "Ben"]


@dataclass
class StoryParams:
    setting: str
    child_name: str
    helper_name: str
    suspect: str
    clue: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CLUES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld at a kennel.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
        raise StoryError("Unknown suspect.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    combos = valid_combos()
    setting = args.setting or rng.choice(sorted(SETTINGS))
    clue = args.clue or rng.choice(sorted(CLUES))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice(["Aunt June", "Ms. Bell", "Mara"])
    return StoryParams(setting=setting, child_name=name, helper_name=helper, suspect=suspect, clue=clue)


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a kid-friendly whodunit at a kennel that includes the words "kennel" and "use".',
        f"Tell a suspenseful mystery where {world.facts['child'].id} and {world.facts['helper'].id} use clues to find a hidden puppy.",
        f"Write a story with a flashback, sound effects, and a calm reveal at the kennel.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    clue = world.facts["clue"]
    pup = world.facts["pup"]
    return [
        QAItem(question="What was the mystery?", answer="The mystery was where the puppy had gone and why the kennel was so quiet. The answer was hidden in a ribbon snagged on the latch."),
        QAItem(question="What clue helped solve it?", answer=f"{clue.sound} led them to look near the feed bin, and the ribbon showed that {pup.label} had only hidden. The sound made the search feel suspenseful, but it was really a small accident."),
        QAItem(question=f"What did {child.id} and {helper.id} use to solve the case?", answer="They used their ears, their eyes, and a careful flashback about the collar ribbon. That helped them notice the real clue instead of guessing wildly."),
    ]


def world_qa(world: World) -> list[QAItem]:
    setting = world.setting
    return [
        QAItem(question="What is a kennel?", answer="A kennel is a place where dogs stay safely in small pens or rooms. People go there to feed them, care for them, and keep them clean."),
        QAItem(question="Why do stories use sound effects?", answer="Sound effects help the reader hear what is happening in the scene. They can make a mystery feel more tense and lively."),
        QAItem(question="What is a flashback?", answer="A flashback is a quick look back at something that happened earlier. It helps explain a clue that would be confusing without the memory."),
        QAItem(question="What makes a story suspenseful?", answer="Suspense happens when you know something important is going on, but you do not know the answer yet. It keeps you wondering until the truth is revealed."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(p)
    parts.append("\n== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    parts.append("\n== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes} attrs={e.attrs}")
    return "\n".join(lines)


ASP_RULES = r"""
found :- puppy_found.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("kennel_world", "yes"),
        asp.fact("sound_effects", "yes"),
        asp.fact("flashback", "yes"),
        asp.fact("whodunit", "yes"),
    ])


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show kennel_world/1."))
    return asp.atoms(model, "kennel_world")


def asp_verify() -> int:
    try:
        if not asp_valid():
            print("MISMATCH: ASP returned no facts.")
            return 1
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story:
            print("MISMATCH: empty story.")
            return 1
        print("OK: ASP smoke test and story generation passed.")
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1


CURATED = [
    StoryParams(setting="morning", child_name="Mina", helper_name="Aunt June", suspect="raccoon", clue="ribbon"),
    StoryParams(setting="afternoon", child_name="Owen", helper_name="Ms. Bell", suspect="wind", clue="bell"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.suspect not in SUSPECTS:
        raise StoryError("Invalid suspect.")
    if params.clue not in CLUES:
        raise StoryError("Invalid clue.")
    world = tell(SETTINGS[params.setting], params.child_name, params.helper_name, SUSPECTS[params.suspect], CLUES[params.clue])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program(show="#show kennel_world/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode: kennel world fact present =", bool(asp_valid()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

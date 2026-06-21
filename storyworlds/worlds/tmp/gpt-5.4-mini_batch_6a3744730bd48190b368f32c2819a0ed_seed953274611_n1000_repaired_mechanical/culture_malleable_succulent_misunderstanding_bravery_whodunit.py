#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/culture_malleable_succulent_misunderstanding_bravery_whodunit.py
==================================================================================================

A tiny whodunit-flavored storyworld about a school culture fair, a missing
succulent, a malleable craft lump, and a brave child who clears up a
misunderstanding.

The story is built from state:
- a fair creates noise and confusion,
- one child notices a missing object,
- a misleading clue points to the wrong suspect,
- bravery turns the child toward a careful search,
- the truth is found and the misunderstanding ends.

The words culture, malleable, and succulent are part of the domain and can
appear naturally in the rendered story.
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
class Setting:
    id: str
    place: str
    culture: str
    bustle: str
    tag: str = ""
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
class Clue:
    id: str
    label: str
    misleading: bool = False
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
class Misunderstanding:
    id: str
    suspicion: str
    truth: str
    reason: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hall").meters["bustle"] >= THRESHOLD and ("confusion",) not in world.fired:
        world.fired.add(("confusion",))
        world.get("child").memes["uncertain"] += 1
        out.append("The room felt full of noise and second guesses.")
    return out


def _r_missing(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["suspect"] < THRESHOLD:
        return out
    if ("missing",) not in world.fired:
        world.fired.add(("missing",))
        world.get("succulent").meters["hidden"] += 1
        out.append("Something small was missing from the fair table.")
    return out


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["brave"] < THRESHOLD:
        return out
    if ("brave",) not in world.fired:
        world.fired.add(("brave",))
        child.memes["courage"] += 1
        out.append("The child took a deep breath and chose to look again.")
    return out


CAUSAL_RULES = [Rule("confusion", _r_confusion), Rule("missing", _r_missing), Rule("brave", _r_brave)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_truth(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    return sim.get("succulent").meters["found"] >= THRESHOLD


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    clue: str
    misunderstanding: str
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


SETTINGS = {
    "festival": Setting(id="festival", place="the school hall", culture="a culture fair", bustle="music, drums, and bright paper lanterns", tag="fair"),
    "museum": Setting(id="museum", place="the community room", culture="a neighborhood culture day", bustle="quiet talk, poster boards, and careful footsteps", tag="exhibit"),
}

CLUES = {
    "spilled_soil": Clue(id="spilled_soil", label="a little spill of soil", misleading=True, tags={"succulent", "soil"}),
    "green_leaf": Clue(id="green_leaf", label="a green leaf on the floor", misleading=True, tags={"succulent", "leaf"}),
    "note_card": Clue(id="note_card", label="a name card beside the pot", misleading=False, tags={"succulent", "truth"}),
}

MISUNDERSTANDINGS = {
    "wrong_cousin": Misunderstanding(id="wrong_cousin", suspicion="the helper took the plant", truth="the plant had been moved by the wind from the open table", reason="the clue pointed the wrong way", tags={"wrong-suspect"}),
    "misplaced_table": Misunderstanding(id="misplaced_table", suspicion="someone hid the pot on purpose", truth="it had been set down near the art table during cleanup", reason="the fair had too many moving hands", tags={"cleanup"}),
}

NAMES_G = ["Lily", "Mia", "Zoe", "Ava", "Nora"]
NAMES_B = ["Leo", "Noah", "Finn", "Ben", "Theo"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MISUNDERSTANDINGS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld: culture fair, succulent plant, brave truth-telling.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.misunderstanding and args.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    settings = [args.setting] if args.setting else list(SETTINGS)
    ms = [args.misunderstanding] if args.misunderstanding else list(MISUNDERSTANDINGS)
    combos = [(s, m) for s in settings for m in ms if (s, m) in valid_combos()]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, misunderstanding = rng.choice(combos)
    clue = args.clue or rng.choice(list(CLUES))
    gender = rng.choice(["girl", "boy"])
    child_name = rng.choice(NAMES_G if gender == "girl" else NAMES_B)
    helper_gender = "girl" if gender == "boy" else "boy"
    helper_name = rng.choice(NAMES_G if helper_gender == "girl" else NAMES_B)
    return StoryParams(setting=setting, child_name=child_name, child_gender=gender,
                       helper_name=helper_name, helper_gender=helper_gender,
                       clue=clue, misunderstanding=misunderstanding)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Invalid story parameters.")
    world = World()
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    mis = MISUNDERSTANDINGS[params.misunderstanding]

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="detective"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    hall = world.add(Entity(id="hall", type="room", label=setting.place))
    succulent = world.add(Entity(id="succulent", type="plant", label="the succulent"))
    malleable = world.add(Entity(id="clay", type="craft", label="the malleable clay"))
    hall.meters["bustle"] = 1
    child.memes["suspect"] = 1
    child.memes["brave"] = 1
    helper.memes["care"] = 1

    world.say(f"At {setting.place}, the children helped with {setting.culture}.")
    world.say(f"Between the tables sat a succulent and a bowl of malleable clay, both waiting for the craft show.")
    world.say(f"Then {params.child_name} spotted {clue.label} and frowned. It looked like {mis.suspicion}.")
    world.para()
    propagate(world, narrate=True)

    if clue.misleading:
        child.memes["confusion"] += 1
    world.say(f"{params.helper_name} said the clue might be tricking them, because {mis.reason}.")
    child.memes["brave"] += 1
    world.para()
    if predict_truth(world):
        succulent.meters["found"] = 1
        world.say(f"Bravely, {params.child_name} checked the far side of the display and found the succulent by a sign card.")
        world.say(f"The misunderstanding ended at once. The plant had not been stolen; it had only been moved during cleanup.")
    else:
        world.say(f"Still, {params.child_name} searched carefully and found the succulent tucked behind the poster board.")
        world.say("The wrong guess fell apart, and everyone laughed with relief.")

    world.facts.update(setting=setting, clue=clue, misunderstanding=mis, child=child, helper=helper, succulent=succulent, malleable=malleable)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    return [
        f"Write a whodunit story for a young child set at {setting.culture}, and include the words culture, malleable, and succulent.",
        f"Tell a brave mystery story where a child misunderstands a clue at {setting.place}, then solves the puzzle kindly.",
        f"Write a short mystery with a mistaken clue, a brave search, and a succulent that turns up in the right place.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    succulent: Entity = f["succulent"]
    mis: Misunderstanding = f["misunderstanding"]
    clue: Clue = f["clue"]
    qa = [
        ("Where did the story happen?", f"It happened at {setting.place} during {setting.culture}. The busy fair setting made the clue easy to misread."),
        ("What did the child think at first?", f"{child.id} thought {clue.label} meant {mis.suspicion}. That was the misunderstanding the story had to untangle."),
        ("What did bravery change?", f"Bravery made {child.id} keep looking instead of staying stuck on the wrong guess. Because of that, the child found the succulent and learned the truth."),
    ]
    if succulent.meters["found"] >= THRESHOLD:
        qa.append(("What was the truth?", f"The truth was that nobody had taken the succulent. It had simply been moved during cleanup, so the scary guess was wrong."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is culture?", "Culture is the way people celebrate, share food, music, stories, and traditions together."),
        ("What does malleable mean?", "Malleable means something can be shaped or bent without breaking, like soft clay."),
        ("What is a succulent?", "A succulent is a plant with thick leaves or stems that hold water, so it can stay healthy for a long time."),
        ("What is a misunderstanding?", "A misunderstanding happens when someone gets the wrong idea about what is happening."),
        ("What is bravery?", "Bravery means doing the careful, hard thing even when you feel worried."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={dict(m)}")
        if n:
            bits.append(f"memes={dict(n)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- setting(S), misunderstanding(M).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, misunderstanding=None, clue=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"FAILED smoke test: {e}")
        return 1
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    print("MISMATCH between ASP and Python valid_combos().")
    return 1


CURATED = [
    StoryParams(setting="festival", child_name="Lily", child_gender="girl", helper_name="Leo", helper_gender="boy", clue="spilled_soil", misunderstanding="wrong_cousin"),
    StoryParams(setting="museum", child_name="Mia", child_gender="girl", helper_name="Noah", helper_gender="boy", clue="note_card", misunderstanding="misplaced_table"),
]


def generate(params: StoryParams) -> StorySample:
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible settings/misunderstandings.")
        return

    rng0 = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = (args.seed if args.seed is not None else random.randrange(2**31)) + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/curtsy_grin_sound_effects_suspense_mystery.py
===============================================================================

A small mystery storyworld with sound effects and suspense.

Premise
-------
A child notices a puzzling clue in a quiet place, follows the trail of sound,
learns that the "mystery" is harmless, and ends with a graceful curtsy and a grin.

This world is built to be:
- typed
- state-driven
- child-facing
- compatible with the shared Storyweavers result containers
- backed by a Python reasonableness gate and an inline ASP twin

Seed words: curtsy, grin
Style: mystery
Features: sound effects, suspense
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

SPACES = {
    "museum": {
        "place": "the little museum",
        "quiet": "The little museum was quiet and cool, with glass cases shining under the lights.",
        "hiding": "behind the tall statue",
        "ending": "the little museum",
    },
    "library": {
        "place": "the old library",
        "quiet": "The old library was quiet and dusty, with tall shelves and sleepy shadows.",
        "hiding": "between the tall shelves",
        "ending": "the old library",
    },
    "attic": {
        "place": "the attic",
        "quiet": "The attic was quiet and a little dusty, with boxes stacked like sleepy towers.",
        "hiding": "behind the old trunks",
        "ending": "the attic",
    },
}

CLUES = {
    "glove": {
        "label": "white glove",
        "trail": "a single white glove",
        "sound": "flap-flap",
        "hint": "A glove could belong to a museum helper or a costume.",
    },
    "key": {
        "label": "small brass key",
        "trail": "a small brass key",
        "sound": "clink",
        "hint": "A key usually opens something that wants to stay closed.",
    },
    "ribbon": {
        "label": "blue ribbon",
        "trail": "a blue ribbon",
        "sound": "swish",
        "hint": "A ribbon can catch on things and lead the eye along a path.",
    },
}

RESOLUTIONS = {
    "found_owner": {
        "sense": 3,
        "power": 3,
        "text": "followed the clue to a kind helper who had dropped it",
        "fail": "followed the clue too far and found nothing useful",
        "qa": "followed the clue to a kind helper who had dropped it",
    },
    "hidden_note": {
        "sense": 3,
        "power": 3,
        "text": "opened a little box and found a note tucked safely inside",
        "fail": "opened the box too late to learn anything new",
        "qa": "opened a little box and found a note tucked safely inside",
    },
    "false_alarm": {
        "sense": 2,
        "power": 2,
        "text": "learned the mystery was only a costume mix-up and not a real problem",
        "fail": "could not sort out the puzzle before the moment passed",
        "qa": "learned the mystery was only a costume mix-up",
    },
    "too_weak": {
        "sense": 1,
        "power": 1,
        "text": "peeked at the clue and shrugged",
        "fail": "peeked at the clue and still missed the answer",
        "qa": "peeked at the clue and still missed the answer",
    },
}

CHARACTER_NAMES = ["Mila", "Nora", "Toby", "Jun", "Ella", "Leo", "Pia", "Owen"]
HELPER_NAMES = ["Mr. Finch", "Ms. Moon", "Aunt Dot", "the guide", "the librarian"]


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
        return self.label or self.id
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
    quiet: str
    hiding: str
    ending: str
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
    trail: str
    sound: str
    hint: str
    risky: bool = False
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
class Resolution:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa: str
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
    setting: str
    clue: str
    resolution: str
    detective: str
    detective_type: str
    helper: str
    helper_type: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def hazard_at_risk(clue: Clue) -> bool:
    return clue.risky


def sensible_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= SENSE_MIN]


def resolve_power(resolution: Resolution) -> int:
    return resolution.power


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child mystery storyworld with suspense and sound effects.")
    ap.add_argument("--setting", choices=SPACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy", "person"])
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


def explain_rejection(clue: Clue, resolution: Resolution) -> str:
    if not hazard_at_risk(clue):
        return f"(No story: the clue '{clue.id}' does not create a real mystery trail.)"
    if resolution.sense < SENSE_MIN:
        return f"(Refusing resolution '{resolution.id}': it is too weak for this storyworld.)"
    return "(No story: this combination is not reasonable enough for the mystery.)"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SPACES:
        for c in CLUES:
            clue = CLUES[c]
            if not hazard_at_risk(clue):
                continue
            for r in RESOLUTIONS:
                if RESOLUTIONS[r].sense >= SENSE_MIN:
                    combos.append((s, c, r))
    return combos


def build_world_story(params: StoryParams) -> World:
    if params.setting not in SPACES or params.clue not in CLUES or params.resolution not in RESOLUTIONS:
        raise StoryError("Invalid parameters: unknown setting, clue, or resolution.")
    setting = Setting(**SPACES[params.setting])
    clue = Clue(id=params.clue, **CLUES[params.clue])
    resolution = Resolution(id=params.resolution, **RESOLUTIONS[params.resolution])

    if not hazard_at_risk(clue):
        raise StoryError(explain_rejection(clue, resolution))
    if resolution.sense < SENSE_MIN:
        raise StoryError(explain_rejection(clue, resolution))

    world = World()
    detective = world.add(Entity(
        id=params.detective,
        kind="character",
        type=params.detective_type,
        role="detective",
        traits=["curious", "careful"],
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=params.helper_type,
        role="helper",
        traits=["calm", "helpful"],
    ))
    world.add(Entity(id="clue", kind="thing", type="thing", label=clue.label, role="clue"))
    world.add(Entity(id="box", kind="thing", type="thing", label="little box", role="box"))

    detective.memes["curiosity"] += 1
    detective.memes["suspense"] += 1
    helper.memes["calm"] += 1

    world.say(f"{setting.quiet} In the middle of it all, {detective.id} noticed {clue.trail}.")
    world.say(f'"{clue.sound}!" went the sound from {setting.hiding}, and {detective.id} froze for a moment.')
    world.say(f"{detective.id} leaned closer. The clue felt strange, and {helper.id} watched with a patient grin.")

    world.para()
    detective.memes["nervous"] += 1
    world.say(f"Then came a soft rustle -- shhrrk -- from {setting.hiding}.")
    world.say(f'{detective.id} whispered, "Something is hidden there."')
    world.say(f"{helper.id} gave a tiny nod and said the mystery would make sense if they stayed calm.")

    world.para()
    if resolution.id == "found_owner":
        world.say(f"{detective.id} tiptoed forward. The clue led them to {helper.id}, who had dropped it by mistake.")
        world.say(f'The answer arrived with a gentle "tap-tap" of shoes and a relieved laugh.')
        world.say(f"{helper.id} explained how the {clue.label} had slipped away during a costume change.")
        helper.memes["relief"] += 1
        detective.memes["joy"] += 1
    elif resolution.id == "hidden_note":
        world.say(f"{detective.id} opened the little box with a careful click. Inside was a note folded twice.")
        world.say(f'The paper whispered "frrt" as it unfolded, and the message solved the puzzle at once.')
        world.say("The note explained where the missing thing had gone and why it had been hidden safely.")
        detective.memes["joy"] += 1
    else:
        world.say(f"{detective.id} and {helper.id} looked again, and the big spooky clue turned out to be a mix-up.")
        world.say(f'There was a quick "oh!" and then a soft laugh as the mystery lost its fright.')
        detective.memes["joy"] += 1
        helper.memes["joy"] += 1

    world.para()
    detective.memes["suspense"] = 0
    detective.memes["pride"] += 1
    world.say(f"At the end, {detective.id} gave a polite curtsy, and then a bright grin spread across {detective.pronoun('possessive')} face.")
    world.say(f"The mystery was solved, and {setting.ending} felt quiet and safe again.")

    world.facts.update(
        setting=setting,
        clue=clue,
        resolution=resolution,
        detective=detective,
        helper=helper,
        outcome=resolution.id,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "curtsy" and "grin".',
        f"Tell a suspenseful little mystery set in {f['setting'].place} where {f['detective'].id} follows a clue and solves it kindly.",
        f'Write a child-friendly mystery with sound effects like "{f["clue"].sound}" and a calm ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    h = f["helper"]
    clue = f["clue"]
    setting = f["setting"]
    resolution = f["resolution"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {d.id}, who notices a strange clue and tries to solve the mystery. {h.id} helps by staying calm and giving useful clues."
        ),
        QAItem(
            question="What sound did the story use to build suspense?",
            answer=f'The story used sounds like "{clue.sound}!" and a soft "shhrrk" to make the mystery feel suspenseful. Those sounds help the reader feel that something hidden is nearby.'
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{resolution.qa.capitalize()}. That ended the suspense because the clue finally made sense and the place felt safe again."
        ),
        QAItem(
            question="What did the detective do at the end?",
            answer=f"{d.id} gave a curtsy and then smiled with a grin. That ending shows the mystery was solved and everyone could relax."
        ),
        QAItem(
            question="Where did the story happen?",
            answer=f"It happened in {setting.place}. The quiet setting made the clues and sounds stand out more clearly."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    items = [
        QAItem(
            question="What is a curtsy?",
            answer="A curtsy is a polite little bow or dip people sometimes do to show respect or to be fancy."
        ),
        QAItem(
            question="What is a grin?",
            answer="A grin is a big smile. It often shows happiness, pride, or relief."
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects help the reader hear the action in their head. They can make a scene feel more lively and exciting."
        ),
        QAItem(
            question="Why do mystery stories feel suspenseful?",
            answer="Mystery stories feel suspenseful because something is not known yet. The reader keeps wondering what the clue means until the answer is found."
        ),
    ]
    if f["clue"].id == "key":
        items.append(QAItem(
            question="What does a key usually do?",
            answer="A key usually opens a lock. It can unlock a door, a box, or another small hidden place."
        ))
    if f["clue"].id == "glove":
        items.append(QAItem(
            question="What can a glove be used for?",
            answer="A glove can keep hands clean or warm, and it can also be part of a costume."
        ))
    if f["clue"].id == "ribbon":
        items.append(QAItem(
            question="What is a ribbon?",
            answer="A ribbon is a long, thin strip of cloth. People use it for gifts, costumes, and decorations."
        ))
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="museum", clue="glove", resolution="found_owner", detective="Mila", detective_type="girl", helper="Ms. Moon", helper_type="woman"),
    StoryParams(setting="library", clue="key", resolution="hidden_note", detective="Toby", detective_type="boy", helper="Mr. Finch", helper_type="man"),
    StoryParams(setting="attic", clue="ribbon", resolution="false_alarm", detective="Ella", detective_type="girl", helper="Aunt Dot", helper_type="woman"),
]


ASP_RULES = r"""
clue(c) :- clue_id(c).
resolution(r) :- resolution_id(r).
sense_ok(r) :- sense(r, s), sense_min(m), s >= m.
hazard(c) :- risky(c).
valid(S, C, R) :- setting(S), clue(C), resolution(R), hazard(C), sense_ok(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SPACES:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_id", cid))
        if c.risky:
            lines.append(asp.fact("risky", cid))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution_id", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos().")

    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, resolution=None, name=None, helper_name=None, gender=None, helper_gender=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.clue and args.resolution:
        if (args.setting, args.clue, args.resolution) not in combos:
            raise StoryError(explain_rejection(CLUES[args.clue], RESOLUTIONS[args.resolution]))
    picks = [c for c in combos
             if (args.setting is None or c[0] == args.setting)
             and (args.clue is None or c[1] == args.clue)
             and (args.resolution is None or c[2] == args.resolution)]
    if not picks:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, resolution = rng.choice(sorted(picks))
    detective_type = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_gender or rng.choice(["woman", "man", "person"])
    detective = args.name or rng.choice(CHARACTER_NAMES)
    helper = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting,
        clue=clue,
        resolution=resolution,
        detective=detective,
        detective_type=detective_type,
        helper=helper,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world_story(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, clue, resolution) combos:")
        for s, c, r in asp_valid_combos():
            print(f"  {s:8} {c:8} {r}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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

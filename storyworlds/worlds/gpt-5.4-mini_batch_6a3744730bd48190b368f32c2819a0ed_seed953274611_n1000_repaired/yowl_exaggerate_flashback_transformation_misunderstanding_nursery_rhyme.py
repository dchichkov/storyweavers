#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/yowl_exaggerate_flashback_transformation_misunderstanding_nursery_rhyme.py
===========================================================================================================

A tiny storyworld in nursery-rhyme style: a child hears a small scare, yowls
too loudly, exaggerates the danger, misreads a harmless transformation, then a
calm helper clears the misunderstanding. A brief flashback explains why the
sound matters, and the ending proves the change.

The world is intentionally small and state-driven:
- a character has membranes of feelings in ``memes`` and physical effects in
  ``meters``;
- a toy/pet/friend can transform in a harmless way;
- a misunderstanding can amplify fear until a helper corrects it;
- a flashback can nudge the meaning of the yowl or exaggeration.

The prose is built from the simulated state, not from a fixed paragraph with
swapped nouns.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Child-friendly thresholds for narrating state changes.
THRESHOLD = 1.0
LOUD_THRESHOLD = 2.0
CUTE_THRESHOLD = 1.0

TONE_WORDS = {"nursery", "rhyme"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    rhyme_hint: str
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
class Sound:
    id: str
    label: str
    exaggeration: int
    makes_worry: bool = True
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
class Transformation:
    id: str
    label: str
    from_label: str
    to_label: str
    surprising: str
    safe: bool = True
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
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    sound: str
    transformation: str
    flashback: bool = True
    misunderstanding: bool = True
    exaggerate: bool = True
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
        clone.entities = json.loads(json.dumps({k: {
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "role": v.role, "attrs": v.attrs, "meters": dict(v.meters),
            "memes": dict(v.memes)
        } for k, v in self.entities.items()}))
        # rebuild actual Entity objects
        rebuilt: dict[str, Entity] = {}
        for k, v in clone.entities.items():
            ent = Entity(id=v["id"], kind=v["kind"], type=v["type"], label=v["label"],
                         role=v["role"], attrs=v["attrs"])
            ent.meters.update(v["meters"])
            ent.memes.update(v["memes"])
            rebuilt[k] = ent
        clone.entities = rebuilt
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def pronoun_name(name: str, gender: str) -> str:
    return name


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["flashback"] < THRESHOLD:
        return out
    sig = ("flashback",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["remember"] += 1
    out.append("__flashback__")
    return out


def _r_exaggerate(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["fear"] < THRESHOLD or child.meters["sound"] < LOUD_THRESHOLD:
        return out
    sig = ("exaggerate",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["exaggeration"] += 1
    world.get("helper").memes["concern"] += 1
    out.append("__exaggerate__")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    toy = world.get("toy")
    if child.memes["fear"] < THRESHOLD or toy.meters["transformed"] < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["confusion"] += 1
    out.append("__misunderstanding__")
    return out


CAUSAL_RULES = [_r_flashback, _r_exaggerate, _r_misunderstanding]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(x for x in sents if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_happen(sound: Sound, trans: Transformation) -> bool:
    return sound.makes_worry and trans.safe


def bestish_sound() -> Sound:
    return max(SOUNDS.values(), key=lambda s: s.exaggeration)


def predict(world: World) -> dict:
    sim = world.copy()
    _do_sound(sim, narrate=False)
    _do_transformation(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "confusion": sim.get("child").memes["confusion"],
    }


def _do_sound(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    sound = world.facts["sound"]
    child.meters["sound"] += sound.exaggeration
    child.memes["fear"] += 1
    propagate(world, narrate=narrate)


def _do_transformation(world: World, narrate: bool = True) -> None:
    toy = world.get("toy")
    trans = world.facts["transformation"]
    toy.meters["transformed"] += 1
    toy.label = trans.to_label
    toy.attrs["form"] = trans.to_label
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"{trans.from_label.capitalize()} changed into {trans.to_label}; "
            f"{trans.surprising}."
        )


def setup(world: World, child: Entity, helper: Entity, sound: Sound,
          trans: Transformation) -> None:
    world.say(
        f"In {world.setting.place}, under a sky of sing-song light, {child.id} "
        f"and {helper.id} went walking hand in hand."
    )
    world.say(
        f"{child.id} loved the little path because it felt like a nursery rhyme, "
        f"with {world.setting.rhyme_hint} and a soft, merry breeze."
    )
    if world.facts.get("flashback_on"):
        child.meters["flashback"] += 1
        world.say(
            f"For a moment, {child.id} remembered a old story: once, a tiny noise "
            f"had made a shadow seem much bigger than it was."
        )


def sound_beat(world: World, child: Entity, sound: Sound) -> None:
    world.say(
        f"Then came a {sound.label}, sharp as a spoon in a cup."
    )
    child.memes["fear"] += 1
    if sound.exaggeration > 1:
        world.say(
            f"{child.id} gave a great yowl and said, "
            f'"Oh dear, oh dear, it is ten storms in one!"'
        )
    else:
        world.say(
            f"{child.id} gave a yowl, then blinked at the little noise."
        )
    if world.facts.get("flashback_on"):
        world.say(
            f"The old memory bobbed up again, and the sound felt even larger in "
            f"{child.id}'s ears."
        )


def transform_beat(world: World, child: Entity, helper: Entity,
                   trans: Transformation) -> None:
    world.say(
        f"Near the gate sat a {trans.from_label}, and with one gentle twist it "
        f"became {trans.to_label}."
    )
    if world.facts.get("misunderstanding_on"):
        world.say(
            f"{child.id} gasped and thought the change meant trouble, not play."
        )
    helper.memes["gentleness"] += 1


def explain(world: World, child: Entity, helper: Entity,
            trans: Transformation) -> None:
    child.memes["confusion"] = 0.0
    child.memes["fear"] = 0.0
    helper.memes["comfort"] += 1
    world.say(
        f"{helper.id} smiled and said, "
        f'"Nothing is wrong, little friend. The {trans.from_label} was only "
        f"showing a trick of change, not a fright."'
    )
    world.say(
        f"{helper.id} patted the {trans.to_label} and helped {child.id} look "
        f"again. This time the shape was clear, and the worry went thin as mist."
    )


def ending(world: World, child: Entity, helper: Entity, trans: Transformation) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then {child.id} laughed, a little laugh, a bright-haired laugh, and "
        f"gave one more yowl -- not of fear, but of play."
    )
    world.say(
        f"By the end, the {trans.to_label} was still {trans.to_label}, the sky "
        f"was still bright, and {child.id} and {helper.id} skipped home in step."
    )


def tell(setting: Setting, sound: Sound, trans: Transformation,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str,
         flashback: bool, misunderstanding: bool, exaggerate: bool) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    toy = world.add(Entity(id="toy", kind="thing", type="thing", label=trans.from_label,
                           attrs={"form": trans.from_label}))
    world.facts.update(sound=sound, transformation=trans, flashback_on=flashback,
                       misunderstanding_on=misunderstanding, exaggerate_on=exaggerate)
    setup(world, child, helper, sound, trans)
    world.para()
    sound_beat(world, child, sound)
    _do_sound(world)
    world.para()
    transform_beat(world, child, helper, trans)
    _do_transformation(world)
    world.para()
    explain(world, child, helper, trans)
    world.para()
    ending(world, child, helper, trans)
    world.facts.update(child=child, helper=helper, toy=toy, outcome="resolved")
    return world


SETTINGS = {
    "lane": Setting(id="lane", place="the cobble lane", rhyme_hint="a lantern on the gate"),
    "garden": Setting(id="garden", place="the little garden", rhyme_hint="roses in a row"),
    "meadow": Setting(id="meadow", place="the sunny meadow", rhyme_hint="daisies in a ring"),
}

SOUNDS = {
    "birdcall": Sound(id="birdcall", label="birdcall", exaggeration=1, tags={"sound"}),
    "clatter": Sound(id="clatter", label="clatter", exaggeration=2, tags={"sound"}),
    "bang": Sound(id="bang", label="bang", exaggeration=3, tags={"sound"}),
}

TRANSFORMS = {
    "lantern": Transformation(
        id="lantern", label="lantern trick", from_label="paper lantern",
        to_label="glowing lantern", surprising="it only brightened, like a smile",
        tags={"transformation"}),
    "mug": Transformation(
        id="mug", label="mug trick", from_label="plain mug",
        to_label="striped mug", surprising="paint stripes made it look brand new",
        tags={"transformation"}),
    "frog": Transformation(
        id="frog", label="frog trick", from_label="toy frog",
        to_label="blue toy frog", surprising="a ribbon changed its color, not its heart",
        tags={"transformation"}),
}

CHILDREN = ["Mimi", "Lulu", "Poppy", "Tilly", "Nina", "Rosie"]
HELPERS = ["Benny", "Hattie", "Mabel", "Sally", "Teddy", "Winnie"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for snd in SOUNDS:
            for tr in TRANSFORMS:
                if can_happen(SOUNDS[snd], TRANSFORMS[tr]):
                    out.append((s, snd, tr))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--transformation", choices=TRANSFORMS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.sound and args.transformation:
        if not can_happen(SOUNDS[args.sound], TRANSFORMS[args.transformation]):
            raise StoryError("This sound/transformation pairing is not reasonable for the story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.sound is None or c[1] == args.sound)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sound, trans = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(CHILDREN)
    helper = args.helper or rng.choice([n for n in HELPERS if n != child])
    return StoryParams(
        setting=setting, child_name=child, child_gender=child_gender,
        helper_name=helper, helper_gender=helper_gender, sound=sound,
        transformation=trans, flashback=True, misunderstanding=True, exaggerate=True
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    snd: Sound = f["sound"]
    tr: Transformation = f["transformation"]
    return [
        f'Write a nursery-rhyme-style story that includes the word "{snd.label}" and the word "yowl".',
        f"Tell a child-safe rhyme where a little {f['child'].id} hears a {snd.label}, "
        f"exaggerates the worry, and then learns that {tr.from_label} can become {tr.to_label}.",
        f"Write a story with a flashback, a misunderstanding, and a gentle ending about "
        f"change and calm words.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    snd: Sound = f["sound"]
    tr: Transformation = f["transformation"]
    return [
        QAItem(
            question="What made the child yowl?",
            answer=(
                f"{child.id} yowled because the {snd.label} sounded much bigger than it was. "
                f"The flashback made the noise feel even more frightening at first."
            ),
        ),
        QAItem(
            question="Why did the child exaggerate the danger?",
            answer=(
                f"{child.id} was scared and said the little sound was like many storms at once. "
                f"That exaggeration grew from the fear, not from the real size of the noise."
            ),
        ),
        QAItem(
            question="What was misunderstood?",
            answer=(
                f"The child thought the change of {tr.from_label} into {tr.to_label} meant trouble. "
                f"It was really a safe transformation, so the helper could clear the misunderstanding."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended calmly. {child.id} understood the change, stopped worrying, and "
                f"walked home smiling with {helper.id}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a yowl?",
            answer="A yowl is a loud cry or howl, often made when someone is surprised or upset."
        ),
        QAItem(
            question="What does exaggerate mean?",
            answer="To exaggerate means to make something sound bigger, stronger, or scarier than it really is."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something means one thing, but it really means something else."
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a quick memory of something that happened before."
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or look into another."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in list(world.entities.values()):
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if n:
            bits.append(f"memes={dict(n)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
flashback :- flashback_on.
exaggerate :- fear, loud_sound.
misunderstanding :- fear, transformed.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", *()),
        asp.fact("flashback_on"),
        asp.fact("misunderstanding_on"),
        asp.fact("exaggerate_on"),
    ]
    for sid in SETTINGS:
        lines.append(asp.fact("setting_id", sid))
    for snd in SOUNDS.values():
        lines.append(asp.fact("sound", snd.id))
        lines.append(asp.fact("exaggeration", snd.id, snd.exaggeration))
    for tr in TRANSFORMS.values():
        lines.append(asp.fact("transformation", tr.id))
        lines.append(asp.fact("safe", tr.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    else:
        print("OK: ASP parity and smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.sound not in SOUNDS or params.transformation not in TRANSFORMS:
        raise StoryError("Invalid parameters for this storyworld.")
    setting = SETTINGS[params.setting]
    sound = SOUNDS[params.sound]
    trans = TRANSFORMS[params.transformation]
    if not can_happen(sound, trans):
        raise StoryError("That combination is not reasonable.")
    world = tell(
        setting, sound, trans,
        params.child_name, params.child_gender,
        params.helper_name, params.helper_gender,
        params.flashback, params.misunderstanding, params.exaggerate,
    )
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


CURATED = [
    StoryParams(setting="garden", child_name="Mimi", child_gender="girl", helper_name="Benny", helper_gender="boy", sound="clatter", transformation="lantern"),
    StoryParams(setting="meadow", child_name="Lulu", child_gender="girl", helper_name="Hattie", helper_gender="girl", sound="bang", transformation="frog"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

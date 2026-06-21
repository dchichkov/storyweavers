#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mental_sound_effects_kindness_moral_value_fairy.py
===================================================================================

A tiny fairy-tale storyworld about a child, a strange little helper, and a
choice between keeping a treat or sharing it kindly. The world keeps track of
physical state with meters and emotional state with memes, then renders a
complete child-facing story with sound effects, a moral-value turn, and a warm
ending.

The seed words and features guide the domain:
- mental
- Sound Effects
- Kindness
- Moral Value
- Style: Fairy Tale
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
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
        female = {"girl", "mother", "mom", "queen", "fairy"}
        male = {"boy", "father", "dad", "king", "elf", "boy"}
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
class SoundToken:
    id: str
    text: str
    meaning: str
    mood: str
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
class Gift:
    id: str
    label: str
    phrase: str
    kind: str
    value: int
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
class Helper:
    id: str
    label: str
    phrase: str
    kindness: int
    power: int
    rescue_text: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["worry"] >= THRESHOLD and ("worry" not in world.fired):
            world.fired.add(("worry", e.id))
            out.append(f"{e.id} felt a little tight in the chest.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["kindness"] >= THRESHOLD and child.meters["shared"] < THRESHOLD:
        if ("kindness", child.id) not in world.fired:
            world.fired.add(("kindness", child.id))
            out.append("__kindness__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("kindness", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_choice(world: World, child: Entity, helper: Entity, gift: Gift) -> dict:
    sim = world.copy()
    sim.get("child").memes["worry"] += 1
    return {
        "share": child.memes["kindness"] >= THRESHOLD,
        "helped": helper.memes["kindness"] >= THRESHOLD,
        "value": gift.value,
    }


def tell(world: World, child_name: str, child_type: str, helper_name: str, helper_type: str,
         gift: Gift, sound: SoundToken, helper: Helper, setting: str,
         mental_word: str = "mental") -> World:
    child = world.add(Entity(id="child", kind="character", type=child_type,
                             label=child_name, role="hero",
                             traits=["gentle", "curious"]))
    fairy = world.add(Entity(id="fairy", kind="character", type=helper_type,
                             label=helper_name, role="helper",
                             traits=["kind", "sparkling"]))
    chest = world.add(Entity(id="chest", kind="thing", type="thing", label="little chest"))
    child.memes["kindness"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["delight"] = 0.0
    child.meters["gift"] = 0.0
    fairy.memes["kindness"] = float(helper.kindness)
    fairy.meters["help"] = 0.0

    world.say(
        f"Once in a {setting}, there lived {child_name}, who had a {mental_word} habit "
        f"of whispering ideas to {child.pronoun('possessive')} own heart."
    )
    world.say(
        f"One dusk, {child_name} found {gift.phrase} in a little chest. {sound.text} "
        f"went the lid as it opened, and the {gift.label} shone like a small treasure."
    )
    world.say(
        f"{child_name} smiled, but then {helper_name} fluttered down and asked in a tiny voice "
        f"whether the gift was meant for sharing."
    )

    world.para()
    child.memes["worry"] += 1
    predict_choice(world, child, fairy, gift)
    world.say(
        f"{sound.meaning} made the room feel hushed. {child_name} held the {gift.label} close, "
        f"thinking hard about what was right."
    )
    world.say(
        f"{child_name} could keep it all, or {child_name} could be kind and let {helper_name} have some."
    )

    world.para()
    if helper.kindness >= SENSE_MIN:
        child.memes["kindness"] += 1
        child.meters["shared"] += 1
        fairy.meters["help"] += 1
        world.say(
            f"At last, {child_name} nodded. {sound.text} went the little chest again as "
            f"{child_name} opened it and shared the {gift.label} with {helper_name}."
        )
        world.say(
            f"{helper_name} smiled so brightly that the whole room seemed to warm. "
            f"{helper.rescue_text}."
        )
        world.say(
            f"The {gift.label} was smaller in the hand, but the joy felt larger in the heart."
        )
    else:
        child.memes["selfish"] += 1
        world.say(
            f"{child_name} clutched the gift and turned away. {sound.text} echoed softly, "
            f"and the room felt lonely."
        )
        world.say(
            f"But the tale of the {gift.label} stayed unfinished, because kindness was the truer treasure."
        )

    world.facts.update(
        child=child,
        fairy=fairy,
        chest=chest,
        gift=gift,
        sound=sound,
        helper=helper,
        setting=setting,
        shared=child.meters["shared"] >= THRESHOLD,
        moral=child.memes["kindness"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "lantern_room": "lantern room by the old castle wall",
    "meadow": "meadow beneath the silver moon",
    "kitchen": "cozy kitchen of the baker's cottage",
}

SOUNDS = {
    "click": SoundToken(
        id="click",
        text="Click-clack!",
        meaning="The sound of the lid",
        mood="curious",
        tags={"sound", "lid"},
    ),
    "ding": SoundToken(
        id="ding",
        text="Ding-ding!",
        meaning="A bright note rang out",
        mood="cheerful",
        tags={"sound", "bright"},
    ),
    "soft": SoundToken(
        id="soft",
        text="Tip-tap!",
        meaning="The little chest made a soft sound",
        mood="gentle",
        tags={"sound", "gentle"},
    ),
}

GIFTS = {
    "honey_cake": Gift(
        id="honey_cake",
        label="honey cake",
        phrase="a round honey cake",
        kind="food",
        value=3,
        tags={"sweet", "sharing"},
    ),
    "pear": Gift(
        id="pear",
        label="pear",
        phrase="a shiny green pear",
        kind="food",
        value=2,
        tags={"fruit", "sharing"},
    ),
    "berry_bun": Gift(
        id="berry_bun",
        label="berry bun",
        phrase="a warm berry bun",
        kind="food",
        value=4,
        tags={"sweet", "sharing"},
    ),
}

HELPERS = {
    "glow_fairy": Helper(
        id="glow_fairy",
        label="glow fairy",
        phrase="a glow fairy",
        kindness=3,
        power=2,
        rescue_text="She waved her tiny wand, and the whole room glimmered with calm",
        tags={"fairy", "kindness"},
    ),
    "mouse_fairy": Helper(
        id="mouse_fairy",
        label="mouse fairy",
        phrase="a mouse-sized fairy",
        kindness=2,
        power=1,
        rescue_text="He tugged the ribbon to show that sharing makes a tale sweeter",
        tags={"fairy", "sharing"},
    ),
}

NAMES = ["Mara", "Elin", "Lina", "Tess", "Nori", "Ivy"]
BOYS = ["Finn", "Robin", "Pip", "Owen", "Bram", "Jace"]
TYPES = ["girl", "boy"]


@dataclass
class StoryParams:
    setting: str
    sound: str
    gift: str
    helper: str
    child_name: str
    child_type: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for snd in SOUNDS:
            for g in GIFTS:
                for h in HELPERS:
                    combos.append((s, snd, g, h))
    return combos


def explain_rejection(_: str, __: str, ___: str, ____: str) -> str:
    return "(No story: this fairy-tale choice is not reasonable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about mental kindness and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=TYPES)
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
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combination exists.)")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    sound = args.sound or rng.choice(sorted(SOUNDS))
    gift = args.gift or rng.choice(sorted(GIFTS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    if (setting, sound, gift, helper) not in combos:
        raise StoryError(explain_rejection(setting, sound, gift, helper))
    gender = args.gender or rng.choice(TYPES)
    name = args.name or rng.choice(NAMES if gender == "girl" else BOYS)
    return StoryParams(setting=setting, sound=sound, gift=gift, helper=helper,
                       child_name=name, child_type=gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.sound not in SOUNDS or params.gift not in GIFTS or params.helper not in HELPERS:
        raise StoryError("Invalid StoryParams.")
    world = tell(
        World(),
        params.child_name,
        params.child_type,
        "Fay",
        "fairy",
        GIFTS[params.gift],
        SOUNDS[params.sound],
        HELPERS[params.helper],
        SETTINGS[params.setting],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a young child that uses the word "mental" and a sound effect like {f["sound"].text}.',
        f"Tell a story about {f['child'].id} who must choose kindness and sharing instead of keeping {f['gift'].label} all to {f['child'].pronoun('possessive')}self.",
        f"Write a gentle fairy tale where a tiny helper asks a child to make a moral choice, and the ending proves that kindness matters more than keeping treasure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    fairy = f["fairy"]
    gift = f["gift"]
    sound = f["sound"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who found {gift.phrase}, and {fairy.label_word}, who asked for a kind choice."),
        ("What sound did the chest make?",
         f"It went {sound.text} when it opened. That sound helped make the moment feel magical and a little serious."),
        ("What choice did the child have to make?",
         f"{child.id} could keep the {gift.label} alone or share it. The story turns on that choice, because kindness is the moral heart of the tale."),
        ("How did the story end?",
         f"It ended with sharing and a brighter feeling in the room. The child learned that being kind made the treasure feel better than keeping it alone."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is kindness?",
         "Kindness means thinking about another creature's feelings and helping when you can. It often makes others feel safe and welcome."),
        ("What is a moral value?",
         "A moral value is a good idea about how to act, like honesty, kindness, or courage. People use moral values to decide what is right."),
        ("What does mental mean here?",
         "Mental means something in the mind, like a thought, a worry, or a choice you make inside your head. In a fairy tale, a mental choice can be very important."),
        ("Why do stories use sound effects?",
         "Sound effects make a scene feel lively and clear. Words like click-clack or tip-tap help you hear the moment in your imagination."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="lantern_room", sound="click", gift="honey_cake", helper="glow_fairy", child_name="Mara", child_type="girl"),
    StoryParams(setting="meadow", sound="ding", gift="berry_bun", helper="mouse_fairy", child_name="Finn", child_type="boy"),
    StoryParams(setting="kitchen", sound="soft", gift="pear", helper="glow_fairy", child_name="Ivy", child_type="girl"),
]


ASP_RULES = r"""
valid(S, N, G, H) :- setting(S), sound(N), gift(G), helper(H).
kind_choice :- helper(H), kindness_level(H, K), K >= sense_min(M), M = 2.
shared :- child_kindness(C, K), K >= 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for n in SOUNDS:
        lines.append(asp.fact("sound", n))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
        lines.append(asp.fact("gift_value", g, GIFTS[g].value))
    for h, hv in HELPERS.items():
        lines.append(asp.fact("helper", h))
        lines.append(asp.fact("kindness_level", h, hv.kindness))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP valid combos differ from Python.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:  # noqa: BLE001
        ok = False
        print(f"MISMATCH: generate smoke test failed: {e}")
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    return 1


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
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                samples.append(s)
                seen.add(s.story)
            i += 1
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

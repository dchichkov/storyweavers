#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/obsolete_sound_effects_moral_value_repetition_fable.py
======================================================================================

A tiny fable-like storyworld about an old useful thing becoming obsolete, a noisy
fix, and a small moral choice. The generated stories are built from a simple
simulation: a village child wants to use an old bell to announce a feast, the bell
is obsolete, the sound becomes too loud and unpleasant, and a wiser helper offers
a better, quieter way.

The world supports:
- physical meters and emotional memes
- sound-effect narration from simulated state
- repeated phrases as an authored fable device
- a moral ending image showing what changed
- Python and ASP parity checks
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen"}
        male = {"boy", "father", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



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
    detail: str
    season: str = "spring"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Device:
    id: str
    label: str
    sound: str
    obsolete: bool = False
    loudness: int = 1
    cost: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Lesson:
    id: str
    label: str
    prep: str
    ending: str
    quiet: bool = True
    helpful: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: callable

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_noise(world: World) -> list[str]:
    out = []
    bell = world.entities.get("bell")
    if not bell or bell.meters["ringing"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    host = world.get("host")
    helper = world.get("helper")
    host.memes["worry"] += 1
    helper.memes["concern"] += 1
    world.get("square").meters["noise"] += 1
    out.append("__noise__")
    return out


def _r_change(world: World) -> list[str]:
    out = []
    bell = world.entities.get("bell")
    if not bell or bell.meters["replaced"] < THRESHOLD:
        return out
    sig = ("change",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper = world.get("helper")
    helper.memes["satisfaction"] += 1
    out.append("__change__")
    return out


CAUSAL_RULES = [Rule("noise", _r_noise), Rule("change", _r_change)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, bell: Device, lesson: Lesson,
         child_name: str = "Milo", child_type: str = "boy",
         helper_name: str = "Tessa", helper_type: str = "girl",
         elder_name: str = "Grandmother", elder_type: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(child_name, kind="character", type=child_type, role="seeker"))
    helper = world.add(Entity(helper_name, kind="character", type=helper_type, role="guide"))
    elder = world.add(Entity(elder_name, kind="character", type=elder_type, role="elder"))
    square = world.add(Entity("square", type="place", label="the square"))
    device = world.add(Entity("bell", type="thing", label=bell.label))
    child.memes["eagerness"] = 1
    helper.memes["care"] = 1
    elder.memes["wisdom"] = 1
    world.say(
        f"In {setting.place}, {child.id} found {bell.label} in the old shed beside the square. "
        f"{setting.detail}"
    )
    world.say(
        f'"{bell.sound}!" {child.id} said. "Again, again, {bell.sound}!"'
    )
    world.para()
    world.say(
        f"{child.id} wanted to use the {bell.label} to call everyone to the feast, but "
        f"{helper.id} frowned. " 
        f'"That bell is {bell.obsolete and "obsolete" or "old"}, and it may shout too loudly," {helper.id} said.'
    )
    world.say(
        f'"Listen," {elder.id} said, "sometimes old things once had value, but what is useful can become obsolete."'
    )
    bell.meters["ringing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{bell.sound} {bell.sound} {bell.sound}! The sound bounced off the stones and made the pigeons flap away."
    )
    if world.get("square").meters["noise"] >= THRESHOLD:
        world.say(
            f"{helper.id} covered {helper.pronoun('possessive')} ears and repeated, "
            f'"Too loud, too loud, too loud!"'
        )
    world.para()
    world.say(
        f"Then {helper.id} showed {child.id} a {lesson.label}. {lesson.prep}, {helper.id} smiled, "
        f'and the new plan was calm and kind.'
    )
    device.meters["replaced"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} rang the {lesson.label}: {lesson.ending}. Softly, softly, softly, it carried across the square.'
    )
    world.say(
        f"The villagers came at once, and the feast began without a headache."
    )
    world.say(
        f'"Old tools can be fine for yesterday," {elder.id} said, "but the kindest choice is the one that fits today."'
    )
    world.facts.update(
        child=child, helper=helper, elder=elder, setting=setting,
        bell=bell, lesson=lesson, outcome="changed"
    )
    return world


SETTINGS = {
    "village": Setting("village", "the village", "The cobblestones were warm, and the market stalls waited under the trees."),
    "harbor": Setting("harbor", "the harbor", "The boats rocked gently, and the gulls called over the water."),
    "orchard": Setting("orchard", "the orchard", "The apple branches rustled, and the paths were bright with petals."),
}

BELLS = {
    "iron": Device("iron", "iron bell", "clang-clang", obsolete=True, loudness=3, cost="rust and dust"),
    "brass": Device("brass", "brass bell", "ding-ding", obsolete=True, loudness=2, cost="a little shine"),
    "market": Device("market", "market bell", "BONG!", obsolete=True, loudness=4, cost="a bright ring"),
}

LESSONS = {
    "handbell": Lesson("handbell", "a handbell", "ding-ding", "ding-ding, just right"),
    "chime": Lesson("chime", "a small chime", "hung it by the gate", "ting-ting, clear and sweet"),
    "drum": Lesson("drum", "a soft drum", "tapped it with a felt stick", "thump-thump, warm and easy"),
}

GIRL_NAMES = ["Tessa", "Mina", "Lena", "Iris", "Nora"]
BOY_NAMES = ["Milo", "Owen", "Jude", "Finn", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, b, l) for s in SETTINGS for b in BELLS for l in LESSONS]


@dataclass
@dataclass
class StoryParams:
    setting: str
    bell: str
    lesson: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    elder: str
    elder_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a young child that includes the word "{f["bell"].label_word}" and the word "obsolete".',
        f"Tell a short moral story where {f['child'].id} discovers an old {f['bell'].label_word} is obsolete, hears its noisy sound effect, and finds a better way.",
        f"Write a repeatable fable with sound effects and a moral: old things can be useful, but sometimes a quieter tool fits today better.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, elder, bell, lesson = f["child"], f["helper"], f["elder"], f["bell"], f["lesson"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, {helper.id}, and {elder.id}. They all care about the village and the feast."),
        ("Why was the old bell a problem?",
         f"It was obsolete, so it did not fit the village's need very well anymore. When {child.id} rang it, the sound was far too loud and everyone flinched."),
        ("What happened after the bell rang?",
         f"The bell went {bell.sound} {bell.sound} {bell.sound}, and the noise bounced around the square. That made the helper worry, because the villagers needed a kinder way to call everyone."),
        ("How did they fix the problem?",
         f"{helper.id} showed {child.id} {lesson.label} and used it instead. The new sound was gentler, so the feast could begin without the loud trouble."),
        ("What moral did the elder give?",
         f"{elder.id} said that old things can be fine for yesterday, but the kindest choice is the one that fits today. That is the lesson the story leaves behind."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does obsolete mean?",
         "Something obsolete is old-fashioned or no longer the best choice because something better or newer does the job more kindly or well."),
        ("What is a sound effect in a story?",
         "A sound effect is a written sound like clang-clang or ding-ding that helps you hear the moment in your head."),
        ("Why do fables repeat phrases?",
         "Fables often repeat phrases so the lesson is easy to remember and the story feels steady, like a rhyme or chant."),
        ("What is a moral?",
         "A moral is the lesson at the heart of a story, the kind thought the reader is meant to keep."),
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village", "iron", "handbell", "Milo", "boy", "Tessa", "girl", "Grandmother", "woman"),
    StoryParams("harbor", "brass", "chime", "Lena", "girl", "Mina", "girl", "Grandfather", "man"),
    StoryParams("orchard", "market", "drum", "Theo", "boy", "Iris", "girl", "Old Fox", "fox"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.bell is None or c[1] == args.bell)
              and (args.lesson is None or c[2] == args.lesson)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, bell, lesson = rng.choice(sorted(combos))
    child_type = rng.choice(["boy", "girl"])
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = "girl" if child_type == "boy" else "boy"
    helper = args.helper or rng.choice(GIRL_NAMES if helper_type == "girl" else BOY_NAMES)
    elder = args.elder or "Grandmother"
    elder_type = args.elder_type or "woman"
    return StoryParams(setting, bell, lesson, child, child_type, helper, helper_type, elder, elder_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], BELLS[params.bell], LESSONS[params.lesson],
                 params.child, params.child_type, params.helper, params.helper_type,
                 params.elder, params.elder_type)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable storyworld about obsolete things, sound effects, and a moral.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bell", choices=BELLS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["boy", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["boy", "girl"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["man", "woman", "fox"])
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


ASP_RULES = r"""
valid(S, B, L) :- setting(S), bell(B), lesson(L).
obsolete_bell(B) :- bell(B), obsolete(B).
noisy(B) :- bell(B), loudness(B, N), N >= 2.
changed(S, B, L) :- valid(S, B, L), obsolete_bell(B), noisy(B), lesson(L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid, b in BELLS.items():
        lines.append(asp.fact("bell", bid))
        if b.obsolete:
            lines.append(asp.fact("obsolete", bid))
        lines.append(asp.fact("loudness", bid, b.loudness))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    import asp
    clingo = set(asp_valid_combos())
    python = set(valid_combos())
    if clingo == python:
        print(f"OK: gate matches valid_combos() ({len(clingo)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    # smoke test default/curated generation
    try:
        _ = generate(CURATED[0]).story
        _ = generate(resolve_params(build_parser().parse_args([]), random.Random(7))).story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def explain_rejection() -> str:
    return "(No story: this combination does not support the fable's obsolete-to-better turn.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for s, b, l in combos:
            print(f"{s:10} {b:10} {l}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and the {p.bell} ({p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

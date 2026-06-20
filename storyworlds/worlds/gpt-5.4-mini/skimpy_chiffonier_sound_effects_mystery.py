#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/skimpy_chiffonier_sound_effects_mystery.py
============================================================================

A standalone storyworld about a small mystery in a bedroom: a child hears odd
sound effects, notices a skimpy clue, searches a chiffonier, and learns that the
"haunting" was just a clever, safe surprise.

Seed words: skimpy, chiffonier
Style: Mystery
Feature: Sound Effects

The world is built from a few typed entities with physical meters and emotional
memes. The story is state-driven: a rumor begins, clues accumulate, the child
investigates, the sound is explained, and the ending image proves what changed.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    mood: str
    darkness: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    skimpy: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class SoundSource:
    id: str
    label: str
    sound: str
    hiding_place: str
    harmless: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_fear(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["mystery"] < THRESHOLD:
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["unease"] += 1
        out.append("__murmur__")
    return out


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


CAUSAL_RULES = [Rule("fear", _r_fear)]


def _start_mystery(world: World, child: Entity, setting: Setting, clue: Clue) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a quiet night in {setting.place}, {child.id} heard a faint "
        f"{setting.mood} sound drift down the hall: \"{clue.location}\" "
        f"seemed to whisper back."
    )
    world.say(
        f"The room felt {setting.darkness}, and {child.id} noticed a skimpy clue "
        f"near the floor."
    )


def _hear_sound(world: World, source: SoundSource) -> None:
    world.say(f'From somewhere nearby came a soft "{source.sound}" sound.')
    world.say(f"It sounded secret, like it was hiding on purpose.")


def _investigate(world: World, child: Entity, clue: Clue, source: SoundSource) -> None:
    child.meters["mystery"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} followed the clue to the {source.hiding_place} and peered '
        f'behind the chiffonier.'
    )
    if clue.skimpy:
        world.say(
            f"The clue was skimpy -- just a little scrap of ribbon and a tiny note."
        )
    else:
        world.say(f"The clue was small, but it made the mystery feel bigger.")


def _reveal(world: World, child: Entity, source: SoundSource, tool: Tool) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.meters["mystery"] = 0
    world.say(
        f"Then came a quick {source.sound}! It was only {tool.phrase}, making "
        f"{tool.effect}."
    )
    world.say(
        f"{child.id} laughed when the trick was explained, because the scary "
        f"sound was safe after all."
    )


def _ending(world: World, child: Entity, setting: Setting, source: SoundSource) -> None:
    world.say(
        f"By morning, the chiffonier stood just as still as ever, and the little "
        f"sound had turned into a good story instead of a scary one."
    )
    world.say(
        f'{child.id} smiled at the quiet room and tucked the skimpy clue into a '
        f'drawer, ready to remember the mystery.'
    )


SETTINGS = {
    "bedroom": Setting("bedroom", "the bedroom", "murmuring", "a little too dark"),
    "hallway": Setting("hallway", "the hallway", "creaking", "long and shadowy"),
    "attic": Setting("attic", "the attic room", "rustling", "full of sleepy shadows"),
}

CLUES = {
    "ribbon": Clue("ribbon", "ribbon", "a skimpy ribbon", "under the chiffonier", skimpy=True, tags={"skimpy"}),
    "note": Clue("note", "note", "a tiny note", "beside the drawer", skimpy=True, tags={"skimpy"}),
    "button": Clue("button", "button", "a small button", "near the rug", skimpy=False, tags={"sketchy"}),
}

SOURCES = {
    "musicbox": SoundSource("musicbox", "music box", "tinkling", "music box drawer", harmless=True, tags={"sound"}),
    "toy": SoundSource("toy", "toy monkey", "clack-clack", "toy shelf", harmless=True, tags={"sound"}),
    "fan": SoundSource("fan", "little fan", "whirr", "curtain corner", harmless=True, tags={"sound"}),
}

TOOLS = {
    "string": Tool("string", "string", "a hidden string", "the chiffonier door had been tied to move with a pull", tags={"sound"}),
    "spring": Tool("spring", "spring", "a tiny spring", "the drawer was bouncing shut with a playful snap", tags={"sound"}),
    "speaker": Tool("speaker", "speaker", "a small speaker", "someone had made the room whisper on purpose", tags={"sound"}),
}

NAMES = ["Mina", "Theo", "Lia", "Ben", "Noa", "Iris", "Owen", "Clara"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    source: str
    tool: str
    name: str
    gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for clue in CLUES:
            for source in SOURCES:
                if clue in {"ribbon", "note", "button"} and source in SOURCES:
                    combos.append((setting, clue, source))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.source is None or c[2] == args.source)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, source = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting, clue, source, tool, name, gender)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, role="investigator"))
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    source = SOURCES[params.source]
    tool = TOOLS[params.tool]
    world.facts.update(child=child, setting=setting, clue=clue, source=source, tool=tool)

    _start_mystery(world, child, setting, clue)
    world.para()
    _hear_sound(world, source)
    _investigate(world, child, clue, source)
    world.para()
    _reveal(world, child, source, tool)
    _ending(world, child, setting, source)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the words "skimpy" and "chiffonier" and uses sound effects.',
        f"Tell a short mystery where {f['child'].id} hears a strange sound near a chiffonier, finds a skimpy clue, and learns the answer.",
        f"Write a gentle mystery with a safe surprise ending, a little clue, and at least one onomatopoeia sound effect.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    clue = f["clue"]
    source = f["source"]
    tool = f["tool"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who hears a strange sound and decides to investigate. The mystery stays small and safe the whole time."),
        ("What clue did the child find?",
         f"{clue.phrase} near the chiffonier. It was skimpy, but it still helped point the child toward the answer."),
        ("What made the sound?",
         f"It was only {tool.phrase}, making {tool.effect}. That is why the sound seemed spooky at first, but turned out harmless."),
        ("How did the story end?",
         f"It ended with the room quiet again in {setting.place}, and the chiffonier standing still. The scary sound became a good mystery instead of a real problem."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a chiffonier?",
         "A chiffonier is a kind of bedroom cabinet or tall dresser with drawers. People use it to store clothes and small things."),
        ("What does skimpy mean?",
         "Skimpy means small, thin, or not very much. A skimpy clue is tiny, but it can still matter."),
        ("What is a sound effect?",
         "A sound effect is a made-up sound used to help a story feel more lively or exciting. A story can use one to make a mystery feel spooky."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
valid(S,C,So) :- setting(S), clue(C), source(So).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for sid in SOURCES:
        lines.append(asp.fact("source", sid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


CURATED = [
    StoryParams("bedroom", "ribbon", "musicbox", "string", "Mina", "girl"),
    StoryParams("hallway", "note", "fan", "spring", "Theo", "boy"),
    StoryParams("attic", "button", "toy", "speaker", "Iris", "girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

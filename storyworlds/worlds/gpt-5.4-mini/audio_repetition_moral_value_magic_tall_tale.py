#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/audio_repetition_moral_value_magic_tall_tale.py
===============================================================================

A standalone storyworld for a tiny tall-tale domain about an enchanted audio
box, repeated sounds, and a moral choice that matters.

The premise is simple: a child finds a magical audio gadget that can repeat
sounds in a fancy way. The temptation is to use it for a boastful trick, but
the world makes that choice carry social weight. The better path is to use the
magic to help someone instead, and the ending proves the choice changed the
scene.

This world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a forward-moving world state that drives the prose
- a reasonableness gate that only allows plausible story shapes
- a Python gate mirrored by inline ASP rules
- story-grounded and world-knowledge QA generated from world state
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
MORAL_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    soundscape: str
    tall_image: str

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
class AudioThing:
    id: str
    label: str
    phrase: str
    repeats: bool
    magic: bool
    loud: bool
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
class ValueChoice:
    id: str
    virtue: str
    boast: str
    help_action: str
    ending_line: str
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["echoing"] < THRESHOLD:
            continue
        sig = ("echo", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.characters():
            ch.memes["wonder"] += 1
        out.append("__echo__")
    return out


def _r_shame(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.memes["boast"] < THRESHOLD:
            continue
        sig = ("shame", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["stubborn"] += 1
        out.append("__shame__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["peace"] += 1
        out.append("__peace__")
    return out


CAUSAL_RULES = [
    Rule("echo", "sound", _r_echo),
    Rule("shame", "social", _r_shame),
    Rule("kindness", "social", _r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend([s for s in out if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(audio: AudioThing, value: ValueChoice, setting: Setting) -> bool:
    return audio.magic and audio.repeats and value.virtue in {"kind", "humble", "helpful"} and bool(setting.place)


def conflict_possible(audio: AudioThing) -> bool:
    return audio.repeats and audio.magic


def outcome_of(params: "StoryParams") -> str:
    return "helpful" if params.choice == "kind" else "boastful"


def _do_magic(world: World, object_id: str, narrate: bool = True) -> None:
    obj = world.get(object_id)
    obj.meters["echoing"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, elder: Entity, setting: Setting, audio: AudioThing) -> None:
    hero.memes["curiosity"] += 1
    elder.memes["calm"] += 1
    world.say(
        f"On a bright day in {setting.place}, {hero.id} found a {audio.label} that "
        f"could repeat a voice like thunder rolling over a mountain."
    )
    world.say(
        f"The whole place was full of {setting.soundscape}, and the air felt wide "
        f"enough for a tall tale to stand up and walk."
    )


def tempt(world: World, hero: Entity, audio: AudioThing) -> None:
    hero.memes["boast"] += 1
    world.say(
        f'{hero.id} grinned. "I can make the {audio.label} say my words twice!" '
        f'{hero.pronoun().capitalize()} gave the button a daring look.'
    )
    world.say("Once, twice, and a third time, the idea came bouncing back.")
    _do_magic(world, "audio", narrate=False)


def warn(world: World, elder: Entity, hero: Entity, audio: AudioThing, value: ValueChoice) -> None:
    hero.memes["hearing"] += 1
    world.say(
        f'"Listen, {hero.id}," said {elder.id}. "A voice can be a toy, but it can '
        f"also be a promise. If you use that {audio.label} to brag, your words may "
        f'come back bigger than your manners."'
    )
    world.say(f'{elder.id} tapped {elder.pronoun("possessive")} heart and said, "{value.virtue} is the louder magic."')


def choose_path(world: World, hero: Entity, elder: Entity, audio: AudioThing, value: ValueChoice) -> str:
    if value.id == "kind":
        hero.memes["kindness"] += 1
        return "kind"
    hero.memes["stubborn"] += 1
    return "boast"


def boast_branch(world: World, hero: Entity, elder: Entity, audio: AudioThing, value: ValueChoice) -> None:
    world.say(
        f"{hero.id} did not listen. {hero.pronoun().capitalize()} hit the button, and "
        f'the {audio.label} cried out, "I am the grandest voice in the valley!"'
    )
    world.say("The sound came back again and again, bouncing off the rocks like a row of tin pots.")
    hero.memes["embarrassment"] += 1
    elder.memes["sadness"] += 1
    world.say(
        f"At last {hero.id} heard how silly it sounded. {value.ending_line}"
    )


def kind_branch(world: World, hero: Entity, elder: Entity, audio: AudioThing, value: ValueChoice) -> None:
    world.say(
        f'{hero.id} paused, then smiled. "{value.virtue.capitalize()} sounds better," '
        f'{hero.pronoun()} said, and handed the {audio.label} to {elder.id}.'
    )
    world.say(
        f'{elder.id} spoke one gentle sentence, and the {audio.label} answered it back in a warm echo.'
    )
    world.say(
        f"Together they used the little miracle to help a neighbor call for supper, "
        f"and the whole lane felt friendlier after that."
    )
    world.say(value.ending_line)


def tell(setting: Setting, audio: AudioThing, value: ValueChoice,
         hero_name: str = "Lena", hero_gender: str = "girl",
         elder_name: str = "Grandpa", elder_gender: str = "man") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    aobj = world.add(Entity(id="audio", kind="thing", type="thing", label=audio.label))
    world.facts["setting"] = setting
    world.facts["audio"] = audio
    world.facts["value"] = value

    setup(world, hero, elder, setting, audio)
    world.para()
    tempt(world, hero, audio)
    warn(world, elder, hero, audio, value)
    world.para()
    if choose_path(world, hero, elder, audio, value) == "kind":
        kind_branch(world, hero, elder, audio, value)
        world.facts["outcome"] = "kind"
    else:
        boast_branch(world, hero, elder, audio, value)
        world.facts["outcome"] = "boast"
    world.facts.update(hero=hero, elder=elder, audio_obj=aobj)
    return world


SETTINGS = {
    "harbor": Setting("harbor", "the harbor", "masts creaking and gulls laughing", "The masts leaned like giants listening."),
    "fair": Setting("fair", "the county fair", "bells ringing, fiddles calling, and children cheering", "The Ferris wheel stood like a silver moon."),
    "mesa": Setting("mesa", "the red mesa", "wind singing over the stones", "The mesa rose like a sleeping castle."),
}

AUDIO = {
    "horn": AudioThing("horn", "golden audio horn", "a golden audio horn", True, True, True, tags={"audio", "repeat"}),
    "box": AudioThing("box", "silver audio box", "a silver audio box", True, True, False, tags={"audio", "repeat"}),
    "shell": AudioThing("shell", "magic shell speaker", "a magic shell speaker", True, True, False, tags={"audio", "repeat"}),
}

VALUES = {
    "kind": ValueChoice("kind", "kind", "bragging", "help the whole lane", "That was the right kind of loud.", tags={"moral"}),
    "boast": ValueChoice("boast", "boastful", "bragging", "show off to everyone", "The echo reminded them that boasting sounds hollow.", tags={"moral"}),
}

GIRL_NAMES = ["Lena", "Mina", "Ruby", "Tessa", "Nina", "Ivy"]
BOY_NAMES = ["Jasper", "Ollie", "Perry", "Miles", "Theo", "Rowan"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    audio: str
    choice: str
    hero: str
    hero_gender: str
    elder: str
    elder_gender: str
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
    for s in SETTINGS:
        for a in AUDIO:
            for v in VALUES:
                if reasonableness_ok(AUDIO[a], VALUES[v], SETTINGS[s]) and conflict_possible(AUDIO[a]):
                    combos.append((s, a, v))
    return combos


KNOWLEDGE = {
    "audio": [("What is audio?", "Audio is sound that you can hear, like a voice, music, or a thunderous echo.")],
    "repeat": [("What does repeat mean?", "Repeat means to do or say something again. An echo is a kind of repeat.")],
    "echo": [("What is an echo?", "An echo is a sound that bounces back after you make it in a place like a canyon or a room.")],
    "moral": [("What is a moral?", "A moral is a lesson about how to act well, like being kind, honest, or helpful.")],
    "kind": [("Why is being kind important?", "Being kind helps other people feel safe and cared for, and it makes a story end better.")],
    "magic": [("What is magic in a story?", "Magic is something special that can do impossible things, like making a voice come back twice.")],
}
KNOWLEDGE_ORDER = ["audio", "repeat", "echo", "moral", "kind", "magic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child that includes the word "audio" and a magical repeat-sound gadget.',
        f"Tell a story where {f['hero'].id} finds enchanted audio and must choose between bragging and being kind.",
        f"Write a magical tall tale about a repeating voice, a moral choice, and a helpful ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    audio = f["audio"]
    value = f["value"]
    qa = [
        ("What did the child find?", f"{hero.id} found {audio.phrase}, a magical audio thing that could repeat sounds."),
        ("What did the older person warn about?", f"{elder.id} warned that a voice can be a promise, not just a toy, so the magic should be used carefully."),
        ("What choice mattered in the story?", f"The choice was between bragging and being kind. That choice decided whether the echo would sound foolish or helpful."),
    ]
    if f.get("outcome") == "kind":
        qa.append(("How did the story end?", f"It ended with kindness. {hero.id} shared the {audio.label} and used the echo to help someone instead of showing off."))
    else:
        qa.append(("How did the story end?", f"It ended with a lesson about bragging. {hero.id} heard the boast bounce back and learned that louder is not always better."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["audio"].tags) | set(world.facts["value"].tags)
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("mesa", "horn", "kind", "Lena", "girl", "Grandpa", "man"),
    StoryParams("fair", "box", "boast", "Jasper", "boy", "Grandma", "woman"),
]


def explain_rejection() -> str:
    return "(No story: this combination is too plain for a tall-tale audio magic world. Choose a repeating magic audio thing and a moral choice.)"


ASP_RULES = r"""
usable(S, A, V) :- setting(S), audio(A), value(V), repeats(A), magic(A), kind_value(V), place(S).
kind_value(kind).
outcome(kind) :- chosen(kind).
outcome(boast) :- not chosen(kind).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        lines.append(asp.fact("place", s))
    for a in AUDIO:
        lines.append(asp.fact("audio", a))
        if AUDIO[a].repeats:
            lines.append(asp.fact("repeats", a))
        if AUDIO[a].magic:
            lines.append(asp.fact("magic", a))
    for v in VALUES:
        lines.append(asp.fact("value", v))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show usable/3."))
    return sorted(set(asp.atoms(model, "usable")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, audio=None, choice=None, hero=None, hero_gender=None, elder=None, elder_gender=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: gate matches and generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale audio magic story world with repetition and a moral choice.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--audio", choices=AUDIO)
    ap.add_argument("--choice", choices=VALUES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
        raise StoryError(explain_rejection())
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
              and (args.audio is None or c[1] == args.audio)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, audio, choice = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder = args.elder or ("Grandma" if elder_gender == "woman" else "Grandpa")
    return StoryParams(setting, audio, choice, hero, hero_gender, elder, elder_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], AUDIO[params.audio], VALUES[params.choice],
                 params.hero, params.hero_gender, params.elder, params.elder_gender)
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
        print(asp_program("", "#show usable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, a, v in asp_valid_combos():
            print(f"  {s:8} {a:8} {v}")
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

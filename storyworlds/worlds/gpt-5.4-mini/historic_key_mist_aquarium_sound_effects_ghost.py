#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/historic_key_mist_aquarium_sound_effects_ghost.py
=================================================================================

A standalone story world for a small ghost-story aquarium tale.

Premise
-------
A child visits an aquarium, hears strange sound effects, and finds a historic key
in the misty old exhibit. The key opens a hidden music box or cabinet, a gentle
ghost appears, and the child helps set an old memory right.

This world keeps the story concrete and state-driven:
- typed entities have physical meters and emotional memes
- a little rule engine advances the world
- the aquarium mist and sound effects are world facts, not decoration
- the ending proves what changed

It supports the standard storyworld CLI:
    -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    misty: bool = True
    echo: bool = True
    historic: bool = True

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
class SoundEffect:
    id: str
    word: str
    text: str
    mood: str
    volume: int
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
class KeyObject:
    id: str
    label: str
    phrase: str
    historic: bool
    weight: str
    opens: str
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
class GhostState:
    id: str
    label: str
    bound_to: str
    longing: str
    calmed_by: str
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
        clone = World(self.setting)
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


def _r_mist(world: World) -> list[str]:
    out: list[str] = []
    if not world.setting.misty:
        return out
    if "mist" in world.fired:
        return out
    world.fired.add(("mist",))
    world.get("aquarium").meters["mist"] += 1
    for char in world.characters():
        char.memes["unease"] += 1
    out.append("__mist__")
    return out


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    if not world.setting.echo:
        return out
    if "echo" in world.fired:
        return out
    world.fired.add(("echo",))
    for char in world.characters():
        char.memes["alert"] += 1
    out.append("__echo__")
    return out


def _r_ghost_appears(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    box = world.get("musicbox")
    ghost = world.get("ghost")
    if child.memes["wonder"] < THRESHOLD:
        return out
    if box.meters["opened"] < THRESHOLD:
        return out
    if ("ghost",) in world.fired:
        return out
    world.fired.add(("ghost",))
    ghost.meters["present"] += 1
    ghost.memes["sad"] += 1
    out.append("__ghost__")
    return out


def _r_key_turns(world: World) -> list[str]:
    out: list[str] = []
    key = world.get("key")
    lock = world.get("cabinet")
    if key.meters["inserted"] < THRESHOLD:
        return out
    if lock.meters["open"] >= THRESHOLD:
        return out
    if ("unlock",) in world.fired:
        return out
    world.fired.add(("unlock",))
    lock.meters["open"] += 1
    out.append("__unlock__")
    return out


CAUSAL_RULES = [
    Rule("mist", "environment", _r_mist),
    Rule("echo", "sound", _r_echo),
    Rule("key_turns", "physical", _r_key_turns),
    Rule("ghost_appears", "social", _r_ghost_appears),
]


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


def tell_sound(world: World, se: SoundEffect) -> None:
    world.say(se.text)


def examine_key(world: World, child: Entity, key: Entity, box: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} spotted {key.phrase} in the glass case. "
        f"It looked old enough to belong to another century."
    )
    world.say(
        f'"{key.label.capitalize()}," {child.id} whispered, because the aquarium '
        f"was full of dripping glass, pale mist, and soft echoes."
    )


def hear_sound(world: World, child: Entity, se: SoundEffect) -> None:
    child.memes["alert"] += 1
    world.say(f"Then came a sound effect: {se.word} {se.word} {se.word}.")
    world.say(f"It was the kind of sound that made {child.id} pause and listen.")


def try_key(world: World, child: Entity, key: Entity, cabinet: Entity) -> None:
    child.memes["bravery"] += 1
    key.meters["inserted"] += 1
    world.say(
        f"{child.id} reached out and tried the {key.label}. "
        f"It slid into the little lock with a soft click."
    )
    propagate(world, narrate=False)


def open_cabinet(world: World, child: Entity, cabinet: Entity, key: Entity) -> None:
    if cabinet.meters["open"] < THRESHOLD:
        world.say("The lock gave way, and the cabinet door swung open with a groan.")
    else:
        world.say("The cabinet opened at once, as if it had been waiting for that key.")


def reveal_ghost(world: World, ghost: Entity) -> None:
    ghost.memes["sad"] += 0.5
    world.say(
        "Inside was a dusty little music box, and when it opened, a pale ghost "
        "rose like a curl of moonlight."
    )
    world.say(
        f'"At last," sighed the ghost, "someone heard me."'
    )


def help_ghost(world: World, child: Entity, ghost: Entity, setting: Setting) -> None:
    child.memes["kindness"] += 1
    ghost.memes["sad"] = max(0.0, ghost.memes["sad"] - 1.5)
    ghost.memes["peace"] += 2
    world.say(
        f"{child.id} did not run away. {child.id} stood still and listened, "
        f"while the mist drifted around the tanks."
    )
    world.say(
        f"The ghost pointed to a faded plaque. It marked a {setting.id} from a "
        f"historic part of the aquarium, where a keeper had once cared for the rooms."
    )
    world.say(
        "The child closed the music box and set it back in place, so the room could rest."
    )


def ending(world: World, child: Entity, ghost: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"When the child turned away, the mist looked thinner and kinder. "
        f"{child.id} heard one last soft {world.facts['sound'].word} from the hall, "
        f"and this time it sounded like a goodbye."
    )
    world.say(
        f"Outside the old room, {child.id} smiled at the wet glow of the aquarium "
        f"and knew the ghost had found peace at last."
    )


def tell(setting: Setting, sound: SoundEffect, key_obj: KeyObject, ghost_cfg: GhostState,
         child_name: str = "Mia", child_gender: str = "girl", parent_gender: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_gender, role="parent", label="the parent"))
    aquarium = world.add(Entity(id="aquarium", type="place", label="the aquarium"))
    cabinet = world.add(Entity(id="cabinet", type="thing", label="the cabinet"))
    key = world.add(Entity(id="key", type="thing", label=key_obj.label))
    key.meters["historic"] += 1 if key_obj.historic else 0
    key.meters["weight"] += 1
    box = world.add(Entity(id="musicbox", type="thing", label="the music box"))
    ghost = world.add(Entity(id="ghost", type="ghost", label=ghost_cfg.label))

    world.facts.update(sound=sound, key=key_obj, ghost_cfg=ghost_cfg)

    world.say(
        f"On a rainy afternoon, {child.id} and {parent.label_word} visited "
        f"{setting.place}. The windows were foggy, and the halls smelled like salt and stone."
    )
    world.say(
        f"Near an old exhibit, {child.id} found {key_obj.phrase}. "
        f"It was a {('historic' if key_obj.historic else 'plain')} little key, warm from waiting."
    )

    world.para()
    examine_key(world, child, key, cabinet)
    hear_sound(world, child, sound)

    world.para()
    try_key(world, child, key, cabinet)
    open_cabinet(world, child, cabinet, key)
    reveal_ghost(world, ghost)

    world.para()
    help_ghost(world, child, ghost, setting)
    ending(world, child, ghost)

    world.facts.update(
        child=child, parent=parent, aquarium=aquarium, cabinet=cabinet,
        key_entity=key, musicbox=box, ghost=ghost, outcome="peace",
    )
    return world


SETTINGS = {
    "aquarium": Setting("aquarium", "the aquarium", misty=True, echo=True, historic=True),
}

SOUNDS = {
    "drip": SoundEffect("drip", "drip", "Drip, drip, drip.", "unease", 1, {"sound", "mist"}),
    "clang": SoundEffect("clang", "clang", "Clang! The pipes answered from somewhere below.", "alert", 2, {"sound", "echo"}),
    "whoosh": SoundEffect("whoosh", "whoosh", "Whoosh... whoosh... the vents sighed through the hall.", "mystery", 1, {"sound", "ghost"}),
    "tap": SoundEffect("tap", "tap", "Tap-tap-tap went the water against the glass.", "wonder", 1, {"sound"}),
}

KEYS = {
    "historic": KeyObject("historic", "historic key", "a historic key", True, "small and cool", "the old cabinet", {"key", "historic"}),
    "brass": KeyObject("brass", "brass key", "a brass key from the old desk", True, "small and bright", "the cabinet", {"key"}),
}

GHOSTS = {
    "keeper": GhostState("keeper", "the keeper ghost", "aquarium", "to be remembered", "being listened to", {"ghost", "historic"}),
    "childghost": GhostState("childghost", "the little ghost", "musicbox", "to hear its song again", "the music box", {"ghost"}),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Sam"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    sound: str
    key: str
    ghost: str
    child_name: str
    child_gender: str
    parent_gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for sound in SOUNDS:
            for key in KEYS:
                for ghost in GHOSTS:
                    combos.append((s, sound, key, ghost))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story aquarium world with sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--key", choices=KEYS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    sound = args.sound or rng.choice(list(SOUNDS))
    key = args.key or rng.choice(list(KEYS))
    ghost = args.ghost or rng.choice(list(GHOSTS))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    return StoryParams(setting, sound, key, ghost, name, gender, parent_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a 3-to-5-year-old set in {world.setting.place} that includes the words "historic", "key", and "mist".',
        f"Tell a gentle haunted-aquarium story where {f['child'].id} hears sound effects, finds an old key, and helps a lonely ghost.",
        "Write a child-facing ghost story with soft spooky sounds, a misty aquarium, and a kind ending where the ghost calms down.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    key = world.facts["key"]
    sound = world.facts["sound"]
    return [
        QAItem(
            question="What did the child find in the aquarium?",
            answer=f"The child found {key.phrase} near an old exhibit. It mattered because the key opened the hidden cabinet in the misty room."
        ),
        QAItem(
            question="What sound effects were heard?",
            answer=f"The story used {sound.word} as a sound effect. That sound made the aquarium feel spooky, but it also helped the child notice that something was waiting to be found."
        ),
        QAItem(
            question="What happened when the key turned?",
            answer="The cabinet opened, and a ghost rose out of the old music box. The child stayed calm and helped the ghost settle down instead of running away."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {child.id} smiling in the aquarium while the ghost found peace. The mist felt thinner at the end, which showed that the lonely feeling had changed."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem("What is mist?", "Mist is a light cloud of tiny water drops in the air. It makes a place look foggy and soft."),
        QAItem("What does a historic thing mean?", "A historic thing is old and connected to the past. People keep historic things because they tell part of a story."),
        QAItem("What does a key do?", "A key unlocks something that is closed. It can open a lock when the right key fits."),
        QAItem("What are sound effects?", "Sound effects are special sounds that help a story feel real or spooky. They can make a quiet place feel alive."),
    ]
    return out


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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("aquarium", "drip", "historic", "keeper", "Mia", "girl", "mother"),
    StoryParams("aquarium", "whoosh", "brass", "keeper", "Leo", "boy", "father"),
]


def explain_rejection() -> str:
    return "(No story: this world only supports the aquarium setting with a historic key and a misty ghost tale.)"


ASP_RULES = r"""
mist(aquarium) :- setting(aquarium), misty(aquarium).
echo(aquarium) :- setting(aquarium), echoing(aquarium).
unlock :- chosen_key(K), historic_key(K).
ghost_appears :- unlock, kind ghost.
peace :- ghost_appears, child_kind(C), kind child.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.misty:
            lines.append(asp.fact("misty", sid))
        if s.echo:
            lines.append(asp.fact("echoing", sid))
    for kid in KEYS:
        lines.append(asp.fact("historic_key", kid))
    for gid in GHOSTS:
        lines.append(asp.fact("kind", gid))
    lines.append(asp.fact("kind", "child"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        _ = asp.one_model(asp_program("", "#show mist/1."))
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable or failed: {exc}")
        return 1
    return 0


def tell_sample(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SOUNDS[params.sound],
        KEYS[params.key],
        GHOSTS[params.ghost],
        params.child_name,
        params.child_gender,
        params.parent_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_sample(params)


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
        print(asp_program("", "#show mist/1.\n#show unlock/0.\n#show ghost_appears/0.\n#show peace/0."))
        return
    if args.verify:
        # smoke test: ordinary generation must work
        sample = generate(resolve_params(argparse.Namespace(setting=None, sound=None, key=None, ghost=None,
                                                            child_name=None, child_gender=None,
                                                            parent_gender=None), random.Random(7)))
        if not sample.story.strip():
            raise SystemExit(1)
        sys.exit(asp_verify())
    if args.asp:
        print("ASP support is minimal in this world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

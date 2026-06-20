#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/data_rehearsal_happy_ending_friendship_sound_effects.py
=======================================================================================

A standalone story world for a tiny mystery-themed rehearsal domain: children
collect a little piece of data, rehearse a clue show, lean on friendship, make
sound effects, and end with a happy reveal.

The world is small on purpose:
- a scout notices a strange sound,
- friends rehearse a pretend mystery,
- the data points to the missing object,
- the sound effect becomes a clue instead of a scare,
- the ending proves the friendship helped.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/data_rehearsal_happy_ending_friendship_sound_effects.py
    python storyworlds/worlds/gpt-5.4-mini/data_rehearsal_happy_ending_friendship_sound_effects.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/data_rehearsal_happy_ending_friendship_sound_effects.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



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
    clue_sound: str
    mood: str

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
class Prop:
    id: str
    label: str
    phrase: str
    category: str
    makes_sound: bool = False
    searchable: bool = True
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
class Sound:
    id: str
    onomatopoeia: str
    source_hint: str
    intensity: int
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
        return World(self.setting, copy.deepcopy(self.entities), set(self.fired), [[]], dict(self.facts))

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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_joy(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("joy", 0.0) >= THRESHOLD and ("joy", e.id) not in world.fired:
            world.fired.add(("joy", e.id))
            out.append(f"{e.id} felt braver the more the plan sounded right.")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("data_found") and not world.facts.get("clue_spoken"):
        world.facts["clue_spoken"] = True
        out.append("The little bit of data fit the mystery like the last piece of a puzzle.")
    return out


CAUSAL_RULES = [Rule("joy", _r_joy), Rule("clue", _r_clue)]


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.makes_sound:
            lines.append(asp.fact("makes_sound", pid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("intensity", sid, s.intensity))
    lines.append(asp.fact("threshold", THRESHOLD))
    return "\n".join(lines)


ASP_RULES = r"""
mystery_clue(S) :- sound(S), intensity(S, I), threshold(T), I >= T.
happy_ending :- mystery_clue(_).
"""


def asp_program(show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_clue/1.\n#show happy_ending/0."))
    asp_clues = set(asp.atoms(model, "mystery_clue"))
    py_clues = {sid for sid, s in SOUNDS.items() if s.intensity >= THRESHOLD}
    rc = 0
    if {c[0] for c in asp_clues} != py_clues:
        print("MISMATCH: ASP clue inference differs from Python.")
        rc = 1
    if not py_clues:
        print("MISMATCH: no clues inferred.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: generation smoke test failed: {exc}")
        rc = 1
    else:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


SETTINGS = {
    "library": Setting("library", "the library", "tap tap", "quiet"),
    "museum": Setting("museum", "the museum hallway", "click click", "curious"),
    "attic": Setting("attic", "the attic", "thump thump", "mysterious"),
}

PROPS = {
    "notebook": Prop("notebook", "notebook", "a small notebook", "data", searchable=True, tags={"data"}),
    "lamp": Prop("lamp", "lamp", "a little lamp", "tool", makes_sound=False, searchable=True),
    "box": Prop("box", "box", "a cardboard box", "container", searchable=True),
    "ribbon": Prop("ribbon", "ribbon", "a blue ribbon", "clue", searchable=True),
}

SOUNDS = {
    "tap": Sound("tap", "tap tap", "a nervous finger on the table", 1, tags={"sound"}),
    "rustle": Sound("rustle", "rustle rustle", "papers in a stack", 2, tags={"sound"}),
    "clatter": Sound("clatter", "clatter!", "a box tipping over", 3, tags={"sound"}),
}

NAMES = {
    "girl": ["Mia", "Lena", "Nora", "Ava", "Zoe"],
    "boy": ["Noah", "Eli", "Theo", "Max", "Ben"],
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    prop: str
    sound: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery rehearsal story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, p, snd) for s in SETTINGS for p in PROPS for snd in SOUNDS if PROPS[p].searchable]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prop is None or c[1] == args.prop)
              and (args.sound is None or c[2] == args.sound)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, sound = rng.choice(sorted(combos))
    hg = args.hero_gender or rng.choice(["girl", "boy"])
    fg = args.friend_gender or ("boy" if hg == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES[hg])
    friend = args.friend or rng.choice([n for n in NAMES[fg] if n != hero])
    return StoryParams(setting, hero, hg, friend, fg, prop, sound)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(params.hero, "character", params.hero_gender, role="hero", traits=["curious"], memes={"joy": 1.0}))
    friend = world.add(Entity(params.friend, "character", params.friend_gender, role="friend", traits=["helpful"], memes={"joy": 1.0}))
    prop = world.add(Entity("prop", "thing", "thing", label=PROPS[params.prop].label))
    snd = SOUNDS[params.sound]

    world.say(
        f"One quiet evening in {world.setting.place}, {hero.id} and {friend.id} were "
        f"rehearsing a mystery show. They whispered, because mysteries sound better when the room is calm."
    )
    world.say(
        f"{hero.id} opened {PROPS[params.prop].phrase} and found a little page of data inside."
        f" {friend.id} leaned close, and together they listened for {snd.onomatopoeia}."
    )
    world.para()
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.facts["data_found"] = True
    world.say(
        f'"Let’s play it again," said {friend.id}. {hero.id} tapped the table and made '
        f'sound effects for the clues: {SOUNDS[params.sound].onomatopoeia}.'
    )
    propagate(world)
    world.para()
    world.say(
        f"The clue led them to the {prop.label}, where a tiny lost ribbon was hiding under it."
        f" That was the missing piece of the mystery."
    )
    world.say(
        f"{friend.id} laughed, {hero.id} laughed, and the rehearsal turned into a happy ending."
        f" They put the data back in the notebook and promised to keep solving mysteries together."
    )
    world.facts.update(hero=hero, friend=friend, prop=prop, sound=snd, outcome="happy")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a young child that includes the words "data" and "rehearsal".',
        f"Tell a happy mystery about {f['hero'].id} and {f['friend'].id} using sound effects to practice a show.",
        f"Write a friendship story where a clue is found during a rehearsal and the ending is cheerful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    return [
        QAItem(
            question="What were the children doing?",
            answer=f"They were rehearsing a mystery show and looking at data to help solve it. Their practice made the pretend mystery feel real, but still fun."
        ),
        QAItem(
            "How did the sound effects help?",
            f"The sound effects helped them notice the clue hidden in the room. When they copied the sound, they found the missing piece of the mystery."
        ),
        QAItem(
            "How did the story end?",
            f"It ended happily, because {hero.id} and {friend.id} solved the puzzle together. They stayed friends and felt proud of their rehearsal."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is data?", "Data is information you collect and look at to learn something. It can be notes, numbers, or clues."),
        QAItem("What is a rehearsal?", "A rehearsal is a practice run before the real show. It helps people get ready and feel confident."),
        QAItem("What are sound effects?", "Sound effects are special sounds that help tell a story or make a show feel exciting. They can be quiet taps, rustles, or big clatters."),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams("library", "Mia", "girl", "Noah", "boy", "notebook", "tap"),
    StoryParams("museum", "Eli", "boy", "Ava", "girl", "box", "clatter"),
    StoryParams("attic", "Nora", "girl", "Theo", "boy", "ribbon", "rustle"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify_smoke() -> int:
    rc = asp_verify()
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: smoke test failed: {exc}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery_clue/1.\n#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify_smoke())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_clue/1.\n#show happy_ending/0."))
        print(f"mystery clues: {', '.join(sorted(x[0] for x in asp.atoms(model, 'mystery_clue')))}")
        print("happy ending: yes" if asp.atoms(model, "happy_ending") else "happy ending: no")
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

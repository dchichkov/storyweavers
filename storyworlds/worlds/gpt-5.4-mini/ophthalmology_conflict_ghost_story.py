#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ophthalmology_conflict_ghost_story.py
=====================================================================

A standalone storyworld for a small, child-facing ghost-story conflict set in an
ophthalmology clinic.

Premise
-------
A child visits an eye doctor place at dusk. The room feels spooky, a "ghost"
seems to be making the lights blink, and a conflict grows when one child wants
to peek into a dark room while another child warns them not to. The turn is that
the strange ghostly signs come from a practical cause in the clinic, the grown-up
fixes the problem, and the children leave with a calm, bright ending image.

The world is modeled with typed entities, physical meters, and emotional memes.
The story is not a frozen paragraph: the prose comes from state changes such as
fear rising, conflict peaking, and the clinic lights turning steady again.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/ophthalmology_conflict_ghost_story.py
    python storyworlds/worlds/gpt-5.4-mini/ophthalmology_conflict_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/ophthalmology_conflict_ghost_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/ophthalmology_conflict_ghost_story.py --trace
    python storyworlds/worlds/gpt-5.4-mini/ophthalmology_conflict_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/ophthalmology_conflict_ghost_story.py --verify
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
    label: str
    time: str
    mood: str

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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    use: str
    makes_light: bool = False
    suspicious: bool = False
    tags: set[str] = field(default_factory=set)

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
class ConflictBeat:
    id: str
    label: str
    reason: str
    tension: int
    tags: set[str] = field(default_factory=set)

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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["spooky"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        e.memes["alert"] += 1
        out.append("")
    return out


def _r_conflict(world: World) -> list[str]:
    hero = world.entities.get("hero")
    guide = world.entities.get("guide")
    if not hero or not guide:
        return []
    if hero.memes["stubborn"] < THRESHOLD or guide.memes["warning"] < THRESHOLD:
        return []
    sig = ("conflict", "main")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["conflict"] += 1
    guide.memes["conflict"] += 1
    return ["__conflict__"]


def _r_calm(world: World) -> list[str]:
    room = world.entities.get("clinic")
    tech = world.entities.get("tech")
    if not room or not tech:
        return []
    if room.meters["glitch"] < THRESHOLD:
        return []
    sig = ("calm", "main")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["glitch"] = 0.0
    tech.memes["calm"] += 1
    return []


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("conflict", "social", _r_conflict), Rule("calm", "physical", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            for s in rule.apply(world):
                if s:
                    changed = True
                    if not s.startswith("__"):
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard(item: Item) -> bool:
    return item.suspicious


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for item in ITEMS:
            for beat in BEATS:
                if hazard(ITEMS[item]):
                    combos.append((setting, item, beat))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    beat: str
    child: str
    child_gender: str
    companion: str
    companion_gender: str
    adult: str
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


SETTINGS = {
    "clinic": Setting("clinic", "the ophthalmology clinic", "late afternoon", "dim and hushy"),
    "hall": Setting("hall", "the waiting hall", "evening", "echoey"),
}

ITEMS = {
    "eye_chart": Item("eye_chart", "an eye chart", "a big eye chart with tiny black letters", "paper", "to test vision", tags={"ophthalmology"}),
    "lamp": Item("lamp", "a test lamp", "a bright little test lamp", "tool", "to shine light", makes_light=True, tags={"ophthalmology", "light"}),
    "glasses": Item("glasses", "glasses", "a pair of glasses", "wearable", "to help see", tags={"ophthalmology"}),
    "shadow": Item("shadow", "a strange shadow", "a strange shadow by the door", "mystery", "to worry about", suspicious=True, tags={"ghost"}),
}

BEATS = {
    "blink": ConflictBeat("blink", "blinking lights", "the lights keep blinking", 2, tags={"ghost"}),
    "whisper": ConflictBeat("whisper", "whispering hallway", "the hallway sounds like whispering", 1, tags={"ghost"}),
    "cold": ConflictBeat("cold", "cold draft", "a cold draft slips under the door", 2, tags={"ghost"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "June"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Milo"]
TRAITS = ["brave", "careful", "curious", "quiet", "stubborn"]


def reasonableness_gate(item: Item) -> bool:
    return hazard(item)


def tell(setting: Setting, item: Item, beat: ConflictBeat, child: str, child_gender: str, companion: str, companion_gender: str, adult: str) -> World:
    world = World()
    hero = world.add(Entity("hero", "character", child_gender, role="child"))
    guide = world.add(Entity("guide", "character", companion_gender, role="companion"))
    tech = world.add(Entity("tech", "character", "woman", role="adult"))
    clinic = world.add(Entity("clinic", "thing", "clinic", label=setting.label))
    item_ent = world.add(Entity("item", "thing", item.kind, label=item.label))
    room = world.add(Entity("room", "thing", "room", label=setting.label))
    hero.memes["stubborn"] = 1.0
    guide.memes["warning"] = 1.0
    room.meters["glitch"] = 1.0 if beat.id in {"blink", "cold"} else 0.0
    hero.meters["spooky"] = 1.0
    guide.meters["spooky"] = 1.0
    world.say(f"At {setting.label}, {child} and {companion} waited while the ophthalmology clinic grew quiet and dim.")
    world.say(f"{beat.reason.capitalize()}, and that made the room feel like a ghost story.")
    world.para()
    world.say(f"{child} wanted to peek at {item.phrase}, because the tiny light looked like it might explain the shadows.")
    world.say(f"But {companion} shook {companion}'s head and warned that a spooky place was still a real place, not a game.")
    if beat.tension >= 2:
        world.say(f"The two children argued for a moment, and the conflict felt bigger than the little room.")
    propagate(world, narrate=False)
    world.para()
    world.say(f"Then {adult} came in, laughed softly, and showed that the ghostly sign was only a clinic problem that could be fixed.")
    room.meters["glitch"] = 0.0
    tech.memes["calm"] += 1
    world.say(f"The blinking stopped, the lights turned steady, and the ophthalmology tools looked plain and friendly again.")
    world.say(f"{child} and {companion} stood together under the bright lamp, no longer afraid, with their argument gone quiet.")
    world.say(f"By the end, the room felt warm, and the only ghost was the one they had imagined in the dark.")
    world.facts.update(hero=hero, guide=guide, tech=tech, clinic=clinic, item=item, beat=beat, setting=setting, outcome="resolved")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story for a 3-to-5-year-old that takes place in an ophthalmology clinic and includes the word "ophthalmology".',
        f"Tell a spooky but gentle story where {f['hero'].id} and {f['guide'].id} disagree about a strange shadow in the clinic, then the grown-up explains it.",
        f"Write a conflict story in a dim eye-doctor room where a ghostly feeling turns into a sensible fix and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    guide = f["guide"].id
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero} and {guide}, two children in an ophthalmology clinic. The story also includes the grown-up who helps them calm down."
        ),
        QAItem(
            question="Why did the children have a conflict?",
            answer=f"{hero} wanted to peek at the strange-looking light and shadow, but {guide} thought that was a bad idea. They argued because the room felt spooky and both of them wanted different things."
        ),
        QAItem(
            question="How did the story end?",
            answer="The grown-up explained the problem, the blinking stopped, and the room became bright and ordinary again. The children ended the story standing together, safe and calm."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ophthalmology?",
            answer="Ophthalmology is the part of medicine that deals with eyes. An ophthalmology clinic is a place where people go to have their eyes checked."
        ),
        QAItem(
            question="Why can a dark room feel spooky?",
            answer="A dark room can hide shapes and make small sounds seem bigger. When people cannot see well, their imagination can fill in ghostly ideas."
        ),
        QAItem(
            question="What does a doctor do in an eye clinic?",
            answer="An eye doctor checks how well someone can see and uses special tools and lights. The doctor helps keep eyes healthy and explains what the tools are for."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World QA ==")
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
    return "\n".join(lines)


ASP_RULES = r"""
hazard(I) :- item(I), suspicious(I).
valid(S, I, B) :- setting(S), item(I), beat(B), hazard(I).
conflict :- stubborn(hero), warning(guide).
resolved :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.suspicious:
            lines.append(asp.fact("suspicious", iid))
    for bid in BEATS:
        lines.append(asp.fact("beat", bid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghostly ophthalmology conflict storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--beat", choices=BEATS)
    ap.add_argument("--child")
    ap.add_argument("--companion")
    ap.add_argument("--adult")
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
        raise StoryError("No valid story combinations.")
    setting, item, beat = rng.choice(sorted(combos))
    child = args.child or rng.choice(GIRL_NAMES + BOY_NAMES)
    companion = args.companion or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child])
    adult = args.adult or rng.choice(["doctor", "nurse", "parent"])
    child_gender = "girl" if child in GIRL_NAMES else "boy"
    companion_gender = "girl" if companion in GIRL_NAMES else "boy"
    return StoryParams(setting, item, beat, child, child_gender, companion, companion_gender, adult)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], BEATS[params.beat], params.child, params.child_gender, params.companion, params.companion_gender, params.adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
    StoryParams("clinic", "shadow", "blink", "Mina", "girl", "Owen", "boy", "doctor"),
    StoryParams("clinic", "eye_chart", "cold", "Finn", "boy", "Nora", "girl", "nurse"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{t}" for t in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

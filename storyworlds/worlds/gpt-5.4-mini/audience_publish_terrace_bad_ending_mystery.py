#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/audience_publish_terrace_bad_ending_mystery.py
===============================================================================

A standalone story world for a tiny mystery about an audience, a planned
publish, and a terrace, with a bad ending that still feels complete and
state-driven.

The seed idea is a child or small group preparing to publish a mystery note for
an audience, only to make one wrong choice on the terrace. The wrong choice
creates a clue-chain, a warning, and finally a sad ending image that proves what
changed.
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
    ambience: str
    allows_terrace: bool = True

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
class StoryProp:
    id: str
    label: str
    phrase: str
    threat: str
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
class Choice:
    id: str
    sense: int
    delay: int
    text: str
    fail: str
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
        c.facts = copy.deepcopy(self.facts)
        return c


def _rule_tension(world: World) -> list[str]:
    out: list[str] = []
    if world.get("scene").meters["uncertainty"] >= THRESHOLD:
        if ("tension",) not in world.fired:
            world.fired.add(("tension",))
            for ent in list(world.entities.values()):
                if ent.role in {"reader", "author"}:
                    ent.memes["worry"] += 1
            out.append("__tension__")
    return out


def _rule_alarm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("prop").meters["lost"] >= THRESHOLD:
        sig = ("alarm",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("scene").meters["danger"] += 1
            out.append("__alarm__")
    return out


CAUSAL_RULES = [_rule_tension, _rule_alarm]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_choices() -> list[Choice]:
    return [c for c in CHOICES.values() if c.sense >= SENSE_MIN]


def valid_combo(setting: Setting, prop: StoryProp, choice: Choice) -> bool:
    return setting.allows_terrace and prop.id in {"manuscript", "letter"} and choice.sense >= SENSE_MIN


def story_severity(prop: StoryProp, delay: int) -> int:
    return 2 + delay if prop.id == "manuscript" else 1 + delay


def choice_contained(choice: Choice, prop: StoryProp, delay: int) -> bool:
    return choice.delay >= story_severity(prop, delay)


def predict_loss(world: World, prop_id: str) -> dict:
    sim = world.copy()
    sim.get("prop").meters["lost"] += 1
    propagate(sim, narrate=False)
    return {
        "lost": sim.get("prop").meters["lost"] >= THRESHOLD,
        "danger": sim.get("scene").meters["danger"],
    }


def ask_about_publish(world: World, a: Entity, prop: StoryProp) -> None:
    world.say(
        f"An audience was waiting in the hall below, and {a.id} had promised to "
        f"publish something before dusk. On the terrace, the air felt thin and "
        f"quiet, like the whole building was holding its breath."
    )


def hint_mystery(world: World, a: Entity, prop: StoryProp) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f"{a.id} found a folded page with a smudged corner. It looked important, "
        f"but no name was written on it."
    )
    world.say(
        f'"If we publish this note," {a.id} whispered, "maybe the audience will '
        f'finally understand what happened."'
    )


def warn(world: World, b: Entity, a: Entity, prop: StoryProp, parent: Entity) -> None:
    pred = predict_loss(world, "prop")
    b.memes["worry"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{b.id} looked from the page to the dark terrace railing. '
        f'"{a.id}, wait. If you leave {prop.label} out here, the wind could '
        f'send it away before anyone reads it. We should tell {parent.label_word}."'
    )


def defy(world: World, a: Entity, b: Entity, prop: StoryProp) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'{a.id} shook {a.pronoun("possessive")} head. "No. The audience is '
        f'waiting now." So {a.id} carried the page closer to the edge.'
    )


def lose_prop(world: World, prop: StoryProp) -> None:
    world.get("prop").meters["lost"] += 1
    world.get("scene").meters["uncertainty"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A gust slipped over the terrace. The page twisted once, then slid from "
        f"{prop.label} and vanished into the dark."
    )


def shout(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!" {b.id} cried, but the wind swallowed half the sound.')


def recover_fail(world: World, parent: Entity, choice: Choice, prop: StoryProp) -> None:
    world.say(
        f"{parent.label_word.capitalize()} ran up the stairs, but {choice.fail}."
    )
    world.say(
        f"The terrace stayed empty, and whatever the page had said was gone with it."
    )


def lesson_bad(world: World, parent: Entity, a: Entity, b: Entity, prop: StoryProp) -> None:
    for kid in (a, b):
        kid.memes["sadness"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"{parent.label_word.capitalize()} knelt by the terrace door and wrapped "
        f"the children in a hug. " 
        f'"Sometimes a mystery stays a mystery," {parent.pronoun()} said softly. '
        f'"And sometimes waiting is the only safe choice, even when the audience is '
        f'watching."'
    )
    world.say(
        f"{a.id} stared at the empty ledge. The only answer left was the wind and a "
        f"cold, blank place where the page used to be."
    )


def rescue_possible(choice: Choice, prop: StoryProp, delay: int) -> bool:
    return choice.delay >= story_severity(prop, delay)


def tell(setting: Setting, prop: StoryProp, choice: Choice,
         author_name: str = "Mina", author_gender: str = "girl",
         reader_name: str = "Jasper", reader_gender: str = "boy",
         parent_type: str = "mother", delay: int = 1) -> World:
    world = World()
    author = world.add(Entity(id=author_name, kind="character", type=author_gender, role="author"))
    reader = world.add(Entity(id=reader_name, kind="character", type=reader_gender, role="reader"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    scene = world.add(Entity(id="scene", type="scene", label="the terrace"))
    prop_ent = world.add(Entity(id="prop", type="prop", label=prop.label))

    scene.meters["uncertainty"] = 1.0
    author.memes["curiosity"] = 1.0
    reader.memes["trust"] = 1.0

    ask_about_publish(world, author, prop)
    hint_mystery(world, author, prop)

    world.para()
    warn(world, reader, author, prop, parent)
    defy(world, author, reader, prop)

    world.para()
    lose_prop(world, prop)
    shout(world, reader, parent)

    if rescue_possible(choice, prop, delay):
        recover_fail(world, parent, choice, prop)
    else:
        recover_fail(world, parent, choice, prop)

    lesson_bad(world, parent, author, reader, prop)

    world.facts.update(
        setting=setting,
        prop_cfg=prop,
        choice=choice,
        author=author,
        reader=reader,
        parent=parent,
        outcome="bad",
        lost=world.get("prop").meters["lost"] >= THRESHOLD,
        danger=world.get("scene").meters["danger"],
    )
    return world


SETTINGS = {
    "terrace": Setting("terrace", "the terrace", "thin air and a view over the yard", True),
    "library": Setting("library", "the library balcony", "quiet pages and a watchful hush", True),
    "museum": Setting("museum", "the museum terrace", "marble steps and a long drop of silence", True),
}

PROPS = {
    "manuscript": StoryProp("manuscript", "manuscript", "the manuscript page", "easy to lose", {"paper", "publish"}),
    "letter": StoryProp("letter", "letter", "the letter", "easy to lose", {"paper", "publish"}),
    "poster": StoryProp("poster", "poster", "the poster", "easy to lose", {"paper", "publish"}),
}

CHOICES = {
    "pin": Choice("pin", 1, 1, "pinned it to the board", "the pin slipped and the wind took it anyway", {"publish"}),
    "clip": Choice("clip", 2, 1, "clipped it to a folder", "the clip bent, and the page still flew free", {"publish"}),
    "envelope": Choice("envelope", 3, 0, "put it in an envelope", "the envelope tore open at the edge", {"publish"}),
    "stone": Choice("stone", 1, 2, "held it under a stone", "the stone rolled away before help arrived", {"publish"}),
}

NAMES_GIRL = ["Mina", "Ivy", "Nora", "Lena", "Clara", "Ruby"]
NAMES_BOY = ["Jasper", "Theo", "Otis", "Eli", "Noah", "Felix"]
TRAITS = ["careful", "curious", "quiet", "thoughtful", "bold"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    prop: str
    choice: str
    author: str
    author_gender: str
    reader: str
    reader_gender: str
    parent: str
    trait: str
    delay: int = 1
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for pid, p in PROPS.items():
            for cid, c in CHOICES.items():
                if valid_combo(s, p, c):
                    out.append((sid, pid, cid))
    return out


ASP_RULES = r"""
valid(S, P, C) :- setting(S), prop(P), choice(C), compatible(S, P, C).
compatible(S, P, C) :- setting(S), prop(P), choice(C), terrace_ok(S), publishable(P), sensible(C).
terrace_ok(S) :- setting(S), allows_terrace(S).
publishable(P) :- prop(P), publish_topic(P).
sensible(C) :- choice(C), sense(C, V), sense_min(M), V >= M.
outcome(bad) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.allows_terrace:
            lines.append(asp.fact("allows_terrace", sid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("publish_topic", pid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    rc = 0 if a == b else 1
    if rc == 0:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        print("MISMATCH in gate:")
        print("only in asp:", sorted(a - b))
        print("only in python:", sorted(b - a))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate() produced a non-empty story.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.prop is None or c[1] == args.prop)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, choice = rng.choice(sorted(combos))
    prop_cfg = PROPS[prop]
    author_gender = rng.choice(["girl", "boy"])
    reader_gender = "boy" if author_gender == "girl" else "girl"
    author = rng.choice(NAMES_GIRL if author_gender == "girl" else NAMES_BOY)
    reader = rng.choice(NAMES_BOY if reader_gender == "boy" else NAMES_GIRL)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, prop, choice, author, author_gender, reader, reader_gender, parent, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a child that includes the words "audience", "publish", and "terrace".',
        f'Tell a bad-ending mystery where {f["author"].id} tries to publish {f["prop_cfg"].label} for an audience on the terrace, but the plan fails.',
        f'Write a tense, child-friendly mystery about a note, a waiting audience, and a windy terrace, ending sadly but clearly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    author, reader, parent, prop = f["author"], f["reader"], f["parent"], f["prop_cfg"]
    return [
        QAItem(
            question="What was the audience waiting for?",
            answer=f"The audience was waiting for the mystery to be published. They expected the note to explain what had happened, but the page was lost before anyone could read it."
        ),
        QAItem(
            question="Why was the terrace important?",
            answer=f"The terrace was the place where the children tried to handle the page. It was windy there, so the page could slip away easily and turn the plan into a problem."
        ),
        QAItem(
            question=f"What went wrong when {author.id} tried to publish the page?",
            answer=f"{author.id} tried to keep {prop.label} near the terrace edge, but the wind took it. That left the story unfinished and made the ending sad."
        ),
        QAItem(
            question="Did the parent fix everything in time?",
            answer="No. The parent arrived too late to save the page, so the mystery stayed unsolved and the children were left with only the empty ledge."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an audience?",
            answer="An audience is a group of people who are waiting to hear, see, or read something. They listen or watch while the story or performance happens."
        ),
        QAItem(
            question="What does publish mean?",
            answer="To publish something means to share it with other people so they can read it. A published note or story is no longer private."
        ),
        QAItem(
            question="What is a terrace?",
            answer="A terrace is a flat outdoor place attached to a building, often with open air and a railing. Wind can move light paper there very easily."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROPS[params.prop], CHOICES[params.choice],
                 params.author, params.author_gender, params.reader, params.reader_gender,
                 params.parent, params.delay)
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
    StoryParams("terrace", "manuscript", "pin", "Mina", "girl", "Jasper", "boy", "mother", "curious"),
    StoryParams("library", "letter", "clip", "Theo", "boy", "Lena", "girl", "father", "quiet"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

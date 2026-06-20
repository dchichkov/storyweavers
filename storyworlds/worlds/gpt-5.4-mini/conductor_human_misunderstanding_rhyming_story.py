#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/conductor_human_misunderstanding_rhyming_story.py
==================================================================================

A small standalone storyworld about a conductor, a human, and a misunderstanding.

Premise:
- A human meets a conductor in a tiny train-world.
- A misunderstanding grows because the human thinks the conductor means one thing,
  while the conductor means another.
- A calm explanation clears the mix-up.
- The ending lands on a bright, rhyming image: the train rolls on, and both feel
  glad they spoke clearly.

This world keeps the prose child-facing and lightly rhyming, with state-driven
beats rather than a frozen paragraph. It supports the standard Storyweavers CLI,
Q&A sets, tracing, JSON, and an inline ASP twin.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/conductor_human_misunderstanding_rhyming_story.py
    python storyworlds/worlds/gpt-5.4-mini/conductor_human_misunderstanding_rhyming_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/conductor_human_misunderstanding_rhyming_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Misunderstanding:
    id: str
    wrong_meaning: str
    right_meaning: str
    trigger_word: str
    repair_phrase: str

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
        clone.facts = copy.deepcopy(self.facts)
        return clone

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
@dataclass
class StoryParams:
    setting: str
    misunderstanding: str
    conductor_name: str
    conductor_type: str
    human_name: str
    human_type: str
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
    "platform": Setting("platform", "the platform", "A silver train waited by the track, with wind in the air."),
    "station": Setting("station", "the station", "Bright signs blinked, and a clock ticked above the gate."),
    "car": Setting("car", "the train car", "Seats squeaked softly, and the rails hummed below."),
}

MISUNDERSTANDINGS = {
    "whistle": Misunderstanding(
        "whistle",
        wrong_meaning="a silly song to start a parade",
        right_meaning="the signal that the train should go",
        trigger_word="whistle",
        repair_phrase="the conductor's whistle was a signal, not a song",
    ),
    "ticket": Misunderstanding(
        "ticket",
        wrong_meaning="a toy card for a game",
        right_meaning="the paper that lets a rider travel",
        trigger_word="ticket",
        repair_phrase="the ticket was for riding, not for play",
    ),
    "stop": Misunderstanding(
        "stop",
        wrong_meaning="to stop forever and stay still",
        right_meaning="to pause at the next station",
        trigger_word="stop",
        repair_phrase="to stop meant a short pause, not the end of the ride",
    ),
}


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} and {b}, side by side, with a hop and a glide"


def start_scene(world: World, conductor: Entity, human: Entity, mis: Misunderstanding) -> None:
    conductor.memes["calm"] += 1
    human.memes["curious"] += 1
    world.say(
        f"In {world.setting.place}, {conductor.id} the conductor stood neat and bright, "
        f"while {human.id} the human came walking in light."
    )
    world.say(
        f"{world.setting.detail} {rhyme_pair('The day felt sweet', 'the breeze felt neat')}."
    )
    world.say(
        f"{human.id} heard the word \"{mis.trigger_word}\" and smiled with a guess, "
        f"but {human.id} guessed {mis.wrong_meaning}, and that made a mess."
    )


def build_tension(world: World, conductor: Entity, human: Entity, mis: Misunderstanding) -> None:
    human.memes["confusion"] += 1
    conductor.memes["notice"] += 1
    world.para()
    world.say(
        f'"Oh!" said {human.id}. "If it is a {mis.wrong_meaning}, then this is a jest!"'
    )
    world.say(
        f"But {conductor.id} shook {conductor.pronoun('possessive')} head with a kind little sigh, "
        f"for the human had missed the true reason why."
    )
    world.say(
        f"{conductor.id} lifted a hand and spoke nice and slow: "
        f"\"{mis.repair_phrase}.\""
    )


def resolve(world: World, conductor: Entity, human: Entity, mis: Misunderstanding) -> None:
    conductor.memes["relief"] += 1
    human.memes["relief"] += 1
    human.memes["joy"] += 1
    human.memes["confusion"] = 0.0
    world.para()
    world.say(
        f"{human.id} blinked, then grinned, for now {human.id} knew what to know: "
        f"{mis.right_meaning} in a steady row."
    )
    world.say(
        f'"Aha!" said {human.id}. "I see the plan. I was thinking one thing, '
        f"but you meant the train, dear conductor and human-friend fan."
    )
    world.say(
        f"Together they laughed, then stepped aboard, and the wheels went round with a merry sound."
    )
    world.say(
        f"The train rolled on through the evening glow, and the mix-up melted like melting snow."
    )


def tell(setting: Setting, mis: Misunderstanding, conductor_name: str, conductor_type: str,
         human_name: str, human_type: str) -> World:
    world = World(setting)
    conductor = world.add(Entity(id=conductor_name, kind="character", type=conductor_type,
                                 role="conductor", label="conductor"))
    human = world.add(Entity(id=human_name, kind="character", type=human_type,
                             role="human", label="human"))
    world.facts["setting"] = setting
    world.facts["misunderstanding"] = mis
    world.facts["conductor"] = conductor
    world.facts["human"] = human

    start_scene(world, conductor, human, mis)
    build_tension(world, conductor, human, mis)
    resolve(world, conductor, human, mis)

    conductor.memes["trust"] += 1
    human.memes["trust"] += 1
    world.facts["resolved"] = True
    return world


def generate_story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mis: Misunderstanding = f["misunderstanding"]
    conductor: Entity = f["conductor"]
    human: Entity = f["human"]
    setting: Setting = f["setting"]
    return [
        f'Write a rhyming story for a young child about a conductor and a human in {setting.place} who misunderstand the word "{mis.trigger_word}".',
        f"Tell a gentle story where {human.id} thinks {mis.trigger_word} means {mis.wrong_meaning}, but {conductor.id} explains that it really means {mis.right_meaning}.",
        f'Write a short rhyming story that includes the words "conductor" and "human" and ends with a clear, happy explanation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mis: Misunderstanding = f["misunderstanding"]
    conductor: Entity = f["conductor"]
    human: Entity = f["human"]
    return [
        QAItem(
            question="Who are the story about?",
            answer=f"The story is about {conductor.id} the conductor and {human.id} the human. They meet in a little train-world where a small mix-up needs a kind fix."
        ),
        QAItem(
            question=f"What did {human.id} misunderstand?",
            answer=f"{human.id} misunderstood the word \"{mis.trigger_word}\" and thought it meant {mis.wrong_meaning}. {conductor.id} explained that it really meant {mis.right_meaning}."
        ),
        QAItem(
            question="How was the misunderstanding fixed?",
            answer=f"{conductor.id} spoke calmly and said {mis.repair_phrase}. That clear explanation helped {human.id} stop guessing and feel glad again."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a conductor do?",
            answer="A conductor helps guide the train and keeps the ride organized. The conductor can also explain signals so riders know what is happening."
        ),
        QAItem(
            question="What is a human?",
            answer="A human is a person. In stories, a human can be a child or grown-up who talks, listens, and learns."
        ),
        QAItem(
            question="Why can misunderstandings happen?",
            answer="Misunderstandings happen when someone hears a word and thinks it means the wrong thing. They go away when people explain clearly and kindly."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, mis: Misunderstanding) -> str:
    return f"(No story: the setup needs a clear misunderstanding in {setting.place}, and {mis.trigger_word} must be something a human could misread.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about a conductor and a human with a misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MISUNDERSTANDINGS]


ASP_RULES = r"""
setting_ok(S) :- setting(S).
mis_ok(M) :- misunderstanding(M).
valid(S, M) :- setting_ok(S), mis_ok(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH between Python and ASP valid combos.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    else:
        print(f"OK: valid-combo parity for {len(py)} combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: smoke test generated a story.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.misunderstanding is None or c[1] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mis_id = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        misunderstanding=mis_id,
        conductor_name=rng.choice(["June", "Milo", "Pia", "Theo"]),
        conductor_type="woman",
        human_name=rng.choice(["Ada", "Bea", "Nico", "Oli"]),
        human_type="girl",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MISUNDERSTANDINGS[params.misunderstanding],
                 params.conductor_name, params.conductor_type,
                 params.human_name, params.human_type)
    return StorySample(
        params=params,
        story=generate_story_text(world),
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


CURATED = [
    StoryParams("platform", "whistle", "June", "woman", "Ada", "girl"),
    StoryParams("station", "ticket", "Milo", "woman", "Nico", "boy"),
    StoryParams("car", "stop", "Pia", "woman", "Oli", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for s, m in asp_valid_combos():
            print(f"  {s:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

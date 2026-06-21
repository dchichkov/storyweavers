#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/enunciate_conditioning_buss_boat_ramp_reconciliation_space.py
============================================================================================

A standalone story world for a small Space Adventure-style tale set at a boat
ramp.

Premise:
- Two kids are preparing a tiny space launch at the boat ramp.
- One kid cannot clearly enunciate the launch words because the other keeps
  bossing the walkie-talkie conditioning drill.
- A small buss between the friends causes hurt feelings.
- A grown-up helps them reconcile, and they finish with a safer, kinder launch
  practice.

This world keeps the prose child-facing, state-driven, and concrete. It models
meters and memes, uses a Python reasonableness gate plus inline ASP twin, and
supports the required CLI flags.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/enunciate_conditioning_buss_boat_ramp_reconciliation_space.py
    python storyworlds/worlds/gpt-5.4-mini/enunciate_conditioning_buss_boat_ramp_reconciliation_space.py --qa
    python storyworlds/worlds/gpt-5.4-mini/enunciate_conditioning_buss_boat_ramp_reconciliation_space.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    sky: str
    water: str
    launch_spot: str

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
class Tool:
    id: str
    label: str
    use: str
    safe: bool = False
    loud: bool = False
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
class StoryWorld:
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

    def copy(self) -> "StoryWorld":
        clone = StoryWorld(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
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
    speaker: str
    listener: str
    parent: str
    tool: str
    delay: int = 0
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
    "boat_ramp": Setting(
        "boat_ramp",
        "the boat ramp",
        "a bright space sky",
        "the rippling water",
        "the top of the ramp",
    )
}

TOOLS = {
    "walkie": Tool("walkie", "walkie-talkie", "announce launches", safe=True, tags={"space", "talk"}),
    "helmet": Tool("helmet", "space helmet", "keep words clear", safe=True, tags={"space"}),
    "horn": Tool("horn", "boat horn", "make a loud launch sound", loud=True, tags={"space", "boat"}),
    "flashlight": Tool("flashlight", "flashlight", "light the path", safe=True, tags={"space"}),
}

NAMES = ["Mina", "Jasper", "Tia", "Noah", "Luna", "Eli", "Piper", "Milo"]
TYPES = {"girl": ["Mina", "Tia", "Luna", "Piper"], "boy": ["Jasper", "Noah", "Eli", "Milo"]}


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(TYPES[gender])


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for tool in TOOLS:
            # Only safe space tools make a sensible reconciliation story here.
            if TOOLS[tool].safe:
                out.append((sid, tool, "reconciliation"))
    return out


def explain_rejection(tool: Tool) -> str:
    return f"(No story: {tool.label} is not a good fit for a calm reconciliation scene at the boat ramp.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world at a boat ramp.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
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
    if args.tool and not TOOLS[args.tool].safe:
        raise StoryError(explain_rejection(TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, _ = rng.choice(sorted(combos))
    speaker_gender = rng.choice(["girl", "boy"])
    listener_gender = "boy" if speaker_gender == "girl" else "girl"
    speaker = _pick_name(rng, speaker_gender)
    listener = _pick_name(rng, listener_gender)
    while listener == speaker:
        listener = _pick_name(rng, listener_gender)
    parent = rng.choice(["mother", "father"])
    return StoryParams(setting=setting, speaker=speaker, listener=listener, parent=parent, tool=tool)


def _r_feel(world: StoryWorld) -> None:
    for ent in list(world.entities.values()):
        if ent.role in {"speaker", "listener"}:
            if ent.memes["hurt"] >= THRESHOLD:
                ent.memes["quiet"] += 1


def story(world: StoryWorld, speaker: Entity, listener: Entity, parent: Entity, tool: Tool) -> None:
    speaker.memes["curious"] += 1
    listener.memes["orderly"] += 1
    world.say(
        f"At the boat ramp, {speaker.id} and {listener.id} built a tiny space game beside "
        f"{world.setting.water}. {world.setting.sky.capitalize()} looked huge over the ramp, "
        f"and the top of the ramp felt like a launch pad."
    )
    world.say(
        f'{speaker.id} held up a {tool.label} and said, "I can {tool.use}." '
        f'{listener.id} frowned because the practice words were getting hard to {speaker.pronoun("subject")} enunciate.'
    )
    world.para()
    listener.memes["annoyed"] += 1
    speaker.memes["frustrated"] += 1
    world.say(
        f"{listener.id} kept pushing the conditioning drill too hard, and that made {speaker.id} feel small. "
        f"Then, in a quick buss of impatience, {listener.id} brushed past {speaker.id}'s shoulder."
    )
    speaker.memes["hurt"] += 1
    listener.memes["guilt"] += 1
    world.say(
        f"{speaker.id} went quiet and looked at the water. The launch plan had turned into a sad, shaky moment."
    )
    world.para()
    parent.memes["calm"] += 1
    world.say(
        f"{parent.label_word.capitalize()} walked over, knelt beside them, and asked both kids to slow down and enunciate one word at a time."
    )
    world.say(
        f'"Let\'s do the conditioning together," {parent.id} said. "No pushing. No bussing. We can fix this."'
    )
    speaker.memes["hope"] += 1
    listener.memes["regret"] += 1
    speaker.memes["forgiveness"] += 1
    listener.memes["forgiveness"] += 1
    world.say(
        f"{listener.id} apologized, and {speaker.id} nodded. They tried again: clear words, quiet breaths, and steady hands."
    )
    world.para()
    world.say(
        f"This time, {speaker.id} could enunciate the launch call, and {listener.id} counted with care. "
        f"They raised the {tool.label}, laughed softly, and watched the pretend rocket skim across the shining boat ramp."
    )
    world.say(
        f"By the end, the friends were close again, the air felt lighter, and the water below the ramp glittered like a safe little galaxy."
    )


def generate_world(params: StoryParams) -> StoryWorld:
    world = StoryWorld(SETTINGS[params.setting])
    speaker = world.add(Entity(id=params.speaker, kind="character", type="girl" if params.speaker in TYPES["girl"] else "boy", role="speaker"))
    listener = world.add(Entity(id=params.listener, kind="character", type="girl" if params.listener in TYPES["girl"] else "boy", role="listener"))
    parent = world.add(Entity(id=params.parent.capitalize(), kind="character", type=params.parent, role="parent", label=f"the {params.parent}"))
    tool = TOOLS[params.tool]
    world.facts.update(params=params, speaker=speaker, listener=listener, parent=parent, tool=tool, setting=world.setting)
    story(world, speaker, listener, parent, tool)
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    return [
        f'Write a Space Adventure story set at {f["setting"].place} that includes the words "enunciate", "conditioning", and "buss".',
        f"Tell a child-friendly reconciliation story where {f['speaker'].id} and {f['listener'].id} get upset during launch practice, then make up with help from {f['parent'].label_word}.",
        f"Write a story where a tiny rocket practice at the boat ramp ends in reconciliation, clear speech, and a gentle finish.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    speaker, listener, parent, tool = f["speaker"], f["listener"], f["parent"], f["tool"]
    return [
        QAItem(
            question="What happened at the boat ramp?",
            answer=f"{speaker.id} and {listener.id} were pretending the boat ramp was a launch pad for a tiny space adventure. The plan started to go wrong when the practice became too pushy and {listener.id} bussed {speaker.id} in impatience."
        ),
        QAItem(
            question="How did the grown-up help?",
            answer=f"{parent.label_word.capitalize()} told them to slow down, speak clearly, and stop pushing each other. That calm help gave them a chance to reconcile and try the launch again the kind way."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"They spoke more clearly, apologized, and became friends again. The {tool.label} and the boat ramp turned back into part of a happy space game instead of a hurt feeling."
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a boat ramp?",
            answer="A boat ramp is a sloped place where boats can be pushed into or pulled out of the water."
        ),
        QAItem(
            question="What does enunciate mean?",
            answer="To enunciate means to say words clearly so other people can understand them."
        ),
        QAItem(
            question="What is conditioning?",
            answer="Conditioning means practicing something again and again so your body or skills become stronger and steadier."
        ),
        QAItem(
            question="What is a buss?",
            answer="A buss is a quick kiss. In a story, it can also show a sudden little moment that changes how someone feels."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: role={e.role} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_tool(T) :- tool(T), safe(T).
valid(S, T) :- setting(S), tool(T), safe_tool(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.safe:
            lines.append(asp.fact("safe", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, tool=None), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams("boat_ramp", "Mina", "Jasper", "mother", "walkie"),
    StoryParams("boat_ramp", "Tia", "Noah", "father", "helmet"),
    StoryParams("boat_ramp", "Luna", "Eli", "mother", "flashlight"),
]


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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

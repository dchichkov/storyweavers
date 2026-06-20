#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spank_gerund_misunderstanding_animal_story.py
=============================================================================

A small standalone storyworld for a child-facing animal story about a
misunderstood word: "spank-gerund".  The world is built from typed entities with
meters and memes, a tiny causal model, a reasonableness gate, and an inline ASP
twin for parity checking.

The premise is simple: a young animal hears a confusing phrase, thinks it means
one thing, then a patient grown-up or older animal clarifies the misunderstanding
and shows a safer, kinder action instead.  The story ends with a clear changed
state: the animal learns the right meaning and the group does the gentle action
together.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/spank_gerund_misunderstanding_animal_story.py
    python storyworlds/worlds/gpt-5.4-mini/spank_gerund_misunderstanding_animal_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/spank_gerund_misunderstanding_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/spank_gerund_misunderstanding_animal_story.py --verify
    python storyworlds/worlds/gpt-5.4-mini/spank_gerund_misunderstanding_animal_story.py --json
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not isinstance(self.meters, dict):
            self.meters = {}
        if not isinstance(self.memes, dict):
            self.memes = {}

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
    quiet: str
    animal_group: str

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
class Animal:
    id: str
    species: str
    kind_word: str
    role_word: str
    harmless_move: str
    mistaken_move: str
    misheard_line: str
    understanding_line: str

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
class Misunderstanding:
    id: str
    phrase: str
    real_meaning: str
    mistaken_meaning: str
    clarification: str

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
class GentleAction:
    id: str
    phrase: str
    result_line: str
    healing_line: str

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


def _rule_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    speaker = world.get("speaker")
    learner = world.get("learner")
    if learner.memes.get("confusion", 0.0) >= THRESHOLD and ("confusion", learner.id) not in world.fired:
        world.fired.add(("confusion", learner.id))
        learner.memes["worry"] = learner.memes.get("worry", 0.0) + 1
        speaker.memes["patience"] = speaker.memes.get("patience", 0.0) + 1
        out.append("__confused__")
    return out


def _rule_relief(world: World) -> list[str]:
    out: list[str] = []
    learner = world.get("learner")
    if learner.memes.get("understanding", 0.0) >= THRESHOLD and ("relief", learner.id) not in world.fired:
        world.fired.add(("relief", learner.id))
        learner.memes["joy"] = learner.memes.get("joy", 0.0) + 1
        out.append("__relief__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_misunderstanding, _rule_relief):
            got = rule(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(params: "StoryParams") -> bool:
    return params.setting in SETTINGS and params.animal in ANIMALS and params.misunderstanding in MISUNDERSTANDINGS and params.action in ACTIONS


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, animal in ANIMALS.items():
            for mid, mis in MISUNDERSTANDINGS.items():
                for actid, act in ACTIONS.items():
                    if act.phrase == mis.real_meaning:
                        combos.append((sid, aid, mid, actid))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for actid, act in ACTIONS.items():
        lines.append(asp.fact("action", actid))
        lines.append(asp.fact("action_phrase", actid, act.phrase))
    for mid, mis in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("real_meaning", mid, mis.real_meaning))
        lines.append(asp.fact("mistaken_meaning", mid, mis.mistaken_meaning))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S, A, M, X) :- setting(S), animal(A), misunderstanding(M), action(X),
                          action_phrase(X, P), real_meaning(M, P).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


@dataclass
@dataclass
class StoryParams:
    setting: str
    animal: str
    misunderstanding: str
    action: str
    learner_name: str
    learner_gender: str
    speaker_name: str
    speaker_gender: str
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


SETTINGS = {
    "barn": Setting("barn", "a warm barn", "quiet hay and soft straw", "barn animals"),
    "pond": Setting("pond", "a sunny pond", "reeds that swayed in the breeze", "pond animals"),
    "meadow": Setting("meadow", "a green meadow", "butterflies and clover", "field animals"),
}

ANIMALS = {
    "duck": Animal("duck", "duck", "duck", "little duck", "waddle", "spank", "spank-gerund", "means to move in a silly way"),
    "rabbit": Animal("rabbit", "rabbit", "rabbit", "small rabbit", "hop", "spank", "spank-gerund", "means to make a playful move"),
    "kitten": Animal("kitten", "kitten", "kitten", "small kitten", "pounce", "spank", "spank-gerund", "means to do the action gently"),
}

MISUNDERSTANDINGS = {
    "phrase": Misunderstanding("phrase", "spank-gerund", "to do a gentle, silly action", "to hit", "The phrase sounded rough, but it was only a confusing word game."),
}

ACTIONS = {
    "waddle": GentleAction("waddle", "waddle together", "and the animals waddled together in a soft line", "Their feet moved lightly, and everyone laughed."),
    "hop": GentleAction("hop", "hop together", "and the animals hopped together under the sky", "Their hops were tiny and kind."),
    "pounce": GentleAction("pounce", "pounce together", "and the animals pounced together on a pile of leaves", "The leaves puffed up like a fluffy cloud."),
}

LEARNERS = [("Milo", "boy"), ("Luna", "girl"), ("Pip", "boy"), ("Ruby", "girl")]
SPEAKERS = [("Mina", "girl"), ("Otis", "boy"), ("Nora", "girl"), ("Bram", "boy")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story about a misunderstanding and a gentle fix.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--learner")
    ap.add_argument("--learner-gender", choices=["girl", "boy"])
    ap.add_argument("--speaker")
    ap.add_argument("--speaker-gender", choices=["girl", "boy"])
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
    if args.setting and args.animal and args.misunderstanding and args.action:
        if (args.setting, args.animal, args.misunderstanding, args.action) not in combos:
            raise StoryError("Those choices do not make a sensible animal misunderstanding story.")
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.animal is None or c[1] == args.animal) and (args.misunderstanding is None or c[2] == args.misunderstanding) and (args.action is None or c[3] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, animal, misunderstanding, action = rng.choice(sorted(combos))
    lname, lgen = (args.learner, args.learner_gender) if args.learner and args.learner_gender else rng.choice(LEARNERS)
    sname, sgen = (args.speaker, args.speaker_gender) if args.speaker and args.speaker_gender else rng.choice(SPEAKERS)
    return StoryParams(setting, animal, misunderstanding, action, lname, lgen, sname, sgen)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    learner = world.add(Entity("learner", "character", params.learner_gender, label=params.learner_name, role="learner"))
    speaker = world.add(Entity("speaker", "character", params.speaker_gender, label=params.speaker_name, role="speaker"))
    animal = ANIMALS[params.animal]
    mis = MISUNDERSTANDINGS[params.misunderstanding]
    act = ACTIONS[params.action]

    learner.memes["curiosity"] = 1
    learner.memes["confusion"] = 1
    speaker.memes["kindness"] = 1

    world.say(f"In {world.setting.place}, {learner.id} met {speaker.id} and a little {animal.kind_word}.")
    world.say(f'They kept hearing the strange words "{mis.phrase}" and wondered what they meant.')
    world.para()
    world.say(f'{learner.id} thought "{mis.phrase}" meant {mis.mistaken_meaning}, and that made {learner.pronoun("object")} pause.')
    propagate(world, narrate=False)
    world.say(f"{speaker.id} noticed the puzzled look and smiled gently. {speaker.id} explained that {mis.phrase} {mis.clarification.lower()}")
    learner.memes["understanding"] = 1
    world.para()
    action_line = act.result_line
    world.say(f"Then they chose to {act.phrase} instead, and the misunderstanding turned into a game.")
    world.say(f"{learner.id} laughed, because now {mis.phrase} made sense, and the animals could play without any hurt feelings.")
    world.say(f"By the end, {learner.id} and {speaker.id} were {action_line}, and the meadow-like world felt calm again.")
    world.facts.update(
        learner=learner, speaker=speaker, animal=animal, mis=mis, act=act,
        outcome="resolved", understood=True, setting=world.setting.id,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an animal story that includes the word \"{f['mis'].phrase}\" and shows a misunderstanding turning into a gentle game.",
        f"Tell a child-friendly story about {f['learner'].id}, {f['speaker'].id}, and a small animal where a confusing phrase is explained kindly.",
        f"Write a story in an animal story style where a strange word sounds upsetting at first, but ends with a happy correction.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    learner = f["learner"]
    speaker = f["speaker"]
    mis = f["mis"]
    act = f["act"]
    return [
        QAItem(
            question="What misunderstanding caused the problem?",
            answer=f"{learner.id} thought the phrase \"{mis.phrase}\" meant {mis.mistaken_meaning}. {speaker.id} then explained that it really meant {mis.real_meaning}, so the worry went away."
        ),
        QAItem(
            question="How did the story turn out?",
            answer=f"It ended happily. {learner.id} and {speaker.id} chose to {act.phrase} together, and the animals kept playing in a calm, kind way."
        ),
        QAItem(
            question="What changed after the explanation?",
            answer=f"{learner.id} went from confusion to understanding. That change turned the mood from worried to joyful, because the new meaning made the whole game feel safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem("What does a duck do?", "A duck can waddle on land and swim in water. Ducks often move in a funny, bouncy way."),
        QAItem("What does it mean to misunderstand something?", "It means you think something has one meaning when it really means something else. A clear explanation can fix a misunderstanding."),
        QAItem("Why is a gentle explanation helpful?", "A gentle explanation helps because it makes someone feel safe while they learn the right meaning. Kind words can change confusion into calm."),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("barn", "duck", "phrase", "waddle", "Milo", "boy", "Mina", "girl"),
    StoryParams("pond", "rabbit", "phrase", "hop", "Luna", "girl", "Otis", "boy"),
    StoryParams("meadow", "kitten", "phrase", "pounce", "Pip", "boy", "Nora", "girl"),
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    rc = 0
    if cset != pset:
        rc = 1
        print("MISMATCH in valid combos.")
        print("only in clingo:", sorted(cset - pset))
        print("only in python:", sorted(pset - cset))
    else:
        print(f"OK: ASP parity matches valid_combos() ({len(pset)} combos).")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: generation produced empty story.")
    else:
        print("OK: generate() smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
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

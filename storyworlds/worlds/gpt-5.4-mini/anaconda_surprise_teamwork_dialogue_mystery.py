#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/anaconda_surprise_teamwork_dialogue_mystery.py
==============================================================================

A standalone story world for a tiny mystery about an anaconda, a surprise, and
a team that solves a puzzle by talking it through.

The domain is built from a seed prompt:
- word: anaconda
- features: Surprise, Teamwork, Dialogue
- style: Mystery

The world model is small but stateful:
- typed entities with physical meters and emotional memes
- a mystery setup, a clue trail, a false lead, a reveal, and a team fix
- reasonableness gates so only plausible mysteries are generated
- inline ASP twin for parity checks
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    cover: str
    shadow: str
    noise: str

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
class Clue:
    id: str
    label: str
    phrase: str
    where: str
    importance: int = 1
    risky: bool = False

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
class Suspect:
    id: str
    label: str
    phrase: str
    alibi: str
    likely: bool = False
    risky: bool = False

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
    phrase: str
    helps: str
    plural: bool = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

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


def _r_feel_spooked(world: World) -> list[str]:
    out = []
    if world.facts.get("surprise_seen") and not world.facts.get("team_plan"):
        for eid in ("child", "friend", "grownup"):
            if eid in world.entities:
                world.get(eid).memes["worry"] += 1
        out.append("__spooked__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    if world.facts.get("team_plan") and not world.fired.intersection({("teamwork",)}):
        world.fired.add(("teamwork",))
        for eid in ("child", "friend"):
            if eid in world.entities:
                world.get(eid).memes["courage"] += 1
                world.get(eid).memes["trust"] += 1
        out.append("__team__")
    return out


CAUSAL_RULES = [Rule("spooked", "social", _r_feel_spooked), Rule("teamwork", "social", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def is_plausible(setting: Setting, clue: Clue, suspect: Suspect) -> bool:
    return clue.risky and suspect.risky and clue.importance >= 1


def best_tool() -> Tool:
    return max(TOOLS.values(), key=lambda t: len(t.helps))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for sid2, suspect in SUSPECTS.items():
                if is_plausible(SETTINGS[sid], clue, suspect):
                    combos.append((sid, cid, sid2))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    tool: str
    child_name: str
    friend_name: str
    grownup_name: str
    child_gender: str
    friend_gender: str
    grownup_gender: str
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
    "zoo_path": Setting("zoo_path", "the path by the reptile house", "a row of rocks", "the shade of a hedge", "soft footsteps"),
    "greenhouse": Setting("greenhouse", "the greenhouse walk", "glass panels", "a wet fern corner", "a glassy hum"),
    "night_trail": Setting("night_trail", "the moonlit trail", "bush shadows", "a dark bend", "rustling leaves"),
}

CLUES = {
    "slither_marks": Clue("slither_marks", "slither marks", "thin marks in the dirt", "near the stones", importance=2, risky=True),
    "shed_skin": Clue("shed_skin", "a shed skin", "a pale shed skin", "under the bench", importance=2, risky=True),
    "broken_branch": Clue("broken_branch", "a broken branch", "a snapped branch", "beside the path", importance=1, risky=True),
    "tile_reflection": Clue("tile_reflection", "a reflection", "a strange reflection", "in a puddle", importance=1, risky=True),
}

SUSPECTS = {
    "anaconda": Suspect("anaconda", "an anaconda", "the anaconda", "it stayed hidden in the cover", likely=True, risky=True),
    "rope": Suspect("rope", "a coil of rope", "the rope", "it was only left by a keeper", risky=False),
    "hose": Suspect("hose", "a garden hose", "the hose", "it belonged by the plants", risky=False),
}

TOOLS = {
    "flashlight": Tool("flashlight", "a flashlight", "a flashlight", "to look under the shade"),
    "walkie": Tool("walkie", "walkie-talkies", "walkie-talkies", "to share clues", plural=True),
    "map": Tool("map", "a map", "a folded map", "to compare the trail"),
}

GIRL_NAMES = ["Mina", "Lina", "Tess", "Nora", "Ava", "Maya", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Finn", "Leo", "Owen", "Milo", "Kai"]
ADULT_NAMES = ["Rosa", "Marta", "June", "Evan", "Noah", "Iris"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery story world about an anaconda and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.risky:
            lines.append(asp.fact("risky", cid))
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        if suspect.risky:
            lines.append(asp.fact("risky_suspect", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,U) :- setting(S), clue(C), suspect(U), risky(C), risky_suspect(U).
"""


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, suspect = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    child_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if child_gender == "girl" else "girl"
    grownup_gender = rng.choice(["woman", "man"])
    child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend_name = rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    grownup_name = rng.choice(ADULT_NAMES)
    return StoryParams(setting, clue, suspect, tool, child_name, friend_name, grownup_name, child_gender, friend_gender, grownup_gender)


def tell(params: StoryParams) -> World:
    w = World(SETTINGS[params.setting])
    child = w.add(Entity("child", "character", params.child_gender, label=params.child_name, role="child"))
    friend = w.add(Entity("friend", "character", params.friend_gender, label=params.friend_name, role="friend"))
    grownup = w.add(Entity("grownup", "character", params.grownup_gender, label=params.grownup_name, role="grownup"))
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]
    tool = TOOLS[params.tool]
    w.facts.update(child=child, friend=friend, grownup=grownup, clue=clue, suspect=suspect, tool=tool)

    child.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    w.say(f"{child.label} and {friend.label} were exploring {w.setting.place}.")
    w.say(f"Then they found {clue.phrase}, and both of them stopped at once.")
    w.say(f'"Look," {child.label} whispered, "that could be a clue."')
    w.para()
    w.say(f'"Maybe," {friend.label} said, "but maybe it is only a sign that something was here."')
    child.memes["surprise"] += 1
    friend.memes["surprise"] += 1
    w.facts["surprise_seen"] = True
    w.say(f"That was the surprise: the trail seemed to point toward {suspect.phrase}.")
    w.say(f"They used {tool.phrase} {tool.helps}, talking quietly as they went.")
    w.facts["team_plan"] = True
    propagate(w, narrate=False)
    w.para()
    if suspect.likely:
        w.say(f'"Should we call {grownup.label}?" {child.label} asked.')
        w.say(f'"Yes," {friend.label} said. "Let\'s work together and tell {grownup.label} what we found."')
        w.say(f'{grownup.label} came over, shone a light where they pointed, and smiled. It was an anaconda, curled safe behind the cover, not chasing anyone at all.')
        w.say(f'The mystery was solved because the team talked, watched, and listened before they jumped to the wrong idea.')
        child.memes["relief"] += 1
        friend.memes["relief"] += 1
    else:
        w.say(f'"That does not fit," {friend.label} said after another look.')
        w.say(f'{child.label} nodded, and together they used the clues to rule out the false lead.')
        w.say(f'At last {grownup.label} helped them open the path, and the real answer turned out to be simple.')
    w.facts["outcome"] = "solved"
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue = f["clue"].label
    suspect = f["suspect"].label
    return [
        f'Write a mystery story for a small child that includes the word "anaconda" and the clue {clue}.',
        f"Tell a teamwork mystery where two children share a surprise, talk in short sentences, and discover that {suspect} is part of the puzzle.",
        f'Write a calm detective story with dialogue, teamwork, and a surprise reveal near {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, grownup, clue, suspect = f["child"], f["friend"], f["grownup"], f["clue"], f["suspect"]
    return [
        QAItem(
            question="Who worked together in the story?",
            answer=f"{child.label} and {friend.label} worked together like a team. They talked over the clue and then asked {grownup.label} for help."
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was that the trail seemed to point toward {suspect.phrase}. After they looked carefully, they learned the answer was safer and clearer than they first thought."
        ),
        QAItem(
            question="How did the team solve the mystery?",
            answer=f"They used {f['tool'].phrase}, shared what they saw, and followed the clue {clue.phrase}. Working together helped them understand the scene instead of guessing too fast."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an anaconda?", "An anaconda is a very large snake. It moves by slithering and can hide in water or under cover."),
        QAItem("What does teamwork mean?", "Teamwork means people help each other and solve a problem together."),
        QAItem("What is a mystery?", "A mystery is a puzzle with clues that you have to think about before you know the answer."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:7} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("zoo_path", "slither_marks", "anaconda", "flashlight", "Mina", "Theo", "Rosa", "girl", "boy", "woman"),
    StoryParams("greenhouse", "shed_skin", "anaconda", "map", "Nora", "Kai", "Evan", "girl", "boy", "man"),
    StoryParams("night_trail", "broken_branch", "anaconda", "walkie", "Leo", "Ava", "June", "boy", "girl", "woman"),
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
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def resolve_story(params: StoryParams, rng: random.Random) -> StoryParams:
    return params


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for item in asp_valid_combos():
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            combos = [c for c in valid_combos()
                      if (args.setting is None or c[0] == args.setting)
                      and (args.clue is None or c[1] == args.clue)
                      and (args.suspect is None or c[2] == args.suspect)]
            if not combos:
                raise StoryError("(No valid combination matches the given options.)")
            setting, clue, suspect = rng.choice(sorted(combos))
            params = StoryParams(
                setting, clue, suspect, args.tool or rng.choice(sorted(TOOLS)),
                rng.choice(GIRL_NAMES), rng.choice(BOY_NAMES), rng.choice(ADULT_NAMES),
                "girl", "boy", "woman", seed=seed,
            )
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

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

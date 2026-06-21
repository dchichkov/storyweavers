#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/boom_fettuccini_git_curiosity_detective_story.py
===============================================================================

A tiny storyworld built from the seed words:

- boom
- fettuccini
- git

Style: detective story
Feature: curiosity

Premise:
A curious child detective follows small clues through a kitchen-and-studio mystery.
A loud boom from the oven, a pot of fettuccini, and a git commit note become the
three visible clues. The child notices cause and effect in the world, asks
careful questions, finds the missing piece, and ends with a complete little case
solved.

The world is modeled with typed entities, physical meters, and emotional memes.
A forward rule engine turns state changes into consequences and prose. The same
world model also drives prompts, story-grounded Q&A, and child-level world
knowledge Q&A.

This script is standalone and uses only the Python stdlib plus the shared
storyworld result containers. ASP support is inline and imported lazily.
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
SENSE_MIN = 2


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Clue:
    id: str
    label: str
    fact: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Action:
    id: str
    sense: int
    power: int
    clue_text: str
    fail_text: str
    resolution_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_alert(world: World) -> list[str]:
    out: list[str] = []
    oven = world.entities.get("oven")
    if oven and oven.meters["heat"] >= THRESHOLD:
        sig = ("alert", "oven")
        if sig not in world.fired:
            world.fired.add(sig)
            for e in list(world.entities.values()):
                if e.role == "detective":
                    e.memes["curiosity"] += 1
                    e.memes["alertness"] += 1
            out.append("__alert__")
    return out


def _r_smell(world: World) -> list[str]:
    out: list[str] = []
    pan = world.entities.get("pan")
    if pan and pan.meters["boiling"] >= THRESHOLD:
        sig = ("smell", "pan")
        if sig not in world.fired:
            world.fired.add(sig)
            kitchen = world.entities.get("kitchen")
            if kitchen:
                kitchen.meters["clue_density"] += 1
            out.append("A warm, buttery smell drifted through the room.")
    return out


def _r_git(world: World) -> list[str]:
    out: list[str] = []
    note = world.entities.get("gitnote")
    if note and note.meters["missing"] >= THRESHOLD:
        sig = ("git", "missing")
        if sig not in world.fired:
            world.fired.add(sig)
            for e in list(world.entities.values()):
                if e.role == "detective":
                    e.memes["curiosity"] += 1
            out.append("The little git note meant someone had changed the plan.")
    return out


CAUSAL_RULES = [
    Rule("alert", "social", _r_alert),
    Rule("smell", "physical", _r_smell),
    Rule("git", "clue", _r_git),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def cook_story(world: World, kid: Entity, chef: Entity, setting: Setting, clue1: Clue, clue2: Clue, clue3: Clue, action: Action, outcome: str) -> None:
    kid.memes["curiosity"] += 1
    kid.memes["joy"] += 1
    world.say(
        f"On a quiet evening at {setting.place}, {kid.id} noticed {setting.detail}. "
        f"{kid.id} was a curious little detective who loved asking why."
    )
    world.say(
        f"Near the stove sat a pan of fettuccini, a scribbled git note, and a funny little silence that felt wrong."
    )
    world.say(
        f'"{clue1.label}," {kid.id} whispered. "{clue2.label}... and a git clue."'
    )

    world.para()
    world.say(
        f"Then the oven gave a boom, loud enough to shake the spoon rack."
    )
    oven = world.get("oven")
    oven.meters["heat"] += 1
    pan = world.get("pan")
    pan.meters["boiling"] += 1
    note = world.get("gitnote")
    note.meters["missing"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{kid.id} followed the clues instead of the noise. {kid.pronoun().capitalize()} "
        f"looked at the oven knob, the pan, and the git note, one by one."
    )
    if outcome == "solved":
        world.say(
            f"{kid.id} found the real problem: the timer had been set wrong, so the fettuccini boiled too hard and the pan rattled like a drum."
        )
        world.say(
            f"{chef.label_word.capitalize()} turned off the burner, lifted the lid, and nodded. "
            f'"Good catch," {chef.id} said. "You were curious in the right way."'
        )
        world.say(
            f"The kitchen calmed down at once, and the fettuccini sat steaming safely instead of making any more boom."
        )
    else:
        world.say(
            f"{kid.id} found the problem in time to warn {chef.id}, but the fix was a bit late, so the pan spilled and made a mess."
        )
        world.say(
            f"Still, the curious detective had solved the case: the git note showed the timer change, and everyone knew what happened."
        )
    world.facts.update(
        kid=kid,
        chef=chef,
        setting=setting,
        clue1=clue1,
        clue2=clue2,
        clue3=clue3,
        action=action,
        outcome=outcome,
    )


SETTING_REGISTRY = {
    "kitchen": Setting(id="kitchen", place="the kitchen", detail="the shiny timer blinking on the counter"),
    "studio": Setting(id="studio", place="the little cooking studio", detail="a chalkboard covered in recipe notes"),
}

CLUE_REGISTRY = {
    "boom": Clue(id="boom", label="boom", fact="an oven boom", tags={"boom", "noise"}),
    "fettuccini": Clue(id="fettuccini", label="fettuccini", fact="a pot of fettuccini", tags={"fettuccini", "food"}),
    "git": Clue(id="git", label="git", fact="a git note", tags={"git", "note"}),
}

ACTION_REGISTRY = {
    "inspect": Action(
        id="inspect",
        sense=3,
        power=3,
        clue_text="looked closely at the clues until the pattern made sense",
        fail_text="looked, but the clues were too jumbled to help",
        resolution_text="followed the clues until the answer became clear",
        tags={"detective", "curiosity"},
    ),
    "listen": Action(
        id="listen",
        sense=2,
        power=2,
        clue_text="listened carefully for what the room was saying",
        fail_text="listened, but the room stayed confusing",
        resolution_text="listened to the clues and found the answer",
        tags={"detective", "curiosity"},
    ),
    "rush": Action(
        id="rush",
        sense=1,
        power=1,
        clue_text="rushed at the mystery without thinking",
        fail_text="rushed too fast and missed the important clue",
        resolution_text="rushed at the answer and nearly missed it",
        tags={"impulsive"},
    ),
}

KID_NAMES = ["Maya", "Leo", "Nina", "Ben", "Ivy", "Theo", "Zoe", "Sam"]
CHEF_NAMES = ["Aunt Jo", "Mr. Lin", "Ms. Ada", "Chef Rosa"]


@dataclass
class StoryParams:
    setting: str
    clue1: str
    clue2: str
    clue3: str
    action: str
    kid: str
    kid_gender: str
    chef: str
    chef_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTING_REGISTRY:
        for c1 in CLUE_REGISTRY:
            for c2 in CLUE_REGISTRY:
                for c3 in CLUE_REGISTRY:
                    if len({c1, c2, c3}) != 3:
                        continue
                    combos.append((setting, c1, c2, c3))
    return combos


def explain_action(action: str) -> str:
    a = ACTION_REGISTRY[action]
    good = " / ".join(sorted(x.id for x in ACTION_REGISTRY.values() if x.sense >= SENSE_MIN))
    return f"(Refusing action '{action}': it is too weak-minded for a detective story (sense={a.sense} < {SENSE_MIN}). Try: {good}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld with boom, fettuccini, and git.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--clue1", choices=CLUE_REGISTRY)
    ap.add_argument("--clue2", choices=CLUE_REGISTRY)
    ap.add_argument("--clue3", choices=CLUE_REGISTRY)
    ap.add_argument("--action", choices=ACTION_REGISTRY)
    ap.add_argument("--kid")
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
    ap.add_argument("--chef")
    ap.add_argument("--chef-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and ACTION_REGISTRY[args.action].sense < SENSE_MIN:
        raise StoryError(explain_action(args.action))
    combos = [c for c in valid_combos()
              if args.setting is None or c[0] == args.setting]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, c1, c2, c3 = rng.choice(sorted(combos))
    action = args.action or rng.choice(sorted(k for k, v in ACTION_REGISTRY.items() if v.sense >= SENSE_MIN))
    kid_gender = args.kid_gender or rng.choice(["girl", "boy"])
    chef_gender = args.chef_gender or rng.choice(["woman", "man"])
    kid = args.kid or rng.choice(KID_NAMES)
    chef = args.chef or rng.choice(CHEF_NAMES)
    return StoryParams(setting=setting, clue1=c1, clue2=c2, clue3=c3, action=action, kid=kid, kid_gender=kid_gender, chef=chef, chef_gender=chef_gender)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTING_REGISTRY[params.setting]
    clue1 = CLUE_REGISTRY[params.clue1]
    clue2 = CLUE_REGISTRY[params.clue2]
    clue3 = CLUE_REGISTRY[params.clue3]
    action = ACTION_REGISTRY[params.action]

    kid = world.add(Entity(id=params.kid, kind="character", type=params.kid_gender, role="detective"))
    chef = world.add(Entity(id=params.chef, kind="character", type=params.chef_gender, role="chef", label=params.chef))
    world.add(Entity(id="kitchen", type="room", label=setting.place))
    world.add(Entity(id="oven", type="thing", label="oven"))
    world.add(Entity(id="pan", type="thing", label="pan"))
    world.add(Entity(id="gitnote", type="thing", label="git note"))

    outcome = "solved"
    cook_story(world, kid, chef, setting, clue1, clue2, clue3, action, outcome)
    world.facts["setting"] = setting
    return world


def generate(params: StoryParams) -> StorySample:
    if any(x not in CLUE_REGISTRY for x in [params.clue1, params.clue2, params.clue3]):
        raise StoryError("Unknown clue key.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a young child that includes the words "boom", "fettuccini", and "git".',
        f"Tell a curious little detective story where {f['kid'].id} studies a kitchen mystery and finds out why the fettuccini made a boom.",
        f'Write a story in which curiosity helps solve a small mystery with a git clue and a bowl of fettuccini.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, chef, setting = f["kid"], f["chef"], f["setting"]
    return [
        ("Who is the story about?", f"It is about {kid.id}, a curious little detective, and {chef.id}, who helped solve the kitchen mystery."),
        ("What three clues were in the story?", "The story had a boom, a pot of fettuccini, and a git note. Those clues gave the detective a pattern to follow."),
        ("What caused the boom?", "The oven timer had been set wrong, so the pan of fettuccini boiled hard and rattled the kitchen. That was the noisy clue the detective noticed first."),
        ("How did the story end?", "The case was solved and the kitchen calmed down. The detective's curiosity helped everyone understand what had happened."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is curiosity?", "Curiosity is the feeling that makes you want to look, ask, and learn more. It can help you solve problems by noticing important clues."),
        ("What is a detective?", "A detective is someone who looks for clues and tries to solve a mystery. Detectives pay attention to little details."),
        ("What is git?", "Git is a tool people use to keep track of changes in files and projects. It helps them see what was changed and when."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_pair(A,B,C) :- clue(A), clue(B), clue(C), A != B, B != C, A != C.
detective_story(S) :- setting(S), clue_pair(C1,C2,C3).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for cid in CLUE_REGISTRY:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show detective_story/1."))
    return sorted(set(asp.atoms(model, "detective_story")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()):
        print(f"OK: ASP program produced {len(asp_valid_combos())} detected story markers.")
    else:
        rc = 1
        print("MISMATCH: ASP program did not produce expected markers.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, clue1=None, clue2=None, clue3=None, action=None,
            kid=None, kid_gender=None, chef=None, chef_gender=None
        ), random.Random(777)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_sample_args() -> argparse.Namespace:
    return build_parser().parse_args([])


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
    StoryParams(setting="kitchen", clue1="boom", clue2="fettuccini", clue3="git", action="inspect", kid="Maya", kid_gender="girl", chef="Chef Rosa", chef_gender="woman"),
    StoryParams(setting="studio", clue1="git", clue2="boom", clue3="fettuccini", action="listen", kid="Leo", kid_gender="boy", chef="Mr. Lin", chef_gender="man"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show detective_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP is available for the inline story markers.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

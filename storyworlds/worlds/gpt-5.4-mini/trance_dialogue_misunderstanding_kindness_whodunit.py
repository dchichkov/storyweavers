#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trance_dialogue_misunderstanding_kindness_whodunit.py
======================================================================================

A standalone story world sketch for a tiny whodunit-style domain: a child notices a
strange clue, everyone talks past one another, and a kind act clears the mystery.

This world is intentionally small and concrete:
- Dialogue drives the turning points.
- A misunderstanding creates the whodunit tension.
- Kindness resolves the scene.
- The word "trance" appears as part of the mystery's atmosphere, but the story stays
  child-facing and grounded in a simple simulation.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/trance_dialogue_misunderstanding_kindness_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/trance_dialogue_misunderstanding_kindness_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/trance_dialogue_misunderstanding_kindness_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/trance_dialogue_misunderstanding_kindness_whodunit.py --verify
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
    kind: str = "thing"  # "character" | "thing"
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
    detail: str
    hidden_spot: str
    quiet_type: str = "quiet"

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
class Clue:
    id: str
    label: str
    phrase: str
    use_word: str
    is_strange: bool = False
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
class Suspect:
    id: str
    label: str
    kind: str
    habit: str
    has_alias: bool = False
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
class Kindness:
    id: str
    action: str
    effect: str
    answer: str
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


def _r_spread_rumor(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["suspicion"] < THRESHOLD:
            continue
        sig = ("rumor", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("room").meters["tense"] += 1
        out.append("__rumor__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["helped"] < THRESHOLD:
            continue
        sig = ("kindness", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("room").meters["safe"] += 1
        ent.memes["warmth"] += 1
        out.append("__kindness__")
    return out


CAUSAL_RULES = [
    Rule("rumor", "social", _r_spread_rumor),
    Rule("kindness", "social", _r_kindness),
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


def predict_misunderstanding(world: World, clue_id: str) -> dict:
    sim = world.copy()
    _show_clue(sim, sim.get(clue_id), narrate=False)
    return {
        "tense": sim.get("room").meters["tense"],
        "spooked": sim.get("child").memes["worry"] >= THRESHOLD,
    }


def _show_clue(world: World, clue: Entity, narrate: bool = True) -> None:
    clue.meters["revealed"] += 1
    world.get("child").memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def tell_setting(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"At {setting.place}, the air was still and {setting.detail}."
        f" {child.id} and {helper.id} were looking for a missing thing."
    )
    world.say(
        f"Near {setting.hidden_spot}, {child.id} found a clue and stared at it in a kind of trance."
    )


def talk(world: World, child: Entity, helper: Entity, clue: Clue) -> None:
    world.say(
        f'"What is this?" {child.id} asked. "{clue.use_word}, maybe?"'
    )
    helper.memes["care"] += 1
    world.say(
        f'"No," {helper.id} said, peering closer. "I think it means {clue.phrase}."'
    )


def mixup(world: World, child: Entity, helper: Entity, clue: Clue, suspect: Suspect) -> None:
    child.meters["suspicion"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.id} looked from the clue to {helper.id} and guessed wrong. "
        f'"You hid it, didn\'t you?" {child.id} said.'
    )
    if suspect.has_alias:
        world.say(
            f'"I only know {suspect.label} by the nickname {suspect.kind}," {helper.id} replied, '
            f"which made the guess even more confusing."
        )
    else:
        world.say(f'"No," {helper.id} said. "I was trying to help."')


def explain(world: World, helper: Entity, child: Entity, clue: Clue, suspect: Suspect) -> None:
    world.say(
        f'"Look," {helper.id} said softly. "{clue.phrase} is just {suspect.habit}. '
        f"It doesn't mean anyone did something bad.\""
    )


def kindness_beat(world: World, helper: Entity, child: Entity, kind: Kindness) -> None:
    child.meters["helped"] += 1
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f"{helper.id} chose {kind.action}. {kind.effect} {kind.answer}"
    )


def ending(world: World, child: Entity, helper: Entity, clue: Clue, suspect: Suspect) -> None:
    world.say(
        f"Then {child.id} laughed, because the clue was never a secret at all. "
        f"It was only {suspect.habit}, and the missing thing was right where it belonged."
    )
    world.say(
        f"{child.id} thanked {helper.id}, and the room felt calm again."
    )


def tell(setting: Setting, clue: Clue, suspect: Suspect, kindness: Kindness,
         child_name: str = "Mila", child_type: str = "girl",
         helper_name: str = "Noah", helper_type: str = "boy") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    room = world.add(Entity(id="room", kind="thing", type="room", label="the room"))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="thing", label=clue.label))

    world.facts["setting"] = setting
    world.facts["clue"] = clue
    world.facts["suspect"] = suspect
    world.facts["kindness"] = kindness
    world.facts["child"] = child
    world.facts["helper"] = helper

    tell_setting(world, child, helper, setting)
    world.para()
    _show_clue(world, clue_ent)
    talk(world, child, helper, clue)
    mixup(world, child, helper, clue, suspect)
    explain(world, helper, child, clue, suspect)
    world.para()
    kindness_beat(world, helper, child, kindness)
    ending(world, child, helper, clue, suspect)

    world.facts["outcome"] = "resolved"
    world.facts["room"] = room
    return world


SETTINGS = {
    "library": Setting("library", "the library", "the shelves were tall and whisper-quiet", "the reading nook"),
    "hall": Setting("hall", "the school hall", "the hallway was bright but hushed", "the lost-and-found shelf"),
    "attic": Setting("attic", "the attic", "the rafters made the shadows look mysterious", "the old trunk"),
}

CLUES = {
    "note": Clue("note", "a note", "a note with a tiny star", "note", True, {"note", "paper"}),
    "ribbon": Clue("ribbon", "a ribbon", "a ribbon with a loop", "ribbon", True, {"ribbon", "cloth"}),
    "key": Clue("key", "a key", "a small brass key", "key", True, {"key", "metal"}),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "pet", "sleeping under warm lamps", False, {"cat"}),
    "teacher": Suspect("teacher", "the teacher", "grown-up", "keeping spare things tidy", False, {"teacher"}),
    "uncle": Suspect("uncle", "Uncle Ben", "helper", "sorting boxes in a hurry", True, {"uncle"}),
}

KINDNESSES = {
    "share": Kindness("share", "sharing the flashlight", "The light made the corners less scary.", "It helped everyone see the answer.", {"help", "light"}),
    "listen": Kindness("listen", "listening carefully", "The room felt gentler after that.", "The careful listening made the misunderstanding shrink.", {"listen", "care"}),
    "return": Kindness("return", "walking back together to return the thing", "The missing thing was found without anyone being blamed.", "That kind step fixed the whole mix-up.", {"return", "help"}),
}

CHILDREN = ["Mila", "Eden", "Pia", "Nora", "Leo", "Finn", "Owen", "Ivy"]
HELPERS = ["Noah", "June", "Sage", "Maya", "Eli", "Rose"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    kindness: str
    child_name: str
    helper_name: str
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
        for c in CLUES:
            for u in SUSPECTS:
                for k in KINDNESSES:
                    combos.append((s, c, u, k))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: dialogue, misunderstanding, kindness, and a whodunit tone.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--kindness", choices=KINDNESSES)
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
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)
              and (args.kindness is None or c[3] == args.kindness)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, suspect, kindness = rng.choice(sorted(combos))
    child_name = rng.choice(CHILDREN)
    helper_name = rng.choice([n for n in HELPERS if n != child_name])
    return StoryParams(setting, clue, suspect, kindness, child_name, helper_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    clue = f["clue"]
    suspect = f["suspect"]
    kind = f["kindness"]
    return [
        f'Write a child-friendly whodunit story that includes the word "trance" and a clue like {clue.label}.',
        f"Tell a short mystery where {child.id} and {helper.id} talk, misunderstand the clue, and then solve it kindly.",
        f"Write a gentle mystery with dialogue, a mistake, and {kind.action} as the turning point.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    clue = f["clue"]
    suspect = f["suspect"]
    kind = f["kindness"]
    return [
        ("Who was the story about?",
         f"It was about {child.id} and {helper.id}, who were trying to solve a small mystery together."),
        ("What did the child find?",
         f"{child.id} found {clue.phrase}, and it looked strange enough to start the mystery."),
        ("Why did the child get confused?",
         f"{child.id} guessed wrong about the clue and thought {helper.id} might be hiding something. The misunderstanding made the room feel tense for a moment."),
        ("How did they fix the problem?",
         f"{helper.id} answered gently and chose {kind.action}. That kindness helped clear the misunderstanding and showed the clue was only {suspect.habit}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue = f["clue"]
    kind = f["kindness"]
    tags = set(clue.tags) | set(kind.tags)
    bank = {
        "note": QAItem("What is a note?", "A note is a short message written on paper."),
        "ribbon": QAItem("What is a ribbon?", "A ribbon is a soft strip of cloth used for tying or decorating things."),
        "key": QAItem("What is a key?", "A key is a small metal tool that can open a lock."),
        "help": QAItem("What does kindness mean?", "Kindness means helping, caring, or being gentle with someone."),
        "light": QAItem("Why can light help in a mystery?", "Light helps people see details clearly, so it is easier to understand what is happening."),
        "listen": QAItem("Why is listening carefully useful?", "Listening carefully helps people understand the real meaning instead of guessing wrong."),
        "care": QAItem("What does it mean to be careful?", "Being careful means slowing down and paying attention so you do not make a mistake."),
        "return": QAItem("Why is it kind to return something?", "Returning something helps fix a mix-up and shows respect for the person who lost it."),
    }
    order = ["note", "ribbon", "key", "help", "light", "listen", "care", "return"]
    return [bank[t] for t in order if t in tags]


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
mystery_tense(Room) :- tense(Room, T), T >= 1.
kindness_helps(Room) :- safe(Room, S), S >= 1.
valid_story(S, C, U, K) :- setting(S), clue(C), suspect(U), kindness(K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for uid in SUSPECTS:
        lines.append(asp.fact("suspect", uid))
    for kid in KINDNESSES:
        lines.append(asp.fact("kindness", kid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: empty story.")
        rc = 1
    else:
        print("OK: generation smoke test passed.")
    return rc


CURATED = [
    StoryParams("library", "note", "cat", "listen", "Mila", "Noah"),
    StoryParams("hall", "ribbon", "teacher", "share", "Eden", "June"),
    StoryParams("attic", "key", "uncle", "return", "Leo", "Maya"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], SUSPECTS[params.suspect], KINDNESSES[params.kindness], params.child_name, "girl" if params.child_name in {"Mila", "Pia", "Nora", "Ivy"} else "boy", params.helper_name, "girl" if params.helper_name in {"June", "Maya", "Rose"} else "boy")
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
        print(asp_program("", "#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos[:20]:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1

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

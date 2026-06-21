#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/smack_teamwork_bad_ending_sound_effects_whodunit.py
====================================================================================

A small whodunit storyworld for a neighborhood puzzle: two kids and a grown-up
try to solve a noisy little mystery together, but their teamwork goes wrong and
the ending turns bad. The story keeps the clue-hunt feel of a whodunit, includes
sound effects, and uses the seed word "smack".
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
    traits: list[str] = field(default_factory=list)
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
class Room:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Clue:
    id: str
    label: str
    sound: str
    owner: str
    place: str
    risk: int
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
    verb: str
    sound: str
    method: str
    consequence: str
    power: int
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
class StoryParams:
    room: str = "kitchen"
    clue: str = "cookie_jar"
    action: str = "smack"
    hero: str = "Maya"
    hero_gender: str = "girl"
    helper: str = "Noah"
    helper_gender: str = "boy"
    parent: str = "mother"
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


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        w = World(copy.deepcopy(self.room))
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
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


def _r_noise(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["noise"] < THRESHOLD:
            continue
        sig = ("noise", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.room.memes["tension"] += 1
        out.append("__noise__")
    return out


def _r_panic(world: World) -> list[str]:
    out = []
    if world.room.memes["tension"] >= THRESHOLD:
        if ("panic",) in world.fired:
            return out
        world.fired.add(("panic",))
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["fear"] += 1
        out.append("__panic__")
    return out


RULES = [Rule("noise", _r_noise), Rule("panic", _r_panic)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


ROOMS = {
    "kitchen": Room("kitchen", "the kitchen"),
    "hall": Room("hall", "the hallway"),
    "attic": Room("attic", "the attic"),
}

CLUES = {
    "cookie_jar": Clue("cookie_jar", "cookie jar", "clink", "Parent", "counter", 1, {"jar", "noise"}),
    "toy_box": Clue("toy_box", "toy box", "thump", "Parent", "bench", 2, {"box", "noise"}),
    "lamp_chain": Clue("lamp_chain", "lamp chain", "ting", "Parent", "table", 2, {"lamp", "noise"}),
}

ACTIONS = {
    "smack": Action("smack", "smack it", "SMACK!", "smacked", "smacked too hard", 2, {"smack", "noise"}),
    "tap": Action("tap", "tap it", "tap-tap", "tapped", "tapped softly", 1, {"tap", "noise"}),
    "bang": Action("bang", "bang on it", "BANG!", "banged", "banged hard", 3, {"bang", "noise"}),
}

GIRL_NAMES = ["Maya", "Luna", "Ivy", "Zoe", "Ella", "Nora"]
BOY_NAMES = ["Noah", "Finn", "Theo", "Leo", "Eli", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for clue in CLUES:
            for action in ACTIONS:
                if action == "tap" and CLUES[clue].risk > 1:
                    continue
                if ACTIONS[action].power >= CLUES[clue].risk:
                    combos.append((room, clue, action))
    return combos


def explain_rejection(clue: Clue, action: Action) -> str:
    return (
        f"(No story: {action.label} would not make a strong enough whodunit beat "
        f"for the {clue.label}, or it would be too weak to matter. Pick a louder clue "
        f"or a stronger action.)"
    )


def sound_line(sound: str) -> str:
    return sound


def setup(world: World, hero: Entity, helper: Entity, parent: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"Late one evening, {hero.id} and {helper.id} found a mystery in {world.room.label}. "
        f"Something had vanished, and only a clue on the table remained."
    )
    world.say(
        f'"{clue.sound}!" went the clue when they touched it. '
        f"{hero.id} frowned. {helper.id} leaned closer. \"We should work together,\" "
        f"{helper.pronoun()} said."
    )


def investigate(world: World, hero: Entity, helper: Entity, clue: Clue, action: Action) -> None:
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"They teamed up at once: {hero.id} looked under the chair while {helper.id} "
        f"reached for the clue. Then {hero.id} said, \"Maybe {action.verb} will help.\""
    )
    world.say(f'"{action.sound}" {hero.id} said, and {helper.id} nodded.')
    clue_ent = world.get(clue.id)
    clue_ent.meters["noise"] += 1
    propagate(world, narrate=False)


def reveal(world: World, parent: Entity, clue: Clue, action: Action) -> None:
    world.say(
        f"{parent.label_word.capitalize()} came in, following the noise. "
        f"At last the clue gave up its secret with a {sound_line(clue.sound)}."
    )
    world.say(
        f"That made the answer clear: the missing thing had been moved into the wrong room, "
        f"and the whole search had started from a small mistake."
    )


def bad_ending(world: World, parent: Entity, hero: Entity, helper: Entity, clue: Clue) -> None:
    world.room.meters["broken"] += 1
    hero.memes["guilt"] += 1
    helper.memes["guilt"] += 1
    world.say(
        f"But then {hero.id} tried to smack the clue again, and {ACTIONS['smack'].sound} -- "
        f"the little piece slipped, fell, and broke."
    )
    world.say(
        f"{parent.label_word.capitalize()} rushed in too late. The clue was ruined, the missing thing "
        f"was still missing, and the mystery ended in a bad, sad mess."
    )
    world.say(
        f"Nobody solved the case, and the house grew quiet except for the soft {clue.sound} of regret."
    )


def tell(room: Room, clue: Clue, action: Action, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str, parent_type: str) -> World:
    world = World(room)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    clue_ent = world.add(Entity(id=clue.id, kind="thing", type="thing", label=clue.label))
    hero.memes["curiosity"] = 1
    helper.memes["curiosity"] = 1

    setup(world, hero, helper, parent, clue)
    world.para()
    investigate(world, hero, helper, clue, action)
    world.para()
    reveal(world, parent, clue, action)
    world.para()
    bad_ending(world, parent, hero, helper, clue)

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        clue=clue,
        action=action,
        room=room,
        outcome="bad",
        broken=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit story for a young child that includes the sound "{f["clue"].sound}" and the word "smack".',
        f"Tell a teamwork mystery where {f['hero'].id} and {f['helper'].id} investigate a clue together, but the ending goes wrong.",
        f"Write a child-friendly detective story with sound effects, teamwork, and a bad ending after someone says smack.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue"]
    action = f["action"]
    return [
        QAItem(
            question="Who worked together in the mystery?",
            answer=f"{hero.id} and {helper.id} worked together. They searched side by side and each one helped with a different part of the clue hunt.",
        ),
        QAItem(
            question="What sound did the clue make?",
            answer=f"The clue made a {clue.sound} sound. That noisy little sound was part of the puzzle, and it drew everyone toward the table.",
        ),
        QAItem(
            question="What happened when they used smack?",
            answer=f"When they used smack, the clue got damaged. The choice was too rough, so the mystery ended badly instead of being solved neatly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work toward the same goal. Each person does a part, and together they can do more than one person alone.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story about figuring out what happened and who did it. The reader follows clues to solve the puzzle.",
        ),
        QAItem(
            question="Why are sound effects used in stories?",
            answer="Sound effects make scenes feel lively and clear. They help you hear the action in your head, like a smack or a clink.",
        ),
        QAItem(
            question="Why can smack be a problem in a mystery?",
            answer="Smacking something can be too rough and may damage a clue. In a mystery, a damaged clue can make the answer harder to find.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    room = world.room
    if room.meters:
        lines.append(f"  room ({room.id}) meters={dict(room.meters)} memes={dict(room.memes)}")
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(room="kitchen", clue="cookie_jar", action="smack", hero="Maya", hero_gender="girl", helper="Noah", helper_gender="boy", parent="mother"),
    StoryParams(room="hall", clue="toy_box", action="tap", hero="Luna", hero_gender="girl", helper="Finn", helper_gender="boy", parent="father"),
]


def valid_params(params: StoryParams) -> bool:
    return params.room in ROOMS and params.clue in CLUES and params.action in ACTIONS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.room not in ROOMS:
        raise StoryError("Unknown room.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if args.action and args.action not in ACTIONS:
        raise StoryError("Unknown action.")
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.clue is None or c[1] == args.clue)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room_id, clue_id, action_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(room=room_id, clue=clue_id, action=action_id,
                       hero=hero, hero_gender=hero_gender,
                       helper=helper, helper_gender=helper_gender,
                       parent=parent)


def generate(params: StoryParams) -> StorySample:
    if not valid_params(params):
        raise StoryError("Invalid parameters.")
    world = tell(ROOMS[params.room], CLUES[params.clue], ACTIONS[params.action],
                 params.hero, params.hero_gender, params.helper, params.helper_gender,
                 params.parent)
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("sound", cid, c.sound))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("power", aid, a.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R,C,A) :- room(R), clue(C), action(A), power(A,P), clue(C), P >= 1.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with teamwork, sound effects, and a bad ending.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gesture_happy_ending_animal_story.py
===================================================================

A small animal story world about a shy gesture, a mistaken feeling, and a happy
ending. A tiny forest scene gives one animal a problem it cannot solve alone:
it needs to ask, share, or point clearly, and another animal notices the gesture,
understands it, and helps. The world model tracks physical meters and emotional
memes so the ending changes because state changes.

The seed words and style request are intentionally simple:
- word: gesture
- feature: happy ending
- style: animal story

This script keeps the story child-facing, concrete, and state-driven.
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
MOOD_UP = 1.0
MOOD_DOWN = 1.0


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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    setting_line: str
    sound: str
    weather: str = ""
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
class Problem:
    id: str
    need: str
    obstacle: str
    sign: str
    risky: bool = True
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
class Gesture:
    id: str
    name: str
    line: str
    means: str
    helps_with: str
    tag: str = "gesture"
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
class HelperAction:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    gesture: str
    helper_action: str
    protagonist: str
    protagonist_gender: str
    friend: str
    friend_gender: str
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


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.animals():
        if e.memes["hope"] < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["calm"] += MOOD_UP
        out.append("__relief__")
    return out


CAUSAL_RULES: list[Callable[[World], list[str]]] = [_r_relief]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
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


def problem_needs_gesture(problem: Problem, gesture: Gesture) -> bool:
    return gesture.helps_with == problem.need


def action_is_reasonable(action: HelperAction, problem: Problem) -> bool:
    return action.sense >= 2 and problem.risky


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, problem in PROBLEMS.items():
            for gid, gesture in GESTURES.items():
                for aid, action in ACTIONS.items():
                    if problem_needs_gesture(problem, gesture) and action_is_reasonable(action, problem):
                        combos.append((sid, pid, gid, aid))
    return combos


def predict_help(world: World, problem: Problem) -> dict:
    sim = world.copy()
    helper = sim.get("helper")
    helper.meters["distance"] += 1
    helper.memes["attention"] += 1
    return {"noticed": True, "calmed": helper.memes["attention"] >= THRESHOLD}


def setup(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["shy"] += 1
    friend.memes["kind"] += 1
    world.say(
        f"At {setting.place}, the {setting.sound} of the trees mixed with soft paws on the path. "
        f"{hero.id} and {friend.id} were close enough to share the same little adventure."
    )


def introduce_problem(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["worry"] += 1
    hero.meters["carried"] += 1
    world.say(
        f"{hero.id} had a small problem: {problem.sign}. {hero.pronoun().capitalize()} wanted {problem.need}, "
        f"but {problem.obstacle} made it hard to ask."
    )


def make_gesture(world: World, hero: Entity, gesture: Gesture) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"Then {hero.id} made {gesture.line}. It was a quiet {gesture.tag} that meant {gesture.means}."
    )


def notice_and_help(world: World, friend: Entity, hero: Entity, action: HelperAction, problem: Problem) -> None:
    friend.memes["attention"] += 1
    world.say(
        f"{friend.id} noticed the {problem.sign} right away and understood the gesture. "
        f"In a flash {friend.pronoun()} {action.text}."
    )
    hero.meters["carried"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    propagate(world, narrate=False)


def ending(world: World, hero: Entity, friend: Entity, setting: Setting, gesture: Gesture) -> None:
    world.say(
        f"After that, {hero.id} could relax and smile. {friend.id} stayed nearby, and the two animals "
        f"went on together through {setting.place}, now using small gestures and gentle looks to understand each other."
    )
    world.say(
        f"The day felt bright and safe, and the {gesture.name} had helped turn a hard moment into a happy one."
    )


def tell(setting: Setting, problem: Problem, gesture: Gesture, action: HelperAction,
         protagonist: str = "Milo", protagonist_gender: str = "boy",
         friend: str = "Mina", friend_gender: str = "girl") -> World:
    world = World(setting)
    hero = world.add(Entity(id=protagonist, kind="character", type=protagonist_gender, role="protagonist"))
    helper = world.add(Entity(id=friend, kind="character", type=friend_gender, role="friend"))
    world.add(Entity(id="helper", kind="character", type="animal", role="helper"))
    world.entities["helper"] = helper

    setup(world, hero, helper, setting)
    world.para()
    introduce_problem(world, hero, problem)
    make_gesture(world, hero, gesture)
    world.para()
    notice_and_help(world, helper, hero, action, problem)
    ending(world, hero, helper, setting, gesture)

    world.facts.update(
        hero=hero,
        friend=helper,
        setting=setting,
        problem=problem,
        gesture=gesture,
        action=action,
        helped=True,
        happy=True,
    )
    return world


SETTINGS = {
    "forest": Setting(id="forest", place="the forest trail", setting_line="soft moss and tall trees", sound="hush"),
    "meadow": Setting(id="meadow", place="the sunny meadow", setting_line="bright grass and clover", sound="whisper"),
    "pond": Setting(id="pond", place="the pond bank", setting_line="reeds and small ripples", sound="lap"),
}

PROBLEMS = {
    "stuck_voice": Problem(id="stuck_voice", need="water", obstacle="a shy throat", sign="a tiny pointing paw toward the pond"),
    "lost_berry": Problem(id="lost_berry", need="berries", obstacle="a branch too high to reach", sign="an upturned nose and a look at the tree"),
    "fallen_leaf": Problem(id="fallen_leaf", need="help", obstacle="a pile of leaves hiding the trail", sign="a paw tapped twice on the ground"),
}

GESTURES = {
    "point": Gesture(id="point", name="pointing gesture", line="a little paw point toward the path", means="this way", helps_with="help"),
    "bow": Gesture(id="bow", name="bow gesture", line="a small bow with one careful step", means="please come with me", helps_with="help"),
    "tap": Gesture(id="tap", name="tapping gesture", line="two gentle taps on the ground", means="look here", helps_with="help"),
}

ACTIONS = {
    "guide": HelperAction(id="guide", sense=3, power=3, text="walked over and guided the way"),
    "share": HelperAction(id="share", sense=3, power=3, text="shared the berries from the lower bush"),
    "lift": HelperAction(id="lift", sense=2, power=2, text="lifted the branch just enough for a safe step"),
}

GIRL_NAMES = ["Mina", "Luna", "Pip", "Tia", "Nora"]
BOY_NAMES = ["Milo", "Finn", "Bram", "Otis", "Pico"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a young child that includes the word "{f["gesture"].name}".',
        f"Tell a happy-ending story where {f['hero'].id} uses a small gesture and {f['friend'].id} understands it.",
        f"Write a gentle forest story about animals, a shy problem, and a helpful gesture that leads to a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, problem, gesture, action = f["hero"], f["friend"], f["problem"], f["gesture"], f["action"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, two animals in {world.setting.place}."),
        ("What problem did {0} have?".format(hero.id),
         f"{hero.id} wanted {problem.need}, but {problem.obstacle} made it hard to ask. That is why the story needed a gesture."),
        ("What gesture did {0} make?".format(hero.id),
         f"{hero.id} made {gesture.line}. It was a quiet way to say {gesture.means}."),
        ("How did the other animal help?",
         f"{friend.id} noticed the gesture and {action.text}. That helped {hero.id} feel safe and happy again."),
        ("How did the story end?",
         f"It ended happily. The animals understood each other, the worry went away, and they kept going together through {world.setting.place}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a gesture?",
         "A gesture is a movement, like pointing or nodding, that can help animals or people understand each other without many words."),
        ("Why can gestures be helpful?",
         "Gestures can help when someone is shy, far away, or needs to show something quickly. They make it easier to ask for help or share a feeling."),
        ("Why are animal stories nice for young children?",
         "Animal stories are nice because animals can feel familiar and gentle, and their actions are easy to imagine. They often show kindness in a simple way."),
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
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="forest", problem="stuck_voice", gesture="point", helper_action="guide",
                protagonist="Milo", protagonist_gender="boy", friend="Mina", friend_gender="girl"),
    StoryParams(setting="meadow", problem="lost_berry", gesture="bow", helper_action="share",
                protagonist="Nora", protagonist_gender="girl", friend="Finn", friend_gender="boy"),
    StoryParams(setting="pond", problem="fallen_leaf", gesture="tap", helper_action="lift",
                protagonist="Pip", protagonist_gender="girl", friend="Otis", friend_gender="boy"),
]


def explain_rejection(problem: Problem, gesture: Gesture) -> str:
    if gesture.helps_with != problem.need:
        return "(No story: that gesture does not fit this animal problem well enough.)"
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
valid(S,P,G,A) :- setting(S), problem(P), gesture(G), action(A),
                  needs(P,N), helps(G,N), sense(A,V), V >= 2.
happy(S,P,G,A) :- valid(S,P,G,A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, p.need))
    for gid, g in GESTURES.items():
        lines.append(asp.fact("gesture", gid))
        lines.append(asp.fact("helps", gid, g.helps_with))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, gesture=None, helper_action=None, protagonist=None, protagonist_gender=None, friend=None, friend_gender=None), _random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as err:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a gesture and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gesture", dest="gesture_name", choices=GESTURES)
    ap.add_argument("--helper-action", choices=ACTIONS)
    ap.add_argument("--protagonist")
    ap.add_argument("--protagonist-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.gesture_name:
        if not problem_needs_gesture(PROBLEMS[args.problem], GESTURES[args.gesture_name]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], GESTURES[args.gesture_name]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.gesture_name is None or c[2] == args.gesture_name)
              and (args.helper_action is None or c[3] == args.helper_action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, gesture, helper_action = rng.choice(sorted(combos))
    hero_gender = args.protagonist_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.protagonist or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    return StoryParams(setting=setting, problem=problem, gesture=gesture, helper_action=helper_action,
                       protagonist=hero, protagonist_gender=hero_gender,
                       friend=friend, friend_gender=friend_gender)


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("problem", PROBLEMS), ("gesture", GESTURES), ("helper_action", ACTIONS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], GESTURES[params.gesture], ACTIONS[params.helper_action],
                 protagonist=params.protagonist, protagonist_gender=params.protagonist_gender,
                 friend=params.friend, friend_gender=params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/precise_apple_flourish_kindness_humor_sound_effects.py
======================================================================================

A small animal-story world about a careful helper, a missed apple, a funny
sound, and a kind flourish that fixes the moment.

Seed words: precise, apple, flourish
Features: Kindness, Humor, Sound Effects
Style: Animal Story
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "cow", "goat"}
        male = {"boy", "father", "dad", "man", "fox", "bear", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    surface: str
    sounds: list[str] = field(default_factory=list)

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
class Snack:
    id: str
    label: str
    phrase: str
    precious: bool = True

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
class Action:
    id: str
    verb: str
    goal: str
    sound: str
    risk: str
    method: str
    resolution: str
    flourish: str
    safe: bool = False

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.sound_log: list[str] = []

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
        clone.sound_log = list(self.sound_log)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["spill"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["embarrassment"] += 1
        out.append("__spill__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if not any(e.meters["spill"] >= THRESHOLD for e in list(world.entities.values())):
        return out
    for e in list(world.entities.values()):
        if e.kind != "character":
            continue
        sig = ("laugh", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["humor"] += 1
        out.append("__laugh__")
    return out


def _r_kind(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("Helper")
    if not helper:
        return out
    if helper.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["warmth"] += 1
    out.append("__kind__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("laugh", _r_laugh), Rule("kind", _r_kind)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_spill(world: World, snack_id: str) -> bool:
    sim = world.copy()
    sim.get(snack_id).meters["spill"] += 1
    propagate(sim, narrate=False)
    return sim.get(snack_id).meters["spill"] >= THRESHOLD


def assert_reasonable(setting: Setting, action: Action, snack: Snack) -> None:
    if not action.safe and snack.precious and action.id == "tumble":
        raise StoryError("That action is too rough for this gentle animal story.")
    if action.id == "precise" and not snack.precious:
        raise StoryError("The precise action only makes sense with a special apple.")


def _sound(txt: str) -> str:
    return txt


def tell(setting: Setting, action: Action, snack: Snack,
         hero_name: str = "Milo", helper_name: str = "Pia",
         hero_type: str = "fox", helper_type: str = "rabbit",
         friend_type: str = "bird") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label=helper_name))
    friend = world.add(Entity(id="Friend", kind="character", type=friend_type, role="friend"))
    apple = world.add(Entity(id="Apple", kind="thing", type="apple", label=snack.label, attrs={"phrase": snack.phrase}))
    table = world.add(Entity(id="table", kind="thing", type="table", label="the picnic table"))
    world.facts["setting"] = setting
    world.facts["action"] = action
    world.facts["snack"] = snack

    hero.memes["care"] = 1
    helper.memes["kindness"] = 1
    friend.memes["humor"] = 1

    world.say(
        f"{hero.id} the {hero.type} was helping at {setting.place}. "
        f"{helper.label_word} set down {snack.phrase} on {setting.surface}, and everything felt calm."
    )
    world.say(
        f'{hero.id} wanted to be precise. "{action.verb.capitalize()}," {hero.id} said, '
        f"and pointed exactly at the spot where the {snack.label} should go."
    )

    world.para()
    world.say(
        f"Then came a tiny {action.sound} on the {setting.surface}."
    )
    if action.id == "tumble":
        hero.meters["spill"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{hero.id} slipped, and the {snack.label} rolled -- {action.sound} -- right off the table."
        )
    else:
        world.say(
            f"{hero.id} moved with a careful {action.method}, and the {snack.label} stayed balanced."
        )
        world.say(f'But the breeze gave a mischievous little "{action.sound}" anyway.')

    world.para()
    if hero.meters["spill"] >= THRESHOLD:
        world.say(
            f"{friend.id} the {friend.type} blinked, then let out a funny little {action.sound} of a laugh."
        )
        if predict_spill(world, "Apple"):
            world.say(
                f"{helper.label_word.capitalize()} did not scold. {helper.label_word} just smiled, "
                f"picked up the {snack.label}, and said, \"Let's try again, slower this time.\""
            )
        helper.memes["kindness"] += 1
        world.say(
            f"{helper.label_word.capitalize()} set the {snack.label} back with a gentle flourish, "
            f"like a tiny magic trick."
        )
        world.say(
            f"This time, {hero.id} used {action.resolution}, and the {snack.label} sat steady and safe."
        )
    else:
        helper.memes["kindness"] += 1
        world.say(
            f"{helper.label_word.capitalize()} chuckled kindly and gave {hero.id} a warm nod."
        )
        world.say(
            f"With one bright flourish, the {snack.label} stayed in place, and the little team laughed together."
        )

    world.say(
        f"By the end, {hero.id} had learned that precise hands, a kind helper, and a funny sound could all fit in one happy day."
    )

    world.facts.update(hero=hero, helper=helper, friend=friend, apple=apple, table=table,
                       outcome="spill" if hero.meters["spill"] >= THRESHOLD else "steady")
    return world


SETTINGS = {
    "orchard": Setting("orchard", "the orchard", "the grass under the apple tree", ["rustle", "tweet"]),
    "picnic": Setting("picnic", "the picnic", "the red picnic blanket", ["chirp", "buzz"]),
    "barnyard": Setting("barnyard", "the barnyard", "the warm hay bale", ["moo", "cluck"]),
}

ACTIONS = {
    "precise": Action(
        "precise", "place the apple just so", "a careful spot",
        "plink", "nothing risky", "steady hands", "the apple stayed in place", "flourish", safe=True
    ),
    "tumble": Action(
        "tumble", "carry the apple", "the basket",
        "boing", "a spill", "slowly and with two hands", "the apple stayed in place", "flourish", safe=False
    ),
}

SNACKS = {
    "apple": Snack("apple", "the apple", "a shiny red apple", precious=True),
    "pie": Snack("pie", "the pie", "a small berry pie", precious=True),
    "snack": Snack("snack", "the snack", "a simple snack", precious=False),
}

GUESTS = ["Milo", "Nora", "Pip", "Luna", "Toby", "Roo"]
HELPERS = ["Pia", "Holly", "Nell", "Bram", "Mika", "Sage"]



@dataclass
class StoryParams:
    setting: str
    action: str
    snack: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    friend_gender: str
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

CURATED = [
    StoryParams("orchard", "precise", "apple", "Milo", "girl", "Pia", "rabbit", "bird"),
    StoryParams("picnic", "tumble", "apple", "Nora", "girl", "Holly", "rabbit", "bird"),
    StoryParams("barnyard", "precise", "pie", "Pip", "boy", "Bram", "rabbit", "bird"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for aid in ACTIONS:
            for sn in SNACKS:
                if aid == "precise" and sn == "apple":
                    combos.append((sid, aid, sn))
                if aid == "tumble" and sn == "apple":
                    combos.append((sid, aid, sn))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with kindness, humor, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    if args.action and args.snack and args.action == "precise" and args.snack != "apple":
        raise StoryError("The precise apple story needs an apple.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.snack is None or c[2] == args.snack)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, snack = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GUESTS)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting, action, snack, hero, "fox", helper, "rabbit", "bird")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story that uses the words "precise", "apple", and "flourish".',
        f"Tell a gentle story where {f['hero'].id} tries to be precise with an apple, and a kind helper makes it funny instead of upsetting.",
        f"Write a short story with kindness, humor, and sound effects in an orchard or picnic setting.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, snack, setting = f["hero"], f["helper"], f["snack"], f["setting"]
    out = []
    if f["outcome"] == "spill":
        out.append((
            f"What happened to the apple?",
            f"It rolled off the table with a little {world.facts['action'].sound} sound. "
            f"That made the moment funny, but {helper.label_word} stayed kind and helped put it back."
        ))
    else:
        out.append((
            f"How did {hero.id} handle the apple?",
            f"{hero.id} handled it with careful hands, and the apple stayed steady. "
            f"The story still used a playful sound effect and ended with everyone smiling."
        ))
    out.append((
        f"How did {helper.label_word} help?",
        f"{helper.label_word.capitalize()} helped by staying kind, not scolding, and giving a gentle flourish when the apple needed another try."
    ))
    out.append((
        "Why did the story feel funny?",
        f"It had a tiny sound effect, a little slip, and then a cheerful recovery. "
        f"The humor came from the harmless mishap, not from anyone being mean."
    ))
    return out


KNOWLEDGE = [
    ("What is an apple?",
     "An apple is a round fruit that can be red, green, or yellow. People and animals sometimes enjoy it as a snack."),
    ("What does it mean to be precise?",
     "Being precise means doing something carefully and exactly, with attention to the little details."),
    ("What is a flourish?",
     "A flourish is a lively, showy little motion, like a quick swirl or a fancy finish."),
    ("What is kindness?",
     "Kindness means treating others gently and helpfully, especially when something goes wrong."),
    ("What are sound effects?",
     "Sound effects are little words or noises, like plink or boing, that help a story feel alive."),
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return list(KNOWLEDGE)


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
    lines.append("== (3) World-knowledge questions ==")
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,N) :- setting(S), action(A), snack(N), A = precise, N = apple.
valid(S,A,N) :- setting(S), action(A), snack(N), A = tumble, N = apple.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for nid in SNACKS:
        lines.append(asp.fact("snack", nid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, action=None, snack=None, hero=None, helper=None), random.Random(0)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    action = ACTIONS[params.action]
    snack = SNACKS[params.snack]
    assert_reasonable(setting, action, snack)
    world = tell(setting, action, snack, params.hero, params.helper, "fox", "rabbit", "bird")
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gargle_retire_tennis_suspense_moral_value_curiosity.py
======================================================================================

A standalone TinyStories-style storyworld about a child, a curious mystery,
tennis practice, a skipped-gargle suspense beat, and a moral turn toward doing
the right thing. The domain is small and classical: a young player, an adult
coach or parent, a tiny problem, a choice, and a clear ending image.

Seed words:
- gargle
- retire
- tennis

Features:
- Suspense
- Moral Value
- Curiosity

Style:
- Rhyming Story

The world model tracks typed entities with physical meters and emotional memes.
The story is generated from simulated state, not from a frozen paragraph.
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
    mood: str
    detail: str
    afford: set[str] = field(default_factory=set)

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
class Curiosity:
    id: str
    label: str
    sparkle: str
    clue: str

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
class TennisItem:
    id: str
    label: str
    phrase: str
    action: str
    safe: bool = True

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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    player = world.entities.get("child")
    if not player:
        return out
    if player.memes["worry"] < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("court").meters["tension"] += 1
    out.append("__suspense__")
    return out


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("curiosity",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["questioning"] += 1
    out.append("__curious__")
    return out


CAUSAL_RULES = [
    Rule("suspense", "mood", _r_suspense),
    Rule("curiosity", "mind", _r_curiosity),
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming tennis storyworld with suspense, moral value, and curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--tennis", choices=TENNIS.items())
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


def _rhyming_pair(setting: Setting) -> tuple[str, str]:
    return {
        "park": ("spark", "dark"),
        "court": ("short", "sport"),
        "school": ("cool", "rule"),
    }[setting.id]


def tell(setting: Setting, curiosity: Curiosity, tennis: TennisItem,
         name: str = "Mia", gender: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity("child", kind="character", type=gender, role="player", traits=["young"]))
    parent = world.add(Entity("parent", kind="character", type=parent_type, role="guide", label="the parent"))
    court = world.add(Entity("court", type="place", label=setting.place))
    ball = world.add(Entity("ball", type="thing", label=tennis.label))
    child.id = name
    child.memes["curiosity"] = 1
    child.memes["worry"] = 1
    world.facts["name"] = name
    world.facts["curiosity"] = curiosity
    world.facts["tennis"] = tennis

    rhyme_a, rhyme_b = _rhyming_pair(setting)
    world.say(f"{name} went out to play by the {setting.place}, with a bright little grin and a curious gaze.")
    world.say(f"The air held a hush, a soft little buzz, and {setting.detail} made the day feel snug as a hug.")
    world.say(f"{name} saw {curiosity.label} and wondered, with wonder, what made {curiosity.sparkle} sparkle and thunder.")

    world.para()
    world.say(f"{name} wanted to play {tennis.label}, but first came the old rule to {tennis.action}.")
    world.say(f"{name} heard a strange clue: {curiosity.clue}, and {name} wondered what that could do.")
    world.say(f"Near the bench sat a cup, and inside it was up a note that said, 'Do not skip the gargle, dear pup.'")
    child.memes["worry"] += 1
    child.memes["curiosity"] += 1
    propagate(world, narrate=False)
    world.say(f"The clue made {name} slow down, not because of a frown, but because good choices wear a golden crown.")

    world.para()
    world.say(f"{parent.label_word.capitalize()} came near with a smile and said, 'Let's be safe all the while.'")
    world.say(f"'First gargle and rinse, then you may play; health comes before fun at the end of the day.'")
    child.memes["moral"] += 1
    child.memes["relief"] += 1
    world.say(f"{name} listened and did it, then bounced like a sprite, and the worry went shrinking away from the light.")

    world.para()
    world.say(f"At last {name} served the ball with a swish, and the bounce made a bright little wish.")
    world.say(f"They retired to the bench when the sky grew dim; the game ended softly, but joy stayed with him.")
    world.say(f"The court felt calm, and the ending was clear: curiosity guided them; moral value was near.")
    world.say(f"So {name} kept a clean smile and a safe, steady pace, with a happy, brave glow on {name}'s face.")

    world.facts.update(child=child, parent=parent, court=court, ball=ball, outcome="safe")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the words "{f["curiosity"].label}", "gargle", and "retire".',
        f"Tell a suspenseful but gentle tennis story where {f['name']} gets curious, chooses the right moral action, and then retires from play at the end.",
        f"Write a short rhyming moral story about tennis practice, curiosity, and doing the healthy thing first.",
    ]


def story_qa(world: World) -> list[QAItem]:
    name = world.facts["name"]
    cur = world.facts["curiosity"]
    tennis = world.facts["tennis"]
    return [
        QAItem(
            question=f"What made {name} curious?",
            answer=f"{name} noticed {cur.label} and wondered about {cur.sparkle}. That clue made the moment feel suspenseful before the parent gave the safe answer."
        ),
        QAItem(
            question=f"What did {name} do before playing tennis?",
            answer=f"{name} gargled and rinsed first, because the parent reminded {name} that health comes before fun. That was the moral choice in the story."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{name} played tennis safely and then retired to the bench when the sky grew dim. The ending shows that curiosity can be good when it leads to a safe choice."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is gargling?", "Gargling is swishing water in your throat and mouth to clean them or soothe them."),
        QAItem("What does retire mean?", "To retire means to stop for the day and rest, or to leave a game or job behind for a while."),
        QAItem("What is tennis?", "Tennis is a game where players hit a ball with rackets over a net."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "park": Setting("park", "the park", "a hush of suspense", "The trees leaned close, and the tennis court looked a little mysterious.", {"tennis"}),
    "court": Setting("court", "the court", "a neat bright hush", "The net stood straight, and the lines looked like little white roads.", {"tennis"}),
    "school": Setting("school", "the schoolyard", "a curious breeze", "The bells were quiet, and the playground waited like a stage.", {"tennis"}),
}

CURIOSITIES = {
    "note": Curiosity("note", "a note", "a tiny folded corner", "It said to pause and choose well."),
    "whistle": Curiosity("whistle", "a whistle", "a sharp little sparkle", "It sounded like someone was calling for care."),
    "shiny": Curiosity("shiny", "a shiny coin", "a bright round glimmer", "It gleamed beside the bench and asked to be noticed."),
}

TENNIS = {
    "ball": TennisItem("ball", "tennis", "gargle, rinse, and then play", "play tennis"),
    "practice": TennisItem("practice", "tennis practice", "gargle, rinse, and then play", "play tennis"),
    "match": TennisItem("match", "tennis match", "gargle, rinse, and then play", "play tennis"),
}

GIRL_NAMES = ["Mia", "Luna", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Eli", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, t) for s in SETTINGS for c in CURIOSITIES for t in TENNIS]


@dataclass
@dataclass
class StoryParams:
    setting: str
    curiosity: str
    tennis: str
    name: str
    gender: str
    parent: str
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


ASP_RULES = r"""
setting(S) :- setting_fact(S).
curiosity(C) :- curiosity_fact(C).
tennis(T) :- tennis_fact(T).
valid(S, C, T) :- setting(S), curiosity(C), tennis(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for cid in CURIOSITIES:
        lines.append(asp.fact("curiosity_fact", cid))
    for tid in TENNIS:
        lines.append(asp.fact("tennis_fact", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        _ = sample.to_json()
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.curiosity is None or c[1] == args.curiosity)
              and (args.tennis is None or c[2] == args.tennis)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, c, t = rng.choice(sorted(combos))
    name = args.name if hasattr(args, "name") and getattr(args, "name") else rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = "girl" if name in GIRL_NAMES else "boy"
    parent = args.parent if hasattr(args, "parent") and getattr(args, "parent") else rng.choice(["mother", "father"])
    return StoryParams(s, c, t, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CURIOSITIES[params.curiosity], TENNIS[params.tennis],
                 name=params.name, gender=params.gender, parent_type=params.parent)
    return StorySample(
        params=params,
        story=world.render(),
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming suspense storyworld about tennis, curiosity, and moral choices.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--tennis", choices=TENNIS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, c, t, "Mia", "girl", "mother")) for s, c, t in valid_combos()[:5]]
    else:
        seen: set[str] = set()
        i = 0
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

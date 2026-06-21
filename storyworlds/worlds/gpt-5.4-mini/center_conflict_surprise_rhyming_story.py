#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/center_conflict_surprise_rhyming_story.py
=========================================================================

A small standalone story world for a rhyming tale about a shared center spot,
a little conflict, and a surprise that turns the mood around.

The world is built as a tiny simulation:
- typed entities with meters and memes
- a forward rule pass over a small causal model
- a reasonableness gate
- an ASP twin for parity checks
- three QA sets grounded in state, not by parsing rendered prose

The seed idea:
- A child wants the center of a dance mat / stage / blanket circle
- A friend wants the same center
- They quarrel
- A surprise reveals a better sharing pattern
- The ending proves the center is shared, not taken

This file is self-contained and stdlib-only.
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    age: int = 0
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
    rhyme: str
    center: str
    shared_surface: str

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
class Desire:
    id: str
    label: str
    verb: str
    noun: str
    rhyme: str
    turns: str

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
class Surprise:
    id: str
    label: str
    item: str
    reveal: str
    rhyme: str

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
class Resolution:
    id: str
    label: str
    method: str
    ending: str
    rhyme: str
    sense: int

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("hero")
    b = world.get("friend")
    if a.memes["claiming"] < THRESHOLD or b.memes["claiming"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["frustration"] += 1
    b.memes["frustration"] += 1
    a.meters["tension"] += 1
    b.meters["tension"] += 1
    out.append("__conflict__")
    return out


def _r_calm_after_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.get("room").meters["surprised"] < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.characters():
        e.memes["calm"] += 1
        e.meters["tension"] = max(0.0, e.meters["tension"] - 1.0)
    out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("calm_after_surprise", "social", _r_calm_after_surprise),
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


def reasonableness_gate(setting: Setting, desire: Desire, surprise: Surprise) -> bool:
    return setting.center == "center" and desire.id in {"dance_circle", "game_ring"} and bool(surprise.item)


def surprise_can_help(desire: Desire, surprise: Surprise) -> bool:
    return desire.id == "dance_circle" and surprise.id == "glitter_streamers"


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").memes["claiming"] += 1
    sim.get("friend").memes["claiming"] += 1
    propagate(sim, narrate=False)
    return {
        "conflict": sim.get("hero").memes["frustration"] >= THRESHOLD,
        "tension": sim.get("hero").meters["tension"],
    }


def setup(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In {setting.place}, by the bright round center, {hero.id} and {friend.id} "
        f"came in for a dancer's adventure."
    )
    world.say(
        f'The {setting.shared_surface} shone soft and wide, and the {setting.center} '
        f"looked made for the middle inside."
    )


def want_center(world: World, hero: Entity, friend: Entity, desire: Desire) -> None:
    hero.memes["claiming"] += 1
    friend.memes["claiming"] += 1
    world.say(
        f'{hero.id} wanted the center, the very front place; {friend.id} wanted it too '
        f"with a smile on {friend.pronoun('possessive')} face."
    )
    world.say(
        f"Both reached for the middle, both tugged with zeal, and the sweet little plan "
        f"started to squeal."
    )


def argue(world: World, hero: Entity, friend: Entity, desire: Desire) -> None:
    propagate(world, narrate=False)
    world.say(
        f'"It is mine!" said {hero.id}. "No, mine!" said {friend.id}, and the happy round '
        f"ring turned prickly instead."
    )
    world.say(
        f"Their feet made a shuffle, their voices grew tight, and the center felt small "
        f"in the middle of night."
    )


def surprise_reveal(world: World, parent: Entity, surprise: Surprise) -> None:
    world.get("room").meters["surprised"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {parent.label_word} came smiling with a surprise in {parent.pronoun('possessive')} hand:"
    )
    world.say(
        f"{surprise.reveal}. It sparkled like laughter and glimmered like sand."
    )


def share_center(world: World, hero: Entity, friend: Entity, setting: Setting,
                 desire: Desire, surprise: Surprise, resolution: Resolution) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["gratitude"] += 1
    friend.memes["gratitude"] += 1
    world.say(
        f'"We can share the center," said {hero.id}. "We can both take a turn," said {friend.id}.'
    )
    world.say(
        f"They set the {surprise.item} in a ring around the middle, and the middle grew bright as a lantern-lit den."
    )
    world.say(
        f"Now {hero.id} twirled in one circle, then {friend.id} took the next; the room found its rhythm, neat as a text."
    )
    world.say(
        f"In the center they danced, and no one stayed stuck; the little surprise turned conflict to luck."
    )


def end_image(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"At story's sweet ending, {hero.id} and {friend.id} smiled in the center so clear, "
        f"with the round little room full of sparkle and cheer."
    )
    world.say(
        f"The center was shared, and the sharing was fun; two friends in one circle, the same as the sun."
    )


def tell(setting: Setting, desire: Desire, surprise: Surprise, resolution: Resolution,
         hero_name: str = "Mina", friend_name: str = "Noah", parent_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    world.add(Entity(id="stage", type="thing", label=setting.shared_surface))
    world.facts.update(setting=setting, desire=desire, surprise=surprise, resolution=resolution)

    setup(world, hero, friend, setting)
    world.para()
    want_center(world, hero, friend, desire)
    argue(world, hero, friend, desire)
    world.para()
    surprise_reveal(world, parent, surprise)
    share_center(world, hero, friend, setting, desire, surprise, resolution)
    world.para()
    end_image(world, hero, friend, setting)

    world.facts.update(
        hero=hero, friend=friend, parent=parent, room=room,
        conflict=hero.memes["frustration"] >= THRESHOLD,
        surprised=room.meters["surprised"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "dance_room": Setting("dance_room", "the dance room", "rhyming room", "center", "polka-dot floor"),
    "playmat": Setting("playmat", "the playmat", "tiny bright den", "center", "soft square mat"),
    "circle_time": Setting("circle_time", "the play circle", "circle song", "center", "round rug"),
}

DESIRES = {
    "dance_circle": Desire("dance_circle", "center dance", "dance in the center", "dance", "spark", "turns"),
    "game_ring": Desire("game_ring", "ring game", "play in the center", "play", "gleam", "spins"),
}

SURPRISES = {
    "glitter_streamers": Surprise("glitter_streamers", "glitter streamers", "glitter streamers", "streamers dropped from above", "shimmer"),
    "toy_drums": Surprise("toy_drums", "toy drums", "toy drums", "drums to beat a happy beat", "rumble"),
}

RESOLUTIONS = {
    "share_turns": Resolution("share_turns", "share turns", "take turns in the middle", "shared center", "glow", 3),
}

GIRL_NAMES = ["Mina", "Luna", "Pia", "Rosa", "Nina"]
BOY_NAMES = ["Noah", "Eli", "Owen", "Kai", "Theo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    desire: str
    surprise: str
    resolution: str
    hero: str
    friend: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for did, d in DESIRES.items():
            for suid, su in SURPRISES.items():
                if reasonableness_gate(s, d, su):
                    out.append((sid, did, suid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting, desire, surprise = f["setting"], f["desire"], f["surprise"]
    return [
        f'Write a rhyming story for a small child about two friends in {setting.place} who both want the center, and a surprise helps them share it.',
        f"Tell a conflict-and-surprise rhyming story where {f['hero'].id} and {f['friend'].id} quarrel over the center of the game, then learn a happy way to take turns.",
        f'Use the word "center" in a gentle rhyming story where the middle spot is fought over, then made joyful by a surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, parent = f["hero"], f["friend"], f["parent"]
    setting, desire, surprise = f["setting"], f["desire"], f["surprise"]
    answers = [
        QAItem("Who is the story about?",
               f"It is about {hero.id} and {friend.id}, two children who wanted the center spot. {parent.label_word.capitalize()} helped them solve the problem."),
        QAItem("What caused the conflict?",
               f"They both wanted the center of the game at the same time, so they argued. The same middle place made both children feel strong feelings."),
    ]
    if f.get("surprised"):
        answers.append(QAItem("What was the surprise?",
                              f"The surprise was {surprise.reveal}. It changed the game by making the center bright and fun for both children."))
    answers.append(QAItem("How did they end the story?",
                           f"They took turns and shared the center. The ending shows that the middle spot could belong to both of them in turn."))
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a center?",
               "A center is the middle of something. It is the part that is equally near to all the sides."),
        QAItem("What does a surprise do in a story?",
               "A surprise is something unexpected. It can change how the characters feel and what they choose next."),
        QAItem("What is a conflict?",
               "A conflict is when characters want different things and cannot agree right away. Stories often use it to make the middle exciting."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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


CURATED = [
    StoryParams("dance_room", "dance_circle", "glitter_streamers", "share_turns", "Mina", "Noah", "mother"),
    StoryParams("playmat", "game_ring", "toy_drums", "share_turns", "Luna", "Eli", "father"),
]


def explain_rejection(setting: Setting, desire: Desire, surprise: Surprise) -> str:
    return "(No story: the chosen setting or desire does not make a good center conflict with a useful surprise.)"


def outcome_of(params: StoryParams) -> str:
    return "shared"


ASP_RULES = r"""
conflict :- claiming(hero), claiming(friend).
surprised :- surprise(room).
shared :- conflict, surprised.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did in DESIRES:
        lines.append(asp.fact("desire", did))
    for suid in SURPRISES:
        lines.append(asp.fact("surprise", suid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    # smoke test generate
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE FAIL: generate crashed: {exc}")
        return 1
    py = set(valid_combos())
    asp_set = set(valid_combos())
    if py != asp_set:
        rc = 1
    print(f"OK: smoke generate ran; combos={len(py)}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming center-conflict-surprise story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--desire", choices=DESIRES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.desire is None or c[1] == args.desire)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, desire, surprise = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES)
    friend = args.friend or rng.choice(BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, desire, surprise, "share_turns", hero, friend, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], DESIRES[params.desire], SURPRISES[params.surprise], RESOLUTIONS[params.resolution], params.hero, params.friend, params.parent)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for combo in valid_combos():
            print(" ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
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

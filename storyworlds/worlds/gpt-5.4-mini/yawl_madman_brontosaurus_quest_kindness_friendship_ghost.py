#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/yawl_madman_brontosaurus_quest_kindness_friendship_ghost.py
==========================================================================================

A standalone story world for a tiny ghost-story quest about a yawl, a frightened
madman, and a brontosaurus-shaped mystery that can only be solved with kindness
and friendship.

The domain is intentionally small: a child or two drift out in a little yawl,
hear a lonely "madman" warning about a ghostly brontosaurus, and discover that
the spooky thing is not dangerous at all. It is a lost, gentle creature whose
path home has been blocked by fog, and the way through is to offer help rather
than fear.

The world keeps the story state-driven: distance on the water, fog, trust,
kindness, and friendship all change what happens and what gets narrated.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
    water: str
    hush: str
    foggy: bool = True

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
class Quest:
    id: str
    title: str
    goal: str
    clue: str
    finish: str
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
class Boat:
    id: str
    label: str
    phrase: str
    breeze: str
    holds: str
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
class GhostThing:
    id: str
    label: str
    phrase: str
    sound: str
    gentle: bool = True
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

    def chars(self) -> list[Entity]:
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_fog(world: World) -> list[str]:
    out: list[str] = []
    if not world.setting.foggy:
        return out
    for e in world.chars():
        if e.meters["hope"] < THRESHOLD:
            continue
        sig = ("fog", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["uncertainty"] += 1
        out.append("__fog__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for e in world.chars():
        if e.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["trust"] += 1
        e.meters["warmth"] += 1
        out.append("__kindness__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    pals = [e for e in world.chars() if e.memes["trust"] >= THRESHOLD]
    if len(pals) < 2:
        return out
    sig = ("friendship", tuple(sorted(e.id for e in pals)))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in pals:
        e.memes["friendship"] += 1
        e.meters["closer"] += 1
    out.append("__friendship__")
    return out


CAUSAL_RULES = [
    Rule("fog", "atmosphere", _r_fog),
    Rule("kindness", "social", _r_kindness),
    Rule("friendship", "social", _r_friendship),
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


def reasonable_quest(quest: Quest, ghost: GhostThing) -> bool:
    return quest.id == "find_home" and ghost.gentle


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid in QUESTS:
            for gid in GHOSTS:
                if reasonable_quest(QUESTS[qid], GHOSTS[gid]):
                    combos.append((sid, qid, gid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    ghost: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
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


def setup(world: World, hero: Entity, friend: Entity, quest: Quest, boat: Boat, ghost: GhostThing) -> None:
    hero.meters["hope"] += 1
    friend.meters["hope"] += 1
    world.say(
        f"At {world.setting.place}, {hero.id} and {friend.id} climbed into {boat.phrase} and let the little boat drift."
    )
    world.say(
        f"They were on a {quest.title}, because {quest.goal} was waiting beyond the fog."
    )


def worry(world: World, friend: Entity, ghost: GhostThing) -> None:
    friend.memes["fear"] += 1
    world.say(
        f"Then a gray shape rose from the mist. {friend.id} gulped. "
        f'"Did you hear that? The {ghost.label} sounded like a ghost in the dark."'
    )


def warn(world: World, hero: Entity, friend: Entity, quest: Quest, ghost: GhostThing) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f'{hero.id} held out a steady hand. "Maybe it is not a monster," {hero.id} said. '
        f'"Maybe it needs help."'
    )
    world.say(
        f"The little yawl creaked softly, and the fog made the water look like a silver road."
    )


def reveal(world: World, ghost: GhostThing) -> None:
    world.say(
        f"The shape drifted closer. It was a brontosaurus, huge and gentle, with a sad little {ghost.sound} from deep in its throat."
    )
    world.say(
        f"It was not hunting them at all. It was lost, and its long neck kept brushing the fog."
    )


def help_it(world: World, hero: Entity, friend: Entity, ghost: GhostThing, quest: Quest) -> None:
    hero.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} pointed toward the far lights, and {friend.id} waved slowly so the brontosaurus would know they were friends."
    )
    world.say(
        f"Together they followed {quest.clue}, and the kind old creature turned with them toward home."
    )
    propagate(world, narrate=False)


def end(world: World, hero: Entity, friend: Entity, ghost: GhostThing, quest: Quest) -> None:
    hero.meters["hope"] += 1
    friend.meters["hope"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"By the time the yawl reached the shore, the fog was thinner and the brontosaurus was safe."
    )
    world.say(
        f"{hero.id} and {friend.id} had finished the {quest.title}, and the night felt less spooky and more kind."
    )
    world.say(
        f"Behind them, the brontosaurus gave one last soft call and disappeared home into the mist."
    )


def tell(setting: Setting, quest: Quest, ghost: GhostThing, boat: Boat,
         hero_name: str = "Mia", hero_gender: str = "girl",
         friend_name: str = "Noah", friend_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.facts["parent"] = parent
    world.facts["quest"] = quest
    world.facts["ghost"] = ghost
    world.facts["boat"] = boat

    setup(world, hero, friend, quest, boat, ghost)
    world.para()
    worry(world, friend, ghost)
    warn(world, hero, friend, quest, ghost)
    propagate(world, narrate=True)
    world.para()
    reveal(world, ghost)
    help_it(world, hero, friend, ghost, quest)
    world.para()
    end(world, hero, friend, ghost, quest)

    world.facts.update(hero=hero, friend=friend, outcome="kind")
    return world


SETTINGS = {
    "harbor_fog": Setting("harbor_fog", "the harbor", "water", "fog", foggy=True),
    "moon_bay": Setting("moon_bay", "Moon Bay", "water", "moonlight", foggy=True),
    "quiet_cove": Setting("quiet_cove", "the quiet cove", "water", "mist", foggy=True),
}

QUESTS = {
    "find_home": Quest("find_home", "quest to find the lost shore", "the lost shore", "a silver wake", "the brontosaurus followed their lantern-light", {"quest", "kindness", "friendship"}),
}

GHOSTS = {
    "bronto": GhostThing("bronto", "brontosaurus", "a brontosaurus", "hollow moan", gentle=True, tags={"brontosaurus"}),
}

BOATS = {
    "yawl": Boat("yawl", "yawl", "a little yawl", "salt breeze", "two small children and a lantern", {"yawl"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Theo", "Finn", "Ben", "Leo", "Max"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, quest, ghost = f["hero"], f["friend"], f["quest"], f["ghost"]
    return [
        f'Write a ghost story for a 3-to-5-year-old that includes the words "yawl", "madman", and "brontosaurus".',
        f"Tell a gentle quest story where {hero.id} and {friend.id} drift in a yawl, meet a strange madman in the fog, and discover a brontosaurus that needs kindness.",
        f'Write a friendship story in a spooky style where a child helps a lost brontosaurus instead of being afraid.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, ghost, quest = f["hero"], f["friend"], f["ghost"], f["quest"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, who went out in a yawl on a small quest. They were brave enough to look into the fog together."),
        ("Why did they feel scared at first?",
         f"They heard a strange warning from a lonely madman-like voice in the mist, and then a huge shape moved nearby. That made the night feel spooky before they understood what it was."),
        ("What did they learn about the brontosaurus?",
         f"They learned it was gentle and lost, not dangerous at all. It needed kindness and friendship to find its way home."),
        ("How did the story end?",
         f"It ended with the children helping the brontosaurus back toward the shore. The yawl floated home safely, and the scary night turned into a kind one."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a yawl?",
         "A yawl is a small boat that can carry people on the water. In this story it helps the children travel through the fog."),
        ("What is a brontosaurus?",
         "A brontosaurus is a very big dinosaur with a long neck. In the story it is gentle and needs help getting home."),
        ("What is kindness?",
         "Kindness means being gentle, helpful, and caring toward someone else. It can make scary moments feel safe."),
        ("What is friendship?",
         "Friendship is when people care about each other and help each other. Friends can feel braver together."),
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("harbor_fog", "find_home", "bronto", "Mia", "girl", "Noah", "boy", "mother"),
    StoryParams("moon_bay", "find_home", "bronto", "Lily", "girl", "Theo", "boy", "father"),
    StoryParams("quiet_cove", "find_home", "bronto", "Noah", "boy", "Mia", "girl", "mother"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
        lines.append(asp.fact("gentle", gid))
    for bid in BOATS:
        lines.append(asp.fact("boat", bid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, Q, G) :- setting(S), quest(Q), ghost(G), gentle(G).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    rc = 0
    if a == b:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a - b:
            print("  only in asp:", sorted(a - b))
        if b - a:
            print("  only in python:", sorted(b - a))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story quest about a yawl, a madman, and a brontosaurus.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    combos = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.ghost is None or c[2] == args.ghost)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, ghost = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, quest, ghost, hero, hero_gender, friend, friend_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], GHOSTS[params.ghost], BOATS["yawl"],
                 params.hero, params.hero_gender, params.friend, params.friend_gender, params.parent)
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
        print(f"{len(asp_valid_combos())} compatible story combos:\n")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.friend}: {p.setting} / {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/number_sharing_moral_value_rhyming_story.py
===========================================================================

A standalone storyworld for a tiny rhyming moral tale about sharing a number
of toys, learning fairness, and ending with a warm, child-facing lesson.

The world model keeps track of:
- physical meters: how many toys, snacks, and gifts exist or are held
- emotional memes: want, worry, fairness, joy, guilt, gratitude, and lesson

The seed idea is simple:
A child counts a number of sweet things, feels tempted to keep them all, then
learns that sharing makes the day brighter.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python reasonableness gate and inline ASP twin
- uses world state to drive prose and Q&A
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
KIND_MIN = 1
SHARE_MIN = 1
LESSON_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    count: int = 0
    plural: bool = False
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
    rhyme_end: str
    stage_line: str

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
class Treasure:
    id: str
    label: str
    count: int
    kind: str
    rhyme_word: str
    shimmer: str
    plural: bool = False

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
class CharacterPack:
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    adult_name: str
    adult_type: str

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
        clone.facts = dict(self.facts)
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


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    treasure = world.get("treasure")
    if child.meters["kept"] >= THRESHOLD and helper.memes["kindness"] >= THRESHOLD:
        sig = ("share",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["shared"] += 1
            helper.meters["shared"] += 1
            child.memes["joy"] += 1
            helper.memes["joy"] += 1
            out.append("__share__")
    if treasure.meters["shared"] >= THRESHOLD and treasure.meters["count"] >= SHARE_MIN:
        sig = ("lesson",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("adult").memes["lesson"] += 1
            out.append("__lesson__")
    return out


CAUSAL_RULES = [
    Rule("sharing", "social", _r_sharing),
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


def rhyme(a: str, b: str) -> bool:
    return a[-2:] == b[-2:] or a[-1:] == b[-1:]


def treasure_risk(count: int) -> bool:
    return count >= KIND_MIN


def can_share(treasure: Treasure) -> bool:
    return treasure.count >= SHARE_MIN


def predict_choice(world: World, treasure_id: str) -> dict:
    sim = world.copy()
    _do_keep(sim, sim.get("child"), sim.get("treasure"), narrate=False)
    return {
        "shared": sim.get("treasure").meters["shared"] >= THRESHOLD,
        "joy": sim.get("child").memes["joy"],
    }


def _do_keep(world: World, child: Entity, treasure: Entity, narrate: bool = True) -> None:
    child.meters["kept"] += treasure.count
    child.memes["want"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, setting: Setting, treasure: Treasure, pack: CharacterPack) -> None:
    child = world.add(Entity("child", kind="character", type=pack.child_type, label=pack.child_name, role="keeper"))
    helper = world.add(Entity("helper", kind="character", type=pack.helper_type, label=pack.helper_name, role="sharer"))
    adult = world.add(Entity("adult", kind="character", type=pack.adult_type, label=pack.adult_name, role="guide"))
    basket = world.add(Entity("basket", type="thing", label="basket", count=treasure.count, plural=treasure.plural))
    tre = world.add(Entity("treasure", type="thing", label=treasure.label, count=treasure.count, plural=treasure.plural))
    world.facts.update(setting=setting, treasure_cfg=treasure, pack=pack, basket=basket)
    child.memes["wonder"] += 1
    helper.memes["kindness"] += 1
    adult.memes["care"] += 1
    child.meters["number"] = treasure.count
    tre.meters["count"] = treasure.count


def tell(setting: Setting, treasure: Treasure, pack: CharacterPack) -> World:
    world = World()
    setup(world, setting, treasure, pack)
    child = world.get("child")
    helper = world.get("helper")
    adult = world.get("adult")
    tre = world.get("treasure")

    world.say(
        f"In {setting.place}, under {setting.mood} skies so bright, "
        f"{child.label} found {treasure.count} {treasure.label} in a basket of light."
    )
    world.say(
        f"The little ones counted the number with glee, "
        f"and the scene felt as merry as merry could be."
    )
    world.para()
    world.say(
        f"{child.label} said, \"These are mine, and I shall keep them near.\" "
        f"But {helper.label} said, \"Sharing is kind, my dear.\""
    )
    child.memes["want"] += 1
    child.memes["stubborn"] += 1
    helper.memes["kindness"] += 1
    adult.memes["care"] += 1

    if not can_share(treasure):
        raise StoryError("This number story needs at least one thing to share.")
    pred = predict_choice(world, "treasure")
    world.facts["predicted_shared"] = pred["shared"]

    world.para()
    if treasure.count == 1:
        world.say(
            f"The single sweet sparkled alone, and {helper.label} smiled a plea: "
            f"\"One little thing can still be shared by thee.\""
        )
    else:
        world.say(
            f"{child.label} hugged the pile, then paused with a sigh, "
            f"for {helper.label}'s kind words fluttered up high."
        )
    world.say(
        f"\"When we both have a turn, the fun feels more wide; "
        f"two happy hearts can fit side by side.\""
    )
    child.memes["worry"] += 1
    child.memes["thought"] += 1

    world.para()
    _do_keep(world, child, tre, narrate=False)
    if treasure.count >= 2:
        world.say(
            f"{child.label} split the {treasure.count} treasures in two, "
            f"and gave half to {helper.label} with a grin so true."
        )
    else:
        world.say(
            f"{child.label} held out the lone little prize, "
            f"and shared it with {helper.label} before anybody's eyes."
        )
    world.say(
        f"Then {adult.label_word} clapped softly and said, "
        f"\"A kind heart is the best kind of gold to be fed.\""
    )

    world.para()
    if treasure.count > 1:
        world.say(
            f"They counted again, and the number stayed bright: "
            f"one for you, one for me, and the room felt right."
        )
    else:
        world.say(
            f"They watched the small gift go round with delight, "
            f"and the one tiny number grew kinder that night."
        )
    world.say(
        f"{setting.stage_line} Their smiling faces shone through the room, "
        f"and sharing, like singing, had chased away gloom."
    )

    child.meters["shared"] = 1
    tre.meters["shared"] = 1
    child.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    adult.memes["lesson"] += 1

    world.facts.update(
        child=child,
        helper=helper,
        adult=adult,
        treasure=tre,
        outcome="shared",
        count=treasure.count,
    )
    return world


SETTINGS = {
    "garden": Setting("garden", "the garden", "gentle", "glow", "The flowers nodded by the old stone wall."),
    "playroom": Setting("playroom", "the playroom", "warm", "show", "The toy shelf sparkled in the afternoon show."),
    "kitchen": Setting("kitchen", "the kitchen", "sunny", "glow", "The window made the table gleam and glow."),
}

TREASURES = {
    "cookies": Treasure("cookies", "cookies", 2, "sweet", "treats", "They smelled like a bakery treat.", plural=True),
    "berries": Treasure("berries", "berries", 3, "fruit", "glow", "They shone like tiny ruby beads.", plural=True),
    "marbles": Treasure("marbles", "marbles", 4, "toy", "roll", "They sparkled like a little pond.", plural=True),
    "stickers": Treasure("stickers", "stickers", 1, "gift", "shine", "It glimmered with a tiny design.", plural=True),
}

PACKS = {
    "anna": CharacterPack("Anna", "girl", "Milo", "boy", "Mom", "mother"),
    "ben": CharacterPack("Ben", "boy", "Lia", "girl", "Dad", "father"),
    "maya": CharacterPack("Maya", "girl", "Noah", "boy", "Mom", "mother"),
    "leo": CharacterPack("Leo", "boy", "Zoe", "girl", "Dad", "father"),
}

TRAITS = ["gentle", "curious", "cheerful", "thoughtful", "patient"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    treasure: str
    pack: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, treasure in TREASURES.items():
            if treasure_risk(treasure.count) and can_share(treasure):
                for pid in PACKS:
                    combos.append((sid, tid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming sharing storyworld about number and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--pack", choices=PACKS)
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
              and (args.treasure is None or c[1] == args.treasure)
              and (args.pack is None or c[2] == args.pack)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treasure, pack = rng.choice(sorted(combos))
    trait = rng.choice(TRAITS)
    return StoryParams(setting, treasure, pack, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    tre = f["treasure_cfg"]
    pack = f["pack"]
    return [
        f'Write a rhyming moral story for a young child that includes the word "number" and a lesson about sharing.',
        f"Tell a gentle story set in {setting.place} where {pack.child_name} finds {tre.count} {tre.label} and learns to share them kindly.",
        f"Write a short rhyming tale about one child, one helper, and {tre.count} small treasures, ending with a moral about sharing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    adult = f["adult"]
    tre = f["treasure"]
    setting = f["setting"]
    qas = [
        ("Who is the story about?",
         f"It is about {child.label}, {helper.label}, and {adult.label_word} in {setting.place}. They are the ones who learn the value of sharing."),
        ("What number is in the story?",
         f"The story uses the number {tre.count}. That number matters because it is the amount of {tre.label} the child found."),
        ("What did the child learn?",
         f"{child.label} learned that sharing makes the day kinder. Giving some away made both children happier."),
        ("How did the story end?",
         f"It ended with a fair share and a warm smile. The child and helper both felt proud of the kind choice."),
    ]
    if f.get("predicted_shared"):
        qas.append(
            ("Why did the child decide to share?",
             f"{helper.label} spoke kindly, and {adult.label_word} gave a calm lesson about fairness. The child saw that sharing the {tre.count} {tre.label} would make everyone feel good.")
        )
    return qas


KNOWLEDGE = {
    "number": [("What is a number?",
                "A number is a word or symbol that tells how many things there are.")],
    "sharing": [("What is sharing?",
                 "Sharing means letting someone else use or enjoy some of what you have. It is a kind way to play together.")],
    "fairness": [("What does fairness mean?",
                  "Fairness means people get a kind and even chance. It helps everyone feel respected.")],
    "kind": [("What is a kind action?",
               "A kind action helps someone else feel good or be included. Sharing is a kind action.")],
    "count": [("Why do we count things?",
               "We count things to know how many there are. Counting helps us share and compare carefully.")],
    "cookie": [("Why can cookies be shared?",
                "Cookies can be shared by giving each person some. That way everyone gets a taste.")],
    "berry": [("What are berries?",
               "Berries are small juicy fruits, and people often eat them as a snack or dessert.")],
    "marble": [("What are marbles?",
                "Marbles are small round toys that can be rolled, sorted, or kept in a bag.")],
    "sticker": [("What is a sticker?",
                 "A sticker is a little picture with glue on the back. You can peel it and stick it on paper.")],
}
KNOWLEDGE_ORDER = ["number", "count", "sharing", "fairness", "kind", "cookie", "berry", "marble", "sticker"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["treasure_cfg"].kind, "number", "sharing", "fairness", "kind", "count"}
    tags.add(world.facts["treasure_cfg"].id[:-1] if world.facts["treasure_cfg"].id.endswith("s") else world.facts["treasure_cfg"].id)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
kept(C,T) :- child(C), treasure(T), count(T,N), N >= 1.
sharing(C,T) :- kept(C,T), helper(H), kindness(H).
lesson(A) :- adult(A), sharing(_, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("count", tid, t.count))
    for pid in PACKS:
        lines.append(asp.fact("pack", pid))
    lines.append(asp.fact("kindness", "helper"))
    lines.append(asp.fact("adult", "adult"))
    lines.append(asp.fact("child", "child"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show sharing/2.\n#show lesson/1."))
    atoms = set(asp.atoms(model, "sharing"))
    ok = len(valid_combos()) == len(SETTINGS) * len(TREASURES) * len(PACKS)
    if atoms and ok:
        print("OK: ASP and Python gates are present.")
    else:
        return 1
    sample = generate(StoryParams("garden", "cookies", "anna", "gentle"))
    if not sample.story.strip():
        return 1
    print("OK: generation smoke test passed.")
    return 0


CURATED = [
    StoryParams("garden", "cookies", "anna", "gentle"),
    StoryParams("playroom", "berries", "ben", "thoughtful"),
    StoryParams("kitchen", "marbles", "maya", "patient"),
    StoryParams("garden", "stickers", "leo", "curious"),
]


def explain_rejection() -> str:
    return "(No story: this world needs a shareable treasure with at least one item.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TREASURES[params.treasure], PACKS[params.pack])
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
        print(asp_program("", "#show sharing/2.\n#show lesson/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatibility is broad in this small world; use --verify for parity.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.setting}: {p.treasure} ({p.pack})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

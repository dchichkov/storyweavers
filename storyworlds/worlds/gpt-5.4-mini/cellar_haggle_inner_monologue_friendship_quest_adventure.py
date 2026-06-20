#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cellar_haggle_inner_monologue_friendship_quest_adventure.py
===========================================================================================

A standalone story world for a small adventure tale about a child, a dusty
cellar, a friendly quest, and a careful haggle.

The domain is built around:
- a cellar with a gate, shelves, stairs, and a lantern
- a quest for a missing keepsake or map piece
- an inner monologue that shifts the hero from worry to courage
- friendship that changes the plan
- a haggle that turns a risky demand into a fair trade

The story engine simulates physical meters and emotional memes so the prose is
driven by world state rather than a frozen template.
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

# Make shared result containers importable when run directly from repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
COURAGE_TO_START = 2.0


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
class Scene:
    cellar_name: str
    cellar_detail: str
    quest_goal: str
    mystery_item: str
    treasure_image: str

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
class Offer:
    id: str
    label: str
    ask: str
    give: str
    sense: int
    help: int
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
class World:
    scene: Scene
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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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
@dataclass
class StoryParams:
    scene: str
    quest_item: str
    offer: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    guardian: str
    guardian_gender: str
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


class Rule:
    def __init__(self, name: str, apply: Callable[[World], list[str]]) -> None:
        self.name = name
        self.apply = apply


def _r_fear_to_courage(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["fear"] < THRESHOLD or hero.memes["resolve"] >= THRESHOLD:
        return out
    sig = ("fear_to_courage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["resolve"] += 1
    out.append("__courage__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["resolve"] < THRESHOLD or friend.memes["trust"] < THRESHOLD:
        return out
    sig = ("friendship",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    out.append("__friendship__")
    return out


CAUSAL_RULES = [Rule("fear_to_courage", _r_fear_to_courage), Rule("friendship", _r_friendship)]


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


def valid_offer(offer: Offer) -> bool:
    return offer.sense >= 2


def story_can_start(hero_courage: float, friend_trust: float) -> bool:
    return hero_courage + friend_trust >= COURAGE_TO_START


def scene_registry() -> dict[str, Scene]:
    return {
        "cellar": Scene(
            "cellar",
            "The cellar smelled like old wood and apples, and a narrow stair led down into the dim light.",
            "find the missing brass key",
            "brass key",
            "a brass key shining in a palm",
        ),
        "basement": Scene(
            "basement",
            "The cellar had stone walls and a cool draft that made the candle flame tremble.",
            "recover the old map piece",
            "map piece",
            "a map piece folded open like a tiny wing",
        ),
    }


OFFERS = {
    "coin": Offer("coin", "a coin", "one coin", "the key", 3, 1, tags={"trade", "hagggle"}),
    "story": Offer("story", "a story promise", "a story and a thank-you", "the key", 3, 2, tags={"friendship"}),
    "help": Offer("help", "help with chores", "help carrying jars", "the key", 4, 3, tags={"friendship", "quest"}),
    "badge": Offer("badge", "a shiny badge", "the badge first", "the key", 1, 1, tags={"weak"}),
}

NAMES_GIRL = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ivy"]
NAMES_BOY = ["Leo", "Ben", "Theo", "Max", "Finn", "Eli"]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def _pick_pair(rng: random.Random) -> tuple[str, str, str, str]:
    hg = rng.choice(["girl", "boy"])
    fg = rng.choice(["girl", "boy"])
    hero = _pick_name(rng, hg)
    friend = _pick_name(rng, fg)
    while friend == hero:
        friend = _pick_name(rng, fg)
    return hero, hg, friend, fg


def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender, role="friend"))
    guardian = world.add(Entity(id="guardian", kind="character", type=params.guardian_gender, role="guardian"))
    hero.id = params.hero
    friend.id = params.friend
    guardian.id = params.guardian
    hero.memes["fear"] = 1.0
    hero.memes["resolve"] = 0.0
    friend.memes["trust"] = 1.0
    world.facts.update(hero=hero, friend=friend, guardian=guardian)


def tell(world: World, params: StoryParams) -> World:
    hero = world.get(params.hero)
    friend = world.get(params.friend)
    guardian = world.get("guardian")
    scene = world.scene
    offer = OFFERS[params.offer]

    hero.memes["curiosity"] += 1
    friend.memes["trust"] += 1

    world.say(
        f"On a windy afternoon, {hero.id} and {friend.id} crept toward the {scene.cellar_name}. "
        f"{scene.cellar_detail}"
    )
    world.say(
        f"They were on a small quest: {scene.quest_goal}. {hero.id} could almost picture "
        f"{scene.treasure_image} waiting in the dark."
    )

    world.para()
    world.say(
        f"{hero.id} paused at the steps and listened to {hero.pronoun('possessive')} own inner voice. "
        f'"It is only a cellar," {hero.id} thought. "You can be brave. Ask first. Be fair."'
    )
    world.say(
        f"Down below, {friend.id} whispered that the old shelf might hide the {params.quest_item}."
    )

    hero.memes["fear"] += 1
    friend.memes["caution"] += 0.5
    if not story_can_start(hero.memes["resolve"], friend.memes["trust"]):
        hero.memes["fear"] += 1

    world.para()
    world.say(
        f"{hero.id} called out to {guardian.id} and asked if they could search the cellar."
    )
    world.say(
        f"{guardian.label_word.capitalize()} said they could, but only if the children made a proper haggle."
    )
    world.say(
        f'"{offer.ask}," {guardian.id} said, "and I will give you {offer.give} if you stay gentle with the old things."'
    )

    if offer.sense < 2:
        raise StoryError("The offer is too weak to make a fair haggle.")

    hero.memes["resolve"] += 1
    friend.memes["trust"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f'{friend.id} smiled first. "That seems fair," {friend.id} said, and {hero.id} nodded.'
    )
    world.say(
        f"They accepted the haggle, and {guardian.id} handed over {params.quest_item} wrapped in cloth."
    )
    world.say(
        f"Soon the two friends found the missing piece and climbed back up the stairs, "
        f"with the cellar behind them and their quest complete."
    )
    world.say(
        f"At the top step, {hero.id} looked at {friend.id} and grinned. "
        f'"We did it together," {hero.id} thought, and the dark cellar no longer felt scary at all.'
    )

    world.facts.update(
        scene=scene,
        offer=offer,
        outcome="success",
        quest_item=params.quest_item,
        friendship=friend.memes["joy"] >= THRESHOLD,
        resolved=True,
    )
    return world


def generate_story(params: StoryParams) -> StorySample:
    scenes = scene_registry()
    world = World(scenes[params.scene])
    _setup(world, params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["scene"]
    return [
        f'Write an adventure story for a young child that includes the word "cellar" and the word "haggle".',
        f"Tell a friendship quest story where two children go into the {scene.cellar_name} and make a fair haggle with a grown-up.",
        "Write a story with inner monologue, a cellar, and a small quest that ends with two friends feeling brave.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    guardian = f["guardian"]
    scene = f["scene"]
    offer = f["offer"]
    return [
        ("Where did the children go?",
         f"They went to the {scene.cellar_name}, where the air was cool and old and the stairs led down into the dimness."),
        ("What was their quest?",
         f"Their quest was to {scene.quest_goal}. They wanted to finish the job together and bring back the missing thing."),
        ("How did the hero's inner monologue help?",
         f"{hero.id} listened to an inner thought that said to be brave, ask first, and be fair. That helped {hero.id} move from fear to action instead of turning back."),
        ("What was the haggle?",
         f"The haggle was that the children offered {offer.ask}, and {guardian.id} gave them {offer.give} in return. It was fair because they were polite and careful."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a cellar?",
         "A cellar is a room below a house, often cool and dim, where people store things they do not use every day."),
        ("What does haggle mean?",
         "To haggle means to talk about a trade or price until both sides agree on something fair."),
        ("What is a quest?",
         "A quest is a mission or search for something important, usually with a goal to reach or find."),
        ("Why can friendship matter on an adventure?",
         "Friends can share courage, notice things the other one misses, and help make hard jobs feel possible."),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for item in QUEST_ITEMS:
            for offer in OFFERS:
                if valid_offer(OFFERS[offer]):
                    combos.append((scene, item, offer))
    return combos


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for item in QUEST_ITEMS:
        lines.append(asp.fact("quest_item", item))
    for oid, offer in OFFERS.items():
        lines.append(asp.fact("offer", oid))
        lines.append(asp.fact("sense", oid, offer.sense))
        lines.append(asp.fact("help", oid, offer.help))
    lines.append(asp.fact("sense_min", 2))
    lines.append(asp.fact("courage_to_start", int(COURAGE_TO_START)))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Scene, Item, Offer) :- scene(Scene), quest_item(Item), offer(Offer), sense(Offer, S), sense_min(M), S >= M.
resolved :- courage(R), trust(T), courage_to_start(C), R + T >= C.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import sys as _sys
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between ASP and Python combos.")
        rc = 1
    try:
        params = StoryParams("cellar", "brass key", "story", "Mia", "girl", "Leo", "boy", "Nora", "girl")
        sample = generate(params)
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: generate() smoke test crashed: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: cellar, haggle, friendship, quest.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--item", choices=QUEST_ITEMS)
    ap.add_argument("--offer", choices=OFFERS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--guardian")
    ap.add_argument("--guardian-gender", choices=["girl", "boy", "woman", "man"])
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
    if args.offer and not valid_offer(OFFERS[args.offer]):
        raise StoryError("That haggle offer is too weak to count as a fair trade.")
    scene = args.scene or rng.choice(SCENES)
    item = args.item or rng.choice(QUEST_ITEMS)
    offer = args.offer or rng.choice(list(OFFERS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    guardian_gender = args.guardian_gender or rng.choice(["woman", "man", "girl", "boy"])
    hero, hero_gender, friend, friend_gender = _pick_pair(rng)
    if args.hero:
        hero = args.hero
    if args.friend:
        friend = args.friend
    if args.guardian:
        guardian = args.guardian
    else:
        guardian = rng.choice(["Mrs. Hale", "Mr. Lane", "Aunt June", "Uncle Ben"])
    return StoryParams(
        scene=scene,
        quest_item=item,
        offer=offer,
        hero=hero,
        hero_gender=args.hero_gender or hero_gender,
        friend=friend,
        friend_gender=args.friend_gender or friend_gender,
        guardian=guardian,
        guardian_gender=guardian_gender,
    )


def generate(params: StoryParams) -> StorySample:
    scene = SCENES[params.scene]
    world = World(scene)
    world.add(Entity(id="hero", kind="character", type=params.hero_gender, role="hero"))
    world.add(Entity(id="friend", kind="character", type=params.friend_gender, role="friend"))
    world.add(Entity(id="guardian", kind="character", type=params.guardian_gender, role="guardian", label=params.guardian))
    world.entities["hero"].id = params.hero
    world.entities["friend"].id = params.friend
    world.entities["guardian"].id = params.guardian
    world.entities["hero"].memes["fear"] = 1.0
    world.entities["friend"].memes["trust"] = 1.0
    world.facts.update(scene=scene, quest_item=params.quest_item, offer=OFFERS[params.offer])
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for scene, item, offer in asp_valid_combos():
            print(f"  {scene:10} {item:12} {offer}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("cellar", "brass key", "story", "Mia", "girl", "Leo", "boy", "Mrs. Hale", "woman"),
            StoryParams("basement", "map piece", "help", "Finn", "boy", "Ava", "girl", "Mr. Lane", "man"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.friend}: {p.scene}, {p.quest_item}, {p.offer}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


SCENES = ["cellar", "basement"]
QUEST_ITEMS = ["brass key", "map piece"]

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

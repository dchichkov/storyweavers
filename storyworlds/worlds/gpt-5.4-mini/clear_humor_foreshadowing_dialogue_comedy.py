#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clear_humor_foreshadowing_dialogue_comedy.py
=============================================================================

A small standalone storyworld for a comedy tale about a child, a clear container,
and a surprise that is not nearly as secret as the child thinks.

Domain sketch
-------------
A child wants to hide a snack or small prize in a clear jar/bag/box. Because the
container is transparent, the other child or grown-up can already see the whole
plan. The story uses:
- clear physical state as the key setup,
- humorous misdirection,
- foreshadowing through obvious clues,
- dialogue-driven turn,
- a cheerful ending image that proves what changed.

The world keeps track of objects, visibility, surprise-level, and the emotional
effect of being caught out. The story is not a frozen paragraph; simulated state
drives the prose.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/clear_humor_foreshadowing_dialogue_comedy.py
    python storyworlds/worlds/gpt-5.4-mini/clear_humor_foreshadowing_dialogue_comedy.py --all
    python storyworlds/worlds/gpt-5.4-mini/clear_humor_foreshadowing_dialogue_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/clear_humor_foreshadowing_dialogue_comedy.py --verify
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
    transparent: bool = False
    visible_contents: bool = False
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
class ContainerKind:
    id: str
    label: str
    phrase: str
    transparent: bool
    holds: str
    tells_on_itself: bool
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
class Prize:
    id: str
    label: str
    phrase: str
    surprise: str
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
class Reaction:
    id: str
    sense: int
    text: str
    laugh: str
    fix: str
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


def _r_visible_clue(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if not ent.transparent:
            continue
        if ent.meters["stuffed"] < THRESHOLD:
            continue
        sig = ("visible", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.kind == "character":
                kid.memes["suspicion"] += 1
        out.append("__clue__")
    return out


def _r_embarrassment(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("reveal") and world.facts.get("caught"):
        for kid in list(world.entities.values()):
            if kid.kind == "character":
                kid.memes["embarrassment"] += 1
        out.append("__embarrassment__")
    return out


CAUSAL_RULES = [Rule("visible_clue", "social", _r_visible_clue), Rule("embarrassment", "social", _r_embarrassment)]


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


def predict_reveal(world: World, container_id: str) -> bool:
    sim = world.copy()
    sim.get(container_id).meters["stuffed"] += 1
    propagate(sim, narrate=False)
    return any(e.memes["suspicion"] >= THRESHOLD for e in sim.entities.values() if e.kind == "character")


def world_contains_clear(container: ContainerKind) -> bool:
    return container.transparent


def sensible_reactions() -> list[Reaction]:
    return [r for r in REACTIONS.values() if r.sense >= 2]


def reaction_is_reasonable(container: ContainerKind, prize: Prize) -> bool:
    return container.transparent and prize.id in {"cookie", "rock", "feather", "note"}


def tell(container: ContainerKind, prize: Prize, reaction: Reaction, hero_name: str,
         hero_gender: str, friend_name: str, friend_gender: str, parent_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="instigator", traits=["sneaky"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="cautioner", traits=["sharp-eyed"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    jar = world.add(Entity(id="container", kind="thing", type="container", label=container.label,
                           transparent=container.transparent, visible_contents=container.transparent,
                           attrs={"phrase": container.phrase}))
    stash = world.add(Entity(id="prize", kind="thing", type="prize", label=prize.label, attrs={"phrase": prize.phrase}))
    hero.memes["hope"] = 1.0
    friend.memes["foreshadowing"] = 1.0

    world.say(
        f"One afternoon, {hero_name} and {friend_name} were making a tiny plan in the kitchen. "
        f"{hero_name} pointed at {container.phrase} and whispered, \"Perfect for a secret.\""
    )
    world.say(
        f"{friend_name} blinked at the clear sides. \"Secret?\" {friend_name} said. "
        f"\"That thing is so clear it might as well be wearing a window.\""
    )
    world.say(
        f"{hero_name} grinned and tucked {prize.phrase} inside the {container.label} anyway. "
        f"At once, the whole plan looked less like a secret and more like a joke."
    )

    world.para()
    if predict_reveal(world, jar.id):
        world.say(
            f"{friend_name} leaned closer and squinted. \"I think your secret is waving at us,\" "
            f"{friend_name} said."
        )
        world.say(
            f"\"It is not waving,\" {hero_name} said. \"It is being mysterious.\""
        )
        world.say(
            f"\"Then why can I see it so well?\" {friend_name} asked."
        )
        world.say(
            f"{hero_name} looked at the clear container, then at the prize, then at {parent.label_word}. "
            f"\"Oh,\" {hero_name} said. \"Right. Very invisible. Great job, me.\""
        )
        jar.meters["stuffed"] += 1
        propagate(world, narrate=False)
        world.facts["caught"] = True
        world.say(
            f"{parent.label_word.capitalize()} laughed so hard {parent.pronoun()} had to hold the counter. "
            f"\"Next time,\" {parent.pronoun()} said, \"pick a box that does not announce itself.\""
        )
        world.say(
            f"Then {parent.label_word.capitalize()} handed over a paper bag and a blue marker. "
            f"\"Now the surprise can actually hide,\" {parent.pronoun()} said."
        )
        stash.meters["moved"] += 1
        jar.transparent = False
        world.say(
            f"{hero_name} moved the {prize.label} into the paper bag, and this time the bag kept its mouth shut."
        )
    else:
        world.say(f"Nobody noticed the plan, which was almost disappointing.")
        world.say(f"{parent.label_word.capitalize()} still smiled and said, \"A clear container is honest, if not subtle.\"")
        world.facts["caught"] = False

    world.para()
    if reaction.sense >= 2:
        world.say(
            f"Later, {friend_name} pointed at the paper bag and said, \"That one is better.\" "
            f"{hero_name} nodded. \"Yes,\" {hero_name} said, \"a sneaky plan should probably stop shouting.\""
        )
        world.say(
            f"{parent.label_word.capitalize()} chuckled and lifted the bag. \"Now this is a proper mystery,\" "
            f"{parent.pronoun()} said."
        )
        world.say(
            f"The clear container stayed on the counter, empty and innocent, while the real surprise rested in the bag."
        )
        world.facts["reveal"] = True
    else:
        world.say(f"{parent.label_word.capitalize()} tried a different idea, but it was too silly to work well.")
        world.say(f"The kitchen remained cluttered and nobody learned much, which was not very funny at all.")
        world.facts["reveal"] = False

    world.facts.update(hero=hero, friend=friend, parent=parent, container=jar, prize=stash,
                       container_cfg=container, prize_cfg=prize, reaction=reaction)
    return world


CONTAINERS = {
    "jar": ContainerKind("jar", "clear jar", "a clear jar", True, "holds snacks", True, {"clear"}),
    "box": ContainerKind("box", "clear box", "a clear box", True, "holds tiny prizes", True, {"clear"}),
    "bag": ContainerKind("bag", "clear bag", "a clear bag", True, "holds a surprise", True, {"clear"}),
    "tin": ContainerKind("tin", "painted tin", "a painted tin", False, "holds cookies", False, {"opaque"}),
}

PRIZES = {
    "cookie": Prize("cookie", "cookie", "a cookie", "crumbly", {"snack"}),
    "rock": Prize("rock", "shiny rock", "a shiny rock", "sparkly", {"trinket"}),
    "feather": Prize("feather", "feather", "a feather", "fluffy", {"trinket"}),
    "note": Prize("note", "folded note", "a folded note", "secret", {"paper"}),
}

REACTIONS = {
    "laugh": Reaction("laugh", 3,
                      "laughed and called the secret the least secret secret ever seen",
                      "laughed until the spoons rattled",
                      "suggested a better hiding place",
                      {"humor", "dialogue"}),
    "bag": Reaction("bag", 3,
                    "picked a paper bag and tucked the surprise inside",
                    "smiled and stopped the giggles",
                    "swapped the clear container for an opaque one",
                    {"fix", "dialogue"}),
    "peek": Reaction("peek", 2,
                     "peeked, snorted, and said the jar was basically a glass announcer",
                     "grinned at the obvious clue",
                     "decided to keep the clear container anyway",
                     {"humor"}),
    "silly": Reaction("silly", 1,
                      "made a silly face and did not really fix anything",
                      "laughed, but the problem stayed put",
                      "shrugged and hoped for the best",
                      {"weak"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Zoe", "Ava", "Pia"]
BOY_NAMES = ["Finn", "Theo", "Noah", "Ben", "Leo", "Max"]


@dataclass
@dataclass
class StoryParams:
    container: str
    prize: str
    reaction: str
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for c in CONTAINERS.values():
        for p in PRIZES.values():
            if reaction_is_reasonable(c, p):
                out.append((c.id, p.id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with clear clues, jokes, and dialogue.")
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--reaction", choices=REACTIONS)
    ap.add_argument("--name")
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
    if args.container and args.prize:
        if not reaction_is_reasonable(CONTAINERS[args.container], PRIZES[args.prize]):
            raise StoryError("No story: the clear rule only works when the prize can plausibly be hidden, and the container is actually clear.")
    combos = [c for c in valid_combos()
              if (args.container is None or c[0] == args.container)
              and (args.prize is None or c[1] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    container, prize = rng.choice(sorted(combos))
    reaction = args.reaction or rng.choice(sorted(r.id for r in sensible_reactions()))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(container, prize, reaction, hero, hero_gender, friend, friend_gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the word "clear" and uses dialogue.',
        f"Tell a comedy story where {f['hero'].id} thinks a {f['container_cfg'].label} can hide a surprise, but the container is clear and the clue is obvious.",
        f"Write a playful foreshadowing story where a clear container gives away the joke before the reveal, and everyone laughs kindly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    container = f["container_cfg"]
    prize = f["prize_cfg"]
    qa = [
        ("What did the child want to do?", f"{hero.id} wanted to hide {prize.phrase} in {container.phrase} and make a surprise."),
        ("Why was that funny?", f"It was funny because the container was clear, so the surprise was not secret at all. The other child could see the plan right away and kept pointing it out."),
        ("What did the friend say?", f"{friend.id} said the clear container was basically a window and asked why the secret was showing so much."),
    ]
    if f.get("caught"):
        qa.append((
            "How did the grown-up react?",
            f"{parent.label_word.capitalize()} laughed, then helped swap the clear container for a better hiding place. The grown-up was amused because the joke had been obvious from the start."
        ))
    if f.get("reveal"):
        qa.append((
            "How did the story end?",
            f"The surprise ended up in a paper bag, and the clear container stayed empty on the counter. That ending proves the problem changed from 'too obvious' to 'properly hidden'."
        ))
    return qa


KNOWLEDGE = {
    "clear": [("What does clear mean?",
               "Clear means you can see through it easily, like glass or clean water.")],
    "transparent": [("What is transparent?",
                    "Transparent means light can pass through and you can see what is behind it.")],
    "dialogue": [("What is dialogue in a story?",
                 "Dialogue is when characters talk to each other using quotation marks.")],
    "joke": [("What makes a joke funny?",
              "A joke is funny when it surprises you in a playful way or says something silly on purpose.")],
    "bag": [("What is a paper bag good for?",
             "A paper bag can hold things and hide them from sight better than a clear container.")],
    "cookie": [("Why do cookies smell nice?",
                "Cookies smell nice because they are warm, sweet, and baked with tasty ingredients.")],
}
KNOWLEDGE_ORDER = ["clear", "transparent", "dialogue", "joke", "bag", "cookie"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["container_cfg"].tags) | set(world.facts["prize_cfg"].tags) | {"dialogue", "joke"}
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
        if e.transparent:
            bits.append("transparent=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def ASP_facts() -> str:
    import asp
    lines = []
    for cid, c in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        if c.transparent:
            lines.append(asp.fact("transparent", cid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
    for rid, r in REACTIONS.items():
        lines.append(asp.fact("reaction", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


ASP_RULES = r"""
clear_story(C, P) :- container(C), prize(P), transparent(C).
reasonable(R) :- reaction(R), sense(R, S), S >= 2.
compatible(C, P) :- clear_story(C, P).
"""


def asp_program(show: str) -> str:
    return f"{ASP_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/1."))
    return sorted(r for (r,) in asp.atoms(model, "reasonable"))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


CURATED = [
    StoryParams("jar", "cookie", "laugh", "Mina", "girl", "Finn", "boy", "mother"),
    StoryParams("box", "rock", "bag", "Theo", "boy", "Lily", "girl", "father"),
    StoryParams("bag", "feather", "peek", "Ava", "girl", "Ben", "boy", "mother"),
]


def explain_rejection(container: ContainerKind, prize: Prize) -> str:
    if not container.transparent:
        return "(No story: this world needs a clear container so the joke and foreshadowing can work.)"
    return "(No story: this combination does not make a clear, funny reveal.)"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    asp_set = set((a, b) for a, b in asp_valid_combos())
    if asp_set == python_set:
        print(f"OK: ASP matches valid_combos() ({len(asp_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatible combos:")
    # smoke test
    try:
        sample = generate(resolve_params(argparse.Namespace(container=None, prize=None, reaction=None, name=None, friend=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generation smoke test crashed: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(CONTAINERS[params.container], PRIZES[params.prize], REACTIONS[params.reaction],
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
        print(asp_program("#show compatible/2.\n#show reasonable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hedge_compete_bravery_tall_tale.py
===================================================================

A standalone story world for a tall-tale-style tiny domain about two children
who compete in a garden challenge by a hedge, where bravery helps one child
face a wobbling task, a wiser helper keeps things fair and safe, and the story
ends with a clear proof of what changed.

Seed words: hedge, compete
Feature: Bravery
Style: Tall Tale
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
BRAVERY_MIN = 3.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Challenge:
    id: str
    name: str
    action: str
    bold: str
    risk: str
    zone: str
    spread: str
    end_image: str
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
class Rivalry:
    id: str
    prize: str
    title: str
    fair_rule: str
    finish_line: str
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
class HelpItem:
    id: str
    label: str
    phrase: str
    use: str
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


def _r_tremble(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["wobble"] < THRESHOLD:
            continue
        sig = ("tremble", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append("__tremble__")
    return out


def _r_cheer(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["brave"] < THRESHOLD:
            continue
        sig = ("cheer", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        out.append("__cheer__")
    return out


CAUSAL_RULES = [Rule("tremble", "social", _r_tremble), Rule("cheer", "social", _r_cheer)]


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


def hedge_at_risk(challenge: Challenge) -> bool:
    return True


def fair_help(item: HelpItem, challenge: Challenge) -> bool:
    return item.id in {"straw_hat", "rope"}


def brave_enough(bravery: float) -> bool:
    return bravery >= BRAVERY_MIN


def setup(world: World, a: Entity, b: Entity, rivalry: Rivalry, challenge: Challenge) -> None:
    a.memes["brave"] = 4.0
    b.memes["brave"] = 2.0
    a.memes["pride"] += 1
    b.memes["hope"] += 1
    world.say(
        f"On a morning so bright it could wake the turtles, {a.id} and {b.id} "
        f"went to the garden hedge to {rivalry.title}."
    )
    world.say(
        f"The prize was {rivalry.prize}, and the rule was simple: {rivalry.fair_rule}."
    )
    world.say(
        f"Beyond the hedge stood {challenge.name}, a dare so tall it seemed to "
        f"touch the clouds with its elbows."
    )


def promise(world: World, b: Entity, challenge: Challenge) -> None:
    b.memes["worry"] += 1
    world.say(
        f"{b.id} peered at the hedge and whispered, "
        f'"That looks mighty wobbly. Maybe we should be careful."'
    )
    world.say(
        f"But the path ahead was long, and the {challenge.action} looked like the kind "
        f"of task a brass band would trumpet about for a week."
    )


def boast(world: World, a: Entity) -> None:
    a.memes["bravery"] += 1
    world.say(
        f"{a.id} puffed out a chest as wide as a pie plate and said, "
        f'"I could {a.attrs["feat"]} faster than a galloping goose!"'
    )


def dare(world: World, a: Entity, challenge: Challenge) -> None:
    a.meters["wobble"] += 1
    a.meters["distance"] += 1
    world.say(
        f"So {a.id} took the dare and began to {challenge.action}. "
        f"{challenge.bold} {challenge.risk}."
    )
    propagate(world, narrate=False)


def warn(world: World, b: Entity, a: Entity, challenge: Challenge, rival: Rivalry) -> None:
    world.say(
        f'{b.id} said, "If the hedge shakes and the gate spins, that could spoil the '
        f'whole {rival.prize} contest."'
    )
    if b.memes["worry"] >= THRESHOLD:
        world.say(
            f'{b.id} pointed at the {challenge.zone} and added, '
            f'"A brave heart is fine, but a brave heart still needs a smart step."'
        )


def helper(world: World, help_item: HelpItem, hero: Entity) -> None:
    hero.memes["brave"] += 1
    hero.meters["wobble"] = 0.0
    world.say(
        f"Then a grown-up brought {help_item.phrase}. {help_item.use}, and it steadied "
        f"the whole merry business."
    )


def finish(world: World, a: Entity, b: Entity, rivalry: Rivalry, challenge: Challenge) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At last, {a.id} got through the hedge line and won {rivalry.prize}. "
        f"{challenge.end_image}"
    )
    world.say(
        f"{b.id} laughed, because the race had turned out fair, and the brave one "
        f"had learned to be brave without being foolish."
    )


def tell(rivalry: Rivalry, challenge: Challenge, help_item: HelpItem,
         hero: str = "Pip", hero_gender: str = "boy",
         friend: str = "Mabel", friend_gender: str = "girl",
         helper_type: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=hero, kind="character", type=hero_gender, role="runner"))
    b = world.add(Entity(id=friend, kind="character", type=friend_gender, role="runner"))
    helper_ent = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper"))

    a.attrs["feat"] = challenge.action
    setup(world, a, b, rivalry, challenge)
    world.para()
    promise(world, b, challenge)
    boast(world, a)
    dare(world, a, challenge)
    warn(world, b, a, challenge, rivalry)
    world.para()
    helper(world, help_item, a)
    finish(world, a, b, rivalry, challenge)

    world.facts.update(
        hero=a, friend=b, helper=helper_ent, rivalry=rivalry, challenge=challenge,
        help_item=help_item, brave=a.memes["brave"] >= BRAVERY_MIN, wobble=a.meters["wobble"]
    )
    return world


CHALLENGES = {
    "hedge_jump": Challenge(
        "hedge_jump",
        "the hedge-top jump",
        "leap over the hedge",
        "the leap was so bold it could make a kite blush",
        "one bad slip could tangle a shoe in the branches",
        "topmost branches",
        "the hedge line",
        "the hedge stood green and grand as a parade float",
        {"hedge", "bravery"},
    ),
    "gate_spin": Challenge(
        "gate_spin",
        "the spinning-gate race",
        "spin through the garden gate",
        "the gate wheeled like a lassoed moon",
        "one wild spin could make a child dizzy as a yo-yo",
        "swinging gate",
        "the gate path",
        "the gate flashed like a silver fish in sunshine",
        {"hedge", "bravery"},
    ),
    "ditch_cross": Challenge(
        "ditch_cross",
        "the ditch-crossing dare",
        "cross the little ditch by the hedge",
        "the ditch yawned like a sleepy canyon",
        "a muddy splash could stop a race in a snap",
        "muddy bank",
        "the ditch side",
        "the ditch shone like a ribbon of brown glass",
        {"hedge", "bravery"},
    ),
}

RIVALRIES = {
    "apple": Rivalry("apple", "the golden apple", "compete for the golden apple",
                     "the first runner must keep the race fair", "golden apple"),
    "ribbon": Rivalry("ribbon", "the blue ribbon", "compete for the blue ribbon",
                      "nobody may shove, and nobody may cheat", "blue ribbon"),
}

HELP = {
    "rope": HelpItem("rope", "a rope", "a rope strong as a fencepost",
                     "It gave the children a steady handhold."),
    "straw_hat": HelpItem("straw_hat", "a straw hat", "a straw hat with a wide brim",
                          "It reminded everybody to slow down and keep balance."),
}

GIRL_NAMES = ["Mabel", "Lily", "Nina", "Clara", "Ruby", "Hazel", "Ivy"]
BOY_NAMES = ["Pip", "Theo", "Sam", "Jasper", "Milo", "Finn", "Evan"]


@dataclass
@dataclass
class StoryParams:
    challenge: str
    rivalry: str
    help_item: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    helper_type: str
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
    return [(c, r, h) for c in CHALLENGES for r in RIVALRIES for h in HELP]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the words "hedge" and "compete" and shows bravery in a playful way.',
        f"Tell a story where {f['hero'].id} and {f['friend'].id} compete near a hedge, one child shows bravery, and a helper gives a safer, steadier way to continue.",
        f'Write a funny, grand-sounding story about a hedge challenge, a fair contest, and a brave child who learns to be bold without being reckless.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["hero"], f["friend"]
    ch, rv, hp = f["challenge"], f["rivalry"], f["help_item"]
    qa = [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, who went to the hedge to {rv.title}."),
        ("What were they trying to do?",
         f"They were trying to {ch.action} and win {rv.prize}. The whole contest was meant to be fair and exciting."),
        ("Why did the friend worry?",
         f"{b.id} worried because {ch.risk}. That meant bravery alone was not enough; they needed a steadier plan too."),
        ("How did bravery matter in the story?",
         f"{a.id} was brave enough to keep going, but not so proud as to ignore help. The brave choice was to accept a safer way and finish the challenge well."),
    ]
    if f["brave"]:
        qa.append((
            "What proved that the brave child changed?",
            f"{a.id} still wanted to compete, but the wobble stopped once {hp.label} came out. "
            f"By the end, {a.id} could finish the hedge challenge without stumbling."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["challenge"].tags) | set(f["rivalry"].tags) | set(f["help_item"].tags)
    out = []
    if "hedge" in tags:
        out.append(("What is a hedge?",
                     "A hedge is a line of bushes or small trees that grows together like a green wall."))
    if "bravery" in tags:
        out.append(("What is bravery?",
                     "Bravery means doing something hard or scary while keeping your heart steady."))
    if "rope" in tags:
        out.append(("What is a rope for?",
                     "A rope can help you hold on, pull things, or keep your balance."))
    if "straw_hat" in tags:
        out.append(("What is a straw hat good for?",
                     "A straw hat can shade your eyes and remind you to move slowly and carefully."))
    out.append(("What does it mean to compete?",
                 "To compete means to take part in a contest and try your best to do well."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hedge_jump", "apple", "rope", "Pip", "boy", "Mabel", "girl", "mother"),
    StoryParams("gate_spin", "ribbon", "straw_hat", "Mabel", "girl", "Pip", "boy", "father"),
]


def explain_rejection() -> str:
    return "(No story: this tall-tale needs a hedge challenge, a fair competition, and a safe help item.)"


ASP_RULES = r"""
valid(C,R,H) :- challenge(C), rivalry(R), help_item(H).
brave(Hero) :- bravery(Hero), brave_level(Hero, L), min_brave(M), L >= M.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    for r in RIVALRIES:
        lines.append(asp.fact("rivalry", r))
    for h in HELP:
        lines.append(asp.fact("help_item", h))
    lines.append(asp.fact("min_brave", BRAVERY_MIN))
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
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    # smoke test ordinary generation
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world about a hedge competition and bravery."
    )
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--rivalry", choices=RIVALRIES)
    ap.add_argument("--help-item", choices=HELP)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["boy", "girl"])
    ap.add_argument("--helper-type", choices=["mother", "father"])
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
    if args.challenge is not None and args.rivalry is not None and args.help_item is not None:
        pass
    combos = [c for c in valid_combos()
              if (args.challenge is None or c[0] == args.challenge)
              and (args.rivalry is None or c[1] == args.rivalry)
              and (args.help_item is None or c[2] == args.help_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    challenge, rivalry, help_item = rng.choice(sorted(combos))
    ch = CHALLENGES[challenge]
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    friend_gender = args.friend_gender or ("girl" if hero_gender == "boy" else "boy")
    hero_pool = BOY_NAMES if hero_gender == "boy" else GIRL_NAMES
    friend_pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
    hero = args.hero or rng.choice(hero_pool)
    friend = args.friend or rng.choice([n for n in friend_pool if n != hero] or friend_pool)
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    return StoryParams(challenge, rivalry, help_item, hero, hero_gender, friend, friend_gender, helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(CHALLENGES[params.challenge], RIVALRIES[params.rivalry], HELP[params.help_item],
                 params.hero, params.hero_gender, params.friend, params.friend_gender,
                 params.helper_type)
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
        print(f"{len(asp_valid_combos())} compatible (challenge, rivalry, help_item) combos:\n")
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
            header = f"### {p.hero} and {p.friend}: {p.challenge} ({p.rivalry})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()

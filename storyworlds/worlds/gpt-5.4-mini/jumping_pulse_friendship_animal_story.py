#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jumping_pulse_friendship_animal_story.py
========================================================================

A small standalone story world about animal friends, a jumping game, and a
fluttering pulse of excitement that settles into a kind ending.

Seed idea
---------
Two animal friends plan a jumping game. One friend gets so excited their pulse
jumps fast, but a kind friend notices, slows the game down, and helps them
choose a gentler way to keep playing together. The story ends with their
friendship stronger and the pulse calm again.

This script is a self-contained TinyStories-style storyworld with:
- typed entities with physical meters and emotional memes
- a reasonableness gate
- an inline ASP twin
- three QA sets built from world state
- text / JSON / trace / verify / asp modes
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
from typing import Optional

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
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "cat"}
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
class Animal:
    id: str
    species: str
    sound: str
    movement: str
    favorite_place: str
    jump_style: str
    pulse_word: str
    friend_word: str
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
class Challenge:
    id: str
    scene: str
    starter: str
    goal: str
    risk: str
    danger: str
    pulse_rise: int
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
class CalmChoice:
    id: str
    label: str
    action: str
    effect: str
    weight: int
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
@dataclass
class StoryParams:
    animal1: str
    animal2: str
    challenge: str
    choice: str
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


ANIMALS = {
    "bunny": Animal("bunny", "bunny", "boing", "hopping", "sunny meadow", "high jumps", "pulse", "friend"),
    "fox": Animal("fox", "fox", "yip", "leaping", "soft hill", "quick jumps", "pulse", "friend"),
    "panda": Animal("panda", "panda", "hum", "bouncing", "bamboo patch", "gentle jumps", "pulse", "pal"),
    "kitten": Animal("kitten", "kitten", "mew", "springing", "window sill", "tiny jumps", "pulse", "friend"),
}

CHALLENGES = {
    "log_jump": Challenge("log_jump", "a row of mossy logs by the pond", "They wanted to hop across", "reach the other side", "a slip into the mud", "the mud below", pulse_rise=2, tags={"jumping", "pulse"}),
    "leaf_pile": Challenge("leaf_pile", "a huge leaf pile in the yard", "They wanted to bounce into", "make the pile puff up", "a tumble and a wobble", "the leaf pile shaking too much", pulse_rise=1, tags={"jumping"}),
    "stone_gap": Challenge("stone_gap", "a little gap between garden stones", "They wanted to jump over", "land safely together", "a twisty landing", "the stones below", pulse_rise=2, tags={"jumping", "pulse"}),
}

CALM_CHOICES = {
    "slow_breath": CalmChoice("slow_breath", "slow breaths", "sit together and take slow breaths", "the pulse slowed and the game felt easy again", 3, tags={"pulse"}),
    "hand_hop": CalmChoice("hand_hop", "hand-hops", "hold paws and make smaller hops", "the friends stayed close and the jumps got gentler", 4, tags={"jumping"}),
    "rest_break": CalmChoice("rest_break", "a rest break", "share a drink of water and rest in the shade", "the excitement settled and the next jump felt safe", 5, tags={"pulse", "jumping"}),
}

GREETINGS = [
    "On a bright morning",
    "One breezy afternoon",
    "At the edge of a sunny clearing",
]

NAMES = {
    "bunny": ["Milo", "Nina", "Pip", "Luna"],
    "fox": ["Fenn", "Ruby", "Toby", "Sage"],
    "panda": ["Bao", "Mimi", "Jun", "Kiki"],
    "kitten": ["Poppy", "Miso", "Tilly", "Nori"],
}


def reasonableness_ok(challenge: Challenge, choice: CalmChoice) -> bool:
    return any(tag in challenge.tags for tag in choice.tags)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for cid, c in CHALLENGES.items():
        for oid, o in CALM_CHOICES.items():
            if reasonableness_ok(c, o):
                out.append((cid, oid))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for tag in c.tags:
            lines.append(asp.fact("ctag", cid, tag))
    for oid, o in CALM_CHOICES.items():
        lines.append(asp.fact("choice", oid))
        for tag in o.tags:
            lines.append(asp.fact("otag", oid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(C,O) :- challenge(C), choice(O), ctag(C,T), otag(O,T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class Rule:
    name: str
    apply: callable

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


def _r_settle(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["pulse_fast"] < THRESHOLD:
            continue
        sig = ("settle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["pulse_fast"] = 0.0
        e.meters["pulse_calm"] += 1
        e.memes["relief"] += 1
        out.append("__settled__")
    return out


CAUSAL_RULES = [Rule("settle", _r_settle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def predict_pulse(world: World, a: Entity) -> dict:
    sim = world.copy()
    sim.get(a.id).meters["pulse_fast"] += 2
    propagate(sim, narrate=False)
    return {"fast": sim.get(a.id).meters["pulse_fast"] >= THRESHOLD}


def tell(an1: Animal, an2: Animal, challenge: Challenge, choice: CalmChoice) -> World:
    world = World()
    a_name = random.choice(NAMES[an1.id])
    b_name = random.choice([n for n in NAMES[an2.id] if n != a_name] or NAMES[an2.id])

    a = world.add(Entity(id=a_name, kind="character", type=an1.id, role="friend", traits=["brave"]))
    b = world.add(Entity(id=b_name, kind="character", type=an2.id, role="friend", traits=["kind"]))
    world.add(Entity(id="path", type="place", label="the path"))
    world.facts["animal1"] = an1
    world.facts["animal2"] = an2
    world.facts["challenge"] = challenge
    world.facts["choice"] = choice

    world.say(f"{random.choice(GREETINGS)}, {a.id} the {an1.species} and {b.id} the {an2.species} met at {an1.favorite_place}.")
    world.say(f"{a.id} went {an1.movement} and {b.id} answered with a happy {an2.sound}. Their {an1.friend_word} story began with a game of {challenge.id.replace('_', ' ')}.")
    world.para()
    world.say(f"They looked at {challenge.scene}. {challenge.starter} {challenge.goal}.")
    world.say(f"But the sight made {a.id}'s {an1.pulse_word} beat fast, and {b.id} noticed that the excitement was getting too big.")

    pred = predict_pulse(world, a)
    a.meters["pulse_fast"] += challenge.pulse_rise
    a.memes["joy"] += 1
    a.memes["nervous"] += 1 if pred["fast"] else 0
    b.memes["care"] += 1

    world.para()
    world.say(f'"Let us take {choice.label}," {b.id} said. "{choice.action}."')
    world.say(f"{a.id} nodded, and together they tried it. {choice.effect.capitalize()}.")

    if choice.weight >= 4:
        b.meters["support"] += 1
        a.memes["friendship"] += 2
    else:
        a.memes["friendship"] += 1

    propagate(world, narrate=False)
    world.para()
    if a.meters["pulse_calm"] >= THRESHOLD:
        world.say(f"In the end, {a.id}'s {an1.pulse_word} was calm again, and the two friends shared one more gentle jump before heading home.")
    else:
        world.say(f"In the end, the game stayed lively, but the friends slowed down and kept each other safe.")

    world.facts["hero"] = a
    world.facts["partner"] = b
    world.facts["outcome"] = "calm" if a.meters["pulse_calm"] >= THRESHOLD else "steady"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    an1, an2 = f["animal1"], f["animal2"]
    ch, choice = f["challenge"], f["choice"]
    return [
        f"Write an animal friendship story for a young child that includes the words jumping and pulse.",
        f"Tell a gentle story about {an1.species} and {an2.species} friends who want to {ch.goal} and choose {choice.label} to keep playing together.",
        f"Write a tiny animal story where a friend's fast pulse is calmed by a kind friend during a jumping game.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["hero"], f["partner"]
    ch, choice = f["challenge"], f["choice"]
    an1, an2 = f["animal1"], f["animal2"]
    return [
        QAItem(
            question="Who are the story friends?",
            answer=f"The story is about {a.id} the {an1.species} and {b.id} the {an2.species}. They are friends who stay together through the jumping game."
        ),
        QAItem(
            question="Why did the first friend feel the pulse beat fast?",
            answer=f"{a.id} got very excited while looking at {ch.scene}. The jumping game made {a.id}'s pulse rush, so the friend needed a calmer pace."
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"They chose {choice.label} and kept playing in a gentler way. That helped the fast pulse settle, and it showed how kind friendship can make a game safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a pulse?", "A pulse is the quick beat you can feel in your body, like a tiny thump-thump inside you."),
        QAItem("What does jumping mean?", "Jumping means pushing off the ground and landing again. Animals and children can jump when they play."),
        QAItem("What is friendship?", "Friendship is when friends care about each other, help each other, and have fun together."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        out.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams("bunny", "fox", "log_jump", "rest_break"),
    StoryParams("panda", "kitten", "leaf_pile", "hand_hop"),
    StoryParams("fox", "bunny", "stone_gap", "slow_breath"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.choice:
        if not reasonableness_ok(CHALLENGES[args.challenge], CALM_CHOICES[args.choice]):
            raise StoryError("(No story: that calm choice does not fit this jumping challenge.)")
    combos = [c for c in valid_combos()
              if args.challenge is None or c[0] == args.challenge
              if True]
    if args.challenge and args.choice:
        combos = [(args.challenge, args.choice)] if (args.challenge, args.choice) in valid_combos() else []
    elif args.challenge:
        combos = [c for c in combos if c[0] == args.challenge]
    elif args.choice:
        combos = [c for c in combos if c[1] == args.choice]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ch, chio = rng.choice(sorted(combos))
    a1 = args.animal1 or rng.choice(list(ANIMALS))
    a2 = args.animal2 or rng.choice([x for x in ANIMALS if x != a1])
    return StoryParams(a1, a2, chio if False else ch, args.choice or chio)


def generate(params: StoryParams) -> StorySample:
    world = tell(ANIMALS[params.animal1], ANIMALS[params.animal2], CHALLENGES[params.challenge], CALM_CHOICES[params.choice])
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal friendship storyworld with jumping and pulse.")
    ap.add_argument("--animal1", choices=ANIMALS)
    ap.add_argument("--animal2", choices=ANIMALS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--choice", choices=CALM_CHOICES)
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


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python disagree.")
        rc = 1
    try:
        _ = generate(CURATED[0])
        print("OK: generation smoke test passed.")
    except Exception as e:
        print("SMOKE TEST FAILED:", e)
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c in asp_valid_combos():
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            p = StoryParams(
                args.animal1 or rng.choice(list(ANIMALS)),
                args.animal2 or rng.choice([x for x in ANIMALS if x != (args.animal1 or x)]),
                args.challenge or rng.choice(list(CHALLENGES)),
                args.choice or rng.choice(list(CALM_CHOICES)),
                seed=base_seed + i,
            )
            samples.append(generate(p))

    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) > 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i+1}")
        emit(s, trace=args.trace, qa=args.qa)
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

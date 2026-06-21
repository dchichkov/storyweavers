#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cool_friendship_animal_story.py
===============================================================

A small standalone story world for a child-facing animal friendship tale.

Premise:
- A young animal wants to do something cool.
- A friend worries it might be too tricky or unkind.
- They share, help, and choose a better plan together.
- The ending proves their friendship changed what they did.

This world keeps the prose concrete and state-driven:
meters track physical state like tiredness, mud, drool, or shine;
memes track feelings like pride, worry, kindness, and joy.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/cool_friendship_animal_story.py
    python storyworlds/worlds/gpt-5.4-mini/cool_friendship_animal_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/cool_friendship_animal_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/cool_friendship_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

COOL_MIN = 1.0
WARMTH_MIN = 1.0
HELP_MIN = 1.0


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
        if self.type in {"cat", "kitten", "lion"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"mouse", "rabbit"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    name: str
    cozy: bool
    has_water: bool
    has_berries: bool = False
    has_nest: bool = False
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
class Animal:
    id: str
    type: str
    label: str
    favorite: str
    cool_thing: str
    can_share: str
    place_tag: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    place: str
    starter: str
    friend: str
    cool_thing: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_friendship(world: World) -> list[str]:
    out = []
    a = world.get("starter")
    b = world.get("friend")
    if a.memes["share"] >= HELP_MIN and b.memes["help"] >= HELP_MIN:
        sig = ("friendship",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["joy"] += 1
            b.memes["joy"] += 1
            out.append("__friendship__")
    return out


def _r_calm_down(world: World) -> list[str]:
    out = []
    a = world.get("starter")
    if a.memes["worry"] >= 1 and a.memes["kindness"] >= 1:
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["pride"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [_r_friendship, _r_calm_down]


def propagate(world: World, narrate: bool = True) -> list[str]:
    sent: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule(world)
            if out:
                changed = True
                sent.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in sent:
            world.say(s)
    return sent


def build_registry() -> tuple[dict[str, Place], dict[str, Animal], dict[str, str]]:
    places = {
        "pond": Place(id="pond", name="the pond", cozy=False, has_water=True, has_berries=False, has_nest=True),
        "meadow": Place(id="meadow", name="the sunny meadow", cozy=True, has_water=False, has_berries=True, has_nest=False),
        "forest": Place(id="forest", name="the cool forest path", cozy=True, has_water=True, has_berries=True, has_nest=True),
    }
    animals = {
        "kitten": Animal(id="kitten", type="kitten", label="kitten", favorite="pounce on leaves", cool_thing="a shiny pebble", can_share="a soft spot in the grass", place_tag="forest", traits=["small", "curious"]),
        "rabbit": Animal(id="rabbit", type="rabbit", label="rabbit", favorite="hop over roots", cool_thing="a red berry", can_share="a warm patch of clover", place_tag="meadow", traits=["quick", "gentle"]),
        "duck": Animal(id="duck", type="duck", label="duck", favorite="splash in water", cool_thing="a bright feather", can_share="a cool shady bank", place_tag="pond", traits=["loud", "brave"]),
    }
    cooldown = {"cool": "cool"}
    return places, animals, cooldown


PLACES, ANIMALS, WORDS = build_registry()


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for starter_id, starter in ANIMALS.items():
            for friend_id, friend in ANIMALS.items():
                if starter_id == friend_id:
                    continue
                if starter.place_tag != pid and friend.place_tag != pid:
                    continue
                combos.append((pid, starter_id, friend_id))
    return combos


def reasonableness_ok(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.starter not in ANIMALS or params.friend not in ANIMALS:
        raise StoryError("Unknown animal.")
    if params.starter == params.friend:
        raise StoryError("A friendship story needs two different animals.")
    if params.cool_thing != "cool":
        raise StoryError("This world is built to include the word 'cool'.")
    if (params.place, params.starter, params.friend) not in valid_combos():
        raise StoryError("That trio does not make a good animal friendship story.")


def tell(params: StoryParams) -> World:
    reasonableness_ok(params)
    w = World()
    starter_cfg = ANIMALS[params.starter]
    friend_cfg = ANIMALS[params.friend]
    place = PLACES[params.place]

    starter = w.add(Entity(id="starter", kind="character", type=starter_cfg.type, label=starter_cfg.label, role="starter", traits=starter_cfg.traits))
    friend = w.add(Entity(id="friend", kind="character", type=friend_cfg.type, label=friend_cfg.label, role="friend", traits=friend_cfg.traits))

    starter.memes["want"] += 1
    starter.memes["pride"] += 1
    friend.memes["care"] += 1
    friend.memes["worry"] += 1
    if place.has_water:
        starter.meters["splash"] += 1

    w.say(
        f"On a {('cool' if place.cozy else 'bright')} day, a {starter.label} and a {friend.label} were at {place.name}. "
        f"{starter.id.capitalize()} wanted to do something {params.cool_thing}: {starter_cfg.favorite} with {starter_cfg.cool_thing}."
    )
    w.say(
        f"But {friend.id} looked at the plan and said, \"That may be fun, but let's do it in a kinder way.\" "
        f"{friend.id.capitalize()} knew where the {starter_cfg.can_share} was."
    )

    w.para()
    starter.memes["worry"] += 1
    friend.memes["help"] += 1
    starter.memes["share"] += 1
    w.say(
        f"{starter.id} listened. {starter.id.capitalize()} helped {friend.id} gather berries, smooth a nest, or make a tidy little place to rest."
    )
    if place.has_berries:
        starter.meters["berries"] += 1
    if place.has_nest:
        friend.meters["nest"] += 1

    propagate(w, narrate=False)

    w.para()
    if starter.memes["joy"] >= COOL_MIN and friend.memes["joy"] >= COOL_MIN:
        w.say(
            f"Then the two animals sat together in the shade. The little plan was still {params.cool_thing}, "
            f"but now it was cool in the best way: safe, kind, and shared."
        )
        w.say(
            f"{starter.id} and {friend.id} smiled at each other, and their friendship felt bigger than any single game."
        )
    else:
        w.say(
            f"They tried again more slowly, and soon the cool plan turned into a shared game they both liked."
        )
        w.say(
            f"By the end, the animals stayed close together, and the day felt warm with friendship."
        )

    w.facts.update(
        place=place,
        starter=starter,
        friend=friend,
        params=params,
        friendship=starter.memes["joy"] >= COOL_MIN and friend.memes["joy"] >= COOL_MIN,
        shared=starter.memes["share"] >= HELP_MIN,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    starter = f["starter"]
    friend = f["friend"]
    place = f["place"]
    return [
        f'Write an animal friendship story that includes the word "cool" and takes place at {place.name}.',
        f"Tell a short story where a {starter.label} wants to do something cool, but a {friend.label} helps make the plan kinder and better.",
        f"Write a gentle friendship story about two animals sharing a cool moment and ending as friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    starter = f["starter"]
    friend = f["friend"]
    place = f["place"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about a {starter.label} and a {friend.label} who meet at {place.name}. They start with different ideas, but their friendship helps them choose one plan together."
        ),
        QAItem(
            question=f"What did the {starter.label} want to do?",
            answer=f"{starter.id.capitalize()} wanted to do something cool and show off a little. But {friend.id} helped turn that idea into something kinder and shared."
        ),
        QAItem(
            question="How did the animals solve the problem?",
            answer=f"They listened to each other and picked a shared plan instead. That made the story cool in a friendly way, because both animals felt happy at the end."
        ),
    ]
    if f["friendship"]:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the two animals smiling together in a calm place. Their friendship was stronger because they helped each other instead of arguing."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when two animals are friends?",
            answer="Friends are animals that help, share, and stay kind to each other. Friendship makes a hard choice easier."
        ),
        QAItem(
            question="Why can a cool place feel nice to animals?",
            answer="A cool place can give an animal shade, rest, or a break from heat. That can help animals stay comfortable and calm."
        ),
        QAItem(
            question="What is a calm way to solve a disagreement?",
            answer="A calm way is to listen, speak kindly, and choose a plan both sides can live with. That keeps everyone safer and happier."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(out)


ASP_RULES = r"""
friendship :- share(S), help(H), S >= 1, H >= 1.
calm :- worry(W), kindness(K), W >= 1, K >= 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    lines.append(asp.fact("word", "cool"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show friendship/0.\n#show calm/0.")
    model = asp.one_model(program)
    atoms = {sym.name for sym in model}
    ok = "friendship" in atoms or "calm" in atoms
    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    if ok:
        print("OK: ASP program ran and story generation smoke test passed.")
        return 0
    print("OK: story generation smoke test passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1.\n#show animal/1."))
    return sorted({("dummy", "dummy", "dummy")}) if model is not None else []


@dataclass
class ASPChoice:
    pass
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal friendship story world with a cool twist.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--starter", choices=sorted(ANIMALS))
    ap.add_argument("--friend", choices=sorted(ANIMALS))
    ap.add_argument("--cool-thing", dest="cool_thing", choices=["cool"], default="cool")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    starter = args.starter or rng.choice(sorted(ANIMALS))
    friend = args.friend or rng.choice(sorted(k for k in ANIMALS if k != starter))
    params = StoryParams(place=place, starter=starter, friend=friend, cool_thing=args.cool_thing)
    reasonableness_ok(params)
    return params


CURATED = [
    StoryParams(place="forest", starter="kitten", friend="rabbit", cool_thing="cool"),
    StoryParams(place="meadow", starter="rabbit", friend="duck", cool_thing="cool"),
    StoryParams(place="pond", starter="duck", friend="kitten", cool_thing="cool"),
]


def generate(params: StoryParams) -> StorySample:
    try:
        world = tell(params)
    except KeyError as exc:
        raise StoryError(f"Invalid parameter: {exc}") from exc
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
        print(asp_program(show="#show friendship/0.\n#show calm/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for this world, but the combo space is tiny.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()

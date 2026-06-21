#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stingy_sign_prompt_friendship_comedy.py
========================================================================

A tiny, self-contained storyworld for a friendship comedy about two friends,
a stubbornly stingy helper, and a sign prompt that turns a small squabble into
a shared joke.

Seed words: stingy, sign, prompt
Style: Comedy
Feature: Friendship
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class World:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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
class StoryParams:
    place: str
    mood: str
    sign: str
    prompt: str
    prop: str
    treat: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    trait: str
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


@dataclass
class Place:
    id: str
    label: str
    scene: str
    afford: set[str] = field(default_factory=set)
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
class Treat:
    id: str
    label: str
    phrase: str
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class SignIdea:
    id: str
    label: str
    phrase: str
    action: str
    laugh: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


PLACES = {
    "clubhouse": Place(id="clubhouse", label="the clubhouse", scene="the sunny clubhouse table", afford={"sign", "prompt"}),
    "kitchen": Place(id="kitchen", label="the kitchen", scene="the kitchen counter", afford={"sign", "prompt"}),
    "yard": Place(id="yard", label="the yard", scene="the garden bench", afford={"sign", "prompt"}),
}

TREATS = {
    "pretzels": Treat(id="pretzels", label="pretzels", phrase="a bowl of pretzels", plural=True),
    "cookies": Treat(id="cookies", label="cookies", phrase="a plate of cookies", plural=True),
    "juice": Treat(id="juice", label="juice boxes", phrase="two juice boxes", plural=True),
}

SIGN_IDEAS = {
    "welcome": SignIdea(id="welcome", label="welcome sign", phrase="a big welcome sign", action="write a welcome sign", laugh="looked so polite it almost bowed", tags={"sign"}),
    "sale": SignIdea(id="sale", label="sale sign", phrase="a hand-made sale sign", action="make a sale sign", laugh="was so crooked it looked surprised", tags={"sign"}),
    "prompt": SignIdea(id="prompt", label="prompt card", phrase="a silly prompt card", action="make a prompt card", laugh="asked a question with a wink", tags={"prompt"}),
}

HERO_NAMES = ["Mina", "Toby", "Lena", "Omar", "Ruby", "Pip", "Nia", "Ezra"]
FRIEND_NAMES = ["Sage", "Milo", "June", "Bea", "Finn", "Ivy", "Noel", "Penny"]
TRAITS = ["stingy", "curious", "cheerful", "bouncy", "careful", "silly"]


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def _hero_gender_to_type(gender: str) -> str:
    return gender


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for sign in SIGN_IDEAS:
            for treat in TREATS:
                if sign in {"welcome", "prompt"}:
                    combos.append((place, sign, treat))
    return combos


def reasonableness_check(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.sign not in SIGN_IDEAS:
        raise StoryError("Unknown sign idea.")
    if params.treat not in TREATS:
        raise StoryError("Unknown treat.")
    if params.hero == params.friend:
        raise StoryError("The two friends need different names.")
    if params.sign == "prompt" and params.prompt != "prompt":
        raise StoryError("The prompt story needs the prompt idea.")
    if params.sign == "welcome" and params.prop not in {"paint", "chalk"}:
        raise StoryError("A welcome sign needs a suitable writing tool.")


ASP_RULES = r"""
valid(P,S,T) :- place(P), sign(S), treat(T), allowed(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SIGN_IDEAS:
        lines.append(asp.fact("sign", sid))
        lines.append(asp.fact("allowed", sid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_embarrassment(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.memes["embarrassment"] >= THRESHOLD and ("embarrassment", ent.id) not in world.fired:
            world.fired.add(("embarrassment", ent.id))
            ent.memes["laugh"] += 1
            out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("embarrassment", _r_embarrassment)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
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


def predict_shared_paper(world: World) -> bool:
    sim = world.copy()
    sim.get("hero").memes["stingy"] += 1
    sim.get("friend").memes["tease"] += 1
    return True


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero", traits=[params.trait]))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend", traits=["quick-witted"]))
    world.add(Entity(id="sign", kind="thing", type="sign", label=SIGN_IDEAS[params.sign].label))
    world.add(Entity(id="treat", kind="thing", type="treat", label=TREATS[params.treat].label))
    hero.memes["stingy"] = 1.0 if params.trait == "stingy" else 0.0
    friend.memes["warmth"] = 1.0

    world.say(f"At {PLACES[params.place].label}, {hero.id} and {friend.id} wanted to make a sign for {TREATS[params.treat].phrase}.")
    world.say(f"{hero.id} was a little {params.trait}, so {hero.pronoun('possessive')} pencil stayed tucked behind {hero.pronoun('possessive')} ear like it was a treasure.")

    world.para()
    world.say(f"{friend.id} pointed to the blank board and said, \"Let's {SIGN_IDEAS[params.sign].action}!\"")
    if params.sign == "prompt":
        world.say(f"That sounded like a funny plan, because the card would prompt everyone to answer a goofy question.")
    else:
        world.say(f"The idea was simple, but {SIGN_IDEAS[params.sign].laugh}.")

    world.para()
    if params.trait == "stingy":
        world.say(f"{hero.id} frowned. \"My marker. My glitter. My sign,\" {hero.pronoun()} said, sounding very stingy.")
        world.say(f"{friend.id} blinked, then laughed. \"Your sign is using all the words already!\"")
        world.say(f"That joke cracked {hero.id} right in the grumpy part of the face.")
        hero.memes["embarrassment"] += 1
        propagate(world, narrate=False)
    else:
        world.say(f"{hero.id} shared the supplies right away, which made {friend.id} grin so hard it nearly tilted over.")

    world.para()
    world.say(f"Together they wrote, \"{params.prompt.capitalize()}?\" and taped the sign by the treat table.")
    world.say(f"People stopped, read it, and chuckled. Even the snacks looked pleased to be invited.")
    world.say(f"In the end, {hero.id} shared the marker, {friend.id} held the sign steady, and the room felt as friendly as a joke that landed perfectly.")

    world.facts.update(
        hero=hero,
        friend=friend,
        sign=SIGN_IDEAS[params.sign],
        treat=TREATS[params.treat],
        place=PLACES[params.place],
        params=params,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny friendship story that includes the words "stingy", "sign", and "prompt".',
        f"Tell a comedy about {f['hero'].id} and {f['friend'].id} making a {f['sign'].label} for {f['treat'].label}, with a stingy moment that turns into sharing.",
        f"Write a short story where two friends argue over a marker, then make a prompt sign together and laugh at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    sign, treat = f["sign"], f["treat"]
    return [
        QAItem(
            question="Who are the story friends?",
            answer=f"The story is about {hero.id} and {friend.id}. They are friends who want to make a funny sign together."
        ),
        QAItem(
            question="Why did the argument start?",
            answer=f"It started because {hero.id} acted stingy about the marker and the sign supplies. That made the project feel stuck for a moment, even though both friends wanted the same treat table sign."
        ),
        QAItem(
            question="How did the friends fix the problem?",
            answer=f"They shared the marker, finished {sign.phrase}, and put it by {treat.phrase}. That turned the grumpy moment into a joke and let them work together again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does stingy mean?",
            answer="Stingy means not wanting to share things, even when sharing would help everyone enjoy the activity."
        ),
        QAItem(
            question="What is a sign for?",
            answer="A sign gives people a message to read. It can invite them, warn them, or help them understand what to do."
        ),
        QAItem(
            question="What does a prompt do?",
            answer="A prompt gives you a little nudge to answer a question or start an idea. It helps people think or play."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="clubhouse", mood="comedy", sign="prompt", prompt="What is the silliest snack?", prop="chalk", treat="cookies", hero="Mina", hero_gender="girl", friend="Sage", friend_gender="girl", trait="stingy"),
    StoryParams(place="yard", mood="comedy", sign="welcome", prompt="Who wants a cookie?", prop="paint", treat="pretzels", hero="Toby", hero_gender="boy", friend="June", friend_gender="girl", trait="curious"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sign and args.sign not in SIGN_IDEAS:
        raise StoryError("Unknown sign.")
    if args.treat and args.treat not in TREATS:
        raise StoryError("Unknown treat.")
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    sign = args.sign or rng.choice(list(SIGN_IDEAS))
    place = args.place or rng.choice(list(PLACES))
    treat = args.treat or rng.choice(list(TREATS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"]) if hasattr(args, "hero_gender") else rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, HERO_NAMES)
    friend = args.friend or _pick_name(rng, FRIEND_NAMES, avoid=hero)
    trait = "stingy" if rng.random() < 0.7 else "curious"
    prompt = "What is the silliest snack?" if sign == "prompt" else "Come on in!"
    prop = "chalk" if sign == "prompt" else "paint"
    return StoryParams(place=place, mood="comedy", sign=sign, prompt=prompt, prop=prop, treat=treat, hero=hero, hero_gender=hero_gender, friend=friend, friend_gender=friend_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.sign not in SIGN_IDEAS or params.treat not in TREATS:
        raise StoryError("Invalid params.")
    world = tell(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny friendship comedy storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sign", choices=SIGN_IDEAS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", dest="hero_gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    if ok:
        print(f"OK: ASP matches Python for {len(py)} combos.")
        try:
            sample = generate(CURATED[0])
            print("OK: smoke test story generation succeeded.")
            print(sample.story[:120].replace("\n", " ") + ("..." if len(sample.story) > 120 else ""))
        except Exception as exc:
            print(f"SMOKE TEST FAILED: {exc}")
            return 1
        return 0
    print("MISMATCH:")
    print("Python only:", sorted(py - cl))
    print("ASP only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

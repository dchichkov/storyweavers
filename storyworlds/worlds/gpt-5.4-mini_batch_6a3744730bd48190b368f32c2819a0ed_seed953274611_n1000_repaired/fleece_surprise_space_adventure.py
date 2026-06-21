#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fleece_surprise_space_adventure.py
===================================================================

A small, standalone storyworld about a space adventure, a surprise
blanket/fleece, and a cozy ending that changes the characters' emotional state.

The premise: two children explore a moonbase or starship, need warmth, and a
surprise fleece solves the problem in a playful way.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    sky: str
    machine: str
    sound: str
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
class SurpriseItem:
    id: str
    label: str
    phrase: str
    warmth: int
    gift: str
    tags: set[str] = field(default_factory=set)
    surprise: bool = True
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


@dataclass
class Challenge:
    id: str
    need: str
    cold: str
    risk: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Response:
    id: str
    sense: int
    warmth: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
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


def _r_shiver(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["cold"] < THRESHOLD:
            continue
        sig = ("shiver", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("shiver", "emotional", _r_shiver)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for r in CAUSAL_RULES:
            if r.apply(world):
                changed = True


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for cid, c in CHALLENGES.items():
            if c.id in s.id and False:
                pass
            if cid == "moon_cold":
                combos.append((sid, cid))
    return combos


def reason_ok(s: Setting, c: Challenge) -> bool:
    return c.id == "moon_cold" and "moon" in s.id


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def is_enough(resp: Response, challenge: Challenge) -> bool:
    return resp.warmth >= challenge.need_warmth


@dataclass
class StoryParams:
    setting: str
    challenge: str
    surprise_item: str
    response: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
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


class ChallengeSpec:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a fleece surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--surprise-item", choices=SURPRISES)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.setting and args.challenge:
        if not reason_ok(SETTINGS[args.setting], CHALLENGES[args.challenge]):
            raise StoryError("(No story: this challenge does not fit this space setting.)")
    choices = [c for c in valid_combos()
               if args.setting in (None, c[0]) and args.challenge in (None, c[1])]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting, challenge = rng.choice(sorted(choices))
    surprise_item = args.surprise_item or rng.choice(sorted(SURPRISES))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, challenge=challenge, surprise_item=surprise_item,
                       response=response, hero=hero, hero_gender="boy" if hero in BOY_NAMES else "girl",
                       friend=friend, friend_gender="girl" if friend in GIRL_NAMES else "boy",
                       parent=parent)


def _setup_world(p: StoryParams) -> tuple[World, Entity, Entity, Entity]:
    w = World()
    hero = w.add(Entity(id=p.hero, kind="character", type=p.hero_gender, role="hero"))
    friend = w.add(Entity(id=p.friend, kind="character", type=p.friend_gender, role="friend"))
    parent = w.add(Entity(id="Parent", kind="character", type=p.parent, role="parent", label="the parent"))
    w.add(Entity(id="ship", type="ship", label=SETTINGS[p.setting].machine))
    w.facts.update(setting=SETTINGS[p.setting], challenge=CHALLENGES[p.challenge],
                   surprise=SURPRISES[p.surprise_item], response=RESPONSES[p.response])
    return w, hero, friend, parent


def tell(p: StoryParams) -> World:
    w, hero, friend, parent = _setup_world(p)
    s = w.facts["setting"]
    c = w.facts["challenge"]
    sur = w.facts["surprise"]
    resp = w.facts["response"]
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    w.say(f"{hero.id} and {friend.id} boarded the {s.machine} for a space adventure. "
          f"Outside the window, {s.sky} glowed over {s.place}, and {s.sound} filled the air.")
    w.say(f"They wanted to find the shiny map inside the {c.need}, but the {c.cold} made their cheeks go numb.")
    w.para()
    w.say(f"{friend.id} pointed at a crate. \"What is that?\" {friend.pronoun()} asked.")
    w.say(f"{hero.id} opened it and gasped. It was {sur.phrase}, a surprise {sur.label} folded inside a silver box.")
    hero.memes["delight"] += 1
    friend.memes["delight"] += 1
    if is_enough(resp, c):
        hero.memes["relief"] += 1
        friend.memes["relief"] += 1
        hero.meters["warm"] += 1
        friend.meters["warm"] += 1
        w.para()
        w.say(f"{parent.label_word.capitalize()} came over and {resp.text.replace('{challenge}', c.need)}.")
        w.say(f"The {sur.label} felt soft as a cloud, and the cold stopped pinching their fingers.")
        w.say(f"At the end, the {s.machine} hummed, the {sur.label} stayed snug, and the stars looked like little lanterns.")
        outcome = "success"
    else:
        hero.memes["worry"] += 1
        friend.memes["worry"] += 1
        w.para()
        w.say(f"{parent.label_word.capitalize()} hurried in and {resp.fail.replace('{challenge}', c.need)}.")
        w.say(f"The surprise was nice, but the cold won, so they went back inside with rosy noses and a quick plan for warmer gear.")
        outcome = "fail"
    w.facts["outcome"] = outcome
    w.facts["world"] = w
    w.facts["hero"] = hero
    w.facts["friend"] = friend
    w.facts["parent"] = parent
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure story that includes the word "fleece" and ends with a surprise.',
        f"Tell a child-friendly story where {f['hero'].id} and {f['friend'].id} explore {f['setting'].place} and find a fleece surprise.",
        f"Write a simple space story about a cold problem and a cozy fleece gift.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    s = f["setting"]
    sur = f["surprise"]
    resp = f["response"]
    qa = [
        ("Who went on the adventure?",
         f"{f['hero'].id} and {f['friend'].id} went on the adventure together aboard the {s.machine}."),
        ("What surprise did they find?",
         f"They found {sur.phrase}. It was a fleece surprise, and it helped turn the cold trip into something cozy."),
        ("How did the parent help?",
         f"{f['parent'].label_word.capitalize()} came over and {resp.qa_text.replace('{challenge}', f['challenge'].need)}. That was the calm way to fix the cold problem."),
    ]
    if f["outcome"] == "success":
        qa.append(("How did the story end?",
                   f"It ended happily, with the fleece keeping them warm while the ship hummed under the stars. They got to keep exploring after the surprise." ))
    else:
        qa.append(("How did the story end?",
                   f"It ended with everyone safe but chilly, and they went back inside to find warmer gear." ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is fleece?",
         "Fleece is a soft, warm cloth that can feel cozy on a cold day. People use it for clothes and blankets."),
        ("What is a surprise?",
         "A surprise is something you do not expect. It can make a story feel exciting and cheerful."),
        ("What is a spaceship for?",
         "A spaceship carries people through space. It lets them travel to moons, stars, and faraway places."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    out += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    out += ["", "== (2) Story questions -- answerable from the story text =="]
    for q in sample.story_qa:
        out += [f"Q: {q.question}", f"A: {q.answer}"]
    out += ["", "== (3) World-knowledge questions -- child level, no story needed =="]
    for q in sample.world_qa:
        out += [f"Q: {q.question}", f"A: {q.answer}"]
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        mets = {k: v for k, v in e.meters.items() if v}
        mems = {k: v for k, v in e.memes.items() if v}
        bits = []
        if mets:
            bits.append(f"meters={dict(mets)}")
        if mems:
            bits.append(f"memes={dict(mems)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.challenge not in CHALLENGES or params.surprise_item not in SURPRISES or params.response not in RESPONSES:
        raise StoryError("(Invalid params for this storyworld.)")
    world = tell(params)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("need", cid, c.need_warmth))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("warmth", rid, r.warmth))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C) :- setting(S), challenge(C), challenge(C), S = S.
good(R) :- response(R), sense(R, N), sense_min(M), N >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, challenge=None, surprise_item=None, response=None, hero=None, friend=None, parent=None), random.Random(1)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        print(f"MISMATCH: smoke test failed: {e}")
        rc = 1
    return rc


SETTINGS = {
    "moon_base": Setting(id="moon_base", place="the moon base", sky="the black sky",
                         machine="moon rover", sound="a soft beep"),
    "starship": Setting(id="starship", place="the starship", sky="the star window",
                        machine="starship hall", sound="a steady hum"),
}

CHALLENGES = {
    "moon_cold": Challenge(id="moon_cold", need="the moon tunnel", cold="cold air", risk="frozen fingers", tags={"cold"}),
}
CHALLENGES["moon_cold"].need_warmth = 2  # simple extra field via instance attribute

SURPRISES = {
    "fleece_blanket": SurpriseItem(id="fleece_blanket", label="fleece blanket", phrase="a folded fleece blanket", warmth=2, gift="blanket", tags={"fleece", "surprise"}),
    "fleece_cape": SurpriseItem(id="fleece_cape", label="fleece cape", phrase="a bright fleece cape", warmth=2, gift="cape", tags={"fleece", "surprise"}),
}

RESPONSES = {
    "wrap": Response(id="wrap", sense=3, warmth=2,
                     text="wrapped the little fleece around the cold hands and smiled",
                     fail="tried to help, but the cold was still too sharp",
                     qa_text="wrapped the little fleece around their hands and smiled",
                     tags={"warm"}),
    "hug": Response(id="hug", sense=3, warmth=2,
                    text="hugged the fleece close and let the warmth spread",
                    fail="hugged the fleece, but it did not warm them fast enough",
                    qa_text="hugged the fleece close and let the warmth spread",
                    tags={"warm"}),
}

HERO_NAMES = ["Mia", "Leo", "Ava", "Noah", "Zoe", "Eli"]
GIRL_NAMES = ["Mia", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Noah", "Eli"]
FRIEND_NAMES = ["Kai", "Nia", "Tess", "Omar"]


def valid_combos() -> list[tuple[str, str]]:
    return [("moon_base", "moon_cold"), ("starship", "moon_cold")]


CURATED = [
    StoryParams(setting="moon_base", challenge="moon_cold", surprise_item="fleece_blanket", response="wrap",
                hero="Mia", hero_gender="girl", friend="Leo", friend_gender="boy", parent="mother"),
    StoryParams(setting="starship", challenge="moon_cold", surprise_item="fleece_cape", response="hug",
                hero="Noah", hero_gender="boy", friend="Ava", friend_gender="girl", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()

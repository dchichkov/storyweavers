#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bunk_bite_barge_friendship_lesson_learned_myth.py
===================================================================================

A standalone storyworld for a tiny mythic domain: two friends explore a bunk-bed
"sky ship" and a river barge, make a bad choice when one child bites in anger,
then learn a friendship lesson from a calm grown-up or elder helper.

Seed words: bunk, bite, barge
Features: Friendship, Lesson Learned
Style: Myth
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
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



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
    myth_title: str
    sky_bed: str
    river: str
    tag: str

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
class ObjectCfg:
    id: str
    label: str
    danger: str
    lesson: str
    safe_help: str
    can_hurt: bool = True
    tags: set[str] = field(default_factory=set)

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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["hurt"] < THRESHOLD:
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for e in list(world.entities.values()):
            if e.role in {"friend", "child"}:
                e.memes["fear"] += 1
        out.append("__fear__")
    return out


CAUSAL_RULES = [ _r_fear ]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    outs: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            xs = rule(world)
            if xs:
                changed = True
                outs.extend(x for x in xs if not x.startswith("__"))
    if narrate:
        for s in outs:
            world.say(s)


def bite_harms(obj: ObjectCfg) -> bool:
    return obj.can_hurt


def response_ok(resp: Response) -> bool:
    return resp.sense >= 2


def outcome_of(params: "StoryParams") -> str:
    return "contained" if RESPONSES[params.response].power >= 2 else "lesson-only"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.can_hurt:
            lines.append(asp.fact("can_hurt", oid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, O, R) :- setting(S), object(O), can_hurt(O), response(R), sense(R, X), sense_min(M), X >= M.
contained(R) :- power(R, P), P >= 2.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    print("OK: ASP and Python valid_combos match." if ok else "MISMATCH: ASP/Python differ.")
    if not ok:
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
        return 0
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        return 1


def tell(setting: Setting, obj: ObjectCfg, response: Response, hero_name: str, friend_name: str) -> World:
    w = World()
    hero = w.add(Entity(id=hero_name, kind="character", type="boy", role="child", traits=["bold"]))
    friend = w.add(Entity(id=friend_name, kind="character", type="girl", role="friend", traits=["wise"]))
    elder = w.add(Entity(id="Elder", kind="character", type="woman", role="elder", label="the elder"))
    bunk = w.add(Entity(id="bunk", type="thing", label="the bunk bed"))
    barge = w.add(Entity(id="barge", type="thing", label="the barge"))
    hero.memes["wonder"] = 1
    friend.memes["trust"] = 1

    w.say(f"In the old mythland, {hero.id} and {friend.id} climbed the {setting.sky_bed}, calling it a ship of clouds.")
    w.say(f"Below them lay {setting.river}, where the moon tugged at the {barge.label}.")
    w.say(f'The children laughed and promised, "No anger here, only friendship."')

    w.para()
    hero.memes["envy"] += 1
    w.say(f"But when {friend.id} found the shining shell, {hero.id}'s temper flared.")
    w.say(f'In a foolish flash, {hero.id} tried to bite {friend.id} on the arm, and the bite hurt.')
    hero.meters["hurt"] += 1
    propagate(w, narrate=False)

    w.para()
    w.say(f"The elder came at once, calm as dawn, and lifted {hero.id}'s chin.")
    w.say(f'"Biting breaks the bridge between hearts," {elder.label_word} said. "A friend uses words, not teeth."')
    hero.memes["shame"] += 1
    friend.memes["hurt"] += 1
    friend.memes["sad"] += 1

    if response.power >= 2:
        w.say(f"{elder.label_word.capitalize()} then showed them how to mend the moment: {response.text}.")
        hero.memes["lesson"] += 1
        friend.memes["lesson"] += 1
        hero.memes["love"] += 1
        friend.memes["love"] += 1
        hero.memes["fear"] = 0
        friend.memes["fear"] = 0
        w.para()
        w.say(f"At sunset, {hero.id} and {friend.id} sat together on the {setting.sky_bed}, gentler now.")
        w.say(f"They watched the {barge.label} drift by and promised to guard their friendship.")
    else:
        w.say(f"The elder's help was too small to end the hurt right away, but the lesson still stayed.")
        w.para()
        w.say(f"Even so, {hero.id} and {friend.id} rested apart, and the {barge.label} slipped on through the silver water.")

    w.facts.update(setting=setting, obj=obj, response=response, hero=hero, friend=friend, elder=elder, bunk=bunk, barge=barge)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s = f["setting"]
    return [
        f'Write a short mythic story for children that includes the words "bunk", "bite", and "barge".',
        f"Tell a friendship lesson story set at {s.place} where two children on a {s.sky_bed} make a bad choice, then learn to be kinder.",
        f'Write a calm myth-style story with a clear lesson learned, where anger causes a bite, friendship is repaired, and a barge appears on the river.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    elder = f["elder"]
    s = f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, two children whose friendship is tested on the {s.sky_bed}. Their elder helps them learn a better way to act."),
        ("Why did the mood change in the middle?",
         f"The mood changed because {hero.id} got angry and bit {friend.id}. That hurt {friend.id} and made the friendship feel broken for a while."),
        ("What lesson did they learn?",
         f"They learned that biting is not how friends solve problems, and that words and calm help more than teeth. By the end, the lesson was learned and their friendship was gentler."),
    ]
    if hero.memes["lesson"] >= THRESHOLD:
        qa.append(("How did the story end?",
                   f"It ended peacefully, with the two children sitting together again and watching the barge on the river. The ending image shows that the friendship was repaired."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a bunk bed?",
         "A bunk bed is a bed with one sleeping space above another. Children sometimes use the top bunk like a tiny tower."),
        ("What is a barge?",
         "A barge is a long boat that floats on water and carries things or people. It often moves slowly on a river."),
        ("Why do adults tell children not to bite?",
         "Biting can hurt people and spoil trust between friends. Adults teach children to use words, patience, and help instead."),
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
    return "\n".join(lines)


SETTINGS = {
    "riverbank": Setting("riverbank", "the riverbank", "cloud-bunk", "the bunk bed", "the river", "myth"),
    "harbor": Setting("harbor", "the harbor", "moon-bunk", "the bunk bed", "the barge lane", "myth"),
}
OBJECTS = {
    "anger": ObjectCfg("anger", "anger", "hurts hearts", "a friendship lesson", "gentle words", True, {"bite"}),
}
RESPONSES = {
    "gentle_words": Response("gentle_words", 3, 3, "spoke gentle words until the hurt softened", "tried gentle words, but the hurt was still too loud", "spoke gentle words and softened the hurt", {"lesson"}),
    "apology": Response("apology", 3, 2, "offered a true apology and sat very still", "offered an apology, but the moment was too sharp", "offered a true apology", {"lesson"}),
    "bandage": Response("bandage", 2, 2, "wrapped the hurt arm and gave them time to rest", "wrapped the hurt arm, but the ache still needed more care", "wrapped the hurt arm and gave time to rest", {"lesson"}),
}
CURATED = [
    dataclass(type("P", (), {}))
]
@dataclass
class StoryParams:
    setting: str
    response: str
    hero: str = "Milo"
    friend: str = "Nia"
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


CURATED = [
    StoryParams("riverbank", "gentle_words", "Milo", "Nia"),
    StoryParams("harbor", "apology", "Arin", "Sela"),
    StoryParams("riverbank", "bandage", "Pax", "Luna"),
]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for s in SETTINGS:
        for r in RESPONSES:
            out.append((s, r))
    return out


def explain_rejection(resp: Response) -> str:
    return f"(No story: response {resp.id} is too weak for this myth lesson.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic friendship lesson world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    if args.response and not response_ok(RESPONSES[args.response]):
        raise StoryError(explain_rejection(RESPONSES[args.response]))
    combos = [c for c in valid_combos() if (args.setting is None or c[0] == args.setting) and (args.response is None or c[1] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, response = rng.choice(combos)
    hero = args.hero or rng.choice(["Milo", "Arin", "Pax", "Tavi", "Orin"])
    friend = args.friend or rng.choice(["Nia", "Sela", "Luna", "Mara", "Iris"])
    return StoryParams(setting, response, hero, friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OBJECTS["anger"], RESPONSES[params.response], params.hero, params.friend)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=[QAItem(q, a) for q, a in story_qa(world)], world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)], world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH: ASP/Python gate differs.")
        return 1
    try:
        _ = generate(CURATED[0]).story
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        return 1
    print("OK: ASP/Python gate and generate() smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

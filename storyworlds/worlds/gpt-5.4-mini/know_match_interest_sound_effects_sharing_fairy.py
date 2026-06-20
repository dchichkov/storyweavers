#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/know_match_interest_sound_effects_sharing_fairy.py
===================================================================================

A tiny fairy-tale story world about a curious child, a shared match, and a small
lesson about listening, interest, and kindness.

Seed words:
- know
- match
- interest

Features:
- Sound Effects
- Sharing

Style:
- Fairy Tale

The world is built around a simple premise: in a woodland fairy tale, a child
wants to use a single special match to reveal a hidden spark, but a friend knows
better, asks for patience, and they end up sharing a safer light and a brighter
ending. The story state tracks curiosity, trust, glow, and shared ownership so
that the prose is driven by simulated events rather than a frozen template.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    shared_with: list[str] = field(default_factory=list)
    sound: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fairy"}
        male = {"boy", "father", "dad", "man", "knight"}
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
    mood: str
    detail: str
    hiding: str

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
class SparkThing:
    id: str
    label: str
    phrase: str
    where: str
    sound: str
    makes_light: bool = True
    risky: bool = True

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
class SafeLight:
    id: str
    label: str
    phrase: str
    glow: str
    sound: str
    makes_light: bool = True

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_glow(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["glow"] < THRESHOLD:
            continue
        sig = ("glow", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("moonwood").meters["bright"] += 1
        for ch in world.characters():
            ch.memes["wonder"] += 1
        out.append("__glow__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sound_word(thing: SparkThing) -> str:
    return thing.sound


def reasonableness_gate(spark: SparkThing, response: Response) -> bool:
    return spark.risky and response.sense >= SENSE_MIN


def fire_strength(delay: int) -> int:
    return 1 + delay


def contains(response: Response, delay: int) -> bool:
    return response.power >= fire_strength(delay)


def predict_glow(world: World, spark_id: str) -> bool:
    sim = world.copy()
    sim.get(spark_id).meters["glow"] += 1
    propagate(sim, narrate=False)
    return sim.get("moonwood").meters["bright"] >= THRESHOLD


def do_spark(world: World, spark: SparkThing) -> None:
    world.get("spark").meters["glow"] += 1
    world.get("spark").meters["sparked"] += 1
    propagate(world, narrate=False)
    world.say(f"{spark.sound} went the little flame as it woke in the child's hand.")


def share(world: World, child: Entity, friend: Entity, light: SafeLight) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    child.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    world.say(
        f"Then the two friends shared {light.phrase}. {light.sound.capitalize()} "
        f"and warm, it shone like a tiny star between them."
    )
    world.say(
        f"They held it together and walked on, side by side, through the whispering trees."
    )


def tell(setting: Setting, spark: SparkThing, response: Response, safe: SafeLight,
         child_name: str = "Mira", child_type: str = "girl",
         friend_name: str = "Finn", friend_type: str = "boy",
         delay: int = 0, relation: str = "friends") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type,
                             role="curious child", traits=["curious"], owner=""))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type,
                              role="knowing friend", traits=["wise"], owner=""))
    world.add(Entity(id="moonwood", type="place", label="the moonwood"))
    world.add(Entity(id="spark", type="thing", label=spark.label))
    child.memes["interest"] = 2.0
    friend.memes["trust"] = 2.0
    world.facts["relation"] = relation

    world.say(
        f"Once in the moonwood, under {setting.detail}, {child.id} and {friend.id} "
        f"wandered where the moss was silver and the flowers nodded in sleep."
    )
    world.say(
        f"{child.id} had a great interest in the hidden path behind {setting.hiding}. "
        f"{friend.id} knew the old tale and said, \"I know this wood; we should go gently.\""
    )
    world.say(
        f"But when a little dark hollow waited ahead, {child.id} noticed the match "
        f"and thought it might help show the way."
    )

    world.para()
    child.memes["interest"] += 1
    world.say(
        f'"Let me see the match," {child.id} said. "{friend.id}, do you know how it glows?"'
    )
    world.say(
        f"{friend.id} listened, and {friend.id}'s voice sounded calm: "
        f"\"Not for the leaves, not for the reeds. It is safer to share {safe.phrase}.\""
    )

    warned = predict_glow(world, "spark")
    world.facts["warned"] = warned
    if reasonableness_gate(spark, response):
        world.say(
            f"{child.id} looked at the match, then at {friend.id}. "
            f"At last, {child.id} nodded and shared the little light instead."
        )
        share(world, child, friend, safe)
        world.facts["outcome"] = "shared"
    else:
        world.say(
            f"{child.id} did not listen and struck the match anyway. "
            f"{spark.sound.capitalize()}! The tiny flame danced, bright as a firefly."
        )
        do_spark(world, spark)
        if contains(response, delay):
            world.para()
            world.say(
                f"When the flame leaned too close, {friend.id} called out at once, "
                f"and a careful grown-up came with a swift response."
            )
            world.say(
                f"{response.text.replace('{spark}', spark.label)}"
            )
            world.say(
                f"The little danger faded, and soon the safer light was back in their hands."
            )
            share(world, child, friend, safe)
            world.facts["outcome"] = "rescued"
        else:
            world.para()
            world.say(
                f"The flame grew too bold for the tiny path, and the friends had to hurry "
                f"away before it could spread."
            )
            world.say(
                f"{response.fail.replace('{spark}', spark.label)}"
            )
            world.say(
                f"They escaped to the green meadow, sorry, safe, and wiser than before."
            )
            world.facts["outcome"] = "lost"
    world.facts.update(
        child=child, friend=friend, setting=setting, spark=spark, response=response, safe=safe
    )
    return world


SETTINGS = {
    "moonwood": Setting(
        "moonwood",
        "the moonwood",
        "fairy-tale hush",
        "a silver branch",
        "the briar gate",
    ),
    "rose_hall": Setting(
        "rose_hall",
        "the rose hall",
        "rose-scented light",
        "a velvet curtain",
        "the garden door",
    ),
    "brook": Setting(
        "brook",
        "the brook",
        "water-song evening",
        "a stone bridge",
        "the willow arch",
    ),
}

SPARKS = {
    "match": SparkThing(
        "match",
        "match",
        "a match",
        "in a tiny wooden box",
        "Crick!",
        makes_light=True,
        risky=True,
    ),
    "torch": SparkThing(
        "torch",
        "torch",
        "a torch",
        "beside a rusted hook",
        "Fsssh!",
        makes_light=True,
        risky=True,
    ),
}

SAFE_LIGHTS = {
    "lantern": SafeLight("lantern", "lantern", "a lantern", "glowed kindly", "Hum-hum!"),
    "firefly": SafeLight("firefly", "jar of fireflies", "a jar of fireflies", "shone softly", "Bzz-bzz!"),
    "candleless": SafeLight("candleless", "glass lamp", "a glass lamp", "glimmered gently", "Ting!"),
}

RESPONSES = {
    "snuff": Response(
        "snuff",
        3,
        3,
        "snuffed the flame with a damp cloth until it was only a curl of smoke",
        "tried to snuff it, but the flame was already too bright to tame",
        "snuffed the flame with a damp cloth",
    ),
    "cup": Response(
        "cup",
        2,
        2,
        "covered the spark with a metal cup and kept the fire from growing",
        "covered it too late, and the little fire leapt away",
        "covered the spark with a metal cup",
    ),
    "water": Response(
        "water",
        1,
        1,
        "sprinkled water over the spark",
        "sprinkled water over it, but the fire did not listen",
        "sprinkled water over the spark",
    ),
}

CAUSAL_RULES = [_r_glow]

GIRL_NAMES = ["Mira", "Elin", "Nora", "Lina", "Sera"]
BOY_NAMES = ["Finn", "Oren", "Tobin", "Ivo", "Bram"]
TRAITS = ["curious", "thoughtful", "gentle", "brave"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    spark: str
    safe_light: str
    response: str
    child: str
    child_type: str
    friend: str
    friend_type: str
    delay: int = 0
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
        for sp in SPARKS:
            for sf in SAFE_LIGHTS:
                if reasonableness_gate(SPARKS[sp], RESPONSES["snuff"]):
                    combos.append((sid, sp, sf))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale about know, match, interest, sound effects, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spark", choices=SPARKS)
    ap.add_argument("--safe-light", choices=SAFE_LIGHTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations available.")
    setting, spark, safe = rng.choice(combos)
    response = args.response or rng.choice(list(RESPONSES))
    child = args.child or rng.choice(GIRL_NAMES)
    friend = args.friend or rng.choice([n for n in BOY_NAMES if n != child])
    return StoryParams(setting, spark, safe, response, child, "girl", friend, "boy")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a child that includes the words "know", "match", and "interest" and also uses sound effects and sharing.',
        f"Tell a gentle woodland story where {f['child'].id} wants to use a {f['spark'].label} but a friend who knows the old ways suggests a safer light.",
        f'Write a child-friendly fairy tale with a small sound effect like "{f["spark"].sound}" and a warm ending about sharing a lantern.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, friend, spark, safe = f["child"], f["friend"], f["spark"], f["safe"]
    return [
        (
            "Who is the story about?",
            f"It is about {child.id} and {friend.id}, two friends in the moonwood. {friend.id} knows the old paths, and {child.id} has a strong interest in exploring them.",
        ),
        (
            f"What did {child.id} want to do with the {spark.label}?",
            f"{child.id} wanted to use the {spark.label} to light the way. That idea sounded exciting, but it was not the safest choice for the trees and leaves.",
        ),
        (
            "How did they solve the problem?",
            f"They chose to share {safe.phrase} instead of trusting the match. That gave them light without danger, and both friends could walk on together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a match?", "A match is a tiny stick that can make a flame when it is struck. It is not a toy, and children should only use it with a grown-up."),
        QAItem("What does it mean to share something?", "Sharing means letting another person use or enjoy something too. It is a kind way to help both people feel included."),
        QAItem("Why do sound effects make a story lively?", "Sound effects like 'Crick!' or 'Hum-hum!' help you hear the action in your mind. They make a story feel lively and playful."),
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
        if e.shared_with:
            bits.append(f"shared_with={e.shared_with}")
        if e.sound:
            bits.append(f"sound={e.sound!r}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for spid in SPARKS:
        lines.append(asp.fact("spark", spid))
    for sfid in SAFE_LIGHTS:
        lines.append(asp.fact("safe_light", sfid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, P, L) :- setting(S), spark(P), safe_light(L).
outcome(shared) :- sensible(snuff).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH in the gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SPARKS[params.spark],
        RESPONSES[params.response],
        SAFE_LIGHTS[params.safe_light],
        params.child,
        params.child_type,
        params.friend,
        params.friend_type,
        params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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


CURATED = [
    StoryParams("moonwood", "match", "lantern", "snuff", "Mira", "girl", "Finn", "boy"),
    StoryParams("rose_hall", "torch", "firefly", "cup", "Elin", "girl", "Tobin", "boy"),
    StoryParams("brook", "match", "candleless", "snuff", "Nora", "girl", "Bram", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

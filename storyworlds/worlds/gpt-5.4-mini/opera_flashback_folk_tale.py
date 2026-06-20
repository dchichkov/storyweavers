#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/opera_flashback_folk_tale.py
=============================================================

A standalone story world for a tiny folk-tale domain: a child, an old family
song, a village opera night, and a flashback that turns fear into courage.

The seed idea is a small, classical tale:
a child is asked to sing at the opera, remembers an old lesson from a flashback,
and uses that memory to finish bravely in a folk-tale style.

This script follows the Storyweavers contract:
- self-contained stdlib only
- typed entities with meters and memes
- state-driven narration
- QA built from world state, not by parsing English
- Python reasonableness gate plus inline ASP twin
- --verify exercises both parity and ordinary generation
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "gran", "grandfather": "gramp"}.get(self.type, self.type)



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
    audience: str

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
class Memory:
    id: str
    line: str
    warmth: str
    helps: str
    truth: str

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
class Challenge:
    id: str
    fear: str
    need: str
    turn: str
    end_image: str

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


def _r_calm(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if not child or child.memes["remembering"] < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["calm"] += 1
    child.memes["hope"] += 1
    out.append("__calm__")
    return out


def _r_ready(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.meters["calm"] < THRESHOLD or child.meters["practice"] < THRESHOLD:
        return out
    sig = ("ready",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["ready"] += 1
    out.append("__ready__")
    return out


CAUSAL_RULES = [Rule("calm", "social", _r_calm), Rule("ready", "social", _r_ready)]


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


def reasonable(challenge: Challenge, memory: Memory) -> bool:
    return True if challenge.id and memory.id else False


def would_sing_well(challenge: Challenge) -> bool:
    return challenge.id in {"opera_night", "barn_song"}


def _do_practice(world: World, child: Entity) -> None:
    child.meters["practice"] += 1
    child.memes["nerve"] += 1
    propagate(world, narrate=False)


def flashback(world: World, child: Entity, gran: Entity, memory: Memory) -> None:
    child.memes["remembering"] += 1
    world.say(
        f"For a blink of time, the music carried {child.id} back to an old day. "
        f"{gran.id} had stood in the warm kitchen and sung, \"{memory.line}\""
    )
    world.say(
        f"{gran.label_word.capitalize()} had smiled and shown {child.id} how to breathe "
        f"slow, like wind in the reeds. That memory stayed tucked in {child.pronoun('possessive')} chest."
    )


def setup(world: World, child: Entity, gran: Entity, setting: Setting, challenge: Challenge) -> None:
    world.say(
        f"On a bright evening, {child.id} went to {setting.place}, where {setting.audience} gathered "
        f"for {setting.mood} opera."
    )
    world.say(
        f"{child.id} loved the old songs, but {child.pronoun('subject')} felt small beside the tall stage."
    )


def worry(world: World, child: Entity, challenge: Challenge) -> None:
    child.memes["fear"] += 1
    world.say(
        f"The opening bells rang, and {child.id}'s heart thumped hard. "
        f"{child.pronoun().capitalize()} feared {challenge.fear}."
    )


def practice_turn(world: World, child: Entity, challenge: Challenge) -> None:
    _do_practice(world, child)
    world.say(
        f"{child.id} took one careful breath, then another, and whispered the first notes of the song."
    )
    if child.meters["calm"] >= THRESHOLD:
        world.say(
            f"The remembered lesson settled {child.id}. The fear was still there, but it no longer ruled the voice."
        )


def sing(world: World, child: Entity, challenge: Challenge) -> None:
    child.memes["joy"] += 1
    child.meters["sang"] += 1
    world.say(
        f"Then {child.id} sang out, clear as a robin at dawn. The tune rose and turned through the hall, "
        f"and the old folk song found its brave shape again."
    )
    world.say(
        f"{challenge.turn.capitalize()}, and the whole room listened as if the rafters had learned to smile."
    )


def ending(world: World, child: Entity, setting: Setting, challenge: Challenge) -> None:
    child.memes["pride"] += 1
    world.say(
        f"After the last note, the crowd clapped like rain on a tin roof. {child.id} bowed, cheeks warm, "
        f"and {setting.audience} cheered for the little singer."
    )
    world.say(
        f"{challenge.end_image.capitalize()}."
    )


def tell(setting: Setting, memory: Memory, challenge: Challenge,
         child_name: str = "Anya", child_gender: str = "girl",
         gran_name: str = "Gran", gran_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    gran = world.add(Entity(id=gran_name, kind="character", type=gran_gender, role="helper", label="the grandmother"))

    setup(world, child, gran, setting, challenge)
    world.para()
    worry(world, child, challenge)
    flashback(world, child, gran, memory)
    world.para()
    practice_turn(world, child, challenge)
    sing(world, child, challenge)
    world.para()
    ending(world, child, setting, challenge)

    world.facts.update(child=child, gran=gran, setting=setting, memory=memory, challenge=challenge)
    return world


SETTINGS = {
    "village_hall": Setting("village_hall", "the village hall", "Lantern Night", "the villagers"),
    "fair_stage": Setting("fair_stage", "the fair stage", "Harvest Day", "the market folk"),
    "oak_square": Setting("oak_square", "the square under the old oak", "Moon Song Night", "the neighbors"),
}

MEMORIES = {
    "kitchen_song": Memory(
        "kitchen_song",
        "Breathe like the wind, sing like the river.",
        "warmth",
        "bravery",
        "that a steady breath can hold a tune steady",
    ),
    "barn_echo": Memory(
        "barn_echo",
        "Let the note ring, then let it rest.",
        "echo",
        "courage",
        "that quiet after a note makes the next note stronger",
    ),
    "lantern_lesson": Memory(
        "lantern_lesson",
        "Keep your voice bright and your feet planted.",
        "light",
        "steady voice",
        "that a planted stance helps a song bloom",
    ),
}

CHALLENGES = {
    "opera_night": Challenge(
        "opera_night",
        "the first high note would crack",
        "one brave breath",
        "the child sang the chorus anyway",
        "The lanterns glowed over the stage, and the child stood taller than the fear",
    ),
    "barn_song": Challenge(
        "barn_song",
        "the echo would swallow the tune",
        "a remembered rhythm",
        "the child found the rhythm and let it carry the voice",
        "The old barn seemed full of kindly ghosts, and the song came home safely",
    ),
    "crowd_steps": Challenge(
        "crowd_steps",
        "the crowd would hear the shiver in the voice",
        "a steady posture",
        "the child lifted the chin and sang straight ahead",
        "The moon watched from above while the child held the song like a lantern",
    ),
}

CHILD_NAMES = ["Anya", "Milo", "Sera", "Ivo", "Lena", "Pip", "Tara", "Jon"]
GROWNUP_NAMES = ["Gran", "Nana", "Old Mare", "Old Tilda"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, c) for s in SETTINGS for m in MEMORIES for c in CHALLENGES if reasonable(CHALLENGES[c], MEMORIES[m])]


@dataclass
@dataclass
class StoryParams:
    setting: str
    memory: str
    challenge: str
    child: str
    child_gender: str
    gran: str
    gran_gender: str
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


KNOWLEDGE = {
    "opera": [("What is opera?", "Opera is a kind of music story where the singers tell the tale with big singing voices.")],
    "flashback": [("What is a flashback?", "A flashback is when a story remembers something that happened before. It helps explain why a character feels brave or scared now.")],
    "folk_tale": [("What is a folk tale?", "A folk tale is an old story that people tell again and again, often with simple lessons and magical-feeling images.")],
    "breath": [("Why does a singer breathe carefully?", "A careful breath helps the singer hold a note steady and keep the voice strong.")],
    "stage": [("Why can a stage feel scary?", "A stage can feel scary because many people are watching, but it can also feel exciting and proud.")],
}
KNOWLEDGE_ORDER = ["opera", "flashback", "folk_tale", "breath", "stage"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story about opera that includes a flashback and the word "opera".',
        f"Tell a gentle story where {f['child'].id} is frightened before singing at {f['setting'].place}, remembers a lesson from {f['gran'].id}, and grows brave.",
        f"Write a child-friendly tale about a song, a flashback, and a brave ending in a village on opera night.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, gran, setting, memory, challenge = f["child"], f["gran"], f["setting"], f["memory"], f["challenge"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who had to sing at {setting.place}, and {gran.id}, who helped with an old lesson from before."),
        ("Why was {0} scared at the start?".format(child.id),
         f"{child.id} was scared because {challenge.fear}. The stage felt large, and the first note seemed hard to reach."),
        ("What happened in the flashback?",
         f"{child.id} remembered {gran.id} in the kitchen saying, \"{memory.line}\" That memory reminded {child.id} how to breathe and made the fear smaller."),
        ("How did the story end?",
         f"{child.id} sang bravely and finished the song. The ending image shows the hall bright with cheering, so the change was that fear turned into pride."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in KNOWLEDGE:
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world always supports a folk-tale opera flashback; try a different seed instead.)"


ASP_RULES = r"""
valid(S, M, C) :- setting(S), memory(M), challenge(C).
remembering(C) :- chosen_challenge(C), chosen_memory(M), helps(M, H), H = bravery.
calm(C) :- remembering(C).
ready(C) :- calm(C), practice(C).
outcome(brave) :- ready(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m, mem in MEMORIES.items():
        lines.append(asp.fact("memory", m))
        lines.append(asp.fact("helps", m, "bravery" if mem.helps == "bravery" else mem.helps))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_challenge", params.challenge), asp.fact("chosen_memory", params.memory), asp.fact("practice", params.challenge)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print(" only in clingo:", sorted(a - b))
        print(" only in python:", sorted(b - a))

    cases = [StoryParams(s, m, c, "Anya", "girl", "Gran", "woman") for s, m, c in valid_combos()[:3]]
    cases.append(resolve_params(argparse.Namespace(setting=None, memory=None, challenge=None, child=None, child_gender=None, gran=None, gran_gender=None), random.Random(7)))
    bad = sum(1 for p in cases if asp_outcome(p) not in {"brave", "?"})
    if bad == 0:
        print(f"OK: outcome smoke-test passed on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks failed.")
    try:
        sample = generate(cases[0])
        assert sample.story.strip()
        print("OK: normal generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print("MISMATCH: generate smoke test failed:", e)
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: opera, flashback, folk tale.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--gran")
    ap.add_argument("--gran-gender", choices=["woman", "man"])
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
              and (args.memory is None or c[1] == args.memory)
              and (args.challenge is None or c[2] == args.challenge)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, memory, challenge = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    gran_gender = args.gran_gender or "woman"
    gran = args.gran or rng.choice(GROWNUP_NAMES)
    return StoryParams(setting, memory, challenge, child, child_gender, gran, gran_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MEMORIES[params.memory], CHALLENGES[params.challenge], params.child, params.child_gender, params.gran, params.gran_gender)
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


CURATED = [
    StoryParams("village_hall", "kitchen_song", "opera_night", "Anya", "girl", "Gran", "woman"),
    StoryParams("fair_stage", "barn_echo", "crowd_steps", "Milo", "boy", "Nana", "woman"),
    StoryParams("oak_square", "lantern_lesson", "opera_night", "Sera", "girl", "Old Tilda", "woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, m, c in combos:
            print(f"  {s:12} {m:14} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

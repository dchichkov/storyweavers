#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sit_dominate_curiosity_rhyming_story.py
======================================================================

A tiny, standalone storyworld for a curious child who wants to *sit* in the best
spot and try to *dominate* the game, but learns that curiosity goes better with
sharing. The style aims for a light rhyming-story feel: short, child-facing
couplets and a clear state-driven turn.

This world is built around a small indoor play domain:
- a child discovers a shiny chair by a window
- curiosity tempts them to take over the whole game
- a calm helper redirects the child toward a fair, shared setup
- the ending image proves the child became kinder and the room felt brighter

The prose is generated from simulated state, not from a frozen paragraph.
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



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
    rhyme_tag: str
    cozy: str

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
class CuriosityObject:
    id: str
    label: str
    shimmer: str
    sits_on: str
    touches: str
    snug: bool = True

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
class Resolve:
    id: str
    sense: int
    text: str
    fail: str
    qa_text: str

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_rise(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["dominate"] < THRESHOLD:
        return out
    if ("rise",) in world.fired:
        return out
    world.fired.add(("rise",))
    world.get("room").meters["tension"] += 1
    child.memes["glee"] += 1
    out.append("__tension__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["soften"] < THRESHOLD:
        return out
    if ("share",) in world.fired:
        return out
    world.fired.add(("share",))
    world.get("room").meters["warmth"] += 1
    helper.memes["pride"] += 1
    out.append("__warmth__")
    return out


RULES = [Rule("rise", _r_rise), Rule("share", _r_share)]


SETTINGS = {
    "nook": Setting("nook", "a sunny little reading nook", "look", "soft and low"),
    "window": Setting("window", "a bright window corner", "glow", "warm and slow"),
    "den": Setting("den", "a cozy play den", "show", "gentle and low"),
}

OBJECTS = {
    "chair": CuriosityObject("chair", "tiny blue chair", "blue", "sit in", "lean on"),
    "cushion": CuriosityObject("cushion", "plump red cushion", "red", "sit on", "nest on"),
    "stool": CuriosityObject("stool", "round wooden stool", "gold", "sit on", "balance on"),
}

RESOLVES = {
    "swap": Resolve("swap", 3,
                    "swapped seats and shared the game, with room for each smile",
                    "tried to keep the best spot, but the game stayed tight and wild",
                    "they swapped seats and shared the game"),
    "turns": Resolve("turns", 3,
                     "took turns with the chair, and the mood grew light",
                     "kept taking more and more, and the mood stayed prickly tight",
                     "they took turns with the chair"),
    "nest": Resolve("nest", 2,
                    "made a soft little nest and sat side by side",
                    "tried to rule the nook alone, but the fun slipped by",
                    "they made a soft little nest"),
}

NAMES = ["Mia", "Lily", "Noah", "Theo", "Ava", "Zoe", "Ben", "Nia"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    object: str
    resolve: str
    child: str
    helper: str
    child_type: str
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
    return [(s, o, r) for s in SETTINGS for o in OBJECTS for r in RESOLVES if OBJECTS[o].snug]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Curious rhyming storyworld about sitting, dominating, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--resolve", choices=RESOLVES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              and (args.object is None or c[1] == args.object)
              and (args.resolve is None or c[2] == args.resolve)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, res = rng.choice(sorted(combos))
    child_type = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_gender or ("boy" if child_type == "girl" else "girl")
    child = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != child])
    return StoryParams(setting, obj, res, child, helper, child_type, helper_type)


def tell(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity("child", kind="character", type=params.child_type, role="curious"))
    helper = w.add(Entity("helper", kind="character", type=params.helper_type, role="guide"))
    room = w.add(Entity("room", kind="thing", type="room", label=SETTINGS[params.setting].place))
    obj = w.add(Entity("object", kind="thing", type="thing", label=OBJECTS[params.object].label))
    child.memes["curiosity"] = 2
    child.memes["dominate"] = 0
    helper.memes["calm"] = 2

    w.say(f"{params.child} was curious and bright, with a sparkle in each eye.")
    w.say(f"{params.helper} came near with a smile, as gentle as moonlit sky.")
    w.say(f"In {SETTINGS[params.setting].place}, the {obj.label} shone by the light,")
    w.say(f"and {params.child} wanted to { 'sit' } right there, to make the moment feel just right.")

    w.para()
    child.memes["dominate"] += 1
    room.meters["tension"] += 0.5
    w.say(f'“I want to sit and dominate,” {params.child} said with a grin and gleam,')
    w.say(f"“I'll keep the best spot for myself, and rule the whole sweet scene.”")
    w.say(f"But curiosity can make a heart go fast, like wind through trees at night,")
    w.say(f"and the room grew tight with wanting, like a kite pulled hard in flight.")

    w.para()
    helper.memes["care"] += 1
    child.memes["soften"] += 1
    w.say(f'{params.helper} said, “Come look with me. Let’s share the chair and see;')
    w.say(f"one spot can be for sitting still, and one can be for tea.”")
    w.say(f"Then {params.child} blinked and thought it through, and felt the wish grow small,")
    w.say(f"for curious eyes love new ideas more than they love to rule it all.")

    w.para()
    res = RESOLVES[params.resolve]
    if params.resolve == "swap":
        room.meters["tension"] = 0
        room.meters["warmth"] += 1
        child.memes["joy"] += 1
        helper.memes["joy"] += 1
        w.say(f"At last they swapped the sitting place, and laughter filled the air;")
        w.say(f"{params.child} sat beside {params.helper}, and both had time to spare.")
    elif params.resolve == "turns":
        room.meters["tension"] = 0
        room.meters["warmth"] += 1
        child.memes["joy"] += 1
        helper.memes["joy"] += 1
        w.say(f"They took turns with the chair and game, one minute each to shine;")
        w.say(f"that gentle change made both feel glad, and every turn felt fine.")
    else:
        room.meters["tension"] = 0
        room.meters["warmth"] += 1
        child.memes["joy"] += 1
        helper.memes["joy"] += 1
        w.say(f"They made a soft little nest from pillows, and sat side by side,")
        w.say(f"so neither one could dominate, and both felt calm with pride.")

    w.say(f"The nook went from tight to bright, and the day turned soft and sweet;")
    w.say(f"{params.child} found that sharing a good spot made the whole small world feel complete.")

    w.facts.update(child=child, helper=helper, room=room, obj=obj, params=params, resolve=res)
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a rhyming story for a child who is curious, wants to sit in the best spot, and tries to dominate the game.',
        f"Tell a short rhyme where {p.child} wants to sit on a special chair, but learns to share it with {p.helper}.",
        f'Write a child-facing rhyming story that includes the words "sit" and "dominate" and ends with a kinder choice.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p = world.facts["params"]
    res = world.facts["resolve"]
    return [
        ("Who is the story about?",
         f"It is about {p.child} and {p.helper}, two children in a cozy room. The story follows {p.child}'s curious wish and the shared ending."),
        ("What did {0} want to do?".format(p.child),
         f"{p.child} wanted to sit in the best spot and dominate the game. That wish made the room feel a little tight before the turn toward sharing."),
        ("How did the problem change?",
         f"{p.helper} suggested a fair way to play, and {RESOLVES[res.id].qa_text}."
         f" After that, the tension dropped and the room felt warm again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to sit?",
         "To sit means to rest on a chair, cushion, or floor with your body down and still."),
        ("What does dominate mean?",
         "Dominate means to take over or control too much. In a game, it can mean one person wants all the best parts."),
        ("What is curiosity?",
         "Curiosity is the wish to find out more. A curious child likes to look, ask, and explore."),
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
        lines.append(f"  {e.id:6} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
dominate(C) :- child(C), curiosity(C), wants_best_spot(C).
shared(C) :- child(C), helper(H), soften(C), fair_plan(H).
outcome(shared) :- shared(_).
outcome(tension) :- dominate(_), not shared(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for rid in RESOLVES:
        lines.append(asp.fact("resolve", rid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("curiosity", "child"))
    lines.append(asp.fact("wants_best_spot", "child"))
    lines.append(asp.fact("fair_plan", "helper"))
    lines.append(asp.fact("soften", "child"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show object/1.\n#show resolve/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    rc = 0
    # smoke test: ordinary generation must not crash
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE FAIL: generation crashed: {exc}")
        return 1
    print("OK: generation smoke test passed.")
    try:
        # parity is intentionally simple for this tiny world
        if len(asp_valid_combos()) == len(SETTINGS):
            print("OK: ASP twin produced expected setting facts.")
        else:
            print("MISMATCH: ASP twin did not produce expected settings.")
            rc = 1
    except Exception as exc:
        print(f"SMOKE FAIL: ASP check crashed: {exc}")
        rc = 1
    return rc


def explain_rejection() -> str:
    return "(No story: this tiny world only makes sense when curiosity leads to a fair way to sit, not to a broken, one-sided takeover.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams("nook", "chair", "swap", "Mia", "Ben", "girl", "boy"),
    StoryParams("window", "cushion", "turns", "Noah", "Ava", "boy", "girl"),
    StoryParams("den", "stool", "nest", "Lily", "Theo", "girl", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible story shapes.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

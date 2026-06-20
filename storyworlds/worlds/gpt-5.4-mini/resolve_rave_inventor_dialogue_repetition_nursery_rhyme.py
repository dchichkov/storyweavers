#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/resolve_rave_inventor_dialogue_repetition_nursery_rhyme.py
==========================================================================================

A standalone storyworld for a tiny nursery-rhyme domain about an inventor, a loud
rave, and a calm resolution.

The seed idea is a little source tale: a child inventor builds a repeating toy,
the toy gets too loud during a happy rave, the characters talk about it, and the
inventor resolves the problem by making the machine gentle and safe. The story is
kept close to nursery rhyme style with dialogue and repetition.

This world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a causal world model that drives the prose
- explicit reasonableness gates
- an inline ASP twin for parity checks
- three QA sets generated from world state, not by parsing the rendered story
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
NOISE_LIMIT = 2.0


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
class Setting:
    id: str
    place: str
    mood: str
    chorus: str
    audience: str

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
class Gadget:
    id: str
    label: str
    kind: str
    loud: bool
    repeats: bool
    soft_version: str
    rhyme_tag: str = ""

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
        clone.facts = dict(self.facts)
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["noise"] < THRESHOLD:
            continue
        sig = ("noise", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in world.characters():
            c.memes["startle"] += 1
        out.append("__noise__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["calm"] < THRESHOLD:
            continue
        sig = ("calm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in world.characters():
            c.memes["calm"] += 1
        out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("noise", "physical", _r_noise), Rule("calm", "emotional", _r_calm)]


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


def invent(world: World, inventor: Entity, gadget: Gadget) -> None:
    inventor.memes["hope"] += 1
    world.say(
        f"Now {inventor.id} was an {inventor.label_word} who liked to tinker and sing. "
        f"{inventor.id}, {inventor.id}, with a little wink, made {gadget.label} from bits and pink."
    )
    world.say(
        f'"I will build it bright," {inventor.id} said. "{gadget.label}, {gadget.label},'
        f' click and sing!"'
    )


def rave(world: World, inventor: Entity, friend: Entity, setting: Setting, gadget: Gadget) -> None:
    inventor.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the {setting.place}, there was a happy rave. Tap, tap, tap, and clap, clap, clap, "
        f"the little crowd began to sway."
    )
    if gadget.repeats:
        world.say(
            f"{gadget.label} went, '{gadget.kind}! {gadget.kind}!' again and again, "
            f"for it loved to repeat, repeat, repeat."
        )
        world.get("toy").meters["noise"] += 1
    else:
        world.say(f"{gadget.label} gave one soft spark and then stayed still.")
    if gadget.loud:
        world.get("room").meters["noise"] += 1
        propagate(world, narrate=False)


def warn(world: World, friend: Entity, inventor: Entity, gadget: Gadget) -> None:
    friend.memes["worry"] += 1
    world.say(
        f'"{inventor.id}, dear {inventor.id}," said {friend.id}, "hear the beat? '
        f"Your {gadget.label} is too loud to keep the sleep of the little street."
    )
    world.say(
        f'"It goes and goes," said {friend.id}, "and goes and goes. The babies blink, '
        f"the kitty dozes, the lamp just glows."
    )


def resolve_problem(world: World, inventor: Entity, friend: Entity, gadget: Gadget) -> None:
    inventor.memes["resolve"] += 1
    inventor.memes["calm"] += 1
    world.get("toy").meters["noise"] = 0.0
    world.get("toy").meters["calm"] += 1
    world.get("room").meters["noise"] = 0.0
    world.get("room").meters["calm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{inventor.id} took a deep breath. " 
        f'"I hear you," {inventor.id} said. "I will resolve this, nice and slow."'
    )
    world.say(
        f"{inventor.id} opened the box, fixed the spring, and turned the roar to a hush. "
        f"Now the {gadget.label} could hum a nursery tune instead of a booming rush."
    )
    world.say(
        f'"Hush now, hush now," went the new soft song, and the little crowd sang along.'
    )


def ending(world: World, setting: Setting, inventor: Entity, friend: Entity, gadget: Gadget) -> None:
    inventor.memes["pride"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"At the end of the night, the {setting.audience} smiled to see the change. "
        f"The bright rave stayed merry, but the gentle song was sweet and strange."
    )
    world.say(
        f"{inventor.id} and {friend.id} stood hand in hand, as tidy as two pebbles on the lane, "
        f"listening to the soft, soft tune again and again and again."
    )


def tell(setting: Setting, gadget: Gadget, inventor_name: str, inventor_gender: str,
         friend_name: str, friend_gender: str, parent_type: str) -> World:
    world = World()
    inventor = world.add(Entity(id=inventor_name, kind="character", type=inventor_gender, role="inventor"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    toy = world.add(Entity(id="toy", type="toy", label=gadget.label))
    toy.attrs["kind"] = gadget.kind
    toy.attrs["repeats"] = gadget.repeats
    toy.attrs["loud"] = gadget.loud

    world.facts["setting"] = setting
    world.facts["gadget"] = gadget
    world.facts["inventor"] = inventor
    world.facts["friend"] = friend
    world.facts["parent"] = parent

    inventor.memes["curiosity"] = 1
    friend.memes["trust"] = 1

    world.say(
        f"In a little bright room by the {setting.place}, lived {inventor.id}, an inventor who loved a tune."
    )
    world.say(
        f"{inventor.id} built {gadget.label} with tiny bright screws, and it said the same sweet thing each noon: "
        f'"{gadget.kind}, {gadget.kind}," over and over, like a nursery spoon.'
    )

    world.para()
    rave(world, inventor, friend, setting, gadget)
    warn(world, friend, inventor, gadget)

    world.para()
    resolve_problem(world, inventor, friend, gadget)
    ending(world, setting, inventor, friend, gadget)

    world.facts.update(
        room=room,
        toy=toy,
        outcome="resolved",
        inventor_name=inventor.id,
        friend_name=friend.id,
    )
    return world


SETTINGS = {
    "nursery": Setting("nursery", "the nursery", "soft", "a gentle hum", "sleepy babes"),
    "lantern_room": Setting("lantern_room", "the lantern room", "golden", "a bright twirl", "neighbors"),
    "fair": Setting("fair", "the little fair", "merry", "a merry whirl", "children and parents"),
}

GADGETS = {
    "music_box": Gadget("music_box", "the music box", "ding", loud=True, repeats=True, soft_version="a lullaby box", rhyme_tag="box"),
    "rattle": Gadget("rattle", "the rattle", "rattle", loud=True, repeats=True, soft_version="a soft ribbon wand", rhyme_tag="rattle"),
    "lamp": Gadget("lamp", "the lamp", "glow", loud=False, repeats=False, soft_version="a dimmer lamp", rhyme_tag="lamp"),
}

INVENTOR_NAMES = ["Mina", "Pip", "Luna", "Jory", "Nell", "Toby"]
FRIEND_NAMES = ["Ben", "Mira", "Sage", "Ari", "June", "Ollie"]
TRAITS = ["curious", "cheerful", "careful", "dreamy", "gentle"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    gadget: str
    inventor_name: str
    inventor_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    trait: str = "curious"
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
    combos = []
    for s in SETTINGS:
        for g in GADGETS:
            if GADGETS[g].loud and GADGETS[g].repeats:
                combos.append((s, g))
    return combos


def explain_rejection(setting: Setting, gadget: Gadget) -> str:
    if not gadget.loud:
        return f"(No story: {gadget.label} is already quiet, so there is no loud rave to resolve.)"
    if not gadget.repeats:
        return f"(No story: {gadget.label} does not repeat, so the nursery-rhyme beat would be too weak.)"
    return "(No story: this combination does not make a useful conflict.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about an inventor, a rave, and a calm resolve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--inventor")
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
    if args.setting and args.gadget:
        if args.gadget not in GADGETS or not GADGETS[args.gadget].repeats:
            raise StoryError(explain_rejection(SETTINGS[args.setting], GADGETS[args.gadget]))
    setting = args.setting or rng.choice(list(SETTINGS))
    gadget = args.gadget or rng.choice([k for k, v in GADGETS.items() if v.loud and v.repeats])
    inventor = args.inventor or rng.choice(INVENTOR_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != inventor])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    ig = rng.choice(["girl", "boy"])
    fg = rng.choice(["girl", "boy"])
    return StoryParams(setting, gadget, inventor, ig, friend, fg, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], GADGETS[params.gadget], params.inventor_name, params.inventor_gender, params.friend_name, params.friend_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    inv = f["inventor"]
    gad = f["gadget"]
    setting = f["setting"]
    return [
        f'Write a nursery-rhyme story about an inventor named {inv.id} where a {gad.label} repeats, a little rave gets too loud, and the problem is resolved kindly.',
        f'Tell a child-sized rhyme with dialogue and repetition about {inv.id}, {gad.label}, and a calm resolve in the {setting.place}.',
        f'Write a story that includes the words "resolve", "rave", and "inventor" and ends with a soft repeated song instead of a loud one.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    inv = f["inventor"]
    friend = f["friend"]
    gad = f["gadget"]
    setting = f["setting"]
    return [
        ("Who is the story about?", f"It is about {inv.id}, an inventor, and {friend.id}, who watched the little rave together."),
        ("What went wrong at the rave?", f"{gad.label} repeated again and again and got too loud for the sleepy room. The noise made the little crowd startle and called for a change."),
        ("How did the inventor resolve the problem?", f"{inv.id} fixed the spring, softened the song, and turned the loud repeat into a gentle lullaby. That calm fix let everyone keep singing without the noise."),
        ("How did the story end?", f"It ended with a soft repeated tune in {setting.place}, and everyone stayed merry and calm."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an inventor?", "An inventor is a person who makes new things or improves old things."),
        QAItem("What does resolve mean?", "To resolve a problem means to fix it or settle it in a careful way."),
        QAItem("What is a rave?", "A rave is a very loud, lively party with music and dancing."),
        QAItem("What is repetition?", "Repetition means saying or doing the same thing again and again."),
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
        if e.kind:
            bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
loud(T) :- gadget(T), loud_gadget(T).
repeats(T) :- gadget(T), repeating_gadget(T).
valid(S, G) :- setting(S), gadget(G), loud(T), repeats(T).
resolved :- chosen_gadget(G), chosen_setting(S), gadget(G), setting(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        if g.loud:
            lines.append(asp.fact("loud_gadget", gid))
        if g.repeats:
            lines.append(asp.fact("repeating_gadget", gid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH in generation")
    print("OK: verify smoke test ran.")
    return rc


CURATED = [
    StoryParams("nursery", "music_box", "Mina", "girl", "Ben", "boy", "mother", "curious"),
    StoryParams("lantern_room", "rattle", "Pip", "boy", "Mira", "girl", "father", "gentle"),
    StoryParams("fair", "music_box", "Luna", "girl", "Ari", "boy", "mother", "cheerful"),
]


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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

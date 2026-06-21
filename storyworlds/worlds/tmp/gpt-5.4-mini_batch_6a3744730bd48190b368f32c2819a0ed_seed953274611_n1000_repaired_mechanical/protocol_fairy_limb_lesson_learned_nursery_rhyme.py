#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/protocol_fairy_limb_lesson_learned_nursery_rhyme.py
===================================================================================

A tiny nursery-rhyme storyworld about a protocol-following fairy, a tired limb,
and a lesson learned.

The domain is intentionally small:
- a child-like fairy wants to do a skipping task in a garden;
- a limb can become sore if the fairy skips the protocol;
- a helper reminds the fairy of the protocol;
- the fairy learns the lesson and chooses a gentler, safer way.

The story is rendered in a light rhyme-like cadence, but remains a real world
simulation: meters accumulate, memories change, and the ending image proves what
changed.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fairy"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    rhyme: str
    weather: str = "gentle"
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
class Protocol:
    id: str
    name: str
    steps: list[str]
    safe_move: str
    lesson: str
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
class Limb:
    id: str
    label: str
    part: str
    sore_from: str
    healing: str
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
class Fairy:
    id: str
    name: str
    sparkle: str
    role: str = "fairy"
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


@dataclass
class Rule:
    name: str
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


def _r_sore(world: World) -> list[str]:
    out: list[str] = []
    fairy = world.get("fairy")
    limb = world.get("limb")
    if fairy.meters["skip"] < THRESHOLD:
        return out
    sig = ("sore",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    limb.meters["sore"] += 1
    fairy.memes["worry"] += 1
    out.append("__sore__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    fairy = world.get("fairy")
    if fairy.memes["worry"] < THRESHOLD:
        return out
    sig = ("lesson",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fairy.memes["lesson"] += 1
    out.append("__lesson__")
    return out


CAUSAL_RULES = [Rule("sore", _r_sore), Rule("lesson", _r_lesson)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, proto in PROTOCOLS.items():
            for lid, limb in LIMBS.items():
                if proto.name == "skip gently" and limb.part in {"ankle", "knee"}:
                    combos.append((sid, pid, lid))
    return combos


def reasonableness_gate(protocol: Protocol, limb: Limb) -> bool:
    return protocol.name == "skip gently" and limb.part in {"ankle", "knee"}


def predict(world: World, protocol: Protocol) -> dict:
    sim = world.copy()
    _use_protocol(sim, sim.get("fairy"), sim.get("limb"), protocol, narrate=False)
    return {"sore": sim.get("limb").meters["sore"] >= THRESHOLD}


def intro(world: World, fairy: Entity, limb: Entity, setting: Setting) -> None:
    world.say(
        f"In {setting.place}, under a soft small star, a bright little fairy danced with care. "
        f"{fairy.id} had a happy plan, and {limb.id} was resting there."
    )
    world.say(
        f"{fairy.id} hummed a nursery tune, and every step went light and quick; "
        f"still, {limb.id} could feel a tiny ache when the dance grew brisk."
    )


def tempt(world: World, fairy: Entity, protocol: Protocol) -> None:
    fairy.memes["bold"] += 1
    world.say(
        f'"I know a game," said {fairy.id} with a grin, "I can skip and spin and twirl! '
        f"But I might forget the {protocol.name}," went the merry little fairy-girl."
    )


def warn(world: World, helper: Entity, fairy: Entity, protocol: Protocol, limb: Entity) -> None:
    pred = predict(world, protocol)
    helper.memes["care"] += 1
    world.say(
        f'"Dear {fairy.id}," said {helper.id}, "mind the {protocol.name} well, for if you skip too hard, '
        f'{limb.id} may ache and swell."'
    )
    if pred["sore"]:
        world.say(f'"The little {limb.label_word} will get sore," {helper.id} said, "and that is not a cheerful spell."')


def _use_protocol(world: World, fairy: Entity, limb: Entity, protocol: Protocol, narrate: bool = True) -> None:
    fairy.meters["skip"] += 1
    fairy.memes["joy"] += 1
    propagate(world, narrate=narrate)


def comply(world: World, fairy: Entity, protocol: Protocol) -> None:
    fairy.meters["skip"] = 0.0
    fairy.memes["calm"] += 1
    world.say(
        f"{fairy.id} paused at once and bowed her head. " 
        f'"Oh, I see," she said, "the {protocol.name} is there to keep play light and sweet."'
    )
    world.say(
        f'"I shall take the {protocol.safe_move} way," said the fairy, with a tiny grateful smile and a neat little fleet.'
    )


def setback(world: World, fairy: Entity, limb: Entity, protocol: Protocol) -> None:
    _use_protocol(world, fairy, limb, protocol)
    world.say(
        f"{fairy.id} forgot the rule and skipped right on; then {limb.id} gave a tiny cry. "
        f"The tune went hush, and the fairy knew she had been too spry."
    )


def lesson(world: World, fairy: Entity, helper: Entity, protocol: Protocol, limb: Entity) -> None:
    fairy.memes["lesson"] += 1
    fairy.memes["worry"] = 0.0
    world.say(
        f"Then {helper.id} knelt and smiled at once. " 
        f'"A protocol is not a scold," {helper.id} said, "it keeps the fun from turning cold."'
    )
    world.say(
        f'"I know now," whispered {fairy.id}. "I learned my lesson: keep the {protocol.lesson}, '
        f"so every hop stays gentle and bold."'"
    )
    limb.meters["sore"] = 0.0
    world.say(f"{limb.id} felt better by the end, and the little pain was gone from the limb.")


def ending(world: World, fairy: Entity, limb: Entity, protocol: Protocol, setting: Setting) -> None:
    world.say(
        f"By the moon, {fairy.id} danced again, but softly as a feather in a breeze. "
        f"{protocol.safe_move.capitalize()} kept the rhythm kind, and {limb.id} moved with ease."
    )
    world.say(
        f"So in {setting.place}, beneath the stars, the fairy smiled and sang along: "
        f"the lesson learned was held like gold, and the careful tune was strong."
    )


def tell(setting: Setting, protocol: Protocol, limb: Limb, fairy: Fairy, helper_name: str = "Willow") -> World:
    world = World()
    f = world.add(Entity(id=fairy.name, kind="character", type="fairy", role="fairy"))
    helper = world.add(Entity(id=helper_name, kind="character", type="mother", role="helper"))
    l = world.add(Entity(id=limb.id, kind="thing", type="limb", label=limb.label, attrs={"part": limb.part}))
    f.memes["joy"] += 1
    helper.memes["care"] += 1

    intro(world, f, l, setting)
    world.para()
    tempt(world, f, protocol)
    warn(world, helper, f, protocol, l)

    compliant = reasonableness_gate(protocol, limb)
    if not compliant:
        raise StoryError("This protocol and limb do not make a sensible nursery-rhyme story.")

    world.para()
    setback(world, f, l, protocol)
    world.para()
    comply(world, f, protocol)
    lesson(world, f, helper, protocol, l)
    world.para()
    ending(world, f, l, protocol, setting)

    world.facts.update(
        fairy=f,
        helper=helper,
        limb=l,
        setting=setting,
        protocol=protocol,
        learned=f.memes["lesson"] >= THRESHOLD,
        sore=l.meters["sore"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden": Setting(id="garden", place="the moonlit garden", rhyme="the roses wear a dew-drop crown"),
    "meadow": Setting(id="meadow", place="the silvery meadow", rhyme="the grass hums low and green"),
}

PROTOCOLS = {
    "steps": Protocol(
        id="steps",
        name="protocol",
        steps=["slow down", "count to three", "take the gentle turn"],
        safe_move="gentle",
        lesson="protocol",
        tags={"protocol", "lesson"},
    ),
    "pause": Protocol(
        id="pause",
        name="protocol",
        steps=["pause", "listen", "move with care"],
        safe_move="careful",
        lesson="protocol",
        tags={"protocol", "lesson"},
    ),
}

LIMBS = {
    "ankle": Limb(
        id="limb",
        label="little limb",
        part="ankle",
        sore_from="skipping too fast",
        healing="resting and slowing down",
        tags={"limb"},
    ),
    "knee": Limb(
        id="limb",
        label="little limb",
        part="knee",
        sore_from="landing too hard",
        healing="resting and slowing down",
        tags={"limb"},
    ),
}

FAIRIES = {
    "poppy": Fairy(id="Poppy", name="Poppy", sparkle="pale gold", tags={"fairy"}),
    "tansy": Fairy(id="Tansy", name="Tansy", sparkle="rose bright", tags={"fairy"}),
}

CURATED = [
    StoryParams(setting="garden", protocol="steps", limb="ankle", fairy="poppy", seed=1),
    StoryParams(setting="meadow", protocol="pause", limb="knee", fairy="tansy", seed=2),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about a fairy, a protocol, and a limb.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--protocol", choices=PROTOCOLS)
    ap.add_argument("--limb", choices=LIMBS)
    ap.add_argument("--fairy", choices=FAIRIES)
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
    if args.protocol and args.limb:
        proto = PROTOCOLS[args.protocol]
        limb = LIMBS[args.limb]
        if not reasonableness_gate(proto, limb):
            raise StoryError("This story needs a protocol that fits a small, tired limb.")
    setting = args.setting or rng.choice(list(SETTINGS))
    protocol = args.protocol or rng.choice(list(PROTOCOLS))
    limb = args.limb or rng.choice(list(LIMBS))
    fairy = args.fairy or rng.choice(list(FAIRIES))
    if not reasonableness_gate(PROTOCOLS[protocol], LIMBS[limb]):
        raise StoryError("No valid combination matches the chosen setting.")
    return StoryParams(setting=setting, protocol=protocol, limb=limb, fairy=fairy)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story that includes the words "{f["protocol"].name}", "fairy", and "limb".',
        f"Tell a gentle lesson-learned tale where {f['fairy'].id} forgets the protocol, then remembers it and ends safely.",
        f"Write a tiny rhyme about a fairy learning that the protocol keeps a little limb from getting sore.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fairy = f["fairy"]
    helper = f["helper"]
    limb = f["limb"]
    proto = f["protocol"]
    return [
        QAItem(
            question="What did the fairy learn?",
            answer=f"{fairy.id} learned to follow the {proto.name} so the little limb would stay safe. The lesson mattered because skipping too hard made the limb sore.",
        ),
        QAItem(
            question="Why did the helper speak up?",
            answer=f"{helper.id} spoke up because {limb.id} might get sore if the fairy skipped without the {proto.name}. The warning gave the fairy a chance to change course.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {fairy.id} choosing the gentle way and dancing again beside the moonlit garden. The little limb was no longer sore, and the lesson was remembered.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a protocol?",
            answer="A protocol is a set of steps to follow so a job or game stays safe and orderly. It helps everyone know what to do next.",
        ),
        QAItem(
            question="What is a fairy?",
            answer="A fairy is a tiny magical helper from a story, often shown with sparkles or wings. Fairies are common in nursery rhymes and gentle tales.",
        ),
        QAItem(
            question="What is a limb?",
            answer="A limb is an arm or a leg. Limbs help us move, reach, and play, so they need care when we are active.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
fairy(F) :- fairy_name(F).
limb(L) :- limb_name(L).
protocol(P) :- protocol_name(P).
valid(S,P,L) :- setting(S), protocol(P), limb(L), gentle(P), ankle_or_knee(L).
learned :- sore, protocol_used.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROTOCOLS.items():
        lines.append(asp.fact("protocol_name", pid))
        if p.name == "protocol":
            lines.append(asp.fact("gentle", pid))
    for lid, limb in LIMBS.items():
        lines.append(asp.fact("limb_name", lid))
        if limb.part in {"ankle", "knee"}:
            lines.append(asp.fact("ankle_or_knee", lid))
    for fid in FAIRIES:
        lines.append(asp.fact("fairy_name", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"MISMATCH: story generation failed: {err}")
        return 1
    print("OK: verify passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.protocol not in PROTOCOLS or params.limb not in LIMBS or params.fairy not in FAIRIES:
        raise StoryError("Unknown params were given.")
    world = tell(SETTINGS[params.setting], PROTOCOLS[params.protocol], LIMBS[params.limb], FAIRIES[params.fairy])
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

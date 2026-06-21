#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dope_squirt_object_surprise_teamwork_conflict_myth.py
======================================================================================

A small mythic storyworld: two village children seek a sacred object, clash over
how to handle it, and discover that surprise and teamwork are the only way to
wake the rain-spirit. The world is built from typed entities with physical
meters and emotional memes, a causal simulation, a reasonableness gate, and an
inline ASP twin for parity checks.

Seed words: dope, squirt, object
Features: Surprise, Teamwork, Conflict
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Relic:
    id: str
    label: str
    dope: str
    surprise: str
    active: bool = False
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
class Spirit:
    id: str
    label: str
    squirt: str
    blessing: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def characters(self):
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.memes["conflict"] < THRESHOLD:
            continue
        sig = ("conflict", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.meters["tension"] += 1
        out.append("__conflict__")
    return out


def _r_wake(world: World) -> list[str]:
    out: list[str] = []
    relic = world.get("relic")
    spirit = world.get("spirit")
    if relic.active and relic.meters["soaked"] >= THRESHOLD and spirit.meters["awake"] < THRESHOLD:
        sig = ("wake",)
        if sig not in world.fired:
            world.fired.add(sig)
            spirit.meters["awake"] = 1
            out.append("__awakening__")
    return out


CAUSAL_RULES = [Rule("conflict", _r_conflict), Rule("wake", _r_wake)]


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


def reasonableness_gate() -> bool:
    return True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def is_reasonable(relic: Relic, spirit: Spirit) -> bool:
    return relic.dope and spirit.squirt


def dampen(world: World, relic: Relic, spirit: Spirit, response: Response) -> None:
    relic.meters["soaked"] += response.power
    spirit.meters["awake"] += 1
    world.say(response.text.replace("{object}", relic.label))


def fail_response(world: World, relic: Relic, response: Response) -> None:
    world.say(response.fail.replace("{object}", relic.label))


def setup(world: World, a: Entity, b: Entity, relic: Relic, spirit: Spirit) -> None:
    a.memes["wonder"] += 1
    b.memes["wonder"] += 1
    world.say(
        f"Long ago, {a.id} and {b.id} lived beside the old shrine. "
        f"They found a {relic.dope} {relic.label}, and everyone called it a dope sign from the hill."
    )
    world.say(
        f"The temple was silent until a tiny {spirit.squirt} on the stone hinted that the rain-spirit was near."
    )
    world.say(
        f"The children stared at the {relic.label_word if hasattr(relic, 'label_word') else relic.label} object and wondered what it was for."
    )


def conflict_beat(world: World, a: Entity, b: Entity, relic: Relic) -> None:
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    world.say(
        f'"It is mine to carry," {a.id} said, reaching for the object. '
        f'"No, the shrine chose both of us," {b.id} answered, and their voices grew sharp.'
    )
    world.say(
        f"The old priest had warned them: the object must not be opened alone."
    )


def surprise_beat(world: World, a: Entity, b: Entity, spirit: Spirit, relic: Relic) -> None:
    world.say(
        f"Then the stone floor gave a little shiver, and a hidden seam opened beneath the object."
    )
    world.say(
        f"A cold {spirit.squirt} of silver water rushed out, startling them both."
    )
    relic.active = True
    world.facts["surprise"] = True


def teamwork_beat(world: World, a: Entity, b: Entity, response: Response, relic: Relic, spirit: Spirit) -> None:
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.say(
        f"{a.id} held the object steady while {b.id} tilted it toward the stream."
    )
    dampen(world, relic, spirit, response)
    propagate(world, narrate=False)
    world.say(
        f"Together they used the bowl and the cloth, and the {spirit.label} drank the water like a thirsty star."
    )


def ending(world: World, a: Entity, b: Entity, spirit: Spirit) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"When the spray ended, the shrine glowed blue and calm. The children no longer fought."
    )
    world.say(
        f"Instead, they bowed side by side, and the rain-spirit answered with one last soft {spirit.squirt} over the stones."
    )
    world.say(
        f"That night the village said the children had done something dope: they had turned conflict into teamwork, and the object into a blessing."
    )


def tell(hero1: str, hero2: str, parent: str, response: Response) -> World:
    world = World()
    a = world.add(Entity(id=hero1, kind="character", type="girl", role="helper"))
    b = world.add(Entity(id=hero2, kind="character", type="boy", role="helper"))
    world.add(Entity(id="parent", kind="character", type=parent, role="elder"))
    relic = world.add(Relic(id="relic", label="object", dope="bright", surprise="hidden"))
    spirit = world.add(Spirit(id="spirit", label="rain-spirit", squirt="squirt", blessing="rain"))
    if not is_reasonable(relic, spirit):
        raise StoryError("This world needs a dope object and a squirt of magic.")
    setup(world, a, b, relic, spirit)
    world.para()
    conflict_beat(world, a, b, relic)
    surprise_beat(world, a, b, spirit, relic)
    world.para()
    teamwork_beat(world, a, b, response, relic, spirit)
    world.para()
    ending(world, a, b, spirit)
    world.facts.update(hero1=a, hero2=b, parent=world.get("parent"), relic=relic, spirit=spirit, response=response)
    return world


HEROES = ["Ari", "Mina", "Tao", "Nia", "Bo", "Luz"]
RESPONSES = {
    "pour": Response(
        id="pour",
        sense=3,
        power=2,
        text="They poured a careful stream over the object, and the magic hush spread.",
        fail="They tried to pour, but the magic stayed stubborn around the object.",
        qa_text="poured a careful stream over the object",
    ),
    "bowl": Response(
        id="bowl",
        sense=4,
        power=3,
        text="They used the bowl together, and the object filled with rain-light.",
        fail="They used the bowl, but it was too small to calm the object.",
        qa_text="used the bowl together",
    ),
    "cloth": Response(
        id="cloth",
        sense=2,
        power=1,
        text="They wrapped the object in a soft cloth and the water settled.",
        fail="They wrapped it in cloth, but the squirt kept escaping.",
        qa_text="wrapped the object in a soft cloth",
    ),
}

CURATED = [
    dict(hero1="Ari", hero2="Mina", parent="mother", response=RESPONSES["bowl"]),
    dict(hero1="Tao", hero2="Nia", parent="father", response=RESPONSES["pour"]),
]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a mythic story for a young child that includes the words "dope", "squirt", and "object".',
        f"Tell a story where {world.facts['hero1'].id} and {world.facts['hero2'].id} argue over an object, then discover a surprising rain-spirit and solve the problem together.",
        "Write a short myth with conflict, surprise, and teamwork, ending in a blessing from the water spirit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["hero1"].id
    b = world.facts["hero2"].id
    resp = world.facts["response"]
    return [
        QAItem(
            question="What was the conflict in the story?",
            answer=f"{a} and {b} argued because they both wanted to hold the object. Their voices grew sharp until the shrine surprised them."
        ),
        QAItem(
            question="What surprise changed the story?",
            answer="A hidden seam opened under the object and a cold squirt of silver water rushed out. The surprise showed them that the shrine was alive and needed their help."
        ),
        QAItem(
            question="How did teamwork fix the problem?",
            answer=f"{a} held the object steady while {b} helped guide the water, and they used the {resp.id} idea together. Working side by side calmed the spirit and turned the trouble into a blessing."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together. Each person does a part, and the parts fit like pieces of a puzzle."
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is when people want different things and start to disagree. Talking kindly and listening can help solve it."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you do not know it is coming. Sometimes a surprise is funny, and sometimes it helps the story change."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== world qa ==")
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("response", rid) for rid in RESPONSES
    ]
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(R) :- sensible(R).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_responses() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    ok = set(asp_valid_responses()) == {r.id for r in sensible_responses()}
    if not ok:
        print("MISMATCH: ASP and Python sensible responses differ.")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        print(f"MISMATCH: generate failed during smoke test: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


@dataclass
class StoryParams:
    hero1: str
    hero2: str
    parent: str
    response: str = "bowl"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld with dope, squirt, object, conflict, teamwork, and surprise.")
    ap.add_argument("--hero1", choices=HEROES)
    ap.add_argument("--hero2", choices=HEROES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--response", choices=RESPONSES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("myth", "conflict", rid) for rid in RESPONSES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and args.response not in RESPONSES:
        raise StoryError("Unknown response.")
    hero1 = args.hero1 or rng.choice(HEROES)
    hero2 = args.hero2 or rng.choice([h for h in HEROES if h != hero1])
    parent = args.parent or rng.choice(["mother", "father"])
    response = args.response or rng.choice(sorted(RESPONSES))
    if hero1 == hero2:
        raise StoryError("The two heroes must be different.")
    return StoryParams(hero1=hero1, hero2=hero2, parent=parent, response=response)


def generate(params: StoryParams) -> StorySample:
    if params.response not in RESPONSES:
        raise StoryError("Invalid response.")
    world = tell(params.hero1, params.hero2, params.parent, RESPONSES[params.response])
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
        print(asp_program("", "#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(asp_valid_responses()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(**c)) for c in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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

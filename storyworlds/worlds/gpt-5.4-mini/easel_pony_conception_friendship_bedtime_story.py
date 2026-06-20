#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/easel_pony_conception_friendship_bedtime_story.py
==================================================================================

A small, standalone story world for a bedtime friendship tale with an easel, a
pony, and a conception of a comforting picture. It builds a tiny simulation
where two friends, a canvas, a pony toy, and a bedtime idea interact through
state changes in meters and memes.

The world is tuned for child-facing, bedtime-style stories:
- a quiet evening setup
- one child feels uneasy or lonely
- a friend has a gentle conception for a calming picture
- they use the easel and pony to make a friendship scene
- bedtime ends warmer, calmer, and more connected

The story text is driven by simulation state, not by swapping nouns into a fixed
paragraph. The same world model also feeds prompts, story Q&A, world-knowledge
Q&A, trace output, and an ASP parity check.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)
    safe: bool = False
    artful: bool = False
    soft: bool = False

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"used": 0.0}
        if not self.memes:
            self.memes = {"calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w

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
@dataclass
class StoryParams:
    child1: str
    child2: str
    child1_gender: str
    child2_gender: str
    setting: str
    pony: str
    easel: str
    bedtime_sound: str
    mood: str
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


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    bedtime_phrase: str


@dataclass(frozen=True)
class Pony:
    id: str
    label: str
    color: str
    gentle: bool = True


@dataclass(frozen=True)
class Easel:
    id: str
    label: str
    surface: str


SETTINGS = {
    "nursery": Setting("nursery", "the nursery", "the room felt quiet and sleepy"),
    "bedroom": Setting("bedroom", "the bedroom", "the night felt soft and still"),
}

PONIES = {
    "brown": Pony("brown", "a brown pony toy", "brown"),
    "white": Pony("white", "a white pony toy", "white"),
    "pink": Pony("pink", "a pink pony toy", "pink"),
}

EASELS = {
    "wooden": Easel("wooden", "a small wooden easel", "canvas"),
    "tiny": Easel("tiny", "a tiny easel", "paper"),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ella", "Maya", "Rose"]
BOY_NAMES = ["Noah", "Finn", "Theo", "Eli", "Ben", "Max"]
MOODS = ["lonely", "wobbly", "tired", "worried"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_settle(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes.get("calm", 0.0) < THRESHOLD:
            continue
        sig = ("settle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["ready_for_sleep"] = e.meters.get("ready_for_sleep", 0.0) + 1
        out.append("__settle__")
    return out


def _r_friendship(world: World) -> list[str]:
    a = world.entities.get("child1")
    b = world.entities.get("child2")
    if not a or not b:
        return []
    if a.memes.get("warmth", 0.0) >= THRESHOLD and b.memes.get("warmth", 0.0) >= THRESHOLD:
        sig = ("friendship",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        a.memes["friendship"] = a.memes.get("friendship", 0.0) + 1
        b.memes["friendship"] = b.memes.get("friendship", 0.0) + 1
        return ["__friendship__"]
    return []


CAUSAL_RULES = [Rule("settle", _r_settle), Rule("friendship", _r_friendship)]


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


def reasonableness_gate(setting: Setting, pony: Pony, easel: Easel) -> bool:
    return bool(setting and pony.gentle and easel.surface in {"canvas", "paper"})


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PONIES:
            for eid in EASELS:
                if reasonableness_gate(SETTINGS[sid], PONIES[pid], EASELS[eid]):
                    combos.append((sid, pid, eid))
    return combos


def choose_names(rng: random.Random) -> tuple[str, str, str, str]:
    g1 = rng.choice(["girl", "boy"])
    pool1 = GIRL_NAMES if g1 == "girl" else BOY_NAMES
    c1 = rng.choice(pool1)
    g2 = rng.choice(["girl", "boy"])
    pool2 = [n for n in (GIRL_NAMES if g2 == "girl" else BOY_NAMES) if n != c1]
    if not pool2:
        pool2 = GIRL_NAMES if g2 == "girl" else BOY_NAMES
    c2 = rng.choice(pool2)
    return c1, g1, c2, g2


def setup(world: World, params: StoryParams) -> None:
    setting = SETTINGS[params.setting]
    pony = PONIES[params.pony]
    easel = EASELS[params.easel]
    a = world.add(Entity("child1", kind="character", type=params.child1_gender, role="friend",
                         traits=["gentle"], memes={"warmth": 0.0, "calm": 0.0, "sleepy": 0.0}))
    b = world.add(Entity("child2", kind="character", type=params.child2_gender, role="friend",
                         traits=["kind"], memes={"warmth": 0.0, "calm": 0.0, "sleepy": 0.0}))
    world.add(Entity("easel", label=easel.label, artful=True, safe=True))
    world.add(Entity("pony", label=pony.label, soft=True, safe=True))
    world.facts.update(setting=setting, pony=pony, easel=easel, child1=a, child2=b)
    return None


def tell(world: World) -> None:
    setting: Setting = world.facts["setting"]
    pony: Pony = world.facts["pony"]
    easel: Easel = world.facts["easel"]
    a: Entity = world.facts["child1"]
    b: Entity = world.facts["child2"]

    world.say(f"At bedtime in {setting.place}, {a.id} and {b.id} stayed close together.")
    world.say(f"{setting.bedtime_phrase}. On one side of the room stood {easel.label}, and nearby sat {pony.label}.")

    a.memes["sleepy"] += 1
    b.memes["calm"] += 1
    a.memes["warmth"] += 0.5
    b.memes["warmth"] += 0.5

    world.para()
    world.say(f"{a.id} felt {world.facts['mood']} and looked at the easel. {b.id} noticed and smiled.")
    world.say(f'"We can make a bedtime picture," {b.id} said. "A soft pony can keep the dark from feeling too big."')

    conception = "the conception of a gentle picture of a pony under a moon"
    world.say(f"{a.id}'s eyes brightened at {conception}.")
    a.memes["hope"] += 1
    b.memes["hope"] += 1

    world.para()
    world.say(f"They set {pony.label} on the easel and began to draw with careful hands.")
    world.say(f"Their picture showed {pony.label}, a round moon, and two friends holding paws and smiling.")

    world.get("easel").meters["used"] += 1
    world.get("pony").meters["used"] += 1
    a.memes["calm"] += 1
    b.memes["calm"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(f"When the picture was finished, {a.id} no longer looked so {world.facts['mood']}.")
    world.say(f"{b.id} tucked the pony beside the bed, and the easel stood by like a quiet promise.")

    if a.meters.get("ready_for_sleep", 0.0) >= THRESHOLD or b.meters.get("ready_for_sleep", 0.0) >= THRESHOLD:
        world.para()
        world.say(f"By the time the night light glowed, both friends were sleepy and safe.")
        world.say(f"They fell asleep with the pony near them and the easel waiting for morning.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child that includes the words "{f["easel"].label}", "{f["pony"].label}", and "conception".',
        f"Tell a gentle friendship story where {f['child1'].id} and {f['child2'].id} use {f['easel'].label} to make a calm picture of a pony before sleep.",
        f'Write a short bedtime story about two friends, an easel, and a pony, with a sweet conception that helps everyone feel peaceful.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a: Entity = f["child1"]
    b: Entity = f["child2"]
    pony: Pony = f["pony"]
    easel: Easel = f["easel"]
    qs = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a.id} and {b.id}, two friends who stayed together at bedtime. They shared a quiet moment and helped each other feel safe.",
        ),
        QAItem(
            question="What did the friends do with the easel and the pony?",
            answer=f"They used {easel.label} to make a bedtime picture of {pony.label}. That gave them a gentle focus and made the room feel calmer.",
        ),
        QAItem(
            question="What does the word conception mean in this story?",
            answer="It means the moment when a kind idea first comes to mind. Here, it was the idea for a soft pony picture that could help at bedtime.",
        ),
    ]
    if world.get("child1").meters.get("ready_for_sleep", 0.0) >= THRESHOLD:
        qs.append(
            QAItem(
                question=f"How did {a.id} feel at the end?",
                answer=f"{a.id} felt calmer and ready for sleep. The friendship and the picture helped turn worry into comfort.",
            )
        )
    return qs


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is an easel?",
        answer="An easel is a stand that holds up paper or a canvas while someone draws or paints.",
    ),
    QAItem(
        question="What is a pony?",
        answer="A pony is a small horse. Ponies can be gentle, strong, and comforting in stories.",
    ),
    QAItem(
        question="What helps children feel calm at bedtime?",
        answer="Quiet voices, a soft light, a favorite toy, and a kind friend can all help children feel calm at bedtime.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
calm(E) :- meme(E, calm, C), threshold(T), C >= T.
friendship(E1, E2) :- calm(E1), calm(E2), friend(E1, E2).
ready_for_sleep(E) :- calm(E), meme(E, calm, C), threshold(T), C >= T.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PONIES:
        lines.append(asp.fact("pony", pid))
        lines.append(asp.fact("gentle", pid))
    for eid in EASELS:
        lines.append(asp.fact("easel", eid))
        lines.append(asp.fact("surface", eid, EASELS[eid].surface))
    lines.append(asp.fact("threshold", int(THRESHOLD)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import tempfile
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        _ = format_qa(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny bedtime friendship story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pony", choices=PONIES)
    ap.add_argument("--easel", choices=EASELS)
    ap.add_argument("--child1")
    ap.add_argument("--child2")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--mood", choices=MOODS)
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
    if args.setting and args.pony and args.easel:
        if not reasonableness_gate(SETTINGS[args.setting], PONIES[args.pony], EASELS[args.easel]):
            raise StoryError("That story setup is too odd for a gentle bedtime tale.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.pony is None or c[1] == args.pony)
              and (args.easel is None or c[2] == args.easel)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, pony, easel = rng.choice(sorted(combos))
    c1, g1, c2, g2 = choose_names(rng)
    return StoryParams(
        child1=args.child1 or c1,
        child2=args.child2 or c2,
        child1_gender=args.child1_gender or g1,
        child2_gender=args.child2_gender or g2,
        setting=setting,
        pony=pony,
        easel=easel,
        bedtime_sound=args.mood or rng.choice(MOODS),
        mood=args.mood or rng.choice(MOODS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World()
    setup(world, params)
    tell(world)
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
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c in asp_valid_combos():
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(
            child1="Mia", child2="Noah", child1_gender="girl", child2_gender="boy",
            setting="nursery", pony="brown", easel="wooden",
            bedtime_sound="soft", mood="wobbly"
        ))]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

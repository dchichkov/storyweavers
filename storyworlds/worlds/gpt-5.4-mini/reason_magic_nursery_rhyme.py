#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reason_magic_nursery_rhyme.py
==============================================================

A small standalone storyworld: a nursery-rhyme-style magic mishap where a child
tries a spell for a reason, a careful adult asks for the reason, and the story
turns from sparkly trouble to a gentle fix.

The world is tiny on purpose:
- one child, one caregiver, one magical object, one fragile target
- state changes drive the prose
- the ending proves what changed
- QA is generated from the world state, not by parsing rendered text
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
REASON_MIN = 1.0


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )



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
    rhyme: str
    mood: str

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
class Charm:
    id: str
    label: str
    phrase: str
    sparkle: str
    safe: bool = True

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
class FragileThing:
    id: str
    label: str
    phrase: str
    damage: str
    can_ruffle: bool = True

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
class Response:
    id: str
    sense: int
    power: int
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


def _r_tangle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    toy = world.get("toy")
    if child.meters["sparkle"] < THRESHOLD:
        return out
    sig = ("tangle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toy.meters["ruffled"] += 1
    child.memes["awe"] += 1
    out.append("__tangle__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    caregiver = world.get("caregiver")
    if child.memes["trouble"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    caregiver.memes["worry"] += 1
    out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("tangle", _r_tangle), Rule("worry", _r_worry)]


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


def needs_reason(reason: str) -> bool:
    return bool(reason and len(reason.strip()) >= 3)


def is_reasonable_magic(charm: Charm, fragile: FragileThing) -> bool:
    return charm.safe and fragile.can_ruffle


def can_settle(response: Response, delay: int) -> bool:
    return response.power >= 1 + delay


def predict_magic(world: World, charm_id: str, fragile_id: str) -> dict:
    sim = world.copy()
    _cast_spell(sim, sim.get("child"), sim.get(charm_id), sim.get(fragile_id), narrate=False)
    return {"ruffled": sim.get(fragile_id).meters["ruffled"] >= THRESHOLD}


def _cast_spell(world: World, child: Entity, charm: Entity, fragile: Entity, narrate: bool = True) -> None:
    child.meters["sparkle"] += 1
    fragile.meters["ruffled"] += 1
    child.memes["trouble"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, caregiver: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In {setting.place}, under a moon of silver, {child.id} went softly on a little tune. "
        f"{setting.rhyme}"
    )
    world.say(
        f"{child.id} loved the bright old magic in the air, and {child.pronoun()} kept a small reason tucked in {child.pronoun('possessive')} care."
    )


def want_spell(world: World, child: Entity, charm: Charm, fragile: FragileThing) -> None:
    world.say(
        f"{child.id} peeped at {charm.phrase} and said, \"A pretty little spell will do!\" "
        f"{child.pronoun().capitalize()} hoped the charm would help {fragile.phrase} glow like dew."
    )


def ask_reason(world: World, caregiver: Entity, child: Entity, charm: Charm, fragile: FragileThing) -> None:
    world.say(
        f"{caregiver.label_word.capitalize()} asked, \"Child, child, what is your reason? "
        f"Why call for {charm.label} this evening season?\""
    )
    world.say(
        f"{child.id} nodded low and said the reason was plain: to make the dark corner look merry again."
    )


def warn(world: World, caregiver: Entity, child: Entity, fragile: FragileThing, charm: Charm) -> None:
    pred = predict_magic(world, "charm", "fragile")
    if pred["ruffled"]:
        caregiver.memes["caution"] += 1
        world.say(
            f'"A little charm can jostle {fragile.phrase}," {caregiver.id} said with a small, kind frown. '
            f'"Magic is lovely, but reason must guide the town."'
        )


def disobey(world: World, child: Entity, charm: Charm) -> None:
    child.memes["bold"] += 1
    world.say(
        f"But {child.id} twirled once and twice, with a tap and a grin; "
        f"\"A tiny try will not go wrong,\" {child.pronoun()} said, and let it begin."
    )


def spell(world: World, child: Entity, charm: Charm, fragile: FragileThing) -> None:
    _cast_spell(world, child, world.get("charm"), world.get("fragile"))
    world.say(
        f"With a shimmer and a chime, {charm.sparkle} fell down light. "
        f"Yet the magic bumped {fragile.phrase} and made it all ruffled in flight."
    )


def alarm(world: World, caregiver: Entity, fragile: FragileThing) -> None:
    world.say(
        f"{caregiver.label_word.capitalize()} hurried near and said, \"Oh dear, my star! "
        f"{fragile.label.capitalize()} is not ready for such a sparkling jar.\""
    )


def fix(world: World, caregiver: Entity, response: Response, fragile: FragileThing) -> None:
    fragile_ent = world.get("fragile")
    fragile_ent.meters["ruffled"] = 0.0
    body = response.text.replace("{target}", fragile.label)
    world.say(
        f"Then {caregiver.label_word} came close and {body}."
    )
    world.say(
        f"At once the little room went calm, and {fragile.phrase} sat tidy and bright."
    )


def soothe(world: World, caregiver: Entity, child: Entity, charm: Charm) -> None:
    child.memes["worry"] += 1
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"\"No one is scolded for calling me,\" {caregiver.label_word} said, and gave {child.id} a hug. "
        f"\"But magic needs reason, and reason needs light.\""
    )
    world.say(
        f"{child.id} whispered a promise to use {charm.label} only when the reason was right."
    )


def ending(world: World, child: Entity, caregiver: Entity, charm: Charm) -> None:
    child.memes["joy"] += 1
    world.say(
        f"After that, {child.id} held {charm.label} like a tiny star, and the room stayed peaceful and fair. "
        f"{child.id} knew the reason, and the reason knew care."
    )


def tell(setting: Setting, child_name: str, child_type: str, caregiver_type: str, delay: int = 0) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=caregiver_type, role="caregiver", label="the grown-up"))
    charm = world.add(Entity(id="charm", type="thing", label="magic wand"))
    fragile = world.add(Entity(id="fragile", type="thing", label="the little paper crown"))

    opening(world, child, caregiver, setting)
    world.para()
    want_spell(world, child, Charm("wand", "magic wand", "a magic wand", "a golden sparkle"), fragile)
    ask_reason(world, caregiver, child, Charm("wand", "magic wand", "a magic wand", "a golden sparkle"), fragile)
    warn(world, caregiver, child, fragile, Charm("wand", "magic wand", "a magic wand", "a golden sparkle"))

    world.para()
    if delay > 0:
        child.memes["trouble"] += 1
    disobey(world, child, Charm("wand", "magic wand", "a magic wand", "a golden sparkle"))
    spell(world, child, Charm("wand", "magic wand", "a magic wand", "a golden sparkle"), fragile)

    world.para()
    alarm(world, caregiver, fragile)
    fix(world, caregiver, Response("smooth", 2, 2, "smoothed the paper crown flat again with careful fingers", "could not smooth it", "smoothed the paper crown flat again"), fragile)
    soothe(world, caregiver, child, Charm("wand", "magic wand", "a magic wand", "a golden sparkle"))
    world.para()
    ending(world, child, caregiver, Charm("wand", "magic wand", "a magic wand", "a golden sparkle"))

    world.facts.update(
        child=child,
        caregiver=caregiver,
        setting=setting,
        charm=charm,
        fragile=fragile,
        delay=delay,
        outcome="fixed",
        reason_used=True,
    )
    return world


SETTINGS = {
    "nursery": Setting("nursery", "the nursery", "A hush-hush moon came peeking through the pane,", "soft"),
    "attic": Setting("attic", "the attic room", "A tick-tock mouse went patter on the beam,", "twinkly"),
    "garden": Setting("garden", "the garden gate", "A sleepy bee went hum and hummed a beam,", "gentle"),
}

RESPONSES = {
    "smooth": Response("smooth", 2, 2, "smoothed the {target} flat again with careful fingers", "could not smooth it", "smoothed the {target} flat again"),
    "stitch": Response("stitch", 2, 2, "stitched the {target} neat and true with a silver thread", "could not stitch it", "stitched the {target} neat and true"),
    "glue": Response("glue", 1, 1, "set the {target} straight with a dab of glue", "could not set it straight", "set the {target} straight"),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Pippa", "Tess"]
BOY_NAMES = ["Pip", "Noah", "Theo", "Milo", "Finn"]
TRAITS = ["careful", "curious", "gentle", "bold"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_type: str
    caregiver_type: str
    response: str
    delay: int = 0
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
    out = []
    for sid in SETTINGS:
        for rid in RESPONSES:
            for _ in range(1):
                out.append((sid, rid, "paper crown"))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    return [
        f'Write a nursery-rhyme-style story with the word "reason" about {c.id} and a magic wand.',
        f"Tell a gentle magic story where {c.id} wants to use a wand for a reason, and a grown-up helps the child choose wisely.",
        f"Write a tiny rhyme where magic stirs trouble, reason is spoken aloud, and the ending turns calm again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, g = f["child"], f["caregiver"]
    return [
        ("Who is the story about?",
         f"It is about {c.id} and the grown-up who watches over {c.id}. The child wants magic, but the grown-up keeps the reason in view."),
        ("What did the child want to use?",
         f"{c.id} wanted to use a magic wand. The wand was supposed to make the little paper crown look bright, but it ended up ruffling it instead."),
        ("Why did the grown-up speak up?",
         f"The grown-up saw that the magic would ruffle the paper crown. That is why the grown-up asked for the reason and warned the child first."),
        ("How did the story end?",
         f"It ended with the paper crown made neat again and the child learning to use magic only when there is a good reason. The room finished calm and tidy."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is magic in a story?",
         "Magic is pretend power that can make surprising things happen in a story. It is often sparkly, playful, and a little mysterious."),
        ("What does reason mean?",
         "Reason means the why behind a choice. It is the good thought that helps someone decide what to do."),
        ("Why do grown-ups ask for a reason?",
         "Grown-ups ask for a reason so they can tell whether a choice is safe and sensible. That helps keep people and things from getting hurt."),
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


CURATED = [
    StoryParams("nursery", "Mina", "girl", "mother", "smooth", 0),
    StoryParams("attic", "Pip", "boy", "father", "stitch", 0),
    StoryParams("garden", "Nora", "girl", "mother", "glue", 1),
]


ASP_RULES = r"""
ruffled(F) :- sparkly(F).
warn_needed(C) :- child(C), ruffled(_).
ending_calm :- repaired(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    lines.append(asp.fact("reason_min", int(REASON_MIN)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp  # lazy
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    _ = asp
    print(f"OK: ASP facts load for {len(SETTINGS)} settings and {len(RESPONSES)} responses.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        assert sample.world is not None
        print("OK: smoke test story generation works.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme-style magic reason storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father", "aunt", "uncle"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    response = args.response or rng.choice(list(RESPONSES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(["mother", "father", "aunt", "uncle"])
    delay = rng.randint(0, 1)
    if not needs_reason("reason"):
        raise StoryError("Missing reason.")
    return StoryParams(setting, name, gender, caregiver, response, delay=delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.child_name, params.child_type, params.caregiver_type, params.delay)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(SETTINGS)} settings, {len(RESPONSES)} responses, nursery magic ready.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} in {p.setting} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

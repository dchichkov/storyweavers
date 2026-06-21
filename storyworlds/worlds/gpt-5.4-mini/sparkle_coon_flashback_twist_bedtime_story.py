#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sparkle_coon_flashback_twist_bedtime_story.py
==============================================================================

A standalone bedtime-story world about a little child, a lost sleepy friend, a
sparkly object, a flashback, and a gentle twist ending.

The tiny domain:
- A child is ready for bed but notices a coon outside the window.
- The coon has lost a glowing bedtime charm: a sparkle stone.
- The child remembers a helpful flashback to where the stone came from.
- The twist is that the "mischief" is actually the coon's way of returning a
  lost lullaby token to the nest, and bedtime becomes calm and kind.

The world is small, state-driven, and constraint-checked. It has typed entities
with physical meters and emotional memes, a reasonableness gate, inline ASP
rules, and three QA sets generated from world state rather than parsed English.
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
class Motif:
    id: str
    name: str
    glow: str
    use: str
    tags: set[str] = field(default_factory=set)

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
class Place:
    id: str
    name: str
    window: str
    night_sound: str
    bedtime_color: str
    tags: set[str] = field(default_factory=set)

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
    tags: set[str] = field(default_factory=set)

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


def _r_twinkle(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["sparkle"] < THRESHOLD:
            continue
        sig = ("twinkle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").memes["wonder"] += 1
        out.append("__twinkle__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("twist_revealed") and "child" in world.entities:
        child = world.get("child")
        sig = ("calm", "child")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["calm"] += 1
            child.memes["love"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("twinkle", "physical", _r_twinkle), Rule("calm", "social", _r_calm)]


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


def reasonableness_gate(place: Place, motif: Motif, response: Response) -> bool:
    return "window" in place.tags and motif.id in {"sparkle", "coon"} and response.sense >= SENSE_MIN


SENSE_MIN = 2


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def is_resolved(response: Response, delay: int) -> bool:
    return response.power >= 1 + delay


def flashback(world: World, child: Entity, motif: Motif, place: Place) -> None:
    child.memes["memory"] += 1
    world.facts["flashback_seen"] = True
    world.say(
        f"At bedtime, {child.id} noticed a tiny {motif.name} by the window, "
        f"glowing like a dropped star. For a moment, {child.pronoun()} remembered "
        f"the last time {child.pronoun('possessive')} {place.label_word} had looked so bright."
    )
    world.say(
        f"In that memory, the room was smaller and quieter, and the same soft light "
        f"had led {child.id} to a lost little promise."
    )


def setup(world: World, child: Entity, parent: Entity, place: Place) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"Tonight, {child.id} was tucked into bed in {place.name}. "
        f"{place.window} showed a dark blue night, and {place.night_sound}."
    )
    world.say(
        f"{child.id} was almost asleep when {child.pronoun()} noticed something "
        f"small and bright near the glass."
    )


def notice_coon(world: World, coon: Entity, motif: Motif) -> None:
    coon.memes["mischief"] += 1
    coon.memes["care"] += 1
    world.say(
        f"Outside, a little coon sat on the sill, its paws holding a {motif.name}. "
        f"The stone sent out a {motif.glow} and the coon blinked in the light."
    )


def warn(world: World, child: Entity, parent: Entity, motif: Motif) -> None:
    child.memes["worry"] += 1
    world.say(
        f'"{child.id}?" {parent.label_word.capitalize()} whispered from the hall. '
        f'"What is that sparkle?"'
    )
    world.say(
        f"{child.id} pressed a hand to the window and said the light looked lonely, "
        f"like it was trying to tell a bedtime secret."
    )


def reveal_twist(world: World, child: Entity, coon: Entity, motif: Motif) -> None:
    world.facts["twist_revealed"] = True
    coon.memes["relief"] += 1
    world.say(
        f"Then the twist arrived: the coon was not stealing at all. It had found "
        f"the {motif.name} in the garden and was carrying it back to a nest of sleepy kits."
    )
    world.say(
        f"{child.id} remembered the flashback at once and understood why the light "
        f"had seemed so familiar."
    )
    world.say(
        f"The coon nudged the stone toward the tree, as careful as a nurse tucking in a blanket."
    )


def soothe(world: World, child: Entity, parent: Entity, motif: Motif, response: Response, delay: int) -> None:
    if is_resolved(response, delay):
        child.memes["calm"] += 1
        world.say(
            f"{parent.label_word.capitalize()} smiled and {response.text.replace('{motif}', motif.name)}."
        )
        world.say(
            f"The {motif.name} stopped shining so strongly and became a soft little glow "
            f"in the dark, the kind that makes bedtime feel safe."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} tried to help, but {response.fail.replace('{motif}', motif.name)}."
        )


def ending(world: World, child: Entity, parent: Entity, motif: Motif, coon: Entity) -> None:
    world.say(
        f"{child.id} yawned and waved goodnight to the coon. The {motif.name} drifted "
        f"back to the tree, and the window went calm again."
    )
    world.say(
        f"After that, {child.id} fell asleep with a warm little sparkle in {child.pronoun('possessive')} heart."
    )


def tell(place: Place, motif: Motif, response: Response, delay: int = 0) -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type="girl", role="hero"))
    parent = world.add(Entity("parent", kind="character", type="mother", role="helper", label="the parent"))
    coon = world.add(Entity("coon", kind="character", type="thing", role="visitor", label="the coon"))
    room = world.add(Entity("room", type="room"))
    gem = world.add(Entity("sparkle", type="thing", label=motif.name))
    gem.meters["sparkle"] += 1

    setup(world, child, parent, place)
    world.para()
    notice_coon(world, coon, motif)
    warn(world, child, parent, motif)
    flashback(world, child, motif, place)
    world.para()
    reveal_twist(world, child, coon, motif)
    soothe(world, child, parent, motif, response, delay)
    propagate(world, narrate=True)
    world.para()
    ending(world, child, parent, motif, coon)

    world.facts.update(
        child=child,
        parent=parent,
        coon=coon,
        place=place,
        motif=motif,
        response=response,
        delay=delay,
        resolved=is_resolved(response, delay),
    )
    return world


PLACE_REGISTRY = {
    "nursery": Place("nursery", "the nursery", "The window", "the trees rustled outside", "moon-blue", {"window", "bedtime"}),
    "bedroom": Place("bedroom", "the bedroom", "The window", "the curtains breathed with the wind", "soft-indigo", {"window", "bedtime"}),
    "attic_room": Place("attic_room", "the attic room", "The little window", "the old house creaked gently", "silver-blue", {"window", "bedtime"}),
}

MOTIF_REGISTRY = {
    "sparkle": Motif("sparkle", "sparkle stone", "tiny and silver", "light the dark", {"sparkle", "glow"}),
    "coon": Motif("coon", "coon charm", "warm and amber", "carry home", {"coon", "glow"}),
}

RESPONSES = {
    "gentle_tuck": Response("gentle_tuck", 3, 2,
                            "tucked the sparkle stone into a small bowl on the sill so it could rest",
                            "tried to tuck it away, but the light kept trembling and sliding back",
                            "tucked the sparkle stone into a small bowl on the sill so it could rest",
                            {"calm", "bedtime"}),
    "lantern_nook": Response("lantern_nook", 3, 3,
                             "set a little lantern beside the tree and made a safe path for the coon",
                             "set out a lantern, but the wind and worry made the plan wobble",
                             "set a little lantern beside the tree and made a safe path for the coon",
                             {"calm", "bedtime"}),
    "soft_song": Response("soft_song", 2, 1,
                          "hummed a soft song and waited for the coon to finish its careful trip",
                          "hummed, but the night was too restless and the little plan came apart",
                          "hummed a soft song and waited for the coon to finish its careful trip",
                          {"song", "bedtime"}),
    "too_late": Response("too_late", 1, 0,
                         "reached out too quickly and startled the coon",
                         "reached out too quickly, but the coon whisked the stone away",
                         "reached out too quickly and startled the coon",
                         {"mischief"}),
}

SENSE_MIN = 2


@dataclass
class StoryParams:
    place: str
    motif: str
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

CURATED = [
    dataclass(type("P", (), {}))
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACE_REGISTRY:
        for m in MOTIF_REGISTRY:
            for r in RESPONSES:
                if reasonableness_gate(PLACE_REGISTRY[p], MOTIF_REGISTRY[m], RESPONSES[r]):
                    combos.append((p, m, r))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "{f["motif"].name}" and "coon".',
        f"Tell a gentle story with a flashback and a twist, where a child sees a coon near the window and learns what the sparkle stone really means.",
        f"Write a cozy bedtime story about a tiny glow at the window, ending with the child feeling safe and sleepy.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    place, motif, response = f["place"], f["motif"], f["response"]
    child, parent, coon = f["child"], f["parent"], f["coon"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, {parent.label_word}, and the coon outside the window. The story stays close to bedtime and the little glowing thing they notice."),
        ("What did the child remember in the flashback?",
         f"{child.id} remembered the last time the {motif.name} had shone near {place.window.lower()}. The memory helped {child.id} understand that the light was familiar, not scary."),
        ("What was the twist in the story?",
         f"The twist was that the coon was not taking the {motif.name} away for mischief. It was carrying the sparkle stone back to its nest, so the child could relax and watch kindly."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a coon?",
         "A coon is a small night animal with a striped tail and clever paws. It often looks curious and careful when it moves around homes and trees."),
        ("What does sparkle mean?",
         "Something that sparkles gives off tiny bright flashes of light. Sparkly things can look magical at bedtime because they shine softly in the dark."),
        ("Why are bedtime stories soothing?",
         "Bedtime stories are soothing because they are calm, familiar, and gentle. They help a child settle down and feel safe enough to sleep."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(place: Place, motif: Motif, response: Response) -> str:
    return f"(No story: the chosen ending is too weak or too strange for a gentle bedtime tale.)"


def outcome_of(params: StoryParams) -> str:
    return "resolved" if is_resolved(RESPONSES[params.response], params.delay) else "unresolved"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACE_REGISTRY:
        lines.append(asp.fact("place", p))
    for m in MOTIF_REGISTRY:
        lines.append(asp.fact("motif", m))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
        lines.append(asp.fact("power", r, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(P, M, R) :- place(P), motif(M), response(R), sensible(R).
resolved(R) :- response(R), power(R,P), delay(D), P >= 1 + D.
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
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    sample = generate(resolve_params(argparse.Namespace(place=None, motif=None, response=None, delay=None, seed=None), random.Random(7)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: sample story is empty.")
    else:
        print("OK: generate() smoke test produced a story.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with sparkle, coon, flashback, and twist.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--motif", choices=MOTIF_REGISTRY)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
              if (args.place is None or c[0] == args.place)
              and (args.motif is None or c[1] == args.motif)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    p, m, r = rng.choice(sorted(combos))
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(p, m, r, delay=delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACE_REGISTRY[params.place], MOTIF_REGISTRY[params.motif], RESPONSES[params.response], params.delay)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        params_list = [StoryParams(p, m, r, delay=0) for p, m, r in valid_combos()[:5]]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

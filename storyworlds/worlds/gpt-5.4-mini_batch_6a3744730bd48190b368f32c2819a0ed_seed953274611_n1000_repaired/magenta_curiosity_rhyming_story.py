#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/magenta_curiosity_rhyming_story.py
===================================================================

A tiny standalone storyworld for a rhyming curiosity tale: a child spots a
magenta mystery, follows clues with a lantern, and learns something new in the
end. The world is built from typed entities, accumulating meters and memes,
state-driven narration, a Python reasonableness gate, and an inline ASP twin.

The domain is intentionally small:
- one curious child
- one bright magenta thing
- one hidden place
- one helper light
- one clue trail

The story aims for a child-facing rhyming feel without flattening into a frozen
template. Different seeds change names, setting flavor, the hidden place, and
the resolution details, while the simulated world state drives the prose.
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
    phrase: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.id


@dataclass
class Place:
    id: str
    scene: str
    rhyme: str
    color_place: str
    dark_spot: str
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
class Mystery:
    id: str
    label: str
    phrase: str
    gleam: str
    hidden_in: str
    clue: str
    tags: set[str] = field(default_factory=set)
    discoverable: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Resolution:
    id: str
    sense: int
    power: int
    text: str
    fail_text: str
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
class StoryParams:
    place: str
    mystery: str
    light: str
    resolution: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
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
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_fear(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["hidden_glow"] >= THRESHOLD and ("child" in e.tags or e.role == "child"):
            sig = ("fear", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["curiosity"] += 1
            out.append("__quiet__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
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


def valid_places() -> list[str]:
    return sorted(PLACES)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid, mystery in MYSTERIES.items():
            if not mystery.discoverable:
                continue
            if place.id not in mystery.hidden_in:
                continue
            for lid, light in LIGHTS.items():
                if "glow" in light.tags:
                    combos.append((pid, mid, lid))
    return combos


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b} in a little rhyme"


def predict_discovery(world: World, mystery_id: str) -> bool:
    sim = world.copy()
    sim.get(mystery_id).meters["hidden_glow"] += 1
    propagate(sim, narrate=False)
    return sim.get("child").memes["curiosity"] >= THRESHOLD


def reason_gate(resolution: Resolution) -> bool:
    return resolution.sense >= SENSE_MIN


SENSE_MIN = 2

PLACES = {
    "garden": Place(
        id="garden",
        scene="a garden with a song in the air",
        rhyme="a garden party in a row of sweet pears",
        color_place="flower bed",
        dark_spot="behind the viney gate",
        tags={"garden", "outdoor"},
    ),
    "attic": Place(
        id="attic",
        scene="a dusty attic under the rafters",
        rhyme="a attic nook with a creaky old stare",
        color_place="old trunk corner",
        dark_spot="behind the stacked boxes",
        tags={"attic", "indoor"},
    ),
    "porch": Place(
        id="porch",
        scene="a porch where the evening air swayed",
        rhyme="a porch with a breeze and a moonlit gleam",
        color_place="bench shadow",
        dark_spot="under the wicker chair",
        tags={"porch", "outdoor"},
    ),
}

MYSTERIES = {
    "ribbon": Mystery(
        id="ribbon",
        label="magenta ribbon",
        phrase="a magenta ribbon",
        gleam="shiny and bright",
        hidden_in={"garden", "porch"},
        clue="A flutter of color peeked near the leaves.",
        tags={"magenta", "curious"},
    ),
    "stone": Mystery(
        id="stone",
        label="magenta stone",
        phrase="a smooth magenta stone",
        gleam="pink-purple and neat",
        hidden_in={"attic", "porch"},
        clue="A round little glimmer winked from the dark.",
        tags={"magenta", "curious"},
    ),
    "shell": Mystery(
        id="shell",
        label="magenta shell",
        phrase="a magenta shell",
        gleam="softly gleaming",
        hidden_in={"garden"},
        clue="A tiny shine hid under a curled-up leaf.",
        tags={"magenta", "curious"},
    ),
}

LIGHTS = {
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        glow="glowed like a warm star",
        tags={"light"},
    ),
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a bright flashlight",
        glow="shone like a silver ray",
        tags={"light"},
    ),
}

RESOLUTIONS = {
    "share": Resolution(
        id="share",
        sense=3,
        power=3,
        text="held the mystery up so both could see and smiled at the find",
        fail_text="tried to hush the mystery, but the dark kept it hidden",
        tags={"share"},
    ),
    "name_it": Resolution(
        id="name_it",
        sense=2,
        power=2,
        text="named the color out loud and tucked the clue into memory",
        fail_text="named the color, but the clue was still too faint to follow",
        tags={"name"},
    ),
    "follow_clue": Resolution(
        id="follow_clue",
        sense=3,
        power=4,
        text="followed the clue to the secret spot and found the bright surprise",
        fail_text="followed the clue, but the trail ran out in the dark",
        tags={"follow"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Eli", "Sam"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming curiosity storyworld with magenta mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    if args.resolution and not reason_gate(RESOLUTIONS[args.resolution]):
        raise StoryError("That ending is too weak for a curious story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.light is None or c[2] == args.light)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, light = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(RESOLUTIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        mystery=mystery,
        light=light,
        resolution=resolution,
        child_name=name,
        child_gender=gender,
        adult_name=adult,
        adult_gender=adult,
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.light not in LIGHTS or params.resolution not in RESOLUTIONS:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    light = LIGHTS[params.light]
    resolution = RESOLUTIONS[params.resolution]

    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child", tags={"child"}))
    adult = world.add(Entity(id=params.adult_name.capitalize(), kind="character", type=params.adult_gender, role="adult", label=f"the {params.adult_name}"))
    hidden = world.add(Entity(id="mystery", kind="thing", type="mystery", label=mystery.label, tags=set(mystery.tags)))
    lamp = world.add(Entity(id="light", kind="thing", type="light", label=light.label, tags=set(light.tags)))

    child.memes["curiosity"] = 1
    world.say(f"In {place.scene}, {child.id} felt a tingle of curiosity. {place.rhyme}.")
    world.say(f"{child.id} saw {mystery.phrase}, {mystery.gleam} and magenta bright, {mystery.clue}")

    world.para()
    world.say(f'"{light.phrase}!" said {child.id}. {child.id} took it along to look and to see.')
    child.meters["curious_steps"] += 1
    child.memes["curiosity"] += 1
    hidden.meters["hidden_glow"] += 1
    propagate(world, narrate=False)

    world.say(f"With {light.phrase}, the shadows grew light, and the dark felt less tight.")
    world.say(f"{child.id} followed the shimmer near {place.dark_spot}, a clue in the night.")

    world.para()
    if predict_discovery(world, hidden.id):
        world.say(f"{adult.label_word if adult.label else 'The grown-up'} came near and smiled with delight.")
    if resolution.sense >= SENSE_MIN:
        world.say(f"Then {child.id} {resolution.text}.")
        child.memes["joy"] += 1
        child.memes["pride"] += 1
    else:
        world.say(f"Then {child.id} {resolution.fail_text}.")
    world.say(f"At last, the magenta secret was found in the light, and curiosity made the whole day bright.")

    world.facts.update(
        child=child,
        adult=adult,
        place=place,
        mystery=mystery,
        light=light,
        resolution=resolution,
        outcome="found",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a child who sees something {f["mystery"].label} and feels curious.',
        f"Tell a rhyming curiosity story where {f['child'].id} uses {f['light'].phrase} to look for {f['mystery'].phrase}.",
        f'Write a gentle story that includes the word "magenta" and ends with a bright discovery.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    place = f["place"]
    light = f["light"]
    return [
        ("What color mystery did the child notice?",
         f"The child noticed something magenta. It was {mystery.phrase}, and that bright color is what sparked the curiosity."),
        ("Why did the child bring the light?",
         f"{child.id} brought {light.phrase} to see into the dark spot more clearly. The light helped the child follow the clue instead of guessing in the shadows."),
        ("How did the story end?",
         f"It ended with the magenta secret found and curiosity rewarded. The child saw that asking and looking carefully can lead to a happy discovery in {place.scene}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is curiosity?",
         "Curiosity is the feeling that makes you want to ask questions and look carefully. It helps children learn by exploring safely."),
        ("What does a lantern do?",
         "A lantern gives off light so you can see in darker places. It is a helpful way to look without using a flame."),
        ("Why is magenta an interesting color?",
         "Magenta is a bright, lively color that stands out fast. A color like that can catch your eye and make you wonder what it belongs to."),
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:10} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- resolution(R), sense(R,S), sense_min(M), S >= M.
valid(P,M,L) :- place(P), mystery(M), light(L), discoverable(M), hidden_at(M,P).
discovered :- child_curiosity(C), C >= 1, hidden_glow(H), H >= 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if m.discoverable:
            lines.append(asp.fact("discoverable", mid))
        for p in sorted(m.hidden_in):
            lines.append(asp.fact("hidden_at", mid, p))
    for lid in LIGHTS:
        lines.append(asp.fact("light", lid))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
    sens = set(asp_sensible())
    py_sens = {r for r, rr in RESOLUTIONS.items() if rr.sense >= SENSE_MIN}
    if sens == py_sens:
        print("OK: sensible resolutions match.")
    else:
        rc = 1
        print("MISMATCH in sensible resolutions.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, light=None, resolution=None, name=None, gender=None, adult=None), random.Random(7)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible resolutions: {', '.join(asp_sensible())}\n")
        for p, m, l in asp_valid_combos():
            print(f"{p:8} {m:8} {l}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="garden", mystery="shell", light="lantern", resolution="follow_clue", child_name="Mia", child_gender="girl", adult_name="mother", adult_gender="mother"),
            StoryParams(place="attic", mystery="stone", light="flashlight", resolution="share", child_name="Leo", child_gender="boy", adult_name="father", adult_gender="father"),
            StoryParams(place="porch", mystery="ribbon", light="lantern", resolution="name_it", child_name="Nora", child_gender="girl", adult_name="mother", adult_gender="mother"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

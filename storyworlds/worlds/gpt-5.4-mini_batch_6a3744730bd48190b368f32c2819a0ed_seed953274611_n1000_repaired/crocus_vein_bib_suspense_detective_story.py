#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crocus_vein_bib_suspense_detective_story.py
===========================================================================

A small storyworld in a detective-story style with suspense:
a child detective searches for a missing clue while a careful helper protects a
delicate crocus bulb, a visible vein of soil, and a stained bib. The world model
tracks physical meters and emotional memes, so the prose follows state changes:
the clue is hidden, suspicion rises, a reveal turns the search, and the ending
image proves what changed.
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c
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


@dataclass
class Scene:
    id: str
    place: str
    mood: str
    suspense_line: str
    reveal_line: str
    ending_image: str
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
class Clue:
    id: str
    label: str
    hidden_in: str
    tell: str
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
class Protector:
    id: str
    label: str
    use_line: str
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
    scene: str
    clue: str
    protector: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
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


SCENES = {
    "greenhouse": Scene(
        id="greenhouse",
        place="the old greenhouse",
        mood="foggy and still",
        suspense_line="A pale mist hung over the glass, and every shadow looked like a secret.",
        reveal_line="The final clue was hiding right where the light caught the wet glass.",
        ending_image="The crocus stood upright again, bright beside the cleared little vein of soil.",
        tags={"suspense", "detective", "glass"},
    ),
    "garden": Scene(
        id="garden",
        place="the back garden",
        mood="quiet and damp",
        suspense_line="The garden path was silent except for one drip, drip, drip under the stones.",
        reveal_line="The hidden sign was tucked along a thin vein in the soil by the crocus bed.",
        ending_image="The bib was clean, the clue was found, and the crocus bed looked peaceful again.",
        tags={"suspense", "detective", "soil"},
    ),
    "porch": Scene(
        id="porch",
        place="the porch steps",
        mood="blue and hushed",
        suspense_line="Even the porch light seemed to wait for the answer.",
        reveal_line="The last clue had slipped into the fold of the bib, where the helper had not thought to look.",
        ending_image="The bib no longer hid anything, and the crocus by the steps finally had its name back.",
        tags={"suspense", "detective", "porch"},
    ),
}

CLUES = {
    "crocus": Clue(
        id="crocus",
        label="crocus",
        hidden_in="the flower bed",
        tell="a purple petal and a bent green stem",
        tags={"flower", "purple", "garden"},
    ),
    "vein": Clue(
        id="vein",
        label="vein",
        hidden_in="the damp soil",
        tell="a thin dark vein running through the earth",
        tags={"soil", "line", "dark"},
    ),
    "bib": Clue(
        id="bib",
        label="bib",
        hidden_in="the pantry hook",
        tell="a tiny red stain on the bib",
        tags={"cloth", "stain", "kitchen"},
    ),
}

PROTECTORS = {
    "glove": Protector(
        id="glove",
        label="rubber glove",
        use_line="slipped on the rubber glove before touching anything else",
        tags={"glove", "careful"},
    ),
    "lamp": Protector(
        id="lamp",
        label="desk lamp",
        use_line="switched on the desk lamp to inspect the clue without missing a detail",
        tags={"light", "inspect"},
    ),
    "tape": Protector(
        id="tape",
        label="evidence tape",
        use_line="marked the path with evidence tape so nobody would step on the clue",
        tags={"tape", "detective"},
    ),
}

NAMES_GIRL = ["Mira", "Lena", "Ivy", "Nora", "Tess", "Ruby"]
NAMES_BOY = ["Owen", "Eli", "Milo", "Noah", "Finn", "Theo"]


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    helper = world.get("helper")
    clue = world.get("clue")
    scene = world.get("scene")
    if detective.meters["search"] < THRESHOLD or clue.meters["found"] >= THRESHOLD:
        return out
    sig = ("tension",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["unease"] += 1
    helper.memes["worry"] += 1
    scene.meters["suspense"] += 1
    out.append("The room felt one breath away from an answer.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    detective = world.get("detective")
    if clue.meters["found"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["relief"] += 1
    detective.memes["joy"] += 1
    out.append(world.facts["scene_obj"].reveal_line)
    return out


CAUSAL_RULES = [Rule("tension", _r_tension), Rule("reveal", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, p) for s in SCENES for c in CLUES for p in PROTECTORS]


def explain_rejection() -> str:
    return "(No story: the chosen clue and protector do not support a real suspenseful detective turn.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful detective storyworld with crocus, vein, and bib.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--protector", choices=PROTECTORS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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


def asp_facts() -> str:
    import asp
    parts = []
    for s in SCENES:
        parts.append(asp.fact("scene", s))
    for c in CLUES:
        parts.append(asp.fact("clue", c))
    for p in PROTECTORS:
        parts.append(asp.fact("protector", p))
    return "\n".join(parts)


ASP_RULES = r"""
valid(S,C,P) :- scene(S), clue(C), protector(P).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combo sets differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as err:
        print(f"MISMATCH: smoke test failed: {err}")
        rc = 1
    else:
        print("OK: ASP parity and smoke test passed.")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scene = args.scene or rng.choice(list(SCENES))
    clue = args.clue or rng.choice(list(CLUES))
    protector = args.protector or rng.choice(list(PROTECTORS))
    if clue == "bib" and protector == "tape":
        raise StoryError(explain_rejection())
    dt = args.detective_type or rng.choice(["girl", "boy"])
    ht = args.helper_type or rng.choice(["girl", "boy"])
    dn = args.detective_name or rng.choice(NAMES_GIRL if dt == "girl" else NAMES_BOY)
    hn = args.helper_name or rng.choice([n for n in (NAMES_GIRL if ht == "girl" else NAMES_BOY) if n != dn])
    return StoryParams(scene=scene, clue=clue, protector=protector, detective_name=dn, detective_type=dt, helper_name=hn, helper_type=ht)


def _build_world(params: StoryParams) -> World:
    w = World()
    scene = w.add(Entity(id="scene", kind="place", type="place", label=SCENES[params.scene].place))
    detective = w.add(Entity(id="detective", kind="character", type=params.detective_type, label=params.detective_name, role="detective"))
    helper = w.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name, role="helper"))
    clue = w.add(Entity(id="clue", kind="thing", type="thing", label=CLUES[params.clue].label, role="clue"))
    protector = w.add(Entity(id="protector", kind="thing", type="thing", label=PROTECTORS[params.protector].label, role="protector"))
    w.facts.update(scene_obj=SCENES[params.scene], clue_obj=CLUES[params.clue], protector_obj=PROTECTORS[params.protector])
    return w


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.clue not in CLUES or params.protector not in PROTECTORS:
        raise StoryError("Invalid parameters.")
    world = _build_world(params)
    detective = world.get("detective")
    helper = world.get("helper")
    clue = world.get("clue")
    scene = world.get("scene")
    prot = world.get("protector")
    detective.meters["search"] += 1
    detective.memes["focus"] += 1
    world.say(f"It was {SCENES[params.scene].mood} in {SCENES[params.scene].place}.")
    world.say(f"{detective.id} was a careful little detective, and {helper.id} stayed close beside {detective.pronoun('object')}.")
    world.say(f"Somewhere in the hush, the words crocus, vein, and bib all seemed to matter.")
    world.para()
    world.say(SCENES[params.scene].suspense_line)
    world.say(f"{helper.id} pointed toward the clue and whispered that something was off about the {clue.label}.")
    world.say(f"{detective.id} {PROTECTORS[params.protector].use_line}.")
    propagate(world, narrate=True)
    world.para()
    clue.meters["found"] += 1
    detective.memes["courage"] += 1
    if params.clue == "crocus":
        world.say(f"Under the glass, they found a crocus with a bent stem, and the little flower was safe at last.")
    elif params.clue == "vein":
        world.say(f"Along the soil, they traced a vein-like line and learned it was only a dark root path, not a wound.")
    else:
        world.say(f"On the bib, the tiny stain led them back to the kitchen table and the lost note tucked there.")
    propagate(world, narrate=True)
    world.para()
    world.say(SCENES[params.scene].ending_image)
    world.facts.update(detective=detective, helper=helper, clue=clue, protector=prot, scene=scene,
                       outcome="solved", name=params.detective_name)
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
    return [
        f"Write a suspenseful detective story for a child that includes crocus, vein, and bib.",
        f"Tell a detective-style mystery where {f['detective'].label} and {f['helper'].label} search for a clue in {f['scene_obj'].place}.",
        f"Write a gentle suspense story where the clue about a crocus, a vein, and a bib is found at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det = f["detective"]
    helpr = f["helper"]
    clue = f["clue_obj"]
    scene = f["scene_obj"]
    return [
        ("Who is the story about?", f"It is about {det.label} and {helpr.label}, two small detectives working together."),
        ("Why was there suspense?", f"The place was quiet and the clue was hidden, so nobody knew what they would find next. That waiting made the search feel tense and careful."),
        ("What was found in the end?", f"They found the {clue.label} clue and made sense of it. The search ended with the mystery solved and the scene calm again."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a crocus?", "A crocus is a small flower that can bloom early, sometimes even while the weather is still chilly."),
        QAItem("What is a vein?", "A vein is a thin line in a leaf, a hand, or the ground that can look like it branches through a surface."),
        QAItem("What is a bib?", "A bib is a cloth that protects clothes from spills, especially when a child is eating."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id}: {e.label_word or e.id} {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(out)


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
    StoryParams(scene="greenhouse", clue="crocus", protector="lamp", detective_name="Mira", detective_type="girl", helper_name="Owen", helper_type="boy"),
    StoryParams(scene="garden", clue="vein", protector="tape", detective_name="Nora", detective_type="girl", helper_name="Finn", helper_type="boy"),
    StoryParams(scene="porch", clue="bib", protector="glove", detective_name="Theo", detective_type="boy", helper_name="Ivy", helper_type="girl"),
]


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combinations:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

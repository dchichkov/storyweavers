#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/picket_sound_effects_moral_value_conflict_fairy.py
==================================================================================

A tiny fairy-tale storyworld about a child, a picket fence, noisy magic, a moral
choice, and a small conflict that resolves into a kinder ending.

The world is intentionally small and classical:
- a child wants something shiny or whimsical,
- the wish causes a conflict near a picket fence or gate,
- sound effects emphasize the action,
- a moral choice determines whether the ending becomes gentle or messy,
- the prose ends with a concrete image proving what changed.

This file is standalone and only uses the Python stdlib plus the shared
storyworlds/results.py containers.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "fairy"}
        male = {"boy", "father", "man", "king", "knight"}
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
class Realm:
    id: str
    opening: str
    place: str
    sound: str
    moral: str
    conflict_word: str
    ending_image: str

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
class Desire:
    id: str
    label: str
    phrase: str
    sparkle: str
    risky: bool
    makes_noise: bool = True
    tags: set[str] = field(default_factory=set)

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
class Fence:
    id: str
    label: str
    phrase: str
    sound: str
    can_rattle: bool = True
    can_open: bool = False
    tags: set[str] = field(default_factory=set)

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
class Choice:
    id: str
    kind: str
    text: str
    good: bool
    power: int
    tags: set[str] = field(default_factory=set)

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_rattle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    fence = world.get("fence")
    if child.meters["noise"] < THRESHOLD or fence.meters["rattling"] >= THRESHOLD:
        return out
    sig = ("rattle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fence.meters["rattling"] += 1
    child.memes["startled"] += 1
    out.append("__rattle__")
    return out


def _r_conflict(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["stubborn"] < THRESHOLD or child.memes["reproved"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["conflict"] += 1
    return ["__conflict__"]


CAUSAL_RULES = [Rule("rattle", "physical", _r_rattle), Rule("conflict", "social", _r_conflict)]


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


def predict(world: World, desire: Desire) -> dict:
    sim = world.copy()
    _do_desire(sim, sim.get("child"), desire, narrate=False)
    return {
        "noisy": sim.get("fence").meters["rattling"] >= THRESHOLD,
        "conflict": sim.get("child").memes["conflict"],
    }


def _do_desire(world: World, child: Entity, desire: Desire, narrate: bool = True) -> None:
    child.meters["noise"] += 1 if desire.makes_noise else 0
    child.meters["sparkle"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, realm: Realm, child: Entity, fairy: Entity, fence: Entity, desire: Desire) -> None:
    child.memes["wonder"] += 1
    fairy.memes["kindness"] += 1
    world.say(
        f"Long ago, in {realm.place}, a little {child.type} named {child.id} walked by "
        f"{fence.phrase}. {realm.opening}"
    )
    world.say(
        f"{child.id} loved the shimmer in the air and whispered, '{desire.phrase}!' "
        f"Nearby, a fairy watched with gentle eyes."
    )


def urge(world: World, child: Entity, desire: Desire, fence: Fence) -> None:
    child.memes["stubborn"] += 1
    world.say(
        f"{child.id} reached for {desire.label}, and the moment sounded like {desire.sparkle}."
    )
    world.say(
        f'Then came {fence.sound} from the {fence.label}, as if the little fence were asking for quiet.'
    )


def warn(world: World, fairy: Entity, child: Entity, choice: Choice, realm: Realm) -> None:
    pred = predict(world, DESIRES[choice.id if choice.id in DESIRES else "bell"])
    child.memes["reproved"] += 1
    world.facts["predicted_conflict"] = pred["conflict"]
    world.say(
        f'{fairy.id} said softly, "{choice.text}." {fairy.pronoun().capitalize()} reminded '
        f"{child.id} that {realm.moral}"
    )


def choose_good(world: World, child: Entity, choice: Choice, realm: Realm) -> None:
    child.memes["joy"] += 1
    child.memes["kindness"] += 1
    world.say(
        f'{child.id} listened, took a breath, and chose the kinder path instead.'
    )
    world.say(
        f"They used the safe idea, and the morning stayed peaceful beside the {realm.conflict_word}."
    )


def choose_bad(world: World, child: Entity, choice: Choice, realm: Realm) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'{child.id} did not listen and pushed ahead with a bright, noisy idea.'
    )
    world.say(
        f"The little scene grew rough at once, and the fence began to shake like a spoon in a pot."
    )


def resolve(world: World, child: Entity, realm: Realm, choice: Choice) -> None:
    if choice.good:
        child.meters["noise"] = 0
        world.say(
            f"{realm.ending_image}"
        )
    else:
        child.memes["conflict"] += 1
        world.say(
            f"In the end, the wind caught the sound, but {child.id} learned that {realm.moral}."
        )
        world.say(
            f"{realm.ending_image}"
        )


def tell(realm: Realm, desire: Desire, fence: Fence, choice: Choice,
         child_name: str = "Mira", child_gender: str = "girl",
         fairy_name: str = "Star", parent_name: str = "Mother") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    fairy = world.add(Entity(id="fairy", kind="character", type="fairy", label=fairy_name, role="guide"))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label=parent_name, role="guardian"))
    fence_ent = world.add(Entity(id="fence", type="thing", label=fence.label, attrs={"sound": fence.sound}))

    setup(world, realm, child, fairy, fence, desire)
    world.para()
    urge(world, child, desire, fence)
    warn(world, fairy, child, choice, realm)

    world.para()
    if choice.good:
        choose_good(world, child, choice, realm)
    else:
        choose_bad(world, child, choice, realm)
    resolve(world, child, realm, choice)

    world.facts.update(
        child=child,
        fairy=fairy,
        parent=parent,
        fence=fence_ent,
        realm=realm,
        desire=desire,
        choice=choice,
        outcome="good" if choice.good else "bad",
    )
    return world


REALMS = {
    "rose_gate": Realm(
        "rose_gate",
        "The roses rustled like tiny skirts in the breeze.",
        "a cottage garden with a white picket fence",
        "clink-clink, tap-tap",
        "it is kinder to ask than to take",
        "conflict",
        "The child stood beside the white picket fence with folded hands, and the roses swayed quietly as the sun went down."
    ),
    "starlit_lawn": Realm(
        "starlit_lawn",
        "Moonlight made every blade of grass shine silver.",
        "a moonlit lawn with a wooden picket fence",
        "knock-knock, rattle-rattle",
        "a gentle heart is better than a greedy one",
        "conflict",
        "The wooden picket fence stayed still at last, and the child carried a small lantern home instead of a stolen treasure."
    ),
}

DESIRES = {
    "bell": Desire("bell", "a silver bell", "a silver bell", "tinkle-tinkle", True, True, {"sound"}),
    "cake": Desire("cake", "the cake on the sill", "the cake on the sill", "smack-smack", True, True, {"moral"}),
    "flower": Desire("flower", "the fairy flower", "the fairy flower", "flutter-flutter", False, True, {"moral"}),
}

FENCES = {
    "white": Fence("white", "white picket fence", "a white picket fence", "clink-clink"),
    "wood": Fence("wood", "wooden picket fence", "a wooden picket fence", "knock-knock"),
}

CHOICES = {
    "ask": Choice("ask", "moral", "ask the grown-up first", True, 3, {"moral"}),
    "return": Choice("return", "moral", "put it back where it belonged", True, 3, {"moral"}),
    "snatch": Choice("snatch", "conflict", "take it without asking", False, 1, {"conflict"}),
}


@dataclass
@dataclass
class StoryParams:
    realm: str
    desire: str
    fence: str
    choice: str
    child_name: str
    child_gender: str
    parent_name: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for r in REALMS:
        for d in DESIRES:
            for f in FENCES:
                for c in CHOICES:
                    if DESIRES[d].risky:
                        combos.append((r, d, f, c))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a young child that includes the word "picket" and a soft sound effect.',
        f"Tell a story where {f['child'].label_word} sees something tempting near a picket fence, hears a sound, and learns a moral lesson.",
        f"Write a gentle fairy tale with a small conflict, a magical helper, and an ending that shows the child became kinder."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    realm = f["realm"]
    desire = f["desire"]
    choice = f["choice"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, a little {child.type}, and a fairy who watched over the garden."),
        ("What did the child want?",
         f"{child.id} wanted {desire.phrase}. The wish made the scene feel exciting, but it also caused trouble near the picket fence."),
        ("What lesson did the fairy give?",
         f"The fairy taught that {realm.moral}. That lesson helped the child choose a better way to act.")
    ]
    if f["outcome"] == "good":
        qa.append((
            "How did the story end?",
            f"It ended peacefully. {child.id} listened, chose to {choice.text}, and the picket fence stayed calm instead of rattling."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with a rough little conflict, but {child.id} still learned to be kinder. The picket fence sounded its warning, and the lesson stayed."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["desire"].tags) | set(f["choice"].tags) | {"picket"}
    out = []
    knowledge = {
        "picket": [("What is a picket fence?",
                    "A picket fence is a fence made of upright slats with little gaps between them. In fairy tales, it often stands around a garden or cottage.")],
        "sound": [("Why do stories use sound effects?",
                   "Sound effects make a scene feel lively and help you imagine what is happening. They can make magic, footsteps, or a fence rattling feel more real.")],
        "moral": [("What is a moral in a story?",
                  "A moral is a lesson the story wants you to remember. It often tells you how to be kind, honest, or careful.")],
        "conflict": [("What is conflict in a story?",
                     "Conflict is when characters want different things or something goes wrong. It gives the story a problem that needs to be solved.")],
    }
    for tag in ["picket", "sound", "moral", "conflict"]:
        if tag in tags:
            out.extend(knowledge[tag])
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rose_gate", "bell", "white", "ask", "Mira", "girl", "Mother"),
    StoryParams("starlit_lawn", "cake", "wood", "return", "Owen", "boy", "Mother"),
    StoryParams("rose_gate", "flower", "white", "snatch", "Lena", "girl", "Mother"),
]


def explain_rejection() -> str:
    return "(No story: the choices must allow a little fairy-tale conflict near a picket fence.)"


ASP_RULES = r"""
conflict(C) :- choice(C), not good_choice(C).
good_choice(C) :- choice(C), good(C).
valid(R, D, F, C) :- realm(R), desire(D), fence(F), choice(C), risky(D).
outcome(good) :- chosen_choice(C), good_choice(C).
outcome(bad) :- chosen_choice(C), not good_choice(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in REALMS:
        lines.append(asp.fact("realm", rid))
    for did, d in DESIRES.items():
        lines.append(asp.fact("desire", did))
        if d.risky:
            lines.append(asp.fact("risky", did))
    for fid in FENCES:
        lines.append(asp.fact("fence", fid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        if c.good:
            lines.append(asp.fact("good", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = asp.fact("chosen_choice", params.choice)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        _ = generate(CURATED[0])
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld with picket, sound effects, moral value, and conflict.")
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--desire", choices=DESIRES)
    ap.add_argument("--fence", choices=FENCES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
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
    if args.realm and args.realm not in REALMS:
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.realm is None or c[0] == args.realm)
              and (args.desire is None or c[1] == args.desire)
              and (args.fence is None or c[2] == args.fence)
              and (args.choice is None or c[3] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    realm, desire, fence, choice = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(["Mira", "Lena", "Owen", "Pip", "June", "Nico"])
    parent_name = args.parent_name or rng.choice(["Mother", "Father"])
    return StoryParams(realm, desire, fence, choice, child_name, child_gender, parent_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(REALMS[params.realm], DESIRES[params.desire], FENCES[params.fence], CHOICES[params.choice],
                 params.child_name, params.child_gender, "Star", params.parent_name)
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

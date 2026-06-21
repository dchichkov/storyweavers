#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/carrot_kindness_reconciliation_flashback_folk_tale.py
======================================================================================

A small standalone storyworld in a folk-tale style: a child loses a carrot,
shows kindness, remembers an old slight in a flashback, and reaches
reconciliation with the helper who can restore the garden peace.

The world is built around:
- a shared garden space with physical meters and emotional memes,
- a simple forward causal model,
- a reasonableness gate,
- a Python/ASP twin,
- three grounded QA sets,
- and complete child-facing stories that end with a visible change.

This script is self-contained except for the shared Storyweavers result and ASP
helpers. It uses only the Python standard library for everything else.
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
KIND_HELP = 1.0
RECONCILE_HELP = 1.0


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
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    soil: str
    tree: str
    path: str
    season: str
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
class Item:
    id: str
    label: str
    phrase: str
    needed_for: str
    edible: bool = False
    fragile: bool = False
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
class Action:
    id: str
    verb: str
    small_harm: str
    big_harm: str
    remedy: str
    kindness_text: str
    reconciliation_text: str
    flashback_text: str
    power: int
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
            raise StoryError(f"Missing entity: {eid}")
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


def _r_drop(world: World) -> list[str]:
    out = []
    gardener = world.get("gardener")
    carrot = world.get("carrot")
    if carrot.meters["lost"] < THRESHOLD:
        return out
    sig = ("drop",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gardener.memes["worry"] += 1
    out.append("__drop__")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    helper = world.get("helper")
    child = world.get("child")
    if helper.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["hope"] += 1
    out.append("__kindness__")
    return out


def _r_reconciliation(world: World) -> list[str]:
    out = []
    helper = world.get("helper")
    child = world.get("child")
    if helper.meters["returned"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] += 1
    helper.memes["warmth"] += 1
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("drop", _r_drop), Rule("kindness", _r_kindness), Rule("reconcile", _r_reconciliation)]


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


def reasonableness(action: Action, item: Item) -> bool:
    return action.id in ACTIONS and item.id in ITEMS and item.needed_for == action.verb and item.edible


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for act in ACTIONS:
            for item in ITEMS:
                if reasonableness(ACTIONS[act], ITEMS[item]):
                    combos.append((setting, act, item))
    return combos


@dataclass
class StoryParams:
    setting: str
    action: str
    item: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    gardener_name: str
    gardener_gender: str
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


SETTINGS = {
    "orchard": Setting("orchard", "the orchard", "soft earth", "apple tree", "curving path", "spring"),
    "kitchen_garden": Setting("kitchen_garden", "the kitchen garden", "dark soil", "pear tree", "stone path", "summer"),
    "cottage_plot": Setting("cottage_plot", "the cottage plot", "loamy soil", "plum tree", "narrow path", "autumn"),
}

ITEMS = {
    "carrot": Item("carrot", "a bright carrot", "carrot", "pull", edible=True, fragile=True, tags={"carrot", "garden"}),
    "turnip": Item("turnip", "a round turnip", "turnip", "pull", edible=True, fragile=False, tags={"turnip", "garden"}),
    "beet": Item("beet", "a little beet", "beet", "pull", edible=True, fragile=False, tags={"beet", "garden"}),
}

ACTIONS = {
    "pull": Action(
        "pull",
        "pull it from the soil",
        "the root might snap and sink back into the earth",
        "the root could break clean in two and be lost",
        "put a small spoon under it and loosen the soil",
        "the child offered help instead of blame",
        "the helper and child mended their friendship",
        "the child remembered an earlier spring, when a shared seedling had been broken and both had cried",
        power=2,
        tags={"kindness", "reconciliation", "flashback", "carrot"},
    )
}

GIRL_NAMES = ["Mina", "Lena", "Tara", "Nora", "Ivy", "Pia"]
BOY_NAMES = ["Jasper", "Owen", "Eli", "Bram", "Noel", "Finn"]


def setup_story(world: World, params: StoryParams) -> None:
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name, role="helper"))
    gardener = world.add(Entity(id="gardener", kind="character", type=params.gardener_gender, label=params.gardener_name, role="gardener"))
    item = world.add(Entity(id="carrot", kind="thing", type="carrot", label=ITEMS[params.item].label, plural=False))
    child.memes["curiosity"] += 1
    helper.memes["kindness"] += 0.0
    gardener.memes["love"] += 1
    world.facts.update(child=child, helper=helper, gardener=gardener, item=item, action=ACTIONS[params.action], setting=world.setting)


def tell(world: World) -> None:
    f = world.facts
    child, helper, gardener, item, action = f["child"], f["helper"], f["gardener"], f["item"], f["action"]
    s = f["setting"]

    world.say(
        f"Once in {s.place}, {child.label} and {helper.label} walked the narrow path beside the rows of greens."
    )
    world.say(
        f"The earth was busy with {s.season} life, and a bright carrot was waiting under the leaves."
    )
    world.para()
    world.say(
        f"{child.label} reached for the carrot, but it slipped from the damp soil and vanished under a clump of roots."
    )
    child.meters["searching"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{helper.label} saw the worry and offered a kind hand: {action.kindness_text}."
    )
    helper.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.para()

    world.say(
        f"Then came a flashback. {child.label} remembered an earlier spring, when a shared seedling had been broken and both children had cried."
    )
    world.say(
        f"That old memory softened {child.label}'s heart, and {child.label} chose not to blame anyone."
    )
    child.memes["forgiveness"] += 1

    if helper.memes["kindness"] >= THRESHOLD:
        world.say(
            f"{helper.label} knelt beside the bed and used a small spoon to loosen the earth until the carrot showed its orange head again."
        )
        helper.meters["returned"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{child.label} lifted the carrot carefully and said, '{action.reconciliation_text.capitalize()}.'"
        )
        world.say(
            f"{gardener.label_word.capitalize()} smiled, because the row was safe again and the little quarrel had become a gentle friendship."
        )
    else:
        world.say(
            f"The child had no one gentle enough to help, and the carrot stayed hidden in the soil."
        )

    world.say(
        f"At the end, the carrot lay in {child.label}'s hands, the path was calm, and the garden felt like a place where a mistake could be healed."
    )

    world.facts["outcome"] = "reconciled"
    world.facts["flashback"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper = f["child"], f["helper"]
    return [
        f'Write a folk tale for a young child that includes the word "carrot" and shows {child.label} learning kindness in a garden.',
        f"Tell a small reconciliation story where {child.label} and {helper.label} remember an old hurt, then make peace and recover the carrot.",
        f"Write a gentle folk tale with a flashback, a lost carrot, and a kind helper who makes things right again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, gardener, action, item = f["child"], f["helper"], f["gardener"], f["action"], f["item"]
    return [
        ("Who is the story about?", f"It is about {child.label} and {helper.label} in the garden, with {gardener.label} watching over the beds."),
        ("What was lost in the soil?", f"A bright carrot was lost in the soil. It mattered because the children wanted to bring it back without breaking it."),
        ("What did the flashback show?", f"The flashback showed an earlier spring when a shared seedling had been broken. That memory helped the child choose kindness instead of blame."),
        ("How did the children make peace?", f"{helper.label} helped with a small spoon, and {child.label} answered with forgiveness. The two children were reconciled because they worked together and spoke gently."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a carrot?", "A carrot is a root vegetable that grows under the ground. It is often bright orange and crunchy."),
        ("Why do roots hide under soil?", "Roots grow under the soil so plants can hold on and drink water. That is why people sometimes have to pull vegetables gently from the earth."),
        ("What does kindness mean?", "Kindness means choosing a gentle way to help someone. It can soften anger and make a hard moment feel safer."),
        ("What is reconciliation?", "Reconciliation is when people who had a problem make peace again. They stop fighting and find a way to be friendly."),
        ("What is a flashback?", "A flashback is a memory of something that happened earlier. Stories use it to show why a character feels a certain way now."),
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about carrot, kindness, flashback, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--gardener-name")
    ap.add_argument("--gardener-gender", choices=["girl", "boy"])
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


def explain_rejection(item: Item) -> str:
    return f"(No story: {item.label} does not fit this little garden tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(list(ACTIONS))
    item = args.item or "carrot"
    if item not in ITEMS:
        raise StoryError("(No story: unknown item.)")
    if item != "carrot":
        raise StoryError(explain_rejection(ITEMS[item]))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    gardener_gender = args.gardener_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child_name])
    gardener_name = args.gardener_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n not in {child_name, helper_name}])
    return StoryParams(
        setting=setting,
        action=action,
        item=item,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        gardener_name=gardener_name,
        gardener_gender=gardener_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.action not in ACTIONS or params.item not in ITEMS:
        raise StoryError("(No story: invalid parameters.)")
    world = World(SETTINGS[params.setting])
    setup_story(world, params)
    tell(world)
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


ASP_RULES = r"""
chosen_carrot(carrot).
kindness_happens :- helper_kindness.
flashback_happens :- remembered_old_hurt.
reconciliation_happens :- kindness_happens, helper_returns, old_hurt_softened.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("power", aid, a.power))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        if iid == "carrot":
            lines.append(asp.fact("edible", iid))
            lines.append(asp.fact("needed_for", iid, "pull"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("python only:", sorted(py - cl))
        print("clingo only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as e:
        rc = 1
        print(f"FAILED: generate() smoke test crashed: {e}")
    return rc


def valid_story_combo(setting: str, action: str, item: str) -> bool:
    return setting in SETTINGS and action in ACTIONS and item in ITEMS and item == "carrot"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, a, i) for s in SETTINGS for a in ACTIONS for i in ITEMS if valid_story_combo(s, a, i)]


CURATED = [
    StoryParams(setting="orchard", action="pull", item="carrot", child_name="Mina", child_gender="girl", helper_name="Bram", helper_gender="boy", gardener_name="Lena", gardener_gender="girl"),
    StoryParams(setting="kitchen_garden", action="pull", item="carrot", child_name="Eli", child_gender="boy", helper_name="Nora", helper_gender="girl", gardener_name="Tara", gardener_gender="girl"),
    StoryParams(setting="cottage_plot", action="pull", item="carrot", child_name="Ivy", child_gender="girl", helper_name="Finn", helper_gender="boy", gardener_name="Jasper", gardener_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

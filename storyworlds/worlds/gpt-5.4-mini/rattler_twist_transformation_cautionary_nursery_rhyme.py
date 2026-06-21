#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rattler_twist_transformation_cautionary_nursery_rhyme.py
========================================================================================

A standalone storyworld for a tiny cautionary nursery-rhyme domain.

Premise
-------
A child hears a rattler in a garden and wants to look too close. A careful
sibling warns them, a grown-up helps with a safe plan, and the child learns to
watch wildlife from a distance.

The domain is built around three seed features:
- rattler
- Twist
- Transformation
- Cautionary
- Nursery Rhyme style

The story model is small on purpose: it keeps the tension focused on one
forbidden choice, one safe turn, and one ending image that proves the child
changed. It supports plain text output, JSON, QA, tracing, and a small ASP twin
for parity checks.
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
    bright_spot: str
    hiding_spot: str
    open_image: str

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
class Rattler:
    id: str
    label: str
    twist_sound: str
    slither_words: str
    caution: str
    cautious_distance: str
    dangerous: bool = True
    talks: bool = False

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
class SafeChoice:
    id: str
    label: str
    action: str
    ending: str
    allows_viewing: str
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
class World:
    setting: Setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

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


def _r_scared(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("rattler_seen") and not world.facts.get("safe_choice"):
        for ent in list(world.entities.values()):
            if ent.role in {"child", "sibling"}:
                ent.memes["worry"] += 1
        if ("scared",) not in world.fired:
            world.fired.add(("scared",))
            out.append("__scared__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("safe_choice") and not world.facts.get("lesson_done"):
        child = world.get("child")
        child.memes["caution"] += 1
        child.memes["wonder"] += 1
        world.facts["lesson_done"] = True
        out.append("__transform__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("scared", "social", _r_scared),
    Rule("transform", "social", _r_transform),
]


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


def setting_for(name: str) -> Setting:
    return SETTINGS[name]


def reasonableness_gate(rattler: Rattler, setting: Setting) -> bool:
    return rattler.dangerous and "garden" in setting.id


def sensible_choices() -> list[SafeChoice]:
    return [c for c in SAFE_CHOICES.values() if c.safe]


def best_choice() -> SafeChoice:
    return max(SAFE_CHOICES.values(), key=lambda c: len(c.ending))


def predict_danger(world: World, choice_id: str) -> dict:
    sim = world.copy()
    choice = SAFE_CHOICES[choice_id]
    sim.facts["safe_choice"] = choice.safe
    if choice.safe:
        propagate(sim, narrate=False)
    return {
        "worry": sim.get("child").memes["worry"],
        "lesson": sim.get("child").memes["caution"],
    }


def setup(world: World, child: Entity, sibling: Entity, setting: Setting, rattler: Rattler) -> None:
    child.memes["curiosity"] += 1
    sibling.memes["care"] += 1
    world.say(
        f"In {setting.place}, where the daisies bent and the green grass swayed, "
        f"{child.id} and {sibling.id} went a little way."
    )
    world.say(
        f"{setting.open_image} Then came a tiny sound: {rattler.twist_sound}, "
        f"from {setting.hiding_spot} away."
    )


def notice(world: World, child: Entity, rattler: Rattler) -> None:
    child.memes["curiosity"] += 1
    world.facts["rattler_seen"] = True
    world.say(
        f'"What is that?" {child.id} said low. "A {rattler.label}? A twisty toy?" '
        f"But the sound was not for play."
    )


def warn(world: World, sibling: Entity, child: Entity, rattler: Rattler) -> None:
    sibling.memes["caution"] += 1
    world.say(
        f'"Keep back," {sibling.id} said quick, "a {rattler.label} may hide and coil. '
        f'It likes its {rattler.cautious_distance}."'
    )
    world.say(
        f'"A {rattler.label} can mean danger, so we use our eyes, not our hands," '
        f"{sibling.id} said."
    )


def twist(world: World, child: Entity, rattler: Rattler) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'But {child.id} leaned in close, then stopped. "{rattler.label}," '
        f'{child.id} whispered, "you make a twisty sound."'
    )


def transform(world: World, choice: SafeChoice) -> None:
    world.facts["safe_choice"] = True
    world.say(
        f"Then the little scene changed its tune: {choice.action}. "
        f"{choice.ending}."
    )
    world.say(
        f"{choice.allows_viewing} The garden felt bright again, and the worry grew small."
    )


def ending(world: World, child: Entity, sibling: Entity, rattler: Rattler, choice: SafeChoice) -> None:
    child.memes["joy"] += 1
    sibling.memes["joy"] += 1
    child.memes["caution"] += 1
    world.say(
        f'{child.id} took one careful step back and nodded. '
        f'"No touch," {child.id} said. "Only look."'
    )
    world.say(
        f"{sibling.id} smiled, and together they watched from {rattler.cautious_distance}, "
        f"safe as a nursery rhyme."
    )
    world.say(
        f"By the last soft line, {child.id} had changed: from rush to care, "
        f"and from near to far."
    )


def tell(setting: Setting, rattler: Rattler, choice: SafeChoice,
         child_name: str = "Milly", child_gender: str = "girl",
         sibling_name: str = "Billy", sibling_gender: str = "boy",
         parent_name: str = "Mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    sibling = world.add(Entity(id=sibling_name, kind="character", type=sibling_gender, role="sibling"))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother", role="parent"))
    world.add(Entity(id="rattler", kind="thing", type="animal", label=rattler.label, role="hazard"))

    setup(world, child, sibling, setting, rattler)
    world.para()
    notice(world, child, rattler)
    warn(world, sibling, child, rattler)
    twist(world, child, rattler)
    world.para()
    transform(world, choice)
    ending(world, child, sibling, rattler, choice)

    world.facts.update(
        child=child, sibling=sibling, parent=parent, setting=setting,
        rattler=rattler, choice=choice, outcome="safe", safe_choice=True,
    )
    return world


SETTINGS = {
    "garden": Setting("garden", "the garden", "The marigolds were in a row, and the bees hummed by the fence.", "the stone wall", "The morning was blue and mild"),
    "yard": Setting("yard", "the yard", "The laundry flapped, and the little gate stood half-open.", "the berry bush", "The morning was bright and mild"),
    "orchard": Setting("orchard", "the orchard", "The apples shone, and the grass was soft underfoot.", "the old root", "The air was sweet and still"),
}

RATTLERS = {
    "snake": Rattler("snake", "rattler", "a soft rattle-rattle sound", "slithered in a coil", "keep back", "two whole steps away", True, False),
    "toy": Rattler("toy", "rattler toy", "a tiny rattle-rattle sound", "spun in a loop", "hold it gently", "one little arm away", False, False),
}

SAFE_CHOICES = {
    "call": SafeChoice("call", "call a grown-up", "called for Mother", "Mother came in calm and kind", "They stayed back and let the grown-up look first"),
    "back": SafeChoice("back", "back away slowly", "backed away slowly", "The rattler stayed where it was, and nobody hurt it or touched it", "They watched from a safe place"),
    "basket": SafeChoice("basket", "lift a basket over it from far away", "used a basket as a safe marker", "The basket made a little fence around the spot", "They could find the place again without touching it"),
}



def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for rid, rattler in RATTLERS.items():
            if reasonableness_gate(rattler, setting):
                for cid in sensible_choices():
                    combos.append((sid, rid, cid.id))
    return combos


@dataclass
class StoryParams:
    setting: str
    rattler: str
    choice: str
    child_name: str
    child_gender: str
    sibling_name: str
    sibling_gender: str
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
    ("garden", "snake", "call", "Milly", "girl", "Billy", "boy"),
    ("yard", "snake", "back", "Mara", "girl", "Ned", "boy"),
    ("orchard", "snake", "basket", "Pip", "boy", "Dot", "girl"),
]



def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary nursery-rhyme storyworld about a rattler, a twist, and a safe transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rattler", choices=RATTLERS)
    ap.add_argument("--choice", choices=SAFE_CHOICES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--sibling-name")
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
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
    if args.setting and args.rattler:
        if not reasonableness_gate(RATTLERS[args.rattler], SETTINGS[args.setting]):
            raise StoryError("(No story: this setting does not fit a cautionary rattler tale.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.rattler is None or c[1] == args.rattler)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, rattler, choice = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    sibling_gender = args.sibling_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or rng.choice(["Milly", "Tilly", "Rosie", "Poppy", "Nell", "Bobby", "Davy"])
    sibling_name = args.sibling_name or rng.choice(["Billy", "Tommy", "Mara", "Ned", "Kit", "Jo"])
    return StoryParams(setting, rattler, choice, child_name, child_gender, sibling_name, sibling_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery-rhyme style cautionary story about a child who hears a {f['rattler'].label} in {f['setting'].place}.",
        f"Tell a short story that includes the word 'rattler' and ends with a safe transformation from fear to careful watching.",
        f"Write a gentle rhyme where {f['child'].id} wants to touch the {f['rattler'].label}, but {f['sibling'].id} warns them and a grown-up helps."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, sibling, rattler, choice = f["child"], f["sibling"], f["rattler"], f["choice"]
    return [
        QAItem(
            question="What did the children hear in the garden?",
            answer=f"They heard a {rattler.label} making a soft rattle-rattle sound. It came from the hiding spot in the garden, so they knew to look carefully."
        ),
        QAItem(
            question=f"What did {child.id} want to do at first?",
            answer=f"{child.id} wanted to go closer and touch the {rattler.label}. {child.id} was curious, but that was not the safe choice."
        ),
        QAItem(
            question=f"How did {sibling.id} help?",
            answer=f"{sibling.id} warned {child.id} to stay back and use eyes, not hands. That caution kept the child from rushing in."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They chose to {choice.label}, and that changed the scene from risky to safe. In the end, they watched from a distance and felt calm again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rattler?",
            answer="A rattler is something that makes a little rattling sound. In a cautionary story, it can be a snake or a thing that tells you to keep back."
        ),
        QAItem(
            question="Why should you stay away from a snake you do not know?",
            answer="Because a snake may be dangerous and can bite if it feels scared. It is safer to step back and let a grown-up help."
        ),
        QAItem(
            question="What should you do when you hear a wild animal close by?",
            answer="You should stay calm, keep your hands to yourself, and call a grown-up. Looking from far away is safer than reaching out."
        ),
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_choice(call).
safe_choice(back).
safe_choice(basket).

sensible(C) :- safe_choice(C).

valid(S, R, C) :- setting(S), rattler(R), choice(C), garden_setting(S), dangerous(R), sensible(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SETTINGS:
        if sid == "garden":
            lines.append(asp.fact("garden_setting", sid))
    for rid in RATTLERS:
        lines.append(asp.fact("rattler", rid))
        if RATTLERS[rid].dangerous:
            lines.append(asp.fact("dangerous", rid))
    for cid in SAFE_CHOICES:
        lines.append(asp.fact("choice", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, rattler=None, choice=None, child_name=None,
            child_gender=None, sibling_name=None, sibling_gender=None
        ), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], RATTLERS[params.rattler], SAFE_CHOICES[params.choice],
                 params.child_name, params.child_gender, params.sibling_name, params.sibling_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for setting, rattler, choice, child_name, child_gender, sibling_name, sibling_gender in CURATED:
            params = StoryParams(setting, rattler, choice, child_name, child_gender, sibling_name, sibling_gender)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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

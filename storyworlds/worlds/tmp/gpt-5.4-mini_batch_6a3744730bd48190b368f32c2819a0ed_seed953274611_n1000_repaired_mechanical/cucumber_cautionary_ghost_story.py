#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cucumber_cautionary_ghost_story.py
==================================================================

A small cautionary ghost-story world for a child who hears a spooky warning
about a cucumber patch after dark. The domain is intentionally tiny: a child,
a caretaker, a place, a forbidden choice, a ghostly consequence, and a safe
turn that avoids the bad outcome.

The story premise is inspired by a classic ghost-story beat:
a child wants to sneak to a strange garden place at night, hears a warning,
ignores it or heeds it depending on the scenario, and learns why the caution
matters. The world model tracks a physical trail, a spooky meter, and a few
emotional shifts so the prose is driven by state rather than templates alone.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SAFE_MIN = 2

GIRL_NAMES = ["Mina", "Iris", "Lena", "Nora", "Ada"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Eli", "Noah"]
CARETAKERS = ["grandma", "grandpa", "aunt", "uncle"]
PLACES = {
    "garden": {"label": "the back garden", "ghosty": "the cucumber rows by the fence"},
    "greenhouse": {"label": "the greenhouse", "ghosty": "the fogged cucumber shelves"},
    "allotment": {"label": "the allotment", "ghosty": "the cucumber bed behind the shed"},
}
TIMES = ["dusk", "midnight", "late evening"]
WARNINGS = {
    "do_not_poke": "don't poke strange things after dark",
    "do_not_pick": "don't pick the cucumbers that look like they are listening",
}
ACTIONS = {
    "sneak": {
        "verb": "sneak out",
        "rush": "tiptoe toward the garden",
        "mess": "muddy",
        "risk": "left little prints in the soil",
    },
    "peek": {
        "verb": "peek through the fence",
        "rush": "edge closer to the rows",
        "mess": "cold",
        "risk": "made the air feel colder",
    },
    "touch": {
        "verb": "touch the cucumber patch",
        "rush": "reach for the nearest leaf",
        "mess": "spooky",
        "risk": "woke the whispering vines",
    },
}
CONSEQUENCES = {
    "clang": {
        "sense": 3,
        "power": 3,
        "success": "closed the creaky gate, steadied the lantern, and led {child} back inside before the whispering got any louder",
        "fail": "shook the gate, but the garden was already full of whispers",
        "qa": "closed the gate and guided {child} safely back inside",
    },
    "cover": {
        "sense": 3,
        "power": 2,
        "success": "held a wool blanket over the lantern glow and walked {child} home with a calm hand on {child_possessive} shoulder",
        "fail": "tried to cover the light, but the shadows still slipped under the door",
        "qa": "covered the lantern glow and took {child} home",
    },
    "call": {
        "sense": 2,
        "power": 4,
        "success": "called softly from the porch and whistled until {child} answered, then brought {child} back to the warm kitchen",
        "fail": "called and called, but the wind swallowed the voice",
        "qa": "called {child} back from the porch",
    },
}
SENSIBLE_CONSEQUENCES = {k: v for k, v in CONSEQUENCES.items() if v["sense"] >= SAFE_MIN}


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
        female = {"girl", "mother", "mom", "woman", "aunt", "grandmother"}
        male = {"boy", "father", "dad", "man", "uncle", "grandfather"}
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
class CucumberPatch:
    id: str
    place: str
    ghosty: str
    whisper: str
    flurry: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    caretaker: str
    caretaker_type: str
    action: str
    consequence: str
    warning: str
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
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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


def _r_whisper(world: World) -> list[str]:
    out = []
    patch = world.get("patch")
    child = world.get("child")
    if patch.meters["disturbed"] >= THRESHOLD and ("whisper",) not in world.fired:
        world.fired.add(("whisper",))
        patch.meters["spooky"] += 1
        child.memes["fear"] += 1
        out.append("__whisper__")
    return out


CAUSAL_RULES = [_r_whisper]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for action in ACTIONS:
            for consequence in CONSEQUENCES:
                combos.append((place, action, consequence))
    return combos


def sensible_consequences() -> list[str]:
    return [k for k, v in CONSEQUENCES.items() if v["sense"] >= SAFE_MIN]


def explain_consequence(rid: str) -> str:
    r = CONSEQUENCES[rid]
    return (
        f"(Refusing consequence '{rid}': it is too weakly sensible "
        f"(sense={r['sense']} < {SAFE_MIN}). Pick a calmer grown-up action.)"
    )


def predict_spook(world: World, action: str) -> float:
    sim = world.copy()
    sim.get("patch").meters["disturbed"] += 1
    propagate(sim, narrate=False)
    return sim.get("patch").meters["spooky"]


def disturb_patch(world: World, child: Entity, patch: CucumberPatch, action: str) -> None:
    child.meters["mischief"] += 1
    patch.meters["disturbed"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} could not stop thinking about the cucumber rows. "
        f"{child.id} {ACTIONS[action]['verb']} after dark, and the garden seemed to hold its breath."
    )


def warn(world: World, caretaker: Entity, child: Entity, warning: str, patch: CucumberPatch) -> None:
    fear = predict_spook(world, "touch")
    if fear >= THRESHOLD:
        world.say(
            f'"{warning}," {caretaker.id} said softly. '
            f'"The cucumbers are not for nighttime games, and {patch.ghosty} can make a child feel very small."'
        )


def defy_or_listen(world: World, child: Entity, listens: bool) -> None:
    if listens:
        child.memes["relief"] += 1
    else:
        child.memes["defiance"] += 1


def ghostly_turn(world: World, patch: CucumberPatch) -> None:
    if patch.meters["spooky"] >= THRESHOLD:
        world.say(
            f"Then a thin whisper slid through the leaves. It was only the wind, but it sounded like the garden was warning them."
        )


def consequence_scene(world: World, caretaker: Entity, child: Entity, consequence: str) -> None:
    cons = CONSEQUENCES[consequence]
    if cons["sense"] < SAFE_MIN:
        raise StoryError(explain_consequence(consequence))
    world.say(
        f"{caretaker.id} came quickly and {cons['success'].format(child=child.id, child_possessive=child.pronoun('possessive'))}."
    )


def resolution(world: World, caretaker: Entity, child: Entity, patch: CucumberPatch) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f"By the time they reached the kitchen, the cucumbers were behind them, the lantern was steady, and the house felt warm again."
    )
    world.say(
        f"{caretaker.id} set a cucumber on the table for breakfast and said that some things are best admired in daylight."
    )


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, role="child"))
    caretaker = world.add(Entity(id=params.caretaker, kind="character", type=params.caretaker_type, role="caretaker"))
    patch = world.add(CucumberPatch(id="patch", place=PLACES[params.place]["label"], ghosty=PLACES[params.place]["ghosty"], whisper="whisper", flurry="flutter", tags={"cucumber", "ghost"}))
    child.memes["curiosity"] = 1.0

    world.say(
        f"At {patch.place}, the cucumber vines made the evening look darker than it really was."
    )
    world.say(
        f"{child.id} had heard that the garden could be spooky after dark, but the thought of the cucumbers kept pulling {child.pronoun('object')} closer."
    )
    world.para()

    disturb_patch(world, child, patch, params.action)
    warn(world, caretaker, child, params.warning, patch)

    if params.action == "sneak":
        ghostly_turn(world, patch)
    else:
        patch.meters["spooky"] += 0.5

    listens = params.action == "peek"
    defy_or_listen(world, child, listens)

    world.para()
    consequence_scene(world, caretaker, child, params.consequence)
    resolution(world, caretaker, child, patch)

    outcome = "safe"
    world.facts.update(
        child=child,
        caretaker=caretaker,
        patch=patch,
        consequence=params.consequence,
        action=params.action,
        warning=params.warning,
        outcome=outcome,
        spooky=patch.meters["spooky"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary ghost story for a young child that includes the word "cucumber" and a spooky garden warning.',
        f"Tell a gentle ghost story where {f['child'].id} wants to wander near the cucumber patch after dark, but {f['caretaker'].id} warns them and brings them back safely.",
        f"Write a short spooky story where the cucumbers feel a little haunted, but the ending teaches children to listen to a grown-up at night.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caretaker = f["caretaker"]
    patch = f["patch"]
    return [
        QAItem(
            question="Why did the garden feel spooky?",
            answer=(
                f"The cucumber rows stood in the dark and made the garden look shadowy. "
                f"The wind through {patch.ghosty} also made the place seem haunted, even though it was only the wind."
            ),
        ),
        QAItem(
            question=f"What did {caretaker.id} warn {child.id} about?",
            answer=(
                f"{caretaker.id} warned {child.id} not to play near the cucumber patch after dark. "
                f"The warning mattered because the dark made ordinary garden sounds feel strange."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended safely, with the child back inside and the cucumbers left in the garden. "
                f"The last image shows a warm kitchen instead of a spooky row of plants."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cucumber?",
            answer="A cucumber is a long green vegetable that grows on vines. People can eat it fresh or in a salad.",
        ),
        QAItem(
            question="Why can dark places feel spooky?",
            answer="Dark places hide details, so normal things can seem strange or scary. A little noise or shadow can make a place feel haunted.",
        ),
        QAItem(
            question="What should a child do if a grown-up gives a safety warning?",
            answer="A child should listen and stay close to the grown-up. Safety warnings are there to keep the child from getting hurt or frightened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({getattr(e, 'kind', 'thing')}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(C) :- consequence(C), sense(C,S), safe_min(M), S >= M.
safe_story(P,A,C) :- place(P), action(A), consequence(C), sensible(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for c, v in CONSEQUENCES.items():
        lines.append(asp.fact("consequence", c))
        lines.append(asp.fact("sense", c, v["sense"]))
    lines.append(asp.fact("safe_min", SAFE_MIN))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_story/3."))
    return sorted(set(asp.atoms(model, "safe_story")))

def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    sample_ok = False
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        sample_ok = bool(sample.story)
    except Exception:
        sample_ok = False
    if ok:
        print(f"OK: ASP gate matches Python ({len(py)} combos).")
    else:
        print("MISMATCH in ASP/Python gate.")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))
    if sample_ok:
        print("OK: story generation smoke test passed.")
    else:
        print("FAIL: story generation smoke test failed.")
    return 0 if ok and sample_ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary cucumber ghost story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=CARETAKERS)
    ap.add_argument("--caretaker-type", choices=["mother", "father", "aunt", "uncle", "grandmother", "grandfather"])
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--consequence", choices=CONSEQUENCES)
    ap.add_argument("--warning", choices=WARNINGS)
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
    if args.consequence and CONSEQUENCES[args.consequence]["sense"] < SAFE_MIN:
        raise StoryError(explain_consequence(args.consequence))
    place = args.place or rng.choice(list(PLACES))
    action = args.action or rng.choice(list(ACTIONS))
    consequence = args.consequence or rng.choice(list(SENSIBLE_CONSEQUENCES))
    warning = args.warning or rng.choice(list(WARNINGS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.name if hasattr(args, "name") and getattr(args, "name", None) else rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    caretaker = args.caretaker or rng.choice(CARETAKERS)
    caretaker_type = args.caretaker_type or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    return StoryParams(
        place=place,
        child_name=child_name,
        child_type=child_type,
        caretaker=caretaker,
        caretaker_type=caretaker_type,
        action=action,
        consequence=consequence,
        warning=warning,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("unknown place")
    if params.action not in ACTIONS:
        raise StoryError("unknown action")
    if params.consequence not in CONSEQUENCES:
        raise StoryError("unknown consequence")
    if CONSEQUENCES[params.consequence]["sense"] < SAFE_MIN:
        raise StoryError(explain_consequence(params.consequence))
    world = tell(params)
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


CURATED = [
    StoryParams(place="garden", child_name="Mina", child_type="girl", caretaker="grandma", caretaker_type="grandmother", action="peek", consequence="clang", warning="do_not_poke"),
    StoryParams(place="greenhouse", child_name="Owen", child_type="boy", caretaker="uncle", caretaker_type="uncle", action="sneak", consequence="call", warning="do_not_pick"),
    StoryParams(place="allotment", child_name="Iris", child_type="girl", caretaker="aunt", caretaker_type="aunt", action="touch", consequence="cover", warning="do_not_poke"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show safe_story/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) != 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

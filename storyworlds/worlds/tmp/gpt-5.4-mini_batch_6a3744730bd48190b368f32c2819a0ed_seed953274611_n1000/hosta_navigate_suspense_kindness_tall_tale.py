#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hosta_navigate_suspense_kindness_tall_tale.py
=============================================================================

A standalone story world in a tall-tale style: a child, a grand hosta garden,
a suspenseful navigation problem, and a kindness turn that saves the day.

The seed words are intentionally embedded in the world:
- hosta
- navigate

The story premise is small and classical:
A child tries to navigate through a confusing garden path in a sudden fog.
A towering hosta patch hides the way, suspense grows, and a kind helper gives
clear directions and a lantern, leading to a safe ending image that proves the
change.

The world uses:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate
- an inline ASP twin
- three QA sets grounded in world state
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    pathwise: bool = False
    glows: bool = False
    tall: bool = False
    leafy: bool = False

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
        return self.label or self.type


@dataclass
class Place:
    id: str
    name: str
    cover: str
    route: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    name: str
    clue: str
    can_confuse: bool = True
    can_hide: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class GuideItem:
    id: str
    name: str
    phrase: str
    helps_navigate: bool = True
    glows: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class KindnessMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hazard: str
    guide: str
    kindness: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None
    fog: int = 1
    delay: int = 0
    hero_age: int = 6
    helper_age: int = 9
    relation: str = "friends"


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
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    fog = world.get("fog")
    if fog.meters["foggy"] < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["unease"] += 1
    world.get("guide").memes["focus"] += 1
    out.append("__suspense__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    hero = world.get("hero")
    if helper.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hope"] += 1
    out.append("__hope__")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("kindness", _r_kindness)]


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


def reasonableness_ok(place: Place, hazard: Hazard, guide: GuideItem, kindness: KindnessMove) -> bool:
    return place.id != "open_field" and hazard.can_hide and guide.helps_navigate and kindness.sense >= 2


def sensible_kindnesses() -> list[KindnessMove]:
    return [k for k in KINDNESSES.values() if k.sense >= 2]


def choose_outcome(kindness: KindnessMove, fog: int, delay: int) -> str:
    return "safe" if kindness.power >= fog + delay else "lost"


def predict(world: World, place_id: str, fog: int) -> dict:
    sim = world.copy()
    sim.get("fog").meters["foggy"] += fog
    propagate(sim, narrate=False)
    return {
        "unease": sim.get("hero").memes["unease"],
        "hope": sim.get("hero").memes["hope"],
    }


def tell(place: Place, hazard: Hazard, guide: GuideItem, kindness: KindnessMove,
         hero_name: str = "Mabel", hero_gender: str = "girl",
         helper_name: str = "Aunt June", helper_gender: str = "woman",
         parent_name: str = "Mother", fog: int = 1, delay: int = 0,
         hero_age: int = 6, helper_age: int = 9, relation: str = "friends") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero",
                            traits=["brave"], attrs={"relation": relation}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper",
                              traits=["kind"], attrs={"relation": relation}))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother", role="parent",
                              label="Mother"))
    fog_ent = world.add(Entity(id="fog", type="thing", label="fog"))
    hosta = world.add(Entity(id="hosta", type="plant", label="hosta", tall=True, leafy=True))
    lantern = world.add(Entity(id="lantern", type="tool", label=guide.name, glows=True))
    path = world.add(Entity(id="path", type="place", label=place.name, pathwise=True))

    hero.memes["curiosity"] += 1
    helper.memes["kindness"] += 1
    if fog > 0:
        fog_ent.meters["foggy"] += fog

    world.say(
        f"One late evening, {hero.id} and {helper.id} stood where the garden path forked like a snake with two tails. "
        f"Behind them rose a giant patch of hosta, broad as wagon wheels and quiet as a secret."
    )
    world.say(
        f'"We must navigate before the fog swallows the whole lane," said {helper.id}, '
        f'and {hero.id} felt the words tickle the air like a warning bell.'
    )

    world.para()
    hero.memes["unease"] += 1
    world.say(
        f"Then the fog came in soft and thick, and even the lantern looked like a tiny moon. "
        f"The hosta leaves leaned together, hiding the stones that marked the way home."
    )
    world.say(
        f'{hero.id} peered into the blur. "{hero.id} can navigate this," {hero.pronoun()} said, '
        f"though {hero.pronoun('possessive')} voice sounded smaller than a raindrop."
    )
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{helper.id} did not laugh. {helper.pronoun().capitalize()} lifted the lantern, "
        f"held it high, and pointed out the stepping stones one by one."
    )
    pred = predict(world, "fog", fog)
    world.facts["predicted_unease"] = pred["unease"]
    world.facts["predicted_hope"] = pred["hope"]
    world.say(
        f'"Easy now," {helper.id} said. "Kind hands can help a traveler navigate a hard path."'
    )

    outcome = choose_outcome(kindness, fog, delay)
    if outcome == "safe":
        world.para()
        hero.memes["hope"] += 2
        hero.memes["fear"] = 0
        world.say(
            f"{helper.id} gave {hero.id} the lantern, and together they counted the steps until the path widened."
        )
        world.say(
            f"When the fog thinned, the hosta patch turned from a hiding place into a green guardrail, "
            f"and the children came out smiling with dew on their shoes."
        )
        world.say(
            f"{parent.name if hasattr(parent, 'name') else parent.id} would later say the night was a tall tale, "
            f"but the lantern still glowed by the gate, proving they had found the way home."
        )
    else:
        world.para()
        hero.memes["fear"] += 2
        world.say(
            f"{helper.id} tried to help, but the fog stayed thick as oatmeal and the stepping stones vanished."
        )
        world.say(
            f"They had to stand very still and call for {parent.id}, who came with a brighter lamp and walked them out."
        )
        world.say(
            f"Even then, the hosta leaves shook with mist, and the little lantern looked brave but too weak for the night."
        )

    world.facts.update(
        hero=hero, helper=helper, parent=parent, place_cfg=place, hazard=hazard,
        guide_cfg=guide, kindness_cfg=kindness, fog=fog, delay=delay, outcome=outcome,
        lantern=lantern, hosta=hosta, path=path
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        name="the garden path",
        cover="hosta leaves",
        route="stone path",
        danger="fog",
        tags={"garden", "path"},
    ),
    "maze": Place(
        id="maze",
        name="the hedge maze",
        cover="hedges",
        route="twisting lane",
        danger="fog",
        tags={"maze", "path"},
    ),
    "orchard": Place(
        id="orchard",
        name="the orchard lane",
        cover="apple boughs",
        route="old cart track",
        danger="fog",
        tags={"orchard", "path"},
    ),
}

HAZARDS = {
    "fog": Hazard(id="fog", name="fog", clue="a silver blur", tags={"fog", "suspense"}),
    "twilight": Hazard(id="twilight", name="twilight", clue="a dim blue hush", tags={"twilight"}),
}

GUIDES = {
    "lantern": GuideItem(id="lantern", name="lantern", phrase="a lantern that shone like a barn star", tags={"lantern"}),
    "rope": GuideItem(id="rope", name="rope", phrase="a rope tied to the gate", tags={"rope"}),
    "whistle": GuideItem(id="whistle", name="whistle", phrase="a whistle to call back", tags={"whistle"}),
}

KINDNESSES = {
    "lantern_help": KindnessMove(id="lantern_help", sense=3, power=3,
                                 text="lit the lantern and shared the light",
                                 fail="held the lantern too low and the path vanished again",
                                 qa_text="lit the lantern and shared the light",
                                 tags={"kindness", "light"}),
    "hand_guide": KindnessMove(id="hand_guide", sense=3, power=2,
                               text="took the child's hand and guided the steps",
                               fail="guided too slowly and the fog won the moment",
                               qa_text="took the child's hand and guided the steps",
                               tags={"kindness", "help"}),
    "call_home": KindnessMove(id="call_home", sense=2, power=4,
                              text="called home and brought a brighter lamp",
                              fail="called too late for the little lamp to matter",
                              qa_text="called home and brought a brighter lamp",
                              tags={"kindness", "help"}),
    "blanket_wait": KindnessMove(id="blanket_wait", sense=1, power=1,
                                 text="wrapped the child in a blanket and waited",
                                 fail="wrapped the child in a blanket and waited",
                                 qa_text="wrapped the child in a blanket and waited",
                                 tags={"kindness"}),
}

GIRL_NAMES = ["Mabel", "Nora", "Ivy", "June", "Rose"]
BOY_NAMES = ["Eli", "Milo", "Owen", "Theo", "Ben"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for h in HAZARDS:
            for g in GUIDES:
                for k in KINDNESSES:
                    if reasonableness_ok(PLACES[p], HAZARDS[h], GUIDES[g], KINDNESSES[k]):
                        combos.append((p, h, g, k))
    return combos


def explain_rejection(place: Place, hazard: Hazard, guide: GuideItem, kindness: KindnessMove) -> str:
    if kindness.sense < 2:
        return f"(No story: {kindness.id} is too weak-minded for a real suspense story.)"
    return "(No story: that combination does not make a believable navigation problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about hosta, navigate, kindness, and suspense.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--parent")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              and (args.hazard is None or c[1] == args.hazard)
              and (args.guide is None or c[2] == args.guide)
              and (args.kindness is None or c[3] == args.kindness)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    if args.kindness and KINDNESSES[args.kindness].sense < 2:
        raise StoryError(explain_rejection(PLACES[args.place or "garden"], HAZARDS[args.hazard or "fog"], GUIDES[args.guide or "lantern"], KINDNESSES[args.kindness]))
    place, hazard, guide, kindness = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or "Aunt June"
    parent = args.parent or "Mother"
    helper_gender = "woman"
    return StoryParams(place=place, hazard=hazard, guide=guide, kindness=kindness,
                       hero=name, hero_gender=gender, helper=helper,
                       helper_gender=helper_gender, parent=parent,
                       fog=rng.randint(1, 2), delay=rng.randint(0, 1),
                       hero_age=rng.randint(5, 7), helper_age=rng.randint(8, 12),
                       relation="friends")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale-style story that includes the words "hosta" and "navigate" and turns a garden fog into a suspenseful adventure.',
        f"Tell a child-friendly story where {f['hero'].id} must navigate past towering hosta leaves, and {f['helper'].id} answers with kindness.",
        f'Write a suspense story with a warm ending: the path is hidden, the helper is kind, and the word "hosta" appears in the garden scene.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, parent = f["hero"], f["helper"], f["parent"]
    qa = [
        QAItem(
            question="What was the problem in the story?",
            answer=(
                f"The garden path was hidden by fog and the tall hosta patch, so {hero.id} could not easily navigate home. "
                f"The suspense came from not being able to see the stones that marked the way."
            ),
        ),
        QAItem(
            question="How did the helper show kindness?",
            answer=(
                f"{helper.id} did not tease {hero.id}. {helper.pronoun().capitalize()} lifted the lantern, shared the light, and guided the steps one by one."
            ),
        ),
        QAItem(
            question="What changed by the end?",
            answer=(
                f"At the end, {hero.id} was calm instead of worried, and the lantern and kindness carried the children safely out of the garden. "
                f"The hosta patch became a green border instead of a hiding place."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hosta?",
            answer="A hosta is a leafy garden plant with big broad leaves. It can make a path look hidden when it grows thick.",
        ),
        QAItem(
            question="What does it mean to navigate?",
            answer="To navigate means to find your way from one place to another. People navigate by looking for signs, lights, or landmarks.",
        ),
        QAItem(
            question="Why can fog be tricky?",
            answer="Fog makes the air look white and blurry, so it can hide paths and signs. That is why people often move carefully in fog.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (("pathwise", e.pathwise), ("glows", e.glows), ("tall", e.tall), ("leafy", e.leafy)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
foggy :- meters(fog, F), F >= 1.
suspense :- foggy, helper(helper).
kindness :- kind_move(K), sense(K, S), S >= sense_min.
safe :- kindness, power(K, P), fog_amount(F), delay(D), P >= F + D.
outcome(safe) :- safe.
outcome(lost) :- not safe.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
    for gid, g in GUIDES.items():
        lines.append(asp.fact("guide", gid))
    for kid, k in KINDNESSES.items():
        lines.append(asp.fact("kind_move", kid))
        lines.append(asp.fact("sense", kid, k.sense))
        lines.append(asp.fact("power", kid, k.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    asp_out = asp.atoms(model, "outcome")
    py = {choose_outcome(k, 1, 0) for k in KINDNESSES.values() if k.sense >= 2}
    if not asp_out:
        print("MISMATCH: ASP produced no outcome.")
        return 1
    print("OK: ASP program runs.")
    sample_params = StoryParams(place="garden", hazard="fog", guide="lantern", kindness="lantern_help", hero="Mabel", hero_gender="girl", helper="Aunt June", helper_gender="woman", parent="Mother")
    try:
        sample = generate(sample_params)
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"MISMATCH: generation failed: {exc}")
        return 1
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    return sorted(set(asp.atoms(model, "outcome")))


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.hazard not in HAZARDS or params.guide not in GUIDES or params.kindness not in KINDNESSES:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    hazard = HAZARDS[params.hazard]
    guide = GUIDES[params.guide]
    kindness = KINDNESSES[params.kindness]
    if not reasonableness_ok(place, hazard, guide, kindness):
        raise StoryError(explain_rejection(place, hazard, guide, kindness))
    world = tell(place, hazard, guide, kindness, params.hero, params.hero_gender, params.helper,
                 params.helper_gender, params.parent, params.fog, params.delay, params.hero_age,
                 params.helper_age, params.relation)
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
    StoryParams(place="garden", hazard="fog", guide="lantern", kindness="lantern_help",
                hero="Mabel", hero_gender="girl", helper="Aunt June", helper_gender="woman",
                parent="Mother", fog=1, delay=0),
    StoryParams(place="orchard", hazard="fog", guide="lantern", kindness="hand_guide",
                hero="Eli", hero_gender="boy", helper="Aunt June", helper_gender="woman",
                parent="Mother", fog=1, delay=0),
    StoryParams(place="maze", hazard="fog", guide="whistle", kindness="call_home",
                hero="Ivy", hero_gender="girl", helper="Aunt June", helper_gender="woman",
                parent="Mother", fog=2, delay=0),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Inline ASP twin is available, but this world exposes only outcome verification.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

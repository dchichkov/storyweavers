#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tackle_kindness_nursery_rhyme.py
=================================================================

A tiny, standalone story world for a nursery-rhyme-style tale about kindness,
a small problem, and a gentle tackle.

Seed idea
---------
A child in a rhyme-like world sees a thing in trouble, asks for a little help,
and uses kindness to tackle the problem without roughness.

This world keeps the plot small:
- a child notices a snag
- a helper warns that a hard tackle could make things worse
- the child chooses a kind tackle instead
- the ending proves the change in the world state

The word "tackle" appears in the story in a child-friendly way: it means to
handle a problem bravely, not to bump or wrestle anyone.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/tackle_kindness_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/tackle_kindness_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4-mini/tackle_kindness_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/tackle_kindness_nursery_rhyme.py --trace
    python storyworlds/worlds/gpt-5.4-mini/tackle_kindness_nursery_rhyme.py --json
    python storyworlds/worlds/gpt-5.4-mini/tackle_kindness_nursery_rhyme.py --verify
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
    region: str = ""
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rhyme_open: str
    little_problem: str
    ending_image: str


@dataclass
class Trouble:
    id: str
    label: str
    kind: str
    can_spill: bool = False
    can_tangle: bool = False


@dataclass
class KindAction:
    id: str
    verb: str
    gentle_way: str
    result: str
    help_word: str
    power: int
    sense: int


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["tangled"] < THRESHOLD and ent.meters["spilled"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["mess"] += 1
        for ent2 in world.entities.values():
            if ent2.kind == "character":
                ent2.memes["concern"] += 1
        out.append("__mess__")
    return out


CAUSAL_RULES = [Rule("spread", "physical", _r_spill)]


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


def kind_tackle_ok(trouble: Trouble) -> bool:
    return trouble.can_spill or trouble.can_tangle


def sensible_actions() -> list[KindAction]:
    return [a for a in ACTIONS.values() if a.sense >= 2]


def is_helpful(action: KindAction, trouble: Trouble) -> bool:
    return action.power >= (2 if trouble.can_tangle else 1)


def tell(world_theme: Theme, trouble: Trouble, action: KindAction,
         child_name: str, child_gender: str, helper_name: str,
         helper_gender: str, helper_role: str = "helper") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=["kind", "small"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role=helper_role, traits=["gentle"]))
    problem = world.add(Entity(id="trouble", label=trouble.label))
    room = world.add(Entity(id="room", type="room", label="the room"))
    child.memes["kindness"] = 1.0
    helper.memes["care"] = 1.0

    world.say(
        f"{world_theme.rhyme_open} {child.id} stepped in with a smile so bright; "
        f"in {world_theme.scene}, the day felt light."
    )
    world.say(
        f"{child.id} saw {trouble.label} and said, \"Oh dear!\" "
        f"{world_theme.little_problem}"
    )
    world.para()

    if not kind_tackle_ok(trouble):
        raise StoryError("This trouble is too small and ordinary to be a meaningful tackle.")

    child.memes["bravery"] += 1
    world.say(
        f"{helper.id} softly said, \"A hard tackle may tug too rough; "
        f"kind hands are usually enough.\""
    )
    world.say(
        f"{child.id} nodded and chose to {action.gentle_way}, "
        f"which was a kind way to tackle the trouble."
    )

    # If the action is helpful, it changes the world; otherwise it makes the mess worse.
    if is_helpful(action, trouble):
        problem.meters["spilled"] = 0.0
        problem.meters["tangled"] = 0.0
        room.meters["mess"] = 0.0
        child.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.say(
            f"It worked at once: {action.result}. The little trouble settled down, "
            f"and the room grew calm again."
        )
        world.para()
        world.say(
            f"{world_theme.ending_image} {child.id} and {helper.id} laughed, "
            f"for kindness had tackled the problem without a shove."
        )
        outcome = "kind"
    else:
        problem.meters["spilled"] = 1.0
        problem.meters["tangled"] = 1.0
        propagate(world, narrate=False)
        child.memes["worry"] += 1
        world.say(
            f"But that way was too weak, and the trouble only got bigger. "
            f"{child.id} called for help right away."
        )
        world.para()
        world.say(
            f"{helper.id} fixed it with a kinder, stronger touch, and the day "
            f"ended safe and still."
        )
        outcome = "recovered"

    world.facts.update(
        theme=world_theme,
        trouble=trouble,
        action=action,
        child=child,
        helper=helper,
        outcome=outcome,
    )
    return world


THEMES = {
    "nursery": Theme(
        "nursery",
        "a cozy little nursery rhyme yard",
        "Hush now, hush now, under the tree,",
        "A ribbon was loose and a kite string cried,",
        "At the end, the ribbon sat neat and tied.",
    ),
    "moon": Theme(
        "moon",
        "a silver moonlit garden",
        "Round went the stars, and round went the breeze,",
        "A lantern had tipped by the rosemary trees,",
        "At the end, the lantern stood safe with ease.",
    ),
    "meadow": Theme(
        "meadow",
        "a bright green meadow path",
        "Skip said the daisies, blink said the dew,",
        "A basket had fallen and berries rolled through,",
        "At the end, the berries were gathered anew.",
    ),
}

TROUBLES = {
    "ribbon": Trouble("ribbon", "a loose ribbon", "tangle", can_tangle=True),
    "lantern": Trouble("lantern", "a tipped lantern", "spill", can_spill=True),
    "basket": Trouble("basket", "a fallen basket of berries", "spill", can_spill=True),
}

ACTIONS = {
    "untie": KindAction("untie", "untie the knot", "untie the knot gently", "the ribbon was neat again", "gentle hands", 2, 3),
    "upright": KindAction("upright", "set it upright", "set it upright with care", "the lantern stood steady", "careful hands", 2, 3),
    "gather": KindAction("gather", "gather the berries", "gather the berries one by one", "the berries went back in the basket", "patient hands", 3, 3),
    "tug": KindAction("tug", "tug hard", "tug hard and hope", "nothing much changed", "rough hands", 0, 1),
}

CHILD_NAMES = ["Mia", "Nora", "Leo", "Finn", "Ava", "Theo", "Luna", "Ivy"]
HELPER_NAMES = ["Rose", "Pip", "Mabel", "Hugo", "June", "Ollie"]


@dataclass
class StoryParams:
    theme: str
    trouble: str
    action: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in THEMES:
        for tr in TROUBLES:
            for ac in ACTIONS:
                if kind_tackle_ok(TROUBLES[tr]) and ACTIONS[ac].sense >= 2 and is_helpful(ACTIONS[ac], TROUBLES[tr]):
                    combos.append((t, tr, ac))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme, trouble, action = f["theme"], f["trouble"], f["action"]
    return [
        f'Write a nursery-rhyme-style story where someone notices {trouble.label} in {theme.scene} and uses the word "tackle" in a kind way.',
        f"Tell a small child story with a gentle rhyme feel, where {f['child'].id} learns to tackle {trouble.label} kindly, not roughly.",
        f'Write a cozy rhyming story about kindness, a little problem, and a brave child who chooses to {action.gentle_way}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, trouble, action = f["child"], f["helper"], f["trouble"], f["action"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}. They are the ones who noticed the little trouble and worked together kindly."),
        ("What did {0} do to tackle the problem?".format(child.id),
         f"{child.id} chose to {action.gentle_way}. That was a kind way to tackle the trouble instead of roughness."),
        ("How did the story end?",
         f"It ended with the trouble safely handled and the world calm again. The last image shows {trouble.label} fixed and kindness winning."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does kindness mean?",
         "Kindness means using gentle words and helpful actions so someone else feels safe and cared for."),
        ("What does it mean to tackle a problem?",
         "To tackle a problem means to face it and try to handle it. In this story, it means doing that in a gentle, helpful way."),
        ("Why is rough tackling not the right choice here?",
         "Because this world is about care, not bumping or wrestling. A kind tackle fixes the trouble without making anyone scared."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
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
    StoryParams("nursery", "ribbon", "untie", "Mia", "girl", "Rose", "girl"),
    StoryParams("moon", "lantern", "upright", "Leo", "boy", "Pip", "boy"),
    StoryParams("meadow", "basket", "gather", "Ava", "girl", "June", "girl"),
]


def explain_rejection(action: KindAction, trouble: Trouble) -> str:
    if action.sense < 2:
        return f"(No story: {action.verb} is too rough for this gentle nursery-rhyme world.)"
    if not is_helpful(action, trouble):
        return f"(No story: {action.verb} does not really help with {trouble.label}.)"
    return "(No story: that combination is not a good kind-tackle match.)"


def outcome_of(params: StoryParams) -> str:
    action = ACTIONS[params.action]
    trouble = TROUBLES[params.trouble]
    return "kind" if is_helpful(action, trouble) else "recovered"


ASP_RULES = r"""
helpful(A,T) :- action(A), trouble(T), sense(A,S), S >= 2, power(A,P), need(T,N), P >= N.
valid(Tm, Tr, A) :- theme(Tm), trouble(Tr), action(A), helpful(A, Tr).
outcome(kind) :- helpful(chosen_action, chosen_trouble).
outcome(recovered) :- not helpful(chosen_action, chosen_trouble).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for tr, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tr))
        if trouble.can_spill:
            lines.append(asp.fact("need", tr, 2))
        if trouble.can_tangle:
            lines.append(asp.fact("need", tr, 2))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, act.sense))
        lines.append(asp.fact("power", aid, act.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_action", params.action), asp.fact("chosen_trouble", params.trouble)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    samples = [CURATED[0]]
    rng = random.Random(777)
    for _ in range(5):
        samples.append(resolve_params(argparse.Namespace(theme=None, trouble=None, action=None, child=None, child_gender=None, helper=None, helper_gender=None), rng))
    for p in samples:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print("MISMATCH in outcome for", p)
    try:
        _ = generate(CURATED[0])
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print("MISMATCH: generate() failed:", err)
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about kindness and a gentle tackle.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              if (args.theme is None or c[0] == args.theme)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, trouble, action = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(["Mia", "Nora", "Leo", "Finn", "Ava", "Theo"])
    helper = args.helper or rng.choice(["Rose", "Pip", "June", "Hugo", "Mabel"])
    return StoryParams(theme, trouble, action, child, child_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], TROUBLES[params.trouble], ACTIONS[params.action],
                 params.child, params.child_gender, params.helper, params.helper_gender)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

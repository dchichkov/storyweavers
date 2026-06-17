#!/usr/bin/env python3
"""
storyworlds/worlds/aquarium_calm.py
====================================

A standalone story world about wanting a tiny water creature to play back. The
child's parent predicts how tapping, shaking, or overfeeding would stress the
creature, then offers a compatible calm way to enjoy the moment.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt"}
        male = {"boy", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    motion: str
    sensitive_to: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Impulse:
    id: str
    verb: str
    gerund: str
    try_text: str
    stress: str
    stress_text: str
    lure: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CalmPlan:
    id: str
    label: str
    guards: set[str]
    offer: str
    ending: str
    tags: set[str] = field(default_factory=set)


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
    tag: str
    apply: Callable[[World], list[str]]


def _r_creature_stress(world: World) -> list[str]:
    creature = world.entities.get("creature")
    parent = world.entities.get("Parent")
    if not creature or not parent:
        return []
    out: list[str] = []
    for stress in ("noise", "shaking", "cloudy_water", "chasing"):
        if creature.meters[stress] < THRESHOLD:
            continue
        sig = ("stress", stress)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        creature.meters["scared"] += 1
        parent.memes["concern"] += 1
        out.append("__stress__")
    return out


def _r_hiding(world: World) -> list[str]:
    creature = world.entities.get("creature")
    if not creature or creature.meters["scared"] < THRESHOLD:
        return []
    sig = ("hide", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["hiding"] += 1
    return ["__hide__"]


CAUSAL_RULES = [
    Rule("creature_stress", "physical", _r_creature_stress),
    Rule("hiding", "behavior", _r_hiding),
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
        for sent in produced:
            world.say(sent)
    return produced


def creature_at_risk(impulse: Impulse, creature: Creature) -> bool:
    return impulse.stress in creature.sensitive_to


def plan_works(impulse: Impulse, creature: Creature, plan: CalmPlan) -> bool:
    return creature_at_risk(impulse, creature) and impulse.stress in plan.guards


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for creature_id in sorted(setting.affords):
            creature = CREATURES[creature_id]
            for impulse_id, impulse in IMPULSES.items():
                for plan_id, plan in PLANS.items():
                    if plan_works(impulse, creature, plan):
                        combos.append((place, impulse_id, creature_id, plan_id))
    return combos


def _do_impulse(world: World, hero: Entity, creature: Entity, impulse: Impulse, narrate: bool = True) -> None:
    hero.memes["eager"] += 1
    creature.meters[impulse.stress] += 1
    propagate(world, narrate=narrate)


def predict_stress(world: World, hero: Entity, impulse: Impulse) -> dict:
    sim = world.copy()
    _do_impulse(sim, sim.get(hero.id), sim.get("creature"), impulse, narrate=False)
    creature = sim.get("creature")
    parent = sim.get("Parent")
    return {
        "scared": creature.meters["scared"] >= THRESHOLD,
        "hiding": creature.meters["hiding"] >= THRESHOLD,
        "concern": parent.memes["concern"],
    }


def introduce(world: World, hero: Entity, parent: Entity, creature_cfg: Creature) -> None:
    trait = next((t for t in hero.traits if t), "curious")
    world.say(f"Once upon a time, there was a little {trait} {hero.type} named {hero.id}.")
    world.say(
        f"{hero.id} and {hero.pronoun('possessive')} {parent.label_word} visited {world.setting.place}, "
        f"where {world.setting.detail} and {creature_cfg.phrase} {creature_cfg.motion}."
    )


def want_play(world: World, hero: Entity, impulse: Impulse, creature_cfg: Creature) -> None:
    hero.memes["love"] += 1
    world.say(
        f"{hero.id} wanted {creature_cfg.label} to notice {hero.pronoun('object')}. "
        f"The idea in {hero.pronoun('possessive')} head was to {impulse.verb}, because {impulse.lure}."
    )


def warn(world: World, parent: Entity, hero: Entity, impulse: Impulse, creature_cfg: Creature) -> bool:
    pred = predict_stress(world, hero, impulse)
    if not pred["scared"]:
        return False
    world.facts["predicted_hiding"] = pred["hiding"]
    world.facts["predicted_concern"] = pred["concern"]
    world.say(
        f'{parent.label_word.capitalize()} spoke softly. "If you {impulse.verb}, '
        f"{creature_cfg.label} might {impulse.stress_text} and hide instead of playing. "
        f'Tiny water animals need calm."'
    )
    return True


def resist(world: World, parent: Entity, hero: Entity, impulse: Impulse) -> None:
    hero.memes["frustration"] += 1
    world.say(
        f"{hero.id} frowned and lifted {hero.pronoun('possessive')} hand to {impulse.try_text}, "
        f"but {hero.pronoun('possessive')} {parent.label_word} gently touched the air between hand and glass."
    )
    world.say(f'"Let us help without startling it," {parent.pronoun()} said.')


def offer(world: World, parent: Entity, hero: Entity, plan: CalmPlan) -> None:
    parent.memes["kindness"] += 1
    hero.memes["trust"] += 1
    world.say(
        f'{parent.label_word.capitalize()} smiled. "How about we {plan.offer}? '
        f'That way our quiet choice becomes the invitation."'
    )
    world.facts["plan_used"] = plan


def accept(world: World, hero: Entity, parent: Entity, creature_cfg: Creature, plan: CalmPlan) -> None:
    hero.memes["joy"] += 1
    creature = world.get("creature")
    creature.meters["calm"] += 1
    world.say(
        f"{hero.id} tried the calmer plan, and for a moment the water seemed to hold its breath. "
        f"Then {creature_cfg.label} came closer. {hero.id} beamed, squeezed {hero.pronoun('possessive')} "
        f"{parent.label_word}'s hand, and {plan.ending}."
    )
    world.facts["resolved"] = True


def tell(setting: Setting, impulse: Impulse, creature_cfg: Creature, plan: CalmPlan,
         name: str = "Leo", gender: str = "boy", parent_type: str = "mother",
         trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=[trait], role="hero"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="parent"))
    creature = world.add(Entity(id="creature", type="animal", label=creature_cfg.label, phrase=creature_cfg.phrase))
    world.facts.update(hero=hero, parent=parent, creature=creature, creature_cfg=creature_cfg,
                       impulse=impulse, plan=plan)

    introduce(world, hero, parent, creature_cfg)
    want_play(world, hero, impulse, creature_cfg)
    world.para()
    if not warn(world, parent, hero, impulse, creature_cfg):
        raise StoryError(explain_rejection(impulse, creature_cfg, plan))
    resist(world, parent, hero, impulse)
    world.para()
    offer(world, parent, hero, plan)
    accept(world, hero, parent, creature_cfg, plan)
    return world


SETTINGS = {
    "aquarium": Setting("aquarium", "the small aquarium room", "blue light shimmered on the walls", {"goldfish", "snail", "tadpole"}),
    "pet_shop": Setting("pet_shop", "the quiet pet shop", "bubbles climbed in neat silver strings", {"goldfish", "snail"}),
    "classroom": Setting("classroom", "the classroom science table", "a clean jar sat beside a magnifying glass", {"tadpole", "snail"}),
}

CREATURES = {
    "goldfish": Creature("goldfish", "the goldfish", "a small orange goldfish", "flicked through the water like a ribbon", {"noise", "shaking", "cloudy_water", "chasing"}, tags={"fish", "aquarium", "calm"}),
    "snail": Creature("snail", "the water snail", "a tiny water snail", "slid along the glass with slow brave horns", {"noise", "shaking", "cloudy_water"}, tags={"snail", "aquarium", "calm"}),
    "tadpole": Creature("tadpole", "the tadpole", "a small tadpole", "wiggled its comma tail under a leaf", {"noise", "shaking", "cloudy_water", "chasing"}, tags={"tadpole", "calm"}),
}

IMPULSES = {
    "tap": Impulse("tap", "tap the glass", "tapping the glass", "tap the glass", "noise", "feel frightened by the sudden booming sound", "a tap seemed like saying hello", tags={"noise"}),
    "shake": Impulse("shake", "shake the jar", "shaking the jar", "shake the jar", "shaking", "feel the whole world wobble", "waves looked exciting", tags={"water"}),
    "overfeed": Impulse("overfeed", "drop in a big mountain of food", "overfeeding", "sprinkle in extra food", "cloudy_water", "end up in cloudy water with too much food", "snacks make most friends happy", tags={"food"}),
    "net_chase": Impulse("net_chase", "chase it with the little net", "chasing with the net", "reach for the little net", "chasing", "think a giant shadow is chasing it", "catching looked like a game", tags={"net"}),
}

PLANS = {
    "quiet_watch": CalmPlan("quiet_watch", "quiet watching", {"noise", "shaking", "chasing"}, "put two quiet fingers on the table and watch for three slow breaths", "learned that quiet could be a kind of hello", tags={"calm"}),
    "one_pinch": CalmPlan("one_pinch", "one careful pinch of food", {"cloudy_water"}, "ask the keeper for one tiny pinch of the right food", "watched one speck drift down like a polite invitation", tags={"food", "fish"}),
    "draw_creature": CalmPlan("draw_creature", "drawing what they saw", {"noise", "chasing", "shaking"}, "draw what it does instead of trying to make it perform", "drew a wiggly picture that looked almost alive", tags={"drawing", "calm"}),
    "ask_keeper": CalmPlan("ask_keeper", "asking the keeper", {"noise", "shaking", "cloudy_water", "chasing"}, "ask the keeper what this animal likes before we do anything", "found out that good care begins with asking", tags={"keeper", "calm"}),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Rose"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Theo", "Sam"]
TRAITS = ["curious", "lively", "thoughtful", "eager", "gentle"]
PARENTS = ["mother", "father", "aunt", "uncle"]


@dataclass
class StoryParams:
    place: str
    impulse: str
    creature: str
    plan: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "fish": [("Do fish like tapping on glass?", "No. Tapping can sound very loud underwater, so fish may become scared and hide.")],
    "snail": [("How does a water snail move?", "A water snail moves slowly with a soft foot. It needs calm water and clean surfaces to explore.")],
    "tadpole": [("What is a tadpole?", "A tadpole is a young frog or toad. It lives in water and breathes there while it grows.")],
    "aquarium": [("Why should aquarium water stay clean?", "Clean water helps small animals breathe and stay healthy. Too much food or dirt can make the water cloudy.")],
    "calm": [("Why is calm behavior kind to small animals?", "Small animals can be frightened by loud sounds and sudden movement. Calm behavior helps them feel safe enough to come closer.")],
    "food": [("Why should fish not get too much food?", "Extra food can rot in the water and make it dirty. A tiny correct amount is safer.")],
    "net": [("Why can a net scare a small water animal?", "A net looks like a big moving shadow. The animal may think it is being chased or caught.")],
    "drawing": [("How can drawing help you enjoy an animal safely?", "Drawing lets you notice shapes and movements without touching or frightening the animal.")],
    "keeper": [("Why ask an animal keeper for help?", "A keeper knows what the animal needs. Asking first helps you choose a safe action.")],
}
KNOWLEDGE_ORDER = ["fish", "snail", "tadpole", "aquarium", "calm", "food", "net", "drawing", "keeper"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, impulse, creature, plan = f["hero"], f["impulse"], f["creature_cfg"], f["plan"]
    return [
        f'Write a gentle story for a 3-to-5-year-old about wanting {creature.label} to play, but learning to be calm.',
        f"Tell a story where {hero.id} wants to {impulse.verb}; a parent predicts the stress and offers {plan.label} instead.",
        f"Write a child-friendly story where a small water animal's needs guide the ending, with full cause and effect.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, parent = f["hero"], f["parent"]
    impulse, creature, plan = f["impulse"], f["creature_cfg"], f["plan"]
    pos, obj = hero.pronoun("possessive"), hero.pronoun("object")
    qa = [
        ("Who is the story about?", f"It is about {hero.id}, a little {hero.type}, and {pos} {parent.label_word}. They visit {world.setting.place} and watch {creature.label}."),
        (f"What did {hero.id} want to do?", f"{hero.id} wanted to {impulse.verb} because {impulse.lure}. The impulse came from eagerness, not from wanting to be unkind."),
        ("Why did the parent stop the action?", f"The parent predicted that {impulse.gerund} could make {creature.label} {impulse.stress_text}. If the animal became scared, it would hide instead of feeling safe."),
    ]
    if f.get("resolved"):
        qa.append(("How did they solve the problem?", f"They chose {plan.label}: they would {plan.offer}. That plan matched the actual stress risk and gave {hero.id} a safe way to connect."))
        qa.append(("What changed at the end?", f"At the end, {hero.id} used patience instead of force. {creature.label.capitalize()} came closer because the water stayed calm and the choice was gentle."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["creature_cfg"].tags) | set(f["impulse"].tags) | set(f["plan"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("aquarium", "tap", "goldfish", "quiet_watch", "Leo", "boy", "mother", "curious"),
    StoryParams("pet_shop", "overfeed", "goldfish", "one_pinch", "Mia", "girl", "father", "eager"),
    StoryParams("classroom", "shake", "tadpole", "ask_keeper", "Noah", "boy", "aunt", "thoughtful"),
    StoryParams("aquarium", "net_chase", "tadpole", "draw_creature", "Ava", "girl", "uncle", "lively"),
    StoryParams("classroom", "tap", "snail", "quiet_watch", "Finn", "boy", "mother", "gentle"),
]


def explain_rejection(impulse: Impulse, creature: Creature, plan: Optional[CalmPlan] = None) -> str:
    if not creature_at_risk(impulse, creature):
        return (f"(No story: {creature.label} is not modeled as vulnerable to '{impulse.stress}', "
                f"so the warning would not be grounded.)")
    if plan is not None and not plan_works(impulse, creature, plan):
        return (f"(No story: {plan.label} does not address the '{impulse.stress}' risk from "
                f"{impulse.gerund}, so the compromise is rejected.)")
    return f"(No story: no calm plan is registered for {impulse.gerund} with {creature.label}.)"


ASP_RULES = r"""
creature_at_risk(I,C) :- impulse_stress(I,S), sensitive(C,S).
plan_works(I,C,P) :- creature_at_risk(I,C), impulse_stress(I,S), guards(P,S).
valid(Place,I,C,P) :- affords(Place,C), plan_works(I,C,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for creature_id in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, creature_id))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        for stress in sorted(creature.sensitive_to):
            lines.append(asp.fact("sensitive", cid, stress))
    for iid, impulse in IMPULSES.items():
        lines.append(asp.fact("impulse", iid))
        lines.append(asp.fact("impulse_stress", iid, impulse.stress))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        for stress in sorted(plan.guards):
            lines.append(asp.fact("guards", pid, stress))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a child learns calm care around a tiny water animal.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--impulse", choices=IMPULSES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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
    if args.impulse and args.creature:
        impulse, creature = IMPULSES[args.impulse], CREATURES[args.creature]
        if not creature_at_risk(impulse, creature):
            raise StoryError(explain_rejection(impulse, creature))
    if args.impulse and args.creature and args.plan:
        impulse, creature, plan = IMPULSES[args.impulse], CREATURES[args.creature], PLANS[args.plan]
        if not plan_works(impulse, creature, plan):
            raise StoryError(explain_rejection(impulse, creature, plan))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.impulse is None or c[1] == args.impulse)
              and (args.creature is None or c[2] == args.creature)
              and (args.plan is None or c[3] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, impulse_id, creature_id, plan_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(place, impulse_id, creature_id, plan_id, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    if not plan_works(IMPULSES[params.impulse], CREATURES[params.creature], PLANS[params.plan]):
        raise StoryError(explain_rejection(IMPULSES[params.impulse], CREATURES[params.creature], PLANS[params.plan]))
    world = tell(SETTINGS[params.place], IMPULSES[params.impulse], CREATURES[params.creature], PLANS[params.plan],
                 params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
    if args.json:
        data = [s.to_dict() for s in samples]
        print(json.dumps(data[0] if len(data) == 1 else data, indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples, 1):
        header = f"--- story {idx} ---" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(exc)
        sys.exit(2)

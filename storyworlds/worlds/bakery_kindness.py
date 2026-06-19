#!/usr/bin/env python3
"""
storyworlds/worlds/bakery_kindness.py
====================================

A standalone story world from the seed:

    Words: bakery, kindness, sharing
    Features: Cautionary, Kindness, Moral Value
    Style: Animal Story

The world models a young friend tempted by a warm pastry in a bakery.
A baker predicts, by simulating the choice on a copy of the world, what
will be harmed if the pastry is taken. The story is valid only when the
kind alternative still protects the needy creature or visitor.
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
ROLES = {"breakfast", "comfort", "celebration", "ritual"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    depends_on: Optional[str] = None
    role: str = ""
    need: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"baker", "mother", "aunt", "uncle", "grandpa"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    phrase: str
    affords: set[str]


@dataclass
class BakeryItem:
    id: str
    label: str
    phrase: str
    role: str
    dependent: str
    need: str
    take_verb: str
    admire_verb: str
    scent: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KindPlan:
    id: str
    label: str
    solves: set[str]
    offer: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], list[str]]


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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# Physical + social cascades: one rule set, one engine.
def _r_take_hurts_dependent(world: World) -> list[str]:
    out: list[str] = []
    for thing in world.entities.values():
        if thing.meters["taken"] < THRESHOLD or not thing.depends_on:
            continue
        dependent = world.get(thing.depends_on)
        sig = ("hurt", dependent.id, thing.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        dependent.meters[f"missing_{thing.role}"] += 1
        dependent.memes["upset"] += 1
        out.append(
            f"{dependent.label.capitalize()} would lose {loss_phrase(thing)} "
            f"if {thing.label} was taken away."
        )
    return out


def _r_kindness_eases_dependent(world: World) -> list[str]:
    out: list[str] = []
    for dependent in world.entities.values():
        if dependent.memes["helped"] < THRESHOLD:
            continue
        sig = ("relief", dependent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        dependent.memes["upset"] = 0.0
        dependent.memes["gratitude"] += 1
        out.append(f"{dependent.label.capitalize()} became calm and grateful.")
    return out


CAUSAL_RULES = [
    Rule("take_hurts_dependent", _r_take_hurts_dependent),
    Rule("kindness_eases_dependent", _r_kindness_eases_dependent),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def thing_at_risk(item: BakeryItem) -> bool:
    return item.role in ROLES and item.role != "ritual"


def select_plan(item: BakeryItem) -> Optional[KindPlan]:
    for plan in PLANS:
        if item.role in plan.solves:
            return plan
    return None


def loss_phrase(item: BakeryItem) -> str:
    return {
        "breakfast": "the first sweet bite",
        "comfort": "the only warm snack",
        "celebration": "a sweet piece promised for a small celebration",
        "ritual": "a keepsake crumb",
    }.get(item.role, "something important")


def display_name(identifier: str) -> str:
    return identifier.replace("_", " ")


def reason_phrase(item: BakeryItem) -> str:
    return {
        "breakfast": "to keep them from being hungry",
        "comfort": "to help them feel safe at night",
        "celebration": "to include everyone in the party",
        "ritual": "to honor a tiny old habit",
    }.get(item.role, f"for {item.dependent}")


def explain_rejection(setting: Setting, item: BakeryItem) -> str:
    if item.id not in setting.affords:
        return (
            f"(No story: {setting.phrase} does not serve {item.label}, "
            "so this choice cannot be staged honestly.)"
        )
    if not thing_at_risk(item):
        return f"(No story: taking the {item.label} would not materially harm {item.dependent}.)"
    if select_plan(item) is None:
        return (
            f"(No story: there is no kind plan in this domain for the "
            f"{item.role} role, so kindness cannot honestly replace taking {item.label}.)"
        )
    return "(No story: constraints rejected this combination.)"


def take_treat(world: World, child: Entity, treat: Entity, narrate: bool = True) -> None:
    child.memes["desire"] += 1
    treat.meters["taken"] += 1
    propagate(world, narrate=narrate)


def predict_harm(world: World, child: Entity, treat: Entity) -> dict:
    sim = world.copy()
    take_treat(sim, sim.get(child.id), sim.get(treat.id), narrate=False)
    dependent = sim.get(treat.depends_on or "")
    return {
        "upset": dependent.memes["upset"] >= THRESHOLD,
        "missing": {k: v for k, v in dependent.meters.items() if v},
        "dependent": dependent,
    }


def introduce(world: World, child: Entity, baker: Entity) -> None:
    world.say(
        f"Once upon a time, there was a curious {child.type} named {child.id}. "
        f"{child.id} visited the bakery with {baker.label}."
    )


def admire_and_hope(world: World, child: Entity, item: BakeryItem) -> None:
    child.memes["joy"] += 1
    world.say(
        f"The display was shiny and warm, and {item.phrase} {item.admire_verb}. "
        f"It smelled like {item.scent}, and {child.id} wanted it right away."
    )


def warn(world: World, child: Entity, baker: Entity, item: BakeryItem, treat: Entity) -> bool:
    pred = predict_harm(world, child, treat)
    if not pred["upset"]:
        return False
    world.facts["predicted_upset"] = True
    world.facts["predicted_dependent"] = pred["dependent"].label
    world.facts["predicted_role"] = item.role
    world.say(
        f'"If we take {item.label}, {pred["dependent"].label} may miss {loss_phrase(item)}, '
        f'and that would be wrong, because {pred["dependent"].label} needs it {reason_phrase(item)}," '
        f'said {baker.label}.'
    )
    return True


def reach_for_it(world: World, child: Entity, item: BakeryItem) -> None:
    child.memes["selfish_pull"] += 1
    world.say(
        f"{child.id} reached out anyway for {item.label} but held still for one heartbeat."
    )


def pause_and_choose(world: World, child: Entity) -> None:
    child.memes["inner_conflict"] += 1
    world.say(
        f'{child.id} thought, "I can wait, and still be kind."'
    )


def compromise(world: World, child: Entity, item: BakeryItem, plan: KindPlan,
               item_ent: Entity, dependent: Entity) -> None:
    child.memes["kindness"] += 1
    child.memes["joy"] += 1
    dependent.memes["helped"] += 1
    propagate(world, narrate=False)
    world.say(f'{child.pronoun().capitalize()} said, "{plan.offer}."')
    world.say(
        plan.result.format(child=child.id, item=item_ent.label, dependent=dependent.label)
    )


def thanks(world: World, child: Entity, dependent: Entity) -> None:
    world.say(
        f"{dependent.label.capitalize()} nudged {child.id} and nodded as if saying thank you. "
        "Everyone smiled, and the shop felt warmer."
    )


def moral(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} learned that waiting for a fair share can make a bakery feel generous. "
        "The warm smell of bread stayed in the room, and so did the kindness."
    )


def tell(setting: Setting, item_cfg: BakeryItem, child_type: str,
         child_name: str, baker_name: str) -> World:
    if not thing_at_risk(item_cfg):
        raise StoryError(explain_rejection(setting, item_cfg))
    plan = select_plan(item_cfg)
    if plan is None:
        raise StoryError(explain_rejection(setting, item_cfg))

    world = World(setting)
    child = world.add(Entity(child_name, kind="character", type=child_type, label=child_name))
    baker = world.add(Entity("Baker", kind="character", type="baker", label=baker_name))
    dependent = world.add(
        Entity(
            item_cfg.dependent,
            kind="character",
            type="neighbor",
            label=f"the {display_name(item_cfg.dependent)}",
            need=item_cfg.need,
        )
    )
    treat = world.add(
        Entity(
            "Treat",
            kind="thing",
            type=item_cfg.id,
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            depends_on=dependent.id,
            role=item_cfg.role,
            need=item_cfg.need,
        )
    )

    introduce(world, child, baker)
    world.para()
    admire_and_hope(world, child, item_cfg)
    warned = warn(world, child, baker, item_cfg, treat)
    reach_for_it(world, child, item_cfg)
    world.para()
    pause_and_choose(world, child)
    compromise(world, child, item_cfg, plan, treat, dependent)
    if warned:
        world.facts["warned"] = True
    else:
        world.facts["warned"] = False
    thanks(world, child, dependent)
    moral(world, child)

    world.facts.update(
        child=child,
        baker=baker,
        dependent=dependent,
        treat=treat,
        item_cfg=item_cfg,
        plan=plan,
        setting=setting,
    )
    return world


SETTINGS = {
    "corner_bakery": Setting("a corner bakery with warm windows", {"croissant", "berry_tart", "bun"}),
    "river_bakery": Setting("a tiny bakery by the river", {"croissant", "bun", "birthday_pie"}),
    "festival_bakery": Setting("a lantern-lit festival bakery", {"birthday_pie", "berry_tart", "sugar_cake"}),
}

ITEMS = {
    "croissant": BakeryItem(
        "croissant",
        "a golden croissant",
        "a golden croissant",
        "breakfast",
        "grandma_cat",
        "her first bite for morning",
        "take one warm croissant",
        "glittered with honey-like shine",
        "butter and warm sugar",
        {"bakery", "kindness", "breakfast"},
    ),
    "berry_tart": BakeryItem(
        "berry_tart",
        "a berry tart",
        "a berry tart with jamy sides",
        "celebration",
        "lively_rabbit",
        "the first sweet at their small party",
        "take the berry tart",
        "sat like a little moon on a plate",
        "strawberries and cinnamon",
        {"bakery", "celebration", "sharing"},
    ),
    "bun": BakeryItem(
        "bun",
        "a soft milk bun",
        "a soft milk bun",
        "comfort",
        "sleepy_fox",
        "a calming bedtime treat",
        "take the soft bun",
        "looked warm enough to hug",
        "vanilla and flour",
        {"bakery", "comfort", "kindness"},
    ),
    "birthday_pie": BakeryItem(
        "birthday_pie",
        "a birthday pie",
        "a bright birthday pie",
        "celebration",
        "tiny_drummer",
        "their little festival ceremony",
        "take the birthday pie",
        "glowed like summer red berries",
        "cinnamon cream and laughter",
        {"bakery", "celebration"},
    ),
    "sugar_cake": BakeryItem(
        "sugar_cake",
        "a sugar-caked slice",
        "a sugar-caked slice",
        "ritual",
        "hollow_rabbit",
        "the ritual tray for the oldest customer",
        "take the sugar-cake slice",
        "looked impossible to resist",
        "toasted sugar",
        {"bakery", "ritual"},
    ),
}

PLANS = [
    KindPlan(
        "fresh_batch",
        "ask for a fresh batch",
        {"breakfast", "comfort"},
        "Let us ask for a fresh batch instead",
        "{child} helped with the dough, and by the end of their turn, {dependent} still had what it needed.",
        {"helping", "breakfast", "comfort"},
    ),
    KindPlan(
        "share_party_plate",
        "share the party plate",
        {"celebration"},
        "Let us split a party plate and give all the small guests a turn",
        "{child} arranged a small share plate, and {dependent} received a fair piece anyway.",
        {"sharing", "celebration"},
    ),
]

HEROES = {
    "girl": ["Mina", "Luna", "Ari", "Nora"],
    "boy": ["Niko", "Owen", "Theo", "Jules"],
}

BAKERS = ["Brielle", "Sera", "Mara", "Annie"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        for item_id in setting.affords:
            item = ITEMS[item_id]
            if thing_at_risk(item) and select_plan(item):
                combos.append((place, item_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    item: str
    hero: str
    name: str
    baker: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bakery": [
        (
            "What happens in a bakery?",
            "A bakery is a place where dough, sugar, and practice turn together into bread and treats.",
        ),
    ],
    "kindness": [
        (
            "Why is kindness important?",
            "Kindness helps everyone feel safe, and shared choices often keep communities stronger.",
        ),
    ],
    "breakfast": [
        (
            "Why is breakfast food important for some people and animals?",
            "Breakfast can set a steady start to the day and helps young bodies grow, move, and focus.",
        ),
    ],
    "comfort": [
        (
            "How does food help with comfort?",
            "Warm and sweet food can calm a body and make everyone feel more cared for.",
        ),
    ],
    "celebration": [
        (
            "Why does sharing at a celebration matter?",
            "At celebrations, sharing keeps the joy balanced so everyone can take part.",
        ),
    ],
}

KNOWLEDGE_ORDER = ["bakery", "kindness", "breakfast", "comfort", "celebration"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, item = f["child"], f["item_cfg"]
    return [
        'Write a gentle bakery kindness story using the words "bakery", "kindness", and "sharing".',
        f"Tell a short cautionary story where a young {child.type} named {child.id} is tempted to take {item.label}.",
        "Make the story about being tempted, warned, and choosing a better kinder option.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, baker, dependent, item, plan = (
        f["child"],
        f["baker"],
        f["dependent"],
        f["item_cfg"],
        f["plan"],
    )
    warned = "were warned" if world.facts["warned"] else "were not warned"
    return [
        (f"Who is the story about?",
         f"The story is about {child.id}, the baker {baker.label}, and {dependent.label}."),
        (
            f"Why did {child.id} pause before taking {item.label}?",
            f"{baker.label} warned {child.pronoun('object')} that taking it could leave {dependent.label} without {loss_phrase(item)}.",
        ),
        (
            f"What did {child.id} choose to do instead?",
            f"Instead of taking it alone, {child.pronoun()} chose a sharing plan: {plan.offer.lower()}. That let the treat stay connected to the creature who needed it.",
        ),
        (
            "What lesson did the hero learn?",
            f"{child.id} learned that waiting and helping in a bakery can keep everyone better fed and happier. "
            "The ending shows kindness as something the whole shop can feel.",
        ),
        (
            f"Was this a warned moment?",
            f"Yes. {baker.label} warned {child.id} about what could have happened." if world.facts["warned"] else f"No. {child.id} and {baker.label} were not warned in this version."
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["item_cfg"].tags) | set(f["plan"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    if tags & {"sharing", "helping"}:
        out.append((
            "Why do sharing and helping matter?",
            "They keep scarcity from turning into hurt feelings and let everyone get a fair part."
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.need:
            bits.append(f"need={ent.need}")
        if ent.depends_on:
            bits.append(f"depends_on={ent.depends_on}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:14} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: {world.facts.get('warned')} warned")
    return "\n".join(lines)


CURATED = [
    StoryParams("corner_bakery", "croissant", "girl", "Mina", "Brielle"),
    StoryParams("river_bakery", "berry_tart", "boy", "Theo", "Sera"),
    StoryParams("festival_bakery", "birthday_pie", "girl", "Ari", "Mara"),
    StoryParams("corner_bakery", "bun", "boy", "Niko", "Annie"),
]


ASP_RULES = r"""
item_role(I, R) :- item(I), role(R), item_role(I, R).
at_risk(I) :- item_role(I, R), role(R), R != ritual.
has_plan(I) :- item_role(I, R), solves(P, R).
valid(P, I) :- setting(P), affords(P, I), at_risk(I), has_plan(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for role in sorted(ROLES):
        lines.append(asp.fact("role", role))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for item in sorted(setting.affords):
            lines.append(asp.fact("affords", place, item))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_role", item_id, item.role))
    for plan in PLANS:
        lines.append(asp.fact("plan", plan.id))
        for role in sorted(plan.solves):
            lines.append(asp.fact("solves", plan.id, role))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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
    ap = argparse.ArgumentParser(
        description="Story world sketch: bakery, kindness, sharing. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--name")
    ap.add_argument("--baker", choices=BAKERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and (args.place, args.item) not in valid_combos():
        raise StoryError(explain_rejection(SETTINGS[args.place], ITEMS[args.item]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.item is None or c[1] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item = rng.choice(combos)
    hero = args.hero or rng.choice(sorted(HEROES))
    names = HEROES[hero]
    name = args.name or rng.choice(names)
    baker = args.baker or rng.choice(BAKERS)
    return StoryParams(place, item, hero, name, baker)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ITEMS[params.item], params.hero, params.name, params.baker)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item) combos:\n")
        for place, item in combos:
            print(f"  {place:16} {item}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

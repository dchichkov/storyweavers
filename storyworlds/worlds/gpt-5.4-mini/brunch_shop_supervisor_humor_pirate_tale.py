#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/brunch_shop_supervisor_humor_pirate_tale.py
============================================================================

A tiny standalone storyworld for a humorous pirate-tale brunch shop.

Premise:
- A small shop prepares a brunch special.
- A piratey child or crew member gets a little too clever with the menu.
- A supervisor notices a concrete problem in the world state.
- The supervisor fixes it with a sensible, child-facing solution.
- The ending image proves what changed: the shop is calm, the brunch is safe,
  and the joke lands without breaking the room.

The domain is intentionally small and constraint-checked. Stories only generate
when there is an actual problem to supervise, and the fix must match that
problem. This keeps the humor grounded in simulated state instead of a frozen
paragraph with swapped nouns.
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
SENSE_MIN = 2


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "supervisor"}
        male = {"boy", "father", "dad", "man", "captain"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    scene: str
    crowded: bool = False

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
class MenuItem:
    id: str
    name: str
    mess: str
    hazard: str
    fix: str
    tags: set[str] = field(default_factory=set)

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
class SupervisorPlan:
    id: str
    sense: int
    power: int
    action: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_messy(world: World) -> list[str]:
    out: list[str] = []
    if world.get("deck").meters["mess"] >= THRESHOLD and ("mess", "deck") not in world.fired:
        world.fired.add(("mess", "deck"))
        world.get("deck").meters["sticky"] += 1
        world.get("supervisor").memes["alert"] += 1
        out.append("__mess__")
    return out


CAUSAL_RULES = [Rule("messy", "physical", _r_messy)]


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


def valid_combo(setting: Setting, item: MenuItem, plan: SupervisorPlan) -> bool:
    return item.mess == "syrup" and plan.sense >= SENSE_MIN


def sensible_plans() -> list[SupervisorPlan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def best_plan() -> SupervisorPlan:
    return max(PLANS.values(), key=lambda p: p.sense)


def spill_risk(item: MenuItem, setting: Setting) -> bool:
    return item.mess == "syrup" and setting.crowded


def fix_works(plan: SupervisorPlan, item: MenuItem) -> bool:
    return plan.power >= 1 and plan.action == item.fix


def _do_caper(world: World, item: Entity, narrate: bool = True) -> None:
    item.meters["mess"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, mate: Entity, supervisor: Entity, setting: Setting, item: MenuItem) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a sunny morning at the {setting.place}, {hero.id} and {mate.id} "
        f"turned brunch into a pirate tale. {setting.scene}"
    )
    world.say(
        f'"Captain {hero.id}!" {mate.id} cheered. "The {item.name} treasure is ready for the feast!"'
    )
    world.say(
        f"But the {supervisor.label_word} watched the deck with a squinty eye. "
        f'The crew had made a funny little mess near the table.'
    )


def temptation(world: World, hero: Entity, item: MenuItem) -> None:
    hero.memes["mischief"] += 1
    world.say(
        f'{hero.id} grinned. "I know! Let us pour the {item.name} like ocean gold."'
    )
    world.say("For one blink, that sounded like a grand pirate joke.")


def warn(world: World, supervisor: Entity, hero: Entity, item: MenuItem) -> None:
    world.get("deck").meters["mess"] += 1
    world.say(
        f"{supervisor.label_word.capitalize()} raised a calm hand. "
        f'"Hold, matey. {item.name.capitalize()} can get sticky fast, and this shop is busy."'
    )


def spill(world: World, item: Entity, menu: MenuItem) -> None:
    _do_caper(world, item)
    world.say(
        f"The joke went splat. {menu.name.capitalize()} dribbled over the table, "
        f"and the deck got slippery and sweet."
    )


def alarm(world: World, mate: Entity, supervisor: Entity, menu: MenuItem) -> None:
    world.say(f'"{supervisor.label_word.upper()}! The {menu.name} is sliding!" {mate.id} yelped.')


def clean_fix(world: World, supervisor: Entity, plan: SupervisorPlan, menu: MenuItem) -> None:
    deck = world.get("deck")
    deck.meters["mess"] = 0.0
    deck.meters["sticky"] = 0.0
    supervisor.memes["alert"] += 1
    world.say(
        f"{supervisor.label_word.capitalize()} came at once and {plan.action}."
    )
    world.say(
        f"The sticky puddle vanished, the plates stayed safe, and the brunch shop smelled like toast again."
    )


def lesson(world: World, supervisor: Entity, hero: Entity, mate: Entity, menu: MenuItem) -> None:
    for kid in (hero, mate):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"Then {supervisor.label_word.capitalize()} gave them a wink. "
        f'"Funny is good," {supervisor.pronoun()} said, "but {menu.hazard} is not for pirate games."'
    )
    world.say(f'"Aye, {supervisor.label_word}!" the little crew laughed, a bit sheepish and a lot wiser.')


def ending(world: World, setting: Setting, hero: Entity, mate: Entity, menu: MenuItem) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"By noon, the {setting.place} was neat again. {hero.id} and {mate.id} "
        f"munched {menu.name} with clean hands, and the supervisor kept watch like a cheerful captain."
    )
    world.say("The only thing sailing was the laughter.")


def tell(setting: Setting, item: MenuItem, plan: SupervisorPlan,
         hero_name: str = "Milo", mate_name: str = "Tia") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", role="hero"))
    mate = world.add(Entity(id=mate_name, kind="character", type="girl", role="mate"))
    supervisor = world.add(Entity(id="Supervisor", kind="character", type="supervisor", label="the supervisor", role="supervisor"))
    deck = world.add(Entity(id="deck", label="the shop counter"))

    setup(world, hero, mate, supervisor, setting, item)
    world.para()
    temptation(world, hero, item)
    warn(world, supervisor, hero, item)

    if not spill_risk(item, setting):
        raise StoryError("(No story: this brunch item does not make a real supervision problem.)")

    world.para()
    spill(world, deck, item)
    alarm(world, mate, supervisor, item)
    if not fix_works(plan, item):
        raise StoryError("(No story: that supervisor plan does not actually solve the mess.)")
    world.para()
    clean_fix(world, supervisor, plan, item)
    lesson(world, supervisor, hero, mate, item)
    world.para()
    ending(world, setting, hero, mate, item)

    world.facts.update(
        hero=hero,
        mate=mate,
        supervisor=supervisor,
        setting=setting,
        item=item,
        plan=plan,
        spoiled=deck.meters["mess"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "dock_shop": Setting(
        "dock_shop",
        "dockside brunch shop",
        "The tables sat beside the windows, and the gulls peeked in like nosy customers.",
        crowded=True,
    ),
    "harbor_cafe": Setting(
        "harbor_cafe",
        "harbor cafe",
        "The little chairs were packed close, and everyone could smell pancakes and sea salt.",
        crowded=True,
    ),
    "island_counter": Setting(
        "island_counter",
        "island market",
        "The counter was small, the line was long, and the jam jar gleamed like treasure.",
        crowded=True,
    ),
}

ITEMS = {
    "jam": MenuItem("jam", "jam", "syrup", "sticky", "wipe the counter clean", {"sweet", "sticky"}),
    "honey": MenuItem("honey", "honey", "syrup", "sticky", "wipe the counter clean", {"sweet", "sticky"}),
    "pancake_syrup": MenuItem("pancake_syrup", "pancake syrup", "syrup", "sticky", "wipe the counter clean", {"sweet", "sticky"}),
}

PLANS = {
    "wipe": SupervisorPlan("wipe", 3, 1, "wiped the counter with a warm cloth", "tried to swipe it away, but the mess kept spreading", "wiped the counter clean", {"clean"}),
    "chalk": SupervisorPlan("chalk", 1, 0, "drew a funny arrow on the floor", "made a joke, but the syrup still sat there", "wiped the counter clean", {"clean"}),
    "tray": SupervisorPlan("tray", 2, 1, "slid a tray under the dripping jar and set it upright", "moved too slowly and the sticky puddle stayed put", "wiped the counter clean", {"clean"}),
}

GIRL_NAMES = ["Tia", "Mara", "Nina", "Lena", "Pippa"]
BOY_NAMES = ["Milo", "Finn", "Oren", "Pax", "Jules"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for pid, plan in PLANS.items():
                if valid_combo(setting, item, plan):
                    combos.append((sid, iid, pid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    plan: str
    hero: str
    mate: str
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


KNOWLEDGE = {
    "brunch": [("What is brunch?", "Brunch is a meal that is part breakfast and part lunch. It is often eaten late in the morning.")],
    "shop": [("What is a shop?", "A shop is a place where people buy things or eat things, depending on the kind of shop.")],
    "supervisor": [("What does a supervisor do?", "A supervisor watches what is happening and helps keep things safe, neat, and fair.")],
    "sticky": [("Why is syrup sticky?", "Syrup is thick and sweet, so it spreads slowly and can make hands and tables sticky.")],
    "clean": [("Why do we clean a table?", "We clean a table so people can eat on it safely and it feels nice again.")],
    "pirate": [("What is a pirate?", "A pirate is a pretend seafarer from old stories, often used in fun adventure games.")],
}

KNOWLEDGE_ORDER = ["brunch", "shop", "supervisor", "sticky", "clean", "pirate"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a humorous pirate tale set in a brunch shop where a supervisor must deal with {f['item'].name}.",
        f"Tell a child-friendly story that includes the words brunch, shop, and supervisor, and has a silly pirate joke.",
        f"Write a short pirate-style brunch story where {f['hero'].id} makes a sticky mistake and the supervisor fixes it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, sup, item, plan = f["hero"], f["mate"], f["supervisor"], f["item"], f["plan"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, {mate.id}, and the supervisor at the brunch shop. They act like a tiny pirate crew while the day gets funny and busy.",
        ),
        QAItem(
            question=f"What problem did {hero.id} make with the {item.name}?",
            answer=f"{hero.id} tried to pour the {item.name} like a pirate joke, and the {item.name} became sticky on the counter. That made the shop messy and a little slippery.",
        ),
        QAItem(
            question="How did the supervisor help?",
            answer=f"The supervisor {plan.qa_text}. That fixed the mess and kept the brunch shop safe for everyone.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with clean tables, happy kids, and a funny pirate mood. The shop stayed open and the laughter kept sailing along.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["item"].tags) | {"brunch", "shop", "supervisor"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
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
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(item: MenuItem) -> str:
    return f"(No story: {item.name} does not create a strong enough sticky-brunch problem.)"


def explain_plan(plan_id: str) -> str:
    p = PLANS[plan_id]
    return f"(Refusing plan '{plan_id}': it is not common-sense enough for this shop.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("mess", iid, item.mess))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, plan.sense))
        lines.append(asp.fact("power", pid, plan.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, P) :- setting(S), item(I), plan(P), mess(I, syrup), sense(P, N), sense_min(M), N >= M.
outcome(fixed) :- valid(_, _, _).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, item=None, plan=None, hero=None, mate=None, seed=None), random.Random(777)))  # type: ignore[arg-type]
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous pirate-brunch shop storyworld with a supervisor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name")
    ap.add_argument("--mate")
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
    if args.item and ITEMS[args.item].mess != "syrup":
        raise StoryError(explain_rejection(ITEMS[args.item]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, plan = rng.choice(sorted(combos))
    hero = args.name or rng.choice(BOY_NAMES)
    mate = args.mate or rng.choice(GIRL_NAMES)
    return StoryParams(setting, item, plan, hero, mate)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], PLANS[params.plan], params.hero, params.mate)
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
        for s, i, p in combos:
            print(f"  {s:14} {i:12} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("dock_shop", "jam", "wipe", "Milo", "Tia"),
            StoryParams("harbor_cafe", "honey", "tray", "Pax", "Mara"),
            StoryParams("island_counter", "pancake_syrup", "chalk", "Finn", "Nina"),
        ]
        samples = [generate(p) for p in curated]
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

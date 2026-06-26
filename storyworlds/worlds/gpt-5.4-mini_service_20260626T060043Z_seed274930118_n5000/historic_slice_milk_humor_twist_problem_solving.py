#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    historic: bool = False
    fragile: bool = False


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    mess: str
    zone: set[str]
    twist: str
    joke: str
    fix_hint: str


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    covers: set[str]
    neutralizes: set[str]
    use: str
    end: str
    plural: bool = False


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
        w = World(self.setting)
        w.entities = {k: asdict(v) and Entity(**asdict(v)) for k, v in self.entities.items()}
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


THRESHOLD = 1.0


def _rule_spill(world: World) -> list[str]:
    out = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        for p in PROBLEMS.values():
            if actor.meters.get(p.id, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.region not in p.zone:
                    continue
                if ("spill", actor.id, item.id, p.id) in world.fired:
                    continue
                world.fired.add(("spill", actor.id, item.id, p.id))
                item.meters[p.id] = item.meters.get(p.id, 0.0) + 1
                item.meters["messy"] = item.meters.get("messy", 0.0) + 1
                out.append(f"{item.label} got caught in the {p.mess}.")
    return out


def _rule_fix(world: World) -> list[str]:
    out = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        for fix in FIXES.values():
            if actor.memes.get("needs_fix", 0.0) < THRESHOLD:
                continue
            if ("fix", actor.id, fix.id) in world.fired:
                continue
            world.fired.add(("fix", actor.id, fix.id))
            actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1
            out.append(fix.end)
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for fn in (_rule_spill, _rule_fix):
            s = fn(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for line in produced:
            world.say(line)


@dataclass
class StoryParams:
    setting: str
    problem: str
    item: str
    hero_name: str
    hero_type: str
    helper_name: str
    seed: Optional[int] = None


SETTINGS = {
    "museum_cafe": Setting(
        place="the old museum café",
        detail="The room had tall windows, oak tables, and a sign that said HISTORIC SLICE.",
        affords={"milk"},
    ),
    "village_kitchen": Setting(
        place="the village kitchen",
        detail="The kitchen was sunny, with a shelf for plates and a shelf for stories.",
        affords={"milk"},
    ),
}

PROBLEMS = {
    "milk": Problem(
        id="milk",
        verb="pour the milk",
        gerund="pouring milk",
        mess="milk spill",
        zone={"torso", "hands"},
        twist="the cup wobbled like a giggling top",
        joke="the milk made a tiny white mustache on the table",
        fix_hint="use a tray and a smaller cup",
    )
}

ITEMS = {
    "slice": Item(
        id="slice",
        label="historic slice",
        phrase="a historic slice with a crumbly edge",
        region="hands",
        historic=True,
        fragile=True,
    )
}

FIXES = {
    "tray": Fix(
        id="tray",
        label="a blue tray",
        phrase="a blue tray with a steady lip",
        covers={"hands", "torso"},
        neutralizes={"milk spill"},
        use="carry the milk on a tray",
        end="They set the cup on a blue tray, and the wobble could not stray.",
    ),
    "spoon": Fix(
        id="spoon",
        label="a tiny spoon",
        phrase="a tiny spoon for careful sips",
        covers={"hands"},
        neutralizes={"milk spill"},
        use="sip slowly with a spoon",
        end="They used a tiny spoon, and the milk stayed neat and gay.",
    ),
}

NAMES = ["Mina", "Toby", "Iris", "Noah", "Pia", "Eli"]
HELPERS = ["Nana", "Papa", "Aunt June", "Uncle Ray"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Historic slice, milk, humor, twist, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or "milk"
    item = args.item or "slice"
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    if problem != "milk" or item != "slice" or setting not in SETTINGS:
        raise StoryError("This little storyworld only supports the historic slice and milk problem.")
    return StoryParams(setting=setting, problem=problem, item=item, hero_name=name, hero_type=hero_type, helper_name=helper)


def _introduce(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} found a historic slice on a plate so bright and neat. "
        f"{hero.pronoun().capitalize()} said it looked like a treat."
    )
    world.say(
        f"{helper.id} smiled and said, 'That slice is old, but still so sweet.'"
    )
    if item.historic:
        hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1


def _problem_turn(world: World, hero: Entity, problem: Problem, item: Entity) -> None:
    hero.meters[problem.id] = hero.meters.get(problem.id, 0.0) + 1
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(
        f"{hero.id} wanted milk with the slice, a merry little treat. "
        f"But {problem.twist}, and that made the plan less neat."
    )
    world.say(
        f"{helper.id} laughed, 'Oh crumbs and hums, that cup may tip and beat!'"
    )
    hero.memes["needs_fix"] = hero.memes.get("needs_fix", 0.0) + 1


def _resolve(world: World, hero: Entity, helper: Entity, item: Entity, problem: Problem) -> None:
    fix = FIXES["tray"]
    world.say(
        f"{helper.id} said, 'Let's use {fix.label} and {fix.use}, and keep it in our seat.'"
    )
    world.say(
        f"{hero.id} nodded. Together they carried the milk with tiny careful feet."
    )
    hero.meters[problem.id] = 0.0
    item.meters["safe"] = item.meters.get("safe", 0.0) + 1
    world.say(
        f"The milk did not spill, the joke turned sweet, and the historic slice stayed neat."
    )
    world.say(
        f"{hero.id} took one small sip and grinned, 'Now that's a winning feat!'"
    )


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="grandma"))
    item = world.add(Entity(**asdict(ITEMS[params.item]), owner=hero.id, caretaker=helper.id))
    _introduce(world, hero, helper, item)
    world.para()
    _problem_turn(world, hero, PROBLEMS[params.problem], item)
    world.para()
    _resolve(world, hero, helper, item, PROBLEMS[params.problem])
    world.facts.update(hero=hero, helper=helper, item=item, problem=PROBLEMS[params.problem], setting=SETTINGS[params.setting])
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a rhyming story with a historic slice, milk, a funny twist, and a smart fix.",
        f"Tell a child-friendly tale set at {world.setting.place} where someone wants milk with a historic slice.",
        "Make the story playful, with a little humor and clear problem solving at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, item, problem = f["hero"], f["helper"], f["item"], f["problem"]
    return [
        QAItem(
            question=f"What did {hero.id} want with the historic slice?",
            answer=f"{hero.id} wanted milk with the historic slice because it looked like a sweet treat.",
        ),
        QAItem(
            question=f"Why did {helper.id} laugh when the milk was poured?",
            answer=f"{helper.id} laughed because the cup wobbled and the milk made the moment funny, not scary.",
        ),
        QAItem(
            question=f"How did they solve the milk problem?",
            answer=f"They solved it by using a tray and moving carefully, so the milk stayed tidy and the slice stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does milk come from?",
            answer="Milk comes from cows and other mammals. People drink it or use it in food and baking.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means something is old and important because it belongs to the past.",
        ),
        QAItem(
            question="Why do people use a tray?",
            answer="People use a tray to carry things more safely and help keep cups from tipping over.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for section, items in [("Prompts", sample.prompts), ("Story QA", sample.story_qa), ("World QA", sample.world_qa)]:
            print(f"== {section} ==")
            if section == "Prompts":
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for q in items:
                    print(f"Q: {q.question}")
                    print(f"A: {q.answer}")
            print()


ASP_RULES = r"""
setting(museum_cafe).
setting(village_kitchen).
problem(milk).
item(slice).

historic_item(slice).
mess(milk_spill).
fix(tray).
fix(spoon).

needs_fix(A) :- wants(A, milk).
safe_story(S) :- setting(S), historic_item(slice), problem(milk).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "museum_cafe"),
        asp.fact("setting", "village_kitchen"),
        asp.fact("problem", "milk"),
        asp.fact("item", "slice"),
        asp.fact("historic_item", "slice"),
        asp.fact("mess", "milk_spill"),
        asp.fact("fix", "tray"),
        asp.fact("fix", "spoon"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show safe_story/1."))
    atoms = set(asp.atoms(model, "safe_story"))
    expected = {("museum_cafe",), ("village_kitchen",)}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(setting="museum_cafe", problem="milk", item="slice", hero_name="Mina", hero_type="girl", helper_name="Nana")
        samples = [generate(params)]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small fable-style storyworld about Curiosity and an awesome mineral.

Seed premise:
A young, curious creature finds an awesome mineral and wants to get closer.
A wiser elder warns that looking closely can still be safe if the child slows
down, uses the right tool, and listens well. The story turns from impulsive
wonder to careful wonder, ending with a real, changed object in hand and a
changed feeling in the heart.

This script is standalone and follows the storyworld contract:
- builds one simulated world
- supports prose, QA, JSON, trace, ASP, verify
- keeps story output driven by world state, not a frozen template
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the stone garden"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mineral:
    id: str
    label: str
    phrase: str
    color: str
    shine: str
    fragility: str
    value: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    protects: set[str]
    helps_with: set[str]
    prep: str
    tail: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def mget(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def emget(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def madd(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def eadd(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def eclear(ent: Entity, key: str) -> None:
    ent.memes[key] = 0.0


def setting_detail(setting: Setting, mineral: Mineral) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, the lamps were soft and the floor was cool."
    return f"{setting.place.capitalize()} was quiet, and the {mineral.color} light on the stone looked almost alive."


def mineral_sentence(mineral: Mineral) -> str:
    return f"The {mineral.label} was {mineral.shine}, {mineral.color}, and strangely {mineral.value}."


def risk_applies(mineral: Mineral, place: Setting) -> bool:
    return mineral.id in place.affords


def select_tool(mineral: Mineral) -> Optional[Tool]:
    for tool in TOOLS:
        if mineral.fragility in tool.helps_with:
            return tool
    return None


def predict_harm(world: World, hero: Entity, mineral: Mineral, tool: Optional[Tool]) -> dict:
    sim = world.copy()
    _approach(sim, sim.get(hero.id), mineral, narrate=False)
    if tool is not None:
        _use_tool(sim, sim.get(hero.id), mineral, tool, narrate=False)
    gem = sim.get(mineral.id)
    return {
        "scratched": mget(gem, "scratched") >= THRESHOLD,
        "scattered": mget(gem, "scattered") >= THRESHOLD,
    }


def _approach(world: World, hero: Entity, mineral: Mineral, narrate: bool = True) -> None:
    if ("approach", hero.id, mineral.id) in world.fired:
        return
    world.fired.add(("approach", hero.id, mineral.id))
    eadd(hero, "curiosity", 1)
    eadd(hero, "wonder", 1)
    madd(world.get(mineral.id), "noticed", 1)
    if narrate:
        world.say(f"{hero.id} leaned closer because {hero.pronoun('possessive')} curiosity had found something wonderful.")


def _warn(world: World, elder: Entity, hero: Entity, mineral: Mineral) -> None:
    if ("warn", elder.id, hero.id, mineral.id) in world.fired:
        return
    world.fired.add(("warn", elder.id, hero.id, mineral.id))
    eadd(elder, "care", 1)
    world.say(
        f'"Slow steps," {elder.pronoun().capitalize()} said. '
        f'"An {mineral.label} can be awesome to find, but it can also crack if we rush."'
    )


def _use_tool(world: World, hero: Entity, mineral: Mineral, tool: Tool, narrate: bool = True) -> None:
    if ("tool", hero.id, mineral.id, tool.id) in world.fired:
        return
    world.fired.add(("tool", hero.id, mineral.id, tool.id))
    gem = world.get(mineral.id)
    hero.memes["curiosity"] = max(0.0, emget(hero, "curiosity") - 0.5)
    eadd(hero, "care", 1)
    if mineral.fragility in tool.helps_with:
        madd(gem, "scratched", 0.0)
        madd(gem, "safe", 1)
        if narrate:
            world.say(f"{hero.id} used {tool.label} {tool.tail}")
    else:
        madd(gem, "scratched", 1)
        if narrate:
            world.say(f"{hero.id} tried {tool.label}, but it was the wrong choice.")


def _resolve(world: World, hero: Entity, elder: Entity, mineral: Mineral, tool: Tool) -> None:
    if ("resolve", hero.id, mineral.id) in world.fired:
        return
    world.fired.add(("resolve", hero.id, mineral.id))
    eclear(hero, "worry")
    eadd(hero, "joy", 1)
    eadd(hero, "pride", 1)
    world.say(
        f'{hero.id} smiled as {hero.pronoun("possessive")} {tool.label} helped keep the stone safe. '
        f'Together they studied the {mineral.label}, and the bright little wonder did not get hurt.'
    )
    world.say(
        f"At the end, {hero.id} carried home not a broken prize, but a careful lesson: "
        f"curiosity is best when it walks with patience."
    )


def tell(setting: Setting, mineral: Mineral, hero_name: str = "Mira", hero_type: str = "mouse",
         elder_name: str = "Tobin", elder_type: str = "tortoise") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "curious"]))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, traits=["wise", "slow"]))
    gem = world.add(Entity(id=mineral.id, type="mineral", label=mineral.label, phrase=mineral.phrase))

    eadd(hero, "curiosity", 1)
    eadd(hero, "wonder", 1)
    eadd(elder, "care", 1)
    madd(gem, "shiny", 1)

    world.say(
        f"{hero.id} was a little curious {hero.type} who loved finding tiny things that looked important."
    )
    world.say(
        f"One morning in {setting.place}, {hero.id} spotted {mineral_sentence(mineral)}"
    )
    world.say(setting_detail(setting, mineral))

    world.para()
    _approach(world, hero, mineral)
    _warn(world, elder, hero, mineral)
    world.say(f"{hero.id} wanted to touch the stone right away, because {hero.pronoun('possessive')} curiosity was strong.")
    world.say(f"But {elder.id} held up a gentle paw and pointed to the dust around it.")

    tool = select_tool(mineral)
    world.para()
    if tool is None:
        raise StoryError(f"No safe tool exists for {mineral.label}.")
    predict = predict_harm(world, hero, mineral, tool)
    if predict["scratched"] or predict["scattered"]:
        raise StoryError("The chosen tool does not actually keep the mineral safe.")
    world.say(f'"How about we {tool.prep} and look together?" {elder.id} asked.')
    _use_tool(world, hero, mineral, tool)
    world.say(f"{hero.id} listened, slowed down, and chose the careful way instead of the quick way.")
    _resolve(world, hero, elder, mineral, tool)

    world.facts.update(hero=hero, elder=elder, mineral=mineral, tool=tool, setting=setting)
    return world


SETTINGS = {
    "stone_garden": Setting(place="the stone garden", affords={"quartz", "jade", "amber"}),
    "riverbank": Setting(place="the riverbank", affords={"quartz", "mica"}),
    "cave_hall": Setting(place="the cave hall", affords={"quartz", "jade", "amber", "mica"}),
}

MINERALS = {
    "quartz": Mineral(
        id="quartz",
        label="quartz",
        phrase="an awesome crystal hidden in the soil",
        color="clear",
        shine="glassy",
        fragility="crumbly",
        value="pretty",
        tags={"awesome", "mineral", "curiosity"},
    ),
    "jade": Mineral(
        id="jade",
        label="jade",
        phrase="an awesome green mineral tucked beside a root",
        color="green",
        shine="smooth",
        fragility="smooth",
        value="cool",
        tags={"awesome", "mineral", "curiosity"},
    ),
    "amber": Mineral(
        id="amber",
        label="amber",
        phrase="an awesome golden mineral resting in a crack",
        color="golden",
        shine="glowing",
        fragility="sticky",
        value="bright",
        tags={"awesome", "mineral", "curiosity"},
    ),
    "mica": Mineral(
        id="mica",
        label="mica",
        phrase="an awesome sparkly mineral that shone like tiny mirrors",
        color="silver",
        shine="sparkly",
        fragility="flaky",
        value="gleaming",
        tags={"awesome", "mineral", "curiosity"},
    ),
}

TOOLS = [
    Tool(
        id="brush",
        label="a soft brush",
        phrase="a soft brush",
        protects={"crumbly", "flaky"},
        helps_with={"crumbly", "flaky"},
        prep="brush away the dust first",
        tail="carefully brushed the dust away",
    ),
    Tool(
        id="cloth",
        label="a clean cloth",
        phrase="a clean cloth",
        protects={"sticky"},
        helps_with={"sticky"},
        prep="wrap it in a clean cloth first",
        tail="wrapped the stone in a clean cloth",
    ),
    Tool(
        id="tray",
        label="a shallow tray",
        phrase="a shallow tray",
        protects={"crumbly", "sticky", "flaky", "smooth"},
        helps_with={"crumbly", "sticky", "flaky", "smooth"},
        prep="set it on a shallow tray first",
        tail="set the stone on a shallow tray",
    ),
]

GIRL_NAMES = ["Mira", "Lina", "Pia", "Nora", "Tia"]
BOY_NAMES = ["Oren", "Bram", "Timo", "Noel", "Eli"]
ELDER_NAMES = ["Tobin", "Sage", "Moss", "Dara"]
TRAITS = ["curious", "gentle", "bright-eyed", "careful"]


@dataclass
class StoryParams:
    place: str
    mineral: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, mineral in MINERALS.items():
            if mid in setting.affords and select_tool(mineral) is not None:
                combos.append((place, mid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style storyworld about Curiosity and an awesome mineral.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mineral", choices=MINERALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


def explain_rejection(place: str, mineral: str) -> str:
    return f"(No story: {mineral} is not a safe fit for {place} in this fable world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mineral:
        if (args.place, args.mineral) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.mineral))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mineral is None or c[1] == args.mineral)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mineral = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mineral=mineral, name=name, gender=gender, elder=elder, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mineral = f["hero"], f["mineral"]
    return [
        f'Write a short fable for a child about Curiosity, an awesome {mineral.label}, and a careful choice.',
        f"Tell a gentle story about {hero.id}, a curious {hero.type}, who wants to study an awesome mineral in {f['setting'].place}.",
        f'Write a simple moral tale that includes the words "awesome" and "mineral" and ends with a lesson about patience.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, mineral, tool = f["hero"], f["elder"], f["mineral"], f["tool"]
    return [
        QAItem(
            question=f"Who found the awesome {mineral.label}?",
            answer=f"{hero.id} found it in {f['setting'].place}, and {elder.id} helped {hero.pronoun('object')} study it safely.",
        ),
        QAItem(
            question=f"Why did {hero.id} need help with the mineral?",
            answer=f"Because {hero.pronoun('possessive')} curiosity made {hero.id} rush forward, and the stone needed a careful touch so it would not get hurt.",
        ),
        QAItem(
            question=f"What did they use to look at the {mineral.label} safely?",
            answer=f"They used {tool.label} so {hero.id} could look closely without damaging the mineral.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer="The lesson was that curiosity is wonderful when it listens, slows down, and uses care.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mineral = f["mineral"]
    out = [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to ask questions, look closely, and learn more.",
        ),
        QAItem(
            question="What is a mineral?",
            answer="A mineral is a natural solid found in the earth, like quartz or jade.",
        ),
    ]
    if mineral.id == "quartz":
        out.append(QAItem(question="What is quartz?", answer="Quartz is a hard mineral that can look clear or milky and often has a shiny surface."))
    if mineral.id == "jade":
        out.append(QAItem(question="What is jade?", answer="Jade is a smooth green stone people often think is beautiful and special."))
    if mineral.id == "amber":
        out.append(QAItem(question="What is amber?", answer="Amber is a golden material that can shine warmly and look like sunlight caught in a stone."))
    if mineral.id == "mica":
        out.append(QAItem(question="What is mica?", answer="Mica is a sparkly mineral that can split into thin shiny pieces."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="stone_garden", mineral="quartz", name="Mira", gender="girl", elder="Tobin", trait="curious"),
    StoryParams(place="riverbank", mineral="mica", name="Oren", gender="boy", elder="Sage", trait="careful"),
    StoryParams(place="cave_hall", mineral="jade", name="Lina", gender="girl", elder="Dara", trait="bright-eyed"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MINERALS[params.mineral], params.name, params.gender, params.elder)
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


ASP_RULES = r"""
place(P) :- setting(P).
mineral(M) :- mineral_type(M).
tool(T) :- tool_type(T).

compatible(P, M) :- setting_affords(P, M), has_tool(M).
valid_story(P, M) :- compatible(P, M).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for m in SETTINGS[p].affords:
            lines.append(asp.fact("setting_affords", p, m))
    for m, mineral in MINERALS.items():
        lines.append(asp.fact("mineral_type", m))
        for tag in mineral.tags:
            lines.append(asp.fact("tag", m, tag))
        if select_tool(mineral) is not None:
            lines.append(asp.fact("has_tool", m))
    for t in TOOLS:
        lines.append(asp.fact("tool_type", t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(clingo_set - py_set))
    print(" only in python:", sorted(py_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible stories:")
        for p, m in vals:
            print(f"  {p:12} {m}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mineral} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

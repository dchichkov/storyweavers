#!/usr/bin/env python3
"""
A tiny adventure storyworld about a rhyming trail of mess that lingers.

A child goes on a small quest to find a lost rhyme token. Along the way, a
silly sticky mess clings to shoes and fur, and the hero must decide whether to
push on or clean up. The story turns on a helpful companion, a practical tool,
and the fact that some mess can linger longer than expected.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    rhyme_line: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in e.covers for e in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


THRESHOLD = 1.0
MESS_KINDS = {"sticky", "muddy", "sandy"}


def _r_mess_lingers(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("mess", 0) < THRESHOLD:
            continue
        if item.meters.get("lingering", 0) >= THRESHOLD:
            continue
        if item.id in world.fired:
            continue
        world.fired.add((item.id, "linger"))
        item.meters["lingering"] = item.meters.get("lingering", 0) + 1
        out.append(f"The mess lingered on {item.label}.")
    return out


def _r_help_cleans(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.kind == "character"), None)
    if not hero:
        return out
    if hero.memes.get("resolve", 0) < THRESHOLD:
        return out
    for item in world.worn_items(hero):
        if item.meters.get("mess", 0) >= THRESHOLD and item.meters.get("cleaned", 0) < THRESHOLD:
            item.meters["cleaned"] = 1
            out.append(f"{hero.id} wiped {item.label} clean.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_mess_lingers, _r_help_cleans):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_at_risk(quest: Quest, prize: str) -> bool:
    return prize in {"cloak", "boots", "pack"}


def select_tool(quest: Quest, prize: str) -> Optional[Tool]:
    for tool in TOOLS:
        if quest.mess in tool.guards and any(r in tool.covers for r in PRIZES[prize].covers):
            return tool
    return None


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} with a brave heart and quick feet.")


def begin_quest(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {helper.label} set out for {world.place.label}."
    )
    world.say(
        f"They wanted to {quest.verb} and find the lost {prize.label}, because adventure called like a bell."
    )
    world.say(f"The path was bright, but the {quest.keyword} signs whispered, \"Rhyme and roam!\"")


def tension(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(
        f"{hero.id} rushed to {quest.rush}, but a sticky mess clung to {hero.pronoun('possessive')} shoes."
    )
    world.zone = set(quest.zone)
    hero.meters["mess"] = hero.meters.get("mess", 0) + 1
    propagate(world, narrate=True)
    if prize.meters.get("lingering", 0) >= THRESHOLD:
        world.say(
            f"The mess did not vanish right away; it lingered like glue in a tune."
        )


def warn(world: World, helper: Entity, hero: Entity, quest: Quest, prize: Entity) -> None:
    if prize_at_risk(quest, prize.label):
        world.say(
            f'"If you keep going," {helper.id} said, "your {prize.label} will get {quest.soil}."'
        )
    else:
        world.say(f'"This trail is safe enough," {helper.id} said, "but the mess may still linger."')


def compromise(world: World, helper: Entity, hero: Entity, quest: Quest, prize: Entity) -> Optional[Tool]:
    tool_def = select_tool(quest, prize.label)
    if tool_def is None:
        return None
    tool = world.add(
        Entity(
            id=tool_def.id,
            type="tool",
            label=tool_def.label,
            protective=True,
            covers=set(tool_def.covers),
            owner=hero.id,
            worn_by=hero.id,
        )
    )
    world.say(
        f"{helper.id} smiled and said, \"How about we {tool_def.prep} and try again?\""
    )
    return tool_def


def resolution(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity, tool: Tool) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.id} nodded, tied on the {tool.label}, and went on with a grin."
    )
    world.say(
        f"At last they found the lost {prize.label}. {quest.rhyme_line} Then the two of them laughed, "
        f"and even the mess that lingered could not stop the quest."
    )


def tell(place: Place, quest: Quest, prize_cfg: "Prize", name: str, gender: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_type))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            caretaker=helper.id,
            owner=hero.id,
            covers=set(prize_cfg.covers),
        )
    )

    introduce(world, hero)
    begin_quest(world, hero, helper, quest, prize)
    world.para()
    tension(world, hero, helper, quest, prize)
    warn(world, helper, hero, quest, prize)
    world.para()
    tool_def = compromise(world, helper, hero, quest, prize)
    if tool_def is not None:
        resolution(world, hero, helper, quest, prize, tool_def)

    world.facts.update(hero=hero, helper=helper, prize=prize, quest=quest, place=place, tool=tool_def)
    return world


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    covers: set[str]


PLACES = {
    "forest": Place(id="forest", label="the forest path", mood="wild", affords={"trail", "rhyme"}),
    "harbor": Place(id="harbor", label="the harbor stairs", mood="windy", affords={"trail", "rhyme"}),
    "cave": Place(id="cave", label="the glowing cave", mood="echoing", affords={"trail", "rhyme"}),
}

QUESTS = {
    "trail": Quest(
        id="trail",
        verb="follow the trail",
        gerund="following the trail",
        rush="run after the tracks",
        mess="sticky",
        soil="sticky and dull",
        zone={"shoes", "pack"},
        rhyme_line="Riddle, diddle, little middle, the trail led back to the riddle.",
        keyword="trail",
        tags={"trail", "mess", "linger"},
    ),
    "rhyme": Quest(
        id="rhyme",
        verb="catch the rhyme",
        gerund="catching the rhyme",
        rush="dash toward the singing rock",
        mess="sandy",
        soil="sandy and stuck",
        zone={"cloak", "pack"},
        rhyme_line="Tick and tock, the rhyme unlocked the hidden box.",
        keyword="rhyme",
        tags={"rhyme", "mess", "linger"},
    ),
}

PRIZES = {
    "boots": Prize(label="boots", phrase="sturdy travel boots", type="boots", covers={"shoes"}),
    "cloak": Prize(label="cloak", phrase="a bright adventure cloak", type="cloak", covers={"cloak"}),
    "pack": Prize(label="pack", phrase="a small map pack", type="pack", covers={"pack"}),
}

TOOLS = [
    Tool(id="brush", label="a soft brush", covers={"shoes"}, guards={"sticky", "sandy"}, prep="brush off the sticky bits", tail="brushed the path clean"),
    Tool(id="cloth", label="a clean cloth", covers={"cloak", "pack"}, guards={"sticky", "sandy"}, prep="wipe the mess away", tail="wiped the cloth and tucked it away"),
    Tool(id="water", label="a water bottle", covers={"shoes", "cloak", "pack"}, guards={"sticky", "sandy"}, prep="rinse everything carefully", tail="rinsed away the lingering mess"),
]

GIRL_NAMES = ["Mira", "Nina", "Tia", "Luna", "Pia"]
BOY_NAMES = ["Rex", "Owen", "Jules", "Kai", "Finn"]
HELPERS = ["mother", "father", "sister", "brother", "guide"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for quest in QUESTS:
            for prize in PRIZES:
                if quest_at_risk(QUESTS[quest], prize) and select_tool(QUESTS[quest], prize):
                    out.append((place, quest, prize))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child that uses the words "mess" and "linger".',
        f"Tell a rhyming adventure about {f['hero'].id}, who wants to {f['quest'].verb} at {f['place'].label}, but a mess lingers and a helper finds a fix.",
        f"Create a gentle quest story where the hero meets a sticky problem, then chooses a tool and keeps going.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, quest, place = f["hero"], f["helper"], f["prize"], f["quest"], f["place"]
    tool = f.get("tool")
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to do on the adventure?",
            answer=f"{hero.id} was trying to {quest.verb} at {place.label} and find the lost {prize.label}.",
        ),
        QAItem(
            question=f"What problem slowed the quest down?",
            answer=f"A sticky mess got on the way, and it did not leave right away. It lingered on the journey.",
        ),
        QAItem(
            question=f"Who helped {hero.id} think of a safer plan?",
            answer=f"{helper.id} helped by noticing the problem and offering a practical way to keep going.",
        ),
    ]
    if tool is not None:
        qa.append(
            QAItem(
                question=f"What tool helped {hero.id} keep going?",
                answer=f"{tool.label} helped {hero.id} deal with the mess so the adventure could continue.",
            )
        )
    qa.append(
        QAItem(
            question=f"How did the story end?",
            answer=f"The hero finished the quest, found the lost {prize.label}, and the lingering mess could not spoil the happy ending.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like 'cat' and 'hat'.",
        ),
        QAItem(
            question="What does linger mean?",
            answer="To linger means to stay around for a while instead of leaving right away.",
        ),
        QAItem(
            question="Why can mess be hard to ignore?",
            answer="Mess can be hard to ignore because it sticks to things and changes how they look and feel.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"zone={sorted(world.zone)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(Q,P) :- quest(Q), prize(P), splashes(Q,R), worn_on(P,R).
tool_fix(T,Q,P) :- tool(T), prize_at_risk(Q,P), quest_mess(Q,M), guards(T,M), covers(T,R), worn_on(P,R).
valid(Place,Q,P) :- place(Place), affords(Place,Q), prize_at_risk(Q,P), tool_fix(_,Q,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for q in sorted(p.affords):
            lines.append(asp.fact("affords", p.id, q))
    for q in QUESTS.values():
        lines.append(asp.fact("quest", q.id))
        lines.append(asp.fact("quest_mess", q.id, q.mess))
        for r in sorted(q.zone):
            lines.append(asp.fact("splashes", q.id, r))
    for p in PRIZES.values():
        lines.append(asp.fact("prize", p.label))
        for r in sorted(p.covers):
            lines.append(asp.fact("worn_on", p.label, r))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for m in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, m))
        for r in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about mess and linger, with rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], PRIZES[params.prize], params.name, params.gender, params.helper)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place, quest, prize in [
            ("forest", "trail", "boots"),
            ("harbor", "rhyme", "cloak"),
            ("cave", "trail", "pack"),
        ]:
            p = StoryParams(place=place, quest=quest, prize=prize, name="Mira", gender="girl", helper="guide")
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

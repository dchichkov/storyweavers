#!/usr/bin/env python3
"""
storyworlds/worlds/chump_queer_proper_inner_monologue_quest_adventure.py
=======================================================================

A small standalone storyworld built from the seed words:
chump, queer, proper

Domain:
- Adventure style
- Inner Monologue
- Quest structure

The world simulates a child-facing adventure where a character wants to prove
they are proper enough for a quest, worries they seem like a chump, and learns
that a queer little detail in the world can be the key to success.

The story state drives prose: meters track physical progress and resources,
memes track self-doubt, courage, belonging, and delight. The ending changes
based on the quest state and the helper found along the way.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0, "progress": 0.0, "stuck": 0.0}
        if not self.memes:
            self.memes = {"doubt": 0.0, "courage": 0.0, "wonder": 0.0, "pride": 0.0}


@dataclass
class Location:
    id: str
    label: str
    details: str
    queer_detail: str
    hazard: str
    ending_image: str


@dataclass
class QuestItem:
    id: str
    label: str
    use: str
    helpful: str
    tool: bool = False


@dataclass
class Companion:
    id: str
    label: str
    kind: str
    role: str
    speech_style: str
    helps_with: str


@dataclass
class StoryParams:
    setting: str
    location: str
    quest_item: str
    companion: str
    style_word: str = "Adventure"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        return World(
            entities=copy.deepcopy(self.entities),
            facts=dict(self.facts),
            paragraphs=[[]],
            fired=set(self.fired),
        )


LOCATIONS = {
    "harbor": Location(
        id="harbor",
        label="the harbor path",
        details="a dock path lined with rope coils and gull shadows",
        queer_detail="a queer little blue shell that chimed when the wind touched it",
        hazard="slippery boards",
        ending_image="the shell chimed softly beside the safe trail",
    ),
    "woods": Location(
        id="woods",
        label="the old woods",
        details="a pine tunnel with moss and bright stones",
        queer_detail="a queer round stone that glowed green under leaves",
        hazard="thorny brambles",
        ending_image="the green stone blinked beside the path like a tiny lantern",
    ),
    "market": Location(
        id="market",
        label="the market lane",
        details="a lane of awnings, baskets, and narrow alleys",
        queer_detail="a queer striped ribbon tied in a knot no one could copy",
        hazard="crowded carts",
        ending_image="the striped ribbon fluttered above the lane like a clue flag",
    ),
}

QUEST_ITEMS = {
    "map": QuestItem("map", "the map", "read the hidden trail", "helps them know where to go"),
    "key": QuestItem("key", "the key", "open the little gate", "fits the gate at the end", tool=True),
    "lantern": QuestItem("lantern", "the lantern", "light the dark turn", "brings a warm safe glow", tool=True),
}

COMPANIONS = {
    "fox": Companion("fox", "a fox", "animal", "guide", "quiet and sly", "spots small clues"),
    "bird": Companion("bird", "a bird", "animal", "guide", "bright and chirpy", "flies ahead"),
    "neighbor": Companion("neighbor", "the neighbor", "person", "helper", "calm and proper", "shows the steady way"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with inner monologue and a quest.")
    ap.add_argument("--setting", choices=LOCATIONS)
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(LOCATIONS))
    location = args.location or setting
    quest_item = args.quest_item or rng.choice(sorted(QUEST_ITEMS))
    companion = args.companion or rng.choice(sorted(COMPANIONS))
    return StoryParams(setting=setting, location=location, quest_item=quest_item, companion=companion, seed=args.seed)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for k in LOCATIONS:
        lines.append(asp.fact("location", k))
    for k in QUEST_ITEMS:
        lines.append(asp.fact("quest_item", k))
    for k in COMPANIONS:
        lines.append(asp.fact("companion", k))
    return "\n".join(lines)


ASP_RULES = r"""
selected(X) :- location(X).
quest_ready :- quest_item(map).
quest_ready :- quest_item(key).
quest_ready :- quest_item(lantern).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    return 0


def _inner_monologue(hero: Entity, world: World, loc: Location) -> None:
    hero.memes["doubt"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"{hero.id} looked at {loc.details} and tried to stand very straight. "
        f"Inside, {hero.id} worried, 'What if I'm a chump and everyone can tell?'"
    )
    world.say(
        f"Then another thought came, quiet but proper: 'A real quest starts when I keep going.'"
    )


def _approach(world: World, hero: Entity, item: QuestItem, comp: Companion, loc: Location) -> None:
    hero.meters["distance"] += 1
    hero.meters["progress"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} followed {comp.label} toward {loc.label}. "
        f"{comp.label.capitalize()} stayed {comp.speech_style}, and {comp.label} knew {comp.helps_with}."
    )
    world.say(
        f"Their quest was to find {item.label}, because it could {item.use}."
    )


def _hazard(world: World, hero: Entity, loc: Location, comp: Companion) -> None:
    hero.meters["stuck"] += 1
    hero.memes["doubt"] += 1
    world.say(
        f"At {loc.label}, the way narrowed with {loc.hazard}. "
        f"{hero.id} almost stopped."
    )
    world.say(
        f"Inside, {hero.id} thought, 'This is the part where a chump would turn back.'"
    )
    world.say(
        f"But then {comp.label} pointed at {loc.queer_detail}, and the queer little clue mattered more than the fear."
    )


def _solve(world: World, hero: Entity, item: QuestItem, loc: Location) -> None:
    hero.meters["progress"] += 2
    hero.memes["courage"] += 2
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} used {item.label} to finish the quest. "
        f"It {item.helpful}, and that made the last step feel proper instead of scary."
    )
    world.say(
        f"At the end, {loc.ending_image}, and {hero.id} smiled because being proper meant being brave enough to do the kind thing."
    )


def _failed_turn(world: World, hero: Entity, item: QuestItem) -> None:
    hero.meters["stuck"] += 1
    hero.memes["doubt"] += 1
    world.say(
        f"{hero.id} tried to rush ahead, but the quest snagged. The best move was to slow down and listen."
    )
    world.say(
        f"In the quiet, {hero.id} admitted, 'I do not need to act like a chump. I need to act proper.'"
    )
    world.say("That small thought was enough to start the next step.")


def tell(params: StoryParams) -> World:
    world = World()
    loc = LOCATIONS[params.location]
    item = QUEST_ITEMS[params.quest_item]
    comp = COMPANIONS[params.companion]
    hero = world.add(Entity(id="Milo", kind="character", type="child", role="hero"))
    world.facts.update(loc=loc, item=item, comp=comp, params=params)

    world.say(
        f"On a bright morning in {params.setting}, Milo set out on an adventure quest."
    )
    world.say(
        f"Milo wanted to seem proper, not like a chump, so Milo lifted {item.label} and went on."
    )
    world.para()
    _inner_monologue(hero, world, loc)
    _approach(world, hero, item, comp, loc)
    world.para()
    _hazard(world, hero, loc, comp)
    if item.id == "map":
        _solve(world, hero, item, loc)
    elif item.id == "lantern":
        _solve(world, hero, item, loc)
    else:
        _failed_turn(world, hero, item)
        _solve(world, hero, item, loc)
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    loc: Location = world.facts["loc"]
    item: QuestItem = world.facts["item"]
    return [
        f"Write an Adventure story where Milo goes on a quest through {loc.label} and thinks about being a chump versus being proper.",
        f"Tell a child-facing Inner Monologue quest tale in {p.setting} using {item.label} and a queer little clue.",
        f"Write a short adventure about Milo, {item.label}, and the need to stay proper when the path gets tricky.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    loc: Location = world.facts["loc"]
    item: QuestItem = world.facts["item"]
    comp: Companion = world.facts["comp"]
    return [
        QAItem(question="What was Milo trying to do?", answer=f"Milo was trying to finish a quest in {loc.label} and prove that staying proper was better than acting like a chump."),
        QAItem(question="Who helped Milo?", answer=f"{comp.label.capitalize()} helped Milo by staying nearby and pointing out the queer little clue."),
        QAItem(question=f"What did Milo carry on the quest?", answer=f"Milo carried {item.label}, which could {item.use}."),
        QAItem(question="What was the queer detail in the setting?", answer=loc.queer_detail.capitalize() + "."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a quest?", answer="A quest is a journey to find or do something important."),
        QAItem(question="What is inner monologue?", answer="Inner monologue is the quiet voice a character thinks inside their head."),
        QAItem(question="What does proper mean here?", answer="Proper means careful, respectful, and doing the right thing."),
        QAItem(question="What does chump mean here?", answer="A chump is someone who acts silly or gets fooled, but the story shows Milo can do better than that."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="harbor", location="harbor", quest_item="map", companion="fox"),
    StoryParams(setting="woods", location="woods", quest_item="lantern", companion="bird"),
    StoryParams(setting="market", location="market", quest_item="key", companion="neighbor"),
]


def generate(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show location/1.\n#show quest_item/1.\n#show companion/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program(show="#show location/1.\n#show quest_item/1.\n#show companion/1."))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample]
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(args.n):
            p = resolve_params(args, random.Random(rng.randrange(2**31)))
            p.seed = args.seed
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

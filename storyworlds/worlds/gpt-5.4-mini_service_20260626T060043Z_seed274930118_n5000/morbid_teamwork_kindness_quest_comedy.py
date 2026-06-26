#!/usr/bin/env python3
"""
Standalone storyworld: a comedic kindness quest with a faint morbid flourish.

Premise:
- A small team goes on a quest to return a misplaced lantern to a lonely
  graveyard gatekeeper so the gate can stay cheerful at dusk.
- One character is theatrically morbid; the others respond with teamwork and
  kindness, turning the spooky mood into a funny one.

This world is deliberately small and constraint-checked:
- typed entities with physical meters and emotional memes
- state changes drive the narration
- invalid explicit choices raise StoryError
- inline ASP rules mirror the Python reasonableness gate
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


# ---------------------------------------------------------------------------
# Entities / world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carrier: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
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
    goal: str
    verb: str
    rush: str
    keyword: str
    risk: str
    completion: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    requires: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "gate": Place("gate", "the old gate", mood="dusky", affords={"lantern_quest"}),
    "path": Place("path", "the lantern path", mood="twilight", affords={"lantern_quest"}),
    "yard": Place("yard", "the moonlit yard", mood="quirky", affords={"lantern_quest"}),
}

QUESTS = {
    "lantern_quest": Quest(
        id="lantern_quest",
        goal="return the lantern to the gatekeeper",
        verb="carry the lantern home",
        rush="dash toward the gate",
        keyword="lantern",
        risk="the gate will stay gloomy",
        completion="the gate glowed again",
        tags={"quest", "kindness", "teamwork", "comedy"},
    )
}

PRIZES = {
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a brass lantern with a wobbly handle",
        type="lantern",
        requires={"carry"},
    )
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a length of rope",
        prep="tie a rope loop through the handle first",
        tail="used the rope loop to carry it together",
        helps={"carry"},
    ),
    "gloves": Tool(
        id="gloves",
        label="soft gloves",
        prep="put on soft gloves before lifting it",
        tail="picked it up carefully in soft gloves",
        helps={"carry"},
    ),
}

NAMES = ["Mina", "Toby", "Iris", "Pip", "June", "Benny", "Cora", "Ollie"]
TYPES = ["girl", "boy"]
TRAITS = ["cheerful", "helpful", "curious", "silly", "gentle", "brave"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    hero: str
    hero_type: str
    ally: str
    ally_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.id == "lantern" and quest.id == "lantern_quest"


def select_tool(quest: Quest, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS.values():
        if quest.risk and "carry" in tool.helps and prize.id == "lantern":
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for qid, quest in QUESTS.items():
            for prid, prize in PRIZES.items():
                if pid in {"gate", "path", "yard"} and prize_at_risk(quest, prize) and select_tool(quest, prize):
                    combos.append((pid, qid, prid))
    return combos


def explain_rejection(quest: Quest, prize: Prize) -> str:
    return (
        f"(No story: this quest only works when the lantern is actually at risk "
        f"and there is a sensible way for the team to carry it. Try the lantern quest.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def predict_mess(world: World, quest: Quest, prize_id: str) -> dict:
    sim = world.copy()
    do_quest(sim, quest, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "broken": bool(prize and prize.meters.get("broken", 0) > 0),
        "lost": bool(prize and prize.carrier is None),
    }


def do_quest(world: World, quest: Quest, narrate: bool = True) -> None:
    hero = world.get(world.facts["hero"].id)
    ally = world.get(world.facts["ally"].id)
    prize = world.get(world.facts["prize"].id)

    hero.meters["purpose"] = hero.meters.get("purpose", 0) + 1
    ally.meters["purpose"] = ally.meters.get("purpose", 0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    ally.memes["hope"] = ally.memes.get("hope", 0) + 1

    # Teamwork: if they cooperate, the lantern gets carried.
    if world.facts.get("tool"):
        tool = world.facts["tool"]
        prize.carrier = hero.id
        hero.memes["pride"] = hero.memes.get("pride", 0) + 1
        ally.memes["pride"] = ally.memes.get("pride", 0) + 1
        hero.meters["carry"] = hero.meters.get("carry", 0) + 1
        ally.meters["carry"] = ally.meters.get("carry", 0) + 1
        if narrate:
            world.say(
                f"Together they {tool.tail}, and the lantern stopped wobbling."
            )
    else:
        prize.carrier = hero.id
        if narrate:
            world.say("They tried to carry it alone, but the handle kept slipping.")

    # Comedy beat: the morbid character is dramatic, but kind.
    if hero.memes.get("morbid", 0) > 0:
        hero.memes["humor"] = hero.memes.get("humor", 0) + 1
        if narrate:
            world.say(
                f"{hero.id} sighed in a very morbid way about the 'terrible fate of sad lanterns,' "
                f"which was so dramatic that {ally.id} snorted a laugh."
            )


def introduce(world: World, hero: Entity, ally: Entity, prize: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type} who liked tiny quests and big plans."
    )
    world.say(
        f"{ally.id} was the sort of friend who could turn a serious moment into a giggle."
    )
    world.say(
        f"One dusky evening, they heard about {prize.phrase} that needed to be returned "
        f"to finish {quest.goal}."
    )


def begin(world: World, quest: Quest, prize: Entity) -> None:
    world.para()
    world.say(
        f"They set off to {quest.verb}, because {quest.risk} if nobody helped."
    )
    world.say(
        f"The path looked spooky in the dim light, but it also looked a little funny, "
        f"like even the shadows were trying not to laugh."
    )


def tension(world: World, hero: Entity, ally: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["morbid"] = hero.memes.get("morbid", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} became morbidly dramatic and whispered, 'What if the lantern lives a lonely life forever?'"
    )
    world.say(
        f"{ally.id} blinked, then said, 'Then we should rescue it together.'"
    )
    hero.memes["determination"] = hero.memes.get("determination", 0) + 1


def warning(world: World, hero: Entity, quest: Quest, prize: Entity) -> bool:
    pred = predict_mess(world, quest, prize.id)
    if pred["lost"]:
        world.say(
            f"'If we rush and fumble, we'll lose the lantern,' {world.facts['ally'].id} said. "
            f"'Let's use our heads and our hands.'"
        )
        return True
    return False


def offer_tool(world: World, hero: Entity, ally: Entity, quest: Quest, prize: Entity) -> Optional[Tool]:
    tool = select_tool(quest, prize)
    if not tool:
        return None
    world.facts["tool"] = tool
    world.say(
        f"{ally.id} found {tool.label} and suggested, '{tool.prep}.'"
    )
    return tool


def resolution(world: World, hero: Entity, ally: Entity, quest: Quest, prize: Entity, tool: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    ally.memes["joy"] = ally.memes.get("joy", 0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    ally.memes["kindness"] = ally.memes.get("kindness", 0) + 1
    prize.carrier = hero.id
    world.para()
    world.say(
        f"They chose the kind plan, and soon {tool.tail}."
    )
    world.say(
        f"When they reached the gate, the lantern was safe, {quest.completion}, and the whole place looked cheerful again."
    )
    world.say(
        f"{hero.id} grinned and admitted that the best part of the quest was not the spooky part at all, "
        f"but working together without dropping anything."
    )


def tell(place: Place, quest: Quest, prize_cfg: Prize, hero_name: str, hero_type: str,
         ally_name: str, ally_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, traits=[trait, "morbid"]
    ))
    ally = world.add(Entity(
        id=ally_name, kind="character", type=ally_type, traits=["kind", "quick"]
    ))
    prize = world.add(Entity(
        id=prize_cfg.id, kind="thing", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id
    ))
    world.facts["hero"] = hero
    world.facts["ally"] = ally
    world.facts["prize"] = prize

    introduce(world, hero, ally, prize, quest)
    begin(world, quest, prize)
    tension(world, hero, ally, quest, prize)
    warning(world, hero, quest, prize)
    tool = offer_tool(world, hero, ally, quest, prize)
    if tool:
        do_quest(world, quest)
        resolution(world, hero, ally, quest, prize, tool)
    else:
        do_quest(world, quest)
        world.para()
        world.say("They managed to finish the quest, but only after a lot of wobbling and apologizing.")
    world.facts.update(tool=tool, quest=quest, place=place)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    quest = f["quest"]
    prize = f["prize"]
    return [
        f"Write a short comedy about a morbid but kind {hero.type} named {hero.id} and a friend who solve a lantern quest together.",
        f"Tell a child-friendly story where {hero.id} and {ally.id} must return {prize.phrase} without dropping it.",
        f"Write a funny quest story about teamwork and kindness that includes the word 'morbid' once.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    prize = f["prize"]
    quest = f["quest"]
    tool = f.get("tool")
    qa = [
        QAItem(
            question=f"Who went on the quest together?",
            answer=f"{hero.id} and {ally.id} went together so they could return the lantern safely.",
        ),
        QAItem(
            question=f"What were they trying to do with the lantern?",
            answer=f"They were trying to {quest.verb} and finish the quest for the gatekeeper.",
        ),
        QAItem(
            question=f"Why did the story get funny instead of just spooky?",
            answer=f"It got funny because {hero.id} acted morbidly dramatic while {ally.id} kept answering with kindness and a practical plan.",
        ),
    ]
    if tool:
        qa.append(
            QAItem(
                question="What helped them carry the lantern?",
                answer=f"{tool.label} helped them carry it together without dropping {prize.it()}.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together instead of all by themselves.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and thoughtful toward someone else.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to reach a goal.",
        ),
        QAItem(
            question="What does morbid mean here?",
            answer="Morbid here means the character is joking in a very spooky, overdramatic way, not being truly scary.",
        ),
    ]
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(Q,P) :- quest(Q), prize(P), q_requires(Q,P).
has_tool(Q,P) :- prize_at_risk(Q,P), tool(T), helps(T,carry).
valid(P,Q,R) :- place(P), quest(Q), prize(R), prize_at_risk(Q,R), has_tool(Q,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for req in ["lantern"]:
            lines.append(asp.fact("q_requires", qid, req))
    for prid in PRIZES:
        lines.append(asp.fact("prize", prid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic kindness quest with a morbid little flourish.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--ally")
    ap.add_argument("--ally-type", choices=TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.quest and args.prize:
        q = QUESTS[args.quest]
        p = PRIZES[args.prize]
        if not (prize_at_risk(q, p) and select_tool(q, p)):
            raise StoryError(explain_rejection(q, p))
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid combinations exist.")
    place, quest, prize = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(TYPES)
    ally_type = args.ally_type or rng.choice(TYPES)
    hero = args.hero or rng.choice(NAMES)
    ally = args.ally or rng.choice([n for n in NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        quest=quest,
        prize=prize,
        hero=hero,
        hero_type=hero_type,
        ally=ally,
        ally_type=ally_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        QUESTS[params.quest],
        PRIZES[params.prize],
        params.hero,
        params.hero_type,
        params.ally,
        params.ally_type,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = [f"--- place: {world.place.label} ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carrier:
            bits.append(f"carrier={e.carrier}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams("gate", "lantern_quest", "lantern", "Mina", "girl", "Toby", "boy", "silly"),
    StoryParams("path", "lantern_quest", "lantern", "Pip", "boy", "Iris", "girl", "curious"),
    StoryParams("yard", "lantern_quest", "lantern", "Cora", "girl", "Ollie", "boy", "gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero} and {p.ally}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

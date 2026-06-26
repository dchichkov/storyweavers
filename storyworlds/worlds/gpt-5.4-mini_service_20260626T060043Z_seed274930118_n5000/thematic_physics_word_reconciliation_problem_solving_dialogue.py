#!/usr/bin/env python3
"""
Standalone storyworld: thematic physics word reconciliation through dialogue and problem solving.

A small, heartwarming classroom domain:
- Two children disagree over how to arrange themed word cards for a physics display.
- The tension is caused by a practical problem: limited space and a toppled stack of cards.
- The turn comes through dialogue and collaborative problem solving.
- The resolution is a reconciled display that proves what changed in the world.

This script follows the Storyweavers world contract:
- typed entities with physical meters and emotional memes
- seeded, state-driven story generation
- QA sets for story grounding and world knowledge
- inline ASP twin plus Python reasonableness gate
- CLI support for default runs, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Topic:
    id: str
    keyword: str
    display: str
    problem: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    theme: str
    fragile: bool = False
    stable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    supports: set[str]
    prep: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    table = world.facts.get("table")
    if not table:
        return out
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.meters.get("frustration", 0) < THRESHOLD:
            continue
        if ("scatter", actor.id) in world.fired:
            continue
        world.fired.add(("scatter", actor.id))
        card = world.get(table)
        card.meters["disorder"] = card.meters.get("disorder", 0) + 1
        out.append(f"The cards on the table slipped out of place.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    for aid in world.entities.values():
        if aid.kind != "aid":
            continue
        if aid.meters.get("used", 0) < THRESHOLD:
            continue
        if ("repair", aid.id) in world.fired:
            continue
        world.fired.add(("repair", aid.id))
        board = world.facts.get("board")
        if board:
            obj = world.get(board)
            obj.meters["order"] = obj.meters.get("order", 0) + 1
            obj.meters["disorder"] = max(0, obj.meters.get("disorder", 0) - 1)
        out.append(f"That made the display steadier and easier to read.")
    return out


CAUSAL_RULES = [Rule("scatter", _r_scatter), Rule("repair", _r_repair)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def validity_check(topic: Topic, prop: Prop, aid: Aid) -> bool:
    return topic.id in prop.tags and topic.id in aid.helps and prop.theme in aid.supports


def choose_aid(topic: Topic, prop: Prop) -> Optional[Aid]:
    for aid in AIDS:
        if topic.id in aid.helps and prop.theme in aid.supports:
            return aid
    return None


def predict_problem(world: World, hero: Entity, topic: Topic, prop: Prop) -> bool:
    sim = world.copy()
    hero_sim = sim.get(hero.id)
    hero_sim.meters["frustration"] = 1.0
    propagate(sim, narrate=False)
    return bool(sim.facts.get("board") and sim.get(sim.facts["board"]).meters.get("disorder", 0) >= THRESHOLD)


SETTINGS = {
    "classroom": Setting(place="the classroom", indoor=True, affords={"display"}),
    "library": Setting(place="the library corner", indoor=True, affords={"display"}),
    "clubroom": Setting(place="the clubroom", indoor=True, affords={"display"}),
}

TOPICS = {
    "thematic": Topic(
        id="thematic",
        keyword="thematic",
        display="theme cards",
        problem="the cards did not match the story theme",
        action="sort the cards by idea",
        result="the cards showed one clear theme",
        tags={"thematic", "word"},
    ),
    "physics": Topic(
        id="physics",
        keyword="physics",
        display="physics cards",
        problem="the cards were mixed up with the wrong labels",
        action="group the cards by force and motion",
        result="the cards matched the lesson",
        tags={"physics", "word"},
    ),
    "word": Topic(
        id="word",
        keyword="word",
        display="word cards",
        problem="some words kept falling out of the stack",
        action="arrange the words into neat rows",
        result="the words stayed easy to read",
        tags={"word", "thematic", "physics"},
    ),
}

PROPS = {
    "cards": Prop(
        id="cards",
        label="word cards",
        phrase="a stack of word cards",
        theme="word",
        fragile=True,
        stable=False,
        tags={"word", "thematic", "physics"},
    ),
    "poster": Prop(
        id="poster",
        label="poster board",
        phrase="a bright poster board",
        theme="thematic",
        fragile=False,
        stable=True,
        tags={"thematic"},
    ),
    "labels": Prop(
        id="labels",
        label="label strips",
        phrase="some label strips",
        theme="physics",
        fragile=False,
        stable=True,
        tags={"physics"},
    ),
}

AIDS = [
    Aid(
        id="tape",
        label="a roll of tape",
        phrase="a roll of tape",
        helps={"word", "thematic", "physics"},
        supports={"word", "thematic", "physics"},
        prep="tape the cards to the board",
        result="the cards stayed put",
        tags={"word", "thematic", "physics"},
    ),
    Aid(
        id="folders",
        label="two folder trays",
        phrase="two folder trays",
        helps={"word", "physics"},
        supports={"word", "physics"},
        prep="sort the cards into trays first",
        result="the cards stopped sliding around",
        tags={"word", "physics"},
    ),
    Aid(
        id="string",
        label="a string line",
        phrase="a string line",
        helps={"thematic"},
        supports={"thematic"},
        prep="hang the theme cards on a line",
        result="the display looked tidy",
        tags={"thematic"},
    ),
]


GIRL_NAMES = ["Mina", "Lila", "Ivy", "Nora", "Zoe", "Maya", "Ada", "Rosa"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Finn", "Leo", "Owen", "Ben", "Max"]
TRAITS = ["gentle", "curious", "patient", "kind", "careful", "bright"]


@dataclass
class StoryParams:
    place: str
    topic: str
    prop: str
    name: str
    gender: str
    partner: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for topic_id in setting.affords:
            topic = TOPICS[topic_id]
            for prop_id, prop in PROPS.items():
                if validity_check(topic, prop, choose_aid(topic, prop) or AIDS[0]):
                    combos.append((place, topic_id, prop_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming classroom storyworld about thematic physics word cards.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--topic", choices=TOPICS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.topic is None or c[1] == args.topic)
              and (args.prop is None or c[2] == args.prop)]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, topic, prop = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    partner = args.partner or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, topic=topic, prop=prop, name=name, gender=gender, partner=partner, trait=trait)


def tell(setting: Setting, topic: Topic, prop: Prop, hero_name: str, hero_gender: str, partner_gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    partner_name = "A friend"
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender))
    board = world.add(Entity(id="board", type="poster", label=prop.label, phrase=prop.phrase))
    world.facts["board"] = board.id
    world.facts["topic"] = topic
    world.facts["prop"] = prop

    world.say(f"{hero_name} was a {trait} child who loved making {topic.display} displays.")
    world.say(f"At {setting.place}, {hero_name} and {partner_name} had a pile of {prop.phrase}.")
    world.say(f"They wanted to {topic.action}, because {topic.problem}.")
    hero.meters["curiosity"] = 1.0
    partner.meters["care"] = 1.0

    world.para()
    world.say(f"But when {hero_name} reached for the cards, the stack tipped and the words slid out of order.")
    hero.meters["frustration"] = 1.0
    world.say(f"{hero_name} frowned, and {partner_name} looked worried too.")
    world.say(f"'{topic.display.capitalize()} should be easy to read,' {hero_name} said softly.")

    world.para()
    world.say(f"'{How' if False else ''}")
    aid = choose_aid(topic, prop)
    if aid is None:
        raise StoryError("No reasonable aid exists for this combination.")
    hero.meters["hope"] = 1.0
    partner.meters["hope"] = 1.0
    world.say(f"'{topic.display.capitalize()} and {prop.label} can still work,' {partner_name} said. 'Let's use {aid.label}.'")
    world.say(f"'{hero_name} nodded. 'Good idea. That will help {topic.action}.'")
    aid_entity = world.add(Entity(id=aid.id, kind="aid", type="aid", label=aid.label, phrase=aid.phrase))
    aid_entity.meters["used"] = 1.0
    propagate(world, narrate=True)

    world.para()
    hero.meters["reconciliation"] = 1.0
    partner.meters["reconciliation"] = 1.0
    world.say(f"Together they followed the plan: they used {aid.prep}, and soon {topic.result}.")
    world.say(f"{hero_name} smiled at {partner_name}, and the two friends felt proud of the neat, calm display.")
    world.say(f"At the end, the classroom board held {prop.label} that matched the {topic.keyword} theme, and everyone could read it clearly.")

    world.facts.update(hero=hero, partner=partner, aid=aid_entity, topic=topic, prop=prop, setting=setting, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    topic = f["topic"]
    prop = f["prop"]
    return [
        f'Write a heartwarming story about "{topic.keyword}" and "{prop.label}" in a classroom.',
        f"Tell a story where {hero.id} and a friend solve a problem by talking kindly and fixing a display.",
        f"Write a gentle dialogue-driven story that ends with {topic.result}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    topic = f["topic"]
    prop = f["prop"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"What problem did {hero.id} notice with the {prop.label}?",
            answer=f"{topic.problem.capitalize()}. The cards had slipped out of order, so the display was hard to read.",
        ),
        QAItem(
            question=f"How did {hero.id} and {partner.id} solve the problem?",
            answer=f"They talked kindly and used {aid.label} to help {topic.action}. That made the display steadier.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {prop.label} matched the {topic.keyword} theme, and the finished display was neat and easy to read.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a physics lesson about?",
            answer="A physics lesson is about how things move, push, pull, fall, and bounce in the world.",
        ),
        QAItem(
            question="What does a word card help people do?",
            answer="A word card helps people see a word clearly so they can sort, read, or use it in a display.",
        ),
        QAItem(
            question="Why do people use tape on posters?",
            answer="People use tape to hold paper or cards in place so they do not slide or fall down.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
topic_valid(P, T) :- setting(P), affords(P, T).
compatible(T, P, A) :- topic(T), prop(P), aid(A), helps(A, T), supports(A, theme(P)).
valid_story(P, T, Pp) :- topic_valid(P, T), prop(Pp), compatible(T, Pp, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TOPICS.items():
        lines.append(asp.fact("topic", tid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("theme", pid, p.theme))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for t in sorted(aid.helps):
            lines.append(asp.fact("helps", aid.id, t))
        for t in sorted(aid.supports):
            lines.append(asp.fact("supports", aid.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set()
    for place, topic, prop in valid_combos():
        python_set.add((place, topic, prop))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def explain_rejection(topic: Topic, prop: Prop) -> str:
    return f"(No story: {topic.display} and {prop.label} do not fit a reasonable fix in this world.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TOPICS[params.topic], PROPS[params.prop],
                 params.name, params.gender, params.partner, params.trait)
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
    StoryParams(place="classroom", topic="word", prop="cards", name="Mina", gender="girl", partner="boy", trait="kind"),
    StoryParams(place="library", topic="thematic", prop="poster", name="Eli", gender="boy", partner="girl", trait="curious"),
    StoryParams(place="clubroom", topic="physics", prop="labels", name="Nora", gender="girl", partner="boy", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

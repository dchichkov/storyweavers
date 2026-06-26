#!/usr/bin/env python3
"""
A standalone storyworld for a small mythic school tale about a condiment,
sound effects, and problem solving.

Premise:
A child at school discovers that a beloved condiment has spilled during lunch.
The spill threatens a classroom ritual, so the child uses sound effects and
careful problem solving to turn the mess into a clever fix.

The storyworld keeps the world model small and state-driven:
- physical meters: spill, mess, tidy, brightness, noise
- emotional memes: worry, courage, pride, relief, wonder

The narrative aims for a myth-like feel: ordinary school objects are given
legendary weight, and the solution feels earned through action and invention.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class School:
    place: str = "the school"
    affords: set[str] = field(default_factory=set)


@dataclass
class Condiment:
    id: str
    label: str
    phrase: str
    mess_kind: str
    sound: str
    spill_noun: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    school: School
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
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
        clone = World(self.school)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("spill", 0.0) < THRESHOLD:
            continue
        sig = ("spill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["mess"] = actor.meters.get("mess", 0.0) + 1
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"A sticky trouble spread across the tiles.")
    return out


def _clean_with_tool(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for tool in world.entities.values():
            if tool.kind != "thing" or tool.label == "":
                continue
            if tool.owner != actor.id:
                continue
            if actor.meters.get("mess", 0.0) < THRESHOLD:
                continue
            if not tool.helps_with.intersection({"spill", "mess"}):
                continue
            sig = ("clean", actor.id, tool.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["mess"] = 0.0
            actor.meters["tidy"] = actor.meters.get("tidy", 0.0) + 1
            actor.memes["courage"] = actor.memes.get("courage", 0.0) + 1
            out.append(f"The clever tool answered the trouble.")
    return out


CAUSAL_RULES = [_spill, _clean_with_tool]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_spill(world: World, actor: Entity, condiment: Condiment, tool: Optional[Tool]) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["spill"] = 1.0
    propagate(sim, narrate=False)
    if tool is not None:
        sim.add(Entity(
            id=tool.id,
            kind="thing",
            type="tool",
            label=tool.label,
            phrase=tool.phrase,
            owner=actor.id,
        ))
        sim.get(tool.id).owner = actor.id
        sim.get(actor.id).meters["mess"] = 1.0
        propagate(sim, narrate=False)
    return sim.get(actor.id).meters.get("mess", 0.0) >= THRESHOLD


def hero_intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.memes.get("traits", [])), "curious")
    world.say(f"{hero.pronoun().capitalize()} was a {trait} child who listened closely to every small thing at school.")


def mythic_school(world: World, hero: Entity, mentor: Entity) -> None:
    world.say(
        f"At {world.school.place}, the halls were said to hum with old lessons, "
        f"and the lunchroom was a bright court where small choices became great."
    )
    world.say(
        f"{hero.id} and {mentor.label} walked beneath the buzzing lights as if they were lanterns in a temple."
    )


def condiment_story(world: World, hero: Entity, condiment: Condiment) -> None:
    world.say(
        f"{hero.id} loved the {condiment.label}, because it made ordinary food feel like a feast fit for a king."
    )
    world.say(
        f"Every time the lid tapped, it sounded like {condiment.sound}."
    )


def incident(world: World, hero: Entity, condiment: Condiment) -> None:
    hero.meters["spill"] = 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"Then, with a sudden {condiment.sound}, the {condiment.label} tipped and spilled across the table."
    )
    propagate(world, narrate=True)


def warning(world: World, mentor: Entity, hero: Entity, condiment: Condiment) -> None:
    world.say(
        f"{mentor.label} frowned kindly and said, \"If we rush, the {condiment.label} will only spread farther.\""
    )
    world.say(
        f"{hero.id} looked at the shining spill and felt the first edge of the problem."
    )


def problem_solving(world: World, hero: Entity, condiment: Condiment, tool: Tool) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    world.say(
        f"{hero.id} listened to the little patter of the mess and thought."
    )
    world.say(
        f"\"We need a way to hear where it is and see where it goes,\" {hero.pronoun()} whispered."
    )
    world.say(
        f"So {hero.id} made a plan with {tool.phrase}, and the room heard {tool.sound} like a brave drum."
    )


def resolution(world: World, hero: Entity, tool: Tool, condiment: Condiment, mentor: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"{hero.id} used {tool.label} to gather the last bright streaks of the {condiment.label}."
    )
    world.say(
        f"At last the table shone again, and the old problem lay quiet as a defeated dragon."
    )
    world.say(
        f"{mentor.label} smiled, and {hero.id} stood taller, proud that careful thinking had saved the day."
    )


def tell(school: School, condiment: Condiment, tool: Tool, hero_name: str, hero_type: str, mentor_type: str, trait: str) -> World:
    world = World(school)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        memes={"traits": [trait], "worry": 0.0, "courage": 0.0, "wonder": 0.0, "pride": 0.0, "relief": 0.0},
        meters={"spill": 0.0, "mess": 0.0, "tidy": 0.0},
    ))
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, label="the teacher"))
    tool_ent = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        owner=hero.id,
    ))
    hero_intro(world, hero)
    mythic_school(world, hero, mentor)
    condiment_story(world, hero, condiment)
    world.para()
    incident(world, hero, condiment)
    warning(world, mentor, hero, condiment)
    world.para()
    problem_solving(world, hero, condiment, tool)
    hero.meters["mess"] = 1.0
    propagate(world, narrate=True)
    world.para()
    resolution(world, hero, tool, condiment, mentor)
    world.facts.update(hero=hero, mentor=mentor, condiment=condiment, tool=tool, tool_ent=tool_ent, school=school)
    return world


SCHOOLS = {
    "school": School(place="the school", affords={"lunchroom", "classroom"}),
}

CONDIMENTS = {
    "ketchup": Condiment(
        id="ketchup",
        label="ketchup",
        phrase="a bright bottle of ketchup",
        mess_kind="red",
        sound="splish-splash",
        spill_noun="spill",
        zone={"table"},
        tags={"condiment", "red", "food"},
    ),
    "mustard": Condiment(
        id="mustard",
        label="mustard",
        phrase="a sunny jar of mustard",
        mess_kind="yellow",
        sound="glorp",
        spill_noun="spill",
        zone={"table"},
        tags={"condiment", "food"},
    ),
    "syrup": Condiment(
        id="syrup",
        label="syrup",
        phrase="a dark bottle of syrup",
        mess_kind="sticky",
        sound="glub-glub",
        spill_noun="spill",
        zone={"table"},
        tags={"condiment", "sticky", "food"},
    ),
}

TOOLS = {
    "napkins": Tool(
        id="napkins",
        label="napkins",
        phrase="a neat stack of napkins",
        helps_with={"spill", "mess"},
        sound="swish-swish",
        tags={"clean", "problem_solving"},
    ),
    "spoon": Tool(
        id="spoon",
        label="a spoon",
        phrase="a small spoon for careful scooping",
        helps_with={"spill"},
        sound="tap-tap",
        tags={"clean", "problem_solving"},
    ),
    "tray": Tool(
        id="tray",
        label="a tray",
        phrase="a flat tray that could hold the drifting sauce",
        helps_with={"spill", "mess"},
        sound="clink-clink",
        tags={"clean", "problem_solving"},
    ),
}

TRAITS = ["curious", "brave", "patient", "bright", "thoughtful"]
NAMES = ["Mina", "Leo", "Iris", "Noah", "Zuri", "Eli"]


@dataclass
class StoryParams:
    school: str
    condiment: str
    tool: str
    name: str
    gender: str
    mentor: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for school_id, school in SCHOOLS.items():
        for condiment_id in CONDIMENTS:
            for tool_id in TOOLS:
                combos.append((school_id, condiment_id, tool_id))
    return combos


ASP_RULES = r"""
condiment(C) :- condiment_fact(C).
tool(T) :- tool_fact(T).

problem(C) :- condiment(C), spill_prone(C).
solution(T) :- tool(T), helps(T, spill).

compatible(C, T) :- problem(C), solution(T).

valid_story(S, C, T) :- school(S), condiment(C), tool(T), compatible(C, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCHOOLS:
        lines.append(asp.fact("school", sid))
    for cid, c in CONDIMENTS.items():
        lines.append(asp.fact("condiment_fact", cid))
        lines.append(asp.fact("spill_prone", cid))
        lines.append(asp.fact("sound", cid, c.sound))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_fact", tid))
        for h in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(s, c, t) for s, c, t in valid_combos()}
    clingo_set = set(asp_valid_stories())
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo_set:
        print("  only in python:", sorted(py - clingo_set))
    if clingo_set - py:
        print("  only in clingo:", sorted(clingo_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic school story about a condiment, sound effects, and problem solving.")
    ap.add_argument("--school", choices=SCHOOLS.keys())
    ap.add_argument("--condiment", choices=CONDIMENTS.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["teacher", "librarian"])
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
    school = args.school or rng.choice(list(SCHOOLS.keys()))
    condiment = args.condiment or rng.choice(list(CONDIMENTS.keys()))
    tool = args.tool or rng.choice(list(TOOLS.keys()))
    if condiment == "syrup" and tool == "spoon":
        raise StoryError("(No story: syrup needs a wider cleanup tool than a spoon alone.)")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    mentor = args.mentor or "teacher"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(school=school, condiment=condiment, tool=tool, name=name, gender=gender, mentor=mentor, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth-like school story about a {f["condiment"].label} spill and the sound "{f["condiment"].sound}".',
        f"Tell a child-facing story set at {f['school'].place} where {f['hero'].id} solves a sticky problem with {f['tool'].label}.",
        f"Write a gentle myth of school life in which a condiment spill is answered by sound effects and clever thinking.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    condiment = f["condiment"]
    tool = f["tool"]
    mentor = f["mentor"]
    return [
        QAItem(
            question=f"What happened to the {condiment.label} at school?",
            answer=f"The {condiment.label} tipped over and spilled in the lunchroom.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} used {tool.label} and careful thinking to gather the mess and make the table clean again.",
        ),
        QAItem(
            question=f"Why did the teacher smile at the end?",
            answer=f"The teacher smiled because {hero.id} solved the problem without panicking, and the class got back its calm, shining table.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a condiment?",
            answer="A condiment is a small food topping or sauce, like ketchup or mustard, that people add to make food taste different.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help you imagine a noise, like swish, tap, splash, or glub.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means thinking about a trouble, choosing a plan, and trying a useful fix instead of giving up.",
        ),
    ]


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    school = SCHOOLS[params.school]
    condiment = CONDIMENTS[params.condiment]
    tool = TOOLS[params.tool]
    world = World(school)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"spill": 0.0, "mess": 0.0, "tidy": 0.0},
        memes={"worry": 0.0, "courage": 0.0, "wonder": 0.0, "pride": 0.0, "relief": 0.0, "traits": [params.trait]},
    ))
    mentor = world.add(Entity(id="Mentor", kind="character", type=params.mentor, label="the teacher"))
    world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))

    story = tell(school, condiment, tool, params.name, params.gender, params.mentor, params.trait)
    story.facts.update(hero=story.get(params.name), mentor=story.get("Mentor"), condiment=condiment, tool=tool, school=school)
    return StorySample(
        params=params,
        story=story.render(),
        prompts=generation_prompts(story),
        story_qa=story_qa(story),
        world_qa=world_knowledge_qa(story),
        world=story,
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
    StoryParams(school="school", condiment="ketchup", tool="napkins", name="Mina", gender="girl", mentor="teacher", trait="curious"),
    StoryParams(school="school", condiment="mustard", tool="tray", name="Leo", gender="boy", mentor="teacher", trait="brave"),
    StoryParams(school="school", condiment="syrup", tool="tray", name="Iris", gender="girl", mentor="teacher", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s, c, t in stories:
            print(f"  {s:8} {c:10} {t:10}")
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
            header = f"### {p.name}: {p.condiment} with {p.tool} at {p.school}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/explicit_mend_flashback_comedy.py
=================================================================

A small comedy storyworld about a kid, a broken thing, an explicit
how-to note, and a flashback that reveals how to mend it properly.

Seed words:
- explicit
- mend

Narrative feature:
- Flashback

Style:
- Comedy

The world is intentionally tiny and state-driven:
a child discovers a broken prop before showtime, remembers an earlier lesson,
tries a silly but plausible wrong fix, then uses the explicit instructions to
mend it well. The ending image proves the repaired item works.

The story stays child-facing, concrete, and a little goofy.
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
BROKEN_MIN = 1.0
FIXED_MIN = 1.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    name: str
    stage: str
    clutter: str
    vibe: str


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    broken_bits: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LessonCard:
    id: str
    title: str
    explicit_note: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
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


def _r_mend(world: World) -> list[str]:
    out: list[str] = []
    prop = world.get("prop")
    child = world.get("child")
    if prop.meters["fixed"] >= FIXED_MIN and ("mend", "applied") not in world.fired:
        world.fired.add(("mend", "applied"))
        child.memes["relief"] += 1
        child.memes["pride"] += 1
        out.append("__mend__")
    return out


CAUSAL_RULES = [Rule("mend", "repair", _r_mend)]


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


def _attempt_wrong_fix(world: World, prop: Entity) -> None:
    prop.meters["glued"] += 1
    prop.memes["goopy"] += 1
    world.say(
        f"{prop.label_word.capitalize()} tried a ridiculous fix with sticky tape, "
        f"but it only made the rip look like a surprised banana."
    )


def _flashback(world: World, child: Entity, card: LessonCard, mentor: Entity) -> None:
    child.memes["remembering"] += 1
    world.say(
        f"Then {child.id} stopped and had a flashback: last week, {mentor.id} had "
        f"shown {child.pronoun('object')} an {card.explicit_note} on {card.title}."
    )
    world.say(
        f"The note was so {card.id} that even the cat would have understood it."
    )


def _mend_properly(world: World, child: Entity, prop: Entity, tool: Tool, card: LessonCard) -> None:
    prop.meters["fixed"] += 1
    prop.meters["shiny"] += 1
    child.memes["focus"] += 1
    world.say(
        f"{child.id} followed the {card.explicit_note} and used {tool.phrase}. "
        f"With careful hands, {child.pronoun()} {tool.effect} the {prop.label}."
    )
    propagate(world, narrate=False)
    world.say(
        f"At last, the {prop.label} was no longer droopy or dramatic; it was neat, "
        f"steady, and ready for the show."
    )


def tell(place: Place, prop: Prop, tool: Tool, card: LessonCard,
         child_name: str = "Milo", child_gender: str = "boy",
         mentor_name: str = "Aunt Bea", mentor_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child",
                             traits=["quick", "silly"]))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_gender, role="mentor",
                              traits=["patient", "clear"]))
    prop_ent = world.add(Entity(id="prop", type="prop", label=prop.label))
    world.add(Entity(id="stage", type="place", label=place.name))

    prop_ent.meters["broken"] += 1
    prop_ent.memes["panic"] += 1

    world.say(
        f"On a busy afternoon, {child.id} found the {prop.label} in {place.name}. "
        f"It was supposed to help with the show on {place.stage}, but one side was "
        f"floppy and {prop.broken_bits}."
    )
    world.say(
        f"{child.id} squinted at the mess. {place.vibe.capitalize()}, {prop.use}, "
        f"and now the whole thing looked like it had lost an argument with a mop."
    )

    world.para()
    _attempt_wrong_fix(world, prop_ent)
    _flashback(world, child, card, mentor)

    world.para()
    world.say(
        f"{mentor.id} appeared with a nod and a toolbox. "
        f'"Be explicit," {mentor.id} said. "Mending is easier when the steps are clear."'
    )
    _mend_properly(world, child, prop_ent, tool, card)

    world.para()
    world.say(
        f"When showtime came, {child.id} gave the {prop.label} a proud twirl, and it "
        f"held together without a wobble."
    )
    world.say(
        f"{mentor.id} laughed. " 
        f'"There," {mentor.id} said, "that is what happens when a silly problem meets '
        f'an explicit plan."'
    )

    world.facts.update(
        child=child,
        mentor=mentor,
        prop=prop,
        tool=tool,
        card=card,
        place=place,
        repaired=prop_ent.meters["fixed"] >= FIXED_MIN,
        broken=prop_ent.meters["broken"] >= THRESHOLD,
        wrong_fix=prop_ent.meters["glued"] >= THRESHOLD,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for prop_id, prop in PROPS.items():
            for tool_id, tool in TOOLS.items():
                if prop_id in place_tags(place) and tool_id in prop.tags:
                    combos.append((place_id, prop_id, tool_id))
    return combos


def place_tags(place: Place) -> set[str]:
    return {"busy", "small", "stagey", "comedy"} | {place.id}


PLACES = {
    "backstage": Place(id="backstage", name="the backstage hallway", stage="the curtain stage", clutter="boxes", vibe="Everything echoed like a spoon in a teacup."),
    "garage": Place(id="garage", name="the garage", stage="the cardboard castle stage", clutter="old paint pots", vibe="The light was dusty and everything smelled faintly of crayons."),
    "basement": Place(id="basement", name="the basement playroom", stage="the blanket fort stage", clutter="sock puppets", vibe="The room was dim, but it felt very serious about being silly."),
}

PROPS = {
    "banner": Prop(id="banner", label="banner", phrase="a glittery show banner", broken_bits="one corner had torn loose", use="for the big laugh", tags={"tape", "thread"}),
    "curtain": Prop(id="curtain", label="curtain", phrase="a stage curtain", broken_bits="the hem had come undone", use="to hide the surprise entrance", tags={"tape", "thread"}),
    "mask": Prop(id="mask", label="mask", phrase="a paper mask", broken_bits="the eye hole had split open", use="to look spooky in a funny way", tags={"glue", "string"}),
}

TOOLS = {
    "tape": Tool(id="tape", label="tape", phrase="clear tape", effect="patched"),
    "thread": Tool(id="thread", label="thread", phrase="a needle and thread", effect="stitched"),
    "glue": Tool(id="glue", label="glue", phrase="a glue stick", effect="sealed"),
}


@dataclass
class StoryParams:
    place: str
    prop: str
    tool: str
    child: str
    child_gender: str
    mentor: str
    mentor_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="backstage", prop="banner", tool="tape", child="Milo", child_gender="boy", mentor="Aunt Bea", mentor_gender="girl"),
    StoryParams(place="garage", prop="curtain", tool="thread", child="Nina", child_gender="girl", mentor="Uncle Lou", mentor_gender="boy"),
    StoryParams(place="basement", prop="mask", tool="glue", child="Pip", child_gender="boy", mentor="Mom", mentor_gender="girl"),
]


KNOWLEDGE = {
    "explicit": [("What does explicit mean?",
                  "Explicit means clear, direct, and easy to understand. When instructions are explicit, people do not have to guess.")],
    "mend": [("What does mend mean?",
              "To mend something means to fix it so it can be used again. People mend torn cloth, broken toys, and other little problems.")],
    "flashback": [("What is a flashback in a story?",
                  "A flashback is when the story briefly shows something from before. It helps explain why a character knows what to do.")],
    "tape": [("What does tape do?",
              "Tape sticks things together for a while. It can help mend small tears when used carefully.")],
    "thread": [("What is thread for?",
                "Thread is thin string used for sewing. It can hold cloth together after it is stitched.")],
    "glue": [("What does glue do?",
              "Glue helps paper and light pieces stick together. It is useful for small fixes.")],
    "banner": [("What is a banner?",
                 "A banner is a sign or decoration that can hang up for a party or show.")],
    "curtain": [("What is a curtain?",
                  "A curtain is a hanging piece of cloth that can cover a window or a stage.")],
    "mask": [("What is a mask?",
               "A mask covers part of your face for pretend play, costumes, or a show.")],
}
KNOWLEDGE_ORDER = ["explicit", "mend", "flashback", "tape", "thread", "glue", "banner", "curtain", "mask"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a child where the word "explicit" appears in a helpful instruction and the word "mend" appears when someone fixes a prop.',
        f"Tell a comedy story with a flashback: {f['child'].id} finds a broken {f['prop'].label}, remembers an earlier lesson, and mends it before showtime.",
        f'Write a playful story about a small stage disaster where clear directions help a child mend the problem instead of making it worse.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, mentor, prop, tool, card = f["child"], f["mentor"], f["prop"], f["tool"], f["card"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who found a broken {prop.label}, and {mentor.id}, who helped with a calm, funny fix."),
        ("What went wrong?",
         f"The {prop.label} was broken before showtime. One side had torn loose, so it looked like it might fall apart at the worst possible moment."),
        ("What was the flashback for?",
         f"The flashback reminded {child.id} of the earlier lesson from {mentor.id}. That memory made the explicit instructions feel important right away."),
        ("How did they mend it?",
         f"{child.id} followed the explicit note and used {tool.phrase}. The careful fixing turned the broken {prop.label} into something ready for the stage."),
    ]
    if f["wrong_fix"]:
        qa.append((
            "Why was the first fix silly?",
            f"{child.id} tried sticky tape first, but it was a ridiculous idea for the job. It made the problem look even more comic until the flashback brought a better plan."
        ))
    if f["repaired"]:
        qa.append((
            "How did the story end?",
            f"The {prop.label} held together at showtime, and everyone could laugh instead of panic. The ending shows the mend worked because the prop stayed steady."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["card"].tags) | set(world.facts["tool"].tags) | set(world.facts["prop"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, prop: Prop, tool: Tool) -> str:
    if tool.id not in prop.tags:
        return f"(No story: {tool.label} is not a useful match for mending a {prop.label}.)"
    return f"(No story: the combination does not produce a clear comedy repair.)"


ASP_RULES = r"""
broken(prop) :- prop(prop).
explicit_note(card) :- lesson(card).
mendable(prop, tool) :- prop(prop), tool(tool), needs(prop, tool).
flashback_needed(child) :- broken(prop), explicit_note(card).

repaired(prop) :- broken(prop), mend_tool(tool), fixed_with(prop, tool).
comic_end(prop) :- repaired(prop), showtime(prop).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("needs", pid, next(iter(p.tags))))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for cid in LESSONS:
        lines.append(asp.fact("lesson", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program("#show repaired/1."))
        _ = model
    except Exception as exc:
        print(f"ASP smoke test failed: {exc}")
        return 1
    return 0


def valid_combo(place_id: str, prop_id: str, tool_id: str) -> bool:
    return tool_id in PROPS[prop_id].tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id in PLACES:
        for prop_id, prop in PROPS.items():
            for tool_id in TOOLS:
                if valid_combo(place_id, prop_id, tool_id):
                    combos.append((place_id, prop_id, tool_id))
    return combos


LESSONS = {
    "explicit": LessonCard(id="explicit", title="The Clear Note", explicit_note="explicit steps", tags={"explicit"}),
    "mend": LessonCard(id="mend", title="How to Mend It", explicit_note="explicit mending steps", tags={"mend"}),
}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prop and args.tool and not valid_combo(args.place or "backstage", args.prop, args.tool):
        raise StoryError(explain_rejection(PLACES[args.place or "backstage"], PROPS[args.prop], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.prop is None or c[1] == args.prop)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prop, tool = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["boy", "girl"])
    mentor_gender = args.mentor_gender or rng.choice(["boy", "girl"])
    child = args.child or rng.choice(["Milo", "Nia", "Pip", "Zed", "Luna", "Ollie"])
    mentor = args.mentor or rng.choice(["Aunt Bea", "Uncle Lou", "Mom", "Dad", "Coach Kim"])
    return StoryParams(place=place, prop=prop, tool=tool, child=child, child_gender=child_gender, mentor=mentor, mentor_gender=mentor_gender)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.prop not in PROPS or params.tool not in TOOLS:
        raise StoryError("Invalid params for this world.")
    card = LESSONS["explicit"]
    world = tell(PLACES[params.place], PROPS[params.prop], TOOLS[params.tool], card, params.child, params.child_gender, params.mentor, params.mentor_gender)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with explicit instructions, mend, and a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--mentor")
    ap.add_argument("--mentor-gender", choices=["boy", "girl"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show repaired/1."))
        return
    if args.verify:
        rc = asp_verify()
        if rc != 0:
            sys.exit(rc)
        try:
            sample = generate(CURATED[0])
            _ = sample.story
        except Exception as exc:
            print(f"Story smoke test failed: {exc}")
            sys.exit(1)
        print("OK: ASP smoke test and story generation succeeded.")
        sys.exit(0)
    if args.asp:
        print(f"{len(valid_combos())} valid combos:")
        for combo in valid_combos():
            print("  " + " ".join(combo))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

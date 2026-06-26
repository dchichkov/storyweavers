#!/usr/bin/env python3
"""
storyworlds/worlds/opera_bravery_mystery.py
===========================================

A standalone Storyweavers world for a small opera-house mystery with a brave
young lead.

Premise:
- A child is preparing for an opera performance.
- Something important goes missing backstage.
- The child has to be brave, follow clues, and solve the mystery in time.

This world is intentionally small and constraint-checked: the story is not just
a shuffled paragraph, but a state-driven sequence of setup, tension, clue
search, and resolution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    dark: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    title: str
    clue_word: str
    missing_item: str
    missing_phrase: str
    missing_location: str
    culprit: str
    reveal: str
    fear: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("fear", 0.0) < THRESHOLD:
            continue
        if ("fearline", actor.id) in world.fired:
            continue
        world.fired.add(("fearline", actor.id))
        out.append(f"{actor.id} felt a little shiver when the hall went quiet.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("bravery", 0.0) < THRESHOLD:
            continue
        if ("brave", actor.id) in world.fired:
            continue
        world.fired.add(("brave", actor.id))
        actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1
        out.append(f"Then {actor.id} took a steady breath and kept going.")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("bravery", _r_bravery)]


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
        for s in produced:
            world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small opera-house mystery about bravery.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--tool", choices=sorted(TOOLS))
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


def prize_at_risk(mystery: Mystery, tool: Tool) -> bool:
    return mystery.clue_word in tool.helps_with or mystery.missing_location in tool.covers


def select_tool(mystery: Mystery) -> Optional[Tool]:
    for tool in TOOLS.values():
        if prize_at_risk(mystery, tool):
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if place not in setting.affords:
                continue
            if select_tool(mystery) is None:
                continue
            for tool_id, tool in TOOLS.items():
                if prize_at_risk(mystery, tool):
                    out.append((place, mid, tool_id))
    return out


def explain_rejection(mystery: Mystery, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} cannot help solve the {mystery.title} here. "
        f"The tool needs to fit the clue or the missing-place, otherwise the mystery stays unsolved.)"
    )


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    parent: str
    tool: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Lina", "Tess", "Ivy", "Nora", "Mia", "Aria", "June"]
BOY_NAMES = ["Theo", "Owen", "Noah", "Eli", "Leo", "Finn", "Sam", "Ben"]


SETTINGS = {
    "opera_house": Setting(place="the opera house", dark=False, affords={"missing_mask", "lost_note", "stolen_key"}),
    "backstage": Setting(place="backstage", dark=True, affords={"missing_mask", "lost_note", "stolen_key"}),
    "balcony": Setting(place="the balcony", dark=False, affords={"missing_mask", "lost_note"}),
}

MYSTERIES = {
    "missing_mask": Mystery(
        id="missing_mask",
        title="the missing mask",
        clue_word="mask",
        missing_item="mask",
        missing_phrase="a silver opera mask",
        missing_location="costume trunk",
        culprit="a curious stage kitten",
        reveal="The kitten had rolled the mask under a velvet curtain.",
        fear="the dark backstage hall",
        sound="a tiny clink from behind the curtain",
        tags={"mask", "opera", "curtain"},
    ),
    "lost_note": Mystery(
        id="lost_note",
        title="the lost note",
        clue_word="note",
        missing_item="note",
        missing_phrase="the last high note on the page",
        missing_location="music stand",
        culprit="a windy open window",
        reveal="A gust had blown the page onto a chair near the doorway.",
        fear="the fluttering shadows",
        sound="a paper rustle near the stairs",
        tags={"note", "music", "page"},
    ),
    "stolen_key": Mystery(
        id="stolen_key",
        title="the missing key",
        clue_word="key",
        missing_item="key",
        missing_phrase="the little brass key to the prop cabinet",
        missing_location="prop cabinet",
        culprit="the stage manager who had hidden it for safety",
        reveal="The stage manager had tucked the key in a pocket and forgotten to say so.",
        fear="the locked door",
        sound="a faint jingle from a coat pocket",
        tags={"key", "lock", "cabinet"},
    ),
}

TOOLS = {
    "lantern": Tool(id="lantern", label="a small lantern", phrase="a small lantern", helps_with={"dark"}, covers={"backstage"}),
    "ear": Tool(id="ear", label="a careful ear", phrase="a careful ear", helps_with={"note", "mask", "key"}, covers=set()),
    "glove": Tool(id="glove", label="a soft white glove", phrase="a soft white glove", helps_with={"mask", "key"}, covers={"costume trunk", "prop cabinet"}),
    "curtain_pin": Tool(id="curtain_pin", label="a silver curtain pin", phrase="a silver curtain pin", helps_with={"mask"}, covers={"curtain"}),
}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery and args.tool:
        myst = MYSTERIES[args.mystery]
        tool = TOOLS[args.tool]
        if not prize_at_risk(myst, tool):
            raise StoryError(explain_rejection(myst, tool))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    if args.tool is None:
        # choose tool consistent with mystery
        tools = [tid for tid, t in TOOLS.items() if prize_at_risk(MYSTERIES[mystery], t)]
        tool = rng.choice(sorted(tools))
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent, tool=tool)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", "brave", "curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    item = world.add(Entity(id="Missing", type="thing", label=mystery.missing_item, phrase=mystery.missing_phrase, owner=hero.id, caretaker=parent.id))
    clue = world.add(Entity(id="Clue", type="thing", label="clue", phrase=mystery.clue_word))
    gear = world.add(Entity(id=tool.id, type="thing", label=tool.label, phrase=tool.phrase, owner=hero.id))

    hero.memes["fear"] = 1 if setting.dark else 0
    hero.memes["bravery"] = 0
    world.facts.update(hero=hero, parent=parent, mystery=mystery, tool=gear, setting=setting, item=item)

    world.say(f"{hero.id} was a little {params.gender} who loved the opera house because every hallway seemed to hold a secret.")
    world.say(f"That night, {hero.id} came with {hero.pronoun('possessive')} {parent.label_word} to the opera.")
    world.say(f"Backstage, something was wrong: {mystery.missing_phrase} had gone missing.")

    world.para()
    world.say(f"{hero.id} heard {mystery.sound} and looked toward {mystery.fear}.")
    hero.memes["fear"] += 1
    propagate(world, narrate=True)

    world.say(f"{hero.id} wanted to help, but the hall felt huge and quiet.")
    world.say(f"{hero.pronoun().capitalize()} noticed {tool.label} nearby and picked {tool.phrase} up.")
    hero.memes["bravery"] += 1
    propagate(world, narrate=True)

    world.para()
    if mystery.id == "missing_mask":
        world.say(f"{hero.id} followed the soft click behind the curtain and found a tiny paw print in the dust.")
        world.say(f"{tool.label.capitalize()} helped {hero.id} lift the curtain without getting tangled in it.")
        world.say(mystery.reveal)
    elif mystery.id == "lost_note":
        world.say(f"{hero.id} followed the paper rustle to the stairs and saw one sheet bent at the corner.")
        world.say(f"{tool.label.capitalize()} helped {hero.id} listen closely until the wind stopped rattling the pages.")
        world.say(mystery.reveal)
    else:
        world.say(f"{hero.id} tiptoed past the locked door and listened for the smallest sound.")
        world.say(f"{tool.label.capitalize()} helped {hero.id} think carefully instead of panicking.")
        world.say(mystery.reveal)

    hero.memes["bravery"] += 1
    hero.memes["fear"] = 0
    world.say(f"{hero.id} was brave enough to tell the grown-ups what {hero.pronoun('subject')} had found.")
    world.say(f"At last, the mystery was solved, and the opera could begin.")

    world.facts["solved"] = True
    world.facts["tool"] = tool
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    myst = f["mystery"]
    tool = f["tool"]
    return [
        f'Write a child-friendly mystery story set at the opera house that includes "{myst.clue_word}".',
        f"Tell a brave little story about {hero.id} using {tool.label} to solve {myst.title}.",
        f"Write a gentle opera mystery where someone is missing and the main character keeps going even when the hall feels dark.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    myst = f["mystery"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Where was {hero.id} when the mystery began?",
            answer=f"{hero.id} was at {world.setting.place} with {hero.pronoun('possessive')} {parent.label_word}, backstage near the opera."
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{myst.missing_phrase} was missing, and that made the opera feel uncertain until the clue was found."
        ),
        QAItem(
            question=f"How did {tool.label} help {hero.id}?",
            answer=f"{tool.label.capitalize()} helped {hero.id} stay brave and look carefully for clues instead of turning back."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the mystery solved, the missing {myst.missing_item} found or explained, and the opera ready to begin."
        ),
    ]


WORLD_KNOWLEDGE = {
    "opera": [("What is opera?", "Opera is a kind of stage show where people sing the story instead of only speaking it.")],
    "bravery": [("What is bravery?", "Bravery means doing something hard or scary because it is the right thing to do.")],
    "mystery": [("What is a mystery?", "A mystery is something that seems hidden or strange until clues help explain it.")],
    "clue": [("What is a clue?", "A clue is a small piece of information that helps solve a mystery.")],
    "lantern": [("What does a lantern do?", "A lantern gives off light, so it can help people see in dark places.")],
    "mask": [("What is a mask?", "A mask is something you wear over your face, often for a costume or a show.")],
    "key": [("What does a key do?", "A key unlocks a door, a box, or another locked thing.")],
    "note": [("What is a note in music?", "A note is one sound in a song or melody.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags)
    tags.add("opera")
    tags.add("bravery")
    out: list[QAItem] = []
    for tag in ["opera", "bravery", "mystery", "clue", "lantern", "mask", "key", "note"]:
        if tag in tags or tag in {"opera", "bravery", "mystery", "clue"}:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="opera_house", mystery="missing_mask", name="Mina", gender="girl", parent="mother", tool="glove"),
    StoryParams(place="backstage", mystery="lost_note", name="Theo", gender="boy", parent="father", tool="ear"),
    StoryParams(place="opera_house", mystery="stolen_key", name="Ivy", gender="girl", parent="mother", tool="glove"),
]


ASP_RULES = r"""
prize_at_risk(M, T) :- mystery(M), tool(T), clue_word(M, C), helps_with(T, C).
prize_at_risk(M, T) :- mystery(M), tool(T), missing_location(M, L), covers(T, L).
valid(Place, M, T) :- setting(Place), mystery(M), tool(T), affords(Place, M), prize_at_risk(M, T).
valid_story(Place, M, T, Gender) :- valid(Place, M, T), wears(Gender, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dark:
            lines.append(asp.fact("dark", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_word", mid, m.clue_word))
        lines.append(asp.fact("missing_location", mid, m.missing_location))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for c in sorted(t.helps_with):
            lines.append(asp.fact("helps_with", tid, c))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", tid, c))
    for g, mids in [("girl", ["missing_mask", "lost_note", "stolen_key"]), ("boy", ["missing_mask", "lost_note", "stolen_key"])]:
        for mid in mids:
            lines.append(asp.fact("wears", g, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_gender(mystery: Mystery, gender: str) -> str:
    return f"(No story: this mystery does not fit a {gender} in the chosen configuration.)"


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery and args.tool:
        if not prize_at_risk(MYSTERIES[args.mystery], TOOLS[args.tool]):
            raise StoryError(explain_rejection(MYSTERIES[args.mystery], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent, tool=tool)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, mystery, tool) combos ({len(stories)} with gender):\n")
        for place, mystery, tool in triples:
            genders = sorted(g for (p, m, t, g) in stories if (p, m, t) == (place, mystery, tool))
            print(f"  {place:12} {mystery:14} {tool:10}  [{', '.join(genders)}]")
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
            params = build_story_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def explain_rejection(mystery: Mystery, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} cannot reasonably solve {mystery.title}. "
        f"The clue or hiding place does not match what the tool can help with.)"
    )


if __name__ == "__main__":
    main()

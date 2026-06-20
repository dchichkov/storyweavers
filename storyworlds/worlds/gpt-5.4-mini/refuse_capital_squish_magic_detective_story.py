#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/refuse_capital_squish_magic_detective_story.py
==============================================================================

A small, standalone story world for a magic detective tale.

Premise
-------
A child detective investigates a puzzling scene in a tiny city. A neat clue is
found in the capital, a magical messenger refuses to cooperate at first, and a
spell-squish detail helps solve the case. The story branches by world state, not
by swapping nouns into a frozen paragraph.

The world is designed to include the seed words:
- refuse
- capital
- squish

It also keeps the tone close to a detective story, with a child-friendly magic
twist: a sensible clue trail, a small misunderstanding, a turn, and a final
reveal that changes the world state.
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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    name: str
    capital: str
    mood: str
    has_magic: bool = True
    clue_spot: str = ""
    night_sound: str = ""

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
class Clue:
    id: str
    label: str
    phrase: str
    hidden_in: str
    squishable: bool = False
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
class MagicTool:
    id: str
    label: str
    phrase: str
    sound: str
    help_text: str
    can_refuse: bool = False
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
class Action:
    id: str
    title: str
    first_move: str
    effect: str
    solve_text: str
    power: int
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
    def __init__(self) -> None:
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


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.meters["focus"] < THRESHOLD:
        return out
    if world.get("clue").meters["found"] >= THRESHOLD:
        sig = ("clue",)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["hope"] += 1
            out.append("__clue__")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    if world.get("tool").meters["used"] < THRESHOLD:
        return out
    clue = world.get("clue")
    if clue.meters["found"] >= THRESHOLD and clue.meters["squished"] >= THRESHOLD:
        sig = ("magic",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("detective").memes["confidence"] += 1
            out.append("__magic__")
    return out


CAUSAL_RULES = [
    Rule("clue", "social", _r_clue),
    Rule("magic", "social", _r_magic),
]


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


def smart_reasonable(tool: MagicTool, clue: Clue, place: Place) -> bool:
    return place.has_magic and clue.squishable and tool.can_refuse


def predict(world: World) -> dict:
    sim = world.copy()
    _do_investigate(sim, narrate=False)
    return {
        "found": sim.get("clue").meters["found"] >= THRESHOLD,
        "squished": sim.get("clue").meters["squished"] >= THRESHOLD,
    }


def _do_investigate(world: World, narrate: bool = True) -> None:
    tool = world.get("tool")
    clue = world.get("clue")
    detective = world.get("detective")
    tool.meters["used"] += 1
    clue.meters["found"] += 1
    detective.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, detective: Entity, place: Place) -> None:
    detective.memes["focus"] += 1
    world.say(
        f"On a moonlit evening, {detective.id} walked into {place.name}, the "
        f"{place.capital}, where every shadow seemed to keep a secret."
    )
    world.say(
        f"{detective.id} was a careful little detective. {detective.pronoun().capitalize()} "
        f"liked quiet streets, bright clues, and one magic notebook."
    )


def case_intro(world: World, place: Place, clue: Clue) -> None:
    world.say(
        f"A tiny mystery waited near {place.clue_spot}. Someone had left a clue "
        f"hidden {clue.hidden_in}, and the whole alley smelled like a puzzle."
    )
    world.say(
        f'{world.get("detective").id} whispered, "If I can find the clue, I can '
        f"solve the case."
    )


def refusal_scene(world: World, tool: MagicTool, clue: Clue) -> None:
    world.get("detective").memes["determination"] += 1
    world.say(
        f"Then {tool.label} gave a little sparkle and seemed to refuse to help. "
        f'"{tool.sound}" it seemed to say, as if the magic wanted the detective '
        f'to slow down and look closer.'
    )
    world.say(
        f'{world.get("detective").id} frowned. "You refuse now, but I will '
        f"still find out what happened."
    )


def squish_turn(world: World, clue: Clue) -> None:
    clue.meters["squished"] += 1
    world.say(
        f"{world.get('detective').id} pressed the soft clue into a notebook page "
        f"with a tiny squish. The mark turned plain and neat, like a stamp made by "
        f"moonlight."
    )


def reveal(world: World, action: Action, place: Place) -> None:
    detective = world.get("detective")
    detective.memes["joy"] += 1
    detective.memes["confidence"] += 1
    world.say(
        f"{detective.id} followed the squished mark, took one last careful look, "
        f"and solved the case. {action.solve_text}."
    )
    world.say(
        f"At the end, the {place.capital} felt calm again, and the little magic "
        f"mystery was no longer hiding."
    )


def tell(place: Place, clue: Clue, tool: MagicTool, action: Action,
         detective_name: str = "Mina", detective_gender: str = "girl",
         sidekick_name: str = "Pip", sidekick_gender: str = "boy") -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name, kind="character", type=detective_gender,
        role="detective", traits=["sharp", "kind"],
    ))
    sidekick = world.add(Entity(
        id=sidekick_name, kind="character", type=sidekick_gender,
        role="helper", traits=["small", "brave"],
    ))
    world.add(Entity(id="tool", label=tool.label, role="magic", attrs={"phrase": tool.phrase}))
    world.add(Entity(id="clue", label=clue.label, role="clue", attrs={"phrase": clue.phrase}))
    world.add(Entity(id="place", label=place.name, role="place", attrs={"capital": place.capital}))

    opening(world, detective, place)
    world.para()
    case_intro(world, place, clue)
    refusal_scene(world, tool, clue)
    squish_turn(world, clue)
    world.para()
    reveal(world, action, place)

    world.facts.update(
        detective=detective, sidekick=sidekick, place=place, clue=clue, tool=tool,
        action=action, outcome="solved",
        refusal=tool.can_refuse, squish=clue.meters["squished"] >= THRESHOLD,
    )
    return world


PLACES = {
    "capital": Place("capital", "the capital", "capital city", "busy", True, "the fountain square", "the bells"),
    "harbor": Place("harbor", "the harbor town", "harbor capital", "salt-bright", True, "the dockside lane", "the gulls"),
    "hill": Place("hill", "the hill town", "hill capital", "windy", True, "the old steps", "the chimneys"),
}

CLUES = {
    "ink": Clue("ink", "ink blot", "a round black blot", "inside the torn map", True, {"ink", "squish"}),
    "sticker": Clue("sticker", "star sticker", "a shiny star sticker", "under the lamp", True, {"sticker", "squish"}),
    "ticket": Clue("ticket", "paper ticket", "a folded paper ticket", "inside the book", True, {"paper", "squish"}),
}

TOOLS = {
    "wand": MagicTool("wand", "magic wand", "a magic wand", "brrt", "helped the detective listen to the clues", True, {"magic", "refuse"}),
    "glove": MagicTool("glove", "magic glove", "a magic glove", "fzzt", "could warm the clue without hurting it", True, {"magic", "refuse"}),
    "lens": MagicTool("lens", "magic lens", "a magic lens", "ping", "could show hidden marks", True, {"magic", "refuse"}),
}

ACTIONS = {
    "map": Action("map", "read the map", "look at the map", "the clue had been hidden for a reason", "the clue pointed to the mayor's desk and the missing key", 2, {"map", "capital"}),
    "bell": Action("bell", "follow the bell sound", "listen to the bells", "the sound led straight to the square", "the bells had been warning everyone about the hidden door", 2, {"bell", "capital"}),
    "gate": Action("gate", "check the city gate", "peek at the gate", "the gatekeeper had seen the clue first", "the gatekeeper remembered a visitor with a star sticker", 2, {"gate", "capital"}),
}


@dataclass
@dataclass
class StoryParams:
    place: str
    clue: str
    tool: str
    action: str
    detective_name: str
    detective_gender: str
    sidekick_name: str
    sidekick_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Magic detective storyworld with refuse/capital/squish.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CLUES:
            for t in TOOLS:
                for a in ACTIONS:
                    if smart_reasonable(TOOLS[t], CLUES[c], PLACES[p]):
                        combos.append((p, c, t, a))
    return combos


def explain_rejection(place: Place, clue: Clue, tool: MagicTool) -> str:
    if not place.has_magic:
        return "(No story: this place has no magic at all, so the detective's tool has nothing to do.)"
    if not clue.squishable:
        return "(No story: the clue cannot be squished into a readable mark, so the case never turns.)"
    if not tool.can_refuse:
        return "(No story: the magic tool never refuses, and this world needs a little refusal before the clue can stand out.)"
    return "(No story: this combination is not reasonable.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clue and args.tool:
        if not smart_reasonable(PLACES[args.place], CLUES[args.clue], TOOLS[args.tool]):
            raise StoryError(explain_rejection(PLACES[args.place], CLUES[args.clue], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.tool is None or c[2] == args.tool)
              and (args.action is None or c[3] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, tool, action = rng.choice(sorted(combos))
    return StoryParams(
        place, clue, tool, action,
        args.detective_name or rng.choice(["Mina", "Ivy", "Nora", "Elsie"]),
        args.detective_gender or rng.choice(["girl", "boy"]),
        args.sidekick_name or rng.choice(["Pip", "Jory", "Sam", "Toby"]),
        args.sidekick_gender or rng.choice(["girl", "boy"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly detective story that includes the words "refuse", "capital", and "squish".',
        f"Tell a magic detective tale where {f['detective'].id} visits {f['place'].name} in the {f['place'].capital}, meets a clue, and learns why a tool might refuse at first.",
        f'Write a short mystery where a magic tool says no, a clue gets squished, and the detective solves the case in the capital.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det, place, clue, tool, action = f["detective"], f["place"], f["clue"], f["tool"], f["action"]
    qa = [
        ("Who is the story about?",
         f"It is about {det.id}, a small detective, and the mystery {det.pronoun('subject')} is trying to solve in {place.name}."),
        ("Why did the magic tool refuse at first?",
         f"The magic tool refused because the case needed the detective to slow down and notice the clue first. That refusal was part of the puzzle, not the end of the help."),
        ("What did the detective do with the clue?",
         f"{det.id} squished the clue into a neat mark in the notebook. That made the clue easy to read and helped the next step of the case."),
        ("Where did the story happen?",
         f"It happened in {place.name}, the {place.capital}. The capital setting gave the mystery a busy, important feeling."),
    ]
    if f.get("squish"):
        qa.append((
            "How did squishing the clue help?",
            f"The squished mark showed the detective a clear shape instead of a messy secret. Because of that, {det.id} could follow the clue and solve the case."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the case solved and the capital calm again. The mystery stopped hiding once the clue was understood."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a capital city?",
         "A capital city is the main city of a place. It is often where important leaders or offices are found."),
        ("What does refuse mean?",
         "To refuse means to say no or not agree to do something. A person or even a magical object can refuse."),
        ("What does squish mean?",
         "To squish something is to press it so it becomes flat or soft. A squished mark can be easier to see or can make a funny sound."),
        ("What is a detective?",
         "A detective is someone who looks for clues and solves mysteries."),
        ("What is magic in a story?",
         "Magic is something surprising that can do unusual things, like glow, whisper, or reveal hidden clues."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_possible(P,C,T,A) :- place(P), clue(C), tool(T), action(A),
                                magic_place(P), squishable(C), refuses(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].has_magic:
            lines.append(asp.fact("magic_place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        if CLUES[cid].squishable:
            lines.append(asp.fact("squishable", cid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        if TOOLS[tid].can_refuse:
            lines.append(asp.fact("refuses", tid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_possible/4."))
    return sorted(set(asp.atoms(model, "reasonably_possible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid-combos disagree.")
    else:
        print(f"OK: ASP and Python valid-combos agree ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("capital", "ink", "wand", "map", "Mina", "girl", "Pip", "boy"),
    StoryParams("harbor", "sticker", "glove", "bell", "Ivy", "girl", "Sam", "boy"),
    StoryParams("hill", "ticket", "lens", "gate", "Nora", "girl", "Jory", "boy"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place], CLUES[params.clue], TOOLS[params.tool], ACTIONS[params.action],
        params.detective_name, params.detective_gender, params.sidekick_name, params.sidekick_gender,
    )
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


def build_all_params() -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonably_possible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible combos:")
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in build_all_params()]
    else:
        seen = set()
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
            header = f"### {p.detective_name}: {p.place}, {p.clue}, {p.tool}, {p.action}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/victor_probation_mystery_to_solve_bad_ending.py
===============================================================================

A small whodunit storyworld: Victor is on probation after a bad prank, and a
mystery must be solved before the end of the day. The domain is intentionally
tiny and state-driven: clues are physical, trust changes are emotional, and the
ending is a bad one when Victor makes the wrong move and the real thief slips
away.

This world supports a complete story, three Q&A sets, trace output, JSON, and a
Python/ASP parity check.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
TRUST_LOW = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"   # boy, girl, guard, curator, room, clue, object
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "guard"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class MysterySetting:
    id: str
    place: str
    mood: str
    locked_room: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    clue: str
    guilty: bool = False
    suspicious: int = 0
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    place: str
    points_to: str
    detail: str
    reliable: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    text: str
    success_text: str
    fail_text: str
    sense: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    def __init__(self, setting: MysterySetting) -> None:
        self.setting = setting
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


def _r_doubt(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("accused_wrong") and ("doubt",) not in world.fired:
        world.fired.add(("doubt",))
        for ent in world.characters():
            ent.memes["worry"] += 1
        out.append("__doubt__")
    return out


def _r_trust_drop(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("victor_mistake") and ("trust_drop",) not in world.fired:
        world.fired.add(("trust_drop",))
        world.get("Victor").memes["trust"] -= 2
        out.append("__trust__")
    return out


CAUSAL_RULES = [
    _r_doubt,
    _r_trust_drop,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(mystery: MysterySetting, clue: Clue, action: Action) -> bool:
    return clue.reliable and action.sense >= 2 and mystery.locked_room == "museum"


def sensible_actions() -> list[Action]:
    return [a for a in ACTIONS.values() if a.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for mid, m in SETTINGS.items():
        for cid, c in CLUES.items():
            for aid, a in ACTIONS.items():
                if reasonableness_gate(m, c, a):
                    combos.append((mid, cid, aid))
    return combos


def mystery_pressure(clue: Clue, delay: int) -> int:
    return 1 + delay if clue.reliable else 2 + delay


def solve_success(action: Action, clue: Clue, delay: int) -> bool:
    return action.sense + 1 >= mystery_pressure(clue, delay)


def predict(world: World, clue_id: str, action_id: str, delay: int) -> dict:
    sim = world.copy()
    clue = CLUES[clue_id]
    action = ACTIONS[action_id]
    sim.facts["victor_mistake"] = action.id == "blurt"
    sim.facts["accused_wrong"] = action.id == "blame_clerk"
    propagate(sim, narrate=False)
    return {"solved": solve_success(action, clue, delay), "trust": sim.get("Victor").memes["trust"]}


def setup(world: World, victor: Entity, guardian: Entity, setting: MysterySetting) -> None:
    victor.memes["curiosity"] += 1
    victor.memes["trust"] = 3
    world.say(
        f"On a gray afternoon, Victor was on probation after a bad prank, so he had to "
        f"stay near the museum and help the guard."
    )
    world.say(
        f"The old museum felt hushed and echoey. In the locked room, something had gone missing, "
        f"and everybody wanted the mystery solved."
    )


def introduce_clue(world: World, clue: Clue, victim: Entity) -> None:
    world.say(
        f"At the display case, Victor found {clue.label}. It rested by {clue.place} and pointed toward "
        f"{victim.label_word}."
    )


def question_suspect(world: World, suspect: Suspect) -> None:
    world.say(
        f"Victor eyed {suspect.label}. {suspect.alibi.capitalize()}, but {suspect.clue}."
    )
    suspect.suspicious += 1


def wrong_accusation(world: World, suspect: Suspect) -> None:
    world.facts["accused_wrong"] = True
    world.say(
        f"Victor pointed at {suspect.label} and announced, 'It was {suspect.label}!'"
    )
    if suspect.guilty:
        world.say("But he guessed wrong, and that made the room go even quieter.")


def solve_mystery(world: World, action: Action, suspect: Suspect, clue: Clue, delay: int) -> bool:
    world.facts["victor_mistake"] = action.id == "blurt"
    if action.id == "blame_clerk":
        wrong_accusation(world, suspect)
        return False
    if action.id == "blurt":
        world.say("Victor blurted the clue too loudly before checking the facts.")
        world.get("Victor").memes["trust"] -= 1
        return False
    if solve_success(action, clue, delay):
        world.say(
            f"Victor followed the clue, stayed calm, and used the old key to open the drawer. "
            f"The missing item was found, and the real thief was cornered."
        )
        return True
    world.say(
        f"Victor tried to solve it, but the clue was not enough, and the trail went cold."
    )
    return False


def bad_ending(world: World) -> None:
    world.get("Victor").memes["trust"] -= 3
    world.get("Victor").meters["regret"] += 1
    world.say(
        "A door slammed somewhere down the hall. By the time the guard hurried back, the thief had "
        "slipped out the side entrance."
    )
    world.say(
        "Victor stood under the dusty light and knew he had failed. The museum kept its silence, "
        "and the missing thing was gone for good."
    )


def tell(setting: MysterySetting, clue: Clue, suspect: Suspect, action: Action, delay: int = 1) -> World:
    world = World(setting)
    victor = world.add(Entity(id="Victor", kind="character", type="boy", role="probationer"))
    guard = world.add(Entity(id="Guard", kind="character", type="guard", label="the guard"))
    curator = world.add(Entity(id="Curator", kind="character", type="woman", label="the curator"))
    victim = world.add(Entity(id="Missing", kind="character", type="thing", label="the missing star"))
    world.add(Entity(id="room", type="room", label=setting.locked_room))

    setup(world, victor, guard, setting)
    world.para()
    introduce_clue(world, clue, victim)
    question_suspect(world, suspect)
    solved = solve_mystery(world, action, suspect, clue, delay)
    if not solved:
        world.para()
        bad_ending(world)

    world.facts.update(
        victor=victor,
        guard=guard,
        curator=curator,
        suspect=suspect,
        clue=clue,
        action=action,
        setting=setting,
        solved=solved,
        bad_ending=not solved,
        delay=delay,
        accused_wrong=world.facts.get("accused_wrong", False),
        victor_mistake=world.facts.get("victor_mistake", False),
    )
    propagate(world, narrate=False)
    return world


SETTINGS = {
    "museum": MysterySetting("museum", "the museum", "hushed", "museum", "dusty light"),
    "school": MysterySetting("school", "the school", "quiet", "hallway", "dark lockers"),
}

CLUES = {
    "key": Clue("key", "a tarnished key", "the rug", "the drawer", "It fit the old lock.", tags={"key", "lock"}),
    "note": Clue("note", "a folded note", "the desk", "the curator", "The handwriting matched the sign.", tags={"note"}),
    "thread": Clue("thread", "a blue thread", "the floor", "the cloak", "It matched the thief's coat.", tags={"thread"}),
}

SUSPECTS = {
    "clerk": Suspect("clerk", "the clerk", "woman", "She had been shelving books", "her hands were clean", guilty=False, tags={"clerk"}),
    "janitor": Suspect("janitor", "the janitor", "man", "He was fixing a door", "his shoes were dusty", guilty=False, tags={"janitor"}),
    "visitor": Suspect("visitor", "the visitor", "boy", "He said he was looking around", "he kept staring at the case", guilty=True, tags={"visitor"}),
}

ACTIONS = {
    "careful": Action("careful", "think carefully", "used the clue and solved the mystery", "could not solve the mystery", 3, tags={"solve"}),
    "blurt": Action("blurt", "blurt out the answer", "blurted the answer and was lucky", "blurted the answer and made things worse", 1, tags={"bad"}),
    "blame_clerk": Action("blame_clerk", "blame the clerk", "accused the clerk and found the truth", "accused the clerk and lost the trail", 2, tags={"bad"}),
}



@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    action: str
    delay: int = 1
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

CURATED = [
    ("museum", "key", "visitor", "careful", 1),
    ("museum", "note", "visitor", "blurt", 1),
    ("museum", "thread", "visitor", "blame_clerk", 2),
]



def explain_rejection() -> str:
    return "(No story: this mystery setup is too thin or too odd for a believable whodunit.)"


def explain_action(aid: str) -> str:
    return f"(Refusing action '{aid}': the story needs a more sensible way to solve the mystery.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit for a child that includes the words "Victor" and "probation".',
        f"Tell a mystery story where Victor is on probation, finds {f['clue'].label}, and must decide what to do next.",
        f"Write a bad-ending mystery where Victor guesses badly and the thief gets away.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    suspect: Suspect = f["suspect"]
    clue: Clue = f["clue"]
    action: Action = f["action"]
    items = [
        QAItem("Who is the story about?", "It is about Victor, who is on probation, and a small museum mystery he tries to solve."),
        QAItem("What clue did Victor find?", f"Victor found {clue.label}. It gave him a lead, but the lead still had to be checked carefully."),
    ]
    if f["solved"]:
        items.append(QAItem(
            "How did Victor solve the mystery?",
            f"He used the clue, stayed calm, and opened the locked drawer. That let him catch the real thief and prove who was guilty."
        ))
    else:
        items.append(QAItem(
            "Why was the ending bad?",
            f"Victor made the wrong move with {action.text}, so the trail went cold and the thief got away. The museum stayed sad and the missing thing was never recovered."
        ))
    items.append(QAItem(
        "Was the suspect guilty?",
        "The visitor was the one who seemed guilty, because the signs all pointed that way even though Victor mishandled the case."
    ))
    return items


WORLD_KNOWLEDGE = {
    "probation": [
        QAItem("What is probation?", "Probation is a warning period after a mistake. It means someone must behave carefully and follow rules."),
    ],
    "mystery": [
        QAItem("What is a mystery?", "A mystery is something puzzling that you need clues to solve. The clues help you figure out what really happened."),
    ],
    "clue": [
        QAItem("What is a clue?", "A clue is a small piece of information that helps solve a problem. Good detectives follow clues one by one."),
    ],
    "museum": [
        QAItem("What is a museum?", "A museum is a place where special objects are kept and shown to visitors. People visit to look, learn, and be careful."),
    ],
    "whodunit": [
        QAItem("What is a whodunit story?", "A whodunit is a mystery story where readers ask who did it. The fun is in following the clues to find the answer."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = [WORLD_KNOWLEDGE["probation"][0], WORLD_KNOWLEDGE["mystery"][0], WORLD_KNOWLEDGE["clue"][0], WORLD_KNOWLEDGE["museum"][0], WORLD_KNOWLEDGE["whodunit"][0]]
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, A) :- setting(S), clue(C), action(A), reliable(C), sense(A, N), N >= 2.
solved(A) :- sense(A, N), N >= 3.
bad_end(A) :- sense(A, N), N < 3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.reliable:
            lines.append(asp.fact("reliable", cid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid_combos:")
        print("python only:", sorted(py - cl))
        print("clingo only:", sorted(cl - py))
        rc = 1
    # smoke test: a normal generation must not crash
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: empty story from generate()")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit world with Victor on probation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.action and ACTIONS[args.action].sense < 2:
        raise StoryError(explain_action(args.action))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, clue, action = rng.choice(sorted(combos))
    suspect = args.suspect or "visitor"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, clue, suspect, action, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], SUSPECTS[params.suspect], ACTIONS[params.action], params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    curated = [StoryParams(*c) for c in CURATED]
    if args.all:
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

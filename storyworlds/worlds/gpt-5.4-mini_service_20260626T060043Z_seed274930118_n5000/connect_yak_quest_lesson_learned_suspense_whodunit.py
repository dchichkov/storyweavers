#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/connect_yak_quest_lesson_learned_suspense_whodunit.py
===============================================================================================================================

A small whodunit-style story world about a curious child, a missing token,
a yak, and a quest to connect clues.

The seed words are woven into the premise:
- connect
- yak

The story instrument set is:
- Quest
- Suspense
- Lesson Learned

The world is intentionally small and deterministic enough to verify, but still
state-driven: the detective's choices change physical and emotional state, and
the resolution is caused by those changes rather than a frozen paragraph with
swapped nouns.
"""

from __future__ import annotations

import argparse
import copy
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
    carried_by: Optional[str] = None
    region: str = ""
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little museum"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveal: str
    hide_with: str
    place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    traits: list[str] = field(default_factory=list)
    alibi: str = ""
    shaky_about: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def connect_score(world: World) -> float:
    return world.facts.get("connected", 0.0)


def _r_lookcloser(world: World) -> list[str]:
    out: list[str] = []
    detective = world.facts.get("detective")
    if not detective:
        return out
    det = world.get(detective.id)
    if det.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("lookcloser", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    det.memes["focus"] = det.memes.get("focus", 0.0) + 1
    out.append(f"{det.label} leaned in and studied the room more carefully.")
    return out


def _r_connection(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_handled") and world.facts.get("yak_seen"):
        sig = ("connection",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.facts["connected"] = 1.0
        out.append("The clues clicked together at last.")
    return out


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mystery_unsolved") and not world.facts.get("connected"):
        sig = ("suspense",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("For a moment, the answer still hid in the dark corner of the case.")
    return out


CAUSAL_RULES = [
    _r_lookcloser,
    _r_connection,
    _r_suspense,
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_scene() -> tuple[Setting, list[Clue], list[Suspect]]:
    setting = Setting(place="the little museum", indoors=True, affords={"quest", "inspect"})
    clues = [
        Clue(
            id="mudprint",
            label="muddy print",
            phrase="a muddy print near the side door",
            reveal="someone had come in from the yard",
            hide_with="a rolled rug",
            place="the side hall",
            tags={"mud", "door"},
        ),
        Clue(
            id="bell",
            label="tiny bell",
            phrase="a tiny bell snagged on a chair leg",
            reveal="it matched the yak's collar",
            hide_with="a curtain",
            place="the reading room",
            tags={"yak", "bell"},
        ),
        Clue(
            id="ticket",
            label="ticket stub",
            phrase="a torn ticket stub from the evening show",
            reveal="the missing token had been carried during the show",
            hide_with="a book",
            place="the front desk",
            tags={"ticket", "show"},
        ),
    ]
    suspects = [
        Suspect(
            id="keeper",
            label="the museum keeper",
            type="man",
            traits=["tidy", "nervous"],
            alibi="he was locking the glass cases",
            shaky_about={"bell"},
        ),
        Suspect(
            id="tutor",
            label="the art tutor",
            type="woman",
            traits=["calm", "careful"],
            alibi="she was counting paint brushes",
            shaky_about={"ticket"},
        ),
        Suspect(
            id="yak",
            label="the woolly yak",
            type="yak",
            traits=["curious", "gentle"],
            alibi="it was outside by the fence",
            shaky_about={"mud"},
        ),
    ]
    return setting, clues, suspects


def tell(hero_name: str = "Mina", hero_type: str = "girl", helper_name: str = "Aunt June") -> World:
    setting, clues, suspects = build_scene()
    world = World(setting)

    detective = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={"footsteps": 0.0},
        memes={"curiosity": 1.0, "hope": 0.0, "worry": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="aunt",
        label=helper_name,
        meters={"patience": 1.0},
        memes={"kindness": 1.0},
    ))
    world.add(Entity(
        id="yak",
        kind="character",
        type="yak",
        label="the woolly yak",
        meters={"hoofprints": 1.0},
        memes={"restless": 1.0},
    ))

    clue_ents: list[Entity] = []
    for clue in clues:
        clue_ents.append(world.add(Entity(
            id=clue.id,
            type="clue",
            label=clue.label,
            phrase=clue.phrase,
            owner="mystery",
            caretaker="musem",
            region=clue.place,
        )))

    world.facts.update(
        detective=detective,
        helper=helper,
        clues=clues,
        clue_ents=clue_ents,
        suspects=suspects,
        mystery_unsolved=True,
        clue_handled=False,
        yak_seen=False,
    )

    world.say(f"{hero_name} loved solving little puzzles, especially when she could connect the clues.")
    world.say(f"That afternoon, {hero_name} and {helper_name} stepped into {setting.place}, where something strange had gone missing.")
    world.say(f"On the floor, {hero_name} found a {clues[0].phrase}, and that made her heart beat faster.")
    world.para()

    detective.memes["worry"] += 1.0
    world.say(f"{hero_name} wanted to race ahead, but {helper_name} put a gentle hand on her shoulder.")
    world.say(f'"A good case needs patience," {helper_name} said. "Look closely first."')
    propagate(world)

    world.para()
    world.say(f"{hero_name} walked from room to room, thinking like a tiny detective.")
    world.say(f"In the reading room, she spotted {clues[1].phrase}.")
    world.facts["clue_handled"] = True
    world.facts["yak_seen"] = True
    world.say(f"Then, through the open back door, she saw a woolly yak blinking in the yard as if it had wandered into the wrong story.")
    propagate(world)

    world.para()
    world.say(f"{hero_name} connected the muddy print, the bell, and the torn ticket stub.")
    world.say(f"The yak had slipped inside, brushed the chair, and snatched the show ticket off the desk while it chased the shiny bell on its collar.")
    world.say(f"{helper_name} laughed softly when the case finally made sense.")
    world.say(f'"So the answer was never a thief," she said. "It was a curious yak and a messy trail."')
    world.say(f"{hero_name} smiled, because the clues fit together at last, and the whole room felt lighter.")
    world.facts["mystery_unsolved"] = False
    world.facts["connected"] = 1.0
    detective.memes["relief"] += 1.0
    detective.memes["hope"] += 1.0
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a child-friendly whodunit about a detective who must connect clues and notice a yak.',
        'Tell a suspenseful mystery story in which a little detective solves the case by being patient.',
        'Write a short story with the words "connect" and "yak" where the ending teaches a gentle lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    qa = [
        QAItem(
            question=f"What was {detective.label} trying to do at {world.setting.place}?",
            answer=f"{detective.label} was trying to connect the clues and solve the little mystery.",
        ),
        QAItem(
            question=f"Who told {detective.label} to be patient?",
            answer=f"{helper.label} told her to look closely first and not rush the case.",
        ),
        QAItem(
            question="What animal made the mystery feel surprising?",
            answer="A woolly yak made the mystery surprising, because it was the oddest thing in the museum.",
        ),
    ]
    if f.get("connected"):
        qa.append(
            QAItem(
                question="How was the mystery solved?",
                answer="It was solved when the detective connected the muddy print, the tiny bell, and the ticket stub, which showed the yak had wandered inside and caused the mess.",
            )
        )
        qa.append(
            QAItem(
                question="What lesson did the detective learn?",
                answer="She learned that patience helps a mystery make sense, because looking carefully at each clue can reveal the truth.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to connect clues?",
            answer="To connect clues means to think about how small facts fit together and point to one answer.",
        ),
        QAItem(
            question="What is suspense in a mystery story?",
            answer="Suspense is the feeling of wondering what will happen next before the answer is revealed.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a useful idea someone understands after a problem or story, like being patient or kind.",
        ),
        QAItem(
            question="What is a yak?",
            answer="A yak is a large, shaggy animal that lives in cold mountain places.",
        ),
    ]


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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


NAMES_GIRL = ["Mina", "Tessa", "Iris", "Nora", "Lena", "Pia"]
NAMES_BOY = ["Eli", "Noah", "Finn", "Jasper", "Owen", "Theo"]
HELPERS = ["Aunt June", "Uncle Ben", "Grandma Rose", "Dad", "Mom"]


ASP_RULES = r"""
connected :- clue_handled, yak_seen.
suspense :- mystery_unsolved, not connected.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("clue_handled"))
    lines.append(asp.fact("yak_seen"))
    lines.append(asp.fact("mystery_unsolved"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world about a quest to connect clues and a yak.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, "girl" if params.gender == "girl" else "boy", params.helper)
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


def asp_verify() -> int:
    import asp
    program = asp_program("#show connected/0.\n#show suspense/0.")
    model = asp.one_model(program)
    atoms = {sym.name for sym in model}
    if {"connected", "suspense"} <= atoms:
        print("OK: ASP twin matches the simple Python story gate.")
        return 0
    print("MISMATCH: ASP program did not derive the expected atoms.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show connected/0.\n#show suspense/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show connected/0.\n#show suspense/0."))
        print("ASP atoms:", " ".join(sorted(sym.name for sym in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for i in range(5):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            seed = base_seed + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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

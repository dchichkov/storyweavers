#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cantina_punk_compartment_attic_ladder_repetition_teamwork.py
============================================================================================

A tiny fable-like storyworld about a dusty attic ladder, a little cantina set
in the rafters, and a stubborn compartment that will not open unless two
friends work together and repeat the right steps.

The seed words are folded into the world as concrete, stateful pieces:
- cantina: a toy snack-cantina / tea-cantina in the attic play space
- punk: a scrappy little punk kid who is brave but impatient
- compartment: a stuck storage compartment on the attic ladder

The story instrument is repetition: the kids try the same sensible sequence,
learn the pattern, and succeed together.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: list[str] = field(default_factory=list)
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    setting_word: str = "attic ladder"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Switch:
    id: str
    label: str
    phrase: str
    action: str
    open_gain: float
    patience_gain: float
    teamwork_gain: float
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    place: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    leader: str
    helper: str
    repeated_action: str
    final_action: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.place: Optional[Place] = None
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.place = copy.deepcopy(self.place)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    chamber = world.get("compartment")
    for kid in [e for e in world.entities.values() if e.role in {"leader", "helper"}]:
        if kid.memes["trying"] < THRESHOLD:
            continue
        sig = ("repeat", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        chamber.meters["loose"] += 1
        kid.memes["patience"] += 1
        out.append("__repeat__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    helper = world.get("helper")
    if leader.memes["teamwork"] < THRESHOLD or helper.memes["teamwork"] < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("compartment").meters["open"] += 1
    leader.memes["joy"] += 1
    helper.memes["joy"] += 1
    out.append("__open__")
    return out


CAUSAL_RULES = [Rule("repetition", _r_repetition), Rule("teamwork", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def can_open_with_teamwork(chosen: Switch, place: Place) -> bool:
    return chosen.open_gain >= 1.0 and "attic" in place.label


def predict_world(world: World, switch: Switch) -> dict:
    sim = world.copy()
    do_attempt(sim, narrate=False, switch=switch)
    return {"opened": sim.get("compartment").meters["open"] >= THRESHOLD,
            "loose": sim.get("compartment").meters["loose"]}


def setup(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.place = place
    world.say(
        f"Up in the attic ladder, {a.id} and {b.id} found a tiny cantina with a "
        f"rusty compartment tucked under a dusty step."
    )
    world.say(
        f"{a.id} was a scrappy punk, quick to grin and quicker to try. "
        f"{b.id} was the steady one, the friend who noticed what the hands missed."
    )


def want(world: World, a: Entity) -> None:
    a.memes["wanting"] += 1
    world.say(
        f'"We need the cantina box," {a.id} said. "We need the cantina box."'
    )


def struggle(world: World, a: Entity, b: Entity, switch: Switch) -> None:
    a.memes["trying"] += 1
    b.memes["trying"] += 1
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.say(
        f'They tried the {switch.action}, then tried the {switch.action} again. '
        f'The compartment stayed shut, and the attic ladder gave a little creak.'
    )
    world.say(
        f'"Again," said {b.id}. "Again, but together."'
    )


def do_attempt(world: World, narrate: bool = True, switch: Optional[Switch] = None) -> None:
    leader = world.get("leader")
    helper = world.get("helper")
    comp = world.get("compartment")
    chosen = switch or SWITCHES["twist"]
    leader.memes["trying"] += 1
    helper.memes["trying"] += 1
    if narrate:
        world.say(
            f'{leader.id} tugged the {comp.label} and {helper.id} held the ladder still. '
            f'Then they used the {chosen.action}.'
        )
    comp.meters["loose"] += 1
    propagate(world, narrate=narrate)


def open_with_praise(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"At last the compartment clicked open. Inside sat the cantina supplies: "
        f"two cups, a little tin spoon, and a striped napkin."
    )
    world.say(
        f'{a.id} laughed, and {b.id} laughed too. "We did it together," they said, '
        f"because the same careful steps had worked when the second pair of hands joined in."
    )


def lesson(world: World, a: Entity, b: Entity) -> None:
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    world.say(
        f"They carried the cups down from the attic ladder and shared the cantina drink "
        f"like a little feast."
    )
    world.say(
        f"And the scrappy punk learned this fable's lesson: when one good try is not enough, "
        f"repetition and teamwork can open even a stubborn door."
    )


SWITCHES = {
    "twist": Switch(
        id="twist",
        label="turning the knob",
        phrase="turning the knob",
        action="turning the knob",
        open_gain=1.0,
        patience_gain=1.0,
        teamwork_gain=1.0,
    ),
    "pull": Switch(
        id="pull",
        label="pulling together",
        phrase="pulling together",
        action="pulling together",
        open_gain=1.0,
        patience_gain=1.0,
        teamwork_gain=1.0,
    ),
}

PLACES = {
    "attic_ladder": Place(id="attic_ladder", label="attic ladder"),
}

NAMES = ["Milo", "Nia", "Pip", "Tess", "Rae", "Jude", "Luna", "Beck"]
TRAITS = ["scrappy", "curious", "bold", "gentle", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for kid1 in NAMES:
            for kid2 in NAMES:
                if kid1 == kid2:
                    continue
                for action in SWITCHES:
                    combos.append((place, kid1, action))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen attic-ladder setup does not support a sensible teamwork turn.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: cantina, punk, compartment, attic ladder, repetition, teamwork."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--kid1")
    ap.add_argument("--kid1-gender", choices=["girl", "boy"])
    ap.add_argument("--kid2")
    ap.add_argument("--kid2-gender", choices=["girl", "boy"])
    ap.add_argument("--leader")
    ap.add_argument("--helper")
    ap.add_argument("--repeated-action", choices=SWITCHES)
    ap.add_argument("--final-action", choices=SWITCHES)
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
    place = args.place or "attic_ladder"
    kid1 = args.kid1 or rng.choice(NAMES)
    kid2 = args.kid2 or rng.choice([n for n in NAMES if n != kid1])
    kid1_gender = args.kid1_gender or rng.choice(["girl", "boy"])
    kid2_gender = args.kid2_gender or rng.choice(["girl", "boy"])
    leader = args.leader or kid1
    helper = args.helper or kid2
    repeated_action = args.repeated_action or rng.choice(list(SWITCHES))
    final_action = args.final_action or repeated_action
    if leader == helper:
        raise StoryError("leader and helper must be different children")
    return StoryParams(
        place=place,
        kid1=kid1,
        kid1_gender=kid1_gender,
        kid2=kid2,
        kid2_gender=kid2_gender,
        leader=leader,
        helper=helper,
        repeated_action=repeated_action,
        final_action=final_action,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fable-style story that includes the words "cantina", "punk", and "compartment".',
        f"Tell a story on an attic ladder where {f['leader']} and {f['helper']} must repeat a task and work together.",
        "Write a short moral tale about patience, repetition, and teamwork in a dusty little attic.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Who are the story's children?",
         f"The story follows {f['leader']} and {f['helper']}, two children in the attic ladder play space."),
        ("What was stuck?",
         "A compartment on the attic ladder was stuck shut at first, so the children had to keep trying."),
        ("How did they solve the problem?",
         "They repeated the same careful steps and worked together. When both children helped at once, the compartment finally clicked open."),
        ("What did they find inside?",
         "They found the cantina supplies inside, which turned the hard task into a small shared reward."),
        ("What lesson does the story teach?",
         "It teaches that repetition and teamwork can do what one impatient try cannot. A steady second try can be stronger when a friend helps."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a cantina?",
         "A cantina is a little place where food and drink are served. In this story, it is a tiny snack corner in the attic play space."),
        ("What does punk mean here?",
         "Punk means scrappy and bold. It describes the kid who is brave, loud, and quick to try again."),
        ("What is a compartment?",
         "A compartment is a small enclosed space or box with a lid or door. It can hold things neatly inside."),
        ("What is teamwork?",
         "Teamwork is when people help each other to finish a job. Together they can do things that are hard alone."),
    ]


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
        if e.tags:
            bits.append(f"tags={e.tags}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    leader = world.add(Entity(id=params.leader, kind="character", type=params.kid1_gender, role="leader"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.kid2_gender, role="helper"))
    comp = world.add(Entity(id="compartment", type="thing", label="compartment", tags=["compartment"]))
    cantina = world.add(Entity(id="cantina", type="thing", label="cantina", tags=["cantina"]))
    world.facts.update(leader=leader.id, helper=helper.id, place=place.label, cantina=cantina.label)
    switch = SWITCHES[params.repeated_action]

    setup(world, leader, helper, place)
    world.para()
    want(world, leader)
    struggle(world, leader, helper, switch)
    do_attempt(world, narrate=True, switch=switch)
    world.para()
    open_with_praise(world, leader, helper)
    lesson(world, leader, helper)

    world.facts.update(
        opened=comp.meters["open"] >= THRESHOLD,
        repeated_action=switch.id,
        final_action=params.final_action,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.repeated_action not in SWITCHES or params.final_action not in SWITCHES:
        raise StoryError("invalid parameters for this storyworld")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


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
    StoryParams(place="attic_ladder", kid1="Milo", kid1_gender="boy", kid2="Nia", kid2_gender="girl", leader="Milo", helper="Nia", repeated_action="twist", final_action="twist"),
    StoryParams(place="attic_ladder", kid1="Pip", kid1_gender="boy", kid2="Tess", kid2_gender="girl", leader="Tess", helper="Pip", repeated_action="pull", final_action="pull"),
]


ASP_RULES = r"""
leader(L) :- role(L, leader).
helper(H) :- role(H, helper).
repeated(R) :- action(R).
teamwork :- leader(_), helper(_).
opened :- repeated(_), teamwork.
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "attic_ladder")]
    for rid in SWITCHES:
        lines.append(asp.fact("action", rid))
    lines.append(asp.fact("role", "leader"))
    lines.append(asp.fact("role", "helper"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show opened/0."))
    ok = any(sym.name == "opened" for sym in model)
    if not ok:
        print("MISMATCH: ASP did not derive opened.")
        return 1
    sample = generate(CURATED[0])
    if not sample.story or "cantina" not in sample.story:
        print("MISMATCH: normal generation failed.")
        return 1
    print("OK: ASP twin and normal generation smoke test passed.")
    return 0


def build_cli_sample(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show opened/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode: this simple world expects teamwork to open the compartment.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

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

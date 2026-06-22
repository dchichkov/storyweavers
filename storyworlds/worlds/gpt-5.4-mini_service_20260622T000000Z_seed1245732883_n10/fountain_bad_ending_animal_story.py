#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T000000Z_seed1245732883_n10/fountain_bad_ending_animal_story.py
===============================================================================================================

A small animal-story world about a tempting fountain, a warning, and a bad ending.

Premise:
- A young animal wants to play with a town fountain.
- Another animal warns that a risky choice will hurt the fountain.
- If the choice goes forward, the fountain gets damaged and the ending is sad.

The domain keeps the story child-facing and concrete, with typed entities,
physical meters, emotional memes, a causal rule engine, QA generation,
and an inline ASP twin for the reasonableness gate.
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
BRAVERY_INIT = 5.0
SCARED_TRAITS = {"careful", "kind", "quiet", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    breakable: bool = False
    splashes: bool = False
    helpful: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "female"}
        male = {"boy", "father", "dad", "man", "male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class AnimalKind:
    id: str
    noun: str
    sound: str
    habitat: str
    trait: str
    pronoun_type: str


@dataclass
class FountainKind:
    id: str
    label: str
    phrase: str
    sparkle: str
    broken_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RiskyAction:
    id: str
    verb: str
    tool_label: str
    tool_phrase: str
    risk: str
    damage: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["hurt"] >= THRESHOLD:
            sig = ("hurt", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["sad"] += 1
            out.append("__hurt__")
    fountain = world.entities.get("fountain")
    if fountain and fountain.meters["broken"] >= THRESHOLD:
        sig = ("broken", fountain.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__broken__")
    return out


CAUSAL_RULES = [Rule("damage", "physical", _r_damage)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combo(action: RiskyAction, fountain: FountainKind) -> bool:
    return action.id in ACTIONS and fountain.id in FOUNTAINS and fountain.id == "fountain" and action.id in {"stone", "stick"}


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for a in ACTIONS:
        for f in FOUNTAINS:
            if valid_combo(ACTIONS[a], FOUNTAINS[f]):
                out.append((a, f))
    return out


def reasonableness_check(action: RiskyAction, fountain: FountainKind) -> bool:
    return valid_combo(action, fountain) and fountain.id == "fountain"


def fire_severity(action: RiskyAction, delay: int) -> int:
    return 1 + delay + (1 if action.id == "stone" else 0)


def is_contained(response: Response, action: RiskyAction, delay: int) -> bool:
    return response.power >= fire_severity(action, delay)


def predict_damage(world: World, action_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get("instigator"), ACTIONS[action_id], narrate=False)
    return {
        "hurt": sim.get("instigator").meters["hurt"],
        "broken": sim.get("fountain").meters["broken"],
    }


def _do_action(world: World, actor: Entity, action: RiskyAction, narrate: bool = True) -> None:
    actor.meters["mischief"] += 1
    actor.meters["hurt"] += 1
    fountain = world.get("fountain")
    fountain.meters["broken"] += 1
    fountain.meters["splash"] += 1
    actor.memes["fear"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity, fountain: Entity, kind: FountainKind) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright morning, {a.id} and {b.id} padded through the garden path "
        f"to the town fountain. {kind.phrase}"
    )
    world.say(
        f"{a.id} loved the cool water. {b.id} loved the little silver sparkles "
        f"as they danced in the sun."
    )


def tempt(world: World, a: Entity, action: RiskyAction) -> None:
    a.memes["bravery"] += 1
    world.say(
        f'{a.id} grinned and said, "{action.verb.capitalize()} the fountain! '
        f'I know a game!"'
    )
    world.say(f"The idea felt exciting for one quick moment.")


def warn(world: World, b: Entity, a: Entity, action: RiskyAction, fountain: FountainKind) -> None:
    pred = predict_damage(world, action.id)
    b.memes["care"] += 1
    world.facts["predicted_broken"] = pred["broken"]
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, no. '
        f"{action.risk}. {fountain.label_word if hasattr(fountain, 'label_word') else fountain.label} is not a toy."
    )


def defy(world: World, a: Entity, action: RiskyAction) -> None:
    a.memes["defiance"] += 1
    world.say(f'But {a.id} did not listen. {a.id} ran closer with a little {action.tool_label}.')


def back_down(world: World, a: Entity, b: Entity, safe: Response, fountain: FountainKind) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} looked at {b.id}, thought about the warning, and gave up the idea."
    )
    world.say(
        f"Instead, they used {safe.text} and sat by the fountain while the water stayed shining and safe."
    )


def break_fountain(world: World, a: Entity, action: RiskyAction, fountain: Entity) -> None:
    _do_action(world, a, action)
    world.say(
        f"{action.tool_phrase} hit the fountain with a hard crack. The water "
        f"spurted crookedly, and a small stone chip bounced into the grass."
    )


def alarm(world: World, b: Entity, a: Entity, fountain: FountainKind) -> None:
    world.say(f'"{a.id}! Stop!" {b.id} cried. "The {fountain.label} is breaking!"')


def rescue(world: World, parent: Entity, response: Response, fountain: Entity, action: RiskyAction) -> None:
    fountain.meters["broken"] = 0.0
    body = response.text.replace("{action}", action.id)
    world.say(f"{parent.label_word.capitalize()} hurried over and {body}.")
    world.say("The fountain still dripped, but it would need a grown-up to fix it.")


def bad_ending(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    a.memes["sad"] += 1
    b.memes["sad"] += 1
    world.say(
        f"{parent.label_word.capitalize()} knelt down with a worried face. "
        f'"Now the fountain will have to be repaired," {parent.pronoun()} said.'
    )
    world.say(
        f"The two little animals sat very quietly on the grass. The pretty fountain "
        f"was no longer singing, only dripping sadly into a cracked bowl."
    )
    world.say(
        "They went home without another game, and the garden felt much less bright."
    )


ANIMALS = {
    "rabbit": AnimalKind("rabbit", "rabbit", "thump", "burrow", "quick", "she"),
    "fox": AnimalKind("fox", "fox", "yip", "den", "curious", "he"),
    "squirrel": AnimalKind("squirrel", "squirrel", "chitter", "tree", "busy", "they"),
    "duck": AnimalKind("duck", "duck", "quack", "pond", "playful", "she"),
}

FOUNTAINS = {
    "fountain": FountainKind(
        id="fountain",
        label="fountain",
        phrase="The fountain stood in the middle of the garden, ringed by daisies and shining tiles.",
        sparkle="silver sparkles",
        broken_phrase="a cracked bowl",
        tags={"fountain", "water"},
    )
}

ACTIONS = {
    "stone": RiskyAction(
        id="stone",
        verb="throw stones at",
        tool_label="stone",
        tool_phrase="A little stone",
        risk="Stones can chip the bowl and break the water stream",
        damage="chip",
        tags={"stone", "hurt"},
    ),
    "stick": RiskyAction(
        id="stick",
        verb="poke",
        tool_label="stick",
        tool_phrase="A thin stick",
        risk="Sticks can scratch the fountain and make the water spill crookedly",
        damage="scratch",
        tags={"stick", "hurt"},
    ),
}

RESPONSES = {
    "call_grownup": Response(
        id="call_grownup",
        sense=3,
        power=4,
        text="called the gardener right away and asked for help fixing the fountain",
        fail="called the gardener, but the damage had already gone too far",
        tags={"grownup", "help"},
    ),
    "cover_pipe": Response(
        id="cover_pipe",
        sense=2,
        power=2,
        text="covered the broken pipe with a cloth and kept the water from spraying too high",
        fail="tried to cover the pipe, but the water kept splashing everywhere",
        tags={"help"},
    ),
    "wait": Response(
        id="wait",
        sense=1,
        power=1,
        text="waited and hoped the fountain would fix itself",
        fail="waited, but nothing got better",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Mina", "Ruby", "Luna", "Pippa", "Nina", "Tilly"]
BOY_NAMES = ["Pip", "Benny", "Ollie", "Theo", "Toby", "Milo"]
TRAITS = ["careful", "kind", "quiet", "thoughtful", "brave"]

CURATED = [
    StoryParams(
        instigator="Mina",
        instigator_gender="girl",
        cautioner="Pip",
        cautioner_gender="boy",
        parent="mother",
        action="stone",
        response="call_grownup",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        instigator="Ollie",
        instigator_gender="boy",
        cautioner="Ruby",
        cautioner_gender="girl",
        parent="father",
        action="stick",
        response="cover_pipe",
        trait="kind",
        delay=1,
    ),
]


@dataclass
class StoryParams:
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    action: str
    response: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: a fountain, a warning, and a bad ending.")
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--cautioner")
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("That response is too weak for this story.")
    action = args.action or rng.choice(list(ACTIONS))
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    instigator_gender = rng.choice(["girl", "boy"])
    cautioner_gender = "boy" if instigator_gender == "girl" else "girl"
    instigator = args.name or rng.choice(GIRL_NAMES if instigator_gender == "girl" else BOY_NAMES)
    cautioner = args.cautioner or rng.choice([n for n in (BOY_NAMES if cautioner_gender == "boy" else GIRL_NAMES) if n != instigator])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        action=action,
        response=response,
        trait=trait,
        delay=rng.randint(0, 1),
    )


def tell(params: StoryParams) -> World:
    world = World()
    a = world.add(Entity(id=params.instigator, kind="character", type=params.instigator_gender, role="instigator", traits=["young", "bold"]))
    b = world.add(Entity(id=params.cautioner, kind="character", type=params.cautioner_gender, role="cautioner", traits=[params.trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label=f"the {params.parent}"))
    fountain = world.add(Entity(id="fountain", kind="thing", type="fountain", label="fountain", breakable=True))
    action = ACTIONS[params.action]
    response = RESPONSES[params.response]
    kind = FOUNTAINS["fountain"]

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["care"] = 1.0 if params.trait in SCARED_TRAITS else 0.5
    world.facts.update(action=action, response=response, fountain=kind, parent=parent)

    setup(world, a, b, fountain, kind)
    world.para()
    tempt(world, a, action)
    warn(world, b, a, action, kind)
    world.para()
    if params.trait in SCARED_TRAITS and params.action == "stick":
        back_down(world, a, b, response, kind)
        outcome = "bad"
    else:
        defy(world, a, action)
        world.para()
        break_fountain(world, a, action, fountain)
        alarm(world, b, a, kind)
        bad = True
        if is_contained(response, action, params.delay):
            rescue(world, parent, response, fountain, action)
        bad_ending(world, parent, a, b)
        outcome = "bad"
    world.facts.update(instigator=a, cautioner=b, parent=parent, fountain=fountain, outcome=outcome)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, action = f["instigator"], f["cautioner"], f["action"]
    return [
        f'Write an animal story for a small child that includes a fountain and a warning about {action.tool_label}s.',
        f"Tell a sad little animal story where {a.id} ignores {b.id}'s warning near a fountain and the ending is bad.",
        f'Write a story with a fountain, two young animals, and a bad ending after one animal breaks something by mistake.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent, action = f["instigator"], f["cautioner"], f["parent"], f["action"]
    qa = [
        QAItem(
            question=f"What did {a.id} want to do near the fountain?",
            answer=f"{a.id} wanted to {action.verb} the fountain. It seemed exciting, but it was risky and could hurt the fountain.",
        ),
        QAItem(
            question=f"Why did {b.id} warn {a.id}?",
            answer=f"{b.id} warned {a.id} because {action.risk.lower()}. The warning was meant to keep the fountain safe and stop the trouble before it started.",
        ),
        QAItem(
            question=f"What happened to the fountain at the end?",
            answer="The fountain was damaged and ended up dripping sadly instead of sparkling. The story ends badly because the animals did not choose the safe way.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a fountain?",
            answer="A fountain is a place where water shoots or flows up and then falls back down. People and animals often like to watch fountains sparkle.",
        ),
        QAItem(
            question="Why can stones be dangerous near a fountain?",
            answer="Stones can chip the fountain or break parts of it. A hard throw can turn a pretty fountain into something cracked and broken.",
        ),
        QAItem(
            question="What should you do when a friend says an idea is unsafe?",
            answer="You should stop and listen carefully. It is safer to choose a new game than to keep doing something that could cause damage.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id}: meters={meters} memes={memes} role={e.role} type={e.type}")
    return "\n".join(out)


ASP_RULES = r"""
valid(action(A), fountain(F)) :- action(A), fountain(F), risky(A), F = fountain.
bad_end :- chosen_action(A), bad(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("fountain", "fountain"))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("risky", aid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show response/1."))
    return sorted(r for (r,) in asp.atoms(model, "response"))


def asp_verify() -> int:
    rc = 0
    if set(valid_combos()) == {("stone", "fountain"), ("stick", "fountain")}:
        print("OK: python gate is populated.")
    else:
        rc = 1
        print("MISMATCH: python gate unexpected.")
    sample = generate(resolve_params(argparse.Namespace(action=None, response=None, parent=None, name=None, cautioner=None), random.Random(7)))
    if not sample.story:
        rc = 1
        print("MISMATCH: generation failed.")
    else:
        print("OK: generation smoke test succeeded.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.action not in ACTIONS:
        raise StoryError("Unknown action.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if RESPONSES[params.response].sense < 2:
        raise StoryError("That response is too weak for a story.")
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
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses:", ", ".join(sorted(RESPONSES)))
        print("compatible combos:", valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

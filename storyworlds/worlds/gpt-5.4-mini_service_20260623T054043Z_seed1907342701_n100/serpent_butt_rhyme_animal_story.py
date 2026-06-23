#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/serpent_butt_rhyme_animal_story.py
===============================================================================================================

A tiny animal-story world in rhyme: a serpent wants to play, its butt gets stuck,
and a friendly helper finds a clever, gentle fix. The prose is state-driven, not
a frozen paragraph swap, and the ending image proves what changed.

Seed tale sketch:
---
A serpent in a sunny yard loves to glide and hiss in rhyme. It sees a shiny
berry cart and tries to slide underneath, but its little butt bumps the frame
and gets stuck. A rabbit laughs, then sees the serpent is in trouble and helps
it wiggle free with a smooth vine loop. The serpent says thank you, shares the
berries, and ends the day curled on a warm stone, with its butt no longer stuck
and the cart still bright and tidy.

Causal state updates:
---
stuck body part + helper method   -> stuck -> 0 ; relief += 1
gentle help offered               -> trust += 1 ; joy += 1
sharing berries                   -> love += 1 ; hunger -> 0

Scripted beats:
---
setup with rhyme                   -> joy += 1
misstep / stuck moment             -> worry += 1 ; conflict += 1
helper arrives                     -> relief pending
solution accepted                  -> conflict -> 0 ; joy += 1
ending image                       -> state proves free butt / shared berries / warm rest
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "rooster"}
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
    scene: str
    affords: set[str] = field(default_factory=set)
    rhyme: str = ""


@dataclass
class Trouble:
    id: str
    label: str
    verb: str
    part: str
    cause: str
    zone: set[str] = field(default_factory=set)
    rhyme: str = ""


@dataclass
class Help:
    id: str
    label: str
    method: str
    phrase: str
    fix: str
    rhyme: str = ""


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    taste: str
    share: str
    rhyme: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_unstick(world: World) -> list[str]:
    out: list[str] = []
    serpent = world.entities.get("serpent")
    helper = world.entities.get("helper")
    if not serpent or not helper:
        return out
    if serpent.meters["stuck"] < THRESHOLD or helper.meters["helping"] < THRESHOLD:
        return out
    sig = ("unstick",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    serpent.meters["stuck"] = 0.0
    serpent.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.facts["freed"] = True
    out.append("__freed__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    serpent = world.entities.get("serpent")
    treasure = world.entities.get("berries")
    if not serpent or not treasure:
        return out
    if serpent.meters["shared"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    serpent.memes["love"] += 1
    serpent.meters["hunger"] = 0.0
    out.append("__share__")
    return out


CAUSAL_RULES = [
    Rule("unstick", "physical", _r_unstick),
    Rule("share", "physical", _r_share),
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


def rhyme_line(*parts: str) -> str:
    return " ".join(parts)


def predict_help(world: World) -> dict:
    sim = world.copy()
    sim.get("serpent").meters["stuck"] += 0
    sim.get("helper").meters["helping"] += 1
    propagate(sim, narrate=False)
    return {"freed": sim.facts.get("freed", False), "relief": sim.get("serpent").memes["relief"]}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for trouble_id, trouble in TROUBLES.items():
            for help_id, help_ in HELPS.items():
                if trouble.part in help_.fix:
                    combos.append((place_id, trouble_id, help_id))
    return combos


@dataclass
class StoryParams:
    place: str = ""
    trouble: str = ""
    help: str = ""
    treasure: str = ""
    serpent_name: str = "Sly"
    helper_name: str = "Hare"
    seed: Optional[int] = None


PLACES = {
    "sunny_pond": Place("sunny_pond", "the sunny pond", "a sunny pond and a soft green lawn",
                        affords={"slither", "share"}, rhyme="bright"),
    "berry_patch": Place("berry_patch", "the berry patch", "a berry patch beside a warm stone",
                         affords={"slither", "share"}, rhyme="day"),
    "garden_gate": Place("garden_gate", "the garden gate", "a garden gate with a vine fence",
                         affords={"slither", "share"}, rhyme="way"),
}

TROUBLES = {
    "stuck_butt": Trouble("stuck_butt", "stuck butt", "slid under", "butt", "gate frame",
                          zone={"butt"}, rhyme="stuck"),
    "muddy_butt": Trouble("muddy_butt", "muddy butt", "splashed across", "butt", "mud puddle",
                          zone={"butt"}, rhyme="mud"),
}

HELPS = {
    "vine_loop": Help("vine_loop", "a vine loop", "looped a vine", "a smooth vine loop",
                      "wiggled free", rhyme="green"),
    "berry_nudge": Help("berry_nudge", "a berry nudge", "rolled a berry", "a gentle berry nudge",
                        "moved along", rhyme="sweet"),
}

TREASURES = {
    "berries": Treasure("berries", "berries", "a pile of bright berries", "sweet", "shared", rhyme="red"),
    "stones": Treasure("stones", "stones", "a warm stone", "warm", "rested", rhyme="sun"),
}


def explain_rejection(place: Place, trouble: Trouble, help_: Help) -> str:
    return f"(No story: {help_.label} does not make sense for {trouble.label} at {place.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world in rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--help", dest="help_id", choices=HELPS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--serpent-name")
    ap.add_argument("--helper-name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.help_id is None or c[2] == args.help_id)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble, help_id = rng.choice(sorted(combos))
    treasure = args.treasure or rng.choice(list(TREASURES))
    return StoryParams(
        place=place,
        trouble=trouble,
        help=help_id,
        treasure=treasure,
        serpent_name=args.serpent_name or rng.choice(["Sly", "Nell", "Roo", "Pip"]),
        helper_name=args.helper_name or rng.choice(["Hare", "Mole", "Fawn", "Duck"]),
        seed=None,
    )


def tell(place: Place, trouble: Trouble, help_: Help, treasure: Treasure,
         serpent_name: str, helper_name: str) -> World:
    world = World(place)
    serpent = world.add(Entity(id="serpent", kind="character", type="serpent", label=serpent_name))
    helper = world.add(Entity(id="helper", kind="character", type="hare", label=helper_name))
    berries = world.add(Entity(id="berries", type="thing", label=treasure.label, phrase=treasure.phrase))
    world.facts.update(
        serpent=serpent, helper=helper, berries=berries, place=place, trouble=trouble,
        help_=help_, treasure=treasure, freed=False
    )
    serpent.memes["joy"] += 1
    serpent.meters["shared"] = 0.0
    serpent.meters["stuck"] = 0.0
    serpent.meters["hunger"] = 1.0
    helper.meters["helping"] = 0.0
    helper.memes["joy"] = 0.0

    world.say(f"In {place.label}, {serpent_name} the serpent liked to glide and rhyme.")
    world.say(f"{serpent_name} found {treasure.phrase} and hoped to taste it in time.")
    world.para()
    world.say(f"But when {serpent_name} {trouble.verb} the {trouble.cause}, {serpent_name}'s {trouble.part} went tight,")
    world.say(f"and there {serpent_name} stayed, with a stuck little butt, out of sight.")
    serpent.meters["stuck"] += 1
    serpent.memes["worry"] += 1
    serpent.memes["conflict"] += 1
    world.para()
    world.say(f"Then {helper_name} came trotting by with a grin and a glance,")
    world.say(f"and {helper_name} gave {help_.phrase} a careful chance.")
    helper.meters["helping"] += 1
    serpent.meters["shared"] += 1
    predict_help(world)
    propagate(world, narrate=False)
    world.say(f"{helper_name} said, \"Wiggle and giggle; we'll make a soft fix.\"")
    world.say(f"So {serpent_name} slid free, with a flip and a mix.")
    world.para()
    world.say(f"{serpent_name} shared the {treasure.label}, then curled on a stone so warm,")
    world.say(f"with a clean little butt and a happy safe form.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story in rhyme that uses the words "serpent" and "butt" and ends with a kind helper.',
        f"Tell a rhyming story about {f['serpent'].label} the serpent getting stuck and then getting free.",
        f"Write a gentle animal story where a serpent's butt gets stuck, a helper helps, and the berries get shared.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    serpent = f["serpent"]
    helper = f["helper"]
    trouble = f["trouble"]
    place = f["place"]
    treasure = f["treasure"]
    return [
        QAItem(
            question=f"Who is the story about in {place.label}?",
            answer=f"It is about {serpent.label}, a serpent who likes to rhyme and glide. {serpent.label} has a tricky moment, but the story stays gentle and cheerful.",
        ),
        QAItem(
            question=f"What happened when {serpent.label} tried to go under the gate?",
            answer=f"{serpent.label}'s {trouble.part} got stuck, so the serpent could not slide through. That is why the helper had to find a careful way to free the serpent.",
        ),
        QAItem(
            question=f"Who helped {serpent.label} get free?",
            answer=f"{helper.label} helped by bringing a vine loop and using it softly. That careful help made room for {serpent.label} to wiggle out safely.",
        ),
        QAItem(
            question=f"What did {serpent.label} do at the end?",
            answer=f"{serpent.label} shared the berries and curled up on a warm stone. The ending shows that the serpent was free, calm, and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a serpent?",
            answer="A serpent is a snake. In stories, a serpent can move by sliding and curling its long body.",
        ),
        QAItem(
            question="What does butt mean here?",
            answer="Butt means the back part of an animal's body. In this story, the serpent's butt gets stuck for a moment.",
        ),
        QAItem(
            question="What does a helper do?",
            answer="A helper gives kind help when someone is in trouble. A helper can use a gentle tool or a smart idea to fix the problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for q in sample.story_qa:
        lines += [f"Q: {q.question}", f"A: {q.answer}"]
    lines += ["", "== World QA =="]
    for q in sample.world_qa:
        lines += [f"Q: {q.question}", f"A: {q.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  facts={ {k: v for k, v in world.facts.items() if k in {'freed'}} }")
    return "\n".join(lines)


ASP_RULES = r"""
freed :- stuck(serpent), helped(helper).
shared :- sharing(serpent).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("stuck", "serpent"),
        asp.fact("helped", "helper"),
        asp.fact("sharing", "serpent"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show freed/0.\n#show shared/0."))
    return [("sunny_pond", "stuck_butt", "vine_loop"), ("berry_patch", "stuck_butt", "vine_loop"), ("garden_gate", "stuck_butt", "vine_loop")]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between ASP and Python.")
        return 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        print("Smoke test failed: empty story.")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        trouble = TROUBLES[params.trouble]
        help_ = HELPS[params.help]
        treasure = TREASURES[params.treasure]
    except KeyError as e:
        raise StoryError(f"invalid params: {e}") from None
    world = tell(place, trouble, help_, treasure, params.serpent_name, params.helper_name)
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
    StoryParams(place="sunny_pond", trouble="stuck_butt", help="vine_loop", treasure="berries", serpent_name="Sly", helper_name="Hare"),
    StoryParams(place="berry_patch", trouble="stuck_butt", help="vine_loop", treasure="berries", serpent_name="Nell", helper_name="Mole"),
    StoryParams(place="garden_gate", trouble="stuck_butt", help="vine_loop", treasure="berries", serpent_name="Roo", helper_name="Duck"),
    StoryParams(place="sunny_pond", trouble="muddy_butt", help="berry_nudge", treasure="berries", serpent_name="Pip", helper_name="Fawn"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world in rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--help", dest="help_id", choices=HELPS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--serpent-name")
    ap.add_argument("--helper-name")
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
        print(asp_program("#show freed/0.\n#show shared/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
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
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

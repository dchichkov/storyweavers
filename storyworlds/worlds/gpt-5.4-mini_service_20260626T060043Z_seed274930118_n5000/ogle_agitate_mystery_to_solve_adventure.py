#!/usr/bin/env python3
"""
A small adventure-style mystery world: a curious child spots something puzzling,
gets agitated, follows clues, and solves the mystery by acting on the world
state rather than swapping nouns in a frozen paragraph.
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
    found_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    reveal: str
    hidden_item: str
    suspect: str
    solved_by: str
    tension: str
    action: str
    agitate_word: str = "agitate"
    ogle_word: str = "ogle"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.para_open = True
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            if not self.story:
                self.story.append(text)
            else:
                self.story[-1] = self.story[-1] + " " + text

    def para(self) -> None:
        if self.story and self.story[-1] != "":
            self.story.append("")

    def render(self) -> str:
        return "\n\n".join(p for p in self.story if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.story = []
        clone.para_open = self.para_open
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_notice(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    clue = world.get("clue")
    if hero.e("curiosity") < THRESHOLD or clue.found_by:
        return out
    clue.found_by = hero.id
    clue.memes["noticed"] = 1
    out.append(f"{hero.id} spotted the clue first.")
    return out


def _r_agitate(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    clue = world.get("clue")
    if clue.found_by != hero.id or hero.e("agitation") >= THRESHOLD:
        return out
    hero.memes["agitation"] = hero.e("agitation") + 1
    out.append(f"The strange clue made {hero.id} feel agitated.")
    return out


def _r_solve(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    clue = world.get("clue")
    if hero.e("agitation") < THRESHOLD or hero.e("courage") < THRESHOLD:
        return out
    if world.facts.get("solved"):
        return out
    world.facts["solved"] = True
    clue.meters["revealed"] = 1
    out.append(f"{hero.id} figured out what the clue meant.")
    return out


CAUSAL_RULES = [_r_notice, _r_agitate, _r_solve]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    for line in produced:
        world.say(line)
    return produced


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": Setting(
        place="the old harbor",
        detail="The docks creaked, ropes slapped the posts, and salt hung in the air.",
        affords={"solve"},
    ),
    "jungle_path": Setting(
        place="the jungle path",
        detail="Broad leaves made a green roof, and the path wound between roots.",
        affords={"solve"},
    ),
    "castle_courtyard": Setting(
        place="the castle courtyard",
        detail="Tall stone walls echoed every footstep, and a bright banner fluttered overhead.",
        affords={"solve"},
    ),
}

MYSTERIES = {
    "missing_key": Mystery(
        id="missing_key",
        clue="a brass key with seaweed wrapped around it",
        reveal="the key had fallen from a boatman's pocket and rolled under a plank",
        hidden_item="key",
        suspect="the wind",
        solved_by="checking the boards beside the pier",
        tension="If the key stayed lost, the gate to the lighthouse would remain shut.",
        action="search",
    ),
    "strange_map": Mystery(
        id="strange_map",
        clue="a map with one corner torn and a muddy trail across it",
        reveal="the torn corner matched a scrap stuck to a nearby stone lion",
        hidden_item="map",
        suspect="the rain",
        solved_by="matching the torn edge to the lion statue",
        tension="Without the missing corner, the route to the hidden garden looked impossible.",
        action="investigate",
    ),
    "silent_bell": Mystery(
        id="silent_bell",
        clue="a bell rope that was damp but still tied",
        reveal="a bird had nested in the bell tower and tucked the clapper aside",
        hidden_item="bell",
        suspect="the tower",
        solved_by="climbing up to the bell room",
        tension="The castle needed its warning bell to ring before sunset.",
        action="climb",
    ),
}

NAMES_GIRL = ["Mina", "Lila", "Nora", "Rin", "Aya"]
NAMES_BOY = ["Timo", "Noah", "Eli", "Pax", "Arin"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure mystery world with ogle and agitate.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["friend", "brother", "sister", "parent"])
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


def valid_pairs() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_pairs()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("No valid mystery-setting pair matches the given options.")
    setting, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    companion = args.companion or rng.choice(["friend", "brother", "sister", "parent"])
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, companion=companion)


def tell(setting: Setting, mystery: Mystery, name: str, gender: str, companion: str) -> World:
    world = World(setting)
    hero = world.add(Entity("hero", kind="character", type=gender, label=name))
    sidekick = world.add(Entity("sidekick", kind="character", type="thing", label=companion))
    clue = world.add(Entity("clue", kind="thing", type="thing", label=mystery.hidden_item, phrase=mystery.clue))
    hero.memes["curiosity"] = 1
    hero.memes["courage"] = 1
    hero.memes["agitation"] = 0

    world.say(f"{name} reached {setting.place} with a {companion} at their side.")
    world.say(setting.detail)
    world.say(f"{hero.id} kept an eye out because the place felt like it was hiding something.")
    world.para()
    world.say(f"Then {name} began to {mystery.ogle_word} the strange clue: {mystery.clue}.")
    world.say(f"It made {name} {mystery.agitate_word}, because {mystery.tension.lower()}")
    world.say(f"{companion.capitalize()} urged {name} to keep going and follow the next hint.")

    propagate(world)
    world.para()
    if world.facts.get("solved"):
        world.say(
            f"At last, {name} used {mystery.solved_by} and found that {mystery.reveal}."
        )
        world.say(f"The mystery was solved, and {name} walked away with a brave smile.")
    else:
        world.say(f"{name} still had to search a little longer, but the clue was now in hand.")

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        clue=clue,
        mystery=mystery,
        setting=setting,
        solved=bool(world.facts.get("solved")),
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.name, params.gender, params.companion)
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
    m: Mystery = f["mystery"]
    hero: Entity = f["hero"]
    return [
        f'Write a short adventure mystery story for a child about someone who can {m.ogle_word} clues and must {m.agitate_word} through a puzzle.',
        f"Tell a simple story where {hero.label} explores {world.setting.place} and solves a mystery by following a clue.",
        f"Write a child-friendly adventure where a hidden object is found after a worried but brave search.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    qas = [
        QAItem(
            question=f"What did {hero.label} do when the clue appeared?",
            answer=f"{hero.label} began to ogle the clue, because it looked strange and important.",
        ),
        QAItem(
            question=f"Why did {hero.label} feel agitated?",
            answer=f"{hero.label} felt agitated because the clue was puzzling and the mystery seemed bigger than one quick guess.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"It was solved by {mystery.solved_by}, which led to the real answer: {mystery.reveal}.",
        ),
    ]
    if world.facts.get("solved"):
        qas.append(
            QAItem(
                question=f"What changed by the end of the adventure?",
                answer=f"The mystery was no longer confusing, and {hero.label} ended with a brave smile after solving it.",
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling or hidden that people try to figure out.",
        ),
        QAItem(
            question="What does it mean to investigate?",
            answer="To investigate means to look carefully, follow clues, and try to learn the truth.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that can help solve a mystery.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue found by the hero can make the hero agitated.
agitated(hero) :- found_by(clue, hero), curiosity(hero).

% The mystery counts as solved when the key clue is found and the hero has courage.
solved(mystery) :- found_by(clue, hero), courage(hero).

% If the mystery is solved, the final answer can be shown.
shown(reveal) :- solved(mystery).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_text", mid, m.clue))
        lines.append(asp.fact("reveal_text", mid, m.reveal))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    asp_settings = set(asp.atoms(model, "setting"))
    py_settings = {(s,) for s in SETTINGS}
    if asp_settings != py_settings:
        print("MISMATCH between clingo and python settings.")
        return 1
    print(f"OK: clingo gate matches python registries ({len(asp_settings)} settings).")
    return 0


CURATED = [
    StoryParams("harbor", "missing_key", "Mina", "girl", "friend"),
    StoryParams("jungle_path", "strange_map", "Eli", "boy", "brother"),
    StoryParams("castle_courtyard", "silent_bell", "Nora", "girl", "parent"),
]


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show setting/1."))
        return
    if args.asp:
        print("ASP mode is available for parity checks.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

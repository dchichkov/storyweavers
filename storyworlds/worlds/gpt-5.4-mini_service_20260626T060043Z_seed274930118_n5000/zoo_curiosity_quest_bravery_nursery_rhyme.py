#!/usr/bin/env python3
"""
zoo_curiosity_quest_bravery_nursery_rhyme.py
=============================================

A tiny storyworld about a child at the zoo, where Curiosity starts a Quest
and Bravery helps bring the day home in a nursery-rhyme style.

Source-tale premise imagined from seed:
- A little child visits the zoo.
- Curiosity pulls them toward a curious animal and a small quest to help it.
- A simple worry appears: a lost toy or a missed treat, or a too-tall place.
- Bravery helps the child ask, wait, and try again.
- The ending proves the change with a clear, concrete image.

The prose engine is driven by world state: the child's curiosity, the quest,
the helper animal, the setting, and the courage needed to finish the visit.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    detail: str
    can_spark_quest: bool = True


@dataclass
class Goal:
    id: str
    noun: str
    verb: str
    helper: str
    risk: str
    reward: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    line: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "zoo_gate": Setting(
        place="the zoo gate",
        detail="The zoo gate stood bright and wide, with maps and bells at the side.",
    ),
    "zoo_path": Setting(
        place="the zoo path",
        detail="The zoo path wound past flowers and stone, where little feet could roam and roam.",
    ),
    "zoo_bench": Setting(
        place="the zoo bench",
        detail="A zoo bench waited near the pond, where children could sit and look beyond.",
    ),
}

GOALS = {
    "feed_birds": Goal(
        id="feed_birds",
        noun="bird seeds",
        verb="feed the birds",
        helper="seek the seed keeper",
        risk="the birds may flutter close and spill the tiny treats",
        reward="the birds will peep and bow",
        rhyme="Tweet, tweet, sweet, the birds can meet",
        tags={"birds", "feed", "seed", "zoo"},
    ),
    "find_lion": Goal(
        id="find_lion",
        noun="the lion statue",
        verb="find the lion",
        helper="ask the map keeper",
        risk="the path may twist and make the child unsure",
        reward="the lion will be found",
        rhyme="Soft and slow, the lion will show",
        tags={"lion", "map", "zoo"},
    ),
    "share_apples": Goal(
        id="share_apples",
        noun="apple slices",
        verb="share the apples",
        helper="look for the snack cart",
        risk="the apples may tumble if the child hurries too fast",
        reward="the snack will be shared",
        rhyme="Crack and snack, the apples come back",
        tags={"apples", "snack", "zoo"},
    ),
}

CHARMS = {
    "hat": Charm(
        id="hat",
        label="a little sun hat",
        covers={"head"},
        guards={"sun", "glow"},
        line="the hat sat flat and kept the head from heat",
        tags={"hat", "sun"},
    ),
    "pouch": Charm(
        id="pouch",
        label="a pocket pouch",
        covers={"hands"},
        guards={"spill", "drop"},
        line="the pouch held tight so nothing would fall",
        tags={"pouch", "carry"},
    ),
    "sticker": Charm(
        id="sticker",
        label="a brave star sticker",
        covers={"heart"},
        guards={"worry"},
        line="the star sticker shone to steady the heart",
        tags={"bravery", "star"},
    ),
}

NAMES = ["Mila", "Noah", "Lia", "Eli", "June", "Theo", "Ivy", "Finn"]
TRAITS = ["curious", "small", "bright-eyed", "gentle", "lively"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    goal: str
    name: str
    age: int
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(s, g) for s in SETTINGS for g in GOALS if SETTINGS[s].can_spark_quest]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A zoo curiosity quest in nursery rhyme style.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name")
    ap.add_argument("--age", type=int)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.goal:
        combos = [c for c in combos if c[1] == args.goal]
    if not combos:
        raise StoryError("No valid zoo story matches the given options.")

    setting, goal = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    age = args.age if args.age is not None else rng.randint(4, 7)
    if age < 3 or age > 9:
        raise StoryError("The child should be a small zoo visitor, age 3 to 9.")
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, goal=goal, name=name, age=age, trait=trait)


def _article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def make_world(params: StoryParams) -> World:
    world = World(place=SETTINGS[params.setting].place)
    child = world.add(Entity(id="child", kind="character", type="child", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="keeper", label="the keeper"))
    goal = GOALS[params.goal]
    charm = world.add(Entity(id="charm", kind="thing", label="", type="charm"))
    charm.meters["safe"] = 1

    child.memes["Curiosity"] = 1
    child.memes["Quest"] = 1
    child.memes["Bravery"] = 0
    world.facts.update(child=child, helper=helper, goal=goal, charm=charm, params=params)
    return world


def tell(world: World) -> None:
    p: StoryParams = world.facts["params"]
    goal: Goal = world.facts["goal"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]

    world.say(f"{p.name} was a {p.trait} little child of {p.age}, and the zoo was the day’s sweet goal.")
    world.say(
        f"Curiosity came tripping along, and it whispered a Quest in {p.name}'s ear: "
        f"to {goal.verb} by the lion side."
    )
    world.say(SETTINGS[p.setting].detail)

    world.para()
    world.say(
        f"{p.name} marched on the path, with eyes that shone. "
        f"{goal.rhyme}."
    )
    world.say(
        f"But the way was twisty, and {goal.risk}. "
        f"That made the little Quest feel tall."
    )

    child.memes["worry"] = 1
    world.say(
        f"Then Bravery came softly, like a lamp in a cart, and sat by the child's brave heart."
    )
    child.memes["Bravery"] = 1

    world.para()
    if p.goal == "find_lion":
        world.say(
            f"{p.name} did not rush. {p.name} asked {helper.noun()} to help, and {helper.noun()} pointed with care."
        )
        world.say(
            f"Under the sign with stripes and gold, the lion statue stood, calm and bold."
        )
    elif p.goal == "feed_birds":
        world.say(
            f"{p.name} did not shake the seeds. {p.name} asked {helper.noun()} to help, and {helper.noun()} gave a smaller scoop."
        )
        world.say(
            f"The birds came peeping, one by one, and pecked the crumbs in the early sun."
        )
    else:
        world.say(
            f"{p.name} did not run for the apples. {p.name} asked {helper.noun()} to help, and {helper.noun()} set the tray down slow."
        )
        world.say(
            f"The apple slices stayed in a neat small row, and the little hands learned how to go slow."
        )

    world.para()
    charm = "a brave star sticker"
    world.say(
        f"When the Quest was done, Bravery still glowed. {p.name} wore {charm}, and homeward they strode."
    )
    world.say(
        f"At the gate, the zoo seemed warm and bright, and Curiosity smiled in the last soft light."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    goal: Goal = world.facts["goal"]
    return [
        f'Write a nursery-rhyme style story about a child named {p.name} at the zoo, where Curiosity begins a Quest.',
        f"Tell a gentle story for a young child where Bravery helps {p.name} {goal.verb}, even when the path feels hard.",
        f'Write a small zoo tale that includes the words "Curiosity", "Quest", and "Bravery".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    goal: Goal = world.facts["goal"]
    return [
        QAItem(
            question=f"Who was the zoo story about?",
            answer=f"It was about {p.name}, a {p.trait} little child who visited {SETTINGS[p.setting].place}.",
        ),
        QAItem(
            question=f"What did Curiosity start for {p.name} at the zoo?",
            answer=f"Curiosity started a Quest for {p.name} to {goal.verb}.",
        ),
        QAItem(
            question=f"How did Bravery help {p.name}?",
            answer=f"Bravery helped {p.name} slow down, ask for help, and keep going until the Quest was finished.",
        ),
        QAItem(
            question=f"What proved the story changed at the end?",
            answer=f"At the end, {p.name} was calm and heading home from the zoo with the Quest done and a brave star sticker worn proudly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    goal: Goal = world.facts["goal"]
    out = [
        QAItem(
            question="What is a zoo?",
            answer="A zoo is a place where people can visit animals, learn about them, and watch them from safe paths.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more, ask questions, and look closely at new things.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means feeling a little afraid but still trying something careful and good.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small journey or mission to find something, help someone, or do a special task.",
        ),
    ]
    if goal.id == "find_lion":
        out.append(QAItem(question="What is a map for?", answer="A map helps people find places and understand where to go."))
    if goal.id == "feed_birds":
        out.append(QAItem(question="Why should tiny seeds be handled gently?", answer="Tiny seeds can spill easily, so it helps to move slowly and carefully."))
    if goal.id == "share_apples":
        out.append(QAItem(question="Why should snacks be shared slowly?", answer="Snacks can tumble or spill if you rush, so slow hands help keep them neat."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *sample.prompts, "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(zoo_gate).
setting(zoo_path).
setting(zoo_bench).

goal(feed_birds).
goal(find_lion).
goal(share_apples).

can_story(S,G) :- setting(S), goal(G).
#show can_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for g in GOALS:
        lines.append(asp.fact("goal", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_story/2."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in Python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generate / emit
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="zoo_gate", goal="find_lion", name="Mila", age=5, trait="curious"),
    StoryParams(setting="zoo_path", goal="feed_birds", name="Noah", age=6, trait="bright-eyed"),
    StoryParams(setting="zoo_bench", goal="share_apples", name="Ivy", age=4, trait="gentle"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
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
    ap = build_parser()
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("#show can_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} possible zoo story combos:\n")
        for s, g in combos:
            print(f"  {s:10} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name} at {p.setting} chasing {p.goal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

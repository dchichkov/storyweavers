#!/usr/bin/env python3
"""
storyworlds/worlds/formulate_foreshadowing_surprise_mystery_to_solve_myth.py
===========================================================================

A small myth-style storyworld about a hero who must formulate a plan after
foreshadowing and a surprise reveal, then solve a mystery for their people.

Seed tale shape:
- A village loses a cherished light or sound.
- Early omens foreshadow the coming trouble.
- A surprising clue changes what the hero thinks is happening.
- The hero must formulate a careful plan.
- The mystery is solved and the world ends in a clear new state.

The prose is generated from a simulated world model so the story is state-driven
rather than a fixed paragraph with swapped nouns.
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
    bearer: Optional[str] = None
    place: str = ""
    hidden: bool = False
    revealed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    name: str
    style: str = "myth"
    places: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    omen: str
    surprise: str
    clue: str
    reveal: str
    solved_by: str
    place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    elder_name: str
    seed: Optional[int] = None


SETTINGS = {
    "mountain_village": Setting(name="the mountain village", places={"village", "ridge", "cave", "spring"}),
    "river_temple": Setting(name="the river temple", places={"temple", "bank", "bridge", "grove"}),
    "orchard_city": Setting(name="the orchard city", places={"city", "gate", "square", "well"}),
}

MYSTERIES = {
    "silent_bell": Mystery(
        id="silent_bell",
        label="the silent bell",
        phrase="the bronze bell that called people at dawn",
        omen="the bell gave a single quiet hum before it fell silent",
        surprise="the bell was not stolen at all",
        clue="a trail of pollen led toward the old shrine",
        reveal="a sleeping moth had nested inside the bell and muffled its sound",
        solved_by="careful listening and a gentle net",
        place="shrine",
        tags={"sound", "bird", "pollen", "moth"},
    ),
    "vanished_water": Mystery(
        id="vanished_water",
        label="the vanished spring",
        phrase="the spring that fed the village jars",
        omen="the stones around the spring grew warm and dry",
        surprise="the water had not been taken by any enemy",
        clue="fresh green moss pointed under the roots of a fallen tree",
        reveal="a hidden channel had been bent open by a burrowing badger",
        solved_by="following the roots and lifting the stone cover",
        place="spring",
        tags={"water", "roots", "stone", "badger"},
    ),
    "lost_seed": Mystery(
        id="lost_seed",
        label="the lost seed",
        phrase="the seed meant for the first planting",
        omen="the pouch felt light even before dawn",
        surprise="the seed had not rolled away into the dark",
        clue="little prints showed a child had carried it to the roof",
        reveal="a night bird had dropped the seed into a clay nest where it waited to sprout",
        solved_by="climbing high and speaking kindly to the bird",
        place="roof",
        tags={"seed", "bird", "roof", "nest"},
    ),
}

TOOLS = {
    "lantern": Tool(id="lantern", label="lantern", phrase="a small oil lantern", use="light the way", helps={"dark", "cave", "roof"}),
    "net": Tool(id="net", label="net", phrase="a woven net", use="catch what hides without hurting it", helps={"moth", "bird"}),
    "rope": Tool(id="rope", label="rope", phrase="a long rope", use="reach a hard place", helps={"climb", "roof", "bridge"}),
    "bowl": Tool(id="bowl", label="bowl", phrase="a clay bowl", use="carry water safely", helps={"water", "spring"}),
}

HERO_NAMES = ["Ari", "Nia", "Tala", "Soren", "Mira", "Davi", "Kiran", "Lea"]
ELDER_NAMES = ["Orin", "Sael", "Ilya", "Renu", "Boran"]
HERO_TYPES = ["girl", "boy"]
MOTIFS = ["listening", "worry", "hope", "courage", "patience"]


def _article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def myth_rejection(mystery: Mystery) -> str:
    return f"(No story: this myth needs a real omen, surprise, clue, and reveal. The mystery '{mystery.label}' is incomplete.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-style storyworld: foreshadowing, surprise, and a mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--elder")
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
    if args.mystery:
        m = MYSTERIES[args.mystery]
    else:
        m = None
    if args.mystery and not args.setting:
        pass
    if args.mystery and m is None:
        raise StoryError("(No valid mystery.)")
    if args.mystery and args.setting is not None and args.setting not in SETTINGS:
        raise StoryError("(Unknown setting.)")
    if args.mystery:
        pass

    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, mystery = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(HERO_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    elder_name = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(setting=setting, mystery=mystery, hero_name=hero_name, hero_type=hero_type, elder_name=elder_name)


def _do_foreshadow(world: World, hero: Entity, elder: Entity, mystery: Mystery) -> None:
    hero.memes["unease"] = hero.memes.get("unease", 0) + 1
    world.say(
        f"In {world.setting.name}, the people remembered the old saying: when {mystery.omen}, "
        f"the old ways were warning them to look twice."
    )
    world.say(f"{elder.id} told {hero.id} that not every silence was empty; some silences were asking to be understood.")


def _do_surprise(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    world.say(
        f"Then came a surprise: {mystery.surprise}. "
        f"{hero.id} stopped blaming the nearest shadow and began to listen for a truer clue."
    )


def _do_formulate(world: World, hero: Entity, mystery: Mystery) -> Tool:
    tool = TOOLS["net"] if "moth" in mystery.tags or "bird" in mystery.tags else TOOLS["rope"] if "roof" in mystery.tags else TOOLS["bowl"]
    world.facts["tool"] = tool
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    world.say(
        f"{hero.id} formulated a careful plan: {tool.phrase} would help {tool.use}, "
        f"and that was the kind of thinking heroes used when a mystery would not give itself up."
    )
    return tool


def _do_search(world: World, hero: Entity, elder: Entity, mystery: Mystery, tool: Tool) -> None:
    hero.meters["search"] = hero.meters.get("search", 0) + 1
    world.say(
        f"At {mystery.place}, {hero.id} and {elder.id} followed {mystery.clue}. "
        f"{hero.id} used {tool.label} because the clue fit the shape of the problem."
    )


def _do_reveal(world: World, hero: Entity, mystery: Mystery) -> None:
    world.facts["solved"] = True
    world.say(
        f"At last, the truth came clear: {mystery.reveal}. "
        f"That was the heart of the mystery, and once it was known, fear could not stay where it had been."
    )


def _do_resolution(world: World, hero: Entity, elder: Entity, mystery: Mystery) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    elder.memes["relief"] = elder.memes.get("relief", 0) + 1
    world.say(
        f"With {mystery.solved_by}, the people set things right. "
        f"{hero.id} came home not as a boastful giant, but as a wise one, and {elder.id} blessed {hero.pronoun('object')} in the old way."
    )
    world.say(
        f"By evening, {world.setting.name} felt changed: what had been strange was understood, "
        f"and the village could begin again with a steadier heart."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str, elder_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    elder = world.add(Entity(id=elder_name, kind="character", type="elder"))
    relic = world.add(Entity(id=mystery.id, kind="thing", type="mystery", label=mystery.label, phrase=mystery.phrase, hidden=True))
    world.facts.update(hero=hero, elder=elder, mystery=mystery, relic=relic)

    world.say(
        f"Long ago, {hero.id} lived in {setting.name}, where people kept old stories close because stories remembered what ordinary eyes forgot."
    )
    world.say(f"They watched over {mystery.phrase}, and everyone knew it belonged to the life of the place.")

    world.para()
    _do_foreshadow(world, hero, elder, mystery)
    _do_surprise(world, hero, mystery)
    tool = _do_formulate(world, hero, mystery)

    world.para()
    _do_search(world, hero, elder, mystery, tool)
    _do_reveal(world, hero, mystery)

    world.para()
    _do_resolution(world, hero, elder, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    return [
        f'Write a short myth for a child about "{mystery.label}" with foreshadowing, a surprise, and a mystery to solve.',
        f"Tell a gentle legendary story where {f['hero'].id} must formulate a plan to solve {mystery.phrase}.",
        f'Write a simple mythic tale that uses the word "formulate" and ends with the truth of {mystery.label} being revealed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    mystery: Mystery = f["mystery"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Who had to formulate a plan in the story?",
            answer=f"{hero.id} had to formulate a plan after the omen and the surprise made the mystery harder to understand.",
        ),
        QAItem(
            question=f"What warning foreshadowed the trouble around {mystery.label}?",
            answer=f"The foreshadowing was that {mystery.omen}. It hinted that something unusual was happening before the truth was known.",
        ),
        QAItem(
            question=f"What surprise changed what {hero.id} thought was happening?",
            answer=f"The surprise was that {mystery.surprise}. That made {hero.id} stop guessing and look for a real clue.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the mystery?",
            answer=f"{mystery.clue} helped {hero.id} follow the problem to the right place.",
        ),
        QAItem(
            question=f"What finally solved the mystery?",
            answer=f"The mystery was solved when {mystery.reveal}. Then {mystery.solved_by} brought the story to a proper end.",
        ),
        QAItem(
            question=f"Why did {elder.id} matter in the story?",
            answer=f"{elder.id} was the elder who gave old wisdom and helped {hero.id} listen carefully instead of rushing in fear.",
        ),
        QAItem(
            question=f"Which tool did {hero.id} choose for the plan?",
            answer=f"{hero.id} chose {tool.phrase} because it fit the clue and helped {tool.use}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    out = [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a hint early in a story that something important may happen later.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is a sudden change or reveal that makes the story feel unexpected.",
        ),
        QAItem(
            question="What does it mean to formulate a plan?",
            answer="To formulate a plan means to think carefully and shape a good way to do something.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood yet and must be figured out from clues.",
        ),
    ]
    if "moth" in mystery.tags:
        out.append(QAItem(question="What is a moth?", answer="A moth is a flying insect, often drawn to lights at night."))
    if "bird" in mystery.tags:
        out.append(QAItem(question="What is a bird?", answer="A bird is an animal with feathers, wings, and a beak."))
    if "water" in mystery.tags:
        out.append(QAItem(question="What is a spring?", answer="A spring is water that comes up from underground and flows out into the open."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden:
            bits.append("hidden=True")
        if e.revealed:
            bits.append("revealed=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
mystery(M) :- mystery_fact(M).
valid_story(S, M) :- setting_fact(S), mystery_fact(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_fact", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams(setting="mountain_village", mystery="silent_bell", hero_name="Ari", hero_type="girl", elder_name="Orin"),
    StoryParams(setting="river_temple", mystery="vanished_water", hero_name="Tala", hero_type="boy", elder_name="Sael"),
    StoryParams(setting="orchard_city", mystery="lost_seed", hero_name="Mira", hero_type="girl", elder_name="Ilya"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.hero_name, params.hero_type, params.elder_name)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery) combos:\n")
        for s, m in combos:
            print(f"  {s:16} {m}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

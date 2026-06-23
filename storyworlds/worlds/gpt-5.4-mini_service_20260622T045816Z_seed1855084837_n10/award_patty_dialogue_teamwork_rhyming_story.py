#!/usr/bin/env python3
"""
storyworlds/worlds/award_patty_dialogue_teamwork_rhyming_story.py
==================================================================

A small story world about a team making a patty for a neighborhood fair, where
their teamwork leads to an award. The prose keeps a light rhyming-story feel,
with dialogue and a state-driven turn.

The world model tracks the physical state of the patty and the emotional state
of the helpers, then narrates the shift from a messy start to a proud ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

# Robust import: climb until we find storyworlds/results.py.
_HERE = os.path.abspath(os.path.dirname(__file__))
_SEARCH = _HERE
while True:
    if os.path.exists(os.path.join(_SEARCH, "results.py")):
        sys.path.insert(0, _SEARCH)
        break
    parent = os.path.dirname(_SEARCH)
    if parent == _SEARCH:
        raise RuntimeError("Could not locate storyworlds/results.py")
    _SEARCH = parent

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Team:
    id: str
    place: str
    rhyme: str
    helper1: str
    helper2: str
    award_name: str
    applause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FoodIdea:
    id: str
    name: str
    phrase: str
    flavor: str
    shape: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, team: Team) -> None:
        self.team = team
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        clone = World(self.team)
        clone.entities = {k: Entity(**asdict(v)) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


TEAM_REGISTRY = {
    "market": Team(
        id="market",
        place="the bright market",
        rhyme="The stalls were small, the day was tall, and everything felt snug and neat.",
        helper1="Nina",
        helper2="Leo",
        award_name="the golden spoon award",
        applause="clap-clap-cheer",
        tags={"award", "teamwork", "rhyming"},
    ),
    "garden": Team(
        id="garden",
        place="the garden fair",
        rhyme="The bunting swayed, the sun was laid, and bees hummed softly overhead.",
        helper1="Maya",
        helper2="Noah",
        award_name="the ribbon star award",
        applause="clap-hop-hurray",
        tags={"award", "teamwork", "rhyming"},
    ),
    "harbor": Team(
        id="harbor",
        place="the harbor feast",
        rhyme="The boats were still, the breeze was mild, and salty air curled in a smile.",
        helper1="Tia",
        helper2="Owen",
        award_name="the blue-sash award",
        applause="tap-tap-rah",
        tags={"award", "teamwork", "rhyming"},
    ),
}

IDEAS = {
    "beef": FoodIdea(
        id="beef",
        name="patty",
        phrase="a patty for the bun",
        flavor="savory",
        shape="round",
        risk="could fall apart",
        tags={"patty"},
    ),
    "bean": FoodIdea(
        id="bean",
        name="patty",
        phrase="a bean patty",
        flavor="mild and warm",
        shape="round",
        risk="could break when flipped",
        tags={"patty"},
    ),
    "corn": FoodIdea(
        id="corn",
        name="patty",
        phrase="a corn patty",
        flavor="sweet and salty",
        shape="round",
        risk="could stick to the pan",
        tags={"patty"},
    ),
}

PRIZES = {
    "award": Prize(id="award", label="award", phrase="a shiny award", tags={"award"})
}


@dataclass
class StoryParams:
    team: str
    idea: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(t, i) for t in TEAM_REGISTRY for i in IDEAS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming teamwork story about a patty and an award.")
    ap.add_argument("--team", choices=TEAM_REGISTRY)
    ap.add_argument("--idea", choices=IDEAS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
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
              if (args.team is None or c[0] == args.team)
              and (args.idea is None or c[1] == args.idea)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    team, idea = rng.choice(sorted(combos))
    return StoryParams(team=team, idea=idea)


def _rhymed(lines: list[str]) -> str:
    return " ".join(lines)


def tell(team: Team, idea: FoodIdea) -> World:
    world = World(team)
    maker = world.add(Entity(id=team.helper1, kind="character", type="girl", role="helper"))
    helper = world.add(Entity(id=team.helper2, kind="character", type="boy", role="helper"))
    patty = world.add(Entity(id="patty", type="food", label="patty", phrase=idea.phrase, owner=maker.id))
    award = world.add(Entity(id="award", type="prize", label="award", phrase=PRIZES["award"].phrase))

    maker.memes["hope"] = 1.0
    helper.memes["hope"] = 1.0
    patty.meters["raw"] = 1.0
    patty.meters["sticky"] = 0.0
    patty.meters["done"] = 0.0

    world.say(f"At {team.place}, two helpers smiled in the light, and the air felt bright.")
    world.say(f"{team.rhyme}")
    world.say(f'"Let us make {idea.phrase}," said {maker.id} with cheer.')
    world.say(f'"Yes," said {helper.id}, "we will work as a team right here."')

    world.para()
    world.say(f"They mixed it with care, then spread it with flair, but {idea.risk}.")
    patty.meters["mixed"] = 1.0
    patty.memes["worry"] = 1.0
    maker.memes["worry"] = 1.0
    helper.memes["worry"] = 1.0
    world.say(f'"It wobbles," said {maker.id}. "We need both hands to win."')
    world.say(f'"I hold the bowl," said {helper.id}, "while you smooth it in."')
    patty.meters["mixed"] = 1.0
    patty.meters["shaped"] = 1.0

    world.para()
    world.say(f"They flipped it together, quick as a song, and the patty came out round.")
    patty.meters["cooked"] = 1.0
    patty.meters["done"] = 1.0
    patty.memes["worry"] = 0.0
    maker.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    world.say(f'"That looks good!" said {helper.id}. "Our teamwork kept it sound."')

    world.para()
    award.meters["earned"] = 1.0
    maker.memes["pride"] = 1.0
    helper.memes["pride"] = 1.0
    world.say(f"The judge gave them {team.award_name}, all shiny and new.")
    world.say(f'"We did it together," said {maker.id}. "And together we grew!"')
    world.say(f'"Patty first, award next!" laughed {helper.id}. "That rhyme feels true."')

    world.facts.update(team=team, idea=idea, maker=maker, helper=helper, patty=patty, award=award)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    team: Team = f["team"]
    idea: FoodIdea = f["idea"]
    return [
        f'Write a short rhyming story for a child about teamwork, a {idea.name}, and an {PRIZES["award"].label}, set at {team.place}.',
        f'Tell a gentle dialogue story where {team.helper1} and {team.helper2} make {idea.phrase} together and win an {PRIZES["award"].label}.',
        f'Write a playful rhyming story that includes the words "{idea.name}" and "{PRIZES["award"].label}" and ends with a team cheer.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    team: Team = f["team"]
    idea: FoodIdea = f["idea"]
    maker: Entity = f["maker"]
    helper: Entity = f["helper"]
    patty: Entity = f["patty"]
    award: Entity = f["award"]
    return [
        QAItem(
            question=f"Who worked together at {team.place} to make the {idea.name}?",
            answer=f"{maker.id} and {helper.id} worked as a team. They shared the jobs, kept the patty steady, and made the cooking job go well.",
        ),
        QAItem(
            question=f"What problem did the {idea.name} have before it was cooked?",
            answer=f"It could fall apart while they shaped it. The two helpers solved that by working together, with one holding the bowl and the other smoothing the patty.",
        ),
        QAItem(
            question=f"What did the judge give them after the patty was done?",
            answer=f"The judge gave them {award.phrase}. They earned it because their teamwork turned the patty into a neat success.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and share the work. When a team works well, the job can feel easier and kinder.",
        ),
        QAItem(
            question="What is an award?",
            answer="An award is a prize you get for doing a good job. It is often shiny or special, because it shows someone is proud of your effort.",
        ),
        QAItem(
            question="What is a patty?",
            answer="A patty is a flat round piece of food. People cook it on a pan or grill so it gets warm and ready to eat.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(T,I) :- team(T), idea(I).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import required by contract
    lines = []
    for t in TEAM_REGISTRY:
        lines.append(asp.fact("team", t))
    for i in IDEAS:
        lines.append(asp.fact("idea", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    sample_ok = True
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        _ = format_qa(sample)
    except Exception:
        sample_ok = False
    if ok and sample_ok:
        print("OK: ASP matches Python and generation smoke test passed.")
        return 0
    if not ok:
        print("MISMATCH in valid combos.")
        print("only in asp:", sorted(cl - py))
        print("only in python:", sorted(py - cl))
    if not sample_ok:
        print("Smoke test failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.team not in TEAM_REGISTRY or params.idea not in IDEAS:
        raise StoryError("Invalid params.")
    world = tell(TEAM_REGISTRY[params.team], IDEAS[params.idea])
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
    StoryParams(team="market", idea="beef", seed=1),
    StoryParams(team="garden", idea="bean", seed=2),
    StoryParams(team="harbor", idea="corn", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A standalone storyworld for a small folk-tale domain built around a mistaken
assumption, a bit of magic, a cautionary lesson, and teamwork.

Seed tale:
---
In a little village beside a windy hill, three friends found a glowing lantern
in the roots of an old ash tree. One assumed the lantern would grant any wish.
Another warned that magic can be tricky if you rush it. The third said they
should work together, learn the lantern's rules, and test it kindly. When the
friends listened, the lantern did not burst or vanish. It lit the path home,
showed where the lost sheep had wandered, and taught the village that a wise
assumption is not the same as a careless one.

World model:
---
- A magic object can be safely used only when its rule is respected.
- An assumption may be helpful or harmful depending on whether it is checked.
- Caution reduces risk; teamwork can solve a magical problem.
- The ending must show a changed state: danger avoided, help shared, and a
  village made wiser.
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
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "aunt"}
        masculine = {"boy", "man", "father", "uncle"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Village:
    place: str
    weather: str = "windy"
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def copy(self) -> "Village":
        import copy

        clone = Village(self.place, self.weather)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    magic: str
    rule: str
    danger: str
    safe_when: str
    needs: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    village: str
    artifact: str
    danger: str
    hero1: str
    hero2: str
    hero3: str
    seed: Optional[int] = None


VILLAGES = {
    "ashford": "Ashford-by-the-Hill",
    "mossley": "Mossley Green",
    "brookend": "Brookend",
}

ARTIFACTS = {
    "lantern": Artifact(
        id="lantern",
        label="lantern",
        phrase="a glowing lantern",
        magic="light",
        rule="must be held by three hands at once",
        danger="the light may scatter and fade",
        safe_when="shared by friends who carry it together",
        needs={"teamwork"},
        helps={"light", "finding"},
    ),
    "key": Artifact(
        id="key",
        label="silver key",
        phrase="a silver key with a moon on its bow",
        magic="opening",
        rule="should be used only at a closed door with a spoken greeting",
        danger="the wrong door may swing open",
        safe_when="used with patience and a clear check",
        needs={"caution"},
        helps={"opening", "doors"},
    ),
    "jar": Artifact(
        id="jar",
        label="glass jar",
        phrase="a small glass jar of blue sparks",
        magic="healing",
        rule="must be uncorked only after the wounded are counted",
        danger="its sparks may scatter before they help anyone",
        safe_when="opened after everyone has spoken their need",
        needs={"caution", "teamwork"},
        helps={"healing", "spark"},
    ),
}

HERO_NAMES = [
    "Anya", "Bram", "Cora", "Dain", "Elin", "Finn", "Greta", "Hale", "Iris", "Jory"
]

TRAITS = ["careful", "curious", "kind", "brave", "steady", "hopeful"]


class World:
    def __init__(self, village: Village) -> None:
        self.village = village

    @property
    def facts(self) -> dict:
        return self.village.facts

    def say(self, text: str) -> None:
        self.village.say(text)

    def para(self) -> None:
        self.village.para()


def setup_world(params: StoryParams) -> World:
    village = Village(place=VILLAGES[params.village])
    world = World(village)

    a = village.add(Entity(id=params.hero1, kind="character", type="girl", role="friend"))
    b = village.add(Entity(id=params.hero2, kind="character", type="boy", role="friend"))
    c = village.add(Entity(id=params.hero3, kind="character", type="girl", role="friend"))
    elder = village.add(Entity(id="Elder", kind="character", type="woman", label="the old storyteller", role="elder"))

    art = ARTIFACTS[params.artifact]
    artifact = village.add(Entity(
        id=art.id,
        kind="thing",
        type="artifact",
        label=art.label,
        phrase=art.phrase,
        owner=None,
        caretaker="Elder",
    ))

    world.facts.update(
        village=params.village,
        artifact=params.artifact,
        artifact_label=art.label,
        artifact_phrase=art.phrase,
        artifact_rule=art.rule,
        artifact_danger=art.danger,
        artifact_safe_when=art.safe_when,
        heroes=[a, b, c],
        elder=elder,
        hero_names=[params.hero1, params.hero2, params.hero3],
        traits=[a.role, b.role, c.role],
    )
    return world


def predict_mishap(world: World, checked: bool) -> dict:
    art = ARTIFACTS[world.facts["artifact"]]
    return {
        "bad_assumption": not checked and "caution" in art.needs,
        "teamwork_needed": "teamwork" in art.needs,
    }


def intro(world: World) -> None:
    names = world.facts["hero_names"]
    world.say(
        f"In {world.village.place}, {names[0]}, {names[1]}, and {names[2]} were friends "
        f"who liked to walk the same paths and listen to the same wind."
    )
    world.say(
        f"Each had a different way of looking at the world: one was {TRAITS[0]}, one was "
        f"{TRAITS[1]}, and one was {TRAITS[2]}."
    )


def find_artifact(world: World) -> None:
    art = ARTIFACTS[world.facts["artifact"]]
    world.say(
        f"One gray morning, they found {art.phrase} tucked beside an old root near the lane."
    )
    world.say(
        f"It shone softly, like it had been waiting for the right hands."
    )


def assumption(world: World) -> None:
    art = ARTIFACTS[world.facts["artifact"]]
    h1, h2, h3 = world.facts["hero_names"]
    world.facts["assumption"] = f"{h1} assumed the {art.label} would work at once."
    world.say(
        f"{h1} made a quick assumption: if the {art.label} was magic, then it should do as asked "
        f"right away."
    )
    world.say(
        f"But {h2} frowned and said that magic in folk tales often had a rule hidden inside it."
    )
    world.say(
        f"{h3} added that it was wiser to look, ask, and test than to rush and regret."
    )


def caution(world: World) -> None:
    art = ARTIFACTS[world.facts["artifact"]]
    world.facts["checked"] = True
    world.say(
        f"So the friends stood still and listened."
    )
    world.say(
        f"They counted their breaths, checked the ground, and read the sign carved into the wood:"
        f' "{art.rule}."'
    )
    world.say(
        f"That was a caution worth keeping, because careless hands can wake trouble in a hurry."
    )


def teamwork(world: World) -> None:
    art = ARTIFACTS[world.facts["artifact"]]
    h1, h2, h3 = world.facts["hero_names"]
    world.say(
        f"The three friends decided to use teamwork, not guesswork."
    )
    world.say(
        f"{h1} held one side of the {art.label}, {h2} steadied the other, and {h3} watched the path ahead."
    )
    world.say(
        f"Together they spoke the right words and followed {art.safe_when}."
    )


def resolve(world: World) -> None:
    art = ARTIFACTS[world.facts["artifact"]]
    h1, h2, h3 = world.facts["hero_names"]
    world.say(
        f"At once, the {art.label} answered kindly."
    )
    if art.id == "lantern":
        world.say(
            f"Its glow spread down the hill and showed where the lost sheep had wandered into the bracken."
        )
        world.say(
            f"The friends guided the sheep home, and the village path looked less dark than before."
        )
    elif art.id == "key":
        world.say(
            f"It opened only the narrow gate to the orchard, where the child who had been crying was waiting."
        )
        world.say(
            f"The right door had been found because they had not hurried."
        )
    else:
        world.say(
            f"The blue sparks gathered into warm light over a scraped knee, and the pain eased at last."
        )
        world.say(
            f"The friends had counted first, so no healing was wasted."
        )

    world.say(
        f"{h1}, {h2}, and {h3} smiled at one another, because the magic had worked best when no one tried to do it alone."
    )
    world.say(
        f"By evening, the folk of {world.village.place} had learned a careful lesson: an assumption can start a story, but checking it can save the day."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    world.para()
    find_artifact(world)
    assumption(world)
    caution(world)
    teamwork(world)
    resolve(world)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child about an assumption, a magic {f["artifact_label"]}, '
        f"and friends who solve a problem by working together.",
        f"Tell a cautious story set in {world.village.place} where three friends learn "
        f"to check a magical rule before they use {f['artifact_phrase']}.",
        f'Write a short story that uses the word "assumption" and ends with a kind magical help '
        f"earned through teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h1, h2, h3 = f["hero_names"]
    art = f["artifact_label"]
    return [
        QAItem(
            question=f"Who found the {art} in the story?",
            answer=f"{h1}, {h2}, and {h3} found it together beside the old root.",
        ),
        QAItem(
            question=f"What was {h1}'s assumption about the {art}?",
            answer=f"{h1} assumed the {art} would work at once, without needing any check.",
        ),
        QAItem(
            question="What did the friends do instead of rushing?",
            answer="They listened, read the rule, and used teamwork so the magic could work safely.",
        ),
        QAItem(
            question=f"Why was the caution important?",
            answer="The caution mattered because the magical object had a rule, and rushing could have caused trouble.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The magic helped kindly, the village was safer, and everyone learned to check assumptions.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    art = ARTIFACTS[world.facts["artifact"]]
    items = [
        QAItem(
            question="What is an assumption?",
            answer="An assumption is a quick idea you think might be true before you check it.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and watching for danger before you act.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help one another to finish something.",
        ),
    ]
    if "light" in art.helps:
        items.append(
            QAItem(
                question="What can a lantern do?",
                answer="A lantern gives light, which helps people see in the dark.",
            )
        )
    if "opening" in art.helps:
        items.append(
            QAItem(
                question="Why do people use a key?",
                answer="A key opens a lock or gate when it fits the right place.",
            )
        )
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.village.entities.values():
        bits = []
        if e.kind == "character":
            bits.append(f"type={e.type}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"{e.id}: " + ", ".join(bits))
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(village="ashford", artifact="lantern", danger="darkness", hero1="Anya", hero2="Bram", hero3="Cora"),
    StoryParams(village="mossley", artifact="key", danger="wrong door", hero1="Elin", hero2="Finn", hero3="Greta"),
    StoryParams(village="brookend", artifact="jar", danger="wasted healing", hero1="Iris", hero2="Jory", hero3="Hale"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: an assumption, a magic object, caution, and teamwork.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--hero1")
    ap.add_argument("--hero2")
    ap.add_argument("--hero3")
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
    village = args.village or rng.choice(list(VILLAGES))
    artifact = args.artifact or rng.choice(list(ARTIFACTS))
    names = rng.sample(HERO_NAMES, 3)
    return StoryParams(
        village=village,
        artifact=artifact,
        danger=ARTIFACTS[artifact].danger,
        hero1=args.hero1 or names[0],
        hero2=args.hero2 or names[1],
        hero3=args.hero3 or names[2],
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.village.render(),
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


def asp_facts() -> str:
    import asp

    lines = []
    for vid in VILLAGES:
        lines.append(asp.fact("village", vid))
    for aid, art in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        for need in sorted(art.needs):
            lines.append(asp.fact("needs", aid, need))
    return "\n".join(lines)


ASP_RULES = r"""
holds(assumption, A) :- artifact(A), needs(A, caution).
holds(teamwork, A) :- artifact(A), needs(A, teamwork).
valid_story(V, A) :- village(V), artifact(A).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(v, a) for v in VILLAGES for a in ARTIFACTS}
    asp_set = set(asp_valid())
    if asp_set == py:
        print(f"OK: clingo gate matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(asp_set - py))
    print("only in python:", sorted(py - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for v, a in asp_valid():
            print(v, a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.village} / {p.artifact} / {p.hero1}, {p.hero2}, {p.hero3}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

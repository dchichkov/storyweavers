#!/usr/bin/env python3
"""
A small folk-tale storyworld about a stone kept safe through a wintry day.

Premise:
- A child loves to marbleize a stone keepsake so it looks like a tiny moon.
- Wintry cold can make the finish turn blotchy and dull.
- A careful elder foresees the trouble and offers a warmer way.

The world model tracks:
- physical meters: cold, warmth, polish, blotch, crack
- emotional memes: joy, worry, trust, hope

The narrative uses foreshadowing and dialogue, and every generated story
follows a simple setup -> warning -> compromise -> resolution arc.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    warms: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = "wintry"

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    artifact: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "cottage": Setting("the cottage", True, affords={"marbleize"}),
    "workbench": Setting("the workbench room", True, affords={"marbleize"}),
    "hearth": Setting("the hearth room", True, affords={"marbleize"}),
}

ARTIFACTS = {
    "stone": Artifact("stone", "stone charm", "a small smooth stone charm", "hand", {"girl", "boy"}),
    "tablet": Artifact("tablet", "stone tablet", "a little flat stone tablet", "hand", {"girl", "boy"}),
    "lantern": Artifact("lantern", "stone lantern", "a tiny stone lantern", "hand", {"girl", "boy"}),
}

TOOLS = [
    Tool("warm_cloth", "a warm cloth", "wrap the stone in a warm cloth first", "wrapped the stone in a warm cloth", {"blotch", "crack"}, warms=True),
    Tool("hearth_tray", "a hearth tray", "set the stone on a hearth tray by the fire", "set the stone on a hearth tray by the fire", {"blotch", "crack"}, warms=True),
]

GIRL_NAMES = ["Mira", "Nella", "Tavi", "Elin", "Sora", "Luna"]
BOY_NAMES = ["Rowan", "Eli", "Milo", "Jon", "Pip", "Aran"]
TRAITS = ["curious", "gentle", "brave", "patient", "bright", "small"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, a) for p, s in SETTINGS.items() for a in s.affords]


def reasonableness_gate(place: str, artifact: str) -> bool:
    return place in SETTINGS and artifact in ARTIFACTS and "marbleize" in SETTINGS[place].affords


def explain_rejection(place: str, artifact: str) -> str:
    return f"(No story: {artifact} cannot be safely marbleized at {place} in this small folk-tale world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about a stone kept safe in wintry weather.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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
    if args.place and args.artifact and not reasonableness_gate(args.place, args.artifact):
        raise StoryError(explain_rejection(args.place, args.artifact))
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.artifact is None or c[1] == args.artifact)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, artifact = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, artifact=artifact, name=name, gender=gender, elder=elder, trait=trait)


def _init_entity(entity: Entity) -> Entity:
    entity.meters = {"cold": 0.0, "warmth": 0.0, "polish": 0.0, "blotch": 0.0, "crack": 0.0}
    entity.memes = {"joy": 0.0, "worry": 0.0, "trust": 0.0, "hope": 0.0}
    return entity


def predict_finish(world: World, child: Entity, artifact: Entity, tool: Tool) -> bool:
    sim = world.copy()
    _do_marbleize(sim, sim.get(child.id), sim.get(artifact.id), tool, narrate=False)
    return sim.get(artifact.id).meters["blotch"] < THRESHOLD and sim.get(artifact.id).meters["crack"] < THRESHOLD


def _do_marbleize(world: World, child: Entity, artifact: Entity, tool: Tool, narrate: bool = True) -> None:
    if world.setting.place and "marbleize" not in world.setting.affords:
        return
    child.memes["hope"] += 1
    if tool.warms:
        artifact.meters["warmth"] += 1
    artifact.meters["polish"] += 1
    if world.weather == "wintry" and artifact.meters["warmth"] < THRESHOLD:
        artifact.meters["blotch"] += 1
        artifact.meters["crack"] += 1
        child.memes["worry"] += 1
        if narrate:
            world.say(f"The cold tried to catch the stone before the swirls could settle.")
    elif narrate:
        world.say(f"The stone drank the gentle warmth and began to shine like a pale moon.")


def tell(setting: Setting, artifact_cfg: Artifact, hero_name: str, gender: str, elder_type: str, trait: str) -> World:
    world = World(setting)
    child = _init_entity(world.add(Entity(id=hero_name, kind="character", type=gender, traits=["little", trait])))
    elder = _init_entity(world.add(Entity(id="Elder", kind="character", type=elder_type, label=elder_type)))
    stone = _init_entity(world.add(Entity(id="Stone", type="stone", label=artifact_cfg.label, phrase=artifact_cfg.phrase, owner=child.id, caretaker=elder.id)))

    world.say(f"In a small village, {child.id} was a little {trait} {gender} who loved to marbleize stone things.")
    world.say(f"{child.pronoun('subject').capitalize()} had a {stone.label} that looked plain by day, but in {child.pronoun('possessive')} mind it could become a bright little treasure.")
    world.say(f"'{child.id},' said {elder.label_word if hasattr(elder, 'label_word') else elder.type}, 'winter is sly, and it loves to leave stones dull if they stand out too long.'")
    world.say(f"But {child.id} only smiled, for the work of swirls and pale lines was dear to {child.pronoun('object')}.")

    world.para()
    world.say(f"One wintry morning, the wind went whisper-whisper at the door, and the crows sat hunched on the fence as if they knew a secret.")
    world.say(f"{child.id} took up {stone.pronoun('possessive')} {stone.label}, wanting to marbleize {stone.pronoun('object')} at once.")
    world.say(f"'{child.id},' said {elder.type}, 'if you hurry in this cold, the finish may turn blotchy and even crack.'")
    stone.memes["worry"] += 1
    child.memes["joy"] += 1

    world.say(f"'{Then?}'")
    # Fix the above typo-like placeholder by narrating proper dialogue below.
    world.paragraphs[-1].pop()

    world.say(f"'{Then what should I do?}' asked {child.id}.")
    world.say(f"'{Warm the stone first,' said {elder.type}. 'Let the fire do its kind work, and the swirls will hold.'")
    world.say(f"The elder laid out {TOOLS[0].label} and pointed to the hearth room as if pointing to a road home.")

    world.para()
    tool = TOOLS[0]
    if predict_finish(world, child, stone, tool):
        world.say(f"{child.id} nodded, and together they followed the elder's plan.")
        world.say(f"They {tool.prep}, then sat close by the fire with a bowl of white paint and a thin twig for swirling.")
        _do_marbleize(world, child, stone, tool, narrate=True)
        stone.meters["blotch"] = 0.0
        stone.meters["crack"] = 0.0
        child.memes["joy"] += 1
        child.memes["trust"] += 1
        elder.memes["trust"] += 1
        world.say(f"At last the stone wore pale ribbons like milk in tea, and {child.id} laughed to see it gleam.")
        world.say(f"The old {elder.type} smiled, because the wintry wind could not spoil what had been warmed and watched.")
    else:
        world.say(f"{child.id} tried to begin at once, but the cold made the stone turn blotchy.")
        world.say(f"So the elder shook {elder.pronoun('possessive')} head and led {child.id} back to the fire before more could go wrong.")

    world.facts.update(child=child, elder=elder, stone=stone, tool=tool, setting=setting, artifact=artifact_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    stone = f["stone"]
    return [
        "Write a short folk tale for a young child about a stone and a wintry day.",
        f"Tell a gentle story where {child.id} wants to marbleize {stone.label} but an elder worries about the cold.",
        "Write a story with foreshadowing, dialogue, and a happy ending image of a stone that shines.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    stone = f["stone"]
    return [
        QAItem(
            question=f"What did {child.id} want to do with the {stone.label}?",
            answer=f"{child.id} wanted to marbleize the {stone.label} so it would look bright and special.",
        ),
        QAItem(
            question=f"Why did the {elder.type} warn {child.id} about the wintry day?",
            answer=f"The {elder.type} warned that the cold could make the marble finish turn blotchy and crack before it was done.",
        ),
        QAItem(
            question=f"What did {child.id} and the {elder.type} do instead?",
            answer=f"They warmed the stone by the fire first and then marbleized it close to the hearth, where the cold could not spoil it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is stone?",
            answer="Stone is a hard natural material. People can smooth it, carve it, or paint it, and it lasts a long time.",
        ),
        QAItem(
            question="What does wintry mean?",
            answer="Wintry means cold like winter, with sharp air, frosty mornings, and weather that can make things chill and stiff.",
        ),
        QAItem(
            question="What does it mean to marbleize something?",
            answer="To marbleize something means to make it look like marble, often with pale swirls or shiny streaks.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.type:8}) meters={ {k: v for k, v in e.meters.items() if v} } memes={ {k: v for k, v in e.memes.items() if v} }"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_artifact(A) :- artifact(A).
valid_story(P,A) :- valid_place(P), valid_artifact(A), affords(P, marbleize).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ARTIFACTS:
        lines.append(asp.fact("artifact", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ARTIFACTS[params.artifact], params.name, params.gender, params.elder, params.trait)
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(combos)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("cottage", "stone", "Mira", "girl", "grandmother", "curious"),
            StoryParams("workbench", "tablet", "Rowan", "boy", "grandfather", "patient"),
            StoryParams("hearth", "lantern", "Sora", "girl", "grandmother", "bright"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small fable-style storyworld about an aviary, curiosity, and a wise turn.

Seed tale:
A young finch in an aviary is full of curiosity. It keeps peering at a bright
wind chime beyond the feeder and asking questions instead of eating. The keeper
worries the finch will slip through an open gate, so an older bird shows the
finch how to explore safely from inside the aviary. The finch learns that
curiosity is a gift when it is guided well, and the aviary ends calm and bright.

This script models that premise as a tiny simulated world with physical meters
and emotional memes, then renders a child-facing fable with grounded QA.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    nested: bool = False
    openable: bool = False
    open: bool = False
    risky: bool = False
    safe_view: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "keeper"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name_word(self) -> str:
        return self.label or self.type


@dataclass
class Aviary:
    name: str = "the aviary"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Bird:
    id: str
    species: str
    label: str
    color: str
    role: str  # young bird, elder bird, keeper
    curious: bool = True
    brave: bool = False


@dataclass
class World:
    aviary: Aviary
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
        import copy

        w = World(aviary=copy.deepcopy(self.aviary))
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    bird: str
    elder: str
    keeper: str
    place: str
    object: str
    seed: Optional[int] = None


BIRD_REGISTRY = {
    "finch": Bird(id="finch", species="finch", label="Finch", color="golden", role="young bird", curious=True),
    "robin": Bird(id="robin", species="robin", label="Robin", color="red-breasted", role="young bird", curious=True),
    "sparrow": Bird(id="sparrow", species="sparrow", label="Sparrow", color="brown", role="young bird", curious=True),
}

ELDERS = {
    "owl": Bird(id="owl", species="owl", label="Owl", color="gray", role="elder bird", curious=False),
    "crow": Bird(id="crow", species="crow", label="Crow", color="black", role="elder bird", curious=False),
}

KEEPERS = {
    "keeper": Entity(id="keeper", kind="character", type="keeper", label="the keeper"),
}

OBJECTS = {
    "chime": Entity(
        id="chime",
        type="thing",
        label="wind chime",
        phrase="a bright wind chime",
        risky=True,
        openable=False,
        safe_view=True,
    ),
    "seedbox": Entity(
        id="seedbox",
        type="thing",
        label="seed box",
        phrase="a little seed box",
        risky=False,
        openable=True,
        open=False,
        safe_view=True,
    ),
    "gate": Entity(
        id="gate",
        type="thing",
        label="gate",
        phrase="the aviary gate",
        risky=True,
        openable=True,
        open=True,
        safe_view=False,
    ),
}

PLACES = {
    "aviary": "the aviary",
    "sunny-aviary": "the sunny aviary",
    "garden-aviary": "the aviary beside the garden",
}

BIRD_NAMES = ["Pip", "Milo", "Nia", "Luna", "Tavi", "Rio", "Bea", "Coco"]
KEEPER_NAMES = ["Mara", "Jon", "Iris", "Noah"]
TRAITS = ["curious", "gentle", "bright-eyed", "restless", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for bird in BIRD_REGISTRY:
        for elder in ELDERS:
            for place in PLACES:
                for obj in OBJECTS:
                    if bird in {"finch", "robin", "sparrow"} and obj in {"chime", "seedbox", "gate"}:
                        out.append((bird, elder, place, obj))
    return out


def reasonableness_gate(params: StoryParams) -> None:
    if params.object not in OBJECTS:
        raise StoryError("Unknown object for the aviary tale.")
    if params.bird not in BIRD_REGISTRY:
        raise StoryError("Unknown bird for the aviary tale.")
    if params.elder not in ELDERS:
        raise StoryError("Unknown elder bird for the aviary tale.")
    if params.place not in PLACES:
        raise StoryError("Unknown place for the aviary tale.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(aviary=Aviary(name=PLACES[params.place]))
    bird = BIRD_REGISTRY[params.bird]
    elder = ELDERS[params.elder]
    keeper_name = params.keeper
    young = world.add(Entity(
        id=bird.id,
        kind="character",
        type="bird",
        label=bird.label,
        traits=["young", "curious"],
        meters={"hunger": 0.0, "risk": 0.0, "calm": 0.0},
        memes={"curiosity": 1.0, "joy": 0.5, "restlessness": 0.0},
    ))
    older = world.add(Entity(
        id=elder.id,
        kind="character",
        type="bird",
        label=elder.label,
        traits=["elder", "wise"],
        meters={"calm": 1.0},
        memes={"patience": 1.0, "care": 1.0},
    ))
    keeper = world.add(Entity(
        id="keeper",
        kind="character",
        type="keeper",
        label=keeper_name,
        traits=["careful"],
        meters={"work": 0.0},
        memes={"worry": 0.0, "kindness": 1.0},
    ))
    obj = world.add(OBJECTS[params.object])
    world.facts.update(young=young, older=older, keeper=keeper, obj=obj, place=params.place)
    return world


def predict_risk(world: World, obj_id: str) -> dict:
    sim = world.copy()
    obj = sim.get(obj_id)
    if obj.openable:
        obj.open = True
    risk = 0.0
    if obj.id == "gate" and obj.open:
        risk += 1.0
    if obj.id == "chime":
        risk += 0.5
    return {"risk": risk}


def intro(world: World) -> None:
    bird = world.facts["young"]
    place = world.aviary.name
    world.say(f"{bird.label} lived in {place}, where the air was warm and the twigs were tidy.")
    world.say(f"{bird.pronoun().capitalize()} was a little bird with a very curious heart.")


def desire(world: World) -> None:
    bird = world.facts["young"]
    obj = world.facts["obj"]
    world.say(f"Every day, {bird.label} watched the {obj.label} and wanted to know how it worked.")
    world.say(f"{bird.pronoun().capitalize()} peered, tilted {bird.pronoun('possessive')} head, and asked questions with bright eyes.")


def warning(world: World) -> None:
    bird = world.facts["young"]
    keeper = world.facts["keeper"]
    obj = world.facts["obj"]
    risk = predict_risk(world, obj.id)
    world.facts["predicted_risk"] = risk["risk"]
    if risk["risk"] >= THRESHOLD:
        world.say(
            f"{keeper.label.capitalize()} noticed the open {obj.label} and said, "
            f'"Careful, little one. Curiosity is good, but an open {obj.label} can lead to trouble."'
        )
        keeper.memes["worry"] += 1.0
    else:
        world.say(
            f"{keeper.label.capitalize()} smiled at {bird.label}'s questions, but still kept a close watch."
        )


def restless_turn(world: World) -> None:
    bird = world.facts["young"]
    obj = world.facts["obj"]
    bird.memes["restlessness"] += 1.0
    bird.meters["risk"] += 1.0 if obj.risky else 0.2
    world.say(f"{bird.label} tried to flutter nearer, because wondering made {bird.pronoun('object')} fidgety.")
    if obj.id == "gate" and obj.open:
        world.say(f"One tiny hop brought {bird.label} too close to the open gate.")
    elif obj.id == "chime":
        world.say(f"The bright chime flashed in the sun, and {bird.label} longed to peek outside.")
    else:
        world.say(f"The little seed box looked mysterious, and {bird.label} wanted to inspect it at once.")


def elder_guides(world: World) -> None:
    bird = world.facts["young"]
    older = world.facts["older"]
    obj = world.facts["obj"]
    bird.memes["curiosity"] += 0.5
    older.memes["patience"] += 0.5
    world.say(
        f"{older.label} hopped beside {bird.label} and said, "
        f'"Let your curiosity stay, but let it walk on a safe path."'
    )
    if obj.id == "gate":
        world.say(f"{older.label} showed {bird.label} how to look through the bars without slipping out.")
    elif obj.id == "chime":
        world.say(f"{older.label} pointed out how the wind made the chime sing without anyone poking it.")
    else:
        world.say(f"{older.label} tapped the seed box gently and waited for {bird.label} to watch before opening it.")


def safe_discovery(world: World) -> None:
    bird = world.facts["young"]
    obj = world.facts["obj"]
    keeper = world.facts["keeper"]
    bird.meters["calm"] += 1.0
    bird.memes["joy"] += 1.0
    bird.memes["curiosity"] += 0.5
    keeper.meters["work"] += 0.0
    if obj.id == "gate":
        world.say(f"Then {bird.label} settled on a perch and studied the garden from inside the aviary.")
    elif obj.id == "chime":
        world.say(f"Then {bird.label} listened closely and learned the chime answered the wind, not the beak.")
    else:
        world.say(f"Then {bird.label} discovered the seed box only held food, and the joy was in watching it open.")
    world.say(
        f"By dusk, {bird.label} was calm, {keeper.label} was smiling, and the aviary felt bright and safe again."
    )


ASP_RULES = r"""
bird(B) :- young(B).
elder(E) :- wise(E).
obj(O) :- thing(O).
place(P) :- site(P).

risky(O) :- object_risky(O).
safe_view(O) :- object_safe_view(O).
openable(O) :- object_openable(O).

curious_story(B,E,P,O) :- bird(B), elder(E), place(P), obj(O).
valid_story(B,E,P,O) :- curious_story(B,E,P,O), bird(B), elder(E), place(P), obj(O).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for b in BIRD_REGISTRY.values():
        lines.append(asp.fact("young", b.id))
    for e in ELDERS.values():
        lines.append(asp.fact("wise", e.id))
    for p in PLACES:
        lines.append(asp.fact("site", p))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("thing", oid))
        if o.risky:
            lines.append(asp.fact("object_risky", oid))
        if o.safe_view:
            lines.append(asp.fact("object_safe_view", oid))
        if o.openable:
            lines.append(asp.fact("object_openable", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def tell(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    desire(world)
    world.para()
    warning(world)
    restless_turn(world)
    elder_guides(world)
    world.para()
    safe_discovery(world)
    world.facts["resolved"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    bird = world.facts["young"]
    older = world.facts["older"]
    keeper = world.facts["keeper"]
    obj = world.facts["obj"]
    place = world.aviary.name
    return [
        QAItem(
            question=f"Who lived in {place} and kept staring at the {obj.label}?",
            answer=f"{bird.label}, a curious little bird, lived in {place} and kept staring at the {obj.label}.",
        ),
        QAItem(
            question=f"Why did {keeper.label} worry when {bird.label} got too close?",
            answer=f"{keeper.label} worried because the {obj.label} could be risky, especially if curiosity led {bird.label} toward trouble.",
        ),
        QAItem(
            question=f"How did {older.label} help {bird.label} in the end?",
            answer=f"{older.label} showed {bird.label} a safe way to explore, so {bird.label} could satisfy its curiosity without harm.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {bird.label} was calm and happy, and the aviary felt safe and bright again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an aviary?",
            answer="An aviary is a special place where birds live and can fly, perch, and stay safe.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to find out more about something by looking, asking, and learning.",
        ),
        QAItem(
            question="Why can an open gate be dangerous for a bird?",
            answer="An open gate can be dangerous because a bird might fly out and get lost or enter a place that is not safe.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    bird = world.facts["young"]
    obj = world.facts["obj"]
    place = world.aviary.name
    return [
        f"Write a short fable about {bird.label}, curiosity, and a risky {obj.label} in {place}.",
        f"Tell a child-friendly story where a curious bird learns to explore safely in {place}.",
        f"Write a gentle animal fable ending with a wise lesson about curiosity and safety.",
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.openable:
            bits.append(f"open={e.open}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style aviary storyworld about curiosity.")
    ap.add_argument("--bird", choices=list(BIRD_REGISTRY))
    ap.add_argument("--elder", choices=list(ELDERS))
    ap.add_argument("--keeper", choices=KEEPER_NAMES)
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--object", dest="object_", choices=list(OBJECTS))
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
    filtered = [
        c for c in combos
        if (args.bird is None or c[0] == args.bird)
        and (args.elder is None or c[1] == args.elder)
        and (args.place is None or c[2] == args.place)
        and (args.object_ is None or c[3] == args.object_)
    ]
    if not filtered:
        raise StoryError("No valid aviary story matches the given options.")
    bird, elder, place, obj = rng.choice(filtered)
    keeper = args.keeper or rng.choice(KEEPER_NAMES)
    return StoryParams(bird=bird, elder=elder, keeper=keeper, place=place, object=obj)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(bird="finch", elder="owl", keeper="Mara", place="aviary", object="gate"),
    StoryParams(bird="sparrow", elder="crow", keeper="Iris", place="sunny-aviary", object="chime"),
    StoryParams(bird="robin", elder="owl", keeper="Noah", place="garden-aviary", object="seedbox"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible aviary story combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.bird} / {p.elder} / {p.object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

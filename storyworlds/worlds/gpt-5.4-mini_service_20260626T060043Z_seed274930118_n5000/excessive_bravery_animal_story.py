#!/usr/bin/env python3
"""
Standalone storyworld for an Animal Story about excessive bravery.

Premise:
A small animal wants to do something bold and a little too much.
A worried caretaker stops the animal before the boldness becomes a problem,
then helps turn the brave impulse into a safer, kinder act.

The story model tracks:
- physical state in meters: distance, height, burden, wetness, etc.
- emotional state in memes: courage, fear, pride, worry, trust, relief

The story logic is driven by simulated state, not a frozen template:
the animal pushes too far, the caretaker notices the risk, a safer plan is offered,
and the ending shows what changed.
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
    wears: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0, "height": 0.0, "burden": 0.0, "wet": 0.0}
        if not self.memes:
            self.memes = {"courage": 0.0, "fear": 0.0, "pride": 0.0, "worry": 0.0, "trust": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten", "lioness", "tiger", "rabbit", "mouse", "bird", "fox"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"dog", "puppy", "bear", "boy", "deer", "wolf"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    height_limit: float
    distance_limit: float
    has_water: bool = False
    has_tree: bool = False
    has_stage: bool = False


@dataclass
class BoldAct:
    id: str
    verb: str
    gerund: str
    rush: str
    risk_meter: str
    risk_limit: float
    tension: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    label: str
    prep: str
    safe_verb: str
    safe_gerund: str
    resolves: str
    helps: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        other = World(self.place)
        import copy as _copy
        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


@dataclass
class StoryParams:
    place: str
    act: str
    hero: str
    species: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "barnyard": Place("barnyard", "the barnyard", height_limit=1.2, distance_limit=8.0, has_water=False, has_tree=True),
    "hill": Place("hill", "the hill", height_limit=2.0, distance_limit=12.0, has_water=False, has_tree=True),
    "pond": Place("pond", "the pond", height_limit=1.0, distance_limit=6.0, has_water=True, has_tree=False),
    "stage": Place("stage", "the little stage", height_limit=0.8, distance_limit=4.0, has_water=False, has_tree=False, has_stage=True),
}

ACTS = {
    "climb_tree": BoldAct(
        "climb_tree", "climb the tallest tree", "climbing the tallest tree",
        "dash up the trunk", "height", 1.5, "the branches looked too high and too thin", "tree",
        {"height", "tree"},
    ),
    "race_hill": BoldAct(
        "race_hill", "race down the hill", "racing down the hill",
        "run faster and faster", "distance", 10.0, "the hill was long and steep", "hill",
        {"distance", "hill"},
    ),
    "jump_pond": BoldAct(
        "jump_pond", "jump across the pond rocks", "jumping across the pond rocks",
        "hop onto the farthest stone", "distance", 4.0, "the rocks were slippery and the water was deep below", "pond",
        {"water", "distance"},
    ),
    "sing_stage": BoldAct(
        "sing_stage", "sing louder than the drum", "singing louder than the drum",
        "stand on the tiptoe box and shout", "height", 1.0, "the box wobbled under tiny feet", "stage",
        {"stage", "height"},
    ),
}

RESCUES = {
    "ladder": Rescue(
        "ladder", "a short ladder", "bring a short ladder", "climb", "climbing",
        "the little one could go up only as far as the safe step", "kept brave feet close to the ground",
        {"tree", "height"},
    ),
    "cart": Rescue(
        "cart", "a small cart", "let the cart roll instead", "ride", "riding",
        "the animal still felt fast, but the ground stayed safe", "kept the bold heart moving without a risky sprint",
        {"distance", "hill"},
    ),
    "bridge_stones": Rescue(
        "bridge_stones", "the stepping stones", "choose the stepping stones", "cross", "crossing",
        "the hops stayed small and steady", "kept the brave paws above the water without a wild leap",
        {"water", "distance"},
    ),
    "song_box": Rescue(
        "song_box", "the low song box", "step down from the box and sing from the floor", "sing", "singing",
        "the voice stayed bright and the box stayed unshaken", "kept the performance brave without the wobble",
        {"stage", "height"},
    ),
}

NAMES = {
    "cat": ["Mimi", "Nala", "Tilly", "Pip"],
    "dog": ["Rufus", "Benny", "Otis", "Marlow"],
    "rabbit": ["Poppy", "Clover", "Moss", "Wren"],
    "fox": ["Fiona", "Sunny", "Saffy", "Kiki"],
}
TRAITS = ["brave", "curious", "lively", "determined", "fearless"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in PLACES.values():
        for act in ACTS.values():
            if place.id in act.tags or act.tags & {"distance", "water", "stage", "tree", "hill"}:
                for rescue in RESCUES.values():
                    if act.tags & rescue.tags:
                        out.append((place.id, act.id))
    return sorted(set(out))


def choose_rescue(act: BoldAct) -> Optional[Rescue]:
    for rescue in RESCUES.values():
        if act.tags & rescue.tags:
            return rescue
    return None


def tell(place: Place, act: BoldAct, hero_name: str, species: str, caretaker_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=species, label=hero_name))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=caretaker_type, label=caretaker_type))
    rescue = choose_rescue(act)

    if rescue is None:
        raise StoryError("No safe rescue exists for that brave act.")

    world.facts.update(hero=hero, caretaker=caretaker, act=act, place=place, rescue=rescue)

    # Act 1
    world.say(f"{hero_name} was a little {trait} {species} who loved trying bold things.")
    world.say(f"{hero_name} liked {act.gerund}, because it made the world feel huge and exciting.")
    world.say(f"One day, {hero_name} went to {place.label} with {caretaker_type}.")

    # Act 2
    world.para()
    hero.memes["courage"] += 1
    hero.memes["pride"] += 1
    world.say(f"{hero_name} wanted to {act.verb}, and {hero.pronoun('possessive')} tail twitched with excitement.")
    if act.risk_meter == "height":
        hero.meters["height"] += 1.6
    else:
        hero.meters["distance"] += 10.5
    world.say(f"{hero_name} tried to {act.rush}, but {act.tension}.")
    caretaker.memes["worry"] += 1
    world.say(f"{caretaker_type.capitalize()} watched closely and said, \"That is a little too much bravery.\"")

    # Risk check
    risky = False
    if act.risk_meter == "height":
        risky = hero.meters["height"] > place.height_limit
    elif act.risk_meter == "distance":
        risky = hero.meters["distance"] > place.distance_limit

    if risky:
        world.say(f"{hero_name} paused, because the risky way could end in a tumble or a splash.")
    else:
        world.say(f"{hero_name} noticed the danger before it got worse.")

    # Act 3
    world.para()
    world.say(f"{caretaker_type.capitalize()} offered {rescue.label} and said, \"Let's {rescue.prep}.\"")
    hero.memes["trust"] += 1
    hero.memes["fear"] += 0.5
    world.say(f"{hero_name} listened, took a breath, and chose the safer plan.")
    world.say(f"Then {hero_name} could {rescue.safe_verb} while still feeling bold.")
    hero.memes["relief"] += 1
    caretaker.memes["relief"] += 1
    caretaker.memes["worry"] = 0.0

    if act.risk_meter == "height":
        hero.meters["height"] = min(hero.meters["height"], place.height_limit)
    else:
        hero.meters["distance"] = min(hero.meters["distance"], place.distance_limit)

    world.say(f"In the end, {hero_name} was still brave, but the brave choice was a careful one.")
    world.say(f"{hero_name} smiled at {caretaker_type} from the safe side of the {place.label}.")
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Animal Story about "{f["act"].keyword}" and excessive bravery.',
        f"Tell a gentle story where {f['hero'].id} wants to {f['act'].verb}, but the {f['caretaker'].type} helps keep the bravery safe.",
        f"Write a child-friendly story about a small animal at {f['place'].label} who learns that brave does not have to mean too wild.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    caretaker = f["caretaker"]
    act = f["act"]
    place = f["place"]
    rescue = f["rescue"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place.label}?",
            answer=f"{hero.id} wanted to {act.verb}. {hero.id} felt excited because the idea seemed brave and big.",
        ),
        QAItem(
            question=f"Why did {caretaker.label} worry about {hero.id}?",
            answer=f"{caretaker.label} worried because {act.tension}, so the bold plan was too risky to do without help.",
        ),
        QAItem(
            question=f"How did {caretaker.label} help {hero.id} stay safe?",
            answer=f"{caretaker.label} offered {rescue.label} and suggested a safer way. That let {hero.id} keep the brave feeling without the dangerous part.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means trying to do something hard or scary, even when your heart feels jumpy, while still trying to make a safe choice.",
        ),
        QAItem(
            question="Why can too much bravery be a problem?",
            answer="Too much bravery can be a problem if someone ignores danger and gets hurt. Brave actions are best when they are also careful.",
        ),
        QAItem(
            question="What is a safer way to be brave?",
            answer="A safer way to be brave is to ask for help, use the right tool, or choose a smaller step that still helps you learn and try.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world about excessive bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTS)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=sorted(NAMES))
    ap.add_argument("--caretaker", choices=["mother", "father", "aunt", "uncle", "owl", "goat"])
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if not combos:
        raise StoryError("No valid story matches the chosen place or activity.")
    place_id, act_id = rng.choice(combos)
    act = ACTS[act_id]
    species = args.species or rng.choice(list(NAMES))
    hero = args.name or rng.choice(NAMES[species])
    caretaker = args.caretaker or rng.choice(["mother", "father", "aunt", "uncle", "owl", "goat"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place_id, act=act_id, hero=hero, species=species, caretaker=caretaker, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTS[params.act], params.hero, params.species, params.caretaker, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
place(P) :- setting(P).
act(A) :- action(A).
rescue(R) :- fix(R).

risky(A,P) :- action(A), setting(P), height_risk(A,H), height_limit(P,L), H>L.
risky(A,P) :- action(A), setting(P), distance_risk(A,D), distance_limit(P,L), D>L.

safe(A,R) :- risky(A,P), fix(R), matches(R,A).
valid_story(P,A,R) :- risky(A,P), safe(A,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("setting", p.id))
        lines.append(asp.fact("height_limit", p.id, int(p.height_limit * 10)))
        lines.append(asp.fact("distance_limit", p.id, int(p.distance_limit * 10)))
    for a in ACTS.values():
        lines.append(asp.fact("action", a.id))
        if a.risk_meter == "height":
            lines.append(asp.fact("height_risk", a.id, int(a.risk_limit * 10)))
        else:
            lines.append(asp.fact("distance_risk", a.id, int(a.risk_limit * 10)))
    for r in RESCUES.values():
        lines.append(asp.fact("fix", r.id))
        for tag in sorted(r.tags):
            lines.append(asp.fact("matches", r.id, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, a) for p, a in valid_combos()}
    asp_set = {(p, a) for p, a, _ in asp_valid_combos()}
    if python_set == asp_set:
        print(f"OK: ASP matches Python for {len(python_set)} valid combos.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only python:", sorted(python_set - asp_set))
    print("only ASP:", sorted(asp_set - python_set))
    return 1


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        triples = asp_valid_combos()
        for t in triples:
            print(t)
        return

    samples: list[StorySample] = []
    if args.all:
        for place_id, act_id in sorted(valid_combos()):
            params = StoryParams(
                place=place_id,
                act=act_id,
                hero=NAMES["cat"][0],
                species="cat",
                caretaker="mother",
                trait="brave",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

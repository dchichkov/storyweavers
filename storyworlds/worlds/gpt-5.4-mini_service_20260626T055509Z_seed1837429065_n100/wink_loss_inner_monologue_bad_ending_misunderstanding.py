#!/usr/bin/env python3
"""
A small Adventure storyworld about a brave child, a wink, a loss, and a
misunderstanding that turns into a bad ending.

The world is intentionally tiny and constraint-driven:
- a hero explores a place
- someone winks, but the hero misreads it
- the hero follows the wrong signal
- a useful item is lost
- the story ends with a clear, child-facing consequence

The prose is not a frozen template: it is driven by the world state and the
simulated causal turn from misunderstanding to loss.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    portable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "guide"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    hazards: set[str] = field(default_factory=set)
    hides: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    risk: str
    lost_by: str = ""
    found_by: str = ""
    portable: bool = True


@dataclass
class Cue:
    id: str
    label: str
    action: str
    meaning: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.cues: dict[str, Cue] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

    def add_cue(self, cue: Cue) -> Cue:
        self.cues[cue.id] = cue
        return cue

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    guide_name: str
    clue: str
    loss: str
    seed: Optional[int] = None


PLACES = {
    "cave": Place(id="cave", label="the mossy cave", hazards={"dark"}, hides={"echo"}),
    "harbor": Place(id="harbor", label="the windy harbor", hazards={"waves"}, hides={"fog"}),
    "forest": Place(id="forest", label="the pine forest", hazards={"branches"}, hides={"shadow"}),
    "ruins": Place(id="ruins", label="the old stone ruins", hazards={"crumbles"}, hides={"echo"}),
}

HERO_NAMES = ["Mila", "Ari", "Noah", "Tia", "Jules", "Pip", "Lina", "Koa"]
GUIDE_NAMES = ["Captain Rose", "Old Finn", "Mara", "Scout Ben", "Nia", "Tom"]

LOSS_ITEMS = {
    "map": Item(id="map", label="map", phrase="a folded trail map", risk="lost"),
    "lantern": Item(id="lantern", label="lantern", phrase="a little brass lantern", risk="broken"),
    "key": Item(id="key", label="key", phrase="a small iron key", risk="lost"),
    "rope": Item(id="rope", label="rope", phrase="a coil of rope", risk="snagged"),
}

CLUES = {
    "wink": Cue(id="wink", label="wink", action="winked", meaning="follow me"),
    "nod": Cue(id="nod", label="nod", action="nodded", meaning="be careful"),
    "point": Cue(id="point", label="point", action="pointed", meaning="look there"),
}

TRAITS = ["curious", "brave", "restless", "eager", "careful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure world with a wink, a loss, and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--loss", choices=LOSS_ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def reasonableness_gate(place: Place, clue: Cue, loss: Item) -> bool:
    return clue.id == "wink" and loss.id in {"map", "key", "lantern", "rope"} and place.id in PLACES


def explanation(place: Place, clue: Cue, loss: Item) -> str:
    return (
        f"(No story: this tiny adventure needs a wink to be misunderstood and a real loss to follow, "
        f"but {loss.label} at {place.label} with a {clue.label} does not make a strong enough turn.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place or rng.choice(list(PLACES))
    clue_id = args.clue or "wink"
    loss_id = args.loss or rng.choice(list(LOSS_ITEMS))
    place = PLACES[place_id]
    clue = CLUES[clue_id]
    loss = LOSS_ITEMS[loss_id]

    if not reasonableness_gate(place, clue, loss):
        raise StoryError(explanation(place, clue, loss))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    return StoryParams(
        place=place_id,
        hero_name=name,
        hero_type=gender,
        guide_name=guide,
        clue=clue_id,
        loss=loss_id,
    )


def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add_entity(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    guide = world.add_entity(Entity(id=params.guide_name, kind="character", type="guide"))
    item = world.add_item(LOSS_ITEMS[params.loss])
    cue = world.add_cue(CLUES[params.clue])
    world.facts.update(hero=hero, guide=guide, item=item, cue=cue, place=world.place, params=params)
    return world


def intro(world: World) -> None:
    hero: Entity = world.facts["hero"]
    guide: Entity = world.facts["guide"]
    item: Item = world.facts["item"]
    place: Place = world.facts["place"]
    world.say(
        f"{hero.id} was a {random.choice(TRAITS)} little {hero.type} who loved adventure."
    )
    world.say(
        f"One day, {hero.id} and {guide.id} went to {place.label}, and {hero.id} carried {item.phrase}."
    )
    world.say(
        f"{hero.id} kept the {item.label} close because {item.label}s were important on a trail like this."
    )


def misunderstanding(world: World) -> None:
    hero: Entity = world.facts["hero"]
    guide: Entity = world.facts["guide"]
    cue: Cue = world.facts["cue"]
    item: Item = world.facts["item"]
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"In the middle of the trail, {guide.id} {cue.action} at a side path, but {hero.id} read it the wrong way."
    )
    hero.memes["misunderstanding"] = hero.memes.get("misunderstanding", 0) + 1
    world.say(
        f"In {hero.id}'s head, that wink meant, '{cue.meaning},' so {hero.id} hurried after it."
    )
    if item.id == "map":
        world.say(f"{hero.id} tucked the {item.label} away without checking it again.")
    elif item.id == "key":
        world.say(f"{hero.id} shook the {item.label} and thought the path would be easy.")
    else:
        world.say(f"{hero.id} kept trusting the {item.label} to solve trouble later.")


def lose_item(world: World) -> None:
    hero: Entity = world.facts["hero"]
    guide: Entity = world.facts["guide"]
    item: Item = world.facts["item"]
    place: Place = world.facts["place"]
    if item.id in world.fired:
        return
    world.fired.add((item.id, "lost"))
    if item.id == "map":
        world.say(
            f"The side path bent through the {place.label} and the wind flipped the map open, then it slipped away."
        )
    elif item.id == "key":
        world.say(
            f"The stones were slick, and when {hero.id} reached for the key, it bounced into a crack."
        )
    elif item.id == "lantern":
        world.say(
            f"The dark swallowed the little light, and the lantern bumped hard enough to go out."
        )
    else:
        world.say(
            f"The rope snagged on a root, and when {hero.id} tugged, a whole coil vanished into the brush."
        )
    item.lost_by = hero.id
    hero.memes["loss"] = hero.memes.get("loss", 0) + 1
    guide.memes["alarm"] = guide.memes.get("alarm", 0) + 1
    world.say(f"{guide.id} called for {hero.id}, but the wrong path was already pulling them apart.")


def ending(world: World) -> None:
    hero: Entity = world.facts["hero"]
    guide: Entity = world.facts["guide"]
    item: Item = world.facts["item"]
    place: Place = world.facts["place"]
    hero.memes["sadness"] = hero.memes.get("sadness", 0) + 1
    world.say(
        f"{hero.id} looked back and felt a tight knot in the chest: the wink had not meant what was hoped."
    )
    world.say(
        f"By the time {hero.id} found {guide.id} again, the {item.label} was gone for good."
    )
    world.say(
        f"They had to turn home from {place.label} with empty hands, and the trail stayed quiet behind them."
    )
    world.say(
        f"It was a bad ending for the little expedition, because the misunderstanding had cost them the {item.label}."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    world.para()
    misunderstanding(world)
    lose_item(world)
    world.para()
    ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    item: Item = world.facts["item"]
    place: Place = world.facts["place"]
    return [
        f"Write an adventure story for a young child about a {p.hero_type} named {p.hero_name} at {place.label} that includes a wink and a loss.",
        f"Tell a short story where a guide's wink is misunderstood and {item.phrase} gets lost during the trip.",
        f"Create a child-friendly adventure with a bad ending, inner monologue, and a misunderstanding on the trail.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    item: Item = world.facts["item"]
    place: Place = world.facts["place"]
    hero: Entity = world.facts["hero"]
    guide: Entity = world.facts["guide"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {guide.id} go on their adventure?",
            answer=f"They went to {place.label}.",
        ),
        QAItem(
            question=f"What did {guide.id} do that {hero.id} misunderstood?",
            answer=f"{guide.id} {world.facts['cue'].action} to send a signal, but {hero.id} misunderstood it as a different message.",
        ),
        QAItem(
            question=f"What was lost in the story?",
            answer=f"{item.phrase.capitalize()} was lost during the trip.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=f"The ending was bad because the misunderstanding led to the loss of the {item.label}, and they had to go home without it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wink?",
            answer="A wink is when someone briefly closes one eye as a signal or a joke.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a message means one thing, but it really means something else.",
        ),
        QAItem(
            question="What does loss mean?",
            answer="Loss means something you had is gone, broken, or not available anymore.",
        ),
    ]


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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} memes={dict(e.memes)}")
    for item in world.items.values():
        lines.append(f"{item.id}: label={item.label} lost_by={item.lost_by}")
    return "\n".join(lines)


ASP_RULES = r"""
cue(wink).
loss(map;key;lantern;rope).

misunderstanding(H) :- cue(wink), hero(H).
lost_item(I) :- loss(I), misunderstanding(_).
bad_ending :- lost_item(_), misunderstanding(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for h in sorted(p.hazards):
            lines.append(asp.fact("hazard", pid, h))
    for cid, c in CLUES.items():
        lines.append(asp.fact("cue", cid))
    for iid, i in LOSS_ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("risk", iid, i.risk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/0."))
    has_bad = any(sym.name == "bad_ending" for sym in model)
    py = True
    if has_bad == py:
        print("OK: ASP and Python agree on the bad-ending gate.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


CURATED = [
    StoryParams(place="forest", hero_name="Mila", hero_type="girl", guide_name="Captain Rose", clue="wink", loss="map"),
    StoryParams(place="cave", hero_name="Ari", hero_type="boy", guide_name="Old Finn", clue="wink", loss="key"),
    StoryParams(place="harbor", hero_name="Tia", hero_type="girl", guide_name="Mara", clue="wink", loss="lantern"),
]


def generate(params: StoryParams) -> StorySample:
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.clue != "wink":
        raise StoryError("This world only supports a wink as the misleading signal.")
    if args.place and args.loss:
        place = PLACES[args.place]
        loss = LOSS_ITEMS[args.loss]
        if not reasonableness_gate(place, CLUES["wink"], loss):
            raise StoryError(explanation(place, CLUES["wink"], loss))
    place = args.place or rng.choice(list(PLACES))
    loss = args.loss or rng.choice(list(LOSS_ITEMS))
    params = StoryParams(
        place=place,
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_type=args.gender or rng.choice(["girl", "boy"]),
        guide_name=args.guide or rng.choice(GUIDE_NAMES),
        clue="wink",
        loss=loss,
    )
    return params


def build_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        print(build_json(samples))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.place} / {p.loss}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

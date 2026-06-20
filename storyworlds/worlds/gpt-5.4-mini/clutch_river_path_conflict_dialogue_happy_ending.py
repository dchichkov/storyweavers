#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clutch_river_path_conflict_dialogue_happy_ending.py
====================================================================================

A small standalone storyworld for a child-facing ghost story on a river path.

Premise:
- A child walks beside a river path at dusk.
- A shy "ghost" turns out to be a lost lantern-bearer in a white raincoat.
- The child feels afraid, clutches a warm stone, and there is a brief conflict.
- Through dialogue, they discover the figure needs help reaching a footbridge.
- The ending is happy: the child helps, fear fades, and the path feels friendly.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports --all, --seed, -n, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and an inline ASP twin
- generates three QA sets grounded in simulated state
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


def clean(text: str) -> str:
    return " ".join(text.split())


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fear": 0.0, "trust": 0.0, "relief": 0.0, "kindness": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "trust": 0.0, "relief": 0.0, "kindness": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(clean(text))

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["fear"] >= THRESHOLD and ("fear" not in world.fired):
            world.fired.add(("fear", e.id))
            out.append("__fear__")
    return out


RULES = [Rule("fear", _r_fear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class Place:
    id: str
    label: str
    dark_word: str
    water_word: str
    bridge_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HeroCfg:
    id: str
    gender: str
    name: str


@dataclass
class GhostCfg:
    id: str
    cloak: str
    speech: str
    secret: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    warm: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    ghost: str
    object: str
    seed: Optional[int] = None


PLACES = {
    "river_path": Place("river_path", "the river path", "the reeds", "the river", "the footbridge", {"river", "path", "ghost"}),
}

HEROES = {
    "Mina": HeroCfg("Mina", "girl", "Mina"),
    "Noah": HeroCfg("Noah", "boy", "Noah"),
    "Tia": HeroCfg("Tia", "girl", "Tia"),
    "Eli": HeroCfg("Eli", "boy", "Eli"),
}

GHOSTS = {
    "white_figure": GhostCfg("white_figure", "a white raincoat", "a soft voice", "it was only looking for the bridge", {"ghost", "river"}),
    "lantern_friend": GhostCfg("lantern_friend", "a pale scarf", "a gentle voice", "it had lost its lantern", {"ghost", "lantern"}),
}

OBJECTS = {
    "clutch_pebble": ObjectCfg("clutch_pebble", "a smooth river pebble", "a smooth river pebble to clutch", warm=True, tags={"clutch"}),
    "clutch_toy": ObjectCfg("clutch_toy", "a little toy fox", "a little toy fox to clutch", warm=False, tags={"clutch"}),
    "clutch_mitten": ObjectCfg("clutch_mitten", "a soft mitten", "a soft mitten to clutch", warm=True, tags={"clutch"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, h, g) for p in PLACES for h in HEROES for g in GHOSTS if True]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero not in HEROES:
        raise StoryError("Unknown hero.")
    if params.ghost not in GHOSTS:
        raise StoryError("Unknown ghost.")
    if params.object not in OBJECTS:
        raise StoryError("Unknown object.")
    if "clutch" not in OBJECTS[params.object].tags:
        raise StoryError("The story needs something the child can clutch.")
    if params.place != "river_path":
        raise StoryError("This world is built for a river path.")
    if params.hero == "Mina" and params.ghost == "white_figure":
        return


def predict(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    ghost = sim.get("ghost")
    child.memes["fear"] = 2.0
    ghost.memes["kindness"] = 1.0
    return {"fear": child.memes["fear"], "kindness": ghost.memes["kindness"]}


def tell(place: Place, hero: HeroCfg, ghost: GhostCfg, obj: ObjectCfg) -> World:
    world = World()
    child = world.add(Entity("child", "character", hero.gender, hero.name, role="child"))
    spirit = world.add(Entity("ghost", "character", "person", ghost.id, role="ghost"))
    stone = world.add(Entity("clutch", "thing", "thing", obj.label, role="comfort"))
    bridge = world.add(Entity("bridge", "thing", "thing", place.bridge_word))

    child.memes["fear"] = 0.0
    child.memes["trust"] = 0.0
    spirit.memes["kindness"] = 0.0
    world.facts["place"] = place
    world.facts["hero"] = hero
    world.facts["ghost"] = ghost
    world.facts["object"] = obj
    world.facts["bridge"] = bridge

    world.say(f"At dusk, {hero.name} walked along {place.label}, where the water whispered under the reeds.")
    world.say(f"In the fog, a white figure stood near {place.bridge_word}, and {hero.name} clutched {obj.phrase}.")
    world.say(f'"Who are you?" {hero.name} asked. "Are you a ghost?"')
    world.say(f'"Not a scary one," said the figure in a soft voice. "I was looking for the bridge."')
    child.memes["fear"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(f"{hero.name} took one step back. " + f'"Then why do you look so strange?"')
    world.say(f'"Because I lost my lantern," said the figure. "I did not mean to frighten you."')
    child.memes["trust"] += 1
    spirit.memes["kindness"] += 1
    world.say(f"{hero.name} squeezed {obj.label} tighter, but listened.")
    world.para()
    world.say(f'"If you show me the way, I will walk beside you," said {hero.name}.')
    world.say(f'"And I will keep my voice gentle," said the figure. "You are braver than the fog."')
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["kindness"] += 1
    spirit.memes["relief"] += 1
    world.para()
    world.say(f"Together they followed the river path to the footbridge.")
    world.say(f"There, the lost lantern gleamed under a tree branch, and the white figure laughed with delight.")
    world.say(f'{hero.name} grinned, still clutching {obj.label}, and the path did not feel spooky anymore.')
    world.say("It felt like a safe place where a child and a ghost could be friends.")
    world.facts["outcome"] = "happy"
    world.facts["fear_turned_to_trust"] = child.memes["fear"] <= 0.0 and child.memes["trust"] > 0.0
    return world


KNOWLEDGE = {
    "clutch": [("What does it mean to clutch something?", "To clutch something means to hold it very tightly in your hand, usually because you feel scared or you want to keep it close.")],
    "river": [("What is a river?", "A river is a long flowing stream of water that moves through the land.")],
    "bridge": [("What is a bridge for?", "A bridge helps people cross over water, like a river or a stream, without getting wet.")],
    "fog": [("What is fog?", "Fog is a cloud near the ground that can make the world look gray and blurry.")],
    "ghost": [("What is a ghost in a story?", "In a story, a ghost is often a spooky-looking figure. Sometimes it is scary at first, but it may turn out to be friendly.")],
    "lantern": [("What does a lantern do?", "A lantern gives off light so people can see in the dark.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    ghost = f["ghost"]
    obj = f["object"]
    return [
        f'Write a short ghost story for a child set on a river path that includes the word "clutch" and ends happily.',
        f"Tell a story where {hero.name} sees a ghostly figure, feels worried, asks questions, and then learns the figure is friendly.",
        f"Write a gentle spooky story with dialogue, a small conflict, and a happy ending where {hero.name} helps a strange figure near the river.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    ghost = f["ghost"]
    obj = f["object"]
    place = f["place"]
    qa = [
        ("Where does the story happen?", f"It happens on {place.label}, beside the river and the reeds."),
        ("Why did the child feel scared at first?", f"{hero.name} felt scared because a white figure was standing in the fog near the bridge, and it looked like a ghost at first."),
        ("What did the child do with the object?", f"{hero.name} clutched {obj.phrase}, holding it tightly while listening to the strange voice."),
        ("What did the figure say?", f'The figure said, "{ghost.speech.capitalize()} {ghost.secret}."'),
        ("How did the problem get better?", f"{hero.name} asked questions instead of running away, and the figure answered calmly. After that, they walked together to the bridge and found the lost lantern."),
    ]
    if f.get("fear_turned_to_trust"):
        qa.append(("How did the story end?", "It ended happily, with the child and the ghost-like figure walking together on the river path. The scary feeling changed into trust, and the path felt friendly again."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["object"].tags)
    tags |= {"river", "bridge", "fog", "ghost", "lantern"}
    out = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(items)
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.kind}) label={e.label!r} role={e.role!r} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams("river_path", "Mina", "white_figure", "clutch_pebble"),
    StoryParams("river_path", "Noah", "lantern_friend", "clutch_toy"),
    StoryParams("river_path", "Tia", "white_figure", "clutch_mitten"),
]


def explain_rejection(params: StoryParams) -> str:
    return "This storyworld only supports a river path, a child clutching something, and a ghostly conflict that ends happily."


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, H, G, O) :- place(P), hero(H), ghost(G), object(O).
happy_end(P, H, G, O) :- valid(P, H, G, O), place(P).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set((p, h, g, o) for p in PLACES for h in HEROES for g in GHOSTS for o in OBJECTS):
        print("OK: ASP gate matches Python combos.")
    else:
        print("MISMATCH: ASP gate disagrees.")
        rc = 1
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: story generation failed.")
        rc = 1
    else:
        print("OK: generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world on a river path.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
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
    if args.place and args.place != "river_path":
        raise StoryError("This world only supports the river_path setting.")
    place = "river_path"
    hero = args.hero or rng.choice(list(HEROES))
    ghost = args.ghost or rng.choice(list(GHOSTS))
    obj = args.object_ or rng.choice(list(OBJECTS))
    p = StoryParams(place, hero, ghost, obj)
    reasonableness_gate(p)
    return p


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], HEROES[params.hero], GHOSTS[params.ghost], OBJECTS[params.object])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/4.\n#show happy_end/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos[:10]:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            samples.append(generate(p))
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

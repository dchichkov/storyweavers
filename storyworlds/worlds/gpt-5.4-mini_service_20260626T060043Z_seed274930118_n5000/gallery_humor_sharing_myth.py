#!/usr/bin/env python3
"""
storyworlds/worlds/gallery_humor_sharing_myth.py
=================================================

A small mythic story world about a gallery, a joke, and a sharing choice.

Premise:
A young helper arrives at a gallery with one bright, funny thing they love.
A proud figure wants to keep it for themselves, but the gallery is a place
where stories and objects can be shared. The tension comes from wanting to
keep the delight and also let others enjoy it.

The world model tracks:
- physical state in meters: where the object is, whether it is displayed,
  whether it is safely handled, and whether a room feels crowded or calm
- emotional state in memes: pride, delight, generosity, envy, and warmth

The turn:
A small mishap or boast makes the keeper notice that laughter grows when
it is shared. A companion suggests a way to let the room enjoy the humor
without losing the treasured thing.

Resolution:
The object is shared in a careful way, the room brightens, and the ending
image proves the change: the gallery holds laughter, not possession.

This script follows the Storyweavers contract:
- standalone stdlib script
- StoryParams and registries
- build_parser, resolve_params, generate, emit, main
- lazy ASP helper import inside ASP functions
- inline ASP_RULES twin and Python reasonableness gate
- StoryError for invalid explicit choices
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    displayed_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Gallery:
    name: str
    mood: str
    rooms: list[str]
    allows_laughter: bool = True


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    style: str
    humor_kind: str
    display_room: str
    can_share: bool = True
    fragile_pride: bool = False


@dataclass
class SharingTool:
    id: str
    label: str
    method: str
    protects: set[str]
    helps: set[str]


class World:
    def __init__(self, gallery: Gallery) -> None:
        self.gallery = gallery
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        c = World(self.gallery)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
GALLERIES = {
    "moonhall": Gallery(name="Moon Hall", mood="quiet", rooms=["foyer", "lantern room", "echo chamber"]),
    "sunarchive": Gallery(name="Sun Archive", mood="bright", rooms=["front room", "long hall", "story alcove"]),
    "rivergallery": Gallery(name="River Gallery", mood="gentle", rooms=["entry court", "glass room", "garden wall"]),
}

ARTIFACTS = {
    "laughing_mask": Artifact(
        id="laughing_mask",
        label="laughing mask",
        phrase="a golden mask with a grin carved into it",
        style="mythic",
        humor_kind="joke",
        display_room="foyer",
        can_share=True,
        fragile_pride=True,
    ),
    "jingle_bell": Artifact(
        id="jingle_bell",
        label="jingle bell",
        phrase="a bright bell that giggled when it was tapped",
        style="mythic",
        humor_kind="rhyme",
        display_room="long hall",
        can_share=True,
        fragile_pride=False,
    ),
    "mirror_card": Artifact(
        id="mirror_card",
        label="mirror card",
        phrase="a polished card that turned every frown into a silly face",
        style="mythic",
        humor_kind="trick",
        display_room="story alcove",
        can_share=True,
        fragile_pride=True,
    ),
}

TOOLS = [
    SharingTool(
        id="open_lantern",
        label="an open lantern",
        method="let the light spill so everyone could see the joke at once",
        protects={"gentle"},
        helps={"share"},
    ),
    SharingTool(
        id="small_stage",
        label="a small stone stage",
        method="set the object where many hands could point and many voices could laugh",
        protects={"careful"},
        helps={"share"},
    ),
    SharingTool(
        id="story_circle",
        label="a story circle",
        method="sit in a ring and pass the tale from one mouth to the next",
        protects={"warm"},
        helps={"share"},
    ),
]

NAMES = ["Mira", "Niko", "Ari", "Lina", "Taro", "Sera", "Pia", "Kian"]
KINDS = ["girl", "boy"]
ROLES = ["mother", "father", "aunt", "uncle", "elder"]
TRAITS = ["curious", "proud", "gentle", "bright", "mischievous", "thoughtful"]


@dataclass
class StoryParams:
    gallery: str
    artifact: str
    name: str
    kind: str
    role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def artifact_at_risk(artifact: Artifact) -> bool:
    return artifact.can_share and artifact.fragile_pride


def select_tool(artifact: Artifact) -> Optional[SharingTool]:
    if not artifact_at_risk(artifact):
        return None
    return TOOLS[0] if artifact.humor_kind in {"joke", "trick"} else TOOLS[1]


def explain_rejection(artifact: Artifact) -> str:
    return (
        f"(No story: {artifact.label} does not create the right kind of tension for a mythic gallery tale. "
        f"Choose a shareable, pride-fragile object that can be protected by a gentle way of sharing.)"
    )


# ---------------------------------------------------------------------------
# Mythic causal world
# ---------------------------------------------------------------------------
def world_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def world_meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def raise_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def raise_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []

    for actor in world.characters():
        if world_meme(actor, "boast") >= 1 and ("crowd", actor.id) not in world.fired:
            world.fired.add(("crowd", actor.id))
            raise_meter(actor, "lonely", 1.0)
            out.append(f"{actor.id}'s boast made the room feel small for a moment.")

        if world_meme(actor, "share") >= 1 and ("warmth", actor.id) not in world.fired:
            world.fired.add(("warmth", actor.id))
            raise_meme(actor, "delight", 1.0)
            out.append(f"Their sharing made the gallery feel warmer.")

    if narrate:
        for s in out:
            world.say(s)
    return out


def present_artifact(world: World, hero: Entity, artifact: Entity, gallery: Gallery) -> None:
    artifact.displayed_in = gallery.rooms[0]
    raise_meme(hero, "pride", 1.0)
    world.say(
        f"{hero.id} kept {hero.pronoun('possessive')} {artifact.label} safe in the {gallery.name}, "
        f"as if the room itself were holding a secret."
    )


def gather(world: World, hero: Entity, elder: Entity, gallery: Gallery) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {elder.type} walked into {gallery.name}, "
        f"where the walls waited like patient old ears."
    )
    world.say(
        f"{gallery.name} was {gallery.mood}, and the rooms seemed ready for a story."
    )


def want_to_keep(world: World, hero: Entity, artifact: Entity) -> None:
    raise_meme(hero, "possessive", 1.0)
    world.say(
        f"{hero.id} loved the {artifact.label} and wanted the laughter all to "
        f"{hero.pronoun('object')}, not to the rest of the hall."
    )


def warning(world: World, elder: Entity, hero: Entity, artifact: Entity) -> None:
    raise_meme(hero, "worry", 1.0)
    world.say(
        f'"A joke that stays in one hand gets small," {elder.pronoun("subject")} said. '
        f'"A shared joke can shine on every face."'
    )


def boast_turn(world: World, hero: Entity, artifact: Entity) -> None:
    raise_meme(hero, "boast", 1.0)
    world.say(
        f"{hero.id} tried to keep the {artifact.label} hidden, but the hiding made "
        f"the joke feel heavier than stone."
    )
    propagate(world)


def offer_share(world: World, elder: Entity, hero: Entity, tool: SharingTool) -> None:
    raise_meme(hero, "share", 1.0)
    world.say(
        f"{elder.id} lifted {tool.label} and showed {hero.id} {tool.method}."
    )


def accept_share(world: World, hero: Entity, artifact: Entity, tool: SharingTool) -> None:
    raise_meme(hero, "joy", 1.0)
    raise_meme(hero, "generosity", 1.0)
    hero.memes["possessive"] = 0.0
    artifact.carried_by = None
    world.say(
        f"{hero.id} finally nodded. Together they used {tool.label}, and the {artifact.label} could be seen by all."
    )
    world.say(
        f"The room filled with laughter, and {hero.id} learned that a gift grows when it travels."
    )


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------
def tell(gallery: Gallery, artifact_cfg: Artifact, hero_name: str, kind: str, role: str, trait: str) -> World:
    world = World(gallery)
    hero = world.add(Entity(id=hero_name, kind="character", type=kind, memes={"pride": 0.0, "possessive": 0.0, "joy": 0.0}))
    elder = world.add(Entity(id="elder", kind="character", type=role, label=f"the {role}", memes={"wisdom": 1.0}))
    artifact = world.add(Entity(
        id=artifact_cfg.id,
        kind="thing",
        type="artifact",
        label=artifact_cfg.label,
        phrase=artifact_cfg.phrase,
        owner=hero.id,
        carried_by=hero.id,
        displayed_in=artifact_cfg.display_room,
        meters={"clean": 1.0},
    ))

    world.say(
        f"There was once {hero.id}, a {trait} {kind}, who found {artifact.phrase}."
    )
    present_artifact(world, hero, artifact, gallery)
    world.para()
    gather(world, hero, elder, gallery)
    want_to_keep(world, hero, artifact)
    warning(world, elder, hero, artifact)
    boast_turn(world, hero, artifact)
    world.para()

    tool = select_tool(artifact_cfg)
    if tool:
        offer_share(world, elder, hero, tool)
        accept_share(world, hero, artifact, tool)

    world.facts.update(
        hero=hero,
        elder=elder,
        artifact=artifact,
        gallery=gallery,
        tool=tool,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    artifact = f["artifact"]
    gallery = f["gallery"]
    return [
        f'Write a short mythic story about a {hero.type} named {hero.id} in {gallery.name} who wants to keep a funny treasure to {hero.pronoun("object")}self.',
        f"Tell a gentle gallery myth where {hero.id} learns that {artifact.label} becomes brighter when shared.",
        f'Write a child-friendly story with a gallery, a joke, and a sharing choice; include "{artifact.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    artifact = f["artifact"]
    gallery = f["gallery"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"Who found the {artifact.label} in {gallery.name}?",
            answer=f"{hero.id} found the {artifact.label} in {gallery.name}. {hero.pronoun('subject').capitalize()} was a {f['trait']} {hero.type} traveling with {elder.label}.",
        ),
        QAItem(
            question=f"Why did {hero.id} first want to keep the {artifact.label} hidden?",
            answer=f"{hero.id} felt proud and possessive, so {hero.pronoun('subject')} wanted the laughter to stay in one hand instead of being shared around the gallery.",
        ),
        QAItem(
            question=f"What did {elder.type} say about the {artifact.label}?",
            answer=f"{elder.pronoun('subject').capitalize()} said that a joke that stays in one hand gets small, but a shared joke can shine on every face.",
        ),
    ]
    if tool is not None:
        qa.append(
            QAItem(
                question=f"How did {tool.label} help them share the {artifact.label}?",
                answer=f"They used {tool.label} to let the room see the {artifact.label} safely and at once, so everyone could laugh together without losing the treasure.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt joyful and generous. By the end, {hero.pronoun('subject')} understood that the gift grew when it traveled from person to person.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "gallery": [QAItem(
        question="What is a gallery?",
        answer="A gallery is a place where pictures, objects, or stories are shown so people can look at them and enjoy them.",
    )],
    "humor": [QAItem(
        question="Why do people laugh at a joke?",
        answer="People laugh at a joke because it surprises them in a playful way and makes them feel light and happy.",
    )],
    "sharing": [QAItem(
        question="Why is sharing nice?",
        answer="Sharing is nice because other people can enjoy the same good thing, and it can make everyone feel included.",
    )],
    "myth": [QAItem(
        question="What makes a story feel mythic?",
        answer="A mythic story often feels old, important, and a little magical, as if the whole world is listening to it.",
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["gallery"])
    out.extend(WORLD_KNOWLEDGE["humor"])
    out.extend(WORLD_KNOWLEDGE["sharing"])
    out.extend(WORLD_KNOWLEDGE["myth"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing":
            bits.append(f"displayed_in={e.displayed_in}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
gallery(G) :- gallery_name(G).
artifact(A) :- artifact_name(A).
tool(T) :- tool_name(T).

shareable(A) :- can_share(A).
at_risk(A) :- shareable(A), fragile_pride(A).

compatible(A,T) :- at_risk(A), tool(T), helps(T,share).

valid_story(G,A) :- gallery(G), artifact(A), at_risk(A), compatible(A,_).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid in GALLERIES:
        lines.append(asp.fact("gallery_name", gid))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact_name", aid))
        if a.can_share:
            lines.append(asp.fact("can_share", aid))
        if a.fragile_pride:
            lines.append(asp.fact("fragile_pride", aid))
    for t in TOOLS:
        lines.append(asp.fact("tool_name", t.id))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(g, a) for g in GALLERIES for a, art in ARTIFACTS.items() if artifact_at_risk(art) and select_tool(art)}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python reasonableness gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic gallery story world: humor, sharing, and a gentle turn.")
    ap.add_argument("--gallery", choices=GALLERIES)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.artifact:
        art = ARTIFACTS[args.artifact]
        if not artifact_at_risk(art):
            raise StoryError(explain_rejection(art))
    choices = list(ARTIFACTS.keys())
    if args.artifact:
        choices = [args.artifact]
    artifact = rng.choice(choices)
    gallery = args.gallery or rng.choice(list(GALLERIES))
    kind = args.kind or rng.choice(KINDS)
    role = args.role or rng.choice(ROLES)
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(gallery=gallery, artifact=artifact, name=name, kind=kind, role=role, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(GALLERIES[params.gallery], ARTIFACTS[params.artifact], params.name, params.kind, params.role, params.trait)
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
    StoryParams(gallery="moonhall", artifact="laughing_mask", name="Mira", kind="girl", role="elder", trait="curious"),
    StoryParams(gallery="sunarchive", artifact="jingle_bell", name="Niko", kind="boy", role="aunt", trait="mischievous"),
    StoryParams(gallery="rivergallery", artifact="mirror_card", name="Lina", kind="girl", role="mother", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

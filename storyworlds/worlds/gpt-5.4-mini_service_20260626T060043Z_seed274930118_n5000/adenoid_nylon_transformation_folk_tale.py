#!/usr/bin/env python3
"""
storyworlds/worlds/adenoid_nylon_transformation_folk_tale.py
============================================================

A small folk-tale storyworld about a child, a blocked voice, and a magical
transformation that turns an ordinary nylon thing into a fair solution.

Seed idea:
- In a village folk tale, a child wants to sing or speak clearly at a feast.
- A swollen adenoid makes the voice muffled and sore.
- A kindly helper offers a magical transformation: the nylon ribbon / net / cord
  becomes the right charm, and the child can join the celebration at last.

This script models that as a tiny simulation:
- the adenoid has a size meter,
- the child's voice has a blockage meter,
- a transformation spell can turn a nylon object into a useful folk-tale charm,
- a sensible resolution requires a real change in state, not just a name swap.
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
    worn_by: Optional[str] = None
    transformed_from: Optional[str] = None
    transformed_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    object_kind: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    folk_detail: str


@dataclass
class Transform:
    id: str
    source_kind: str
    target_kind: str
    source_phrase: str
    target_phrase: str
    target_label: str
    helps_with: str
    requires: str
    keyword: str = "transformation"


SETTINGS = {
    "village_green": Setting(
        place="the village green",
        folk_detail="The lanterns hung low over the green, and the old well whispered in the dusk.",
    ),
    "forest_edge": Setting(
        place="the forest edge",
        folk_detail="The pine trees leaned close together, as if they were listening for a secret.",
    ),
    "river_road": Setting(
        place="the river road",
        folk_detail="The river sang under the moon, and the mud kept little footprints like a diary.",
    ),
}

TRANSFORMS = {
    "nylon_ribbon": Transform(
        id="nylon_ribbon",
        source_kind="ribbon",
        target_kind="charm",
        source_phrase="a bright nylon ribbon",
        target_phrase="a soft charm made from the nylon ribbon",
        target_label="nylon charm",
        helps_with="steadying the child’s voice",
        requires="the ribbon must be transformed into a gentle charm",
    ),
    "nylon_net": Transform(
        id="nylon_net",
        source_kind="net",
        target_kind="veil",
        source_phrase="a blue nylon net",
        target_phrase="a whisper-light veil of nylon threads",
        target_label="nylon veil",
        helps_with="softening the noisy air",
        requires="the net must become something light and kind",
    ),
    "nylon_cord": Transform(
        id="nylon_cord",
        source_kind="cord",
        target_kind="thread",
        source_phrase="a strong nylon cord",
        target_phrase="a silver-threaded nylon charm cord",
        target_label="nylon charm cord",
        helps_with="tying the charm to the old story-tree",
        requires="the cord must become a lucky charm cord",
    ),
}

HERO_NAMES = ["Mira", "Anya", "Toma", "Lina", "Bela", "Suri"]
HELPER_NAMES = ["Grandmother", "Old Fox", "Hearth Witch", "Miller", "Weaver", "Boatman"]


def valid_pairs() -> list[tuple[str, str]]:
    return [(place, tid) for place in SETTINGS for tid in TRANSFORMS]


def folk_opening(place: str) -> str:
    return {
        "village_green": "Once, on a village green where the geese marched like little white kings,",
        "forest_edge": "Long ago, at the forest edge where the pines kept old secrets,",
        "river_road": "Once upon a moonlit river road, where the water sang under the stones,",
    }[place]


def do_swell(world: World, child: Entity, adenoid: Entity) -> None:
    child.meters["blocked_voice"] += 1
    adenoid.meters["swell"] += 1
    world.say(
        f"{child.id} tried to greet the day, but {child.pronoun('possessive')} voice came out small and muffled."
    )
    world.say(
        f"The doctor had said the adenoid was swollen, and that made every word feel caught behind a little gate."
    )


def foresee(world: World, child: Entity, tf: Transform) -> bool:
    return child.meters.get("blocked_voice", 0.0) >= THRESHOLD and tf.keyword == "transformation"


def transform_item(world: World, helper: Entity, obj: Entity, tf: Transform, child: Entity) -> Optional[Entity]:
    if obj.type != tf.source_kind:
        return None
    if child.meters.get("blocked_voice", 0.0) < THRESHOLD:
        return None
    if (helper.id, obj.id, tf.id) in world.fired:
        return None
    world.fired.add((helper.id, obj.id, tf.id))
    obj.transformed_to = tf.target_kind
    obj.label = tf.target_label
    obj.phrase = tf.target_phrase
    obj.type = tf.target_kind
    obj.meters["magic"] = 1.0
    child.meters["blocked_voice"] = 0.0
    child.memes["hope"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{helper.id} smiled and sang an old folk spell, and the {tf.source_phrase} changed shape."
    )
    world.say(
        f"It became {tf.target_phrase}, and at once the tight little knot in {child.id}'s throat loosened."
    )
    return obj


def resolution(world: World, child: Entity, helper: Entity, obj: Entity, tf: Transform) -> None:
    world.say(
        f"{child.id} took a deep breath, thanked {helper.pronoun('object')}, and spoke clearly at last."
    )
    world.say(
        f"By dusk, {child.id} was laughing with the villagers, while {obj.phrase} shone like something always meant for the tale."
    )


def tell(setting: Setting, tf: Transform, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(setting.place)
    world.say(folk_opening(setting.place))

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    adenoid = world.add(Entity(id="adenoid", type="body_part", label="adenoid", phrase="the swollen adenoid"))
    obj = world.add(Entity(id="nylon_object", type=tf.source_kind, label=tf.source_kind, phrase=tf.source_phrase, owner=helper.id))

    world.facts.update(hero=hero, helper=helper, adenoid=adenoid, obj=obj, tf=tf, setting=setting)

    world.say(
        f"{hero.id} was a small {hero_type} who loved folk songs, bread crusts, and stories told by lantern light."
    )
    world.say(
        f"One evening, {helper.id} brought {helper.pronoun('object')} {tf.source_phrase}, saying it had been waiting for a wise use."
    )

    world.para()
    do_swell(world, hero, adenoid)
    world.say(
        f"{hero.id} wanted to sing for the feast, but the blocked voice made the notes wobble like reeds in a stream."
    )
    world.say(
        f"{helper.id} looked at the child, then at {tf.source_phrase}, and understood the problem was not just noise, but shape."
    )

    world.para()
    if foresee(world, hero, tf):
        transformed = transform_item(world, helper, obj, tf, hero)
        if not transformed:
            raise StoryError("This transformation cannot be used in the current story.")
        world.say(
            f"That was the right kind of transformation: not a trick, but a change that gave the child a better way through."
        )
        resolution(world, hero, helper, transformed, tf)

    world.facts["resolved"] = hero.meters.get("blocked_voice", 0.0) < THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    tf = f["tf"]
    return [
        f'Write a short folk tale about a child named {hero.id} who needs a {tf.keyword} to solve a problem with a swollen adenoid.',
        f"Tell a gentle story where {hero.id} cannot sing clearly until a {tf.source_phrase} is transformed into {tf.target_label}.",
        f'Write a child-friendly folk tale that includes the words "adenoid" and "nylon" and ends with a happy transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj = f["obj"]
    tf = f["tf"]
    return [
        QAItem(
            question=f"Why was {hero.id}'s voice so small at the feast?",
            answer="Because the adenoid was swollen, so the child's voice sounded muffled and hard to hear.",
        ),
        QAItem(
            question=f"What did {helper.id} change the nylon thing into?",
            answer=f"{helper.id} changed {obj.phrase} into {tf.target_phrase} so it could help the child.",
        ),
        QAItem(
            question=f"How did the transformation help {hero.id}?",
            answer=f"It made the blocked voice loosen, so {hero.id} could speak and sing clearly again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is nylon?",
            answer="Nylon is a strong man-made material. People use it for ribbons, cord, cloth, and other handy things.",
        ),
        QAItem(
            question="What does transformation mean in a folk tale?",
            answer="A transformation is when something changes into a different form, often through magic or a special act.",
        ),
        QAItem(
            question="What is an adenoid?",
            answer="An adenoid is a small part inside the throat area. If it gets swollen, it can make breathing or speaking harder.",
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.transformed_to:
            bits.append(f"transformed_to={e.transformed_to}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(place: str, tf_id: str) -> str:
    if place not in SETTINGS:
        return "(No story: that place is not part of this folk tale world.)"
    if tf_id not in TRANSFORMS:
        return "(No story: that transformation is not available.)"
    return "(No story: the chosen transformation cannot happen here.)"


ASP_RULES = r"""
adenoid_swollen(C) :- blocked_voice(C).
can_transform(O,T) :- nylon(O), transformation(T), adenoid_swollen(C), helps(T,C), source_of(T,O).
resolved(C) :- blocked_voice(C), can_transform(_, _), transformed(_, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for tid, tf in TRANSFORMS.items():
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("helps", tid, "child"))
        lines.append(asp.fact("source_of", tid, tf.source_kind))
        lines.append(asp.fact("target_of", tid, tf.target_kind))
        lines.append(asp.fact("keyword", tid, tf.keyword))
    lines.append(asp.fact("blocked_voice", "child"))
    lines.append(asp.fact("nylon", "nylon_object"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show can_transform/2.\n#show resolved/1.")
    model = asp.one_model(program)
    atoms = set((a.name, tuple(sym for sym in a.arguments)) for a in model)
    if atoms:
        print("OK: ASP reasoning produced a non-empty model.")
        return 0
    print("MISMATCH: ASP model was empty.")
    return 1


CURATED = [
    StoryParams(
        place="village_green",
        hero_name="Mira",
        hero_type="girl",
        helper_name="Grandmother",
        helper_type="woman",
        object_kind="ribbon",
    ),
    StoryParams(
        place="forest_edge",
        hero_name="Toma",
        hero_type="boy",
        helper_name="Old Fox",
        helper_type="fox",
        object_kind="net",
    ),
    StoryParams(
        place="river_road",
        hero_name="Lina",
        hero_type="girl",
        helper_name="Weaver",
        helper_type="woman",
        object_kind="cord",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale world of adenoid, nylon, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--transformation", choices=TRANSFORMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type")
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
    place = args.place or rng.choice(list(SETTINGS))
    tf_id = args.transformation or rng.choice(list(TRANSFORMS))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or ("woman" if helper_name == "Grandmother" else "fox")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        object_kind=TRANSFORMS[tf_id].source_kind,
    )


def generate(params: StoryParams) -> StorySample:
    tf = next(v for v in TRANSFORMS.values() if v.source_kind == params.object_kind)
    world = tell(SETTINGS[params.place], tf, params.hero_name, params.hero_type, params.helper_name, params.helper_type)
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
        print(asp_program("#show can_transform/2.\n#show resolved/1."))
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
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

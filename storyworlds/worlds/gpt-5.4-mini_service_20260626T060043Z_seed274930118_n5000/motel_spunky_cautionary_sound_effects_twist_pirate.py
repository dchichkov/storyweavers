#!/usr/bin/env python3
"""
A standalone storyworld for a tiny Pirate Tale about a spunky crew at a motel,
with a cautionary warning, lively sound effects, and a small twist.

The source tale idea:
- A spunky little pirate loves clattering around a seaside motel.
- The pirate wants to march and sing with boots, bell, and trunk.
- A caretaker warns that the noisy scheme will wake the sleeping guests.
- The pirate tries anyway, the sound effects spread, and trouble grows.
- Twist: the "ghostly" thumps come from a trapped parrot and a loose
  curtain rope, so the crew solves the problem and keeps the motel quiet.

The story model tracks:
- physical meters: noise, mess, strain, calm
- emotional memes: spunk, caution, worry, pride, relief
"""

from __future__ import annotations

import argparse
import dataclasses
from dataclasses import dataclass, field
import json
import os
import random
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


NOISE_THRESHOLD = 1.0
WORRY_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    concealed_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {"noise": 0.0, "mess": 0.0, "strain": 0.0, "calm": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"spunk": 0.0, "caution": 0.0, "worry": 0.0, "pride": 0.0, "relief": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str
    parent: str
    setting: str = "the motel"
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace_log: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


def _narrate(world: World, msg: str, narrate: bool = True) -> None:
    if narrate:
        world.say(msg)
    world.trace_log.append(msg)


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        # noise wakes worry
        for e in world.entities.values():
            if e.kind != "character":
                continue
            if e.meters["noise"] >= NOISE_THRESHOLD and ("worry", e.id) not in world.fired:
                world.fired.add(("worry", e.id))
                e.memes["worry"] += 1
                e.meters["calm"] -= 0.5
                _narrate(world, f"The racket made {e.id} worry about the sleeping guests.", narrate)
                changed = True
        # hidden cause twist: if the parrot is trapped and the curtain rope is loose,
        # the "ghostly" noise gets a cause.
        rope = world.entities.get("rope")
        parrot = world.entities.get("parrot")
        if rope and parrot and rope.concealed_in == "curtain" and parrot.concealed_in == "trunk":
            if ("twist",) not in world.fired and world.get("hero").meters["noise"] >= 1.0:
                world.fired.add(("twist",))
                world.facts["twist_found"] = True
                _narrate(world, "The spooky thumping had a hidden cause: a loose rope and a trapped parrot.", narrate)
                changed = True


def pirate_name_choices() -> list[str]:
    return ["Milo", "Nia", "Pip", "Jory", "Zara", "Bram"]


def parent_choices() -> list[str]:
    return ["mother", "father", "aunt", "uncle"]


def build_world(params: StoryParams) -> World:
    world = World(params.setting)
    hero = world.add(Entity(id="hero", kind="character", type="boy", label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type="mother" if params.parent == "mother" else "father", label=params.parent))
    trunk = world.add(Entity(id="trunk", type="thing", label="old trunk"))
    bell = world.add(Entity(id="bell", type="thing", label="brass bell", owner=hero.id, carried_by=hero.id))
    boots = world.add(Entity(id="boots", type="thing", label="big boots", owner=hero.id, carried_by=hero.id))
    rope = world.add(Entity(id="rope", type="thing", label="curtain rope", concealed_in="curtain"))
    parrot = world.add(Entity(id="parrot", type="thing", label="sleepy parrot", concealed_in="trunk"))
    world.facts.update(hero=hero, parent=parent, trunk=trunk, bell=bell, boots=boots, rope=rope, parrot=parrot)
    return world


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    bell: Entity = world.facts["bell"]
    boots: Entity = world.facts["boots"]
    rope: Entity = world.facts["rope"]
    parrot: Entity = world.facts["parrot"]

    # Act 1
    world.say(
        f"{hero.label} was a spunky little pirate staying at a seaside motel with {hero.pronoun('possessive')} {parent.label}."
    )
    world.say(
        f"{hero.label} loved the clink of {bell.label}, the thump of {boots.label}, and the creak of the hall boards."
    )
    hero.memes["spunk"] += 1
    bell.meters["noise"] += 0.2

    world.para()

    # Act 2: cautionary warning
    world.say(
        f"That evening, {parent.label} held up a finger and said, \"No marching, no shouting, and no bell-ringing in the motel halls.\""
    )
    hero.memes["caution"] += 0.5
    hero.memes["spunk"] += 0.5
    world.say(
        f"\"The guests are asleep,\" {parent.label} warned, \"and a noisy pirate could wake the whole place.\""
    )
    world.say(
        f"But {hero.label} felt bold and tried to tiptoe like a storm with {bell.label} tucked under {hero.pronoun('possessive')} arm."
    )

    hero.meters["noise"] += 1.0
    bell.meters["noise"] += 1.0
    boots.meters["noise"] += 0.4
    propagate(world, narrate=True)

    world.say(
        f"Clink-clank, creak-creak, tap-tap went the hallway, and even the ice machine seemed to whisper back."
    )

    world.para()

    # Twist and resolution
    if world.facts.get("twist_found"):
        world.say(
            f"Then {parent.label} listened closely and found the riddle: the strange thumps were not a ghost at all."
        )
        world.say(
            f"The loose {rope.label} kept knocking the wall, and the sleepy {parrot.label} had been hiding in the {trunk.label} the whole time."
        )
        world.say(
            f"{hero.label} carefully opened the {trunk.label}, soothed the {parrot.label}, and tied the {rope.label} tight."
        )
        hero.meters["noise"] -= 0.6
        hero.meters["calm"] += 1.0
        parent.meters["calm"] += 1.0
        hero.memes["relief"] += 1.0
        parent.memes["relief"] += 1.0
        world.say(
            f"At last the motel grew still, and {hero.label} grinned because the biggest mystery was only a clumsy little mix-up."
        )
    else:
        world.say(
            f"At last {hero.label} lowered {hero.pronoun('possessive')} voice, tucked away the bell, and listened to the quiet motel breathe."
        )

    world.facts["resolved"] = True


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    return [
        QAItem(
            question=f"Who was the spunky pirate staying at the motel?",
            answer=f"The spunky pirate was {hero.label}, and {hero.pronoun()} stayed there with {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question="What did the parent warn about?",
            answer=f"{parent.label.capitalize()} warned that the pirate should not march, shout, or ring the bell in the motel halls because the guests were sleeping.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The strange thumping was not a ghost. It came from a loose curtain rope and a sleepy parrot hiding in the trunk.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{hero.label} soothed the parrot, tied the rope tight, and the motel became quiet again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a motel?",
            answer="A motel is a place where travelers sleep for a night or two, often with rooms near a parking area.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking about danger before acting.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are sounds that help tell what is happening, like clink, creak, thump, or tap.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you thought was going on.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    return [
        f"Write a short pirate tale about {hero.label}, a spunky child at a motel, with a cautionary warning and a surprising twist.",
        f"Tell a child-friendly story where {parent.label} warns a spunky pirate not to make noise in the motel hall.",
        "Use lively sound effects like clink, creak, tap, and thump in a small pirate story with a gentle ending.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:6} ({e.type:9}) meters={{{', '.join(f'{k}: {v:.1f}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v:.1f}' for k, v in e.memes.items() if v)}}} "
            f"owner={e.owner or '-'} carried={e.carried_by or '-'} hidden={e.concealed_in or '-'}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("place", "motel"))
    lines.append(asp.fact("feature", "cautionary"))
    lines.append(asp.fact("feature", "sound_effects"))
    lines.append(asp.fact("feature", "twist"))
    lines.append(asp.fact("style", "pirate"))
    lines.append(asp.fact("word", "motel"))
    lines.append(asp.fact("word", "spunky"))
    return "\n".join(lines)


ASP_RULES = r"""
feature_ok(cautionary) :- feature(cautionary).
feature_ok(sound_effects) :- feature(sound_effects).
feature_ok(twist) :- feature(twist).
story_ok :- place(motel), word(spunky), feature_ok(cautionary), feature_ok(sound_effects), feature_ok(twist), style(pirate).
#show story_ok/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(sym.name == "story_ok" for sym in model)
    if ok:
        print("OK: ASP twin recognizes the motel/pirate/cautionary/sound_effects/twist world.")
        return 0
    print("MISMATCH: ASP twin did not validate the required features.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate motel storyworld with caution, sound effects, and a twist.")
    ap.add_argument("--name", choices=pirate_name_choices())
    ap.add_argument("--parent", choices=parent_choices())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(pirate_name_choices())
    parent = args.parent or rng.choice(parent_choices())
    return StoryParams(name=name, parent=parent, setting="the motel")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
    StoryParams(name="Milo", parent="mother", setting="the motel", seed=1),
    StoryParams(name="Nia", parent="father", setting="the motel", seed=2),
    StoryParams(name="Pip", parent="aunt", setting="the motel", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/0."))
        print("story_ok" if any(sym.name == "story_ok" for sym in model) else "no_story_ok")
        return

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
            header = f"### {p.name}: pirate motel twist"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small myth-style storyworld: a child or pilgrim seeks proof, carries a hankie,
and meets a surprise in a dirt-dim place.

The world is intentionally tiny and classical:
- one hero
- one elder or guide
- one sacred place
- one proof-object
- one hankie
- one surprising reveal

The simulated state drives the story. Physical meters and emotional memes
change as events unfold, and the ending image shows what has changed.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "priest", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    dirt_dim: bool = False
    sacred: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    label: str
    dirt_dim: bool
    sacred: bool
    opening: str


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    kind: str
    belongs_to: str
    can_prove: str
    surprised_by: str


@dataclass
class Hankie:
    id: str
    label: str
    phrase: str
    clean: bool = True


SETTINGS = {
    "temple_yard": Setting(
        id="temple_yard",
        label="the temple yard",
        dirt_dim=True,
        sacred=True,
        opening="The temple yard was dirt-dim after a long dry wind, and the old stones waited in silence.",
    ),
    "hill_shrine": Setting(
        id="hill_shrine",
        label="the hill shrine",
        dirt_dim=True,
        sacred=True,
        opening="The hill shrine stood dirt-dim on its slope, with moss in the cracks and a quiet sky above it.",
    ),
    "river_steps": Setting(
        id="river_steps",
        label="the river steps",
        dirt_dim=True,
        sacred=False,
        opening="The river steps were dirt-dim and soft at the edges, where the water had kissed the stone again and again.",
    ),
}

ARTIFACTS = {
    "sun_mark": Artifact(
        id="sun_mark",
        label="sun mark",
        phrase="a small gold mark",
        kind="proof",
        belongs_to="the sky",
        can_prove="a bright blessing had touched the place",
        surprised_by="the surprise of a hidden sign",
    ),
    "stone_seal": Artifact(
        id="stone_seal",
        label="stone seal",
        phrase="a round stone seal",
        kind="proof",
        belongs_to="the shrine",
        can_prove="the shrine had been cared for by patient hands",
        surprised_by="the surprise of old carvings beneath the dust",
    ),
    "river_pebble": Artifact(
        id="river_pebble",
        label="river pebble",
        phrase="a smooth river pebble",
        kind="proof",
        belongs_to="the river",
        can_prove="the river had once climbed higher than the steps",
        surprised_by="the surprise of a wet shine inside dry stone",
    ),
}

HANKIES = {
    "linen": Hankie(
        id="linen",
        label="linen hankie",
        phrase="a small linen hankie",
        clean=True,
    ),
    "blue": Hankie(
        id="blue",
        label="blue hankie",
        phrase="a blue hankie with a soft edge",
        clean=True,
    ),
}

GIRL_NAMES = ["Mira", "Sana", "Tali", "Nia", "Rhea", "Ila"]
BOY_NAMES = ["Aren", "Bari", "Kian", "Oren", "Tavi", "Eli"]
TRUTHS = ["patient", "brave", "gentle", "curious", "quiet", "hopeful"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    artifact: str
    hankie: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(place=Place(id=setting.id, label=setting.label, dirt_dim=setting.dirt_dim, sacred=setting.sacred))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name, memes={"hope": 0.0, "surprise": 0.0, "doubt": 0.0}))
    guide = world.add(Entity(id="Guide", kind="character", type=params.guide, label=f"the {params.guide}", memes={"calm": 0.0}))
    proof = world.add(Entity(
        id="Proof",
        kind="thing",
        type="proof",
        label=ARTIFACTS[params.artifact].label,
        phrase=ARTIFACTS[params.artifact].phrase,
        owner=hero.id,
        caretaker=guide.id,
        location=setting.id,
        meters={"dust": 0.0, "shine": 0.0},
        memes={"meaning": 0.0},
    ))
    hankie = world.add(Entity(
        id="Hankie",
        kind="thing",
        type="hankie",
        label=HANKIES[params.hankie].label,
        phrase=HANKIES[params.hankie].phrase,
        owner=hero.id,
        held_by=hero.id,
        location=hero.id,
        meters={"dust": 0.0, "dirt_dim": 0.0},
        memes={"care": 0.0},
    ))

    # Act 1: mythic setup
    world.say(f"{hero.id} was a {params.trait} {params.gender} who came to {setting.label} with a question in {hero.pronoun('possessive')} chest.")
    world.say(f"{hero.id} had heard that {ARTIFACTS[params.artifact].can_prove}, but no one could agree on the truth.")
    world.say(f"So {hero.id} carried {hankie.phrase} and hoped for proof.")

    world.para()

    # Act 2: tension
    hero.memes["doubt"] += 1
    guide.memes["calm"] += 1
    world.say(setting.opening)
    world.say(f"The {params.guide} said, 'If you want proof, you must look closely and keep your hands clean enough to see.'")
    world.say(f"{hero.id} knelt by the old stone and held up {hero.pronoun('possessive')} hankie, ready to wipe away the dirt-dim dust.")

    # Physical effect: dust on proof and hankie, but also increase in meaning
    proof.meters["dust"] += 1
    proof.memes["meaning"] += 1
    hankie.meters["dust"] += 1
    hankie.meters["dirt_dim"] += 1
    hero.memes["surprise"] += 1

    world.para()

    # Surprise turn
    world.say(f"Then the surprise came.")
    if params.artifact == "sun_mark":
        world.say(f"When the hankie brushed the stone, a tiny gold mark woke under the dust, bright as a drop of morning.")
        world.say(f"It was proof that {ARTIFACTS[params.artifact].belongs_to} had once blessed the yard.")
    elif params.artifact == "stone_seal":
        world.say(f"When the hankie swept the lint aside, a round stone seal appeared in the crack, hidden where no eye had looked.")
        world.say(f"It was proof that patient hands had cared for the shrine long ago.")
    else:
        world.say(f"When the hankie dabbed the wet edge of the step, a smooth river pebble gleamed there, as if the stone had remembered the water.")
        world.say(f"It was proof that the river had once climbed higher than the steps.")

    # Resolution
    hero.memes["hope"] += 1
    guide.memes["calm"] += 1
    world.say(f"{hero.id} smiled, because the answer had been there all along, small and simple in a dirt-dim place.")
    world.say(f"{hero.id} folded {hankie.it()} carefully and held the proof close, as if {hero.pronoun('possessive')} hands had learned how wonder can hide inside dust.")

    world.facts.update(
        hero=hero,
        guide=guide,
        proof=proof,
        hankie=hankie,
        setting=setting,
        artifact=ARTIFACTS[params.artifact],
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth-like story for a child about a {f["hero"].type} who seeks proof in a dirt-dim sacred place.',
        f"Tell a gentle surprise story where {f['hero'].id} carries a hankie and finds {f['artifact'].label} as proof.",
        f'Write a small story that uses the words "proof", "hankie", and "dirt-dim", and ends with a surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    proof: Entity = f["proof"]
    hankie: Entity = f["hankie"]
    setting: Setting = f["setting"]
    artifact: Artifact = f["artifact"]

    return [
        QAItem(
            question=f"Who came to {setting.label} looking for proof?",
            answer=f"{hero.id} came to {setting.label} looking for proof, and {guide.label} came with calm advice.",
        ),
        QAItem(
            question=f"What did {hero.id} carry to help at {setting.label}?",
            answer=f"{hero.id} carried {hankie.phrase} to help wipe away dust and look closely.",
        ),
        QAItem(
            question=f"What became the proof in the story?",
            answer=f"{proof.label} became the proof, because it showed that {artifact.can_prove}.",
        ),
        QAItem(
            question=f"Why was the place called dirt-dim?",
            answer=f"It was dirt-dim because the old place had dust and soft gray light on its stones.",
        ),
        QAItem(
            question=f"What surprise happened after the hankie moved the dust?",
            answer=f"The surprise was that {artifact.surprised_by} appeared, and the hidden sign could finally be seen.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(question="What is a hankie?", answer="A hankie is a small cloth you can carry to wipe your nose, clean little messes, or cover your hand."),
    QAItem(question="What is proof?", answer="Proof is something that helps show that a true thing really happened or is really there."),
    QAItem(question="What does surprise mean?", answer="A surprise is something you did not expect, so it makes you notice quickly."),
    QAItem(question="What does dirt-dim mean?", answer="Dirt-dim means covered with dust or looking gray and shadowy, like a place that has been quiet for a long time."),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
hero(H) :- character(H).

dirt_dim_place(P) :- place(P), dirt_dim(P).
surprise_event(P,A) :- dirt_dim_place(P), artifact(A), hidden(A).
proof_found(H,A) :- hero(H), artifact(A), reveals(A).
story_ok(P,A) :- place(P), artifact(A), surprise_event(P,A), proof_found(_,A).

#show story_ok/2.
#show surprise_event/2.
#show proof_found/2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dirt_dim:
            lines.append(asp.fact("dirt_dim", sid))
        if s.sacred:
            lines.append(asp.fact("sacred", sid))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("reveals", aid))
        lines.append(asp.fact("hidden", aid))
    for hid, h in HANKIES.items():
        lines.append(asp.fact("hankie", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_ok() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = sorted((sid, aid) for sid, s in SETTINGS.items() for aid in ARTIFACTS if s.dirt_dim)
    cl = asp_story_ok()
    expected = sorted(set(py))
    if cl == expected:
        print(f"OK: ASP parity for story_ok/2 with {len(cl)} combinations.")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("python:", expected)
    print("asp:", cl)
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [(sid, aid, hid) for sid, s in SETTINGS.items() if s.dirt_dim for aid in ARTIFACTS for hid in HANKIES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-like storyworld with proof, hankie, dirt-dim, and surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--hankie", choices=HANKIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father", "priest", "priestess", "elder"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRUTHS)
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
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.artifact:
        combos = [c for c in combos if c[1] == args.artifact]
    if args.hankie:
        combos = [c for c in combos if c[2] == args.hankie]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    setting, artifact, hankie = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(["mother", "father", "priest", "priestess", "elder"])
    trait = args.trait or rng.choice(TRUTHS)
    return StoryParams(setting=setting, artifact=artifact, hankie=hankie, name=name, gender=gender, guide=guide, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.label} dirt_dim={world.place.dirt_dim} sacred={world.place.sacred}")
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="temple_yard", artifact="sun_mark", hankie="linen", name="Mira", gender="girl", guide="elder", trait="curious"),
    StoryParams(setting="hill_shrine", artifact="stone_seal", hankie="blue", name="Aren", gender="boy", guide="priest", trait="patient"),
    StoryParams(setting="river_steps", artifact="river_pebble", hankie="linen", name="Tali", gender="girl", guide="mother", trait="hopeful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/2."))
        combos = sorted(set(asp.atoms(model, "story_ok")))
        print(f"{len(combos)} story_ok combinations:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.setting}, {p.artifact}, {p.hankie}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Family, Curiosity, and a Fairy-Tale Rave

A small standalone story world where a family follows a glowing music night,
meets a threat, and learns that curiosity is brave when it stays together.

This world keeps the story simple and child-facing:
- a family is traveling together
- a magical rave in the woods draws their curiosity
- a threat appears
- the family uses a gentle plan to stay safe
- the ending proves what changed in the world
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mother", "girl", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "boy", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the forest clearing"
    magic: str = "glowing lanterns"
    sound: str = "soft drumbeats"
    safe_spots: set[str] = field(default_factory=lambda: {"home", "path", "clearing"})


@dataclass
class Threat:
    id: str
    name: str
    label: str
    danger: str
    can_be_tamed: bool = True
    scare_word: str = "threat"


@dataclass
class World:
    place: Place
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

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "clearing": Place(name="the forest clearing", magic="glowing lanterns", sound="soft drumbeats"),
    "garden": Place(name="the moon garden", magic="silver ribbons", sound="gentle bells"),
    "riverbank": Place(name="the riverbank glade", magic="shimmering reeds", sound="little flutes"),
}

THREATS = {
    "wolf": Threat(id="wolf", name="wolf", label="a gray wolf", danger="howled at the dancers"),
    "fog": Threat(id="fog", name="fog", label="a thick fog", danger="hid the path"),
    "thorn": Threat(id="thorn", name="thorn bramble", label="a thorn bramble", danger="scratched small feet"),
}

FAMILY_ROLES = {
    "mother": "mother",
    "father": "father",
    "child": "child",
}

GIVEN_NAMES = {
    "mother": ["Mira", "Elin", "Sera", "Nina"],
    "father": ["Rowan", "Cedric", "Bram", "Tobin"],
    "child": ["Pip", "Luna", "Tessa", "Milo"],
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    threat: str
    family_name: str
    mother_name: str
    father_name: str
    child_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
family(F) :- member(F,_).
curious(C) :- trait(C,curious).
threat(T) :- danger(T).
rave(R) :- event(R,rave).

adventure(F) :- family(F), curious(C), member(F,C), rave(_).
unsafe(F,T) :- family(F), threat(T), near(T, path).
needs_together(F) :- adventure(F), unsafe(F,_).

safe(F) :- needs_together(F), stay_close(F), use_light(F).
#show adventure/1.
#show unsafe/2.
#show safe/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    lines.append(asp.fact("event", "night", "rave"))
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in THREATS:
        lines.append(asp.fact("danger", tid))
    for role in FAMILY_ROLES:
        lines.append(asp.fact("role", role))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def family_name_for(place: str, threat: str) -> str:
    return f"{place}_{threat}_family"


def choose_name(rng: random.Random, role: str) -> str:
    return rng.choice(GIVEN_NAMES[role])


def make_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    mother = world.add(Entity(
        id="mother", kind="character", type="mother", label=params.mother_name,
        traits=["gentle", "watchful"], meters={"fear": 0.0}, memes={"love": 2.0}
    ))
    father = world.add(Entity(
        id="father", kind="character", type="father", label=params.father_name,
        traits=["steady", "kind"], meters={"fear": 0.0}, memes={"love": 2.0}
    ))
    child = world.add(Entity(
        id="child", kind="character", type="child", label=params.child_name,
        traits=["curious", "bright"], meters={"fear": 0.0}, memes={"curiosity": 2.0, "joy": 1.0}
    ))
    world.add(Entity(
        id="lantern", kind="thing", type="lantern", label="a lantern string",
        phrase="a lantern string", owner="family", plural=True, meters={"light": 2.0}
    ))
    world.add(Entity(
        id="drums", kind="thing", type="drums", label="tiny drums",
        phrase="tiny drums", owner="family", plural=True
    ))
    world.add(Entity(
        id="threat", kind="thing", type=params.threat, label=THREATS[params.threat].label,
        phrase=THREATS[params.threat].label, owner=None, meters={"danger": 1.0}
    ))
    world.facts = {
        "family_id": params.family_name,
        "place": params.place,
        "threat": params.threat,
    }
    return world


def predict_threat(world: World) -> bool:
    return world.get("child").memes.get("curiosity", 0.0) >= 1.0 and world.get("threat").meters.get("danger", 0.0) >= 1.0


def tell(params: StoryParams) -> World:
    world = make_world(params)
    place = world.place
    mother, father, child = world.get("mother"), world.get("father"), world.get("child")
    threat = world.get("threat")

    world.say(
        f"Once upon a time, a small family lived near {place.name}. "
        f"They loved the night when {place.magic} blinked like stars and {place.sound} floated through the trees."
    )
    world.say(
        f"The little child, {child.label}, was full of curiosity. {child.pronoun('subject').capitalize()} kept asking what made the lights dance so kindly in the dark."
    )

    world.para()
    world.say(
        f"That evening, the family followed the music to a fairy-tale rave in the clearing. "
        f"Fairy lanterns twirled above the grass, and everyone smiled as if the moon itself were clapping."
    )
    world.say(
        f"{mother.label} took {child.pronoun('possessive')} hand, and {father.label} carried the bright lantern string so the path would stay easy to see."
    )

    world.para()
    world.say(
        f"But the night held a threat. From the shadow of the ferns came {threat.label}, and it {THREATS[params.threat].danger}. "
        f"{child.label}'s curiosity grew bold, yet {child.pronoun('subject')} also felt a tiny shiver."
    )
    mother.meters["fear"] += 1.0
    father.meters["fear"] += 1.0
    child.meters["fear"] += 1.0
    child.memes["curiosity"] += 1.0

    if predict_threat(world):
        world.say(
            f"{mother.label} whispered, 'Stay close, little one.' {father.label} lifted the lanterns higher, and the family stepped together instead of apart."
        )
        threat.meters["danger"] += 0.0
        child.memes["joy"] += 1.0
        child.meters["fear"] = 0.0
        mother.meters["fear"] = 0.0
        father.meters["fear"] = 0.0

    world.para()
    if params.threat == "fog":
        world.say(
            f"The family sang softly, and the fog could not hide their light for long. The glowing lanterns made a warm road, and the music found them again."
        )
    elif params.threat == "thorn":
        world.say(
            f"The family chose the grass path around the thorn bramble. Curious {child.label} watched the little thorns from a safe distance, and the family kept the dance going."
        )
    else:
        world.say(
            f"The gray wolf only wanted the drumbeats, not the family. When it saw the lanterns and heard the brave song, it slipped away into the trees."
        )

    world.say(
        f"At last, the family returned home with muddy shoes, happy hearts, and a better way to answer curiosity: together, with a light in hand."
    )

    world.facts.update({
        "mother": mother,
        "father": father,
        "child": child,
        "threat_ent": threat,
        "resolved": True,
    })
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f"Write a fairy-tale story about a family and a curious child who follow music to a rave and meet a threat.",
        f"Tell a gentle bedtime-style tale where {child.label} is curious about glowing lanterns, but the family must stay safe from danger.",
        f"Write a short story for children with a family, a magical rave, and a brave ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    mother: Entity = f["mother"]
    father: Entity = f["father"]
    threat: Entity = f["threat_ent"]
    place = world.place.name

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a family with {mother.label}, {father.label}, and the curious child {child.label}.",
        ),
        QAItem(
            question=f"Where did the family go when the music called them?",
            answer=f"They went to {place}, where the fairy-tale rave was shining under the night sky.",
        ),
        QAItem(
            question=f"What made the evening scary for the family?",
            answer=f"The family met {threat.label}, and that threat made the child feel a little shiver.",
        ),
        QAItem(
            question=f"How did the family stay safe?",
            answer=f"They stayed close together, lifted the lanterns, and chose the safe path instead of running off alone.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more, ask questions, and look carefully at new things.",
        )
    ],
    "rave": [
        QAItem(
            question="What is a rave?",
            answer="A rave is a lively music party with dancing, lights, and a strong beat.",
        )
    ],
    "threat": [
        QAItem(
            question="What is a threat?",
            answer="A threat is something that might cause harm or make people feel unsafe, so they need to be careful.",
        )
    ],
    "family": [
        QAItem(
            question="What is a family?",
            answer="A family is a group of people who care for one another and stay together.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ["family", "curiosity", "rave", "threat"] for item in WORLD_KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification helpers
# ---------------------------------------------------------------------------

def asp_storyworld_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("family", "family1")]
    lines.append(asp.fact("member", "family1", "mother"))
    lines.append(asp.fact("member", "family1", "father"))
    lines.append(asp.fact("member", "family1", "child"))
    lines.append(asp.fact("trait", "child", "curious"))
    lines.append(asp.fact("event", "night", "rave"))
    lines.append(asp.fact("near", "wolf", "path"))
    lines.append(asp.fact("stay_close", "family1"))
    lines.append(asp.fact("use_light", "family1"))
    return "\n".join(lines)


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = f"{asp_storyworld_facts()}\n{ASP_RULES}\n#show adventure/1.\n#show unsafe/2.\n#show safe/1.\n"
    model = asp.one_model(program)
    shown = {
        "adventure": asp.atoms(model, "adventure"),
        "unsafe": asp.atoms(model, "unsafe"),
        "safe": asp.atoms(model, "safe"),
    }
    ok = ("family1",) in shown["adventure"] and ("family1", "wolf") in shown["unsafe"] and ("family1",) in shown["safe"]
    if ok:
        print("OK: ASP twin produced the expected storyworld signals.")
        return 0
    print("MISMATCH: ASP twin did not produce expected signals.")
    print(shown)
    return 1


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale family, curiosity, and a ravening rave threat.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--threat", choices=sorted(THREATS))
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
    place = args.place or rng.choice(list(PLACES))
    threat = args.threat or rng.choice(list(THREATS))
    return StoryParams(
        place=place,
        threat=threat,
        family_name=family_name_for(place, threat),
        mother_name=choose_name(rng, "mother"),
        father_name=choose_name(rng, "father"),
        child_name=choose_name(rng, "child"),
        seed=args.seed,
    )


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


# ---------------------------------------------------------------------------
# Curated variants
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="clearing", threat="wolf", family_name="clearing_wolf_family", mother_name="Mira", father_name="Rowan", child_name="Pip"),
    StoryParams(place="garden", threat="fog", family_name="garden_fog_family", mother_name="Elin", father_name="Cedric", child_name="Luna"),
    StoryParams(place="riverbank", threat="thorn", family_name="riverbank_thorn_family", mother_name="Sera", father_name="Bram", child_name="Tessa"),
]


def asp_list() -> None:
    import storyworlds.asp as asp
    program = f"{asp_storyworld_facts()}\n{ASP_RULES}\n#show adventure/1.\n#show unsafe/2.\n#show safe/1.\n"
    model = asp.one_model(program)
    print(f"adventure: {asp.atoms(model, 'adventure')}")
    print(f"unsafe: {asp.atoms(model, 'unsafe')}")
    print(f"safe: {asp.atoms(model, 'safe')}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(f"{asp_storyworld_facts()}\n{ASP_RULES}")
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            seed = (args.seed if args.seed is not None else rng.randrange(2**31)) + i
            i += 1
            local_rng = random.Random(seed)
            params = resolve_params(args, local_rng)
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
            header = f"### {p.family_name} ({p.place}, threat={p.threat})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

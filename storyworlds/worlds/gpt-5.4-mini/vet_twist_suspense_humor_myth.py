#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vet_twist_suspense_humor_myth.py
=================================================================

A standalone tiny storyworld for a myth-flavored vet tale with a small twist,
gentle suspense, and a little humor.

Premise:
- A child brings a strange creature to a village vet.
- The creature's odd symptom seems scary.
- The vet uses calm, practical care.
- The twist is that the "mystery" is harmless and funny, and the ending proves
  the animal is okay.

This world keeps the contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- a Python reasonableness gate plus inline ASP twin
- StoryParams / build_parser / resolve_params / generate / emit / main
- prompts, story QA, and world-knowledge QA from world state
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    name: str
    mood: str
    place_sentence: str
    wonder_sentence: str


@dataclass
class Animal:
    id: str
    species: str
    label: str
    odd_sound: str
    symptom: str
    funny_detail: str
    is_harmless: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class VetTool:
    id: str
    label: str
    use_sentence: str
    helper_sentence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    skill: int
    comfort: int
    sentence: str
    ending_sentence: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["mystery"] < THRESHOLD:
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.entities.values():
            if kid.role == "child":
                kid.memes["suspense"] += 1
        out.append("__murmur__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    vet = next((e for e in world.entities.values() if e.role == "vet"), None)
    patient = next((e for e in world.entities.values() if e.role == "patient"), None)
    if not vet or not patient:
        return out
    if patient.meters["treated"] < THRESHOLD:
        return out
    sig = ("calm", patient.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    vet.memes["pride"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("calm", "social", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(setting: Setting, animal: Animal, remedy: Remedy) -> bool:
    return setting.id in {"temple", "harbor", "village"} and animal.is_harmless and remedy.skill >= 2


def create_sound(world: World, animal: Entity) -> None:
    animal.meters["mystery"] += 1
    animal.memes["unease"] += 1
    propagate(world, narrate=False)


def inspect(world: World, vet: Entity, animal: Entity, tool: VetTool) -> None:
    vet.memes["focus"] += 1
    world.say(f"{vet.id} listened with {tool.label} and watched the creature closely.")
    world.say(tool.use_sentence.replace("{animal}", animal.label))


def reveal(world: World, child: Entity, animal: Entity) -> None:
    child.memes["surprise"] += 1
    world.say(
        f"Then {child.id} saw the trick: the strange {animal.species} had been "
        f"stuck with a thorny burr in {animal.pronoun('possessive')} fur."
    )


def treat(world: World, vet: Entity, animal: Entity, remedy: Remedy) -> None:
    animal.meters["treated"] += 1
    animal.meters["mystery"] = 0
    animal.memes["relief"] += 1
    vet.memes["care"] += 1
    world.say(remedy.sentence.replace("{animal}", animal.label))
    propagate(world, narrate=False)


def joke_ending(world: World, child: Entity, animal: Entity, setting: Setting, remedy: Remedy) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In the end, the {animal.species} was fine, and {animal.id} shook out "
        f"one last burr with a sneeze that sounded like a tiny drumroll."
    )
    world.say(
        f"{child.id} laughed, because the whole mystery had only been a prickly "
        f"little problem in a very grand cloak of suspense."
    )
    world.say(remedy.ending_sentence.replace("{animal}", animal.label))


def tell(setting: Setting, animal: Animal, tool: VetTool, remedy: Remedy,
         child_name: str = "Mara", child_gender: str = "girl",
         vet_name: str = "Vet", vet_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    vet = world.add(Entity(id=vet_name, kind="character", type=vet_gender, role="vet", label="the vet"))
    patient = world.add(Entity(id=animal.id, kind="character", type="animal", role="patient", label=animal.label))
    world.facts["setting"] = setting
    world.facts["animal"] = animal
    world.facts["tool"] = tool
    world.facts["remedy"] = remedy

    child.memes["curiosity"] += 1
    child.memes["love"] += 1
    vet.memes["calm"] += 1

    world.say(
        f"In {setting.name}, where {setting.mood} hung over the stones, "
        f"{child.id} led {animal.label} to {vet.id}."
    )
    world.say(setting.place_sentence)
    world.say(setting.wonder_sentence)
    world.say(
        f"The {animal.species} made a strange sound: \"{animal.odd_sound}!\" "
        f"It looked spooky, and yet a little funny too."
    )

    world.para()
    world.say(f"{child.id} frowned. \"Is it hurt?\" {child.pronoun()} asked.")
    world.say(
        f"{vet.id} lifted {tool.label} and said, \"Let's find the reason before we "
        f"worry.\""
    )
    inspect(world, vet, patient, tool)
    create_sound(world, patient)

    world.para()
    world.say(
        f"{vet.id} parted the fur and found the truth: {animal.funny_detail}."
    )
    reveal(world, child, patient)

    world.para()
    treat(world, vet, patient, remedy)
    world.say(
        f"{vet.id} smiled. \"No beast of doom today. Just a burr and a brave little patient.\""
    )
    joke_ending(world, child, patient, setting, remedy)

    world.facts.update(
        child=child, vet=vet, patient=patient, outcome="resolved",
        suspense=child.memes["suspense"] >= THRESHOLD,
        surprise=child.memes["surprise"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "temple": Setting(
        "temple",
        "the hill temple",
        "a silver hush",
        "The temple steps were cool, and a bell sang softly in the wind.",
        "Even the statues seemed to listen for the smallest sound.",
    ),
    "harbor": Setting(
        "harbor",
        "the harbor shrine",
        "a salty dusk",
        "The boats rocked below, and lanterns blinked like sleepy fireflies.",
        "The water kept whispering, as if it knew a secret.",
    ),
    "village": Setting(
        "village",
        "the village square",
        "a warm evening",
        "The market stalls were closing, and the air smelled like bread and dust.",
        "Children ran in circles while the elders watched the sky.",
    ),
}

ANIMALS = {
    "goat": Animal("goat", "goat", "a white goat", "mmeeh", "a snagged tuft of fur", "a burr hidden in the beard", tags={"animal", "burr"}),
    "donkey": Animal("donkey", "donkey", "a gray donkey", "hee-haw", "a thorn in the mane", "a burr tangled by the ear", tags={"animal", "burr"}),
    "dog": Animal("dog", "dog", "a small dog", "woof-woof", "a thorn in the paw", "a burr stuck under the collar", tags={"animal", "burr"}),
}

TOOLS = {
    "lamp": VetTool("lamp", "a little lamp", "The light showed every twitch and blink.", tags={"light"}),
    "brush": VetTool("brush", "a soft brush", "The brush lifted away dust and leaves.", tags={"care"}),
    "tweezers": VetTool("tweezers", "small tweezers", "The tweezers picked free the sharp little burr.", tags={"care"}),
}

REMEDIES = {
    "pluck": Remedy("pluck", 3, 3, "carefully plucked the burr away from {animal}", "Soon {animal} stood calmly, its troubles gone."),
    "brush": Remedy("brush", 2, 2, "brushed the fur until the burr fell out of {animal}", "After that, {animal} looked lighter and happier."),
}

GIRL_NAMES = ["Mara", "Iris", "Lina", "Nia", "Tala", "Sora"]
BOY_NAMES = ["Kai", "Niko", "Oren", "Pax", "Timo", "Ren"]


@dataclass
class StoryParams:
    setting: str
    animal: str
    tool: str
    remedy: str
    child_name: str
    child_gender: str
    vet_name: str
    vet_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for aid, a in ANIMALS.items():
            for rid, r in REMEDIES.items():
                if reasonableness_gate(s, a, r):
                    combos.append((sid, aid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-flavored vet story world with a small twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--vet-name")
    ap.add_argument("--vet-gender", choices=["woman", "man"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.animal is None or c[1] == args.animal)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, animal, remedy = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    vet_gender = args.vet_gender or rng.choice(["woman", "man"])
    vet_name = args.vet_name or rng.choice(["Aster", "Nera", "Dorin", "Seth"])
    return StoryParams(setting, animal, tool, remedy, child_name, child_gender, vet_name, vet_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal: Animal = f["animal"]
    setting: Setting = f["setting"]
    return [
        f'Write a myth-like story for a 3-to-5-year-old that includes the word "{animal.species}" and the word "vet".',
        f"Tell a suspenseful but gentle tale set at {setting.name} where a child worries about a strange sound, but a vet finds the real cause.",
        f"Write a humorous myth-style story where a brave little helper takes a {animal.species} to the vet and the mystery turns out smaller than expected.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    vet: Entity = f["vet"]
    animal: Entity = f["patient"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question="Who brought the animal to the vet?",
            answer=f"{child.id} did. {child.id} was the one who noticed the strange sound and led the animal to the vet.",
        ),
        QAItem(
            question="Why did the child feel worried at first?",
            answer=f"The sound seemed spooky and mysterious, so {child.id} did not know what was wrong. That made the moment feel suspenseful until the vet looked closely.",
        ),
        QAItem(
            question="What was the real problem with the animal?",
            answer=f"The animal was only stuck with a burr in its fur. The vet found that small problem and fixed it carefully.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with {animal.label} safe and calm in {setting.name}. The scary mystery turned out to be a tiny, funny one.",
        ),
    ]
    if f.get("surprise"):
        qa.append(QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the frightening mystery was not a monster or a curse at all. It was just a burr, which made the whole scene funny once everyone knew the truth.",
        ))
    return qa


WORLD_QA = {
    "vet": [("What does a vet do?",
             "A vet is a doctor for animals. Vets look at animals, find what is wrong, and help them feel better.")],
    "burr": [("What is a burr?",
               "A burr is a small prickly bit from a plant that can stick to fur or clothes.")],
    "lantern": [("Why do people use a lamp or lantern at night?",
                  "A lamp or lantern gives light, so people can see in the dark without guessing.")],
    "animal": [("Why do animals need care?",
                 "Animals can get hurt, hungry, or stuck, and caring people help them stay safe and healthy.")],
    "suspense": [("What is suspense in a story?",
                  "Suspense is the feeling of wondering what will happen next. It can make a story exciting without being too scary.")],
}
WORLD_ORDER = ["vet", "burr", "lantern", "animal", "suspense"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"vet", "animal", "suspense", "burr"}
    out: list[QAItem] = []
    for tag in WORLD_ORDER:
        if tag in tags:
            q, a = WORLD_QA[tag][0]
            out.append(QAItem(q, a))
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("temple", "goat", "lamp", "pluck", "Mara", "girl", "Aster", "woman"),
    StoryParams("harbor", "donkey", "brush", "brush", "Kai", "boy", "Dorin", "man"),
    StoryParams("village", "dog", "tweezers", "pluck", "Lina", "girl", "Nera", "woman"),
]


def outcome_of(params: StoryParams) -> str:
    return "resolved" if reasonableness_gate(SETTINGS[params.setting], ANIMALS[params.animal], REMEDIES[params.remedy]) else "?"


ASP_RULES = r"""
valid(S,A,R) :- setting(S), animal(A), remedy(R), harmless(A), skill(R, K), K >= 2.
"""
def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        if a.is_harmless:
            lines.append(asp.fact("harmless", aid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("skill", rid, r.skill))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: verify smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ANIMALS[params.animal], TOOLS[params.tool], REMEDIES[params.remedy],
                 params.child_name, params.child_gender, params.vet_name, params.vet_gender)
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


def build_parser():
    return build_parser.__wrapped__()  # type: ignore


def main() -> None:
    args = _build_parser()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
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
    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def _build_parser() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Myth vet story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--vet-name")
    ap.add_argument("--vet-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap.parse_args()


if __name__ == "__main__":
    main()

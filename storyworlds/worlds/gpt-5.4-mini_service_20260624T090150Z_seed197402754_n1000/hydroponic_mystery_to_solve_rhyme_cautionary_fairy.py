#!/usr/bin/env python3
"""
A standalone storyworld for a tiny fairy-tale mystery in a hydroponic garden.

Premise:
- A child or young helper tends a glowing hydroponic garden in a fairy-tale
  place.
- Something goes wrong: a crystal drip, a missing charm, a wilted row, or a
  strange whisper.
- The mystery is solved through careful observation, rhyme, and a cautionary
  lesson about not touching the wrong thing.

This world is intentionally small and classical:
- One scene, one problem, one careful investigation, one resolution.
- Physical state uses meters; emotional state uses memes.
- Prose is driven by world state, not by a frozen template.
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


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "fairy"}
        male = {"boy", "father", "king", "man", "goblin"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    light: str
    afford: set[str] = field(default_factory=set)


@dataclass
class HeroConfig:
    name: str
    gender: str
    title: str
    trait: str


@dataclass
class Mystery:
    id: str
    clue: str
    danger: str
    rhyme: str
    reason: str
    effect: str
    repair: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    gender: str
    title: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "glasshouse": Setting(
        place="the glasshouse",
        light="soft moonlight",
        afford={"search", "sing", "tend"},
    ),
    "moon_garden": Setting(
        place="the moon garden",
        light="silver light",
        afford={"search", "sing", "tend"},
    ),
    "rose_tower": Setting(
        place="the rose tower",
        light="golden dawn",
        afford={"search", "sing", "tend"},
    ),
}

MYSTERIES = {
    "dry_pipe": Mystery(
        id="dry_pipe",
        clue="one line of lettuce drooped even though the pumps hummed",
        danger="the roots might thirst",
        rhyme="When pipes go dry, the leaves grow shy.",
        reason="a tiny pebble had lodged in the drip tube",
        effect="the water could not reach the roots",
        repair="clear the pebble from the tube",
        tags={"hydroponic", "water", "roots"},
    ),
    "mist_alarm": Mystery(
        id="mist_alarm",
        clue="the fogger sang, but the basil still looked thirsty",
        danger="too much fog can sour the leaves",
        rhyme="When mist is thick, the leaves grow sick.",
        reason="the fog cloth had been left over the nozzle",
        effect="the spray could not drift over the trays",
        repair="lift the fog cloth away",
        tags={"hydroponic", "mist", "leaves"},
    ),
    "glow_seed": Mystery(
        id="glow_seed",
        clue="a bright seed bead was missing from the charm bowl",
        danger="a stolen charm can scare the garden sprites",
        rhyme="A charm that strays may dim the praise.",
        reason="a curious beetle had rolled it into the moss",
        effect="the charm no longer sang above the troughs",
        repair="find the seed bead in the moss",
        tags={"hydroponic", "mystery", "charm"},
    ),
    "bent_spoon": Mystery(
        id="bent_spoon",
        clue="the compost spoon lay bent beside the herb shelf",
        danger="rough tools can crack the careful trays",
        rhyme="A careless hand makes tools unplanned.",
        reason="someone had used the spoon to pry open the latch",
        effect="the latch had jammed the seed cabinet",
        repair="set the spoon back and free the latch",
        tags={"hydroponic", "tool", "careful"},
    ),
}

HEROES = {
    "girl": ["Mina", "Lena", "Ivy", "Nora", "Elin"],
    "boy": ["Finn", "Tomas", "Milo", "Evan", "Owen"],
}

TRAITS = ["gentle", "curious", "brave", "careful", "kind", "bright"]

GENTLE_HELP = {
    "search": "look closely among the trays",
    "sing": "hum a soft rhyme",
    "tend": "steady the tiny roots",
}

KNOWLEDGE = {
    "hydroponic": [
        (
            "What does hydroponic mean?",
            "Hydroponic means plants are grown in water with help from a special tray, instead of in soil.",
        )
    ],
    "roots": [
        (
            "Why do roots need water?",
            "Roots drink water and hold the plant steady, so the plant can grow strong and green.",
        )
    ],
    "water": [
        (
            "Why must plant water be clean?",
            "Clean water helps plants grow well, while dirty water can make them weak or sick.",
        )
    ],
    "mist": [
        (
            "What is mist?",
            "Mist is a very fine spray of tiny water drops floating in the air.",
        )
    ],
    "charm": [
        (
            "What is a charm in a fairy tale?",
            "A charm is a special object that can feel magical, lucky, or precious in a story.",
        )
    ],
    "tool": [
        (
            "Why should children use tools carefully?",
            "Tools should be used carefully so they do not break things or cause someone to get hurt.",
        )
    ],
    "careful": [
        (
            "What does it mean to be careful?",
            "Being careful means moving slowly, looking first, and choosing the safe way.",
        )
    ],
}


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def pluralize(word: str) -> str:
    return word if word.endswith("s") else word + "s"


def choice(rng: random.Random, seq):
    return seq[rng.randrange(len(seq))]


def valid_mysteries() -> list[str]:
    return list(MYSTERIES.keys())


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.gender,
        label=params.hero_name,
        phrase=f"little {params.trait} {params.title}",
        memes={"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "resolve": 0.0},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type="woman" if params.gender == "girl" else "man",
        label="the garden elder",
        phrase="the garden elder",
        memes={"care": 1.0},
    ))
    garden = world.add(Entity(
        id="Garden",
        kind="thing",
        type="garden",
        label=setting.place,
        phrase=setting.place,
    ))
    trays = world.add(Entity(
        id="Trays",
        kind="thing",
        type="trays",
        label="the trays",
        phrase="the narrow trays",
        owner=elder.id,
    ))
    clue = world.add(Entity(
        id="Clue",
        kind="thing",
        type="clue",
        label="the clue",
        phrase=mystery.clue,
        owner=garden.id,
    ))

    # Initial state.
    world.facts.update(hero=hero, elder=elder, garden=garden, trays=trays, clue=clue, mystery=mystery)

    # Opening scene.
    world.say(
        f"In {setting.place}, under {setting.light}, {hero.label} was a {params.trait} "
        f"little {params.title} who loved the shining green rows."
    )
    world.say(
        f"{hero.label} tended the hydroponic trays with {elder.label}, and the leaves "
        f"usually stood up straight like tiny crowns."
    )
    world.para()

    # Mystery appears.
    clue_text = mystery.clue
    world.say(
        f"Then one quiet evening, {clue_text}, and {hero.label} frowned."
    )
    world.say(
        f"{hero.label} felt a small worry in {hero.pronoun('possessive')} chest, because "
        f"{mystery.danger}."
    )
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    world.para()

    # Investigation.
    world.say(
        f"{hero.label} said, \"{mystery.rhyme}\""
    )
    world.say(
        f"{elder.label} nodded. \"A good rhyme can hide a good clue,\" {elder.pronoun()} said."
    )
    world.say(
        f"Together they began to {GENTLE_HELP['search']}, and {hero.label} noticed that "
        f"{mystery.reason}."
    )
    hero.memes["curiosity"] += 1
    world.facts["reason"] = mystery.reason
    world.facts["effect"] = mystery.effect
    world.facts["repair"] = mystery.repair

    # Tiny consequence state.
    if mystery.id == "dry_pipe":
        world.add(Entity(
            id="Pipe",
            kind="thing",
            type="pipe",
            label="the drip tube",
            phrase="the drip tube",
            meters={"blocked": 1.0, "wet": 0.0},
        ))
        world.say(
            f"That meant {mystery.effect}, so the lettuce had begun to bow its heads."
        )
    elif mystery.id == "mist_alarm":
        world.add(Entity(
            id="Fogger",
            kind="thing",
            type="fogger",
            label="the fogger",
            phrase="the misting nozzle",
            meters={"blocked": 1.0},
        ))
        world.say(
            f"That meant {mystery.effect}, and the basil curled its leaves in complaint."
        )
    elif mystery.id == "glow_seed":
        world.add(Entity(
            id="Moss",
            kind="thing",
            type="moss",
            label="the moss patch",
            phrase="the soft moss",
            meters={"searched": 1.0},
        ))
        world.say(
            f"That meant the charm no longer sang above the troughs, and the sprites looked dim."
        )
    else:
        world.add(Entity(
            id="Latch",
            kind="thing",
            type="latch",
            label="the seed cabinet latch",
            phrase="the seed cabinet latch",
            meters={"jammed": 1.0},
        ))
        world.say(
            f"That meant the seed cabinet was stuck, and the little packets could not be reached."
        )

    world.para()

    # Turn: cautionary lesson and fix.
    world.say(
        f"{hero.label} remembered the old lesson: \"Never tug at a garden thing before you know what it is.\""
    )
    world.say(
        f"So {hero.label} moved carefully, one hand on the rail and one eye on the clue."
    )
    world.say(
        f"At last, {hero.label} used the rhyme to solve the mystery: {mystery.repair}."
    )
    hero.memes["resolve"] += 1
    hero.memes["joy"] += 1
    world.facts["solved"] = True

    # Resolution changes state.
    if mystery.id == "dry_pipe":
        world.get("Pipe").meters["blocked"] = 0.0
        world.say(
            f"The pebble popped free, the water sang through the tube, and the lettuce lifted again."
        )
    elif mystery.id == "mist_alarm":
        world.get("Fogger").meters["blocked"] = 0.0
        world.say(
            f"The fog cloth slipped away, the mist drifted softly, and the basil brightened at once."
        )
    elif mystery.id == "glow_seed":
        world.get("Moss").meters["searched"] = 0.0
        world.say(
            f"The bright bead was found in the moss, and the charm bowl shimmered once more."
        )
    else:
        world.get("Latch").meters["jammed"] = 0.0
        world.say(
            f"The spoon was set aside, the latch sprang open, and the seed packets rested safe again."
        )

    world.say(
        f"By the end, the garden glowed peacefully, and {hero.label} smiled beside {elder.label}, "
        f"glad that careful hands had saved the fairy-tale rows."
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts from registries:
% setting(S). afford(S,A). mystery(M). tags(M,T).

% The mystery is solvable when the clue, danger, and repair are all present.
solvable(M) :- mystery(M), clue(M,_), danger(M,_), repair(M,_).

% A cautionary story requires a danger and a repair, plus a rhyme.
cautionary(M) :- mystery(M), danger(M,_), repair(M,_), rhyme(M,_).

% A fairy-tale hydroponic mystery is valid when it touches hydroponic plants
% and has a rhyme and a safe repair.
valid_story(S, M) :- setting(S), mystery(M), tags(M,hydroponic), rhyme(M,_), repair(M,_).

#show valid_story/2.
#show solvable/1.
#show cautionary/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("afford", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("danger", mid, m.danger))
        lines.append(asp.fact("rhyme", mid, m.rhyme))
        lines.append(asp.fact("reason", mid, m.reason))
        lines.append(asp.fact("effect", mid, m.effect))
        lines.append(asp.fact("repair", mid, m.repair))
        for t in sorted(m.tags):
            lines.append(asp.fact("tags", mid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2.\n#show solvable/1.\n#show cautionary/1."))
    symbols = set((s.name, tuple(a.name if a.type != a.type.Number and a.type != a.type.String else (a.number if a.type == a.type.Number else a.string) for a in s.arguments)) for s in model)
    expected = set()
    for s in SETTINGS:
        for m in MYSTERIES:
            if "hydroponic" in MYSTERIES[m].tags:
                expected.add(("valid_story", (s, m)))
                expected.add(("solvable", (m,)))
                expected.add(("cautionary", (m,)))
    if symbols == expected:
        print(f"OK: ASP parity verified ({len(expected)} atoms).")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(symbols))
    print("PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# QA and presentation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a gentle fairy tale mystery about {hero.label} in {world.setting.place} with the word "hydroponic".',
        f"Tell a child-sized story where {hero.label} notices a strange problem in a hydroponic garden and solves it with a rhyme.",
        f"Write a cautionary fairy tale about a garden mystery, a soft warning, and a safe repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question=f"Where did {hero.label} discover the mystery?",
            answer=f"{hero.label} discovered it in {world.setting.place}, where the hydroponic trays were glowing under {world.setting.light}.",
        ),
        QAItem(
            question=f"What was the clue that made {hero.label} worry?",
            answer=f"The clue was that {mystery.clue}. That made {hero.label} notice something was wrong.",
        ),
        QAItem(
            question=f"How did {hero.label} solve the problem?",
            answer=f"{hero.label} solved it by listening to the rhyme, finding that {mystery.reason}, and then doing the repair: {mystery.repair}.",
        ),
        QAItem(
            question=f"What cautionary lesson did {hero.label} learn?",
            answer=f"{hero.label} learned not to tug at a garden thing before understanding it, because a careless touch can make a plant problem worse.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            for q, a in pairs:
                out.append(QAItem(question=q, answer=a))
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonable choices
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES if "hydroponic" in MYSTERIES[m].tags]


CURATED = [
    StoryParams(setting="glasshouse", mystery="dry_pipe", hero_name="Mina", gender="girl", title="gardener", trait="gentle"),
    StoryParams(setting="moon_garden", mystery="mist_alarm", hero_name="Finn", gender="boy", title="page", trait="curious"),
    StoryParams(setting="rose_tower", mystery="glow_seed", hero_name="Ivy", gender="girl", title="helper", trait="brave"),
    StoryParams(setting="glasshouse", mystery="bent_spoon", hero_name="Owen", gender="boy", title="apprentice", trait="careful"),
]


def explain_invalid(setting: str, mystery: str) -> str:
    return f"(No story: the requested setting and mystery are not a valid fairy-tale hydroponic pairing.)"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small hydroponic fairy-tale mystery world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--title", choices=["gardener", "page", "helper", "apprentice"])
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
    if args.setting and args.mystery:
        if (args.setting, args.mystery) not in valid_combos():
            raise StoryError(explain_invalid(args.setting, args.mystery))
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choice(rng, HEROES[gender])
    title = args.title or choice(rng, ["gardener", "page", "helper", "apprentice"])
    trait = args.trait or choice(rng, TRAITS)
    return StoryParams(setting=setting, mystery=mystery, hero_name=name, gender=gender, title=title, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/2.\n#show solvable/1.\n#show cautionary/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2.\n"))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        for s, m in atoms:
            print(s, m)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

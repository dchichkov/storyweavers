#!/usr/bin/env python3
"""
A small pirate tale storyworld built around sound effects, moral value, and a
mystery to solve.

Seed tale premise:
A young deckhand on a tiny pirate ship keeps hearing strange sounds in the night.
The crew suspects a trickster, but the real problem is a careless habit that
knocks things loose below deck. The hero must listen closely, choose a good
course, and solve the mystery without blaming the wrong sailor.

This world keeps the narration concrete and state-driven: the ship has a place,
a noisy clue, a moral choice, a hidden cause, and a resolution that changes the
world model.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pirate"}
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
    berth: str
    afford_noise: bool = True


@dataclass
class Mystery:
    clue: str
    sound: str
    cause: str
    reveal: str
    moral: str
    solved_by: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_kind: str
    captain_kind: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_trust(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes.get("listened", 0) >= THRESHOLD and hero.memes.get("kindness", 0) >= THRESHOLD:
        sig = ("trust",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["trust"] = hero.memes.get("trust", 0) + 1
            out.append("The crew trusted the little deckhand to keep listening.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("searched") and world.facts.get("cause_found"):
        sig = ("reveal",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(world.facts["reveal_sentence"])
    return out


CAUSAL_RULES = [Rule("trust", _r_trust), Rule("reveal", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


SETTINGS = {
    "ship": Setting(place="the little ship", berth="below deck"),
    "harbor": Setting(place="the harbor", berth="the hold"),
    "cove": Setting(place="the moonlit cove", berth="the captain's cabin"),
}

MYSTERIES = {
    "lantern": Mystery(
        clue="a clink-clink and a wobble",
        sound="clink-clink",
        cause="a loose lantern hook",
        reveal="The lantern hook had been shaking free and bumping the rail.",
        moral="It was wiser to tell the truth about the loose hook than to hide it.",
        solved_by="tightening the hook",
    ),
    "barrel": Mystery(
        clue="a thump-thump and a roll",
        sound="thump-thump",
        cause="an untied barrel",
        reveal="The barrel had rolled because nobody tied it down after supper.",
        moral="Good sailors tie down what might roll before trouble starts.",
        solved_by="roping the barrel snug",
    ),
    "mapcase": Mystery(
        clue="a scrape-scrape from the chest",
        sound="scrape-scrape",
        cause="a mapcase sliding loose",
        reveal="The mapcase had slid because the latch was left open in the rush.",
        moral="A careful habit saves a ship from needless worry.",
        solved_by="closing the latch properly",
    ),
}

HERO_NAMES = ["Pip", "Mara", "Ned", "Tess", "Jory", "Luna"]
TRAITS = ["brave", "curious", "quick-eared", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mid) for place in SETTINGS for mid in MYSTERIES]


@dataclass
class ASPFacts:
    pass


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("sound", mid, m.sound))
        lines.append(asp.fact("cause", mid, m.cause))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, M) :- setting(Place), mystery(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(a - b))
    print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world with sound effects, moral value, and a mystery to solve.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--hero-kind", choices=["girl", "boy"])
    ap.add_argument("--captain-kind", choices=["captain", "pirate"], default="captain")
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
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              and args.mystery is None or c[1] == args.mystery]
    # explicit parentheses above are intentionally avoided by re-checking below
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    hero_kind = args.hero_kind or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, hero_name=name, hero_kind=hero_kind,
                       captain_kind=args.captain_kind, trait=trait)


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_kind: str,
         captain_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_kind, label=hero_name,
                            traits=["little", trait]))
    captain = world.add(Entity(id="captain", kind="character", type=captain_kind, label="Captain Rook"))
    chest = world.add(Entity(id="chest", type="thing", label="the chest"))
    lantern = world.add(Entity(id="lantern", type="thing", label="the lantern"))
    barrel = world.add(Entity(id="barrel", type="thing", label="the barrel"))
    mapcase = world.add(Entity(id="mapcase", type="thing", label="the mapcase"))
    _ = (chest, lantern, barrel, mapcase)

    world.say(f"{hero_name} was a little {trait} {hero_kind} on {setting.place}, where the waves made the wood creak.")
    world.say(f"{hero_name} loved the salty air, and the ship answered every step with a squeak and a sway.")
    world.para()
    world.say(f"One night, {hero_name} heard {mystery.clue}.")
    world.say(f'“{mystery.sound},” {hero_name} whispered, listening hard.')
    world.say(f"{captain.label} frowned. “A sound like that could mean trouble below deck.”")
    hero.memes["listened"] = 1
    hero.memes["kindness"] = 1
    world.para()
    world.say(f"Some crew wanted to blame a sneaky sea sprite, but {hero_name} chose a fairer way.")
    world.say(f"Instead of accusing anyone, {hero_name} went quietly {setting.berth} to look for the cause.")
    world.facts["searched"] = True
    if mystery.cause == "a loose lantern hook":
        world.say("There, the lantern was swaying near the rail.")
        world.say("A metal hook had worked loose and tapped the post with every roll of the ship.")
    elif mystery.cause == "an untied barrel":
        world.say("There, a barrel was nudging along the planks like a sleepy drum.")
        world.say("Its rope had come undone, so each wave made it thump and roll.")
    else:
        world.say("There, the mapcase had slipped out of place beside the chest.")
        world.say("Its latch had been left open, so the sea made it scrape and slide.")
    world.facts["cause_found"] = True
    world.facts["reveal_sentence"] = mystery.reveal
    propagate(world, narrate=False)
    world.say(mystery.reveal)
    world.para()
    world.say(f"{hero_name} fixed the problem by {mystery.solved_by}.")
    world.say(f"The spooky sound stopped at once, and the ship grew calm again.")
    world.say(f"Captain Rook nodded. “That was a good sailor's choice,” {captain.pronoun('subject')} said.")
    world.say(f"{mystery.moral}")
    world.say(f"At the end, the only sound left was the soft hush of waves against the hull.")
    world.facts.update(hero=hero, captain=captain, setting=setting, mystery=mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a short pirate tale for a young child that includes the sound "{mystery.sound}".',
        f"Tell a gentle story where {hero.label} hears a strange noise on {world.setting.place} and solves the mystery without blaming the wrong sailor.",
        f"Write a tiny pirate story with a moral lesson about being fair and careful, ending with the mystery solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    captain = f["captain"]
    return [
        QAItem(
            question=f"What strange sound did {hero.label} hear on {world.setting.place}?",
            answer=f"{hero.label} heard {mystery.sound} and followed it carefully.",
        ),
        QAItem(
            question=f"Why did {hero.label} avoid blaming anyone right away?",
            answer="Because the little deckhand chose to listen first and be fair instead of accusing someone without proof.",
        ),
        QAItem(
            question=f"What did {hero.label} find was causing the noise?",
            answer=mystery.reveal,
        ),
        QAItem(
            question=f"How did {hero.label} fix the trouble?",
            answer=f"{hero.label} fixed it by {mystery.solved_by}, and then the sound stopped.",
        ),
        QAItem(
            question=f"What did Captain Rook think of {hero.label}'s choice?",
            answer=f"Captain Rook thought it was a good sailor's choice because {hero.label} solved the problem kindly and carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a deckhand?",
            answer="A deckhand is a worker on a ship who helps keep things in order and does useful jobs on deck.",
        ),
        QAItem(
            question="Why should sailors tie down loose things?",
            answer="Loose things can roll, bang, or fall when the ship moves, so tying them down helps keep everyone safe.",
        ),
        QAItem(
            question="What is a fair way to solve a mystery?",
            answer="A fair way is to look for clues first and avoid blaming someone until you know what really happened.",
        ),
    ]


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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.hero_name,
                 params.hero_kind, params.captain_kind, params.trait)
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
    StoryParams(place="ship", mystery="lantern", hero_name="Pip", hero_kind="boy", captain_kind="captain", trait="curious"),
    StoryParams(place="harbor", mystery="barrel", hero_name="Mara", hero_kind="girl", captain_kind="captain", trait="thoughtful"),
    StoryParams(place="cove", mystery="mapcase", hero_name="Ned", hero_kind="boy", captain_kind="pirate", trait="quick-eared"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, mystery) combos:\n")
        for place, mid in triples:
            print(f"  {place:8} {mid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
